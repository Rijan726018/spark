"""
ALGO 01 — Bollinger Band + CVD Divergence  |  ES Futures
─────────────────────────────────────────────────────────
Logic
  Long  : price at/below lower BB + bullish CVD divergence → target upper BB
  Short : price at/above upper BB + bearish CVD divergence → target lower BB

CVD divergence definition
  Bullish : price makes lower low while CVD makes higher low  (hidden demand)
  Bearish : price makes higher high while CVD makes lower high (hidden supply)

Data   : Yahoo Finance  (ES=F, free, 60-day / 5-min limit)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

from utils.indicators import bollinger_bands, cumulative_volume_delta, detect_cvd_divergence
from utils.backtester  import run_backtest, print_stats

# ── Config ────────────────────────────────────────────────────────────────────
SYMBOL       = "ES=F"
INTERVAL     = "1h"       # 5-minute bars
PERIOD       = "730d"      # max lookback for 5m on Yahoo
BB_PERIOD    = 20
BB_STD       = 2.0
CVD_LOOKBACK = 8          # bars to look back for divergence
RISK_PER_TRADE = 500      # max $ risk per trade
RESULTS_DIR  = os.path.join(os.path.dirname(__file__), "..", "results")


# ── Data ──────────────────────────────────────────────────────────────────────
def fetch_data() -> pd.DataFrame:
    print(f"Fetching {SYMBOL} {INTERVAL} bars ({PERIOD})...")

    # Point yfinance cache to temp dir (avoids SQLite issues on some Python builds)
    import tempfile
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
def build_features(df: pd.DataFrame) -> pd.DataFrame:
    bb = bollinger_bands(df["Close"], BB_PERIOD, BB_STD)
    df = pd.concat([df, bb], axis=1)

    df["CVD"] = cumulative_volume_delta(df["High"], df["Low"], df["Close"], df["Volume"])
    df["signal"] = detect_cvd_divergence(df, CVD_LOOKBACK)

    df = df.dropna()
    return df


# ── Chart ─────────────────────────────────────────────────────────────────────
def plot(df: pd.DataFrame, equity_curve: list, trades_df: pd.DataFrame | None):
    fig, axes = plt.subplots(3, 1, figsize=(16, 11),
                             gridspec_kw={"height_ratios": [3, 1.5, 1.5]})
    fig.patch.set_facecolor("#0d0d1a")
    colors = {"bg": "#0d0d1a", "panel": "#12122a", "text": "#e0e0e0",
              "up": "#00e676", "down": "#ff1744", "mid": "#546e7a",
              "band": "#1565c0", "cvd": "#00b0ff", "equity": "#ffd600"}

    # ── Price + BB ────────────────────────────────────────────────────────────
    ax1 = axes[0]
    ax1.set_facecolor(colors["panel"])
    ax1.plot(df.index, df["Close"],    color=colors["text"], lw=0.7, label="ES Close")
    ax1.plot(df.index, df["BB_upper"], color=colors["down"], lw=0.8, ls="--", label="BB Upper")
    ax1.plot(df.index, df["BB_mid"],   color=colors["mid"],  lw=0.6, ls="--", label="BB Mid")
    ax1.plot(df.index, df["BB_lower"], color=colors["up"],   lw=0.8, ls="--", label="BB Lower")
    ax1.fill_between(df.index, df["BB_upper"], df["BB_lower"],
                     alpha=0.06, color=colors["band"])

    longs  = df[df["signal"] ==  1]
    shorts = df[df["signal"] == -1]
    ax1.scatter(longs.index,  longs["Close"],  marker="^", color=colors["up"],   s=60, zorder=5, label="Long signal")
    ax1.scatter(shorts.index, shorts["Close"], marker="v", color=colors["down"], s=60, zorder=5, label="Short signal")

    ax1.set_title("ALGO 01 — BB + CVD Divergence  |  ES Futures  (5m)",
                  color=colors["text"], fontsize=12, pad=8)
    ax1.legend(fontsize=7, loc="upper left",
               facecolor=colors["bg"], labelcolor=colors["text"])

    # ── CVD ───────────────────────────────────────────────────────────────────
    ax2 = axes[1]
    ax2.set_facecolor(colors["panel"])
    ax2.plot(df.index, df["CVD"], color=colors["cvd"], lw=0.8, label="CVD")
    ax2.axhline(0, color=colors["mid"], lw=0.5)
    ax2.set_title("Cumulative Volume Delta", color=colors["text"], fontsize=10)
    ax2.legend(fontsize=7, facecolor=colors["bg"], labelcolor=colors["text"])

    # ── Equity curve ─────────────────────────────────────────────────────────
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
    out = os.path.join(RESULTS_DIR, "algo_01_bb_cvd_1h.png")
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=colors["bg"])
    plt.close()
    print(f"Chart saved: {out}")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    df = fetch_data()
    df = build_features(df)

    signal_count = (df["signal"] != 0).sum()
    print(f"  Signals found : {signal_count}  "
          f"({(df['signal']==1).sum()} long, {(df['signal']==-1).sum()} short)")

    trades, equity_curve = run_backtest(df, risk_per_trade=RISK_PER_TRADE)
    trades_df = print_stats(trades, equity_curve)

    if trades_df is not None:
        pd.set_option("display.max_rows", 999)
        print(trades_df[["entry_time", "exit_time", "direction",
                          "entry", "exit", "pnl", "result"]].to_string(index=False))

        os.makedirs(RESULTS_DIR, exist_ok=True)
        trades_df.to_csv(os.path.join(RESULTS_DIR, "algo_01_1h_trades.csv"), index=False)

    plot(df, equity_curve, trades_df)
