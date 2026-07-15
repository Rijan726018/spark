"""
Generic Backtester
Works on any DataFrame that has: signal (+1/-1/0), target, stop columns.
"""
import numpy as np
import pandas as pd
from pathlib import Path


def run_backtest(df: pd.DataFrame, tick_value: float = 50.0,
                 risk_per_trade: float = 500.0) -> tuple[list, list]:
    """
    Bar-by-bar backtester.

    Entry: signal fires on bar N → enter at open of bar N+1
    Exit: target or stop hit during the bar (checks high/low)
    Sizing: risk_per_trade / (risk_points * tick_value), min 1 contract

    Parameters
    ----------
    df          : OHLCV + signal + target + stop columns
    tick_value  : $ per full point (ES=50, NQ=20, YM=5, GC=100, CL=1000 ...)
    risk_per_trade : $ risked per trade for sizing

    Returns
    -------
    trades      : list of trade dicts
    equity_curve: list of cumulative P&L at each bar
    """
    trades      = []
    position    = None
    equity      = 0.0
    equity_curve = [0.0]

    highs   = df["High"].values
    lows    = df["Low"].values
    opens   = df["Open"].values
    signals = df["signal"].fillna(0).values
    targets = df["target"].values
    stops   = df["stop"].values

    for i in range(1, len(df)):
        # ── Manage open position ───────────────────────────────────────────
        if position is not None:
            d   = position["direction"]
            tgt = position["target"]
            stp = position["stop"]
            qty = position["contracts"]
            ep  = position["entry"]

            hit_tgt = (d == 1  and highs[i] >= tgt) or (d == -1 and lows[i]  <= tgt)
            hit_stp = (d == 1  and lows[i]  <= stp) or (d == -1 and highs[i] >= stp)

            if hit_tgt or hit_stp:
                xp   = tgt if hit_tgt else stp
                pnl  = (xp - ep) * d * qty * tick_value
                equity += pnl
                trades.append({
                    "entry_time": position["entry_time"],
                    "exit_time":  df.index[i],
                    "direction":  "LONG" if d == 1 else "SHORT",
                    "entry":      ep,
                    "exit":       xp,
                    "target":     tgt,
                    "stop":       stp,
                    "contracts":  qty,
                    "pnl":        pnl,
                    "result":     "WIN" if hit_tgt else "LOSS",
                })
                position = None

        # ── New entry signal ───────────────────────────────────────────────
        if position is None and signals[i - 1] != 0:
            d   = int(signals[i - 1])
            ep  = opens[i]
            tgt = float(targets[i - 1]) if not np.isnan(targets[i - 1]) else (
                ep + 10 if d == 1 else ep - 10)
            stp = float(stops[i - 1])   if not np.isnan(stops[i - 1])   else (
                ep - 5  if d == 1 else ep + 5)

            risk_pts = abs(ep - stp)
            if risk_pts > 0:
                qty = max(1, int(risk_per_trade / (risk_pts * tick_value)))
            else:
                qty = 1

            position = {
                "entry_time": df.index[i],
                "entry":      ep,
                "direction":  d,
                "target":     tgt,
                "stop":       stp,
                "contracts":  qty,
            }

        equity_curve.append(equity)

    return trades, equity_curve


def compute_stats(trades: list, tick_value: float = 50.0) -> dict:
    """Compute summary statistics from a trades list."""
    if not trades:
        return {}
    df  = pd.DataFrame(trades)
    wins   = df[df["result"] == "WIN"]
    losses = df[df["result"] == "LOSS"]
    gp  = wins["pnl"].sum()   if len(wins)   else 0.0
    gl  = losses["pnl"].sum() if len(losses) else 0.0
    pf  = abs(gp / gl)        if gl != 0     else 0.0
    eq  = df["pnl"].cumsum()
    dd  = (eq - eq.cummax()).min()
    return {
        "total_trades":  len(df),
        "win_rate":      len(wins) / len(df) * 100,
        "total_pnl":     df["pnl"].sum(),
        "avg_win":       wins["pnl"].mean()   if len(wins)   else 0.0,
        "avg_loss":      losses["pnl"].mean() if len(losses) else 0.0,
        "gross_profit":  gp,
        "gross_loss":    gl,
        "profit_factor": pf,
        "max_drawdown":  dd,
    }


def save_trades(trades: list, csv_path: str):
    """Save trades list to CSV."""
    if not trades:
        return
    Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(trades).to_csv(csv_path, index=False)
