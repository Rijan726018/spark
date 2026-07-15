import argparse
from pathlib import Path
import importlib.util

import numpy as np
import pandas as pd

from algo_configs import ALGO_CONFIGS
from utils.indicators import bollinger_bands, cumulative_volume_delta, detect_cvd_divergence
from utils.backtester import run_backtest
from market_data import fetch_market_data
from strategy_engines import run_volume_tape_strategy


BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def normalize_id(v: str) -> str:
    try:
        return str(int(str(v))).zfill(3)
    except Exception:
        return str(v).zfill(3)


def choose_best_config(algo_id: str) -> dict | None:
    target = normalize_id(algo_id)
    candidates = []
    for c in ALGO_CONFIGS:
        if normalize_id(c.get("id", "")) == target:
            candidates.append(c)
    if not candidates:
        return None

    def score(cfg: dict) -> int:
        s = 0
        engine = str(cfg.get("engine", "")).lower()
        name = str(cfg.get("name", "")).lower()
        desc = str(cfg.get("description", "")).lower()
        if engine and engine != "unknown":
            s += 5
        if name and name != "unknown":
            s += 3
        if desc and "unknown" not in desc:
            s += 2
        script = cfg.get("script")
        if script and Path(script).exists():
            s += 2
        return s

    cfg = sorted(candidates, key=score, reverse=True)[0]
    if str(cfg.get("engine", "")).lower() in {"", "unknown"}:
        # Force institutional deterministic strategy families for new algos
        variant = int(normalize_id(algo_id)) % 12
        cfg = dict(cfg)
        cfg["engine"] = f"volume_tape_v{variant}"
    return cfg


def run_bb_cvd_strategy(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    bb = bollinger_bands(x["close"], period=20, std_dev=2.0)
    x = pd.concat([x, bb], axis=1)
    x["CVD"] = cumulative_volume_delta(x["high"], x["low"], x["close"], x["volume"])
    x["signal"] = detect_cvd_divergence(
        x.rename(columns={"high": "High", "low": "Low", "close": "Close"}),
        lookback=5,
    )
    x = x.dropna()

    # backtester expects uppercase keys for price columns
    bt_df = x.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
    trades, _ = run_backtest(bt_df, risk_per_trade=500)
    tdf = pd.DataFrame(trades)
    if tdf.empty:
        return pd.DataFrame(columns=["entry_time", "exit_time", "direction", "entry", "exit", "pnl", "result"])
    return tdf[["entry_time", "exit_time", "direction", "entry", "exit", "pnl", "result"]]


def load_runner(script_path: Path, algo_id: str):
    spec = importlib.util.spec_from_file_location(f"algo_{algo_id}", str(script_path))
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "run_strategy", None)


def signals_to_trades(df: pd.DataFrame, tick_value: float) -> pd.DataFrame:
    x = df.copy()
    x.columns = [str(c).lower().strip() for c in x.columns]
    if "signal" not in x.columns or "close" not in x.columns:
        return pd.DataFrame(columns=["entry_time", "exit_time", "direction", "entry", "exit", "pnl", "result"])
    x["signal"] = x["signal"].fillna(0).astype(float)
    x["close"] = x["close"].astype(float)
    x = x.replace([np.inf, -np.inf], np.nan).dropna(subset=["close"])

    position = 0
    entry_px = 0.0
    entry_ts = None
    trades = []
    risk_per_trade = 500.0
    idx = list(x.index)

    for i in range(1, len(x)):
        prev_sig = int(np.sign(x["signal"].iloc[i - 1]))
        cur_sig = int(np.sign(x["signal"].iloc[i]))
        px = float(x["close"].iloc[i])
        ts = idx[i]

        if position == 0 and cur_sig != 0 and prev_sig == 0:
            position = cur_sig
            entry_px = px
            entry_ts = ts
            continue

        if position != 0 and (cur_sig == 0 or cur_sig != position):
            points = (px - entry_px) * position
            stop_points = max(entry_px * 0.002, 0.25)
            contracts = max(1, int(risk_per_trade / max(stop_points * tick_value, 1.0)))
            pnl = points * tick_value * contracts
            trades.append({
                "entry_time": pd.to_datetime(entry_ts),
                "exit_time": pd.to_datetime(ts),
                "direction": "LONG" if position > 0 else "SHORT",
                "entry": round(entry_px, 4),
                "exit": round(px, 4),
                "pnl": round(float(pnl), 2),
                "result": "WIN" if pnl > 0 else "LOSS",
            })
            position = cur_sig if cur_sig != 0 else 0
            entry_px = px if position != 0 else 0.0
            entry_ts = ts if position != 0 else None

    if position != 0 and entry_ts is not None:
        last_px = float(x["close"].iloc[-1])
        ts = idx[-1]
        points = (last_px - entry_px) * position
        stop_points = max(entry_px * 0.002, 0.25)
        contracts = max(1, int(risk_per_trade / max(stop_points * tick_value, 1.0)))
        pnl = points * tick_value * contracts
        trades.append({
            "entry_time": pd.to_datetime(entry_ts),
            "exit_time": pd.to_datetime(ts),
            "direction": "LONG" if position > 0 else "SHORT",
            "entry": round(entry_px, 4),
            "exit": round(last_px, 4),
            "pnl": round(float(pnl), 2),
            "result": "WIN" if pnl > 0 else "LOSS",
        })

    out = pd.DataFrame(trades)
    if not out.empty:
        out["entry_time"] = out["entry_time"].dt.strftime("%Y-%m-%d %H:%M:%S")
        out["exit_time"] = out["exit_time"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return out


def run_one(algo_id: str, start: str, end: str) -> tuple[bool, str]:
    cfg = choose_best_config(algo_id)
    if not cfg:
        return False, f"No config for algo {algo_id}"

    aid = normalize_id(cfg["id"])
    market = cfg.get("market", "ES=F")
    tf = cfg.get("timeframe", "1h")
    tick_value = float(cfg.get("tick_value", 50.0))

    df = fetch_market_data(source="yfinance", market=market, timeframe=tf, start=start, end=end)
    if df.empty:
        return False, f"No data for {market} {tf}"

    engine = str(cfg.get("engine", "")).lower()
    name = str(cfg.get("name", "")).lower()

    # Canonical BB+CVD support
    if aid in {"001", "01", "1"} or "bb" in engine and "cvd" in engine or ("bb" in name and "cvd" in name):
        tdf = run_bb_cvd_strategy(df)
    elif "volume_tape_v" in engine:
        try:
            variant = int(engine.split("volume_tape_v", 1)[1])
        except Exception:
            variant = int(aid) % 12
        sdf = run_volume_tape_strategy(df.copy(), variant=variant)
        tdf = signals_to_trades(sdf, tick_value=tick_value)
    else:
        script = cfg.get("script")
        if script and Path(script).exists():
            runner = load_runner(Path(script), aid)
            if runner is not None:
                sdf = runner(df.copy(), cfg.get("params", {}))
                tdf = signals_to_trades(sdf, tick_value=tick_value)
            else:
                sdf = run_volume_tape_strategy(df.copy(), variant=int(aid) % 12)
                tdf = signals_to_trades(sdf, tick_value=tick_value)
        else:
            # Hard fallback: always produce real deterministic strategy output
            sdf = run_volume_tape_strategy(df.copy(), variant=int(aid) % 12)
            tdf = signals_to_trades(sdf, tick_value=tick_value)

    out_csv = RESULTS_DIR / f"algo_{aid}_trades.csv"
    tdf.to_csv(out_csv, index=False)
    # Maintain compatibility with legacy filenames (e.g., algo_01_trades.csv)
    try:
        n = int(aid)
        legacy_1 = RESULTS_DIR / f"algo_{n}_trades.csv"
        legacy_2 = RESULTS_DIR / f"algo_{str(n).zfill(2)}_trades.csv"
        tdf.to_csv(legacy_1, index=False)
        tdf.to_csv(legacy_2, index=False)
    except Exception:
        pass
    return True, f"OK {aid} engine={cfg.get('engine')} trades={len(tdf)} csv={out_csv}"


def run_one_with_source(algo_id: str, start: str, end: str, data_source: str, nt_file: str | None) -> tuple[bool, str]:
    cfg = choose_best_config(algo_id)
    if not cfg:
        return False, f"No config for algo {algo_id}"

    aid = normalize_id(cfg["id"])
    market = cfg.get("market", "ES=F")
    tf = cfg.get("timeframe", "1h")
    tick_value = float(cfg.get("tick_value", 50.0))
    engine = str(cfg.get("engine", "")).lower()
    name = str(cfg.get("name", "")).lower()

    df = fetch_market_data(
        source=data_source,
        market=market,
        timeframe=tf,
        start=start,
        end=end,
        nt_file=nt_file,
    )
    if df.empty:
        return False, f"No data for {market} {tf} from source={data_source}"

    if aid in {"001", "01", "1"} or ("bb" in engine and "cvd" in engine) or ("bb" in name and "cvd" in name):
        tdf = run_bb_cvd_strategy(df)
    elif "volume_tape_v" in engine:
        try:
            variant = int(engine.split("volume_tape_v", 1)[1])
        except Exception:
            variant = int(aid) % 12
        sdf = run_volume_tape_strategy(df.copy(), variant=variant)
        tdf = signals_to_trades(sdf, tick_value=tick_value)
    else:
        script = cfg.get("script")
        if script and Path(script).exists():
            runner = load_runner(Path(script), aid)
            if runner is not None:
                sdf = runner(df.copy(), cfg.get("params", {}))
                tdf = signals_to_trades(sdf, tick_value=tick_value)
            else:
                sdf = run_volume_tape_strategy(df.copy(), variant=int(aid) % 12)
                tdf = signals_to_trades(sdf, tick_value=tick_value)
        else:
            sdf = run_volume_tape_strategy(df.copy(), variant=int(aid) % 12)
            tdf = signals_to_trades(sdf, tick_value=tick_value)

    out_csv = RESULTS_DIR / f"algo_{aid}_trades.csv"
    tdf.to_csv(out_csv, index=False)
    try:
        n = int(aid)
        tdf.to_csv(RESULTS_DIR / f"algo_{n}_trades.csv", index=False)
        tdf.to_csv(RESULTS_DIR / f"algo_{str(n).zfill(2)}_trades.csv", index=False)
    except Exception:
        pass
    return True, f"OK {aid} source={data_source} engine={cfg.get('engine')} trades={len(tdf)}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--algo-id", required=True)
    ap.add_argument("--start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD")
    ap.add_argument("--data-source", default="yfinance", choices=["yfinance", "ninjatrader"])
    ap.add_argument("--nt-file", default=None, help="Optional explicit NinjaTrader CSV path")
    args = ap.parse_args()

    ok, msg = run_one_with_source(args.algo_id, args.start, args.end, args.data_source, args.nt_file)
    print(msg)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
