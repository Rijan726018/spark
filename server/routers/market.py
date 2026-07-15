"""Market data endpoints — bars and trade history."""
import glob
import logging
import os
from pathlib import Path
from typing import List

import numpy as np
from fastapi import APIRouter, HTTPException

logger = logging.getLogger("nexus.market")

router = APIRouter(prefix="/api", tags=["market"])


def _generate_synthetic_bars(symbol: str = "ES", count: int = 500) -> List[dict]:
    import time
    rng  = np.random.default_rng(abs(hash(symbol)) % (2**31))
    base = 5200.0 if symbol in ("ES", "MES") else (18000.0 if symbol in ("NQ", "MNQ") else 5200.0)
    now  = int(time.time())
    bars = []
    close = base
    for i in range(count):
        ts    = now - (count - i) * 300
        ret   = rng.normal(0, 0.002)
        open_ = close
        close = round(open_ * (1 + ret), 2)
        high  = round(max(open_, close) + abs(rng.normal(0, 0.5)), 2)
        low   = round(min(open_, close) - abs(rng.normal(0, 0.5)), 2)
        vol   = int(rng.integers(800, 2500))
        bars.append({"time": ts, "open": open_, "high": high, "low": low,
                     "close": close, "volume": vol})
    return bars


def _generate_synthetic_trades(bars: List[dict], algo_id: str = "001", count: int = 20) -> List[dict]:
    if not bars:
        return []
    rng     = np.random.default_rng(abs(hash(algo_id)) % (2**31))
    indices = sorted(rng.choice(len(bars), size=min(count, len(bars)), replace=False))
    trades  = []
    for i, idx in enumerate(indices):
        bar = bars[idx]
        trades.append({
            "type":    "execution",
            "algo_id": algo_id,
            "symbol":  "ES",
            "side":    "BUY" if i % 2 == 0 else "SELL",
            "price":   bar["close"],
            "qty":     1,
            "time":    bar["time"],
        })
    return trades


def _load_csv_bars(fpath: Path, limit: int) -> List[dict]:
    import csv as _csv
    bars = []
    with open(fpath, "r", encoding="utf-8-sig", newline="") as f:
        reader = _csv.DictReader(f)
        fields = {h.strip().lower(): h for h in (reader.fieldnames or [])}
        def gcol(*names):
            for n in names:
                if n in fields:
                    return fields[n]
            return None
        tc = gcol("time", "datetime", "date", "timestamp")
        oc = gcol("open"); hc = gcol("high"); lc = gcol("low")
        cc = gcol("close", "last"); vc = gcol("volume", "vol")
        if not (tc and oc and hc and lc and cc):
            return []
        from server.ninjatrader_bridge import _parse_timestamp
        for row in reader:
            ts = _parse_timestamp(row[tc].strip())
            if ts is None:
                continue
            try:
                bars.append({
                    "time":   ts,
                    "open":   float(row[oc]), "high": float(row[hc]),
                    "low":    float(row[lc]), "close": float(row[cc]),
                    "volume": int(float(row[vc])) if vc and row.get(vc) else 0,
                })
            except Exception:
                continue
    bars.sort(key=lambda x: x["time"])
    return bars[-limit:]


def _load_trades_csv(fpath: str, algo_id: str, limit: int) -> List[dict]:
    import csv as _csv
    from server.ninjatrader_bridge import _parse_timestamp
    trades = []
    with open(fpath, "r", encoding="utf-8-sig", newline="") as f:
        reader = _csv.DictReader(f)
        fields = {h.strip().lower(): h for h in (reader.fieldnames or [])}
        def gcol(*names):
            for n in names:
                if n in fields:
                    return fields[n]
            return None
        tc = gcol("time", "datetime", "date", "entry time", "entrytime")
        sc = gcol("side", "direction", "type", "action")
        pc = gcol("price", "entry price", "entryprice", "fill price")
        qc = gcol("qty", "quantity", "size", "contracts")
        if not (tc and sc and pc):
            return []
        for row in reader:
            ts = _parse_timestamp(row[tc].strip())
            if ts is None:
                continue
            try:
                trades.append({
                    "type":    "execution",
                    "algo_id": algo_id,
                    "symbol":  "ES",
                    "side":    str(row[sc]).upper().strip(),
                    "price":   float(row[pc]),
                    "qty":     int(float(row[qc])) if qc and row.get(qc) else 1,
                    "time":    ts,
                })
            except Exception:
                continue
    trades.sort(key=lambda x: x["time"], reverse=True)
    return trades[:limit]


@router.get("/bars/{symbol}")
async def get_bars(symbol: str, limit: int = 500, tf: str = "5m"):
    from server.main import nt_bridge, EXPORTS_DIR
    sym = symbol.upper().replace("=F", "")

    if nt_bridge:
        bars = nt_bridge.get_last_bars(sym, limit)
        if bars:
            return {"symbol": sym, "tf": tf, "bars": bars}

    for csv_file in Path(EXPORTS_DIR).glob("*.csv"):
        if sym.lower() in csv_file.stem.lower():
            try:
                bars = _load_csv_bars(csv_file, limit)
                if bars:
                    return {"symbol": sym, "tf": tf, "bars": bars}
            except Exception:
                pass

    bars = _generate_synthetic_bars(sym, limit)
    return {"symbol": sym, "tf": tf, "bars": bars, "synthetic": True}


@router.get("/trades/{algo_id}")
async def get_trades(algo_id: str, limit: int = 100):
    from server.main import _ALGO_CONFIGS
    norm = str(algo_id).zfill(3)
    cfg  = next((a for a in _ALGO_CONFIGS if a["id"] in (norm, algo_id)), None)
    if cfg is None:
        raise HTTPException(status_code=404, detail="Algo not found")

    csv_path = cfg.get("csv_path", "")
    if csv_path and os.path.exists(csv_path):
        try:
            trades = _load_trades_csv(csv_path, algo_id, limit)
            if trades:
                return {"algo_id": algo_id, "trades": trades}
        except Exception as exc:
            logger.debug("Trade CSV load error: %s", exc)

    bars   = _generate_synthetic_bars(cfg.get("symbol", "ES"), 500)
    trades = _generate_synthetic_trades(bars, algo_id, 25)
    return {"algo_id": algo_id, "trades": trades, "synthetic": True}
