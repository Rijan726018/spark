"""
ParametricAlgoLoader — generates importable algo modules at runtime from config.

Instead of 600+ generated_algos/algo_NNN.py files on disk, this module
synthesises a strategy callable for any config that declares an 'engine' key.
The ConfigLoader in utils/config_loader.py is the source of truth for params.

Usage (in server/main.py or similar):
    from engines.parametric_loader import get_strategy_fn
    fn = get_strategy_fn("bb_cvd")
    result_df = fn(ohlcv_df, params)
"""

import logging
from typing import Callable, Optional

import pandas as pd

logger = logging.getLogger("nexus.parametric_loader")

# Map engine key → strategy function name in engines.strategies
_ENGINE_MAP: dict[str, str] = {
    "bb_cvd":      "strategy_bb_cvd",
    "vwap_rev":    "strategy_vwap_rev",
    "donchian":    "strategy_donchian",
    "orb":         "strategy_orb",
    "ema_cross":   "strategy_ema_cross",
    "macd":        "strategy_macd",
    "rsi_rev":     "strategy_rsi_rev",
    "keltner":     "strategy_keltner",
    "cci":         "strategy_cci",
    "williams_r":  "strategy_williams_r",
    "stochastic":  "strategy_stochastic",
    "supertrend":  "strategy_supertrend",
    "triple_ema":  "strategy_triple_ema",
    "mfi":         "strategy_mfi",
    "obv":         "strategy_obv",
    "elder_ray":   "strategy_elder_ray",
    "ichimoku":    "strategy_ichimoku",
    "atr_channel": "strategy_atr_channel",
    "pivot":       "strategy_pivot",
    "rsi_macd":    "strategy_rsi_macd",
    "bb_squeeze":  "strategy_bb_squeeze",
    "vol_surge":   "strategy_volume_surge",
    "inside_bar":  "strategy_inside_bar",
    "mkt_struct":  "strategy_market_structure",
    "gap_fill":    "strategy_gap_fill",
}


def get_strategy_fn(engine_key: str) -> Optional[Callable]:
    """Return the strategy function for the given engine key, or None if unknown."""
    fn_name = _ENGINE_MAP.get(engine_key)
    if not fn_name:
        logger.warning("Unknown engine key '%s' — no strategy function mapped", engine_key)
        return None
    try:
        import engines.strategies as _strat
        fn = getattr(_strat, fn_name, None)
        if fn is None:
            logger.error("engines.strategies has no function '%s'", fn_name)
        return fn
    except ImportError as exc:
        logger.error("Could not import engines.strategies: %s", exc)
        return None


def run_algo(config: dict, ohlcv: pd.DataFrame) -> pd.DataFrame:
    """
    Run a strategy from its config dict against the given OHLCV DataFrame.

    config must contain: 'engine' (str) and 'params' (dict).
    Returns the DataFrame with signal/target/stop columns added.
    Raises ValueError if the engine key is unrecognised.
    """
    engine  = config.get("engine", "")
    params  = config.get("params", {})

    fn = get_strategy_fn(engine)
    if fn is None:
        raise ValueError(
            f"Cannot run algo '{config.get('name', '?')}': "
            f"engine '{engine}' is not registered in ParametricLoader. "
            f"Available engines: {sorted(_ENGINE_MAP)}"
        )

    return fn(ohlcv.copy(), params)
