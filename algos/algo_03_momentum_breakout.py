"""
ALGO 03 — Momentum Breakout  |  ES Futures
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import tempfile
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import yfinance as yf

yf.set_tz_cache_location(tempfile.gettempdir())

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# -- Parameters -----------------------------------------------------------------
SYMBOL         = "ES=F"
PERIOD         = "60d"
INTERVAL       = "15m"
DONCHIAN_LEN   = 20
ATR_LEN        = 14
VOL_SMA_LEN    = 20
VOL_MULT       = 1.5
RISK_REWARD    = 2.0
RISK_STOP      = 1.0
RISK_PER_TRADE = 500.0
ES_TICK_VALUE  = 50.0

# -- Data -----------------------------------------------------------------------
print(f"Downloading {SYMBOL} {INTERVAL} bars ({PERIOD}) …")
raw = yf.download(SYMBOL, period=PERIOD, interval=INTERVAL, auto_adjust=True, progress=False)

# MultiIndex column fix
if isinstance(raw.columns, pd.MultiIndex):
    raw.columns = raw.columns.get_level_values(0)

raw.dropna(inplace=True)
df = raw.copy()

# -- Indicators -----------------------------------------------------------------
# Donchian Channel (shift(1) so bar N uses previous N bars)
df["dc_upper"] = df["High"].rolling(DONCHIAN_LEN).max().shift(1)
df["dc_lower"] = df["Low"].rolling(DONCHIAN_LEN).min().shift(1)

# ATR(14)
prev_close = df["Close"].shift(1)
tr = pd.concat(
    [
        df["High"] - df["Low"],
        (df["High"] - prev_close).abs(),
        (df["Low"]  - prev_close).abs(),
    ],
    axis=1,
).max(axis=1)
df["atr"] = tr.rolling(ATR_LEN).mean()

# Volume SMA(20)
df["vol_sma"] = df["Volume"].rolling(VOL_SMA_LEN).mean()

df.dropna(inplace=True)

# -- Signal Generation ----------------------------------------------------------
df["signal"]     = 0
df["sig_target"] = np.nan
df["sig_stop"]   = np.nan

for i in range(len(df)):
    close  = df["Close"].iloc[i]
    high   = df["High"].iloc[i]
    low    = df["Low"].iloc[i]
    vol    = df["Volume"].iloc[i]
    atr    = df["atr"].iloc[i]
    vol_s  = df["vol_sma"].iloc[i]
    dc_up  = df["dc_upper"].iloc[i]
    dc_lo  = df["dc_lower"].iloc[i]

    if pd.isna(atr) or pd.isna(vol_s):
        continue

    if close > dc_up and vol > VOL_MULT * vol_s:
        df.at[df.index[i], "signal"]     =  1
        df.at[df.index[i], "sig_target"] = close + RISK_REWARD * atr
        df.at[df.index[i], "sig_stop"]   = close - RISK_STOP   * atr
    elif close < dc_lo and vol > VOL_MULT * vol_s:
        df.at[df.index[i], "signal"]     = -1
        df.at[df.index[i], "sig_target"] = close - RISK_REWARD * atr
        df.at[df.index[i], "sig_stop"]   = close + RISK_STOP   * atr

# -- Backtesting ----------------------------------------------------------------
trades     = []
equity     = []
equity_val = 0.0
in_trade   = False

for i in range(len(df) - 1):
    sig = df["signal"].iloc[i]

    if in_trade:
        continue

    if sig == 0:
        continue

    direction  = sig
    entry_bar  = i + 1
    entry_px   = df["Open"].iloc[entry_bar]
    target_px  = df["sig_target"].iloc[i]
    stop_px    = df["sig_stop"].iloc[i]

    risk_points = abs(entry_px - stop_px)
    if risk_points <= 0:
        continue

    contracts = max(1, int(RISK_PER_TRADE / (risk_points * ES_TICK_VALUE)))

    result    = None
    exit_px   = None
    exit_bar  = None

    for j in range(entry_bar, len(df)):
        bar_high = df["High"].iloc[j]
        bar_low  = df["Low"].iloc[j]

        if direction == 1:          # LONG
            if bar_high >= target_px and bar_low <= stop_px:
                # Both hit same bar — assume target hit first (conservative: stop)
                result  = "WIN"
                exit_px = target_px
                exit_bar = j
                break
            elif bar_high >= target_px:
                result  = "WIN"
                exit_px = target_px
                exit_bar = j
                break
            elif bar_low <= stop_px:
                result  = "LOSS"
                exit_px = stop_px
                exit_bar = j
                break
        else:                       # SHORT
            if bar_low <= target_px and bar_high >= stop_px:
                result  = "WIN"
                exit_px = target_px
                exit_bar = j
                break
            elif bar_low <= target_px:
                result  = "WIN"
                exit_px = target_px
                exit_bar = j
                break
            elif bar_high >= stop_px:
                result  = "LOSS"
                exit_px = stop_px
                exit_bar = j
                break

    if result is None:
        continue

    pnl_points = direction * (exit_px - entry_px)
    pnl_dollar = pnl_points * ES_TICK_VALUE * contracts
    equity_val += pnl_dollar
    equity.append(equity_val)

    trades.append(
        {
            "entry_time":  df.index[entry_bar],
            "exit_time":   df.index[exit_bar],
            "direction":   "LONG" if direction == 1 else "SHORT",
            "entry_price": round(entry_px,  2),
            "exit_price":  round(exit_px,   2),
            "target":      round(target_px, 2),
            "stop":        round(stop_px,   2),
            "contracts":   contracts,
            "pnl":         round(pnl_dollar, 2),
            "result":      result,
        }
    )

trades_df = pd.DataFrame(trades)

# -- Statistics -----------------------------------------------------------------
def print_stats(trades_df):
    if trades_df.empty:
        print("No trades generated.")
        return

    total  = len(trades_df)
    wins   = trades_df[trades_df["result"] == "WIN"]
    losses = trades_df[trades_df["result"] == "LOSS"]

    win_rate     = len(wins) / total * 100
    total_pnl    = trades_df["pnl"].sum()
    avg_win      = wins["pnl"].mean()   if not wins.empty   else 0.0
    avg_loss     = losses["pnl"].mean() if not losses.empty else 0.0
    gross_profit = wins["pnl"].sum()    if not wins.empty   else 0.0
    gross_loss   = losses["pnl"].sum()  if not losses.empty else 0.0
    profit_factor = (gross_profit / abs(gross_loss)) if gross_loss != 0 else float("inf")

    # Max Drawdown
    eq_curve = trades_df["pnl"].cumsum()
    roll_max = eq_curve.cummax()
    drawdown = eq_curve - roll_max
    max_dd   = drawdown.min()

    print("=" * 52)
    print("  ALGO 03 — Momentum Breakout  |  ES Futures")
    print("=" * 52)
    print(f"  Total Trades   : {total}")
    print(f"  Win Rate       : {win_rate:.1f}%")
    print(f"  Total P&L      : ${total_pnl:,.2f}")
    print(f"  Avg Win        : ${avg_win:,.2f}")
    print(f"  Avg Loss       : ${avg_loss:,.2f}")
    print(f"  Profit Factor  : {profit_factor:.2f}")
    print(f"  Max Drawdown   : ${max_dd:,.2f}")
    print("=" * 52)

print_stats(trades_df)

# -- Save Trades CSV ------------------------------------------------------------
csv_path = os.path.join(RESULTS_DIR, "algo_03_trades.csv")
trades_df.to_csv(csv_path, index=False)
print(f"Trades saved -> {csv_path}")

# -- Chart ----------------------------------------------------------------------
BG      = "#0d0d1a"
GRID_C  = "#1e1e33"
TEXT_C  = "#ccccdd"

fig, axes = plt.subplots(
    3, 1,
    figsize=(16, 10),
    facecolor=BG,
    gridspec_kw={"height_ratios": [3, 1, 1]},
    sharex=True,
)
fig.subplots_adjust(hspace=0.08)

for ax in axes:
    ax.set_facecolor(BG)
    ax.tick_params(colors=TEXT_C, labelsize=8)
    ax.yaxis.label.set_color(TEXT_C)
    ax.xaxis.label.set_color(TEXT_C)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_C)
    ax.grid(color=GRID_C, linewidth=0.5, linestyle="--")

x = np.arange(len(df))

# -- Subplot 1: Price + Donchian --
ax1 = axes[0]
ax1.plot(x, df["Close"].values, color="#4fc3f7", linewidth=0.8, label="Close")
ax1.plot(x, df["dc_upper"].values, color="red",   linewidth=0.9, linestyle="--", label="DC Upper")
ax1.plot(x, df["dc_lower"].values, color="#00e676", linewidth=0.9, linestyle="--", label="DC Lower")

# Long signals
long_idx = df.index[df["signal"] == 1]
for ts in long_idx:
    pos = df.index.get_loc(ts)
    ax1.scatter(x[pos], df["Close"].iloc[pos], marker="^", color="lime",
                s=60, zorder=5)

# Short signals
short_idx = df.index[df["signal"] == -1]
for ts in short_idx:
    pos = df.index.get_loc(ts)
    ax1.scatter(x[pos], df["Close"].iloc[pos], marker="v", color="red",
                s=60, zorder=5)

ax1.set_ylabel("Price", color=TEXT_C)
ax1.set_title("ALGO 03 — Momentum Breakout | ES Futures (15m)", color=TEXT_C, fontsize=11, pad=8)
ax1.legend(facecolor=BG, edgecolor=GRID_C, labelcolor=TEXT_C, fontsize=8, loc="upper left")

# -- Subplot 2: ATR --
ax2 = axes[1]
ax2.plot(x, df["atr"].values, color="#ff9800", linewidth=0.9, label="ATR(14)")
ax2.set_ylabel("ATR", color=TEXT_C)
ax2.legend(facecolor=BG, edgecolor=GRID_C, labelcolor=TEXT_C, fontsize=8, loc="upper left")

# -- Subplot 3: Equity Curve --
ax3 = axes[2]
if not trades_df.empty:
    eq_curve = trades_df["pnl"].cumsum().values
    ax3.plot(np.arange(len(eq_curve)), eq_curve, color="gold", linewidth=1.0, label="Equity")
    ax3.axhline(0, color="#555577", linewidth=0.6, linestyle="--")
    ax3.fill_between(np.arange(len(eq_curve)), eq_curve, 0,
                     where=(eq_curve >= 0), alpha=0.15, color="gold")
    ax3.fill_between(np.arange(len(eq_curve)), eq_curve, 0,
                     where=(eq_curve < 0),  alpha=0.15, color="red")
else:
    ax3.text(0.5, 0.5, "No Trades", color=TEXT_C, ha="center", va="center",
             transform=ax3.transAxes)

ax3.set_ylabel("P&L ($)", color=TEXT_C)
ax3.legend(facecolor=BG, edgecolor=GRID_C, labelcolor=TEXT_C, fontsize=8, loc="upper left")

# X-axis ticks — show roughly 10 date labels
tick_step = max(1, len(df) // 10)
tick_pos   = x[::tick_step]
tick_labels = [str(df.index[i])[:16] for i in tick_pos]
axes[-1].set_xticks(tick_pos)
axes[-1].set_xticklabels(tick_labels, rotation=30, ha="right", fontsize=7, color=TEXT_C)

plt.tight_layout()
chart_path = os.path.join(RESULTS_DIR, "algo_03_momentum_breakout.png")
fig.savefig(chart_path, dpi=150, bbox_inches="tight", facecolor=BG)
plt.close(fig)
print(f"Chart saved  -> {chart_path}")
