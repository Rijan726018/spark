"""Smoke tests for strategy signal generators."""
import numpy as np
import pandas as pd
import pytest


def make_ohlcv(n: int = 200, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 5200.0 + rng.normal(0, 10, n).cumsum()
    high  = close + rng.uniform(0.5, 3, n)
    low   = close - rng.uniform(0.5, 3, n)
    open_ = close + rng.normal(0, 1, n)
    vol   = rng.integers(800, 2500, n).astype(float)
    idx   = pd.date_range("2024-01-01", periods=n, freq="5min")
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": vol},
        index=idx,
    )


# ── strategy output contract ──────────────────────────────────────────────────

def assert_strategy_contract(result: pd.DataFrame, n: int):
    """Every strategy must return a DataFrame with signal, target, stop columns."""
    assert "signal" in result.columns, "Missing 'signal' column"
    assert "target" in result.columns, "Missing 'target' column"
    assert "stop"   in result.columns, "Missing 'stop' column"
    assert len(result) == n, "Row count changed"
    assert result["signal"].isin([-1, 0, 1]).all(), "Signals must be -1, 0, or 1"


# ── individual strategy tests ─────────────────────────────────────────────────

class TestStrategyBbCvd:
    def test_returns_correct_columns(self):
        from engines.strategies import strategy_bb_cvd
        df = make_ohlcv()
        result = strategy_bb_cvd(df.copy(), {"bb_period": 20, "bb_std": 2.0, "cvd_lookback": 5})
        assert_strategy_contract(result, len(df))

    def test_produces_some_signals(self):
        from engines.strategies import strategy_bb_cvd
        df = make_ohlcv(500)
        result = strategy_bb_cvd(df.copy(), {"bb_period": 20, "bb_std": 2.0, "cvd_lookback": 5})
        assert result["signal"].abs().sum() > 0, "Expected at least one signal in 500 bars"


class TestStrategyVwapRev:
    def test_returns_correct_columns(self):
        from engines.strategies import strategy_vwap_rev
        df = make_ohlcv()
        result = strategy_vwap_rev(df.copy(), {"upper_band": 2.5, "lower_band": 2.5, "stop_buffer": 0.3})
        assert_strategy_contract(result, len(df))


class TestStrategyMomentumBreakout:
    def test_returns_correct_columns(self):
        from engines.strategies import strategy_donchian
        df = make_ohlcv()
        result = strategy_donchian(df.copy(), {"dc_period": 20, "vol_mult": 1.5, "rr_ratio": 2.0})
        assert_strategy_contract(result, len(df))


# ── indicator sanity checks ───────────────────────────────────────────────────

class TestIndicators:
    def test_ema_length(self):
        from engines.indicators import ema
        close = pd.Series(range(100), dtype=float)
        result = ema(close, 20)
        assert len(result) == 100

    def test_bollinger_bands_columns(self):
        from engines.indicators import bollinger_bands
        close = pd.Series(range(100), dtype=float)
        result = bollinger_bands(close, 20, 2.0)
        assert set(result.columns) == {"BB_upper", "BB_mid", "BB_lower"}

    def test_rsi_bounded(self):
        from engines.indicators import rsi
        close = pd.Series(range(200), dtype=float)
        result = rsi(close, 14).dropna()
        assert (result >= 0).all() and (result <= 100).all()

    def test_atr_positive(self):
        from engines.indicators import atr
        df = make_ohlcv()
        result = atr(df["High"], df["Low"], df["Close"], 14).dropna()
        assert (result > 0).all()
