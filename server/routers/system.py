"""System / account / algo metadata endpoints."""
import logging
import time
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("nexus.system")

router = APIRouter(prefix="/api", tags=["system"])


# ── Response models ────────────────────────────────────────────────────────────

class AlgoConfig(BaseModel):
    id:           str
    name:         str
    symbol:       str
    tf:           str
    desc:         str
    category:     str
    status:       str
    win_rate:     float
    profit_factor: float
    max_dd:       float
    csv_path:     str
    engine:       str
    params:       dict


class AccountResponse(BaseModel):
    balance:     float
    pnl:         float
    pnl_pct:     float
    daily_pnl:   float
    status:      str
    broker_info: dict
    nt_bridge:   dict


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/algos", response_model=List[AlgoConfig])
async def get_algos():
    from server.main import _ALGO_CONFIGS
    return _ALGO_CONFIGS


@router.get("/algo/{algo_id}", response_model=AlgoConfig)
async def get_algo(algo_id: str):
    from server.main import _ALGO_CONFIGS
    norm = str(algo_id).zfill(3)
    for a in _ALGO_CONFIGS:
        if a["id"] in (norm, algo_id):
            return a
    raise HTTPException(status_code=404, detail=f"Algo {algo_id} not found")


@router.get("/account", response_model=AccountResponse)
async def get_account():
    from server.main import broker, nt_bridge
    return {
        "balance":     124_500.00,
        "pnl":         2_450.00,
        "pnl_pct":     2.01,
        "daily_pnl":   875.00,
        "status":      "LIVE",
        "broker_info": broker.get_status(),
        "nt_bridge":   nt_bridge.get_status() if nt_bridge else {"connected": False},
    }


@router.get("/positions")
async def get_positions():
    return {
        "positions": [
            {"symbol": "ES", "qty": 1, "avg_price": 5198.50, "pnl": 225.00, "side": "LONG"},
        ]
    }


@router.get("/status")
async def get_status():
    from server.main import _ALGO_CONFIGS, broker, nt_bridge
    return {
        "server":       "online",
        "version":      "3.0.0",
        "nt_bridge":    nt_bridge.get_status() if nt_bridge else {"connected": False},
        "broker":       broker.get_status(),
        "algo_count":   len(_ALGO_CONFIGS),
        "active_algos": len([a for a in _ALGO_CONFIGS if a["status"] == "LIVE"]),
        "timestamp":    int(time.time()),
    }


@router.get("/backtest/{algo_id}")
async def run_backtest(algo_id: str):
    import numpy as np
    from server.main import _ALGO_CONFIGS
    from server.routers.market import _generate_synthetic_bars
    norm = str(algo_id).zfill(3)
    cfg  = next((a for a in _ALGO_CONFIGS if a["id"] in (norm, algo_id)), None)
    if cfg is None:
        raise HTTPException(status_code=404, detail=f"Algo {algo_id} not found")

    bars   = _generate_synthetic_bars(cfg.get("symbol", "ES"), 288 * 30)
    equity = 100_000.0
    series = []
    for b in bars:
        equity += np.random.normal(0, 50)
        series.append({"time": b["time"], "value": round(equity, 2), "close": b["close"]})

    return {
        "stats": {
            "total_pnl": round(equity - 100_000, 2),
            "max_dd":    -0.05,
            "win_rate":  cfg.get("win_rate", 55.0),
        },
        "series": series[-500:],
    }
