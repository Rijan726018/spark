"""
ALGO 02 — VWAP Reversion  |  moomoo (US equities)

Live execution port of algo_02_vwap_reversion.py.

Same logic as the ES backtest:
  LONG  : prior bar closed below VWAP - 2.5σ AND current bar closes higher
  SHORT : prior bar closed above VWAP + 2.5σ AND current bar closes lower
  TARGET: VWAP at signal bar
  STOP  : outer band ± 0.3 × (outer band − VWAP)

Differences vs. the futures version:
  - Pulls 1m K-lines from moomoo OpenD instead of yfinance
  - Position size in shares (not contracts), risk-based
  - Sends real orders through OpenSecTradeContext (US market)
  - Loops every bar close instead of running a one-shot backtest

Requirements
------------
  pip install moomoo-api pandas numpy
  OpenD gateway must be running (default 127.0.0.1:11111)
  Trading password unlocked via the OpenD client first time

Run
---
  python algos/algo_02_vwap_reversion_moomoo.py
"""
from __future__ import annotations

import time
import math
import logging
from dataclasses import dataclass
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from moomoo import (
    OpenQuoteContext,
    OpenSecTradeContext,
    SecurityFirm,
    TrdEnv,
    TrdMarket,
    TrdSide,
    OrderType,
    KLType,
    AuType,
    RET_OK,
)

# ── Config ────────────────────────────────────────────────────────────────────
SYMBOL          = "US.SPY"      # moomoo symbol format: "US.<TICKER>"
KLINE_INTERVAL  = KLType.K_1M   # 1-minute bars (use K_5M to match the ES version)
LOOKBACK_BARS   = 390           # one full RTH session of 1m bars

VWAP_STD_MULT1  = 1.5
VWAP_STD_MULT2  = 2.5

RISK_PER_TRADE  = 250.0         # max $ risk per trade
MAX_POSITION_USD = 25_000.0     # hard cap on notional per trade

TRD_ENV         = TrdEnv.SIMULATE   # flip to TrdEnv.REAL when ready
TRD_MARKET      = TrdMarket.US
SECURITY_FIRM   = SecurityFirm.FUTUSECURITIES   # FUTUINC / FUTUSECURITIES depending on account

OPEND_HOST      = "127.0.0.1"
OPEND_PORT      = 11111
TRADING_PWD     = ""   # leave blank if already unlocked in OpenD

POLL_SECONDS    = 15
RTH_OPEN        = dtime(9, 30)
RTH_CLOSE       = dtime(15, 55)   # stop entries 5 min before close
NY              = ZoneInfo("America/New_York")

log = logging.getLogger("vwap_reversion")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)


# ── Indicators (verbatim port from the futures version) ───────────────────────
def compute_intraday_vwap(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["tp"] = (df["high"] + df["low"] + df["close"]) / 3.0
    df["_date"] = pd.to_datetime(df.index).normalize()

    vwap     = np.full(len(df), np.nan)
    vwap_std = np.full(len(df), np.nan)

    tp_arr  = df["tp"].values
    vol_arr = df["volume"].values
    date_col = pd.Series(df["_date"].values, index=df.index)

    for day in date_col.unique():
        idx = np.where(date_col.values == day)[0]
        tp_day, vol_day = tp_arr[idx], vol_arr[idx]

        cum_tp_vol = np.cumsum(tp_day * vol_day)
        cum_vol    = np.cumsum(vol_day)
        with np.errstate(invalid="ignore", divide="ignore"):
            vwap_day = np.where(cum_vol > 0, cum_tp_vol / cum_vol, tp_day)

        cum_sq_dev = np.cumsum((tp_day - vwap_day) ** 2 * vol_day)
        with np.errstate(invalid="ignore", divide="ignore"):
            var_day = np.where(cum_vol > 0, cum_sq_dev / cum_vol, 0.0)

        vwap[idx]     = vwap_day
        vwap_std[idx] = np.sqrt(var_day)

    df["vwap"]        = vwap
    df["vwap_std"]    = vwap_std
    df["vwap_upper1"] = df["vwap"] + VWAP_STD_MULT1 * df["vwap_std"]
    df["vwap_lower1"] = df["vwap"] - VWAP_STD_MULT1 * df["vwap_std"]
    df["vwap_upper2"] = df["vwap"] + VWAP_STD_MULT2 * df["vwap_std"]
    df["vwap_lower2"] = df["vwap"] - VWAP_STD_MULT2 * df["vwap_std"]
    return df.drop(columns=["tp", "_date"])


@dataclass
class Signal:
    direction: int        # +1 long, -1 short
    target: float
    stop: float


def latest_signal(df: pd.DataFrame) -> Signal | None:
    """Evaluate the most recent CLOSED bar for a setup."""
    if len(df) < 3:
        return None

    i = len(df) - 1   # most recent closed bar (the "confirmation" bar)
    prev = i - 1

    closes = df["close"].values
    upper2 = df["vwap_upper2"].values
    lower2 = df["vwap_lower2"].values
    vwap   = df["vwap"].values
    std    = df["vwap_std"].values

    if std[i] == 0 or std[prev] == 0 or np.isnan(std[i]):
        return None

    # LONG: prior bar broke below lower band, current bar recovers
    if closes[prev] < lower2[prev] and closes[i] > closes[prev]:
        target = vwap[prev]
        band_dist = vwap[prev] - lower2[prev]
        stop = lower2[prev] - 0.3 * band_dist
        if target > stop and band_dist > 0:
            return Signal(direction=1, target=float(target), stop=float(stop))

    # SHORT: prior bar broke above upper band, current bar rejects
    if closes[prev] > upper2[prev] and closes[i] < closes[prev]:
        target = vwap[prev]
        band_dist = upper2[prev] - vwap[prev]
        stop = upper2[prev] + 0.3 * band_dist
        if target < stop and band_dist > 0:
            return Signal(direction=-1, target=float(target), stop=float(stop))

    return None


# ── moomoo plumbing ───────────────────────────────────────────────────────────
def fetch_klines(quote_ctx: OpenQuoteContext, symbol: str) -> pd.DataFrame:
    ret, data, _ = quote_ctx.request_history_kline(
        code=symbol,
        ktype=KLINE_INTERVAL,
        autype=AuType.QFQ,
        max_count=LOOKBACK_BARS,
    )
    if ret != RET_OK:
        raise RuntimeError(f"request_history_kline failed: {data}")

    df = data.rename(columns={"time_key": "ts"}).copy()
    df["ts"] = pd.to_datetime(df["ts"]).dt.tz_localize(NY, nonexistent="shift_forward",
                                                       ambiguous="NaT")
    df = df.set_index("ts").sort_index()
    return df[["open", "high", "low", "close", "volume"]].astype(float)


def position_size(entry: float, stop: float) -> int:
    risk_per_share = abs(entry - stop)
    if risk_per_share <= 0:
        return 0
    qty_by_risk = math.floor(RISK_PER_TRADE / risk_per_share)
    qty_by_cap  = math.floor(MAX_POSITION_USD / entry)
    return max(0, min(qty_by_risk, qty_by_cap))


def current_position(trade_ctx: OpenSecTradeContext, symbol: str) -> int:
    ret, data = trade_ctx.position_list_query(code=symbol, trd_env=TRD_ENV)
    if ret != RET_OK:
        log.warning("position_list_query failed: %s", data)
        return 0
    if data.empty:
        return 0
    qty = int(data.iloc[0]["qty"])
    side = data.iloc[0]["position_side"]
    # SHORT positions report as positive qty with side flag
    return -qty if str(side).upper().endswith("SHORT") else qty


def submit_bracket(
    trade_ctx: OpenSecTradeContext,
    symbol: str,
    direction: int,
    qty: int,
    target: float,
    stop: float,
):
    """
    moomoo doesn't expose native OCO for US equities, so:
      1. Send market entry
      2. Send opposite-side LIMIT for target
      3. Send opposite-side STOP for stop loss
    The watchdog loop cancels the survivor when the position closes.
    """
    entry_side = TrdSide.BUY if direction == 1 else TrdSide.SELL_SHORT
    exit_side  = TrdSide.SELL if direction == 1 else TrdSide.BUY_BACK

    ret, data = trade_ctx.place_order(
        price=0.0,
        qty=qty,
        code=symbol,
        trd_side=entry_side,
        order_type=OrderType.MARKET,
        trd_env=TRD_ENV,
    )
    if ret != RET_OK:
        log.error("entry order rejected: %s", data)
        return
    log.info("ENTRY %s %d %s @ MKT  (target %.2f / stop %.2f)",
             "LONG" if direction == 1 else "SHORT", qty, symbol, target, stop)

    trade_ctx.place_order(
        price=round(target, 2),
        qty=qty,
        code=symbol,
        trd_side=exit_side,
        order_type=OrderType.NORMAL,   # limit
        trd_env=TRD_ENV,
    )
    trade_ctx.place_order(
        price=round(stop, 2),
        qty=qty,
        code=symbol,
        trd_side=exit_side,
        order_type=OrderType.STOP,
        aux_price=round(stop, 2),
        trd_env=TRD_ENV,
    )


def cancel_resting_orders(trade_ctx: OpenSecTradeContext, symbol: str):
    ret, data = trade_ctx.order_list_query(code=symbol, trd_env=TRD_ENV)
    if ret != RET_OK or data.empty:
        return
    open_orders = data[data["order_status"].isin(["SUBMITTED", "WAITING_SUBMIT", "FILLED_PART"])]
    for oid in open_orders["order_id"].tolist():
        trade_ctx.modify_order(modify_order_op=3, order_id=oid, qty=0, price=0,
                               trd_env=TRD_ENV)  # op=3 cancels


# ── Main loop ─────────────────────────────────────────────────────────────────
def in_session(now: datetime) -> bool:
    t = now.astimezone(NY).time()
    return RTH_OPEN <= t <= RTH_CLOSE and now.astimezone(NY).weekday() < 5


def run():
    quote_ctx = OpenQuoteContext(host=OPEND_HOST, port=OPEND_PORT)
    trade_ctx = OpenSecTradeContext(
        filter_trdmarket=TRD_MARKET,
        host=OPEND_HOST,
        port=OPEND_PORT,
        security_firm=SECURITY_FIRM,
    )

    if TRADING_PWD:
        ret, data = trade_ctx.unlock_trade(TRADING_PWD)
        if ret != RET_OK:
            raise RuntimeError(f"unlock_trade failed: {data}")

    ret, _, _ = quote_ctx.subscribe([SYMBOL], [KLINE_INTERVAL])
    if ret != RET_OK:
        raise RuntimeError("subscribe failed — check OpenD quote permissions")

    last_signal_bar: pd.Timestamp | None = None
    log.info("Live. Symbol=%s  env=%s  risk=$%.0f", SYMBOL, TRD_ENV, RISK_PER_TRADE)

    try:
        while True:
            now = datetime.now(tz=NY)
            if not in_session(now):
                log.info("Outside RTH — sleeping 60s")
                time.sleep(60)
                continue

            df = fetch_klines(quote_ctx, SYMBOL)
            df = compute_intraday_vwap(df)

            # close any open positions in the final 5 minutes
            if now.time() >= dtime(15, 55):
                pos = current_position(trade_ctx, SYMBOL)
                if pos != 0:
                    log.info("EOD flatten: closing %d shares", pos)
                    cancel_resting_orders(trade_ctx, SYMBOL)
                    side = TrdSide.SELL if pos > 0 else TrdSide.BUY_BACK
                    trade_ctx.place_order(price=0.0, qty=abs(pos), code=SYMBOL,
                                          trd_side=side, order_type=OrderType.MARKET,
                                          trd_env=TRD_ENV)
                time.sleep(POLL_SECONDS)
                continue

            sig = latest_signal(df)
            bar_ts = df.index[-1]

            if sig and bar_ts != last_signal_bar and current_position(trade_ctx, SYMBOL) == 0:
                entry_est = float(df["close"].iloc[-1])
                qty = position_size(entry_est, sig.stop)
                if qty > 0:
                    submit_bracket(trade_ctx, SYMBOL, sig.direction, qty,
                                   sig.target, sig.stop)
                    last_signal_bar = bar_ts
                else:
                    log.info("Signal skipped — qty=0 (risk=%.2f)",
                             abs(entry_est - sig.stop))

            time.sleep(POLL_SECONDS)

    except KeyboardInterrupt:
        log.info("Stopped by user")
    finally:
        quote_ctx.close()
        trade_ctx.close()


if __name__ == "__main__":
    run()
