"""
Comprehensive Technical Indicators Library
All functions operate on pandas Series/DataFrame and return Series/DataFrame.
"""
import numpy as np
import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# Trend / Moving Averages
# ─────────────────────────────────────────────────────────────────────────────

def ema(close: pd.Series, period: int) -> pd.Series:
    return close.ewm(span=period, adjust=False).mean()


def sma(close: pd.Series, period: int) -> pd.Series:
    return close.rolling(period).mean()


def triple_ema(close: pd.Series, fast=5, mid=13, slow=34) -> pd.DataFrame:
    """Triple EMA — signal when fast > mid > slow (bullish) or fast < mid < slow (bearish)."""
    return pd.DataFrame({
        "TEMA_fast": ema(close, fast),
        "TEMA_mid":  ema(close, mid),
        "TEMA_slow": ema(close, slow),
    }, index=close.index)


def supertrend(high: pd.Series, low: pd.Series, close: pd.Series,
               period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
    """Supertrend indicator. Returns direction (+1 up, -1 down) and the band value."""
    atr_val = atr(high, low, close, period)
    hl2 = (high + low) / 2
    upper = hl2 + multiplier * atr_val
    lower = hl2 - multiplier * atr_val

    supertrend_val = pd.Series(np.nan, index=close.index)
    direction      = pd.Series(0,      index=close.index)

    for i in range(1, len(close)):
        # Upper band
        if upper.iloc[i] < upper.iloc[i - 1] or close.iloc[i - 1] > upper.iloc[i - 1]:
            pass
        else:
            upper.iloc[i] = upper.iloc[i - 1]
        # Lower band
        if lower.iloc[i] > lower.iloc[i - 1] or close.iloc[i - 1] < lower.iloc[i - 1]:
            pass
        else:
            lower.iloc[i] = lower.iloc[i - 1]
        # Direction
        if close.iloc[i] > upper.iloc[i - 1]:
            direction.iloc[i] = 1
            supertrend_val.iloc[i] = lower.iloc[i]
        elif close.iloc[i] < lower.iloc[i - 1]:
            direction.iloc[i] = -1
            supertrend_val.iloc[i] = upper.iloc[i]
        else:
            direction.iloc[i] = direction.iloc[i - 1]
            supertrend_val.iloc[i] = supertrend_val.iloc[i - 1]

    return pd.DataFrame({
        "ST_value":     supertrend_val,
        "ST_direction": direction,
    }, index=close.index)


def ichimoku(high: pd.Series, low: pd.Series,
             conversion: int = 9, base: int = 26,
             span_b: int = 52, displacement: int = 26) -> pd.DataFrame:
    """Ichimoku Cloud."""
    conv  = (high.rolling(conversion).max() + low.rolling(conversion).min()) / 2
    base_ = (high.rolling(base).max()       + low.rolling(base).min())       / 2
    span_a = (conv + base_) / 2
    span_b_ = (high.rolling(span_b).max() + low.rolling(span_b).min()) / 2

    return pd.DataFrame({
        "ICH_conv":   conv,
        "ICH_base":   base_,
        "ICH_span_a": span_a.shift(displacement),
        "ICH_span_b": span_b_.shift(displacement),
        "ICH_lagging": high.shift(-displacement),
    }, index=high.index)


# ─────────────────────────────────────────────────────────────────────────────
# Volatility
# ─────────────────────────────────────────────────────────────────────────────

def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range."""
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low  - close.shift(1)).abs()
    tr  = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean().rename("ATR")


def bollinger_bands(close: pd.Series, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    mid = sma(close, period)
    std = close.rolling(period).std()
    return pd.DataFrame({
        "BB_upper": mid + std_dev * std,
        "BB_mid":   mid,
        "BB_lower": mid - std_dev * std,
    }, index=close.index)


def keltner_channels(high: pd.Series, low: pd.Series, close: pd.Series,
                     period: int = 20, atr_mult: float = 2.0) -> pd.DataFrame:
    """Keltner Channels using EMA + ATR."""
    mid   = ema(close, period)
    atr_v = atr(high, low, close, period)
    return pd.DataFrame({
        "KC_upper": mid + atr_mult * atr_v,
        "KC_mid":   mid,
        "KC_lower": mid - atr_mult * atr_v,
    }, index=close.index)


def donchian(high: pd.Series, low: pd.Series, period: int = 20) -> pd.DataFrame:
    return pd.DataFrame({
        "DC_upper": high.rolling(period).max(),
        "DC_lower": low.rolling(period).min(),
        "DC_mid":   (high.rolling(period).max() + low.rolling(period).min()) / 2,
    }, index=high.index)


def atr_channel(close: pd.Series, high: pd.Series, low: pd.Series,
                ema_period: int = 20, atr_period: int = 14,
                multiplier: float = 1.5) -> pd.DataFrame:
    """EMA-based ATR channel for trend-following breakouts."""
    mid   = ema(close, ema_period)
    atr_v = atr(high, low, close, atr_period)
    return pd.DataFrame({
        "ATRC_upper": mid + multiplier * atr_v,
        "ATRC_lower": mid - multiplier * atr_v,
        "ATRC_mid":   mid,
    }, index=close.index)


# ─────────────────────────────────────────────────────────────────────────────
# Momentum / Oscillators
# ─────────────────────────────────────────────────────────────────────────────

def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain  = delta.clip(lower=0).ewm(com=period - 1, adjust=False).mean()
    loss  = (-delta.clip(upper=0)).ewm(com=period - 1, adjust=False).mean()
    rs    = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).rename("RSI")


def macd(close: pd.Series, fast: int = 12, slow: int = 26,
         signal_period: int = 9) -> pd.DataFrame:
    fast_ema   = ema(close, fast)
    slow_ema   = ema(close, slow)
    macd_line  = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram  = macd_line - signal_line
    return pd.DataFrame({
        "MACD":       macd_line,
        "MACD_signal": signal_line,
        "MACD_hist":  histogram,
    }, index=close.index)


def cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
    """Commodity Channel Index."""
    typical = (high + low + close) / 3
    mean_tp = typical.rolling(period).mean()
    mean_dev = typical.rolling(period).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)
    return ((typical - mean_tp) / (0.015 * mean_dev)).rename("CCI")


def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    highest = high.rolling(period).max()
    lowest  = low.rolling(period).min()
    return (-(highest - close) / (highest - lowest).replace(0, np.nan) * 100).rename("WILLR")


def stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
               k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
    """Stochastic Oscillator (%K, %D)."""
    lowest  = low.rolling(k_period).min()
    highest = high.rolling(k_period).max()
    k = 100 * (close - lowest) / (highest - lowest).replace(0, np.nan)
    d = k.rolling(d_period).mean()
    return pd.DataFrame({"STOCH_K": k, "STOCH_D": d}, index=close.index)


def mfi(high: pd.Series, low: pd.Series, close: pd.Series,
        volume: pd.Series, period: int = 14) -> pd.Series:
    """Money Flow Index."""
    typical = (high + low + close) / 3
    raw_flow = typical * volume
    pos_flow = raw_flow.where(typical > typical.shift(1), 0)
    neg_flow = raw_flow.where(typical < typical.shift(1), 0)
    pos_sum  = pos_flow.rolling(period).sum()
    neg_sum  = neg_flow.rolling(period).sum()
    mfr = pos_sum / neg_sum.replace(0, np.nan)
    return (100 - 100 / (1 + mfr)).rename("MFI")


# ─────────────────────────────────────────────────────────────────────────────
# Volume
# ─────────────────────────────────────────────────────────────────────────────

def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume."""
    direction = np.sign(close.diff()).fillna(0)
    return (direction * volume).cumsum().rename("OBV")


def cumulative_volume_delta(high: pd.Series, low: pd.Series,
                             close: pd.Series, volume: pd.Series) -> pd.Series:
    """Approximate CVD from OHLCV."""
    bar_range = (high - low).replace(0, np.nan)
    close_pos = ((close - low) / bar_range).fillna(0.5)
    delta     = (2 * close_pos - 1) * volume
    return delta.cumsum().rename("CVD")


def vwap(high: pd.Series, low: pd.Series,
         close: pd.Series, volume: pd.Series,
         reset_daily: bool = True) -> pd.Series:
    """VWAP, optionally reset each day."""
    typical = (high + low + close) / 3
    if reset_daily and hasattr(typical.index, 'date'):
        dates = typical.index.date if hasattr(typical.index, 'date') else None
        if dates is not None:
            cum_tp_vol = (typical * volume).groupby(dates).cumsum()
            cum_vol    = volume.groupby(dates).cumsum()
        else:
            cum_tp_vol = (typical * volume).cumsum()
            cum_vol    = volume.cumsum()
    else:
        cum_tp_vol = (typical * volume).cumsum()
        cum_vol    = volume.cumsum()
    return (cum_tp_vol / cum_vol.replace(0, np.nan)).rename("VWAP")


def elder_ray(close: pd.Series, high: pd.Series, low: pd.Series,
              period: int = 13) -> pd.DataFrame:
    """Elder Ray: Bull Power = High - EMA, Bear Power = Low - EMA."""
    base = ema(close, period)
    return pd.DataFrame({
        "ER_bull": high - base,
        "ER_bear": low  - base,
    }, index=close.index)


# ─────────────────────────────────────────────────────────────────────────────
# Support / Resistance
# ─────────────────────────────────────────────────────────────────────────────

def pivot_points(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
    """Classic pivot points (previous day's bar)."""
    pp = (high + low + close) / 3
    r1 = 2 * pp - low
    s1 = 2 * pp - high
    r2 = pp + (high - low)
    s2 = pp - (high - low)
    r3 = high + 2 * (pp - low)
    s3 = low  - 2 * (high - pp)
    return pd.DataFrame({
        "PP": pp, "R1": r1, "R2": r2, "R3": r3,
        "S1": s1, "S2": s2, "S3": s3,
    }, index=close.index)


# ─────────────────────────────────────────────────────────────────────────────
# CVD Divergence (ported from utils/indicators.py)
# ─────────────────────────────────────────────────────────────────────────────

def detect_cvd_divergence(df: pd.DataFrame, lookback: int = 5) -> pd.Series:
    """
    Returns +1 bullish, -1 bearish, 0 none.
    df must have: Close, CVD, BB_upper, BB_lower
    """
    signals = pd.Series(0, index=df.index, dtype=int)
    close  = df["Close"].values
    cvd    = df["CVD"].values
    upper  = df["BB_upper"].values
    lower  = df["BB_lower"].values

    for i in range(lookback, len(df)):
        if close[i] <= lower[i]:
            w_c = close[i - lookback:i]
            w_v = cvd[i - lookback:i]
            pl  = w_c.argmin()
            if close[i] < w_c.min() and cvd[i] > w_v[pl]:
                signals.iloc[i] = 1
        elif close[i] >= upper[i]:
            w_c = close[i - lookback:i]
            w_v = cvd[i - lookback:i]
            ph  = w_c.argmax()
            if close[i] > w_c.max() and cvd[i] < w_v[ph]:
                signals.iloc[i] = -1
    return signals
