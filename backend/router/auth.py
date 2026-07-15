import os
import logging
import redis
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("nexus.auth")

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=int(os.getenv("REDIS_DB", "0")),
    decode_responses=True,
)

TRADOVATE_API_URL = os.getenv("TRADOVATE_API_URL", "https://demo.tradovateapi.com/v1")

TV_USERNAME    = os.getenv("TV_USERNAME", "")
TV_PASSWORD    = os.getenv("TV_PASSWORD", "")
TV_APP_ID      = os.getenv("TV_APP_ID", "")
TV_APP_VERSION = os.getenv("TV_APP_VERSION", "1.0")
TV_CID         = os.getenv("TV_CID", "")
TV_SEC         = os.getenv("TV_SEC", "")

_DEV_MODE = not TV_USERNAME


def get_tradovate_token() -> str:
    """
    Returns a valid Tradovate OAuth token, Redis-cached for 110 minutes.
    In dev mode (TV_USERNAME not set), returns a mock token and logs a warning.
    """
    cache_key = "nexus_tradovate_token"

    cached_token = redis_client.get(cache_key)
    if cached_token:
        logger.debug("Cache hit: reusing existing Tradovate token")
        return cached_token

    if _DEV_MODE:
        logger.warning(
            "TV_USERNAME not set — using mock token. "
            "Set Tradovate credentials in .env for live trading."
        )
        return "mock_token_dev"

    logger.info("Cache miss: fetching new Tradovate token...")
    endpoint = f"{TRADOVATE_API_URL}/auth/accesstokenrequest"

    import requests  # lazy import
    payload = {
        "name":       TV_USERNAME,
        "password":   TV_PASSWORD,
        "appId":      TV_APP_ID,
        "appVersion": TV_APP_VERSION,
        "cid":        TV_CID,
        "sec":        TV_SEC,
    }

    try:
        response = requests.post(endpoint, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        new_token = data.get("accessToken")
        if not new_token:
            raise ValueError(f"Auth response missing accessToken: {data}")

        redis_client.setex(cache_key, 6600, new_token)
        logger.info("New Tradovate token cached (TTL=110min)")
        return new_token

    except Exception as exc:
        logger.error("Tradovate auth failed: %s", exc)
        raise RuntimeError(f"Tradovate authentication failed: {exc}") from exc
