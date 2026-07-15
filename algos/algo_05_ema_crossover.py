"""
ALGO 05 — EMA Crossover  |  ES Futures
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
from datetime import datetime

# -- yfinance timezone cache ----------------------------------------------------
yf.set_tz_cache_location(tempfile.gettempdir())

# -- Config --------------------------------------------------------------------
SYMBOL          = "ES=F"
INTERVAL        = "15m"
PERIOD          = "60d"
EMA_FAST        = 9
EMA_SLOW        = 21
RSI_PERIOD      = 14
ATR_PERIOD      = 14
VOL_SMA_PERIOD  = 20
RISK_PER_TRADE  = 500
ES_TICK_VALUE   = 50.0      # $ per point for ES futures
RESULTS_DIR     = os.path.join(os.path.dirname(__file__), "..", "results")

os.makedirs(RESULTS_DIR, exist_ok=True)

# -- 1. Download data ----------------------------------------------------------
print(f"Downloading {SYMBOL} {INTERVAL} data ({PERIOD}) …")
raw = yf.download(SYMBOL, interval=INTERVAL, period=PERIOD, progress=False)

# MultiIndex column fix
if isinstance(raw.columns, pd.MultiIndex):
    raw.columns = raw.columns.get_level_values(0)

raw.dropna(inplace=True)
df = raw.copy()
print(f"  Bars loaded: {len(df)}")

# -- 2. Indicators -------------------------------------------------------------

# EMA fast / slow
df["ema9"]  = df["Close"].ewm(span=EMA_FAST, adjust=False).mean()
df["ema21"] = df["Close"].ewm(span=EMA_SLOW, adjust=False).mean()

# RSI(14) — ewm-smoothed gains/losses
delta       = df["Close"].diff()
gain        = delta.clip(lower=0)
loss        = -delta.clip(upper=0)
avg_gain    = gain.ewm(span=RSI_PERIOD, adjust=False).mean()
avg_loss    = loss.ewm(span=RSI_PERIOD, adjust=False).mean()
rs          = avg_gain / avg_loss.replace(0, np.nan)
df["rsi"]   = 100 - (100 / (1 + rs))

# ATR(14)
high_low    = df["High"] - df["Low"]
high_close  = (df["High"] - df["Close"].shift(1)).abs()
low_close   = (df["Low"]  - df["Close"].shift(1)).abs()
tr          = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
df["atr"]   = tr.ewm(span=ATR_PERIOD, adjust=False).mean()

# Volume SMA(20)
df["vol_sma"] = df["Volume"].rolling(VOL_SMA_PERIOD).mean()

df.dropna(inplace=True)

# -- 3. Signals ----------------------------------------------------------------
df["signal"]     = 0
df["sig_target"] = np.nan
df["sig_stop"]   = np.nan

prev_ema9  = df["ema9"].shift(1)
prev_ema21 = df["ema21"].shift(1)

long_cross  = (prev_ema9 <= prev_ema21) & (df["ema9"] > df["ema21"])
short_cross = (prev_ema9 >= prev_ema21) & (df["ema9"] < df["ema21"])

long_mask  = long_cross  & (df["rsi"] > 50) & (df["Volume"] > df["vol_sma"])
short_mask = short_cross & (df["rsi"] < 50) & (df["Volume"] > df["vol_sma"])

df.loc[long_mask,  "signal"]     =  1
df.loc[long_mask,  "sig_target"] = df.loc[long_mask,  "Close"] + 2.0 * df.loc[long_mask,  "atr"]
df.loc[long_mask,  "sig_stop"]   = df.loc[long_mask,  "Close"] - 1.0 * df.loc[long_mask,  "atr"]

df.loc[short_mask, "signal"]     = -1
df.loc[short_mask, "sig_target"] = df.loc[short_mask, "Close"] - 2.0 * df.loc[short_mask, "atr"]
df.loc[short_mask, "sig_stop"]   = df.loc[short_mask, "Close"] + 1.0 * df.loc[short_mask, "atr"]

total_signals = (df["signal"] != 0).sum()
print(f"  Signals — Long: {long_mask.sum()}  Short: {short_mask.sum()}  Total: {total_signals}")

# -- 4. Backtest (inline) ------------------------------------------------------
print("Running backtest …")

trades      = []
equity      = 0.0
equity_curve = []
in_trade    = False

idx = df.index.tolist()

i = 0
while i < len(idx) - 1:
    bar      = idx[i]
    sig      = df.at[bar, "signal"]

    if sig != 0 and not in_trade:
        next_bar = idx[i + 1]
        entry    = df.at[next_bar, "Open"]
        target   = df.at[bar, "sig_target"]
        stop     = df.at[bar, "sig_stop"]
        direction = sig  # +1 long, -1 short

        risk_points = abs(entry - stop)
        if risk_points <= 0:
            i += 1
            equity_curve.append(equity)
            continue

        contracts = max(1, int(RISK_PER_TRADE / (risk_points * ES_TICK_VALUE)))

        # Scan forward from next_bar+1 for exit
        exit_price = None
        exit_idx   = None
        win        = False

        for j in range(i + 2, len(idx)):
            future_bar = idx[j]
            hi = df.at[future_bar, "High"]
            lo = df.at[future_bar, "Low"]

            if direction == 1:
                # Long: target above entry, stop below
                if hi >= target:
                    exit_price = target
                    exit_idx   = j
                    win        = True
                    break
                elif lo <= stop:
                    exit_price = stop
                    exit_idx   = j
                    win        = False
                    break
            else:
                # Short: target below entry, stop above
                if lo <= target:
                    exit_price = target
                    exit_idx   = j
                    win        = True
                    break
                elif hi >= stop:
                    exit_price = stop
                    exit_idx   = j
                    win        = False
                    break

        if exit_price is None:
            # Close at last bar close
            exit_price = df.at[idx[-1], "Close"]
            exit_idx   = len(idx) - 1
            win        = (direction == 1 and exit_price > entry) or \
                         (direction == -1 and exit_price < entry)

        pnl = direction * (exit_price - entry) * contracts * ES_TICK_VALUE
        equity += pnl

        trades.append({
            "entry_time":  next_bar,
            "exit_time":   idx[exit_idx],
            "direction":   "LONG" if direction == 1 else "SHORT",
            "entry":       entry,
            "exit":        exit_price,
            "target":      target,
            "stop":        stop,
            "contracts":   contracts,
            "pnl":         pnl,
            "win":         win,
        })

        # Advance i past exit bar
        i = exit_idx
    else:
        i += 1

    equity_curve.append(equity)

# Pad equity curve to match df length if needed
while len(equity_curve) < len(df):
    equity_curve.append(equity_curve[-1] if equity_curve else 0.0)

df["equity"] = equity_curve[:len(df)]

# -- 5. Stats ------------------------------------------------------------------
trades_df = pd.DataFrame(trades)

if len(trades_df) == 0:
    print("No trades generated.")
    total_trades = 0
    win_rate     = 0.0
    total_pnl    = 0.0
    avg_win      = 0.0
    avg_loss     = 0.0
    profit_factor = 0.0
    max_drawdown = 0.0
else:
    total_trades  = len(trades_df)
    wins          = trades_df[trades_df["win"] == True]
    losses        = trades_df[trades_df["win"] == False]
    win_rate      = len(wins) / total_trades * 100
    total_pnl     = trades_df["pnl"].sum()
    avg_win       = wins["pnl"].mean()   if len(wins)   > 0 else 0.0
    avg_loss      = losses["pnl"].mean() if len(losses) > 0 else 0.0
    gross_profit  = wins["pnl"].sum()    if len(wins)   > 0 else 0.0
    gross_loss    = abs(losses["pnl"].sum()) if len(losses) > 0 else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    # Max drawdown from equity curve
    eq = np.array(df["equity"].tolist())
    peak = np.maximum.accumulate(eq)
    dd   = eq - peak
    max_drawdown = dd.min()

print("\n-- Backtest Results -----------------------------------------------------")
print(f"  Total Trades  : {total_trades}")
print(f"  Win Rate      : {win_rate:.1f}%")
print(f"  Total P&L     : ${total_pnl:,.2f}")
print(f"  Avg Win       : ${avg_win:,.2f}")
print(f"  Avg Loss      : ${avg_loss:,.2f}")
print(f"  Profit Factor : {profit_factor:.2f}")
print(f"  Max Drawdown  : ${max_drawdown:,.2f}")
print("-------------------------------------------------------------------------\n")

# -- 6. Save trades CSV --------------------------------------------------------
csv_path = os.path.join(RESULTS_DIR, "algo_05_trades.csv")
if len(trades_df) > 0:
    trades_df.to_csv(csv_path, index=False)
    print(f"Trades saved -> {csv_path}")
else:
    pd.DataFrame().to_csv(csv_path, index=False)
    print(f"Empty trades file saved -> {csv_path}")

# -- 7. Chart ------------------------------------------------------------------
BG_DARK  = "#0d0d1a"
GRID_COL = "#1e1e2e"
TEXT_COL = "#c0c0d0"

fig, axes = plt.subplots(
    3, 1,
    figsize=(16, 12),
    facecolor=BG_DARK,
    gridspec_kw={"height_ratios": [3, 1.2, 1.2]},
    sharex=True,
)
fig.subplots_adjust(hspace=0.08, left=0.06, right=0.97, top=0.93, bottom=0.06)

for ax in axes:
    ax.set_facecolor(BG_DARK)
    ax.tick_params(colors=TEXT_COL, labelsize=8)
    ax.yaxis.label.set_color(TEXT_COL)
    ax.xaxis.label.set_color(TEXT_COL)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_COL)
    ax.grid(color=GRID_COL, linewidth=0.5, linestyle="--", alpha=0.6)

# -- Panel 1: Price + EMAs + signals ------------------------------------------
ax1 = axes[0]
ax1.plot(df.index, df["Close"], color="#8888aa", linewidth=0.8, label="Close", alpha=0.85)
ax1.plot(df.index, df["ema9"],  color="cyan",   linewidth=1.2, label=f"EMA{EMA_FAST}")
ax1.plot(df.index, df["ema21"], color="orange", linewidth=1.2, label=f"EMA{EMA_SLOW}")

long_sigs  = df[df["signal"] ==  1]
short_sigs = df[df["signal"] == -1]

ax1.scatter(long_sigs.index,  long_sigs["Low"]  * 0.9998,
            marker="^", color="lime",  s=60, zorder=5, label="Long signal")
ax1.scatter(short_sigs.index, short_sigs["High"] * 1.0002,
            marker="v", color="red",   s=60, zorder=5, label="Short signal")

ax1.set_ylabel("Price", color=TEXT_COL)
ax1.set_title(
    f"ALGO 05 — EMA Crossover  |  {SYMBOL} {INTERVAL}  |  "
    f"Trades: {total_trades}  Win Rate: {win_rate:.1f}%  "
    f"P&L: ${total_pnl:,.0f}",
    color=TEXT_COL, fontsize=11, pad=8,
)
ax1.legend(loc="upper left", fontsize=8, facecolor=BG_DARK,
           labelcolor=TEXT_COL, edgecolor=GRID_COL)

# -- Panel 2: RSI --------------------------------------------------------------
ax2 = axes[1]
ax2.plot(df.index, df["rsi"], color="#bb88ff", linewidth=0.9, label="RSI(14)")
ax2.axhline(50, color="white",  linewidth=0.8, linestyle="--", alpha=0.5)
ax2.axhline(70, color="#ff6666", linewidth=0.7, linestyle=":", alpha=0.7, label="Overbought 70")
ax2.axhline(30, color="#66ff99", linewidth=0.7, linestyle=":", alpha=0.7, label="Oversold 30")
ax2.fill_between(df.index, df["rsi"], 50,
                 where=(df["rsi"] >= 50), alpha=0.08, color="lime")
ax2.fill_between(df.index, df["rsi"], 50,
                 where=(df["rsi"] <  50), alpha=0.08, color="red")
ax2.set_ylim(0, 100)
ax2.set_ylabel("RSI", color=TEXT_COL)
ax2.legend(loc="upper left", fontsize=7, facecolor=BG_DARK,
           labelcolor=TEXT_COL, edgecolor=GRID_COL)

# -- Panel 3: Equity curve -----------------------------------------------------
ax3 = axes[2]
eq_vals = df["equity"].values
ax3.plot(df.index, eq_vals, color="gold", linewidth=1.1, label="Equity")
ax3.fill_between(df.index, eq_vals, 0,
                 where=(np.array(eq_vals) >= 0), alpha=0.12, color="gold")
ax3.fill_between(df.index, eq_vals, 0,
                 where=(np.array(eq_vals) <  0), alpha=0.15, color="red")
ax3.axhline(0, color=TEXT_COL, linewidth=0.6, linestyle="--", alpha=0.4)
ax3.set_ylabel("Equity ($)", color=TEXT_COL)
ax3.legend(loc="upper left", fontsize=7, facecolor=BG_DARK,
           labelcolor=TEXT_COL, edgecolor=GRID_COL)

# X-axis formatting on bottom panel
ax3.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
ax3.xaxis.set_major_locator(mdates.AutoDateLocator())
plt.setp(ax3.get_xticklabels(), rotation=30, ha="right", color=TEXT_COL, fontsize=7)

png_path = os.path.join(RESULTS_DIR, "algo_05_ema_crossover.png")
fig.savefig(png_path, dpi=150, bbox_inches="tight", facecolor=BG_DARK)
plt.close(fig)
print(f"Chart saved  -> {png_path}")
print("Done.")
