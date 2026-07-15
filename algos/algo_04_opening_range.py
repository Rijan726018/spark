"""
ALGO 04 — Opening Range Breakout  |  ES + NQ Futures  (Hourly, 730 days)
-------------------------------------------------------------------------
Opening Range  = first 2 RTH hours per day  (9 AM + 10 AM hourly bars)
Signal window  = 11 AM – 2 PM ET  (first breakout bar only per day)
Exit           = target hit / stop hit / 3 PM ET timeout
Instruments    = ES=F  ($50/pt)  +  NQ=F  ($20/pt)
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import tempfile
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ── Config ────────────────────────────────────────────────────────────────────
INSTRUMENTS = {
    "ES=F": 50.0,   # $ per point
    "NQ=F": 20.0,
}
INTERVAL        = "1h"
PERIOD          = "730d"
RISK_PER_TRADE  = 500        # max $ risk per trade
MIN_OR_POINTS   = 3.0        # skip days where OR range < 3 pts
OR_HOURS        = {9, 10}    # 9 AM + 10 AM bars = 2-hour opening range
SIGNAL_HOUR_MIN = 11         # first valid signal bar
SIGNAL_HOUR_MAX = 14         # last valid signal bar (3 PM timeout after)
EXIT_HOUR       = 15         # force exit at 3 PM ET
RESULTS_DIR     = os.path.join(os.path.dirname(__file__), "..", "results")

yf.set_tz_cache_location(tempfile.gettempdir())
os.makedirs(RESULTS_DIR, exist_ok=True)


# ── Download one instrument ───────────────────────────────────────────────────
def fetch(symbol: str) -> pd.DataFrame:
    print(f"  Fetching {symbol} {INTERVAL} bars ({PERIOD})...")
    raw = yf.download(symbol, interval=INTERVAL, period=PERIOD, progress=False)
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    raw = raw.dropna()
    raw.index = raw.index.tz_convert("America/New_York")
    raw.sort_index(inplace=True)
    print(f"    {len(raw):,} bars   {raw.index[0].date()}  to  {raw.index[-1].date()}")
    return raw


# ── Build opening range levels per day ───────────────────────────────────────
def compute_or_levels(df: pd.DataFrame) -> dict:
    """Returns {date: (or_high, or_low)} for days that pass the min-range filter."""
    df["_date"] = df.index.date
    df["_hour"] = df.index.hour
    or_levels = {}
    for day, grp in df.groupby("_date"):
        or_bars = grp[grp["_hour"].isin(OR_HOURS)]
        if or_bars.empty:
            continue
        or_high = or_bars["High"].max()
        or_low  = or_bars["Low"].min()
        if (or_high - or_low) < MIN_OR_POINTS:
            continue
        or_levels[day] = (or_high, or_low)
    return or_levels


# ── Generate signals ──────────────────────────────────────────────────────────
def generate_signals(df: pd.DataFrame, or_levels: dict) -> pd.DataFrame:
    df["signal"]     = 0
    df["sig_target"] = np.nan
    df["sig_stop"]   = np.nan
    df["OR_High"]    = np.nan
    df["OR_Low"]     = np.nan

    for day, (or_high, or_low) in or_levels.items():
        day_mask = df["_date"] == day
        df.loc[day_mask, "OR_High"] = or_high
        df.loc[day_mask, "OR_Low"]  = or_low

        sig_mask = (
            day_mask &
            (df["_hour"] >= SIGNAL_HOUR_MIN) &
            (df["_hour"] <= SIGNAL_HOUR_MAX)
        )
        taken = False
        for idx, row in df[sig_mask].iterrows():
            if taken:
                break
            if row["Close"] > or_high:
                df.at[idx, "signal"]     =  1
                df.at[idx, "sig_target"] = or_high + (or_high - or_low)
                df.at[idx, "sig_stop"]   = or_low
                taken = True
            elif row["Close"] < or_low:
                df.at[idx, "signal"]     = -1
                df.at[idx, "sig_target"] = or_low - (or_high - or_low)
                df.at[idx, "sig_stop"]   = or_high
                taken = True
    return df


# ── Backtest one instrument ───────────────────────────────────────────────────
def backtest(df: pd.DataFrame, tick_value: float) -> list:
    all_idx = df.index.tolist()
    idx_map = {ts: i for i, ts in enumerate(all_idx)}
    trades  = []

    for sig_ts, sig_row in df[df["signal"] != 0].iterrows():
        direction = int(sig_row["signal"])
        target    = sig_row["sig_target"]
        stop      = sig_row["sig_stop"]
        sig_pos   = idx_map[sig_ts]

        if sig_pos + 1 >= len(all_idx):
            continue

        entry_ts  = all_idx[sig_pos + 1]
        entry_bar = df.loc[entry_ts]
        entry     = float(entry_bar["Open"])

        risk_pts  = abs(entry - stop)
        if risk_pts < 0.1:
            continue
        contracts = max(1, int(RISK_PER_TRADE / (risk_pts * tick_value)))

        day    = sig_row["_date"]
        pnl    = result = exit_px = exit_ts = None

        for fwd_pos in range(sig_pos + 1, len(all_idx)):
            fwd_ts  = all_idx[fwd_pos]
            fwd_bar = df.loc[fwd_ts]
            fwd_day = fwd_bar["_date"]
            fwd_h   = float(fwd_bar["High"])
            fwd_l   = float(fwd_bar["Low"])
            fwd_hr  = fwd_bar["_hour"]

            # End of day without hit -> timeout
            if fwd_day != day:
                prev_bar = df.loc[all_idx[fwd_pos - 1]]
                exit_ts  = all_idx[fwd_pos - 1]
                exit_px  = float(prev_bar["Close"])
                pnl      = (exit_px - entry) * direction * contracts * tick_value
                result   = "WIN" if pnl > 0 else "LOSS"
                break

            # Force exit at 3 PM
            if fwd_hr >= EXIT_HOUR:
                exit_ts = fwd_ts
                exit_px = float(fwd_bar["Open"])
                pnl     = (exit_px - entry) * direction * contracts * tick_value
                result  = "WIN" if pnl > 0 else "LOSS"
                break

            if direction == 1:   # LONG
                if fwd_h >= target:
                    exit_ts = fwd_ts; exit_px = target
                    pnl     = (target - entry) * contracts * tick_value
                    result  = "WIN"; break
                if fwd_l <= stop:
                    exit_ts = fwd_ts; exit_px = stop
                    pnl     = (stop - entry) * contracts * tick_value
                    result  = "LOSS"; break
            else:                # SHORT
                if fwd_l <= target:
                    exit_ts = fwd_ts; exit_px = target
                    pnl     = (entry - target) * contracts * tick_value
                    result  = "WIN"; break
                if fwd_h >= stop:
                    exit_ts = fwd_ts; exit_px = stop
                    pnl     = (entry - stop) * contracts * tick_value
                    result  = "LOSS"; break

        if pnl is None:
            continue

        trades.append({
            "symbol"    : sig_row.get("_symbol", "ES=F"),
            "date"      : day,
            "direction" : "LONG" if direction == 1 else "SHORT",
            "entry_time": entry_ts,
            "exit_time" : exit_ts,
            "entry"     : round(entry,   2),
            "exit"      : round(exit_px, 2),
            "target"    : round(target,  2),
            "stop"      : round(stop,    2),
            "contracts" : contracts,
            "pnl"       : round(pnl,     2),
            "result"    : result,
            "or_high"   : round(sig_row["OR_High"], 2),
            "or_low"    : round(sig_row["OR_Low"],  2),
        })

    return trades


# ── Stats ─────────────────────────────────────────────────────────────────────
def print_stats(df_t: pd.DataFrame, label: str = "ALL"):
    if df_t.empty:
        print(f"No trades for {label}.")
        return
    wins   = df_t[df_t["result"] == "WIN"]
    losses = df_t[df_t["result"] == "LOSS"]
    gp     = wins["pnl"].sum()   if len(wins)   else 0
    gl     = losses["pnl"].sum() if len(losses) else 0
    pf     = abs(gp / gl) if gl != 0 else float("inf")
    eq     = df_t["pnl"].cumsum().values
    dd     = (eq - np.maximum.accumulate(eq)).min()

    print(f"\n{'='*55}")
    print(f"  ALGO 04 — Opening Range Breakout  [{label}]")
    print(f"{'='*55}")
    print(f"  Total Trades   : {len(df_t)}")
    print(f"  Win Rate       : {len(wins)/len(df_t)*100:.1f}%")
    print(f"  Total P&L      : ${df_t['pnl'].sum():>12,.0f}")
    print(f"  Avg Win        : ${wins['pnl'].mean():>12,.0f}" if len(wins) else "  Avg Win        :            $0")
    print(f"  Avg Loss       : ${losses['pnl'].mean():>12,.0f}" if len(losses) else "  Avg Loss       :            $0")
    print(f"  Profit Factor  : {pf:.2f}")
    print(f"  Max Drawdown   : ${dd:>12,.0f}")
    print(f"{'='*55}")


# ── Chart ─────────────────────────────────────────────────────────────────────
def plot(all_trades: pd.DataFrame, eq_curve_es: list, eq_curve_nq: list):
    BG  = "#0d0d1a"
    FG  = "#e0e0f0"
    GRD = "#1e1e3a"

    fig, axes = plt.subplots(3, 1, figsize=(16, 12),
                             gridspec_kw={"height_ratios": [2, 1.5, 2]},
                             facecolor=BG)
    fig.suptitle("ALGO 04 — Opening Range Breakout  |  ES + NQ Futures  (1h / 730d)",
                 color=FG, fontsize=13, fontweight="bold", y=0.99)

    for ax in axes:
        ax.set_facecolor(BG)
        ax.tick_params(colors=FG, labelsize=7)
        for sp in ax.spines.values():
            sp.set_edgecolor(GRD)
        ax.grid(color=GRD, lw=0.4, ls="--")

    # Panel 1: Daily P&L by symbol
    ax1 = axes[0]
    if not all_trades.empty:
        daily = all_trades.groupby(["date", "symbol"])["pnl"].sum().unstack(fill_value=0)
        x = np.arange(len(daily))
        w = 0.4
        if "ES=F" in daily.columns:
            ax1.bar(x - w/2, daily["ES=F"].values,
                    width=w, label="ES", zorder=2,
                    color=["#00e676" if v >= 0 else "#ff1744" for v in daily["ES=F"].values])
        if "NQ=F" in daily.columns:
            ax1.bar(x + w/2, daily["NQ=F"].values,
                    width=w, label="NQ", zorder=2,
                    color=["#40c4ff" if v >= 0 else "#ff6d00" for v in daily["NQ=F"].values])
        step = max(1, len(daily) // 30)
        ax1.set_xticks(x[::step])
        ax1.set_xticklabels([str(d) for d in daily.index[::step]], rotation=45, ha="right", fontsize=6)
        ax1.axhline(0, color=FG, lw=0.5)
        ax1.legend(fontsize=7, facecolor=BG, labelcolor=FG)
    ax1.set_title("Daily P&L  —  ES (green/red)  vs  NQ (blue/orange)", color=FG, fontsize=9)
    ax1.set_ylabel("P&L ($)", color=FG)

    # Panel 2: Win rate by month
    ax2 = axes[1]
    if not all_trades.empty:
        all_trades["month"] = pd.to_datetime(all_trades["date"]).dt.to_period("M")
        monthly = all_trades.groupby("month").apply(
            lambda g: len(g[g["result"] == "WIN"]) / len(g) * 100
        )
        x2 = np.arange(len(monthly))
        bar_colors = ["#00e676" if v >= 50 else "#ff1744" for v in monthly.values]
        ax2.bar(x2, monthly.values, color=bar_colors, zorder=2)
        ax2.axhline(50, color="#ffb300", lw=0.8, ls="--", label="50% line")
        ax2.set_xticks(x2)
        ax2.set_xticklabels([str(m) for m in monthly.index], rotation=45, ha="right", fontsize=7)
        ax2.legend(fontsize=7, facecolor=BG, labelcolor=FG)
    ax2.set_title("Monthly Win Rate  (green = above 50%)", color=FG, fontsize=9)
    ax2.set_ylabel("Win Rate %", color=FG)

    # Panel 3: Equity curves
    ax3 = axes[2]
    def plot_eq(eq_curve, color, label):
        if eq_curve:
            ts, vals = zip(*eq_curve)
            ax3.plot(ts, vals, color=color, lw=1.2, label=label)
            ax3.fill_between(ts, vals, alpha=0.1, color=color)

    plot_eq(eq_curve_es, "#ffd600", "ES equity")
    plot_eq(eq_curve_nq, "#40c4ff", "NQ equity")
    ax3.axhline(0, color=FG, lw=0.5)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))
    ax3.legend(fontsize=7, facecolor=BG, labelcolor=FG)
    ax3.set_title("Equity Curve  —  ES + NQ", color=FG, fontsize=9)
    ax3.set_ylabel("Cumulative P&L ($)", color=FG)

    plt.tight_layout(rect=[0, 0, 1, 0.97])
    out = os.path.join(RESULTS_DIR, "algo_04_opening_range.png")
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"Chart saved: {out}")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  ALGO 04 — Opening Range Breakout  (1h / 730d)")
    print("=" * 55)

    all_trades   = []
    eq_curve_es  = []
    eq_curve_nq  = []
    equity_es    = 0.0
    equity_nq    = 0.0

    for symbol, tick_val in INSTRUMENTS.items():
        df = fetch(symbol)
        or_levels = compute_or_levels(df)
        df = generate_signals(df, or_levels)
        df["_symbol"] = symbol

        n_sig = (df["signal"] != 0).sum()
        print(f"  {symbol}  |  OR days: {len(or_levels)}  |  Signals: {n_sig}")

        trades = backtest(df, tick_val)
        for t in trades:
            t["symbol"] = symbol

        # Build per-symbol equity curve
        eq = 0.0
        for t in sorted(trades, key=lambda x: x["exit_time"]):
            eq += t["pnl"]
            if symbol == "ES=F":
                equity_es = eq
                eq_curve_es.append((t["exit_time"], eq))
            else:
                equity_nq = eq
                eq_curve_nq.append((t["exit_time"], eq))

        all_trades.extend(trades)

        df_sym = pd.DataFrame(trades)
        print_stats(df_sym, symbol)

    # Combined stats
    df_all = pd.DataFrame(all_trades)
    print_stats(df_all, "ES + NQ COMBINED")

    # Save
    csv_path = os.path.join(RESULTS_DIR, "algo_04_trades.csv")
    df_all.to_csv(csv_path, index=False)
    print(f"Trades saved: {csv_path}")
    print(f"Sample size : {len(df_all)} trades")

    plot(df_all, eq_curve_es, eq_curve_nq)
