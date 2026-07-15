"""
Order Flow & Tape Reading Engine
─────────────────────────────────────────────────────────────────────────────
Approximates institutional order-flow metrics from OHLCV data.
For real tape (L2/DOM/tick data), replace the approximation functions
with live feed data from IB, Rithmic, CQG, etc.

Metrics implemented
───────────────────
1.  CVD          — Cumulative Volume Delta (buy vol - sell vol approximation)
2.  Delta Bar    — Per-bar buy/sell volume estimate
3.  Absorption   — Large volume at extreme with no price progress (stalling)
4.  Imbalance    — Bar body as % of range (directional pressure)
5.  Trapped Traders — Inside bar with large volume (trapped longs/shorts)
6.  Effort vs Result — ATR-normalised volume (high effort, little price move)
7.  Tape Speed   — Relative volume rate (urgency proxy)
8.  Composite Index — Weighted combination of all signals
9.  Footprint-style metrics — simulated bid/ask volume split per bar
10. Delta Divergence — CVD vs price divergence detection

All functions accept pandas Series/DataFrame and return Series/DataFrame.
"""
import numpy as np
import pandas as pd
from engines.indicators import atr, ema, sma


# ─────────────────────────────────────────────────────────────────────────────
# 1. Cumulative Volume Delta (CVD)
# ─────────────────────────────────────────────────────────────────────────────

def bar_delta(high: pd.Series, low: pd.Series,
              close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    Estimate buy vs sell volume per bar.
    Uses close position within bar as proxy:
      close_position = (close - low) / (high - low)
      buy_vol  = close_position * volume
      sell_vol = (1 - close_position) * volume
      delta    = buy_vol - sell_vol
    """
    rng = (high - low).replace(0, np.nan)
    close_pos = ((close - low) / rng).fillna(0.5).clip(0, 1)
    buy_vol  = close_pos * volume
    sell_vol = (1 - close_pos) * volume
    return (buy_vol - sell_vol).rename("BarDelta")


def cvd(high: pd.Series, low: pd.Series,
        close: pd.Series, volume: pd.Series) -> pd.Series:
    """Cumulative Volume Delta — running sum of bar_delta."""
    return bar_delta(high, low, close, volume).cumsum().rename("CVD")


def cvd_ma(cvd_series: pd.Series, period: int = 20) -> pd.Series:
    """Smoothed CVD baseline."""
    return cvd_series.rolling(period).mean().rename("CVD_MA")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Buy/Sell Volume (footprint approximation)
# ─────────────────────────────────────────────────────────────────────────────

def split_volume(high: pd.Series, low: pd.Series,
                 close: pd.Series, volume: pd.Series) -> pd.DataFrame:
    """
    Split each bar's volume into estimated buy / sell portions.
    Returns DataFrame with: buy_vol, sell_vol, delta, delta_pct
    """
    rng = (high - low).replace(0, np.nan)
    cp  = ((close - low) / rng).fillna(0.5).clip(0, 1)
    bv  = cp * volume
    sv  = (1 - cp) * volume
    delta = bv - sv
    delta_pct = (delta / volume.replace(0, np.nan) * 100).fillna(0)
    return pd.DataFrame({
        "buy_vol":   bv,
        "sell_vol":  sv,
        "delta":     delta,
        "delta_pct": delta_pct,
    }, index=close.index)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Absorption Detection
# ─────────────────────────────────────────────────────────────────────────────

def absorption(high: pd.Series, low: pd.Series,
               close: pd.Series, volume: pd.Series,
               vol_threshold: float = 2.0,
               move_threshold: float = 0.3) -> pd.Series:
    """
    Detects bars where high volume appears but price barely moves
    (absorption of supply/demand by large players).

      absorption_up   = +1: high vol at low range (buyers absorbing sellers)
      absorption_down = -1: high vol at low range (sellers absorbing buyers)
      0 = no absorption

    vol_threshold  : bar volume must be > vol_threshold × rolling avg vol
    move_threshold : bar body must be < move_threshold × ATR
    """
    atr_v   = atr(high, low, close, 14)
    vol_avg = volume.rolling(20).mean()
    body    = (close - close.shift(1)).abs()
    rng     = high - low

    high_vol   = volume > vol_threshold * vol_avg
    small_body = body < move_threshold * atr_v
    # Position of close within bar
    cp = ((close - low) / (rng).replace(0, np.nan)).fillna(0.5)

    # Absorption at bottom: high vol, small move, close in upper half (buyers won)
    abs_bull = high_vol & small_body & (cp > 0.5)
    # Absorption at top: high vol, small move, close in lower half (sellers won)
    abs_bear = high_vol & small_body & (cp < 0.5)

    return pd.Series(
        np.where(abs_bull, 1, np.where(abs_bear, -1, 0)),
        index=close.index, name="Absorption"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. Bar Imbalance
# ─────────────────────────────────────────────────────────────────────────────

def bar_imbalance(open_: pd.Series, high: pd.Series,
                  low: pd.Series, close: pd.Series) -> pd.Series:
    """
    Measures directional pressure of each bar.
    Imbalance = body / range  (positive = bullish, negative = bearish)
    -1 to +1 scale.
    """
    rng  = (high - low).replace(0, np.nan)
    body = close - open_
    return (body / rng).fillna(0).clip(-1, 1).rename("Imbalance")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Trapped Traders
# ─────────────────────────────────────────────────────────────────────────────

def trapped_traders(high: pd.Series, low: pd.Series,
                    close: pd.Series, volume: pd.Series,
                    vol_mult: float = 1.5) -> pd.Series:
    """
    Identifies inside bars (range < previous bar) with high volume.
    Indicates traders are trapped — breakout of the inside bar triggers:
      +1: breakout above (trapped shorts squeezed)
      -1: breakdown below (trapped longs stopped)
    """
    vol_avg = volume.rolling(20).mean()
    inside  = (high < high.shift(1)) & (low > low.shift(1))
    high_vol = volume > vol_mult * vol_avg

    trapped = inside & high_vol
    signal  = pd.Series(0, index=close.index)

    for i in range(2, len(close)):
        if trapped.iloc[i - 1]:
            mother_high = high.iloc[i - 2]
            mother_low  = low.iloc[i - 2]
            if close.iloc[i] > mother_high:
                signal.iloc[i] = 1
            elif close.iloc[i] < mother_low:
                signal.iloc[i] = -1

    return signal.rename("TrappedTraders")


# ─────────────────────────────────────────────────────────────────────────────
# 6. Effort vs Result (Wyckoff)
# ─────────────────────────────────────────────────────────────────────────────

def effort_vs_result(high: pd.Series, low: pd.Series,
                     close: pd.Series, volume: pd.Series,
                     period: int = 20) -> pd.DataFrame:
    """
    Compares volume (effort) to price range (result).
    High effort + low result = absorption / reversal likely.
    Low effort + high result = strong conviction move.

    Returns:
      effort_score  : normalised volume (z-score)
      result_score  : normalised bar range
      evr           : result / effort ratio (>1 = efficient move, <1 = absorption)
    """
    vol_z  = (volume - volume.rolling(period).mean()) / volume.rolling(period).std()
    rng    = high - low
    rng_z  = (rng - rng.rolling(period).mean()) / rng.rolling(period).std()
    evr    = (rng_z / vol_z.replace(0, np.nan)).fillna(0)

    return pd.DataFrame({
        "EVR_effort":  vol_z,
        "EVR_result":  rng_z,
        "EVR_ratio":   evr,
    }, index=close.index)


# ─────────────────────────────────────────────────────────────────────────────
# 7. Tape Speed (Volume Rate)
# ─────────────────────────────────────────────────────────────────────────────

def tape_speed(volume: pd.Series, fast: int = 5, slow: int = 20) -> pd.Series:
    """
    Relative tape speed: ratio of fast EMA to slow EMA of volume.
    >1 means volume is accelerating (urgent activity on the tape).
    <1 means volume is decelerating.
    """
    fast_v = volume.ewm(span=fast, adjust=False).mean()
    slow_v = volume.ewm(span=slow, adjust=False).mean()
    return (fast_v / slow_v.replace(0, np.nan)).fillna(1).rename("TapeSpeed")


# ─────────────────────────────────────────────────────────────────────────────
# 8. Composite Order Flow Score
# ─────────────────────────────────────────────────────────────────────────────

def composite_orderflow(high: pd.Series, low: pd.Series,
                         open_: pd.Series, close: pd.Series,
                         volume: pd.Series,
                         period: int = 20) -> pd.DataFrame:
    """
    Combines multiple order flow signals into a single composite score.
    Score range: -100 to +100
    Positive = net bullish order flow pressure
    Negative = net bearish order flow pressure
    """
    # Component 1: CVD momentum (is CVD rising or falling?)
    cvd_v   = cvd(high, low, close, volume)
    cvd_chg = cvd_v.diff(period)
    cvd_std = cvd_chg.rolling(period * 2).std().replace(0, np.nan)
    cvd_z   = (cvd_chg / cvd_std).fillna(0).clip(-3, 3) * 33.3

    # Component 2: Absorption signal (volume without price progress)
    abs_sig = absorption(high, low, close, volume).rolling(3).sum() * 10

    # Component 3: Bar imbalance rolling average
    imb = bar_imbalance(open_, high, low, close).rolling(5).mean() * 20

    # Component 4: Tape speed (volume surge confirms direction)
    ts  = (tape_speed(volume) - 1).clip(-1, 1) * 17

    # Component 5: Delta per bar as % of volume
    sv  = split_volume(high, low, close, volume)
    dv  = sv["delta_pct"].rolling(5).mean() * 0.2

    composite = (cvd_z + abs_sig + imb + ts + dv).clip(-100, 100)
    return pd.DataFrame({
        "OF_score":     composite,
        "OF_cvd_z":     cvd_z,
        "OF_absorb":    abs_sig,
        "OF_imbalance": imb,
        "OF_speed":     ts,
    }, index=close.index)


# ─────────────────────────────────────────────────────────────────────────────
# 9. Delta Divergence (Order Flow vs Price)
# ─────────────────────────────────────────────────────────────────────────────

def delta_divergence(high: pd.Series, low: pd.Series,
                      close: pd.Series, volume: pd.Series,
                      lookback: int = 10) -> pd.Series:
    """
    Detects divergence between price and CVD.
    Bullish: price makes lower low but CVD makes higher low (buying absorption)
    Bearish: price makes higher high but CVD makes lower high (selling distribution)
    Returns +1, -1, or 0.
    """
    cvd_v   = cvd(high, low, close, volume)
    signals = pd.Series(0, index=close.index)

    c = close.values
    d = cvd_v.values

    for i in range(lookback, len(c)):
        wc = c[i - lookback:i]
        wd = d[i - lookback:i]

        if c[i] <= wc.min():   # price at new low
            cvd_at_prev_low = wd[wc.argmin()]
            if d[i] > cvd_at_prev_low:   # CVD NOT at new low → bullish divergence
                signals.iloc[i] = 1

        elif c[i] >= wc.max():  # price at new high
            cvd_at_prev_high = wd[wc.argmax()]
            if d[i] < cvd_at_prev_high:  # CVD NOT at new high → bearish divergence
                signals.iloc[i] = -1

    return signals.rename("DeltaDivergence")


# ─────────────────────────────────────────────────────────────────────────────
# 10. Order Flow Strategies (strategy functions compatible with STRATEGY_MAP)
# ─────────────────────────────────────────────────────────────────────────────

def strategy_orderflow_delta(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Pure order flow strategy: trade CVD delta divergences confirmed by
    absorption. Requires price at Keltner extreme + delta divergence
    + absorption signal in same direction.
    """
    from engines.indicators import keltner_channels
    period   = params.get("kc_period", 20)
    mult     = params.get("kc_mult", 2.0)
    lb       = params.get("lookback", 10)
    rr       = params.get("rr_ratio", 2.0)
    vol_thr  = params.get("vol_threshold", 1.5)

    kc      = keltner_channels(df["High"], df["Low"], df["Close"], period, mult)
    df      = df.join(kc)
    atr_v   = atr(df["High"], df["Low"], df["Close"], 14)
    div_sig = delta_divergence(df["High"], df["Low"], df["Close"], df["Volume"], lb)
    abs_sig = absorption(df["High"], df["Low"], df["Close"], df["Volume"], vol_thr)

    long_sig  = (div_sig == 1) & (abs_sig == 1) & (df["Close"] <= df["KC_lower"])
    short_sig = (div_sig == -1) & (abs_sig == -1) & (df["Close"] >= df["KC_upper"])

    df["signal"] = np.where(long_sig, 1, np.where(short_sig, -1, 0))
    df["target"] = df["KC_mid"]
    df["stop"]   = np.where(long_sig,
                            df["KC_lower"] - atr_v,
                            df["KC_upper"] + atr_v)
    return df


def strategy_absorption_reversal(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Enters on absorption at Bollinger Band extremes.
    High volume + small move at band = institutional reversal signal.
    """
    from engines.indicators import bollinger_bands
    bb_per   = params.get("bb_period", 20)
    bb_std   = params.get("bb_std", 2.0)
    vol_thr  = params.get("vol_threshold", 2.0)
    move_thr = params.get("move_threshold", 0.3)
    rr       = params.get("rr_ratio", 2.0)

    bb    = bollinger_bands(df["Close"], bb_per, bb_std)
    df    = df.join(bb)
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)
    abs_v = absorption(df["High"], df["Low"], df["Close"], df["Volume"],
                       vol_thr, move_thr)

    long_sig  = (abs_v == 1) & (df["Close"] <= df["BB_lower"])
    short_sig = (abs_v == -1) & (df["Close"] >= df["BB_upper"])

    df["signal"] = np.where(long_sig, 1, np.where(short_sig, -1, 0))
    df["target"] = np.where(long_sig, df["BB_upper"], df["BB_lower"])
    df["stop"]   = np.where(long_sig,
                            df["BB_lower"] - atr_v,
                            df["BB_upper"] + atr_v)
    return df


def strategy_trapped_breakout(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Trades the release of trapped traders inside a high-volume inside bar.
    """
    vol_mult = params.get("vol_mult", 1.5)
    rr       = params.get("rr_ratio", 2.0)
    atr_v    = atr(df["High"], df["Low"], df["Close"], 14)

    sig = trapped_traders(df["High"], df["Low"], df["Close"], df["Volume"], vol_mult)
    df["signal"] = sig
    df["target"] = np.where(sig == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(sig == 1,
                            df["Low"] - 0.3 * atr_v,
                            df["High"] + 0.3 * atr_v)
    return df


def strategy_tape_momentum(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Trades accelerating tape (volume surge) in the direction of the
    composite order flow score.
    """
    speed_thresh = params.get("speed_threshold", 1.8)
    score_thresh = params.get("score_threshold", 20)
    rr           = params.get("rr_ratio", 2.0)

    ts    = tape_speed(df["Volume"])
    cof   = composite_orderflow(df["High"], df["Low"], df["Open"],
                                df["Close"], df["Volume"])
    df    = df.join(cof)
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)

    high_speed = ts > speed_thresh
    long_sig   = high_speed & (df["OF_score"] >  score_thresh)
    short_sig  = high_speed & (df["OF_score"] < -score_thresh)

    df["signal"] = np.where(long_sig, 1, np.where(short_sig, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Close"] - atr_v,
                            df["Close"] + atr_v)
    return df


def strategy_evr_reversal(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Effort vs Result reversal: high volume effort produces minimal price result
    at price extremes -> expect reversal.
    """
    from engines.indicators import bollinger_bands
    evr_thresh = params.get("evr_threshold", -0.5)
    bb_per     = params.get("bb_period", 20)
    rr         = params.get("rr_ratio", 2.0)

    evr_df = effort_vs_result(df["High"], df["Low"], df["Close"], df["Volume"])
    df     = df.join(evr_df)
    bb     = bollinger_bands(df["Close"], bb_per)
    df     = df.join(bb)
    atr_v  = atr(df["High"], df["Low"], df["Close"], 14)

    low_evr   = df["EVR_ratio"] < evr_thresh
    long_sig  = low_evr & (df["Close"] <= df["BB_lower"])
    short_sig = low_evr & (df["Close"] >= df["BB_upper"])

    df["signal"] = np.where(long_sig, 1, np.where(short_sig, -1, 0))
    df["target"] = np.where(long_sig, df["BB_upper"], df["BB_lower"])
    df["stop"]   = np.where(long_sig,
                            df["BB_lower"] - atr_v,
                            df["BB_upper"] + atr_v)
    return df


# =============================================================================
# ADVANCED ORDER FLOW & TAPE STRATEGIES
# =============================================================================

def iceberg_detector(high: pd.Series, low: pd.Series,
                     close: pd.Series, volume: pd.Series,
                     price_threshold: float = 0.002,
                     vol_mult: float = 3.0,
                     consecutive: int = 3) -> pd.Series:
    """
    Iceberg Order Detection.
    Icebergs show as repeated large volume bars clustered near the SAME price
    level with minimal price movement — the hidden portion of a large order
    keeps refilling at that level.

    Detection criteria:
      - N consecutive bars where price range < price_threshold * close
      - Volume on each bar > vol_mult * rolling average
      - Price stays within a tight band (no breakout)

    Returns +1 if bullish iceberg (buying at support), -1 if bearish (selling at resistance), 0 otherwise.
    """
    vol_avg   = volume.rolling(20).mean()
    bar_range = high - low
    tight     = bar_range < price_threshold * close
    high_vol  = volume > vol_mult * vol_avg

    iceberg_bar = tight & high_vol
    signal      = pd.Series(0, index=close.index)

    for i in range(consecutive, len(close)):
        window = iceberg_bar.iloc[i - consecutive:i + 1]
        if window.all():
            # Determine direction by net delta over the window
            d = bar_delta(high.iloc[i-consecutive:i+1],
                          low.iloc[i-consecutive:i+1],
                          close.iloc[i-consecutive:i+1],
                          volume.iloc[i-consecutive:i+1])
            net = d.sum()
            signal.iloc[i] = 1 if net > 0 else -1

    return signal.rename("Iceberg")


def strategy_iceberg_reversal(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Iceberg Reversal: enters when iceberg accumulation/distribution completes
    and price breaks out of the tight range where the iceberg was working.

    Bullish iceberg at support -> long on range breakout.
    Bearish iceberg at resistance -> short on breakdown.
    """
    price_thr  = params.get("price_threshold", 0.002)
    vol_mult   = params.get("vol_mult", 3.0)
    consec     = params.get("consecutive", 3)
    rr         = params.get("rr_ratio", 2.0)

    ice  = iceberg_detector(df["High"], df["Low"], df["Close"], df["Volume"],
                             price_thr, vol_mult, consec)
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)

    # Signal fires on the NEXT bar (breakout from the iceberg range)
    prev_ice = ice.shift(1)
    long_sig  = (prev_ice == 1)  & (df["Close"] > df["High"].shift(1))
    short_sig = (prev_ice == -1) & (df["Close"] < df["Low"].shift(1))

    df["signal"] = np.where(long_sig, 1, np.where(short_sig, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Low"].shift(1) - 0.3 * atr_v,
                            df["High"].shift(1) + 0.3 * atr_v)
    return df


def strategy_delta_exhaustion(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Delta Exhaustion: detects when cumulative delta reaches an extreme
    (buyers/sellers completely exhausted) and reverses.

    When CVD makes a new N-bar extreme but price fails to follow,
    the fuel for the move is gone. Counter-trend entry on exhaustion.
    """
    lookback   = params.get("lookback", 20)
    percentile = params.get("percentile", 90)
    rr         = params.get("rr_ratio", 2.0)

    cvd_v  = cvd(df["High"], df["Low"], df["Close"], df["Volume"])
    atr_v  = atr(df["High"], df["Low"], df["Close"], 14)

    # Compute rolling percentile thresholds
    cvd_high = cvd_v.rolling(lookback).quantile(percentile / 100)
    cvd_low  = cvd_v.rolling(lookback).quantile(1 - percentile / 100)

    # Exhaustion: CVD at extreme but price NOT at N-bar high/low
    price_high = df["Close"].rolling(lookback).max()
    price_low  = df["Close"].rolling(lookback).min()

    bull_exhaustion = (cvd_v >= cvd_high) & (df["Close"] < price_high * 0.998)
    bear_exhaustion = (cvd_v <= cvd_low)  & (df["Close"] > price_low  * 1.002)

    # Enter reversal on confirmation: next bar closes against the exhaustion
    long_sig  = bear_exhaustion.shift(1) & (df["Close"] > df["Close"].shift(1))
    short_sig = bull_exhaustion.shift(1) & (df["Close"] < df["Close"].shift(1))

    df["signal"] = np.where(long_sig, 1, np.where(short_sig, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Close"] - atr_v,
                            df["Close"] + atr_v)
    return df


def strategy_stop_hunt(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Stop Hunt / Liquidity Sweep Reversal.
    Detects when price briefly spikes below/above a key level (taking out stops)
    then quickly reverses — a classic institutional liquidity grab.

    Pattern:
      - Price wicks below N-bar low (sweeps stops) but CLOSES back above it
      - OR wicks above N-bar high but closes back below it
      - Volume confirms the sweep (institutional participation)
    """
    lookback = params.get("lookback", 20)
    vol_mult = params.get("vol_mult", 1.2)
    rr       = params.get("rr_ratio", 2.0)

    roll_high = df["High"].rolling(lookback).max().shift(1)
    roll_low  = df["Low"].rolling(lookback).min().shift(1)
    vol_avg   = df["Volume"].rolling(20).mean()
    atr_v     = atr(df["High"], df["Low"], df["Close"], 14)

    # Bullish stop hunt: wick below prior N-bar low, close back above it
    bull_sweep = (df["Low"] < roll_low) & (df["Close"] > roll_low) & (df["Volume"] > vol_mult * vol_avg)
    # Bearish stop hunt: wick above prior N-bar high, close back below it
    bear_sweep = (df["High"] > roll_high) & (df["Close"] < roll_high) & (df["Volume"] > vol_mult * vol_avg)

    df["signal"] = np.where(bull_sweep, 1, np.where(bear_sweep, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Low"] - 0.25 * atr_v,
                            df["High"] + 0.25 * atr_v)
    return df


def strategy_order_block(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Order Block Retest (Smart Money Concept).
    An order block is the last bearish candle before a bullish impulse (or vice versa).
    Price often returns to that candle to fill remaining institutional orders.

    Entry: when price retraces back into the order block zone and shows a reaction.
    Confirmation: volume spike or momentum turn on the retest.
    """
    swing_period = params.get("swing_period", 10)
    vol_mult     = params.get("vol_mult", 1.0)
    rr           = params.get("rr_ratio", 2.5)

    vol_avg = df["Volume"].rolling(20).mean()
    atr_v   = atr(df["High"], df["Low"], df["Close"], 14)

    # Find impulse moves: close moves > 1.5x ATR in one bar
    bar_move   = (df["Close"] - df["Open"]).abs()
    impulse    = bar_move > 1.5 * atr_v

    signal = pd.Series(0, index=df.index)
    for i in range(swing_period + 2, len(df)):
        if not impulse.iloc[i - 1]:
            continue
        bull_impulse = df["Close"].iloc[i-1] > df["Open"].iloc[i-1]
        # The order block is the candle BEFORE the impulse
        ob_high = df["High"].iloc[i-2]
        ob_low  = df["Low"].iloc[i-2]

        if bull_impulse:
            # Price in order block zone + volume confirmation = long
            in_ob = (df["Low"].iloc[i] <= ob_high) & (df["High"].iloc[i] >= ob_low)
            if in_ob and df["Close"].iloc[i] > df["Open"].iloc[i]:
                if df["Volume"].iloc[i] > vol_mult * vol_avg.iloc[i]:
                    signal.iloc[i] = 1
        else:
            # Bearish: price retraces into bearish order block
            in_ob = (df["Low"].iloc[i] <= ob_high) & (df["High"].iloc[i] >= ob_low)
            if in_ob and df["Close"].iloc[i] < df["Open"].iloc[i]:
                if df["Volume"].iloc[i] > vol_mult * vol_avg.iloc[i]:
                    signal.iloc[i] = -1

    df["signal"] = signal
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Low"] - 0.3 * atr_v,
                            df["High"] + 0.3 * atr_v)
    return df


def strategy_fair_value_gap(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Fair Value Gap (FVG) Fill — Smart Money Concept.
    An FVG forms when three consecutive bars leave a gap:
      Bullish FVG: Low[i] > High[i-2] (gap up, imbalance)
      Bearish FVG: High[i] < Low[i-2] (gap down, imbalance)

    Price tends to fill (return to) these gaps as institutions
    seek fair value. Entry when price retraces into the FVG zone.
    """
    max_bars_to_fill = params.get("max_bars_to_fill", 10)
    rr               = params.get("rr_ratio", 2.0)

    atr_v  = atr(df["High"], df["Low"], df["Close"], 14)
    signal = pd.Series(0, index=df.index)
    target_s = pd.Series(np.nan, index=df.index)
    stop_s   = pd.Series(np.nan, index=df.index)

    # Scan for FVGs
    fvg_bullish = {}  # bar_idx: (gap_low, gap_high)
    fvg_bearish = {}

    for i in range(2, len(df)):
        # Bullish FVG: current low > 2-bar-ago high
        if df["Low"].iloc[i] > df["High"].iloc[i - 2]:
            fvg_bullish[i] = (df["High"].iloc[i - 2], df["Low"].iloc[i])
        # Bearish FVG: current high < 2-bar-ago low
        if df["High"].iloc[i] < df["Low"].iloc[i - 2]:
            fvg_bearish[i] = (df["High"].iloc[i], df["Low"].iloc[i - 2])

    # Check if price retraces into FVG within max_bars_to_fill
    for fvg_i, (gap_low, gap_high) in fvg_bullish.items():
        for j in range(fvg_i + 1, min(fvg_i + max_bars_to_fill + 1, len(df))):
            if df["Low"].iloc[j] <= gap_high and df["Close"].iloc[j] >= gap_low:
                # Price dipped into FVG and recovered
                signal.iloc[j]   = 1
                target_s.iloc[j] = df["Close"].iloc[j] + 2.0 * atr_v.iloc[j]
                stop_s.iloc[j]   = gap_low - 0.25 * atr_v.iloc[j]
                break  # Only first retest

    for fvg_i, (gap_high, gap_low) in fvg_bearish.items():
        for j in range(fvg_i + 1, min(fvg_i + max_bars_to_fill + 1, len(df))):
            if df["High"].iloc[j] >= gap_high and df["Close"].iloc[j] <= gap_low:
                signal.iloc[j]   = -1
                target_s.iloc[j] = df["Close"].iloc[j] - 2.0 * atr_v.iloc[j]
                stop_s.iloc[j]   = gap_low + 0.25 * atr_v.iloc[j]
                break

    df["signal"] = signal
    df["target"] = target_s
    df["stop"]   = stop_s
    return df


def strategy_volume_profile_poc(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Volume Profile POC (Point of Control) Reversion.
    The POC is the price level with the most volume traded over N bars.
    Price is magnetically attracted back to the POC — similar to VWAP.

    Entry: when price deviates far from POC (> ATR distance) and shows reversal.
    Target: return to POC.
    """
    lookback    = params.get("lookback", 20)
    atr_mult    = params.get("atr_mult", 1.5)
    rr          = params.get("rr_ratio", 2.0)
    price_bins  = params.get("price_bins", 50)

    atr_v  = atr(df["High"], df["Low"], df["Close"], 14)
    signal = pd.Series(0, index=df.index)
    target_s = pd.Series(np.nan, index=df.index)
    stop_s   = pd.Series(np.nan, index=df.index)

    closes  = df["Close"].values
    volumes = df["Volume"].values
    highs   = df["High"].values
    lows    = df["Low"].values

    for i in range(lookback, len(df)):
        w_close  = closes[i - lookback:i]
        w_vol    = volumes[i - lookback:i]
        w_high   = highs[i - lookback:i]
        w_low    = lows[i - lookback:i]

        price_range = w_high.max() - w_low.min()
        if price_range == 0:
            continue

        # Build volume profile
        bins   = np.linspace(w_low.min(), w_high.max(), price_bins)
        vp     = np.zeros(len(bins) - 1)
        for j in range(len(w_close)):
            idx = np.searchsorted(bins, w_close[j]) - 1
            idx = max(0, min(idx, len(vp) - 1))
            vp[idx] += w_vol[j]

        poc_idx = vp.argmax()
        poc     = (bins[poc_idx] + bins[poc_idx + 1]) / 2
        cur     = closes[i]
        a       = atr_v.iloc[i] if not np.isnan(atr_v.iloc[i]) else price_range * 0.02

        # Long: price far below POC
        if cur < poc - atr_mult * a:
            signal.iloc[i]   = 1
            target_s.iloc[i] = poc
            stop_s.iloc[i]   = cur - a
        # Short: price far above POC
        elif cur > poc + atr_mult * a:
            signal.iloc[i]   = -1
            target_s.iloc[i] = poc
            stop_s.iloc[i]   = cur + a

    df["signal"] = signal
    df["target"] = target_s
    df["stop"]   = stop_s
    return df


def strategy_bid_ask_imbalance(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Bid/Ask Stack Imbalance.
    Uses the bar's body, wick structure, and volume to infer when
    one side of the book dominates. Large imbalance + trend confirmation
    = continuation entry.

    High buy imbalance: large body bullish bar, upper wick small, high volume.
    High sell imbalance: large body bearish bar, lower wick small, high volume.
    """
    imb_thresh = params.get("imbalance_threshold", 0.65)
    vol_mult   = params.get("vol_mult", 1.3)
    consec     = params.get("consecutive", 2)
    rr         = params.get("rr_ratio", 2.0)

    vol_avg = df["Volume"].rolling(20).mean()
    atr_v   = atr(df["High"], df["Low"], df["Close"], 14)

    body    = (df["Close"] - df["Open"]).abs()
    rng     = (df["High"] - df["Low"]).replace(0, np.nan)
    imb_raw = bar_imbalance(df["Open"], df["High"], df["Low"], df["Close"])

    high_vol  = df["Volume"] > vol_mult * vol_avg
    bull_imb  = (imb_raw > imb_thresh) & high_vol
    bear_imb  = (imb_raw < -imb_thresh) & high_vol

    # Require N consecutive imbalance bars
    bull_streak = bull_imb.rolling(consec).min().astype(bool)
    bear_streak = bear_imb.rolling(consec).min().astype(bool)

    df["signal"] = np.where(bull_streak, 1, np.where(bear_streak, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Low"].rolling(consec).min() - 0.2 * atr_v,
                            df["High"].rolling(consec).max() + 0.2 * atr_v)
    return df


def strategy_exhaustion_gap(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Exhaustion Gap Reversal.
    Gaps that appear after a long trend and on declining volume signal
    the final thrust of the move (exhaustion). Trade the reversal.

    Bullish exhaustion (short): gap up after uptrend, declining volume.
    Bearish exhaustion (long): gap down after downtrend, declining volume.
    """
    trend_period = params.get("trend_period", 20)
    min_gap_pct  = params.get("min_gap_pct", 0.001)
    vol_decline  = params.get("vol_decline", params.get("vol_decline_pct", 0.9))
    rr           = params.get("rr_ratio", 2.0)

    atr_v   = atr(df["High"], df["Low"], df["Close"], 14)
    vol_avg = df["Volume"].rolling(trend_period).mean()

    # Trend: price position in upper/lower 40% of N-bar range
    trend_high = df["Close"].rolling(trend_period).max()
    trend_low  = df["Close"].rolling(trend_period).min()
    rng        = (trend_high - trend_low).replace(0, np.nan)
    pos_in_rng = (df["Close"] - trend_low) / rng
    in_uptrend   = pos_in_rng > 0.6
    in_downtrend = pos_in_rng < 0.4

    gap    = (df["Open"] - df["Close"].shift(1)) / df["Close"].shift(1)
    gap_up = gap >  min_gap_pct
    gap_dn = gap < -min_gap_pct
    vol_weak = df["Volume"] < vol_decline * vol_avg

    # Exhaustion short: gap up in uptrend with weak volume
    exhaust_short = gap_up & in_uptrend & vol_weak
    # Exhaustion long: gap down in downtrend with weak volume
    exhaust_long  = gap_dn & in_downtrend & vol_weak

    df["signal"] = np.where(exhaust_long, 1, np.where(exhaust_short, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Open"] - atr_v,
                            df["Open"] + atr_v)
    return df


def strategy_cumulative_delta_trend(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    CVD Trend Following.
    Rather than looking for divergence, this strategy AGREES with CVD.
    When CVD is in a clear uptrend (rising EMA) AND price breaks above
    a resistance level, it confirms institutional buying pressure.
    Trend-following with order flow confirmation.
    """
    cvd_fast  = params.get("cvd_ema_fast", 10)
    cvd_slow  = params.get("cvd_ema_slow", 30)
    dc_period = params.get("dc_period", 20)
    rr        = params.get("rr_ratio", 2.0)

    from engines.indicators import donchian
    cvd_v = cvd(df["High"], df["Low"], df["Close"], df["Volume"])
    fast_e = cvd_v.ewm(span=cvd_fast, adjust=False).mean()
    slow_e = cvd_v.ewm(span=cvd_slow, adjust=False).mean()
    cvd_bull = fast_e > slow_e
    cvd_bear = fast_e < slow_e

    dc    = donchian(df["High"], df["Low"], dc_period)
    df    = df.join(dc)
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)

    prev_upper = df["DC_upper"].shift(1)
    prev_lower = df["DC_lower"].shift(1)

    long_sig  = (df["Close"] > prev_upper) & cvd_bull
    short_sig = (df["Close"] < prev_lower) & cvd_bear

    df["signal"] = np.where(long_sig, 1, np.where(short_sig, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Close"] - atr_v,
                            df["Close"] + atr_v)
    return df


def strategy_tape_exhaustion_reversal(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Tape Exhaustion Reversal.
    Combines tape speed (volume acceleration) with price stalling.
    When the tape is screaming (huge volume spike) but price barely moves,
    the move is exhausting. Fade the tape when effort meets no result.

    This is the most aggressive order-flow reversal strategy — high alpha,
    higher risk. Best used with tight stops at the bar extreme.
    """
    speed_thresh = params.get("speed_threshold", 2.5)
    move_thresh  = params.get("move_threshold", 0.25)
    rr           = params.get("rr_ratio", 2.0)

    ts    = tape_speed(df["Volume"], fast=3, slow=20)
    atr_v = atr(df["High"], df["Low"], df["Close"], 14)
    body  = (df["Close"] - df["Close"].shift(1)).abs()
    cp    = ((df["Close"] - df["Low"]) / (df["High"] - df["Low"]).replace(0, np.nan)).fillna(0.5)

    tape_scream  = ts > speed_thresh
    price_stall  = body < move_thresh * atr_v

    # Exhaustion at top: high tape, price barely up, close in lower half of bar
    exhaust_bear = tape_scream & price_stall & (cp < 0.4)
    # Exhaustion at bottom: high tape, price barely down, close in upper half
    exhaust_bull = tape_scream & price_stall & (cp > 0.6)

    df["signal"] = np.where(exhaust_bull, 1, np.where(exhaust_bear, -1, 0))
    df["target"] = np.where(df["signal"] == 1,
                            df["Close"] + rr * atr_v,
                            df["Close"] - rr * atr_v)
    df["stop"]   = np.where(df["signal"] == 1,
                            df["Low"] - 0.2 * atr_v,
                            df["High"] + 0.2 * atr_v)
    return df
