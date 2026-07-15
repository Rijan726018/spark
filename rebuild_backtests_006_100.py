import json
from pathlib import Path
import importlib.util

import numpy as np
import pandas as pd
import yfinance as yf

from algo_configs import ALGO_CONFIGS

BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "results"
CACHE_DIR = BASE_DIR / "data_cache"
RESULTS_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)


def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    out = df.copy()
    out.columns = [str(c).lower().strip() for c in out.columns]
    expected = ["open", "high", "low", "close", "volume"]
    for col in expected:
        if col not in out.columns:
            if col == "volume":
                out[col] = 0.0
            else:
                return pd.DataFrame()
    out = out[expected]
    out = out.dropna(subset=["open", "high", "low", "close"])
    return out


def get_large_sample_period(interval: str) -> str:
    # yfinance practical limits
    if interval in {"1m", "2m", "5m", "15m", "30m", "60m", "90m"}:
        return "60d"
    if interval in {"1h"}:
        return "730d"
    if interval in {"1d", "5d", "1wk", "1mo"}:
        return "5y"
    return "730d"


def get_market_data(ticker: str, interval: str) -> pd.DataFrame | None:
    period = get_large_sample_period(interval)
    cache_file = CACHE_DIR / f"{ticker.replace('=', '_')}_{interval}_{period}.csv"
    if cache_file.exists():
        try:
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            df = normalize_ohlcv(df)
            if not df.empty:
                return df
        except Exception:
            pass

    try:
        df = yf.download(ticker, period=period, interval=interval, auto_adjust=False, progress=False)
        df = normalize_ohlcv(df)
        if df.empty:
            # Fallback to daily for reliability
            df = yf.download(ticker, period="5y", interval="1d", auto_adjust=False, progress=False)
            df = normalize_ohlcv(df)
        if df.empty:
            return None
        df.to_csv(cache_file)
        return df
    except Exception:
        return None


def load_strategy(script_path: Path, algo_id: str):
    spec = importlib.util.spec_from_file_location(f"algo_{algo_id}", str(script_path))
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "run_strategy"):
        return None
    return module.run_strategy


def signals_to_trades(df: pd.DataFrame, tick_value: float = 50.0, risk_per_trade: float = 500.0) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).lower().strip() for c in out.columns]
    if "signal" not in out.columns or "close" not in out.columns:
        return pd.DataFrame(columns=["entry_time", "exit_time", "direction", "entry", "exit", "pnl", "result"])

    out["signal"] = out["signal"].fillna(0).astype(float)
    out["close"] = out["close"].astype(float)
    out = out.replace([np.inf, -np.inf], np.nan).dropna(subset=["close"])

    trades = []
    position = 0
    entry_price = None
    entry_time = None

    idx = list(out.index)
    for i in range(1, len(out)):
        prev_sig = int(np.sign(out["signal"].iloc[i - 1]))
        cur_sig = int(np.sign(out["signal"].iloc[i]))
        px = float(out["close"].iloc[i])
        ts = idx[i]

        # Enter on transition 0 -> +/-1
        if position == 0 and cur_sig != 0 and prev_sig == 0:
            position = cur_sig
            entry_price = px
            entry_time = ts
            continue

        # Exit on flip or flat
        if position != 0 and (cur_sig == 0 or cur_sig != position):
            exit_price = px
            points = (exit_price - entry_price) * position
            stop_points = max(entry_price * 0.002, 0.25)
            contracts = max(1, int(risk_per_trade / max(stop_points * tick_value, 1.0)))
            pnl = points * tick_value * contracts
            trades.append({
                "entry_time": pd.to_datetime(entry_time),
                "exit_time": pd.to_datetime(ts),
                "direction": "LONG" if position > 0 else "SHORT",
                "entry": round(entry_price, 4),
                "exit": round(exit_price, 4),
                "pnl": round(float(pnl), 2),
                "result": "WIN" if pnl > 0 else "LOSS",
            })
            # Handle immediate re-entry on flip
            position = cur_sig if cur_sig != 0 else 0
            entry_price = px if position != 0 else None
            entry_time = ts if position != 0 else None

    # Close any open trade on last bar
    if position != 0 and entry_price is not None and entry_time is not None:
        last_px = float(out["close"].iloc[-1])
        last_ts = idx[-1]
        points = (last_px - entry_price) * position
        stop_points = max(entry_price * 0.002, 0.25)
        contracts = max(1, int(risk_per_trade / max(stop_points * tick_value, 1.0)))
        pnl = points * tick_value * contracts
        trades.append({
            "entry_time": pd.to_datetime(entry_time),
            "exit_time": pd.to_datetime(last_ts),
            "direction": "LONG" if position > 0 else "SHORT",
            "entry": round(entry_price, 4),
            "exit": round(last_px, 4),
            "pnl": round(float(pnl), 2),
            "result": "WIN" if pnl > 0 else "LOSS",
        })

    tdf = pd.DataFrame(trades)
    if not tdf.empty:
        tdf["entry_time"] = tdf["entry_time"].dt.strftime("%Y-%m-%d %H:%M:%S")
        tdf["exit_time"] = tdf["exit_time"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return tdf


def get_unique_algos_006_100():
    chosen = {}
    for cfg in ALGO_CONFIGS:
        try:
            aid = int(str(cfg.get("id", "0")))
        except ValueError:
            continue
        if aid < 6 or aid > 100:
            continue
        cur = chosen.get(aid)
        if cur is None:
            chosen[aid] = cfg
            continue
        # Prefer non-unknown engine
        if str(cur.get("engine", "")).lower() == "unknown" and str(cfg.get("engine", "")).lower() != "unknown":
            chosen[aid] = cfg
    return [chosen[k] for k in sorted(chosen.keys())]


def main():
    algos = get_unique_algos_006_100()
    if not algos:
        print("No algo configs found in range 006-100.")
        return

    markets_needed = {(a["market"], a["timeframe"]) for a in algos}
    market_cache = {}
    for ticker, tf in sorted(markets_needed):
        df = get_market_data(ticker, tf)
        market_cache[(ticker, tf)] = df
        bars = len(df) if df is not None else 0
        print(f"DATA {ticker} {tf}: {bars} bars")

    summary = {}
    ok = 0
    fail = 0
    for cfg in algos:
        algo_id = str(cfg["id"]).zfill(3)
        script = Path(cfg["script"])
        if not script.exists():
            fail += 1
            print(f"SKIP {algo_id}: script missing")
            continue

        df = market_cache.get((cfg["market"], cfg["timeframe"]))
        if df is None or df.empty:
            fail += 1
            print(f"SKIP {algo_id}: no market data")
            continue

        runner = load_strategy(script, algo_id)
        if runner is None:
            fail += 1
            print(f"SKIP {algo_id}: invalid strategy module")
            continue

        try:
            sdf = runner(df.copy(), cfg.get("params", {}))
            tdf = signals_to_trades(
                sdf,
                tick_value=float(cfg.get("tick_value", 50.0)),
                risk_per_trade=500.0,
            )
            out_csv = RESULTS_DIR / f"algo_{algo_id}_trades.csv"
            tdf.to_csv(out_csv, index=False)

            if not tdf.empty:
                wins = (tdf["result"] == "WIN").sum()
                losses = (tdf["result"] == "LOSS").sum()
                gp = float(tdf.loc[tdf["pnl"] > 0, "pnl"].sum())
                gl = float(tdf.loc[tdf["pnl"] < 0, "pnl"].sum())
                pf = abs(gp / gl) if gl != 0 else 0.0
                summary[algo_id] = {
                    "trades": int(len(tdf)),
                    "win_rate": float((wins / len(tdf)) * 100.0),
                    "total_pnl": float(tdf["pnl"].sum()),
                    "profit_factor": float(pf),
                }
            else:
                summary[algo_id] = {"trades": 0, "win_rate": 0.0, "total_pnl": 0.0, "profit_factor": 0.0}
            ok += 1
            print(f"DONE {algo_id}: trades={summary[algo_id]['trades']} pnl={summary[algo_id]['total_pnl']:.2f}")
        except Exception as e:
            fail += 1
            print(f"FAIL {algo_id}: {e}")

    with open(RESULTS_DIR / "summary_stats_006_100.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"COMPLETE ok={ok} fail={fail} total={len(algos)}")


if __name__ == "__main__":
    main()
