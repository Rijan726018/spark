"""PAMM trade gateway and task polling endpoints."""
import logging
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator

logger = logging.getLogger("nexus.trading")

router = APIRouter(prefix="/api", tags=["trading"])


# ── Request model ──────────────────────────────────────────────────────────────

class TradeSignal(BaseModel):
    symbol:   str   = Field(..., description="Futures symbol, e.g. 'ES'")
    action:   str   = Field(..., description="'Buy' or 'Sell'")
    quantity: float = Field(..., gt=0, description="Master contract size (positive)")

    @validator("action")
    def validate_action(cls, v):
        normalized = v.capitalize()
        if normalized not in ("Buy", "Sell"):
            raise ValueError("action must be 'Buy' or 'Sell'")
        return normalized

    @validator("symbol")
    def validate_symbol(cls, v):
        sym = v.upper().replace("=F", "").strip()
        if not sym:
            raise ValueError("symbol cannot be empty")
        return sym


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/trade")
async def trigger_pamm_trade(signal: TradeSignal):
    """
    Receives a master signal from the React dashboard and fans it out to all
    sub-accounts via Celery workers.  Returns immediately; the frontend may poll
    /api/task/{task_id} for individual results.
    """
    from server.main import CELERY_AVAILABLE
    from server.routers.ws import ws_manager

    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail=(
                "Celery worker is not running. "
                "Start it with: python -m celery -A backend.router.celery_app "
                "worker --loglevel=info --pool=solo"
            ),
        )

    from backend.router.allocator import process_master_signal
    import asyncio

    signal_str = f"{signal.action} {signal.quantity} {signal.symbol} Contract at Market"

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, process_master_signal, signal_str)

    logger.info("PAMM signal dispatched: %s", signal_str)

    await ws_manager.broadcast({
        "type":      "pamm_signal",
        "symbol":    signal.symbol,
        "action":    signal.action,
        "quantity":  signal.quantity,
        "signal":    signal_str,
        "timestamp": int(time.time()),
    })

    return {
        "status":  "queued",
        "signal":  signal_str,
        "message": "Master signal fanned out to all eligible sub-accounts via Celery.",
    }


@router.get("/task/{task_id}")
async def get_task_result(task_id: str):
    """Poll a specific Celery task by ID."""
    from server.main import CELERY_AVAILABLE, _celery_app  # noqa: F401

    if not CELERY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Celery not available")

    from celery.result import AsyncResult
    result = AsyncResult(task_id, app=_celery_app)

    return {
        "task_id": task_id,
        "status":  result.status,
        "result":  result.result if result.ready() else None,
        "ready":   result.ready(),
    }
