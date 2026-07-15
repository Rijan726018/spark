"""
Strategy Signal Generators
Each function accepts an OHLCV DataFrame and params dict.
Returns the DataFrame with added columns: signal (+1/-1/0), target, stop.
"""
import numpy as np
import pandas as pd
from engines.indicators import (
    bollinger_bands, keltner_channels, donchian, atr_channel, atr,
    rsi, macd, cci, williams_r, stochastic, mfi, obv, elder_ray,
    ichimoku, supertrend, triple_ema, ema, sma, vwap, pivot_points,
    cumulative_volume_delta, detect_cvd_divergence,
)

ATR_STOP_MULT   = 1.0
ATR_TARGET_MULT = 2.0


def _apply_atr_targets(df: pd.DataFrame, signal_col="signal",
                        atr_col="ATR", rr: float = 2.0) -> pd.DataFrame:
    """Add target/stop columns from ATR for entries where signal != 0."""
    df["target"] = np.nan
    df["stop"]   = np.nan
    for i in range(len(df)):
        s = df["signal"].iloc[i]
        if s == 0:
            continue
        a = df[atr_col].iloc[i]
        e = df["Close"].iloc[i]
        if s == 1:
            df.at[df.index[i], "target"] = e + rr * a
            df.at[df.index[i], "stop"]   = e - a
        else:
            df.at[df.index[i], "target"] = e - rr * a
            df.at[df.index[i], "stop"]   = e + a
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 1. BB + CVD Divergence
# ─────────────────────────────────────────────────────────────────────────────

def strategy_bb_cvd(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    bb_period  = params.get("bb_period", 20)
    bb_std     = params.get("bb_std", 2.0)
    cvd_lb     = params.get("cvd_lookback", 5)

    bb  = bollinger_bands(df["Close"], bb_period, bb_std)
    df  = df.join(bb)
    df["CVD"] = cumulative_volume_delta(df["High"], df["Low"], df["Close"], df["Volume"])
    df["signal"] = detect_cvd_divergence(df, cvd_lb)
    # Target = opposite BB band, stop = signal band
    df["target"] = np.where(df["signal"] == 1,  df["BB_upper"], df["BB_lower"])
    df["stop"]   = np.where(df["signal"] == 1,  df["BB_lower"], df["BB_upper"])
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 2. VWAP Reversion
# ─────────────────────────────────────────────────────────────────────────────

def strategy_vwap_rev(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    upper_mult  = params.get("upper_band", 2.5)
    lower_mult  = params.get("lower_band", 2.5)
    stop_buf    = params.get("stop_buffer", 0.3)

    typical = (df["High"] + df["Low"] + df["Close"]) / 3
    try:
        dates = typical.index.date
        cum_tp = (typical * df["Volume"]).groupby(dates).cumsum()
        cum_v  = df["Volume"].groupby(dates).cumsum()
    except Exception:
        cum_tp = (typical * df["Volume"]).cumsum()
        cum_v  = df["Volume"].cumsum()

    vwap_v = cum_tp / cum_v.replace(0, np.nan)
    vwap_std = typical.rolling(20).std().fillna(0)

    upper = vwap_v + upper_mult * vwap_std
    lower = vwap_v - lower_mult * vwap_std

    signal = pd.Series(0, index=df.index)
    for i in range(1, len(df)):
        # Long: price crossed below lower → recovered
        if df["Close"].iloc[i-1] < lower.iloc[i-1] and df["Close"].iloc[i] > df["Close"].iloc[i-1]:
            signal.iloc[i] = 1
        # Short: price crossed above upper → recovered
        elif df["Close"].iloc[i-1] > upper.iloc[i-1] and df["Close"].iloc[i] < df["Close"].iloc[i-1]:
            signal.iloc[i] = -1

    df["signal"] = signal
    bw = upper - lower
    df["target"] = vwap_v
    df["stop"]   = np.where(signal == 1,
                            lower - stop_buf * bw,
                            upper + stop_buf * bw)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 3. Donchian Breakout
# ─────────────────────────────────────────────────────────────────────────────

def strategy_donchian(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    period   = params.get("dc_period", 20)
    vol_mult = params.get("vol_mult", 1.5)
    rr       = params.get("rr_ratio", 2.0)

    dc      = donchian(df["High"], df["Low"], period)
    df      = df.join(dc)
    atr_v   = atr(df["High"], df["Low"], df["Close"], 14)
    vol_avg = df["Volume"].rolling(20).mean()

    prev_upper = df["DC_upper"].shift(1)
    prev_lower = df["DC_lower"].shift(1)
    vol_confirm = df["Volume"] > vol_mult * vol_avg

    long_sig  = (df["Close"] > prev_upper) & vol_confirm
    short_sig = (df["Close"] < prev_lower) & vol_confirm

    df["signal"] = np.where(long_sig, 1, np.where(short_sig, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Close"] - atr_v,
                            df["Close"] + atr_v)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 4. Opening Range Breakout
# ─────────────────────────────────────────────────────────────────────────────

def strategy_orb(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """OR Breakout — hourly bars only. OR = first 2 RTH bars (9AM + 10AM ET)."""
    min_range   = params.get("min_range", 3.0)
    cutoff_hour = params.get("cutoff_hour", 15)

    signal = pd.Series(0, index=df.index)
    target = pd.Series(np.nan, index=df.index)
    stop   = pd.Series(np.nan, index=df.index)

    try:
        local_idx = df.index.tz_convert("America/New_York") if df.index.tz else df.index
    except Exception:
        local_idx = df.index

    dates = {}
    for i, dt in enumerate(local_idx):
        d = dt.date()
        if d not in dates:
            dates[d] = []
        dates[d].append(i)

    for d, idxs in dates.items():
        # OR = first 2 bars of the day that are 9AM and 10AM
        or_bars = [i for i in idxs if local_idx[i].hour in (9, 10)][:2]
        if len(or_bars) < 2:
            continue
        or_high = df["High"].iloc[or_bars].max()
        or_low  = df["Low"].iloc[or_bars].min()
        or_range = or_high - or_low
        if or_range < min_range:
            continue

        signal_bars = [i for i in idxs
                       if 11 <= local_idx[i].hour < cutoff_hour
                       and i not in or_bars]
        for i in signal_bars:
            if signal.iloc[i] != 0:
                continue
            if df["Close"].iloc[i] > or_high:
                signal.iloc[i]  = 1
                target.iloc[i]  = or_high + or_range
                stop.iloc[i]    = or_low
                break
            elif df["Close"].iloc[i] < or_low:
                signal.iloc[i]  = -1
                target.iloc[i]  = or_low - or_range
                stop.iloc[i]    = or_high
                break

    df["signal"] = signal
    df["target"] = target
    df["stop"]   = stop
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 5. EMA Crossover
# ─────────────────────────────────────────────────────────────────────────────

def strategy_ema_cross(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    fast     = params.get("ema_fast", 9)
    slow     = params.get("ema_slow", 21)
    rsi_per  = params.get("rsi_period", 14)
    vol_sma  = params.get("vol_sma", 20)
    rr       = params.get("rr_ratio", 2.0)

    fast_e  = ema(df["Close"], fast)
    slow_e  = ema(df["Close"], slow)
    rsi_v   = rsi(df["Close"], rsi_per)
    vol_avg = df["Volume"].rolling(vol_sma).mean()
    atr_v   = atr(df["High"], df["Low"], df["Close"], 14)

    prev_fast = fast_e.shift(1)
    prev_slow = slow_e.shift(1)

    long_cross  = (prev_fast <= prev_slow) & (fast_e > slow_e)
    short_cross = (prev_fast >= prev_slow) & (fast_e < slow_e)
    vol_ok      = df["Volume"] > vol_avg

    df["signal"] = np.where(long_cross  & (rsi_v > 50) & vol_ok, 1,
                   np.where(short_cross & (rsi_v < 50) & vol_ok, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Close"] - atr_v,
                            df["Close"] + atr_v)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 6. MACD Crossover
# ─────────────────────────────────────────────────────────────────────────────

def strategy_macd(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    fast     = params.get("macd_fast", 12)
    slow_    = params.get("macd_slow", 26)
    sig      = params.get("macd_signal", 9)
    rr       = params.get("rr_ratio", 2.0)

    m     = macd(df["Close"], fast, slow_, sig)
    df    = df.join(m)
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)

    prev_macd = df["MACD"].shift(1)
    prev_sig  = df["MACD_signal"].shift(1)

    long_x  = (prev_macd <= prev_sig) & (df["MACD"] > df["MACD_signal"])
    short_x = (prev_macd >= prev_sig) & (df["MACD"] < df["MACD_signal"])
    # Confirm: histogram growing
    hist_grow_up   = df["MACD_hist"] > df["MACD_hist"].shift(1)
    hist_grow_down = df["MACD_hist"] < df["MACD_hist"].shift(1)

    df["signal"] = np.where(long_x  & hist_grow_up,   1,
                   np.where(short_x & hist_grow_down, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Close"] - atr_v,
                            df["Close"] + atr_v)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 7. RSI Reversal
# ─────────────────────────────────────────────────────────────────────────────

def strategy_rsi_rev(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    period    = params.get("rsi_period", 14)
    ob        = params.get("overbought", 70)
    os_       = params.get("oversold", 30)
    rr        = params.get("rr_ratio", 2.0)

    rsi_v = rsi(df["Close"], period)
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)

    # Enter on cross back from extreme
    long_sig  = (rsi_v.shift(1) < os_) & (rsi_v >= os_)
    short_sig = (rsi_v.shift(1) > ob)  & (rsi_v <= ob)

    df["signal"] = np.where(long_sig, 1, np.where(short_sig, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Close"] - atr_v,
                            df["Close"] + atr_v)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 8. Keltner Channel Reversal / Breakout
# ─────────────────────────────────────────────────────────────────────────────

def strategy_keltner(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    period   = params.get("kc_period", 20)
    mult     = params.get("kc_mult", 2.0)
    mode     = params.get("mode", "reversion")   # "reversion" or "breakout"
    rr       = params.get("rr_ratio", 2.0)

    kc    = keltner_channels(df["High"], df["Low"], df["Close"], period, mult)
    df    = df.join(kc)
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)

    if mode == "reversion":
        long_sig  = (df["Close"] <= df["KC_lower"])
        short_sig = (df["Close"] >= df["KC_upper"])
        df["target"] = df["KC_mid"]
        df["stop"]   = np.where(long_sig,
                                df["KC_lower"] - atr_v,
                                df["KC_upper"] + atr_v)
    else:  # breakout
        prev_upper = df["KC_upper"].shift(1)
        prev_lower = df["KC_lower"].shift(1)
        long_sig   = df["Close"] > prev_upper
        short_sig  = df["Close"] < prev_lower
        df["target"] = np.where(long_sig,
                                df["Close"] + rr * atr_v,
                                df["Close"] - rr * atr_v)
        df["stop"]   = np.where(long_sig,
                                df["Close"] - atr_v,
                                df["Close"] + atr_v)

    df["signal"] = np.where(long_sig, 1, np.where(short_sig, -1, 0))
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 9. CCI Reversal
# ─────────────────────────────────────────────────────────────────────────────

def strategy_cci(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    period = params.get("cci_period", 20)
    ob     = params.get("overbought", 100)
    os_    = params.get("oversold", -100)
    rr     = params.get("rr_ratio", 2.0)

    cci_v = cci(df["High"], df["Low"], df["Close"], period)
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)

    long_sig  = (cci_v.shift(1) < os_) & (cci_v >= os_)
    short_sig = (cci_v.shift(1) > ob)  & (cci_v <= ob)

    df["signal"] = np.where(long_sig, 1, np.where(short_sig, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Close"] - atr_v,
                            df["Close"] + atr_v)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 10. Williams %R
# ─────────────────────────────────────────────────────────────────────────────

def strategy_williams_r(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    period = params.get("wr_period", 14)
    ob     = params.get("overbought", -20)
    os_    = params.get("oversold", -80)
    rr     = params.get("rr_ratio", 2.0)

    wr_v  = williams_r(df["High"], df["Low"], df["Close"], period)
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)

    long_sig  = (wr_v.shift(1) < os_) & (wr_v >= os_)
    short_sig = (wr_v.shift(1) > ob)  & (wr_v <= ob)

    df["signal"] = np.where(long_sig, 1, np.where(short_sig, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Close"] - atr_v,
                            df["Close"] + atr_v)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 11. Stochastic
# ─────────────────────────────────────────────────────────────────────────────

def strategy_stochastic(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    k_per  = params.get("k_period", 14)
    d_per  = params.get("d_period", 3)
    ob     = params.get("overbought", 80)
    os_    = params.get("oversold", 20)
    rr     = params.get("rr_ratio", 2.0)

    st    = stochastic(df["High"], df["Low"], df["Close"], k_per, d_per)
    df    = df.join(st)
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)

    # K crosses D from oversold
    long_sig  = (df["STOCH_K"] > df["STOCH_D"]) & (df["STOCH_K"].shift(1) <= df["STOCH_D"].shift(1)) & (df["STOCH_K"] < ob)
    short_sig = (df["STOCH_K"] < df["STOCH_D"]) & (df["STOCH_K"].shift(1) >= df["STOCH_D"].shift(1)) & (df["STOCH_K"] > os_)

    df["signal"] = np.where(long_sig, 1, np.where(short_sig, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Close"] - atr_v,
                            df["Close"] + atr_v)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 12. Supertrend
# ─────────────────────────────────────────────────────────────────────────────

def strategy_supertrend(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    period = params.get("st_period", 10)
    mult   = params.get("st_mult", 3.0)
    rr     = params.get("rr_ratio", 2.0)

    st    = supertrend(df["High"], df["Low"], df["Close"], period, mult)
    df    = df.join(st)
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)

    # Signal on direction flip
    dir_flip_up   = (df["ST_direction"] == 1)  & (df["ST_direction"].shift(1) == -1)
    dir_flip_down = (df["ST_direction"] == -1) & (df["ST_direction"].shift(1) == 1)

    df["signal"] = np.where(dir_flip_up, 1, np.where(dir_flip_down, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = df["ST_value"]
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 13. Triple EMA
# ─────────────────────────────────────────────────────────────────────────────

def strategy_triple_ema(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    fast = params.get("fast", 5)
    mid  = params.get("mid", 13)
    slow_ = params.get("slow", 34)
    rr   = params.get("rr_ratio", 2.0)

    te    = triple_ema(df["Close"], fast, mid, slow_)
    df    = df.join(te)
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)

    bull = (df["TEMA_fast"] > df["TEMA_mid"]) & (df["TEMA_mid"] > df["TEMA_slow"])
    bear = (df["TEMA_fast"] < df["TEMA_mid"]) & (df["TEMA_mid"] < df["TEMA_slow"])
    bull_entry = bull & ~bull.shift(1).fillna(False)
    bear_entry = bear & ~bear.shift(1).fillna(False)

    df["signal"] = np.where(bull_entry, 1, np.where(bear_entry, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Close"] - atr_v,
                            df["Close"] + atr_v)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 14. MFI Reversal
# ─────────────────────────────────────────────────────────────────────────────

def strategy_mfi(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    period = params.get("mfi_period", 14)
    ob     = params.get("overbought", 80)
    os_    = params.get("oversold", 20)
    rr     = params.get("rr_ratio", 2.0)

    mfi_v = mfi(df["High"], df["Low"], df["Close"], df["Volume"], period)
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)

    long_sig  = (mfi_v.shift(1) < os_) & (mfi_v >= os_)
    short_sig = (mfi_v.shift(1) > ob)  & (mfi_v <= ob)

    df["signal"] = np.where(long_sig, 1, np.where(short_sig, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Close"] - atr_v,
                            df["Close"] + atr_v)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 15. OBV Divergence
# ─────────────────────────────────────────────────────────────────────────────

def strategy_obv(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    lookback = params.get("lookback", 20)
    rr       = params.get("rr_ratio", 2.0)

    obv_v = obv(df["Close"], df["Volume"])
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)
    obv_ma = obv_v.rolling(10).mean()

    signal = pd.Series(0, index=df.index)
    for i in range(lookback, len(df)):
        price_window = df["Close"].iloc[i - lookback:i + 1].values
        obv_window   = obv_v.iloc[i - lookback:i + 1].values
        # Bearish divergence: price higher high, OBV lower high
        if price_window[-1] == price_window.max() and obv_window[-1] < obv_window.max():
            signal.iloc[i] = -1
        # Bullish divergence: price lower low, OBV higher low
        elif price_window[-1] == price_window.min() and obv_window[-1] > obv_window.min():
            signal.iloc[i] = 1

    df["signal"] = signal
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Close"] - atr_v,
                            df["Close"] + atr_v)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 16. Elder Ray
# ─────────────────────────────────────────────────────────────────────────────

def strategy_elder_ray(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    period = params.get("er_period", 13)
    rr     = params.get("rr_ratio", 2.0)

    er    = elder_ray(df["Close"], df["High"], df["Low"], period)
    df    = df.join(er)
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)

    # Bull: bull power turns positive from negative, bear power negative (trend up)
    long_sig  = (df["ER_bull"] > 0) & (df["ER_bull"].shift(1) <= 0) & (df["ER_bear"] < 0)
    short_sig = (df["ER_bear"] < 0) & (df["ER_bear"].shift(1) >= 0) & (df["ER_bull"] > 0)
    # More practical: bull power crosses zero
    long_sig  = (df["ER_bull"] > 0) & (df["ER_bull"].shift(1) <= 0)
    short_sig = (df["ER_bear"] < 0) & (df["ER_bear"].shift(1) >= 0)

    df["signal"] = np.where(long_sig, 1, np.where(short_sig, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Close"] - atr_v,
                            df["Close"] + atr_v)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 17. Ichimoku
# ─────────────────────────────────────────────────────────────────────────────

def strategy_ichimoku(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    conv  = params.get("conversion", 9)
    base  = params.get("base", 26)
    rr    = params.get("rr_ratio", 2.0)

    ich   = ichimoku(df["High"], df["Low"], conv, base)
    df    = df.join(ich)
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)

    # Price above cloud AND TK cross
    cloud_top = df[["ICH_span_a", "ICH_span_b"]].max(axis=1)
    cloud_bot = df[["ICH_span_a", "ICH_span_b"]].min(axis=1)

    tk_cross_up   = (df["ICH_conv"] > df["ICH_base"]) & (df["ICH_conv"].shift(1) <= df["ICH_base"].shift(1))
    tk_cross_down = (df["ICH_conv"] < df["ICH_base"]) & (df["ICH_conv"].shift(1) >= df["ICH_base"].shift(1))

    long_sig  = tk_cross_up   & (df["Close"] > cloud_top)
    short_sig = tk_cross_down & (df["Close"] < cloud_bot)

    df["signal"] = np.where(long_sig, 1, np.where(short_sig, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["ICH_base"],
                            df["ICH_base"])
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 18. ATR Channel Breakout
# ─────────────────────────────────────────────────────────────────────────────

def strategy_atr_channel(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    ema_per = params.get("ema_period", 20)
    atr_per = params.get("atr_period", 14)
    mult    = params.get("multiplier", 1.5)
    rr      = params.get("rr_ratio", 2.0)

    from engines.indicators import atr_channel as atrc
    ac    = atrc(df["Close"], df["High"], df["Low"], ema_per, atr_per, mult)
    df    = df.join(ac)
    atr_v = atr(df["High"], df["Low"], df["Close"], atr_per)

    long_sig  = (df["Close"] > df["ATRC_upper"]) & (df["Close"].shift(1) <= df["ATRC_upper"].shift(1))
    short_sig = (df["Close"] < df["ATRC_lower"]) & (df["Close"].shift(1) >= df["ATRC_lower"].shift(1))

    df["signal"] = np.where(long_sig, 1, np.where(short_sig, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["ATRC_mid"] - atr_v,
                            df["ATRC_mid"] + atr_v)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 19. Pivot Point Reversal
# ─────────────────────────────────────────────────────────────────────────────

def strategy_pivot(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    rr = params.get("rr_ratio", 2.0)

    # Use daily OHLC resample for pivots
    daily = df.resample("1D").agg({
        "Open": "first", "High": "max", "Low": "min", "Close": "last"
    }).dropna()
    piv = pivot_points(daily["High"], daily["Low"], daily["Close"])

    # Forward-fill pivot levels onto intraday df
    piv_ff = piv.reindex(df.index, method="ffill")
    df = df.join(piv_ff)
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)

    # Signal: price touches S1/R1 and reverses
    near_r1 = (df["High"] >= df["R1"]) & (df["Close"] < df["R1"])
    near_s1 = (df["Low"]  <= df["S1"]) & (df["Close"] > df["S1"])

    df["signal"] = np.where(near_s1, 1, np.where(near_r1, -1, 0))
    df["target"] = np.where(df["signal"] == 1, df["PP"], df["PP"])
    df["stop"]   = np.where(df["signal"] == 1,
                            df["S1"] - atr_v,
                            df["R1"] + atr_v)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 20. RSI + MACD Confluence
# ─────────────────────────────────────────────────────────────────────────────

def strategy_rsi_macd(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    rsi_per    = params.get("rsi_period", 14)
    macd_fast  = params.get("macd_fast", 12)
    macd_slow  = params.get("macd_slow", 26)
    macd_sig   = params.get("macd_signal", 9)
    rr         = params.get("rr_ratio", 2.0)

    rsi_v = rsi(df["Close"], rsi_per)
    m     = macd(df["Close"], macd_fast, macd_slow, macd_sig)
    df    = df.join(m)
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)

    macd_cross_up   = (df["MACD"] > df["MACD_signal"]) & (df["MACD"].shift(1) <= df["MACD_signal"].shift(1))
    macd_cross_down = (df["MACD"] < df["MACD_signal"]) & (df["MACD"].shift(1) >= df["MACD_signal"].shift(1))

    df["signal"] = np.where(macd_cross_up   & (rsi_v > 40) & (rsi_v < 70), 1,
                   np.where(macd_cross_down & (rsi_v < 60) & (rsi_v > 30), -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Close"] - atr_v,
                            df["Close"] + atr_v)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 21. BB Width Squeeze
# ─────────────────────────────────────────────────────────────────────────────

def strategy_bb_squeeze(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    bb_per   = params.get("bb_period", 20)
    bb_std   = params.get("bb_std", 2.0)
    kc_per   = params.get("kc_period", 20)
    kc_mult  = params.get("kc_mult", 1.5)
    rr       = params.get("rr_ratio", 2.0)

    bb  = bollinger_bands(df["Close"], bb_per, bb_std)
    kc  = keltner_channels(df["High"], df["Low"], df["Close"], kc_per, kc_mult)
    df  = df.join(bb).join(kc)
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)
    mom = df["Close"] - df["Close"].rolling(bb_per).mean()

    # Squeeze: BB inside KC
    squeeze = (df["BB_upper"] < df["KC_upper"]) & (df["BB_lower"] > df["KC_lower"])
    # Release: squeeze was True, now BB breaks out of KC
    squeeze_release_up   = (~squeeze) & squeeze.shift(1).fillna(False) & (mom > 0)
    squeeze_release_down = (~squeeze) & squeeze.shift(1).fillna(False) & (mom < 0)

    df["signal"] = np.where(squeeze_release_up, 1, np.where(squeeze_release_down, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Close"] - atr_v,
                            df["Close"] + atr_v)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 22. Volume Surge Breakout
# ─────────────────────────────────────────────────────────────────────────────

def strategy_volume_surge(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    vol_mult  = params.get("vol_mult", 3.0)
    lookback  = params.get("lookback", 20)
    rr        = params.get("rr_ratio", 2.0)

    vol_avg = df["Volume"].rolling(lookback).mean()
    vol_surge = df["Volume"] > vol_mult * vol_avg
    atr_v  = atr(df["High"], df["Low"], df["Close"], 14)

    bull_surge = vol_surge & (df["Close"] > df["Open"])
    bear_surge = vol_surge & (df["Close"] < df["Open"])

    df["signal"] = np.where(bull_surge, 1, np.where(bear_surge, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Low"] - 0.5 * atr_v,
                            df["High"] + 0.5 * atr_v)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 23. Inside Bar Breakout
# ─────────────────────────────────────────────────────────────────────────────

def strategy_inside_bar(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    rr = params.get("rr_ratio", 2.0)

    inside = (df["High"] < df["High"].shift(1)) & (df["Low"] > df["Low"].shift(1))
    atr_v  = atr(df["High"], df["Low"], df["Close"], 14)

    # Entry on next bar breakout of inside bar
    signal = pd.Series(0, index=df.index)
    for i in range(2, len(df)):
        if inside.iloc[i - 1]:
            mother_high = df["High"].iloc[i - 2]
            mother_low  = df["Low"].iloc[i - 2]
            if df["Close"].iloc[i] > mother_high:
                signal.iloc[i] = 1
            elif df["Close"].iloc[i] < mother_low:
                signal.iloc[i] = -1

    df["signal"] = signal
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Close"] - atr_v,
                            df["Close"] + atr_v)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 24. Market Structure (HH/HL / LL/LH)
# ─────────────────────────────────────────────────────────────────────────────

def strategy_market_structure(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    swing_period = params.get("swing_period", 5)
    rr           = params.get("rr_ratio", 2.0)

    atr_v   = atr(df["High"], df["Low"], df["Close"], 14)
    roll_h  = df["High"].rolling(swing_period).max()
    roll_l  = df["Low"].rolling(swing_period).min()

    # HH: new high above previous swing high
    prev_hh = roll_h.shift(swing_period)
    prev_ll = roll_l.shift(swing_period)

    bull_struct = (df["High"] > prev_hh) & (df["Low"] > prev_ll)
    bear_struct = (df["Low"]  < prev_ll) & (df["High"] < prev_hh)
    bull_entry  = bull_struct & ~bull_struct.shift(1).fillna(False)
    bear_entry  = bear_struct & ~bear_struct.shift(1).fillna(False)

    df["signal"] = np.where(bull_entry, 1, np.where(bear_entry, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Low"] - 0.5 * atr_v,
                            df["High"] + 0.5 * atr_v)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 25. Gap Fill
# ─────────────────────────────────────────────────────────────────────────────

def strategy_gap_fill(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    min_gap_pct = params.get("min_gap_pct", 0.002)
    rr          = params.get("rr_ratio", 1.5)

    gap = (df["Open"] - df["Close"].shift(1)) / df["Close"].shift(1)
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)

    # Gap up → short to fill; gap down → long to fill
    gap_up   = gap >  min_gap_pct
    gap_down = gap < -min_gap_pct

    df["signal"] = np.where(gap_down, 1, np.where(gap_up, -1, 0))
    # Target: previous close (gap fill)
    df["target"] = df["Close"].shift(1)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Open"] - atr_v,
                            df["Open"] + atr_v)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Strategy registry
# ─────────────────────────────────────────────────────────────────────────────

from engines.orderflow import (
    strategy_orderflow_delta,
    strategy_absorption_reversal,
    strategy_trapped_breakout,
    strategy_tape_momentum,
    strategy_evr_reversal,
    strategy_iceberg_reversal,
    strategy_delta_exhaustion,
    strategy_stop_hunt,
    strategy_order_block,
    strategy_fair_value_gap,
    strategy_volume_profile_poc,
    strategy_bid_ask_imbalance,
    strategy_exhaustion_gap,
    strategy_cumulative_delta_trend,
    strategy_tape_exhaustion_reversal,
)

STRATEGY_MAP = {
    # Classic strategies
    "bb_cvd":           strategy_bb_cvd,
    "vwap_rev":         strategy_vwap_rev,
    "donchian":         strategy_donchian,
    "orb":              strategy_orb,
    "ema_cross":        strategy_ema_cross,
    "macd":             strategy_macd,
    "rsi_rev":          strategy_rsi_rev,
    "keltner":          strategy_keltner,
    "cci":              strategy_cci,
    "williams_r":       strategy_williams_r,
    "stochastic":       strategy_stochastic,
    "supertrend":       strategy_supertrend,
    "triple_ema":       strategy_triple_ema,
    "mfi":              strategy_mfi,
    "obv":              strategy_obv,
    "elder_ray":        strategy_elder_ray,
    "ichimoku":         strategy_ichimoku,
    "atr_channel":      strategy_atr_channel,
    "pivot":            strategy_pivot,
    "rsi_macd":         strategy_rsi_macd,
    "bb_squeeze":       strategy_bb_squeeze,
    "volume_surge":     strategy_volume_surge,
    "inside_bar":       strategy_inside_bar,
    "market_structure": strategy_market_structure,
    "gap_fill":         strategy_gap_fill,
    # Order flow / tape strategies
    "orderflow_delta":          strategy_orderflow_delta,
    "absorption_reversal":      strategy_absorption_reversal,
    "trapped_breakout":         strategy_trapped_breakout,
    "tape_momentum":            strategy_tape_momentum,
    "evr_reversal":             strategy_evr_reversal,
    "iceberg_reversal":         strategy_iceberg_reversal,
    "delta_exhaustion":         strategy_delta_exhaustion,
    "stop_hunt":                strategy_stop_hunt,
    "order_block":              strategy_order_block,
    "fair_value_gap":           strategy_fair_value_gap,
    "volume_profile_poc":       strategy_volume_profile_poc,
    "bid_ask_imbalance":        strategy_bid_ask_imbalance,
    "exhaustion_gap":           strategy_exhaustion_gap,
    "cumulative_delta_trend":   strategy_cumulative_delta_trend,
    "tape_exhaustion_reversal": strategy_tape_exhaustion_reversal,
}
