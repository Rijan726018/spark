"""
Batch Backtest Runner
Usage:
  python -m engines.runner --algo 06
  python -m engines.runner --all
  python -m engines.runner --status live
"""
import sys
import argparse
import tempfile
import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE))

import yfinance as yf
import pandas as pd
import numpy as np

from engines.strategies import STRATEGY_MAP
from engines.backtest   import run_backtest, compute_stats, save_trades
from algo_configs       import ALGO_CONFIGS


def _get_data(symbol: str, interval: str, period: str) -> pd.DataFrame | None:
    """Download OHLCV from yfinance with caching to temp dir."""
    try:
        yf.set_tz_cache_location(tempfile.gettempdir())
    except Exception:
        pass
    try:
        df = yf.download(symbol, interval=interval, period=period,
                         auto_adjust=True, progress=False)
        if df is None or df.empty:
            return None
        # Flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        print(f"  [download error] {symbol} {interval}/{period}: {e}")
        return None


def run_strategy_on_df(df: pd.DataFrame, engine: str, params: dict) -> pd.DataFrame:
    """Apply a strategy engine to a DataFrame. Returns df with signal/target/stop."""
    fn = STRATEGY_MAP.get(engine)
    if fn is None:
        print(f"  [unknown engine] {engine}")
        df["signal"] = 0
        df["target"] = np.nan
        df["stop"]   = np.nan
        return df
    try:
        return fn(df.copy(), params or {})
    except Exception as e:
        print(f"  [strategy error] {engine}: {e}")
        df["signal"] = 0
        df["target"] = np.nan
        df["stop"]   = np.nan
        return df


def run_algo(algo: dict, verbose: bool = True) -> dict | None:
    """Run a full backtest for one algo config. Returns stats dict or None."""
    algo_id  = algo.get("id", "??")
    name     = algo.get("name", "Unknown")
    symbol   = algo.get("market", "ES=F")
    interval = algo.get("timeframe", "1h")
    period   = algo.get("period", "730d")
    engine   = algo.get("engine", "")
    params   = algo.get("params", {})
    tick_val = algo.get("tick_value", 50.0)
    csv_path = algo.get("csv")

    if verbose:
        print(f"\n[{algo_id}] {name} - {symbol} {interval}/{period} [{engine}]")

    if not engine:
        if verbose:
            print("  [!] No engine defined - skipping")
        return None

    df = _get_data(symbol, interval, period)
    if df is None or df.empty:
        if verbose:
            print("  [!] No data - skipping")
        return None

    df = run_strategy_on_df(df, engine, params)

    trades, equity = run_backtest(df, tick_value=tick_val)
    if not trades:
        if verbose:
            print("  [!] No trades generated")
        return None

    stats = compute_stats(trades, tick_val)
    if verbose:
        print(f"  Trades: {stats['total_trades']} | "
              f"WR: {stats['win_rate']:.1f}% | "
              f"P&L: ${stats['total_pnl']:,.0f} | "
              f"PF: {stats['profit_factor']:.2f}")

    if csv_path:
        save_trades(trades, csv_path)
        if verbose:
            print(f"  Saved -> {csv_path}")

    return stats


def run_all(status_filter: str | None = None, skip_existing: bool = False) -> dict:
    """Run backtests for all (or filtered) algos."""
    results = {}
    algos = ALGO_CONFIGS
    if status_filter:
        algos = [a for a in algos if a.get("status", "").upper() == status_filter.upper()]

    total = len(algos)
    print(f"\n{'='*60}")
    print(f"  BATCH BACKTEST  -  {total} algorithms")
    print(f"{'='*60}")

    for i, algo in enumerate(algos, 1):
        algo_id  = str(algo.get("id", "??"))
        csv_path = algo.get("csv")

        # Skip if results already exist
        if skip_existing and csv_path and Path(csv_path).exists():
            print(f"[{i}/{total}] #{algo_id} - skipping (results exist)")
            continue

        stats = run_algo(algo)
        if stats:
            results[algo_id] = stats

    print(f"\n{'='*60}")
    print(f"  Complete. Ran {len(results)}/{total} algos successfully.")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Algo backtest runner")
    parser.add_argument("--algo",   type=str, help="Run a specific algo by ID")
    parser.add_argument("--all",    action="store_true", help="Run all algos")
    parser.add_argument("--status", type=str, help="Filter by status (LIVE/TESTING/DEV)")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip algos that already have results CSV")
    args = parser.parse_args()

    if args.algo:
        algo = next((a for a in ALGO_CONFIGS if str(a["id"]) == str(args.algo)), None)
        if algo:
            run_algo(algo, verbose=True)
        else:
            print(f"Algo {args.algo} not found in ALGO_CONFIGS")
    elif args.all or args.status:
        run_all(status_filter=args.status, skip_existing=args.skip_existing)
    else:
        parser.print_help()
