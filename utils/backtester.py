import pandas as pd
import numpy as np


ES_TICK_VALUE = 50.0   # $50 per full point on ES


def run_backtest(df: pd.DataFrame, risk_per_trade: float = 500.0) -> tuple[list, list]:
    """
    Simple bar-by-bar backtester.

    Entry rules
    -----------
    - Signal fires on bar N → enter at open of bar N+1
    - Long:  target = BB_upper at signal bar, stop = BB_lower minus 10% of band width
    - Short: target = BB_lower at signal bar, stop = BB_upper plus  10% of band width

    Sizing
    ------
    - risk_per_trade: max dollar risk per trade
    - Contracts = floor(risk_per_trade / (risk_points * ES_TICK_VALUE)), min 1

    Returns
    -------
    trades      : list of trade dicts
    equity_curve: list of equity values (one per bar)
    """
    trades = []
    position = None
    equity = 0.0          # track P&L only (not absolute capital)
    equity_curve = [0.0]

    highs  = df["High"].values
    lows   = df["Low"].values
    opens  = df["Open"].values
    closes = df["Close"].values
    signals = df["signal"].values
    bb_upper = df["BB_upper"].values
    bb_lower = df["BB_lower"].values

    for i in range(1, len(df)):
        current_equity = equity

        # ── Manage open position ────────────────────────────────────────────
        if position is not None:
            direction  = position["direction"]
            target     = position["target"]
            stop       = position["stop"]
            contracts  = position["contracts"]
            entry_p    = position["entry"]

            hit_target = (direction == 1  and highs[i] >= target) or \
                         (direction == -1 and lows[i]  <= target)
            hit_stop   = (direction == 1  and lows[i]  <= stop)  or \
                         (direction == -1 and highs[i] >= stop)

            if hit_target or hit_stop:
                exit_price = target if hit_target else stop
                pnl = (exit_price - entry_p) * direction * contracts * ES_TICK_VALUE
                equity += pnl
                trades.append({
                    "entry_time": position["entry_time"],
                    "exit_time":  df.index[i],
                    "direction":  "LONG" if direction == 1 else "SHORT",
                    "entry":      entry_p,
                    "exit":       exit_price,
                    "target":     target,
                    "stop":       stop,
                    "contracts":  contracts,
                    "pnl":        pnl,
                    "result":     "WIN" if hit_target else "LOSS",
                })
                position = None

        # ── Check for new entry (only one position at a time) ───────────────
        if position is None and signals[i - 1] != 0:
            direction  = int(signals[i - 1])
            entry_p    = opens[i]
            band_width = bb_upper[i - 1] - bb_lower[i - 1]

            if direction == 1:     # LONG
                target = bb_upper[i - 1]
                stop   = bb_lower[i - 1] - band_width * 0.1
            else:                  # SHORT
                target = bb_lower[i - 1]
                stop   = bb_upper[i - 1] + band_width * 0.1

            risk_points = abs(entry_p - stop)
            if risk_points > 0:
                contracts = max(1, int(risk_per_trade / (risk_points * ES_TICK_VALUE)))
            else:
                contracts = 1

            position = {
                "entry_time": df.index[i],
                "entry":      entry_p,
                "direction":  direction,
                "target":     target,
                "stop":       stop,
                "contracts":  contracts,
            }

        equity_curve.append(equity)

    return trades, equity_curve


def print_stats(trades: list, equity_curve: list) -> pd.DataFrame | None:
    if not trades:
        print("No trades taken in this period.")
        return None

    df_t = pd.DataFrame(trades)
    wins   = df_t[df_t["result"] == "WIN"]
    losses = df_t[df_t["result"] == "LOSS"]

    win_rate      = len(wins) / len(df_t) * 100
    total_pnl     = df_t["pnl"].sum()
    avg_win       = wins["pnl"].mean()   if len(wins)   else 0.0
    avg_loss      = losses["pnl"].mean() if len(losses) else 0.0
    gross_profit  = wins["pnl"].sum()    if len(wins)   else 0.0
    gross_loss    = losses["pnl"].sum()  if len(losses) else 0.0
    profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else float("inf")

    eq = pd.Series(equity_curve)
    peak     = eq.cummax()
    drawdown = (eq - peak)
    max_dd   = drawdown.min()

    print(f"\n{'='*50}")
    print(f"  ALGO 01 — BB + CVD DIVERGENCE  |  ES FUTURES")
    print(f"{'='*50}")
    print(f"  Total Trades   : {len(df_t)}")
    print(f"  Win Rate       : {win_rate:.1f}%")
    print(f"  Total P&L      : ${total_pnl:>10,.0f}")
    print(f"  Avg Win        : ${avg_win:>10,.0f}")
    print(f"  Avg Loss       : ${avg_loss:>10,.0f}")
    print(f"  Profit Factor  : {profit_factor:.2f}")
    print(f"  Max Drawdown   : ${max_dd:>10,.0f}")
    print(f"{'='*50}\n")

    return df_t
