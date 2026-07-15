"""
Nexus AI — Algo Terminal Backend
=================================
FastAPI app entry point. Provides:
  - REST API for algos, account, positions, market data
  - WebSocket hub at /ws/market (bar/tick/execution events)
  - NinjaTrader bridge integration
  - PAMM trade gateway → Redis → Celery
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
load_dotenv()

import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Logging (configure before any conditional imports) ────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
)
logger = logging.getLogger("nexus.server")

# ── PAMM / Celery integration ─────────────────────────────────────────────────
try:
    from backend.router.allocator import process_master_signal
    from backend.router.celery_app import celery_app as _celery_app
    CELERY_AVAILABLE = True
except ImportError as _ce:
    CELERY_AVAILABLE = False
    _celery_app = None
    logger.warning(
        "Celery/PAMM not available (%s). PAMM trade routing disabled. "
        "Start worker with: python -m celery -A backend.router.celery_app worker "
        "--loglevel=info --pool=solo",
        _ce,
    )

# ── Path setup ────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "server"))

EXPORTS_DIR = str(PROJECT_ROOT / "ninjatrader_exports")

from utils.config_loader import load_configs as _load_configs

# ── Broker (mock fallback when engines.broker is absent) ──────────────────────
try:
    from engines.broker import NinjaTraderClient  # type: ignore
except ImportError as _be:
    logger.warning(
        "NinjaTraderClient not available (%s) — running with mock broker. "
        "Live order routing is disabled.",
        _be,
    )
    class NinjaTraderClient:  # type: ignore
        def __init__(self, **kwargs):
            self.connected = False
        async def connect(self):
            self.connected = True
        def get_status(self):
            return {"connected": self.connected, "mock": True}
        async def place_order(self, *args, **kwargs):
            return {"status": "mock"}

# ── NinjaTrader Bridge ────────────────────────────────────────────────────────
try:
    from ninjatrader_bridge import NinjaTraderBridge  # type: ignore
except ImportError:
    try:
        from server.ninjatrader_bridge import NinjaTraderBridge  # type: ignore
    except ImportError as _nb:
        logger.warning(
            "NinjaTraderBridge not available (%s) — CSV/TCP/pipe data ingestion disabled. "
            "Synthetic bar data will be used instead.",
            _nb,
        )
        NinjaTraderBridge = None  # type: ignore

# ── Global state ──────────────────────────────────────────────────────────────
broker: NinjaTraderClient       = NinjaTraderClient()
nt_bridge: Optional[object]     = None
_ALGO_CONFIGS: List[dict]       = []

# ── WebSocket hub (shared with routers) ───────────────────────────────────────
from server.routers.ws import ws_manager

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="Nexus Algo Terminal Backend", version="3.0.0")

_cors_raw     = os.getenv("CORS_ORIGINS", "http://localhost:3000,app://nexus")
_cors_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ──────────────────────────────────────────────────────────
from server.routers import ws as ws_router
from server.routers import market as market_router
from server.routers import system as system_router
from server.routers import trading as trading_router

app.include_router(ws_router.router)
app.include_router(market_router.router)
app.include_router(system_router.router)
app.include_router(trading_router.router)


# ── App lifecycle ─────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    global nt_bridge, _ALGO_CONFIGS

    logger.info("Nexus Algo Terminal Backend starting...")

    _ALGO_CONFIGS = _load_configs()

    try:
        await broker.connect()
        logger.info("Broker connected: %s", broker.get_status())
    except Exception as exc:
        logger.warning("Broker connect failed: %s", exc)

    if NinjaTraderBridge is not None:
        nt_bridge = NinjaTraderBridge(
            exports_dir=EXPORTS_DIR,
            tcp_server_port=9090,
            enable_pipe=True,
            enable_csv=True,
        )
        nt_bridge.add_callback(_on_nt_data)
        await nt_bridge.start()
        logger.info("NinjaTrader bridge started.")

    asyncio.create_task(_synthetic_data_loop())
    asyncio.create_task(_status_loop())

    logger.info("Startup complete. Serving %d algo configs.", len(_ALGO_CONFIGS))


@app.on_event("shutdown")
async def shutdown_event():
    if nt_bridge:
        await nt_bridge.stop()
    logger.info("Shutdown complete.")


# ── NinjaTrader bridge callback ───────────────────────────────────────────────

async def _on_nt_data(data: dict):
    await ws_manager.broadcast(data)


# ── Background tasks ──────────────────────────────────────────────────────────

async def _synthetic_data_loop():
    """Push synthetic bars when no live NT feed is active."""
    symbol = "ES"
    tf     = "5m"
    base   = 5200.0

    while True:
        await asyncio.sleep(5)
        has_live = (
            nt_bridge is not None
            and (nt_bridge.tcp_server_connections > 0 or nt_bridge.client_connected)
        )
        if has_live:
            continue

        now = int(time.time())
        rng = np.random.default_rng(now)
        close = base + rng.normal(0, 2)
        await ws_manager.broadcast({
            "type":   "bar",
            "symbol": symbol,
            "tf":     tf,
            "bar": {
                "time":   now - (now % 300),
                "open":   round(close - rng.uniform(-1, 1), 2),
                "high":   round(close + abs(rng.normal(0, 0.8)), 2),
                "low":    round(close - abs(rng.normal(0, 0.8)), 2),
                "close":  round(close, 2),
                "volume": int(rng.integers(800, 2000)),
            },
        })


async def _status_loop():
    """Broadcast connection status every 10 seconds."""
    while True:
        await asyncio.sleep(10)
        nt_conn = nt_bridge is not None and (
            nt_bridge.tcp_server_connections > 0
            or nt_bridge.client_connected
            or nt_bridge.pipe_connected
        )
        await ws_manager.broadcast({
            "type":             "status",
            "nt_connected":     nt_conn,
            "broker_connected": broker.get_status().get("connected", False),
            "active_algos":     len([a for a in _ALGO_CONFIGS if a["status"] == "LIVE"]),
            "timestamp":        int(time.time()),
        })


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=False,
        log_level="info",
    )
