"""
backend/data_feed.py
====================
Nexus AI — Data Daemon (Phase 1)

Standalone background process that:
  1. Retrieves a Tradovate OAuth token (async-safe, Redis-cached with TTL).
  2. Connects to the Tradovate Market Data WebSocket.
  3. Subscribes to ES tick/quote events.
  4. Normalises each frame into the canonical Tick schema and publishes it
     to the Redis Pub/Sub channel `market_data_stream`.

Run with:
    py -m backend.data_feed
  or directly:
    py backend/data_feed.py

Architecture reference: ARCHITECTURE.md § "The Data Daemon"
"""

import asyncio
import json
import logging
import os
import time
from typing import Optional

import redis.asyncio as aioredis
import websockets
import websockets.exceptions

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("nexus.data_feed")

# ---------------------------------------------------------------------------
# Configuration  (override via environment variables in production)
# ---------------------------------------------------------------------------

# Tradovate endpoints
TRADOVATE_AUTH_URL: str = os.getenv(
    "TRADOVATE_AUTH_URL",
    "https://demo.tradovateapi.com/v1/auth/accesstokenrequest",
)
TRADOVATE_MD_WS_URL: str = os.getenv(
    "TRADOVATE_MD_WS_URL",
    "wss://md.tradovateapi.com/v1/websocket",
)

# Tradovate credentials — MUST be set in .env / environment for production.
TV_USERNAME: str = os.getenv("TV_USERNAME", "")
TV_PASSWORD: str = os.getenv("TV_PASSWORD", "")
TV_APP_ID: str = os.getenv("TV_APP_ID", "")
TV_APP_VERSION: str = os.getenv("TV_APP_VERSION", "1.0")
TV_CID: str = os.getenv("TV_CID", "")
TV_SEC: str = os.getenv("TV_SEC", "")

# Redis
REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

# Token cache
TOKEN_CACHE_KEY: str = "nexus_tradovate_token"
# Tradovate tokens are valid for 120 minutes; we cache for 110 to leave a
# 10-minute safety buffer before the exchange actually expires the token.
TOKEN_TTL_SECONDS: int = 6_600  # 110 minutes

# Pub/Sub channel (must match server/main.py subscriber)
REDIS_CHANNEL: str = "market_data_stream"

# ES symbol to subscribe to (front-month; update as needed)
ES_SYMBOL: str = os.getenv("ES_SYMBOL", "ESM4")

# Reconnection back-off
RECONNECT_BASE_DELAY: float = 1.0   # seconds
RECONNECT_MAX_DELAY: float = 30.0   # seconds

# ---------------------------------------------------------------------------
# Token management
# ---------------------------------------------------------------------------

async def _fetch_token_from_tradovate() -> Optional[str]:
    """
    Performs a real HTTP POST to Tradovate's auth endpoint.
    Returns the accessToken string, or None on failure.

    In development (no credentials set) this falls back to a mock token so
    the daemon can still run and publish synthetic data for local testing.
    """
    # --- Development / mock path -------------------------------------------
    if not TV_USERNAME:
        logger.warning(
            "TV_USERNAME not set — using mock token. "
            "Set TV_USERNAME / TV_PASSWORD / TV_APP_ID / TV_CID / TV_SEC "
            "in your environment for production."
        )
        return "mock_token_dev"

    # --- Production path ----------------------------------------------------
    import aiohttp  # lazy import; only needed when real credentials exist

    payload = {
        "name": TV_USERNAME,
        "password": TV_PASSWORD,
        "appId": TV_APP_ID,
        "appVersion": TV_APP_VERSION,
        "cid": TV_CID,
        "sec": TV_SEC,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                TRADOVATE_AUTH_URL, json=payload, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                token = data.get("accessToken")
                if not token:
                    logger.error("Tradovate auth response missing 'accessToken': %s", data)
                    return None
                logger.info("✅ New Tradovate token obtained from API.")
                return token
    except Exception as exc:
        logger.error("Tradovate auth request failed: %s", exc)
        return None


async def get_token(redis: aioredis.Redis) -> str:
    """
    Returns a valid Tradovate OAuth token.

    Strategy:
      1. Check Redis for a cached token (cache hit → return immediately).
      2. On cache miss, call Tradovate's auth endpoint.
      3. Store the new token in Redis with TOKEN_TTL_SECONDS TTL.
      4. If auth fails entirely, return a fallback mock token so the daemon
         can continue running in degraded / dev mode.
    """
    cached = await redis.get(TOKEN_CACHE_KEY)
    if cached:
        logger.info("⚡ Cache hit — using existing Tradovate token.")
        return cached

    logger.info("🔄 Cache miss — fetching new Tradovate token…")
    token = await _fetch_token_from_tradovate()

    if token:
        await redis.setex(TOKEN_CACHE_KEY, TOKEN_TTL_SECONDS, token)
        logger.info(
            "🔒 Token cached in Redis (TTL=%ds / %.0f min).",
            TOKEN_TTL_SECONDS,
            TOKEN_TTL_SECONDS / 60,
        )
    else:
        token = "fallback_mock_token"
        logger.warning("⚠️  Auth failed — using fallback mock token.")

    return token


# ---------------------------------------------------------------------------
# Tick normalisation
# ---------------------------------------------------------------------------

def _build_tick_payload(raw: dict, symbol: str) -> Optional[str]:
    """
    Converts a raw Tradovate quote/tick dict into the canonical Tick schema
    and returns it as a JSON string ready for Redis PUBLISH.

    Canonical schema (per ARCHITECTURE.md § "The Data Daemon"):
        {
            "symbol":    str,
            "timestamp": int,   # Unix ms
            "price":     float, # last traded price
            "volume":    int,
            "bid":       float,
            "ask":       float
        }

    Returns None if the frame carries no useful price data (e.g. heartbeat
    sub-frames or subscription confirmations).
    """
    # Tradovate quote frames use these keys; fall back gracefully.
    price: float = float(raw.get("lp", raw.get("lastPrice", raw.get("p", 0.0))))
    bid: float   = float(raw.get("bp", raw.get("bid",       raw.get("b", 0.0))))
    ask: float   = float(raw.get("ap", raw.get("ask",       raw.get("a", 0.0))))
    volume: int  = int(  raw.get("lv", raw.get("volume",    raw.get("v", 0))))

    # Skip frames that carry no price information at all
    if price == 0.0 and bid == 0.0 and ask == 0.0:
        return None

    # Use the frame's own timestamp if present; otherwise wall-clock ms
    ts_raw = raw.get("t", raw.get("timestamp"))
    if ts_raw is not None:
        try:
            # Tradovate timestamps are ISO-8601 strings or epoch ms integers
            if isinstance(ts_raw, str):
                from datetime import datetime, timezone
                dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                timestamp = int(dt.timestamp() * 1000)
            else:
                timestamp = int(ts_raw)
        except Exception:
            timestamp = int(time.time() * 1000)
    else:
        timestamp = int(time.time() * 1000)

    tick = {
        "symbol":    symbol,
        "timestamp": timestamp,
        "price":     price,
        "volume":    volume,
        "bid":       bid,
        "ask":       ask,
    }
    return json.dumps(tick)


# ---------------------------------------------------------------------------
# WebSocket client
# ---------------------------------------------------------------------------

async def _run_feed(redis: aioredis.Redis) -> None:
    """
    Single connection lifecycle:
      - Authenticate with Tradovate WS.
      - Subscribe to ES tick data.
      - Ingest frames, normalise, and publish to Redis.
      - Respond to Tradovate heartbeats to keep the connection alive.

    Raises on connection failure so the outer retry loop can back off.
    """
    token = await get_token(redis)

    logger.info("🔌 Connecting to Tradovate Market Data WS: %s", TRADOVATE_MD_WS_URL)

    async with websockets.connect(
        TRADOVATE_MD_WS_URL,
        ping_interval=20,   # websockets library-level keepalive
        ping_timeout=10,
        close_timeout=5,
    ) as ws:
        logger.info("✅ Connected to Tradovate Market Data WebSocket.")

        # --- Step 1: Authorise -----------------------------------------------
        auth_frame = f"authorize\n{token}"
        await ws.send(auth_frame)
        logger.info("🔑 Authorization frame sent.")

        # Wait for the auth acknowledgement before subscribing
        auth_response = await asyncio.wait_for(ws.recv(), timeout=10)
        logger.info("Auth response: %s", auth_response[:200])

        # --- Step 2: Subscribe to ES tick data --------------------------------
        # `md/subscribeQuote` delivers real-time best-bid/offer + last price.
        # For raw tick-by-tick data use `md/subscribeDom` or `md/getChart`.
        subscribe_frame = json.dumps({"symbol": ES_SYMBOL})
        await ws.send(f"md/subscribeQuote\n{subscribe_frame}")
        logger.info("📡 Subscribed to %s quote stream.", ES_SYMBOL)

        # --- Step 3: Ingest loop ---------------------------------------------
        ticks_published: int = 0

        async for raw_message in ws:
            # Tradovate protocol:
            #   'h'        → server heartbeat; must reply with 'h'
            #   'o'        → connection opened confirmation
            #   'c'        → connection closed by server
            #   'a[...]'   → array of JSON event objects

            if raw_message == "h":
                # Respond to keep the connection alive
                await ws.send("h")
                continue

            if raw_message in ("o", "c"):
                logger.info("Tradovate control frame: %r", raw_message)
                if raw_message == "c":
                    logger.warning("Server sent close frame — reconnecting.")
                    break
                continue

            if not raw_message.startswith("a"):
                logger.debug("Unrecognised frame prefix: %r", raw_message[:80])
                continue

            # Parse the array payload
            try:
                events = json.loads(raw_message[1:])
            except json.JSONDecodeError as exc:
                logger.warning("JSON decode error on frame: %s", exc)
                continue

            if not isinstance(events, list):
                events = [events]

            for event in events:
                if not isinstance(event, dict):
                    continue

                # Tradovate wraps quote updates inside an 'e' (event) key
                # with a 'd' (data) sub-key, or delivers them flat.
                data_frames = []
                if "d" in event and isinstance(event["d"], dict):
                    # Nested format: {"e": "md", "d": {"quotes": [...]}}
                    quotes = event["d"].get("quotes", [])
                    data_frames.extend(quotes)
                else:
                    # Flat format: the event itself is the quote dict
                    data_frames.append(event)

                for frame in data_frames:
                    payload_str = _build_tick_payload(frame, ES_SYMBOL)
                    if payload_str is None:
                        continue

                    await redis.publish(REDIS_CHANNEL, payload_str)
                    ticks_published += 1

                    if ticks_published % 100 == 0:
                        logger.info(
                            "📊 %d ticks published to '%s'.",
                            ticks_published,
                            REDIS_CHANNEL,
                        )


# ---------------------------------------------------------------------------
# Main entry point with reconnection loop
# ---------------------------------------------------------------------------

async def main() -> None:
    """
    Outer supervisor loop.

    Maintains a persistent Redis connection and restarts the WebSocket feed
    on any failure using exponential back-off (1 s → 30 s max).
    """
    redis = aioredis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
    )

    logger.info(
        "🚀 Nexus Data Daemon starting — Redis=%s:%d, channel='%s', symbol=%s",
        REDIS_HOST,
        REDIS_PORT,
        REDIS_CHANNEL,
        ES_SYMBOL,
    )

    delay: float = RECONNECT_BASE_DELAY

    while True:
        try:
            await _run_feed(redis)
            # If _run_feed returns cleanly (server-side close), reconnect
            # immediately with a short delay.
            logger.info("Feed ended cleanly — reconnecting in %.1fs…", RECONNECT_BASE_DELAY)
            delay = RECONNECT_BASE_DELAY

        except (
            websockets.exceptions.ConnectionClosed,
            websockets.exceptions.WebSocketException,
            OSError,
            asyncio.TimeoutError,
        ) as exc:
            logger.error(
                "WebSocket error (%s: %s) — reconnecting in %.1fs…",
                type(exc).__name__,
                exc,
                delay,
            )

        except Exception as exc:
            logger.exception("Unexpected error in data feed: %s", exc)

        await asyncio.sleep(delay)
        # Exponential back-off, capped at RECONNECT_MAX_DELAY
        delay = min(delay * 2, RECONNECT_MAX_DELAY)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Data daemon stopped by user.")
