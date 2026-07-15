"""
ALGO 02 — VWAP Reversion  |  ES Futures
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import tempfile

from utils.indicators import bollinger_bands  # not used but keeps import pattern consistent
from utils.backtester  import print_stats      # reuse the stats printer

# ── Config ────────────────────────────────────────────────────────────────────
SYMBOL         = "ES=F"
INTERVAL       = "5m"
PERIOD         = "60d"
VWAP_STD_MULT1 = 1.5    # inner bands
VWAP_STD_MULT2 = 2.5    # outer bands (entry trigger)
RISK_PER_TRADE = 500     # max $ risk per trade
ES_TICK_VALUE  = 50.0    # $50 per full point
RESULTS_DIR    = os.path.join(os.path.dirname(__file__), "..", "results")


# ── Data ──────────────────────────────────────────────────────────────────────
def fetch_data() -> pd.DataFrame:
    print(f"Fetching {SYMBOL} {INTERVAL} bars ({PERIOD})...")

    try:
        yf.set_tz_cache_location(tempfile.gettempdir())
    except Exception:
        pass

    df = yf.download(SYMBOL, period=PERIOD, interval=INTERVAL,
                     auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.dropna()

    if df.empty:
        raise RuntimeError(
            f"No data returned for {SYMBOL}. "
            "Check your internet connection or try INTERVAL='1h' and PERIOD='730d'."
        )

    print(f"  Loaded {len(df):,} bars  ({df.index[0]}  to  {df.index[-1]})")
    return df


# ── Indicators ────────────────────────────────────────────────────────────────
def compute_intraday_vwap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes intraday VWAP that resets each calendar day, plus standard
    deviation bands at 1.5x and 2.5x.

    VWAP  = sum(tp * vol) / sum(vol)
    std   = sqrt( sum((tp - vwap)^2 * vol) / sum(vol) )

    Returns a copy of df with new columns:
        vwap, vwap_std,
        vwap_upper1, vwap_lower1,
        vwap_upper2, vwap_lower2
    """
    df = df.copy()

    # Typical price
    df["tp"] = (df["High"] + df["Low"] + df["Close"]) / 3.0

    # Date key for daily grouping (timezone-aware index safe)
    df["_date"] = df.index.normalize()

    vwap       = np.full(len(df), np.nan)
    vwap_std   = np.full(len(df), np.nan)

    tp_arr  = df["tp"].values
    vol_arr = df["Volume"].values
    dates   = df["_date"].values

    # Walk through bars, accumulate per-day running sums
    cum_tp_vol  = 0.0
    cum_vol     = 0.0
    cum_tp2_vol = 0.0   # sum((tp - vwap)^2 * vol) — recalculated below
    current_day = None

    # We need two passes per day to compute std (need vwap first).
    # Strategy: group by date, process each day's slice.
    date_col = pd.Series(df["_date"].values, index=df.index)
    unique_dates = date_col.unique()

    for day in unique_dates:
        mask = date_col == day
        idx  = np.where(mask)[0]

        tp_day  = tp_arr[idx]
        vol_day = vol_arr[idx]

        # Cumulative sums within the day
        cum_tp_vol_day  = np.cumsum(tp_day  * vol_day)
        cum_vol_day     = np.cumsum(vol_day)

        # Avoid divide-by-zero on bars with zero volume
        with np.errstate(invalid="ignore", divide="ignore"):
            vwap_day = np.where(cum_vol_day > 0,
                                cum_tp_vol_day / cum_vol_day,
                                tp_day)

        # Variance: cumulative weighted variance
        # Var = sum((tp - vwap)^2 * vol) / sum(vol)
        # We store running weighted sum of squared deviations
        cum_sq_dev = np.cumsum((tp_day - vwap_day) ** 2 * vol_day)
        with np.errstate(invalid="ignore", divide="ignore"):
            var_day = np.where(cum_vol_day > 0,
                               cum_sq_dev / cum_vol_day,
                               0.0)
        std_day = np.sqrt(var_day)

        vwap[idx]     = vwap_day
        vwap_std[idx] = std_day

    df["vwap"]     = vwap
    df["vwap_std"] = vwap_std

    df["vwap_upper1"] = df["vwap"] + VWAP_STD_MULT1 * df["vwap_std"]
    df["vwap_lower1"] = df["vwap"] - VWAP_STD_MULT1 * df["vwap_std"]
    df["vwap_upper2"] = df["vwap"] + VWAP_STD_MULT2 * df["vwap_std"]
    df["vwap_lower2"] = df["vwap"] - VWAP_STD_MULT2 * df["vwap_std"]

    df = df.drop(columns=["tp", "_date"])
    return df


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    LONG  signal: bar N close crosses below lower band 2
                  AND bar N+1 close > bar N close (recovery starting)
    SHORT signal: bar N close crosses above upper band 2
                  AND bar N+1 close < bar N close (rejection starting)

    Signal is stored on bar N (the confirmation bar, N+1), placed as
    signal[N+1] = direction so the backtester enters at open of N+2.

    Actually, to match algo_01 convention exactly:
      - signal fires on the BAR we detect the setup
      - backtester enters at open of the NEXT bar

    Implementation:
      We look at bar i-1 (cross bar) and bar i (confirmation bar).
      If conditions met, signal[i] = direction.
      Backtester sees signal[i] != 0 and enters at open[i+1].

    Also stores target/stop per signal bar in separate columns.

    Filter: skip bars where vwap_std == 0 (first bar of each day).
    """
    df = df.copy()
    df["signal"]        = 0
    df["sig_target"]    = np.nan
    df["sig_stop"]      = np.nan

    closes  = df["Close"].values
    upper2  = df["vwap_upper2"].values
    lower2  = df["vwap_lower2"].values
    vwap    = df["vwap"].values
    std     = df["vwap_std"].values

    for i in range(1, len(df)):
        # Skip first bar of day (std == 0) or current bar
        if std[i] == 0 or std[i - 1] == 0:
            continue

        # LONG: bar i-1 closed below lower2, bar i close > bar i-1 close
        if closes[i - 1] < lower2[i - 1] and closes[i] > closes[i - 1]:
            target = vwap[i - 1]
            band_dist = vwap[i - 1] - lower2[i - 1]
            stop = lower2[i - 1] - 0.3 * band_dist
            if target > stop and band_dist > 0:
                df.iloc[i, df.columns.get_loc("signal")]     = 1
                df.iloc[i, df.columns.get_loc("sig_target")] = target
                df.iloc[i, df.columns.get_loc("sig_stop")]   = stop

        # SHORT: bar i-1 closed above upper2, bar i close < bar i-1 close
        elif closes[i - 1] > upper2[i - 1] and closes[i] < closes[i - 1]:
            target = vwap[i - 1]
            band_dist = upper2[i - 1] - vwap[i - 1]
            stop = upper2[i - 1] + 0.3 * band_dist
            if target < stop and band_dist > 0:
                df.iloc[i, df.columns.get_loc("signal")]     = -1
                df.iloc[i, df.columns.get_loc("sig_target")] = target
                df.iloc[i, df.columns.get_loc("sig_stop")]   = stop

    return df


# ── Backtester ────────────────────────────────────────────────────────────────
def run_backtest(df: pd.DataFrame, risk_per_trade: float = 500.0) -> tuple[list, list]:
    """
    Inline backtester for VWAP reversion.

    Entry  : signal on bar N → enter at open of bar N+1
    Target : VWAP at signal bar (stored in sig_target)
    Stop   : extended band level (stored in sig_stop)
    Sizing : contracts = max(1, int(risk_per_trade / (risk_points * ES_TICK_VALUE)))
    """
    trades       = []
    position     = None
    equity       = 0.0
    equity_curve = [0.0]

    highs    = df["High"].values
    lows     = df["Low"].values
    opens    = df["Open"].values
    signals  = df["signal"].values
    targets  = df["sig_target"].values
    stops    = df["sig_stop"].values

    for i in range(1, len(df)):
        # ── Manage open position ────────────────────────────────────────────
        if position is not None:
            direction = position["direction"]
            target    = position["target"]
            stop      = position["stop"]
            contracts = position["contracts"]
            entry_p   = position["entry"]

            hit_target = (direction ==  1 and highs[i] >= target) or \
                         (direction == -1 and lows[i]  <= target)
            hit_stop   = (direction ==  1 and lows[i]  <= stop)   or \
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

        # ── Check for new entry (no pyramid) ───────────────────────────────
        if position is None and signals[i - 1] != 0:
            direction   = int(signals[i - 1])
            entry_p     = opens[i]
            sig_target  = targets[i - 1]
            sig_stop    = stops[i - 1]

            if np.isnan(sig_target) or np.isnan(sig_stop):
                equity_curve.append(equity)
                continue

            risk_points = abs(entry_p - sig_stop)
            if risk_points > 0:
                contracts = max(1, int(risk_per_trade / (risk_points * ES_TICK_VALUE)))
            else:
                contracts = 1

            position = {
                "entry_time": df.index[i],
                "entry":      entry_p,
                "direction":  direction,
                "target":     sig_target,
                "stop":       sig_stop,
                "contracts":  contracts,
            }

        equity_curve.append(equity)

    return trades, equity_curve


# ── Stats ─────────────────────────────────────────────────────────────────────
def print_algo02_stats(trades: list, equity_curve: list) -> pd.DataFrame | None:
    if not trades:
        print("No trades taken in this period.")
        return None

    df_t   = pd.DataFrame(trades)
    wins   = df_t[df_t["result"] == "WIN"]
    losses = df_t[df_t["result"] == "LOSS"]

    win_rate      = len(wins) / len(df_t) * 100
    total_pnl     = df_t["pnl"].sum()
    avg_win       = wins["pnl"].mean()   if len(wins)   else 0.0
    avg_loss      = losses["pnl"].mean() if len(losses) else 0.0
    gross_profit  = wins["pnl"].sum()    if len(wins)   else 0.0
    gross_loss    = losses["pnl"].sum()  if len(losses) else 0.0
    profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else float("inf")

    eq       = pd.Series(equity_curve)
    peak     = eq.cummax()
    drawdown = eq - peak
    max_dd   = drawdown.min()

    print(f"\n{'='*50}")
    print(f"  ALGO 02 — VWAP REVERSION  |  ES FUTURES")
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


# ── Chart ─────────────────────────────────────────────────────────────────────
def plot(df: pd.DataFrame, equity_curve: list, trades_df: pd.DataFrame | None):
    fig, axes = plt.subplots(3, 1, figsize=(16, 11),
                             gridspec_kw={"height_ratios": [3, 1.5, 1.5]})
    fig.patch.set_facecolor("#0d0d1a")

    colors = {
        "bg":     "#0d0d1a",
        "panel":  "#12122a",
        "text":   "#e0e0e0",
        "close":  "#b0bec5",
        "vwap":   "#ffd600",      # amber/gold VWAP line
        "band1":  "#ff8f00",      # inner band — orange
        "band2":  "#e65100",      # outer band — deep orange
        "fill1":  "#ff8f00",
        "fill2":  "#e65100",
        "up":     "#00e676",
        "down":   "#ff1744",
        "std":    "#ffa000",
        "equity": "#ffd600",
        "mid":    "#546e7a",
    }

    # ── Subplot 1: Price + VWAP + Bands ───────────────────────────────────────
    ax1 = axes[0]
    ax1.set_facecolor(colors["panel"])

    ax1.plot(df.index, df["Close"],       color=colors["close"], lw=0.7,  label="ES Close")
    ax1.plot(df.index, df["vwap"],        color=colors["vwap"],  lw=1.2,  label="VWAP")
    ax1.plot(df.index, df["vwap_upper1"], color=colors["band1"], lw=0.8,  ls="--", label="VWAP ±1.5σ")
    ax1.plot(df.index, df["vwap_lower1"], color=colors["band1"], lw=0.8,  ls="--")
    ax1.plot(df.index, df["vwap_upper2"], color=colors["band2"], lw=0.9,  ls="--", label="VWAP ±2.5σ")
    ax1.plot(df.index, df["vwap_lower2"], color=colors["band2"], lw=0.9,  ls="--")

    ax1.fill_between(df.index, df["vwap_upper1"], df["vwap_lower1"],
                     alpha=0.05, color=colors["fill1"])
    ax1.fill_between(df.index, df["vwap_upper2"], df["vwap_lower2"],
                     alpha=0.04, color=colors["fill2"])

    # Signal markers
    longs  = df[df["signal"] ==  1]
    shorts = df[df["signal"] == -1]
    ax1.scatter(longs.index,  longs["Close"],  marker="^", color=colors["up"],
                s=60, zorder=5, label="Long signal")
    ax1.scatter(shorts.index, shorts["Close"], marker="v", color=colors["down"],
                s=60, zorder=5, label="Short signal")

    ax1.set_title("ALGO 02 — VWAP Reversion  |  ES Futures  (5m)",
                  color=colors["text"], fontsize=12, pad=8)
    ax1.legend(fontsize=7, loc="upper left",
               facecolor=colors["bg"], labelcolor=colors["text"])

    # ── Subplot 2: VWAP Std ────────────────────────────────────────────────────
    ax2 = axes[1]
    ax2.set_facecolor(colors["panel"])
    ax2.plot(df.index, df["vwap_std"], color=colors["std"], lw=0.8, label="VWAP Std Dev")
    ax2.axhline(0, color=colors["mid"], lw=0.5)
    ax2.set_title("VWAP Standard Deviation (intraday, resets daily)",
                  color=colors["text"], fontsize=10)
    ax2.legend(fontsize=7, facecolor=colors["bg"], labelcolor=colors["text"])

    # ── Subplot 3: Equity Curve ────────────────────────────────────────────────
    ax3 = axes[2]
    ax3.set_facecolor(colors["panel"])
    ax3.plot(equity_curve, color=colors["equity"], lw=1, label="Equity (P&L $)")
    ax3.axhline(0, color=colors["mid"], lw=0.5)
    ax3.set_title("Equity Curve", color=colors["text"], fontsize=10)
    ax3.legend(fontsize=7, facecolor=colors["bg"], labelcolor=colors["text"])

    for ax in axes:
        ax.tick_params(colors=colors["text"], labelsize=7)
        for spine in ax.spines.values():
            spine.set_color("#1e1e3a")

    plt.tight_layout(pad=1.5)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    out = os.path.join(RESULTS_DIR, "algo_02_vwap_reversion.png")
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=colors["bg"])
    plt.close()
    print(f"Chart saved: {out}")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    df = fetch_data()
    df = compute_intraday_vwap(df)
    df = generate_signals(df)

    signal_count = (df["signal"] != 0).sum()
    print(f"  Signals found : {signal_count}  "
          f"({(df['signal'] == 1).sum()} long, {(df['signal'] == -1).sum()} short)")

    trades, equity_curve = run_backtest(df, risk_per_trade=RISK_PER_TRADE)
    trades_df = print_algo02_stats(trades, equity_curve)

    if trades_df is not None:
        pd.set_option("display.max_rows", 999)
        print(trades_df[["entry_time", "exit_time", "direction",
                          "entry", "exit", "pnl", "result"]].to_string(index=False))

        os.makedirs(RESULTS_DIR, exist_ok=True)
        trades_df.to_csv(os.path.join(RESULTS_DIR, "algo_02_trades.csv"), index=False)

    plot(df, equity_curve, trades_df)
