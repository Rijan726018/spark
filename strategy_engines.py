from __future__ import annotations

import numpy as np
import pandas as pd


def _ensure_cols(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x.columns = [str(c).lower().strip() for c in x.columns]
    needed = ["open", "high", "low", "close", "volume"]
    for c in needed:
        if c not in x.columns:
            if c == "volume":
                x[c] = 0.0
            else:
                raise ValueError(f"Missing required column: {c}")
    x = x[needed].dropna()
    return x


def _orderflow_features(df: pd.DataFrame) -> pd.DataFrame:
    x = _ensure_cols(df)
    rng = (x["high"] - x["low"]).replace(0, np.nan)
    body = x["close"] - x["open"]
    close_pos = ((x["close"] - x["low"]) / rng).clip(0, 1).fillna(0.5)

    # Tape/orderflow proxies from OHLCV (institutional approximation without full tick tape)
    x["delta_proxy"] = (2 * close_pos - 1.0) * x["volume"]
    x["cvd_proxy"] = x["delta_proxy"].cumsum()
    x["imbalance"] = (x["delta_proxy"] / x["volume"].replace(0, np.nan)).fillna(0.0)
    x["vol_z"] = (
        (x["volume"] - x["volume"].rolling(40).mean()) /
        x["volume"].rolling(40).std().replace(0, np.nan)
    ).fillna(0.0)
    x["range"] = (x["high"] - x["low"]).fillna(0.0)
    x["range_z"] = (
        (x["range"] - x["range"].rolling(40).mean()) /
        x["range"].rolling(40).std().replace(0, np.nan)
    ).fillna(0.0)
    x["upper_wick"] = (x["high"] - x[["open", "close"]].max(axis=1)).clip(lower=0)
    x["lower_wick"] = (x[["open", "close"]].min(axis=1) - x["low"]).clip(lower=0)
    x["body"] = body
    x["ema_fast"] = x["close"].ewm(span=12, adjust=False).mean()
    x["ema_slow"] = x["close"].ewm(span=36, adjust=False).mean()
    x["vwap_proxy"] = ((x["close"] * x["volume"]).cumsum() / x["volume"].replace(0, np.nan).cumsum()).fillna(x["close"])
    x["atr"] = (x["high"] - x["low"]).rolling(14).mean().fillna(method="bfill")
    return x


def _signal_to_positions(entry_long: pd.Series, entry_short: pd.Series, exit_flat: pd.Series) -> pd.Series:
    n = len(entry_long)
    pos = np.zeros(n, dtype=int)
    cur = 0
    for i in range(n):
        if exit_flat.iat[i]:
            cur = 0
        if entry_long.iat[i]:
            cur = 1
        elif entry_short.iat[i]:
            cur = -1
        pos[i] = cur
    return pd.Series(pos, index=entry_long.index)


def run_volume_tape_strategy(df: pd.DataFrame, variant: int = 0) -> pd.DataFrame:
    x = _orderflow_features(df)

    # 12 deterministic "desk-style" variants built on orderflow proxies
    v = int(variant) % 12

    if v == 0:
        # Delta divergence mean reversion
        px_ll = x["close"] < x["close"].rolling(20).min().shift(1)
        cvd_hl = x["cvd_proxy"] > x["cvd_proxy"].rolling(20).min().shift(1)
        px_hh = x["close"] > x["close"].rolling(20).max().shift(1)
        cvd_lh = x["cvd_proxy"] < x["cvd_proxy"].rolling(20).max().shift(1)
        long_e = px_ll & cvd_hl & (x["vol_z"] > -0.5)
        short_e = px_hh & cvd_lh & (x["vol_z"] > -0.5)
        flat = (x["close"] > x["vwap_proxy"]) | (x["close"] < x["vwap_proxy"])
    elif v == 1:
        # Stacked imbalance breakout
        long_e = (x["imbalance"] > 0.35) & (x["vol_z"] > 1.2) & (x["close"] > x["ema_fast"])
        short_e = (x["imbalance"] < -0.35) & (x["vol_z"] > 1.2) & (x["close"] < x["ema_fast"])
        flat = (x["imbalance"].abs() < 0.05)
    elif v == 2:
        # Absorption reversal
        long_e = (x["lower_wick"] > x["body"].abs() * 1.4) & (x["vol_z"] > 1.0) & (x["close"] > x["open"])
        short_e = (x["upper_wick"] > x["body"].abs() * 1.4) & (x["vol_z"] > 1.0) & (x["close"] < x["open"])
        flat = (x["range_z"] < -0.3)
    elif v == 3:
        # Initiative drive continuation
        long_e = (x["ema_fast"] > x["ema_slow"]) & (x["delta_proxy"] > 0) & (x["vol_z"] > 0.5) & (x["close"] > x["vwap_proxy"])
        short_e = (x["ema_fast"] < x["ema_slow"]) & (x["delta_proxy"] < 0) & (x["vol_z"] > 0.5) & (x["close"] < x["vwap_proxy"])
        flat = (x["delta_proxy"].rolling(5).mean().abs() < x["volume"].rolling(5).mean() * 0.02)
    elif v == 4:
        # Failed auction reversal
        long_e = (x["close"] < x["close"].rolling(30).min().shift(1)) & (x["delta_proxy"] > x["delta_proxy"].rolling(10).mean())
        short_e = (x["close"] > x["close"].rolling(30).max().shift(1)) & (x["delta_proxy"] < x["delta_proxy"].rolling(10).mean())
        flat = (x["close"] - x["vwap_proxy"]).abs() < (x["atr"] * 0.25)
    elif v == 5:
        # Volume climax fade
        long_e = (x["vol_z"] > 2.2) & (x["imbalance"] < -0.2) & (x["lower_wick"] > x["upper_wick"])
        short_e = (x["vol_z"] > 2.2) & (x["imbalance"] > 0.2) & (x["upper_wick"] > x["lower_wick"])
        flat = (x["vol_z"] < 0.2)
    elif v == 6:
        # Pullback in CVD trend
        cvd_trend = x["cvd_proxy"].rolling(20).mean()
        long_e = (cvd_trend.diff() > 0) & (x["close"] < x["ema_fast"]) & (x["delta_proxy"] > 0)
        short_e = (cvd_trend.diff() < 0) & (x["close"] > x["ema_fast"]) & (x["delta_proxy"] < 0)
        flat = (x["close"] - x["ema_fast"]).abs() < (x["atr"] * 0.15)
    elif v == 7:
        # VWAP reversion with volume gate
        dist = x["close"] - x["vwap_proxy"]
        long_e = (dist < -x["atr"] * 0.8) & (x["vol_z"] > 0.3) & (x["delta_proxy"] > 0)
        short_e = (dist > x["atr"] * 0.8) & (x["vol_z"] > 0.3) & (x["delta_proxy"] < 0)
        flat = dist.abs() < x["atr"] * 0.2
    elif v == 8:
        # Compression -> expansion with tape confirmation
        comp = x["range_z"] < -0.8
        exp = x["range_z"] > 0.8
        long_e = comp.shift(1).fillna(False) & exp & (x["delta_proxy"] > 0) & (x["ema_fast"] > x["ema_slow"])
        short_e = comp.shift(1).fillna(False) & exp & (x["delta_proxy"] < 0) & (x["ema_fast"] < x["ema_slow"])
        flat = x["range_z"] < -0.2
    elif v == 9:
        # Momentum with aggressive imbalance
        long_e = (x["close"] > x["close"].rolling(15).max().shift(1)) & (x["imbalance"] > 0.25)
        short_e = (x["close"] < x["close"].rolling(15).min().shift(1)) & (x["imbalance"] < -0.25)
        flat = x["imbalance"].abs() < 0.05
    elif v == 10:
        # Delta flip at key level proxy
        level = x["close"].rolling(50).mean()
        long_e = (x["close"] > level) & (x["delta_proxy"].rolling(3).sum() > 0) & (x["delta_proxy"].shift(1) < 0)
        short_e = (x["close"] < level) & (x["delta_proxy"].rolling(3).sum() < 0) & (x["delta_proxy"].shift(1) > 0)
        flat = (x["close"] - level).abs() < x["atr"] * 0.1
    else:
        # Hybrid execution model
        long_e = (x["ema_fast"] > x["ema_slow"]) & (x["close"] > x["vwap_proxy"]) & (x["vol_z"] > 0) & (x["delta_proxy"] > 0)
        short_e = (x["ema_fast"] < x["ema_slow"]) & (x["close"] < x["vwap_proxy"]) & (x["vol_z"] > 0) & (x["delta_proxy"] < 0)
        flat = (x["vol_z"] < -0.4) | (x["imbalance"].abs() < 0.03)

    x["signal"] = _signal_to_positions(long_e.fillna(False), short_e.fillna(False), flat.fillna(False))
    return x

