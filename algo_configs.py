"""
ALGO CONFIGS -- 500 Trading Algorithm Registry
Each config defines a fully described strategy for ES/NQ/Gold/Oil/Bond futures.
"""
from pathlib import Path

BASE = Path(__file__).parent

def p(rel):
    return str(BASE / rel) if rel else None

ALGO_CONFIGS = [

    {
        "id": '01', "name": 'BB + CVD DIVERGENCE', "category": 'Mean Reversion',
        "description": (
            'Enters when price touches the outer Bollinger Band (20-period, 2 sigma) while Cumulative Volume Delta diverges -- price makes a new extreme but CVD does not, revealing hidden absorption. Long at lower band when price makes lower low but CVD makes higher low; short at upper band when price makes higher high but CVD makes lower high. Target is always the opposite Bollinger Band. Stop is placed just beyond the signal band. Works best in liquid sessions with real volume data.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'LIVE', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": p("algos/algo_01_bb_cvd.py"), "csv": p("results/algo_01_trades.csv"), "alt_csv": p("results/algo_01_1h_trades.csv"),
        "chart": p("results/algo_01_bb_cvd.png"), "alt_chart": p("results/algo_01_bb_cvd_1h.png"),
        "alt_timeframe": '1h', "alt_period": '730d',
    },
    {
        "id": '02', "name": 'VWAP REVERSION', "category": 'Mean Reversion',
        "description": (
            'Identifies extreme VWAP deviations using intraday volume-weighted standard deviation bands that reset each session. When price crosses 2.5-sigma below VWAP and the next bar shows recovery (close > prior close), a long is entered targeting VWAP itself. The reverse applies for shorts above 2.5-sigma. Stop is placed 30% of the band width beyond the signal level. Filters out the first bar of each day where std is zero. Designed to capture rubber-band snapbacks to fair value.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'LIVE', "engine": 'vwap_rev',
        "params": {'upper_band': 2.5, 'lower_band': 2.5, 'stop_buffer': 0.3},
        "script": p("algos/algo_02_vwap_reversion.py"), "csv": p("results/algo_02_trades.csv"), "alt_csv": None,
        "chart": p("results/algo_02_vwap_reversion.png"), "alt_chart": None,
    },
    {
        "id": '03', "name": 'MOMENTUM BREAKOUT', "category": 'Breakout',
        "description": (
            'Uses a 20-bar Donchian Channel on 15-minute bars. A long signal fires when price closes above the prior channel high with volume exceeding 1.5x its 20-bar average, confirming institutional participation. ATR(14) sizes the trade: target is entry plus 2x ATR, stop is entry minus 1x ATR, giving a 2:1 reward-to-risk. The same logic inverted triggers shorts below the channel low. Volume filter eliminates false breakouts during thin overnight sessions.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'LIVE', "engine": 'donchian',
        "params": {'dc_period': 20, 'vol_mult': 1.5, 'rr_ratio': 2.0},
        "script": p("algos/algo_03_momentum_breakout.py"), "csv": p("results/algo_03_trades.csv"), "alt_csv": None,
        "chart": p("results/algo_03_momentum_breakout.png"), "alt_chart": None,
    },
    {
        "id": '04', "name": 'OPENING RANGE BREAKOUT', "category": 'Breakout',
        "description": (
            'Defines the opening range as the high and low of the first two hourly RTH bars (9AM and 10AM ET). A long triggers on the first hourly bar that closes above OR High; a short triggers on the first close below OR Low. Target equals the OR range projected from the breakout level; stop is the opposite OR level. Only one trade per day, no entries after 3 PM ET. Skips days with OR range below 3 points. Backtested on both ES and NQ across 730 days.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'LIVE', "engine": 'orb',
        "params": {'or_minutes': 30, 'min_range': 3.0, 'cutoff_hour': 15},
        "script": p("algos/algo_04_opening_range.py"), "csv": p("results/algo_04_trades.csv"), "alt_csv": None,
        "chart": p("results/algo_04_opening_range.png"), "alt_chart": None,
    },
    {
        "id": '05', "name": 'EMA CROSSOVER', "category": 'Trend Following',
        "description": (
            'A classic dual-EMA crossover system refined with RSI and volume confirmation. Enters long when the 9-period EMA crosses above the 21-period EMA, RSI(14) is above 50 (confirming momentum), and volume exceeds its 20-bar average. Target is 2x ATR(14) above entry; stop is 1x ATR below. Short signals use the reverse logic. Runs on 15-minute bars to filter out microstructure noise while remaining responsive to intraday trends.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'LIVE', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": p("algos/algo_05_ema_crossover.py"), "csv": p("results/algo_05_trades.csv"), "alt_csv": None,
        "chart": p("results/algo_05_ema_crossover.png"), "alt_chart": None,
    },
    {
        "id": '101', "name": 'BB+CVD ES 5m', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini S&P 500 5m bars during active sessions.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_101_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '102', "name": 'BB+CVD ES 5mB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini S&P 500 5m bars during active sessions.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_102_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '103', "name": 'BB+CVD ES 5mC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini S&P 500 5m bars during active sessions.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_103_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '104', "name": 'BB+CVD ES 15m', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini S&P 500 15m bars during active sessions.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_104_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '105', "name": 'BB+CVD ES 15mB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini S&P 500 15m bars during active sessions.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_105_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '106', "name": 'BB+CVD ES 15mC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini S&P 500 15m bars during active sessions.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_106_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '107', "name": 'BB+CVD ES 1h', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini S&P 500 1h bars during active sessions.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_107_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '108', "name": 'BB+CVD ES 1hB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini S&P 500 1h bars during active sessions.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_108_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '109', "name": 'BB+CVD ES 1hC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini S&P 500 1h bars during active sessions.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_109_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '110', "name": 'BB+CVD NQ 5m', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini NASDAQ 100 5m bars during active sessions.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_110_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '111', "name": 'BB+CVD NQ 5mB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini NASDAQ 100 5m bars during active sessions.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_111_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '112', "name": 'BB+CVD NQ 5mC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini NASDAQ 100 5m bars during active sessions.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_112_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '113', "name": 'BB+CVD NQ 15m', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini NASDAQ 100 15m bars during active sessions.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_113_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '114', "name": 'BB+CVD NQ 15mB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini NASDAQ 100 15m bars during active sessions.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_114_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '115', "name": 'BB+CVD NQ 15mC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini NASDAQ 100 15m bars during active sessions.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_115_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '116', "name": 'BB+CVD NQ 1h', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini NASDAQ 100 1h bars during active sessions.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_116_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '117', "name": 'BB+CVD NQ 1hB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini NASDAQ 100 1h bars during active sessions.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_117_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '118', "name": 'BB+CVD NQ 1hC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini NASDAQ 100 1h bars during active sessions.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_118_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '119', "name": 'BB+CVD YM 5m', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini Dow Jones 5m bars during active sessions.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_119_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '120', "name": 'BB+CVD YM 5mB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini Dow Jones 5m bars during active sessions.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_120_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '121', "name": 'BB+CVD YM 5mC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini Dow Jones 5m bars during active sessions.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_121_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '122', "name": 'BB+CVD YM 15m', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini Dow Jones 15m bars during active sessions.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_122_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '123', "name": 'BB+CVD YM 15mB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini Dow Jones 15m bars during active sessions.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_123_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '124', "name": 'BB+CVD YM 15mC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini Dow Jones 15m bars during active sessions.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_124_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '125', "name": 'BB+CVD YM 1h', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini Dow Jones 1h bars during active sessions.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_125_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '126', "name": 'BB+CVD YM 1hB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini Dow Jones 1h bars during active sessions.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_126_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '127', "name": 'BB+CVD YM 1hC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini Dow Jones 1h bars during active sessions.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_127_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '128', "name": 'BB+CVD RTY 5m', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini Russell 2000 5m bars during active sessions.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_128_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '129', "name": 'BB+CVD RTY 5mB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini Russell 2000 5m bars during active sessions.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_129_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '130', "name": 'BB+CVD RTY 5mC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini Russell 2000 5m bars during active sessions.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_130_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '131', "name": 'BB+CVD RTY 15m', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini Russell 2000 15m bars during active sessions.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_131_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '132', "name": 'BB+CVD RTY 15mB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini Russell 2000 15m bars during active sessions.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_132_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '133', "name": 'BB+CVD RTY 15mC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini Russell 2000 15m bars during active sessions.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_133_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '134', "name": 'BB+CVD RTY 1h', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini Russell 2000 1h bars during active sessions.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_134_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '135', "name": 'BB+CVD RTY 1hB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini Russell 2000 1h bars during active sessions.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_135_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '136', "name": 'BB+CVD RTY 1hC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on E-mini Russell 2000 1h bars during active sessions.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_136_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '137', "name": 'BB+CVD GC 5m', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Gold Futures 5m bars during active sessions.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_137_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '138', "name": 'BB+CVD GC 5mB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Gold Futures 5m bars during active sessions.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_138_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '139', "name": 'BB+CVD GC 5mC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Gold Futures 5m bars during active sessions.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_139_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '140', "name": 'BB+CVD GC 15m', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Gold Futures 15m bars during active sessions.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_140_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '141', "name": 'BB+CVD GC 15mB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Gold Futures 15m bars during active sessions.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_141_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '142', "name": 'BB+CVD GC 15mC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Gold Futures 15m bars during active sessions.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_142_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '143', "name": 'BB+CVD GC 1h', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Gold Futures 1h bars during active sessions.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_143_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '144', "name": 'BB+CVD GC 1hB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Gold Futures 1h bars during active sessions.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_144_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '145', "name": 'BB+CVD GC 1hC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Gold Futures 1h bars during active sessions.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_145_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '146', "name": 'BB+CVD SI 5m', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Silver Futures 5m bars during active sessions.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_146_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '147', "name": 'BB+CVD SI 5mB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Silver Futures 5m bars during active sessions.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_147_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '148', "name": 'BB+CVD SI 5mC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Silver Futures 5m bars during active sessions.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_148_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '149', "name": 'BB+CVD SI 15m', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Silver Futures 15m bars during active sessions.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_149_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '150', "name": 'BB+CVD SI 15mB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Silver Futures 15m bars during active sessions.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_150_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '151', "name": 'BB+CVD SI 15mC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Silver Futures 15m bars during active sessions.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_151_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '152', "name": 'BB+CVD SI 1h', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Silver Futures 1h bars during active sessions.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_152_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '153', "name": 'BB+CVD SI 1hB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Silver Futures 1h bars during active sessions.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_153_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '154', "name": 'BB+CVD SI 1hC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Silver Futures 1h bars during active sessions.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_154_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '155', "name": 'BB+CVD CL 5m', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Crude Oil Futures 5m bars during active sessions.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_155_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '156', "name": 'BB+CVD CL 5mB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Crude Oil Futures 5m bars during active sessions.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_156_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '157', "name": 'BB+CVD CL 5mC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Crude Oil Futures 5m bars during active sessions.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_157_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '158', "name": 'BB+CVD CL 15m', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Crude Oil Futures 15m bars during active sessions.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_158_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '159', "name": 'BB+CVD CL 15mB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Crude Oil Futures 15m bars during active sessions.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_159_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '160', "name": 'BB+CVD CL 15mC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Crude Oil Futures 15m bars during active sessions.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_160_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '161', "name": 'BB+CVD CL 1h', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Crude Oil Futures 1h bars during active sessions.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_161_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '162', "name": 'BB+CVD CL 1hB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Crude Oil Futures 1h bars during active sessions.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_162_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '163', "name": 'BB+CVD CL 1hC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Crude Oil Futures 1h bars during active sessions.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_163_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '164', "name": 'BB+CVD NG 5m', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Natural Gas Futures 5m bars during active sessions.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_164_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '165', "name": 'BB+CVD NG 5mB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Natural Gas Futures 5m bars during active sessions.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_165_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '166', "name": 'BB+CVD NG 5mC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Natural Gas Futures 5m bars during active sessions.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_166_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '167', "name": 'BB+CVD NG 15m', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Natural Gas Futures 15m bars during active sessions.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_167_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '168', "name": 'BB+CVD NG 15mB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Natural Gas Futures 15m bars during active sessions.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_168_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '169', "name": 'BB+CVD NG 15mC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Natural Gas Futures 15m bars during active sessions.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_169_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '170', "name": 'BB+CVD NG 1h', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Natural Gas Futures 1h bars during active sessions.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_170_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '171', "name": 'BB+CVD NG 1hB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Natural Gas Futures 1h bars during active sessions.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_171_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '172', "name": 'BB+CVD NG 1hC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on Natural Gas Futures 1h bars during active sessions.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_172_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '173', "name": 'BB+CVD ZB 15m', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on 30-Year T-Bond 15m bars during active sessions.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_173_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '174', "name": 'BB+CVD ZB 15mB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on 30-Year T-Bond 15m bars during active sessions.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_174_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '175', "name": 'BB+CVD ZB 15mC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on 30-Year T-Bond 15m bars during active sessions.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_175_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '176', "name": 'BB+CVD ZB 1h', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on 30-Year T-Bond 1h bars during active sessions.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_176_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '177', "name": 'BB+CVD ZB 1hB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on 30-Year T-Bond 1h bars during active sessions.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_177_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '178', "name": 'BB+CVD ZB 1hC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on 30-Year T-Bond 1h bars during active sessions.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_178_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '179', "name": 'BB+CVD ZN 15m', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on 10-Year T-Note 15m bars during active sessions.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_179_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '180', "name": 'BB+CVD ZN 15mB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on 10-Year T-Note 15m bars during active sessions.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_180_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '181', "name": 'BB+CVD ZN 15mC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on 10-Year T-Note 15m bars during active sessions.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_181_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '182', "name": 'BB+CVD ZN 1h', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on 10-Year T-Note 1h bars during active sessions.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 2.0, 'cvd_lookback': 5},
        "script": None, "csv": p("results/algo_182_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '183', "name": 'BB+CVD ZN 1hB', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (14,2.0σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on 10-Year T-Note 1h bars during active sessions.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 14, 'bb_std': 2.0, 'cvd_lookback': 3},
        "script": None, "csv": p("results/algo_183_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '184', "name": 'BB+CVD ZN 1hC', "category": 'Mean Reversion',
        "description": (
            'Bollinger Band (20,1.5σ) with Cumulative Volume Delta divergence. Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. Enters short at the upper band when CVD makes a lower high despite a price higher high. Target is always the opposite band; stop is just beyond the signal band. Effective on 10-Year T-Note 1h bars during active sessions.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bb_cvd',
        "params": {'bb_period': 20, 'bb_std': 1.5, 'cvd_lookback': 8},
        "script": None, "csv": p("results/algo_184_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '185', "name": 'RSI REV ES 5m', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on E-mini S&P 500 5m bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_185_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '186', "name": 'RSI REV ES 5mB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on E-mini S&P 500 5m bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_186_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '187', "name": 'RSI REV ES 5mC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on E-mini S&P 500 5m bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_187_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '188', "name": 'RSI REV ES 15m', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on E-mini S&P 500 15m bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_188_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '189', "name": 'RSI REV ES 15mB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on E-mini S&P 500 15m bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_189_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '190', "name": 'RSI REV ES 15mC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on E-mini S&P 500 15m bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_190_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '191', "name": 'RSI REV ES 1h', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on E-mini S&P 500 1h bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_191_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '192', "name": 'RSI REV ES 1hB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on E-mini S&P 500 1h bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_192_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '193', "name": 'RSI REV ES 1hC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on E-mini S&P 500 1h bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_193_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '194', "name": 'RSI REV NQ 5m', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on E-mini NASDAQ 100 5m bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_194_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '195', "name": 'RSI REV NQ 5mB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on E-mini NASDAQ 100 5m bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_195_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '196', "name": 'RSI REV NQ 5mC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on E-mini NASDAQ 100 5m bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_196_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '197', "name": 'RSI REV NQ 15m', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on E-mini NASDAQ 100 15m bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_197_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '198', "name": 'RSI REV NQ 15mB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on E-mini NASDAQ 100 15m bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_198_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '199', "name": 'RSI REV NQ 15mC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on E-mini NASDAQ 100 15m bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_199_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '200', "name": 'RSI REV NQ 1h', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on E-mini NASDAQ 100 1h bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_200_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '201', "name": 'RSI REV NQ 1hB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on E-mini NASDAQ 100 1h bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_201_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '202', "name": 'RSI REV NQ 1hC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on E-mini NASDAQ 100 1h bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_202_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '203', "name": 'RSI REV YM 5m', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on E-mini Dow Jones 5m bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_203_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '204', "name": 'RSI REV YM 5mB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on E-mini Dow Jones 5m bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_204_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '205', "name": 'RSI REV YM 5mC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on E-mini Dow Jones 5m bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_205_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '206', "name": 'RSI REV YM 15m', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on E-mini Dow Jones 15m bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_206_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '207', "name": 'RSI REV YM 15mB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on E-mini Dow Jones 15m bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_207_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '208', "name": 'RSI REV YM 15mC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on E-mini Dow Jones 15m bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_208_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '209', "name": 'RSI REV YM 1h', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on E-mini Dow Jones 1h bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_209_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '210', "name": 'RSI REV YM 1hB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on E-mini Dow Jones 1h bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_210_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '211', "name": 'RSI REV YM 1hC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on E-mini Dow Jones 1h bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_211_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '212', "name": 'RSI REV RTY 5m', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on E-mini Russell 2000 5m bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_212_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '213', "name": 'RSI REV RTY 5mB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on E-mini Russell 2000 5m bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_213_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '214', "name": 'RSI REV RTY 5mC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on E-mini Russell 2000 5m bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_214_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '215', "name": 'RSI REV RTY 15m', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on E-mini Russell 2000 15m bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_215_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '216', "name": 'RSI REV RTY 15mB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on E-mini Russell 2000 15m bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_216_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '217', "name": 'RSI REV RTY 15mC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on E-mini Russell 2000 15m bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_217_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '218', "name": 'RSI REV RTY 1h', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on E-mini Russell 2000 1h bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_218_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '219', "name": 'RSI REV RTY 1hB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on E-mini Russell 2000 1h bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_219_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '220', "name": 'RSI REV RTY 1hC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on E-mini Russell 2000 1h bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_220_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '221', "name": 'RSI REV GC 5m', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on Gold Futures 5m bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_221_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '222', "name": 'RSI REV GC 5mB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on Gold Futures 5m bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_222_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '223', "name": 'RSI REV GC 5mC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on Gold Futures 5m bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_223_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '224', "name": 'RSI REV GC 15m', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on Gold Futures 15m bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_224_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '225', "name": 'RSI REV GC 15mB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on Gold Futures 15m bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_225_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '226', "name": 'RSI REV GC 15mC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on Gold Futures 15m bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_226_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '227', "name": 'RSI REV GC 1h', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on Gold Futures 1h bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_227_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '228', "name": 'RSI REV GC 1hB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on Gold Futures 1h bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_228_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '229', "name": 'RSI REV GC 1hC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on Gold Futures 1h bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_229_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '230', "name": 'RSI REV SI 5m', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on Silver Futures 5m bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_230_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '231', "name": 'RSI REV SI 5mB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on Silver Futures 5m bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_231_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '232', "name": 'RSI REV SI 5mC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on Silver Futures 5m bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_232_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '233', "name": 'RSI REV SI 15m', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on Silver Futures 15m bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_233_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '234', "name": 'RSI REV SI 15mB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on Silver Futures 15m bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_234_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '235', "name": 'RSI REV SI 15mC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on Silver Futures 15m bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_235_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '236', "name": 'RSI REV SI 1h', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on Silver Futures 1h bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_236_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '237', "name": 'RSI REV SI 1hB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on Silver Futures 1h bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_237_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '238', "name": 'RSI REV SI 1hC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on Silver Futures 1h bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_238_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '239', "name": 'RSI REV CL 5m', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on Crude Oil Futures 5m bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_239_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '240', "name": 'RSI REV CL 5mB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on Crude Oil Futures 5m bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_240_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '241', "name": 'RSI REV CL 5mC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on Crude Oil Futures 5m bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_241_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '242', "name": 'RSI REV CL 15m', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on Crude Oil Futures 15m bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_242_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '243', "name": 'RSI REV CL 15mB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on Crude Oil Futures 15m bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_243_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '244', "name": 'RSI REV CL 15mC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on Crude Oil Futures 15m bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_244_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '245', "name": 'RSI REV CL 1h', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on Crude Oil Futures 1h bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_245_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '246', "name": 'RSI REV CL 1hB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on Crude Oil Futures 1h bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_246_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '247', "name": 'RSI REV CL 1hC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on Crude Oil Futures 1h bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_247_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '248', "name": 'RSI REV NG 5m', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on Natural Gas Futures 5m bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_248_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '249', "name": 'RSI REV NG 5mB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on Natural Gas Futures 5m bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_249_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '250', "name": 'RSI REV NG 5mC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on Natural Gas Futures 5m bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_250_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '251', "name": 'RSI REV NG 15m', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on Natural Gas Futures 15m bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_251_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '252', "name": 'RSI REV NG 15mB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on Natural Gas Futures 15m bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_252_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '253', "name": 'RSI REV NG 15mC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on Natural Gas Futures 15m bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_253_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '254', "name": 'RSI REV NG 1h', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on Natural Gas Futures 1h bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_254_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '255', "name": 'RSI REV NG 1hB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on Natural Gas Futures 1h bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_255_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '256', "name": 'RSI REV NG 1hC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on Natural Gas Futures 1h bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_256_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '257', "name": 'RSI REV ZB 15m', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on 30-Year T-Bond 15m bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_257_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '258', "name": 'RSI REV ZB 15mB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on 30-Year T-Bond 15m bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_258_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '259', "name": 'RSI REV ZB 15mC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on 30-Year T-Bond 15m bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_259_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '260', "name": 'RSI REV ZB 1h', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on 30-Year T-Bond 1h bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_260_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '261', "name": 'RSI REV ZB 1hB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on 30-Year T-Bond 1h bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_261_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '262', "name": 'RSI REV ZB 1hC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on 30-Year T-Bond 1h bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_262_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '263', "name": 'RSI REV ZN 15m', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on 10-Year T-Note 15m bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_263_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '264', "name": 'RSI REV ZN 15mB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on 10-Year T-Note 15m bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_264_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '265', "name": 'RSI REV ZN 15mC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on 10-Year T-Note 15m bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_265_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '266', "name": 'RSI REV ZN 1h', "category": 'Mean Reversion',
        "description": (
            'RSI(14) mean-reversion strategy on 10-Year T-Note 1h bars. Enters long when RSI crosses back above the oversold level (30), signalling exhausted selling. Enters short when RSI crosses back below overbought (70), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 14, 'overbought': 70, 'oversold': 30, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_266_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '267', "name": 'RSI REV ZN 1hB', "category": 'Mean Reversion',
        "description": (
            'RSI(9) mean-reversion strategy on 10-Year T-Note 1h bars. Enters long when RSI crosses back above the oversold level (25), signalling exhausted selling. Enters short when RSI crosses back below overbought (75), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 9, 'overbought': 75, 'oversold': 25, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_267_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '268', "name": 'RSI REV ZN 1hC', "category": 'Mean Reversion',
        "description": (
            'RSI(21) mean-reversion strategy on 10-Year T-Note 1h bars. Enters long when RSI crosses back above the oversold level (35), signalling exhausted selling. Enters short when RSI crosses back below overbought (65), signalling exhausted buying. ATR-based 2.0:1 reward-to-risk on every trade. Performs best in ranging, non-trending market conditions.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'rsi_rev',
        "params": {'rsi_period': 21, 'overbought': 65, 'oversold': 35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_268_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '269', "name": 'MACD ES 5m', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on E-mini S&P 500. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_269_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '270', "name": 'MACD ES 5mB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on E-mini S&P 500. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_270_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '271', "name": 'MACD ES 5mC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on E-mini S&P 500. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_271_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '272', "name": 'MACD ES 15m', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on E-mini S&P 500. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_272_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '273', "name": 'MACD ES 15mB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on E-mini S&P 500. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_273_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '274', "name": 'MACD ES 15mC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on E-mini S&P 500. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_274_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '275', "name": 'MACD ES 1h', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on E-mini S&P 500. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_275_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '276', "name": 'MACD ES 1hB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on E-mini S&P 500. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_276_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '277', "name": 'MACD ES 1hC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on E-mini S&P 500. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_277_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '278', "name": 'MACD NQ 5m', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on E-mini NASDAQ 100. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_278_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '279', "name": 'MACD NQ 5mB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on E-mini NASDAQ 100. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_279_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '280', "name": 'MACD NQ 5mC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on E-mini NASDAQ 100. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_280_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '281', "name": 'MACD NQ 15m', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on E-mini NASDAQ 100. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_281_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '282', "name": 'MACD NQ 15mB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on E-mini NASDAQ 100. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_282_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '283', "name": 'MACD NQ 15mC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on E-mini NASDAQ 100. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_283_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '284', "name": 'MACD NQ 1h', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on E-mini NASDAQ 100. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_284_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '285', "name": 'MACD NQ 1hB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on E-mini NASDAQ 100. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_285_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '286', "name": 'MACD NQ 1hC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on E-mini NASDAQ 100. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_286_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '287', "name": 'MACD YM 5m', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on E-mini Dow Jones. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_287_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '288', "name": 'MACD YM 5mB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on E-mini Dow Jones. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_288_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '289', "name": 'MACD YM 5mC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on E-mini Dow Jones. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_289_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '290', "name": 'MACD YM 15m', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on E-mini Dow Jones. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_290_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '291', "name": 'MACD YM 15mB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on E-mini Dow Jones. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_291_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '292', "name": 'MACD YM 15mC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on E-mini Dow Jones. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_292_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '293', "name": 'MACD YM 1h', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on E-mini Dow Jones. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_293_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '294', "name": 'MACD YM 1hB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on E-mini Dow Jones. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_294_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '295', "name": 'MACD YM 1hC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on E-mini Dow Jones. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_295_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '296', "name": 'MACD RTY 5m', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on E-mini Russell 2000. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_296_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '297', "name": 'MACD RTY 5mB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on E-mini Russell 2000. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_297_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '298', "name": 'MACD RTY 5mC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on E-mini Russell 2000. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_298_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '299', "name": 'MACD RTY 15m', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on E-mini Russell 2000. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_299_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '300', "name": 'MACD RTY 15mB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on E-mini Russell 2000. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_300_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '301', "name": 'MACD RTY 15mC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on E-mini Russell 2000. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_301_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '302', "name": 'MACD RTY 1h', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on E-mini Russell 2000. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_302_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '303', "name": 'MACD RTY 1hB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on E-mini Russell 2000. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_303_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '304', "name": 'MACD RTY 1hC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on E-mini Russell 2000. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_304_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '305', "name": 'MACD GC 5m', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on Gold Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_305_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '306', "name": 'MACD GC 5mB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on Gold Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_306_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '307', "name": 'MACD GC 5mC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on Gold Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_307_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '308', "name": 'MACD GC 15m', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on Gold Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_308_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '309', "name": 'MACD GC 15mB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on Gold Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_309_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '310', "name": 'MACD GC 15mC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on Gold Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_310_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '311', "name": 'MACD GC 1h', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on Gold Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_311_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '312', "name": 'MACD GC 1hB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on Gold Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_312_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '313', "name": 'MACD GC 1hC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on Gold Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_313_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '314', "name": 'MACD SI 5m', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on Silver Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_314_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '315', "name": 'MACD SI 5mB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on Silver Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_315_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '316', "name": 'MACD SI 5mC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on Silver Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_316_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '317', "name": 'MACD SI 15m', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on Silver Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_317_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '318', "name": 'MACD SI 15mB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on Silver Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_318_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '319', "name": 'MACD SI 15mC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on Silver Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_319_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '320', "name": 'MACD SI 1h', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on Silver Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_320_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '321', "name": 'MACD SI 1hB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on Silver Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_321_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '322', "name": 'MACD SI 1hC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on Silver Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_322_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '323', "name": 'MACD CL 5m', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on Crude Oil Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_323_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '324', "name": 'MACD CL 5mB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on Crude Oil Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_324_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '325', "name": 'MACD CL 5mC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on Crude Oil Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_325_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '326', "name": 'MACD CL 15m', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on Crude Oil Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_326_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '327', "name": 'MACD CL 15mB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on Crude Oil Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_327_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '328', "name": 'MACD CL 15mC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on Crude Oil Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_328_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '329', "name": 'MACD CL 1h', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on Crude Oil Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_329_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '330', "name": 'MACD CL 1hB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on Crude Oil Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_330_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '331', "name": 'MACD CL 1hC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on Crude Oil Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_331_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '332', "name": 'MACD NG 5m', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on Natural Gas Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_332_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '333', "name": 'MACD NG 5mB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on Natural Gas Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_333_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '334', "name": 'MACD NG 5mC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on Natural Gas Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 5m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_334_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '335', "name": 'MACD NG 15m', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on Natural Gas Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_335_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '336', "name": 'MACD NG 15mB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on Natural Gas Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_336_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '337', "name": 'MACD NG 15mC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on Natural Gas Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_337_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '338', "name": 'MACD NG 1h', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on Natural Gas Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_338_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '339', "name": 'MACD NG 1hB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on Natural Gas Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_339_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '340', "name": 'MACD NG 1hC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on Natural Gas Futures. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_340_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '341', "name": 'MACD ZB 15m', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on 30-Year T-Bond. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_341_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '342', "name": 'MACD ZB 15mB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on 30-Year T-Bond. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_342_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '343', "name": 'MACD ZB 15mC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on 30-Year T-Bond. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_343_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '344', "name": 'MACD ZB 1h', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on 30-Year T-Bond. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_344_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '345', "name": 'MACD ZB 1hB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on 30-Year T-Bond. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_345_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '346', "name": 'MACD ZB 1hC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on 30-Year T-Bond. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_346_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '347', "name": 'MACD ZN 15m', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on 10-Year T-Note. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_347_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '348', "name": 'MACD ZN 15mB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on 10-Year T-Note. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_348_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '349', "name": 'MACD ZN 15mC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on 10-Year T-Note. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 15m bars for 60d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_349_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '350', "name": 'MACD ZN 1h', "category": 'Trend Following',
        "description": (
            'MACD(12,26,9) crossover with histogram momentum filter on 10-Year T-Note. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_350_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '351', "name": 'MACD ZN 1hB', "category": 'Trend Following',
        "description": (
            'MACD(8,21,5) crossover with histogram momentum filter on 10-Year T-Note. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(2.0:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 8, 'macd_slow': 21, 'macd_signal': 5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_351_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '352', "name": 'MACD ZN 1hC', "category": 'Trend Following',
        "description": (
            'MACD(5,13,3) crossover with histogram momentum filter on 10-Year T-Note. Goes long when the MACD line crosses above signal and the histogram is growing. Goes short on the inverse. Uses ATR(1.5:1 R:R) for dynamic profit targets and stops. Runs on 1h bars for 730d of historical data. The histogram confirmation reduces false crossover signals significantly.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'macd',
        "params": {'macd_fast': 5, 'macd_slow': 13, 'macd_signal': 3, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_352_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '353', "name": 'EMA CROSS ES 5m', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on E-mini S&P 500. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_353_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '354', "name": 'EMA CROSS ES 5mB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on E-mini S&P 500. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_354_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '355', "name": 'EMA CROSS ES 5mC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on E-mini S&P 500. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_355_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '356', "name": 'EMA CROSS ES 15m', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on E-mini S&P 500. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_356_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '357', "name": 'EMA CROSS ES 15mB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on E-mini S&P 500. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_357_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '358', "name": 'EMA CROSS ES 15mC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on E-mini S&P 500. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_358_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '359', "name": 'EMA CROSS ES 1h', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on E-mini S&P 500. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_359_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '360', "name": 'EMA CROSS ES 1hB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on E-mini S&P 500. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_360_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '361', "name": 'EMA CROSS ES 1hC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on E-mini S&P 500. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_361_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '362', "name": 'EMA CROSS NQ 5m', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on E-mini NASDAQ 100. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_362_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '363', "name": 'EMA CROSS NQ 5mB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on E-mini NASDAQ 100. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_363_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '364', "name": 'EMA CROSS NQ 5mC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on E-mini NASDAQ 100. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_364_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '365', "name": 'EMA CROSS NQ 15m', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on E-mini NASDAQ 100. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_365_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '366', "name": 'EMA CROSS NQ 15mB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on E-mini NASDAQ 100. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_366_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '367', "name": 'EMA CROSS NQ 15mC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on E-mini NASDAQ 100. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_367_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '368', "name": 'EMA CROSS NQ 1h', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on E-mini NASDAQ 100. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_368_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '369', "name": 'EMA CROSS NQ 1hB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on E-mini NASDAQ 100. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_369_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '370', "name": 'EMA CROSS NQ 1hC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on E-mini NASDAQ 100. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_370_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '371', "name": 'EMA CROSS YM 5m', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on E-mini Dow Jones. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_371_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '372', "name": 'EMA CROSS YM 5mB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on E-mini Dow Jones. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_372_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '373', "name": 'EMA CROSS YM 5mC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on E-mini Dow Jones. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_373_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '374', "name": 'EMA CROSS YM 15m', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on E-mini Dow Jones. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_374_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '375', "name": 'EMA CROSS YM 15mB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on E-mini Dow Jones. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_375_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '376', "name": 'EMA CROSS YM 15mC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on E-mini Dow Jones. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_376_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '377', "name": 'EMA CROSS YM 1h', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on E-mini Dow Jones. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_377_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '378', "name": 'EMA CROSS YM 1hB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on E-mini Dow Jones. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_378_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '379', "name": 'EMA CROSS YM 1hC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on E-mini Dow Jones. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_379_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '380', "name": 'EMA CROSS RTY 5m', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on E-mini Russell 2000. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_380_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '381', "name": 'EMA CROSS RTY 5mB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on E-mini Russell 2000. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_381_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '382', "name": 'EMA CROSS RTY 5mC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on E-mini Russell 2000. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_382_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '383', "name": 'EMA CROSS RTY 15m', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on E-mini Russell 2000. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_383_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '384', "name": 'EMA CROSS RTY 15mB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on E-mini Russell 2000. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_384_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '385', "name": 'EMA CROSS RTY 15mC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on E-mini Russell 2000. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_385_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '386', "name": 'EMA CROSS RTY 1h', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on E-mini Russell 2000. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_386_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '387', "name": 'EMA CROSS RTY 1hB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on E-mini Russell 2000. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_387_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '388', "name": 'EMA CROSS RTY 1hC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on E-mini Russell 2000. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_388_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '389', "name": 'EMA CROSS GC 5m', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on Gold Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_389_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '390', "name": 'EMA CROSS GC 5mB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on Gold Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_390_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '391', "name": 'EMA CROSS GC 5mC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on Gold Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_391_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '392', "name": 'EMA CROSS GC 15m', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on Gold Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_392_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '393', "name": 'EMA CROSS GC 15mB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on Gold Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_393_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '394', "name": 'EMA CROSS GC 15mC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on Gold Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_394_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '395', "name": 'EMA CROSS GC 1h', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on Gold Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_395_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '396', "name": 'EMA CROSS GC 1hB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on Gold Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_396_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '397', "name": 'EMA CROSS GC 1hC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on Gold Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_397_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '398', "name": 'EMA CROSS SI 5m', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on Silver Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_398_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '399', "name": 'EMA CROSS SI 5mB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on Silver Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_399_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '400', "name": 'EMA CROSS SI 5mC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on Silver Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_400_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '401', "name": 'EMA CROSS SI 15m', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on Silver Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_401_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '402', "name": 'EMA CROSS SI 15mB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on Silver Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_402_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '403', "name": 'EMA CROSS SI 15mC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on Silver Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_403_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '404', "name": 'EMA CROSS SI 1h', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on Silver Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_404_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '405', "name": 'EMA CROSS SI 1hB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on Silver Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_405_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '406', "name": 'EMA CROSS SI 1hC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on Silver Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_406_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '407', "name": 'EMA CROSS CL 5m', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on Crude Oil Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_407_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '408', "name": 'EMA CROSS CL 5mB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on Crude Oil Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_408_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '409', "name": 'EMA CROSS CL 5mC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on Crude Oil Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_409_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '410', "name": 'EMA CROSS CL 15m', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on Crude Oil Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_410_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '411', "name": 'EMA CROSS CL 15mB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on Crude Oil Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_411_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '412', "name": 'EMA CROSS CL 15mC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on Crude Oil Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_412_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '413', "name": 'EMA CROSS CL 1h', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on Crude Oil Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_413_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '414', "name": 'EMA CROSS CL 1hB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on Crude Oil Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_414_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '415', "name": 'EMA CROSS CL 1hC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on Crude Oil Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_415_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '416', "name": 'EMA CROSS NG 5m', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on Natural Gas Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_416_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '417', "name": 'EMA CROSS NG 5mB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on Natural Gas Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_417_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '418', "name": 'EMA CROSS NG 5mC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on Natural Gas Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 5m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_418_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '419', "name": 'EMA CROSS NG 15m', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on Natural Gas Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_419_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '420', "name": 'EMA CROSS NG 15mB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on Natural Gas Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_420_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '421', "name": 'EMA CROSS NG 15mC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on Natural Gas Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_421_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '422', "name": 'EMA CROSS NG 1h', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on Natural Gas Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_422_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '423', "name": 'EMA CROSS NG 1hB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on Natural Gas Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_423_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '424', "name": 'EMA CROSS NG 1hC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on Natural Gas Futures. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_424_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '425', "name": 'EMA CROSS ZB 15m', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on 30-Year T-Bond. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_425_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '426', "name": 'EMA CROSS ZB 15mB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on 30-Year T-Bond. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_426_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '427', "name": 'EMA CROSS ZB 15mC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on 30-Year T-Bond. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_427_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '428', "name": 'EMA CROSS ZB 1h', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on 30-Year T-Bond. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_428_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '429', "name": 'EMA CROSS ZB 1hB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on 30-Year T-Bond. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_429_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '430', "name": 'EMA CROSS ZB 1hC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on 30-Year T-Bond. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ZB=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_430_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '431', "name": 'EMA CROSS ZN 15m', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on 10-Year T-Note. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_431_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '432', "name": 'EMA CROSS ZN 15mB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on 10-Year T-Note. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_432_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '433', "name": 'EMA CROSS ZN 15mC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on 10-Year T-Note. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 15m bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_433_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '434', "name": 'EMA CROSS ZN 1h', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (9/21) with RSI(14) and volume confirmation on 10-Year T-Note. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 9, 'ema_slow': 21, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_434_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '435', "name": 'EMA CROSS ZN 1hB', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (5/13) with RSI(14) and volume confirmation on 10-Year T-Note. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 5, 'ema_slow': 13, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_435_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '436', "name": 'EMA CROSS ZN 1hC', "category": 'Trend Following',
        "description": (
            'Dual EMA crossover (13/34) with RSI(14) and volume confirmation on 10-Year T-Note. Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. Short on the reverse. ATR-sized stops and 2.0:1 targets keep each trade well-defined. Runs on 1h bars — fast enough to catch trends, slow enough to filter noise. Volume filter eliminates false breakouts in thin trading periods.'
        ),
        "market": 'ZN=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'ema_cross',
        "params": {'ema_fast': 13, 'ema_slow': 34, 'rsi_period': 14, 'vol_sma': 20, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_436_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '437', "name": 'SUPERTREND ES 5m', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on E-mini S&P 500 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_437_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '438', "name": 'SUPERTREND ES 5mB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on E-mini S&P 500 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_438_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '439', "name": 'SUPERTREND ES 5mC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on E-mini S&P 500 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_439_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '440', "name": 'SUPERTREND ES 15m', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on E-mini S&P 500 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_440_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '441', "name": 'SUPERTREND ES 15mB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on E-mini S&P 500 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_441_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '442', "name": 'SUPERTREND ES 15mC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on E-mini S&P 500 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_442_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '443', "name": 'SUPERTREND ES 1h', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on E-mini S&P 500 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_443_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '444', "name": 'SUPERTREND ES 1hB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on E-mini S&P 500 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_444_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '445', "name": 'SUPERTREND ES 1hC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on E-mini S&P 500 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_445_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '446', "name": 'SUPERTREND NQ 5m', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on E-mini NASDAQ 100 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_446_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '447', "name": 'SUPERTREND NQ 5mB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on E-mini NASDAQ 100 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_447_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '448', "name": 'SUPERTREND NQ 5mC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on E-mini NASDAQ 100 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_448_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '449', "name": 'SUPERTREND NQ 15m', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on E-mini NASDAQ 100 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_449_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '450', "name": 'SUPERTREND NQ 15mB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on E-mini NASDAQ 100 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_450_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '451', "name": 'SUPERTREND NQ 15mC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on E-mini NASDAQ 100 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_451_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '452', "name": 'SUPERTREND NQ 1h', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on E-mini NASDAQ 100 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_452_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '453', "name": 'SUPERTREND NQ 1hB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on E-mini NASDAQ 100 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_453_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '454', "name": 'SUPERTREND NQ 1hC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on E-mini NASDAQ 100 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_454_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '455', "name": 'SUPERTREND YM 5m', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on E-mini Dow Jones 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_455_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '456', "name": 'SUPERTREND YM 5mB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on E-mini Dow Jones 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_456_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '457', "name": 'SUPERTREND YM 5mC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on E-mini Dow Jones 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_457_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '458', "name": 'SUPERTREND YM 15m', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on E-mini Dow Jones 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_458_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '459', "name": 'SUPERTREND YM 15mB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on E-mini Dow Jones 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_459_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '460', "name": 'SUPERTREND YM 15mC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on E-mini Dow Jones 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_460_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '461', "name": 'SUPERTREND YM 1h', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on E-mini Dow Jones 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_461_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '462', "name": 'SUPERTREND YM 1hB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on E-mini Dow Jones 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_462_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '463', "name": 'SUPERTREND YM 1hC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on E-mini Dow Jones 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'YM=F', "tick_value": 5.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_463_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '464', "name": 'SUPERTREND RTY 5m', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on E-mini Russell 2000 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_464_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '465', "name": 'SUPERTREND RTY 5mB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on E-mini Russell 2000 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_465_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '466', "name": 'SUPERTREND RTY 5mC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on E-mini Russell 2000 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_466_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '467', "name": 'SUPERTREND RTY 15m', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on E-mini Russell 2000 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_467_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '468', "name": 'SUPERTREND RTY 15mB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on E-mini Russell 2000 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_468_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '469', "name": 'SUPERTREND RTY 15mC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on E-mini Russell 2000 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_469_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '470', "name": 'SUPERTREND RTY 1h', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on E-mini Russell 2000 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_470_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '471', "name": 'SUPERTREND RTY 1hB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on E-mini Russell 2000 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_471_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '472', "name": 'SUPERTREND RTY 1hC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on E-mini Russell 2000 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'RTY=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_472_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '473', "name": 'SUPERTREND GC 5m', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on Gold Futures 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_473_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '474', "name": 'SUPERTREND GC 5mB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on Gold Futures 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_474_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '475', "name": 'SUPERTREND GC 5mC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on Gold Futures 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_475_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '476', "name": 'SUPERTREND GC 15m', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on Gold Futures 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_476_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '477', "name": 'SUPERTREND GC 15mB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on Gold Futures 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_477_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '478', "name": 'SUPERTREND GC 15mC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on Gold Futures 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_478_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '479', "name": 'SUPERTREND GC 1h', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on Gold Futures 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_479_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '480', "name": 'SUPERTREND GC 1hB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on Gold Futures 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_480_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '481', "name": 'SUPERTREND GC 1hC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on Gold Futures 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_481_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '482', "name": 'SUPERTREND SI 5m', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on Silver Futures 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_482_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '483', "name": 'SUPERTREND SI 5mB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on Silver Futures 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_483_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '484', "name": 'SUPERTREND SI 5mC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on Silver Futures 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_484_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '485', "name": 'SUPERTREND SI 15m', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on Silver Futures 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_485_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '486', "name": 'SUPERTREND SI 15mB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on Silver Futures 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_486_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '487', "name": 'SUPERTREND SI 15mC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on Silver Futures 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_487_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '488', "name": 'SUPERTREND SI 1h', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on Silver Futures 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_488_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '489', "name": 'SUPERTREND SI 1hB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on Silver Futures 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_489_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '490', "name": 'SUPERTREND SI 1hC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on Silver Futures 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'SI=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_490_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '491', "name": 'SUPERTREND CL 5m', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on Crude Oil Futures 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_491_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '492', "name": 'SUPERTREND CL 5mB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on Crude Oil Futures 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_492_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '493', "name": 'SUPERTREND CL 5mC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on Crude Oil Futures 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_493_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '494', "name": 'SUPERTREND CL 15m', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on Crude Oil Futures 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_494_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '495', "name": 'SUPERTREND CL 15mB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on Crude Oil Futures 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_495_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '496', "name": 'SUPERTREND CL 15mC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on Crude Oil Futures 15m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '15m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_496_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '497', "name": 'SUPERTREND CL 1h', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on Crude Oil Futures 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_497_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '498', "name": 'SUPERTREND CL 1hB', "category": 'Trend Following',
        "description": (
            'Supertrend(7,2.5) trend filter on Crude Oil Futures 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 7, 'st_mult': 2.5, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_498_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '499', "name": 'SUPERTREND CL 1hC', "category": 'Trend Following',
        "description": (
            'Supertrend(14,3.5) trend filter on Crude Oil Futures 1h bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 14, 'st_mult': 3.5, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_499_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '500', "name": 'SUPERTREND NG 5m', "category": 'Trend Following',
        "description": (
            'Supertrend(10,3.0) trend filter on Natural Gas Futures 5m bars. Enters on direction flip: long when price closes above the upper Supertrend band, short when it closes below the lower band. Stop is set at the Supertrend value. The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. Clean and mechanical — no ambiguity about trade direction.'
        ),
        "market": 'NG=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'supertrend',
        "params": {'st_period': 10, 'st_mult': 3.0, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_500_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },

    {
        "id": '501', "name": 'CVD DELTA TREND ES 5m', "category": 'Order Flow',
        "description": (
            'Cumulative Volume Delta trend-following on ES 5m. Measures buying vs selling pressure via CVD EMA crossover. Long when fast CVD EMA crosses above slow, confirming bullish delta dominance. Short on bearish cross. Stops set at 1 ATR, targets at 2 ATR.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'orderflow_delta',
        "params": {'cvd_fast': 5, 'cvd_slow': 20, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_501_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '502', "name": 'CVD DELTA TREND ES 1h', "category": 'Order Flow',
        "description": (
            'Cumulative Volume Delta trend-following on ES 1h. Measures buying vs selling pressure via CVD EMA crossover. Long when fast CVD EMA crosses above slow, confirming bullish delta dominance. Short on bearish cross. Stops set at 1 ATR, targets at 2 ATR.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'orderflow_delta',
        "params": {'cvd_fast': 8, 'cvd_slow': 34, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_502_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '503', "name": 'CVD DELTA TREND NQ 5m', "category": 'Order Flow',
        "description": (
            'Cumulative Volume Delta trend-following on NQ 5m. Measures buying vs selling pressure via CVD EMA crossover. Long when fast CVD EMA crosses above slow, confirming bullish delta dominance. Short on bearish cross. Stops set at 1 ATR, targets at 2 ATR.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'orderflow_delta',
        "params": {'cvd_fast': 5, 'cvd_slow': 20, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_503_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '504', "name": 'CVD DELTA TREND NQ 1h', "category": 'Order Flow',
        "description": (
            'Cumulative Volume Delta trend-following on NQ 1h. Measures buying vs selling pressure via CVD EMA crossover. Long when fast CVD EMA crosses above slow, confirming bullish delta dominance. Short on bearish cross. Stops set at 1 ATR, targets at 2 ATR.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'orderflow_delta',
        "params": {'cvd_fast': 8, 'cvd_slow': 34, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_504_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '505', "name": 'CVD DELTA TREND GC 5m', "category": 'Order Flow',
        "description": (
            'Cumulative Volume Delta trend-following on GC 5m. Measures buying vs selling pressure via CVD EMA crossover. Long when fast CVD EMA crosses above slow, confirming bullish delta dominance. Short on bearish cross. Stops set at 1 ATR, targets at 2 ATR.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'orderflow_delta',
        "params": {'cvd_fast': 5, 'cvd_slow': 20, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_505_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '506', "name": 'CVD DELTA TREND GC 1h', "category": 'Order Flow',
        "description": (
            'Cumulative Volume Delta trend-following on GC 1h. Measures buying vs selling pressure via CVD EMA crossover. Long when fast CVD EMA crosses above slow, confirming bullish delta dominance. Short on bearish cross. Stops set at 1 ATR, targets at 2 ATR.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'orderflow_delta',
        "params": {'cvd_fast': 8, 'cvd_slow': 34, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_506_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '507', "name": 'CVD DELTA TREND CL 5m', "category": 'Order Flow',
        "description": (
            'Cumulative Volume Delta trend-following on CL 5m. Measures buying vs selling pressure via CVD EMA crossover. Long when fast CVD EMA crosses above slow, confirming bullish delta dominance. Short on bearish cross. Stops set at 1 ATR, targets at 2 ATR.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'orderflow_delta',
        "params": {'cvd_fast': 5, 'cvd_slow': 20, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_507_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '508', "name": 'CVD DELTA TREND CL 1h', "category": 'Order Flow',
        "description": (
            'Cumulative Volume Delta trend-following on CL 1h. Measures buying vs selling pressure via CVD EMA crossover. Long when fast CVD EMA crosses above slow, confirming bullish delta dominance. Short on bearish cross. Stops set at 1 ATR, targets at 2 ATR.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'orderflow_delta',
        "params": {'cvd_fast': 8, 'cvd_slow': 34, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_508_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '509', "name": 'ABSORPTION REVERSAL ES 5m', "category": 'Order Flow',
        "description": (
            'Detects institutional absorption on ES 5m. High effort (volume spike) with minimal result (tiny body) signals hidden buyers/sellers absorbing flow. Fades the direction of absorption for a mean-reversion entry. Uses Wyckoff effort-vs-result analysis.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'absorption_reversal',
        "params": {'atr_period': 14, 'vol_mult': 2.0, 'body_pct': 0.3, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_509_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '510', "name": 'ABSORPTION REVERSAL ES 1h', "category": 'Order Flow',
        "description": (
            'Detects institutional absorption on ES 1h. High effort (volume spike) with minimal result (tiny body) signals hidden buyers/sellers absorbing flow. Fades the direction of absorption for a mean-reversion entry. Uses Wyckoff effort-vs-result analysis.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'absorption_reversal',
        "params": {'atr_period': 14, 'vol_mult': 1.8, 'body_pct': 0.35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_510_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '511', "name": 'ABSORPTION REVERSAL NQ 5m', "category": 'Order Flow',
        "description": (
            'Detects institutional absorption on NQ 5m. High effort (volume spike) with minimal result (tiny body) signals hidden buyers/sellers absorbing flow. Fades the direction of absorption for a mean-reversion entry. Uses Wyckoff effort-vs-result analysis.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'absorption_reversal',
        "params": {'atr_period': 14, 'vol_mult': 2.0, 'body_pct': 0.3, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_511_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '512', "name": 'ABSORPTION REVERSAL NQ 1h', "category": 'Order Flow',
        "description": (
            'Detects institutional absorption on NQ 1h. High effort (volume spike) with minimal result (tiny body) signals hidden buyers/sellers absorbing flow. Fades the direction of absorption for a mean-reversion entry. Uses Wyckoff effort-vs-result analysis.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'absorption_reversal',
        "params": {'atr_period': 14, 'vol_mult': 1.8, 'body_pct': 0.35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_512_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '513', "name": 'ABSORPTION REVERSAL GC 5m', "category": 'Order Flow',
        "description": (
            'Detects institutional absorption on GC 5m. High effort (volume spike) with minimal result (tiny body) signals hidden buyers/sellers absorbing flow. Fades the direction of absorption for a mean-reversion entry. Uses Wyckoff effort-vs-result analysis.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'absorption_reversal',
        "params": {'atr_period': 14, 'vol_mult': 2.0, 'body_pct': 0.3, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_513_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '514', "name": 'ABSORPTION REVERSAL GC 1h', "category": 'Order Flow',
        "description": (
            'Detects institutional absorption on GC 1h. High effort (volume spike) with minimal result (tiny body) signals hidden buyers/sellers absorbing flow. Fades the direction of absorption for a mean-reversion entry. Uses Wyckoff effort-vs-result analysis.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'absorption_reversal',
        "params": {'atr_period': 14, 'vol_mult': 1.8, 'body_pct': 0.35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_514_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '515', "name": 'ABSORPTION REVERSAL CL 5m', "category": 'Order Flow',
        "description": (
            'Detects institutional absorption on CL 5m. High effort (volume spike) with minimal result (tiny body) signals hidden buyers/sellers absorbing flow. Fades the direction of absorption for a mean-reversion entry. Uses Wyckoff effort-vs-result analysis.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'absorption_reversal',
        "params": {'atr_period': 14, 'vol_mult': 2.0, 'body_pct': 0.3, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_515_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '516', "name": 'ABSORPTION REVERSAL CL 1h', "category": 'Order Flow',
        "description": (
            'Detects institutional absorption on CL 1h. High effort (volume spike) with minimal result (tiny body) signals hidden buyers/sellers absorbing flow. Fades the direction of absorption for a mean-reversion entry. Uses Wyckoff effort-vs-result analysis.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'absorption_reversal',
        "params": {'atr_period': 14, 'vol_mult': 1.8, 'body_pct': 0.35, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_516_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '517', "name": 'TRAPPED TRADERS ES 5m', "category": 'Order Flow',
        "description": (
            'Trapped trader squeeze on ES 5m. Identifies bars that break to new highs/lows then close back inside the range, trapping breakout traders. Fades the breakout once price reverses back through the trap level. High-probability mean-reversion setup.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'trapped_breakout',
        "params": {'lookback': 20, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_517_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '518', "name": 'TRAPPED TRADERS ES 1h', "category": 'Order Flow',
        "description": (
            'Trapped trader squeeze on ES 1h. Identifies bars that break to new highs/lows then close back inside the range, trapping breakout traders. Fades the breakout once price reverses back through the trap level. High-probability mean-reversion setup.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'trapped_breakout',
        "params": {'lookback': 30, 'atr_period': 14, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_518_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '519', "name": 'TRAPPED TRADERS NQ 5m', "category": 'Order Flow',
        "description": (
            'Trapped trader squeeze on NQ 5m. Identifies bars that break to new highs/lows then close back inside the range, trapping breakout traders. Fades the breakout once price reverses back through the trap level. High-probability mean-reversion setup.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'trapped_breakout',
        "params": {'lookback': 20, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_519_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '520', "name": 'TRAPPED TRADERS NQ 1h', "category": 'Order Flow',
        "description": (
            'Trapped trader squeeze on NQ 1h. Identifies bars that break to new highs/lows then close back inside the range, trapping breakout traders. Fades the breakout once price reverses back through the trap level. High-probability mean-reversion setup.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'trapped_breakout',
        "params": {'lookback': 30, 'atr_period': 14, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_520_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '521', "name": 'TRAPPED TRADERS GC 5m', "category": 'Order Flow',
        "description": (
            'Trapped trader squeeze on GC 5m. Identifies bars that break to new highs/lows then close back inside the range, trapping breakout traders. Fades the breakout once price reverses back through the trap level. High-probability mean-reversion setup.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'trapped_breakout',
        "params": {'lookback': 20, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_521_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '522', "name": 'TRAPPED TRADERS GC 1h', "category": 'Order Flow',
        "description": (
            'Trapped trader squeeze on GC 1h. Identifies bars that break to new highs/lows then close back inside the range, trapping breakout traders. Fades the breakout once price reverses back through the trap level. High-probability mean-reversion setup.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'trapped_breakout',
        "params": {'lookback': 30, 'atr_period': 14, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_522_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '523', "name": 'TRAPPED TRADERS CL 5m', "category": 'Order Flow',
        "description": (
            'Trapped trader squeeze on CL 5m. Identifies bars that break to new highs/lows then close back inside the range, trapping breakout traders. Fades the breakout once price reverses back through the trap level. High-probability mean-reversion setup.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'trapped_breakout',
        "params": {'lookback': 20, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_523_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '524', "name": 'TRAPPED TRADERS CL 1h', "category": 'Order Flow',
        "description": (
            'Trapped trader squeeze on CL 1h. Identifies bars that break to new highs/lows then close back inside the range, trapping breakout traders. Fades the breakout once price reverses back through the trap level. High-probability mean-reversion setup.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'trapped_breakout',
        "params": {'lookback': 30, 'atr_period': 14, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_524_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '525', "name": 'TAPE MOMENTUM ES 5m', "category": 'Order Flow',
        "description": (
            'Tape speed momentum on ES 5m. Measures urgency of order flow via volume EMA ratio (fast/slow). When tape accelerates significantly (ratio > threshold) in direction of trend (EMA slope), enters with momentum. Combines volume urgency with price direction.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'tape_momentum',
        "params": {'fast_vol': 5, 'slow_vol': 20, 'speed_thresh': 1.5, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_525_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '526', "name": 'TAPE MOMENTUM ES 1h', "category": 'Order Flow',
        "description": (
            'Tape speed momentum on ES 1h. Measures urgency of order flow via volume EMA ratio (fast/slow). When tape accelerates significantly (ratio > threshold) in direction of trend (EMA slope), enters with momentum. Combines volume urgency with price direction.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'tape_momentum',
        "params": {'fast_vol': 8, 'slow_vol': 34, 'speed_thresh': 1.4, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_526_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '527', "name": 'TAPE MOMENTUM NQ 5m', "category": 'Order Flow',
        "description": (
            'Tape speed momentum on NQ 5m. Measures urgency of order flow via volume EMA ratio (fast/slow). When tape accelerates significantly (ratio > threshold) in direction of trend (EMA slope), enters with momentum. Combines volume urgency with price direction.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'tape_momentum',
        "params": {'fast_vol': 5, 'slow_vol': 20, 'speed_thresh': 1.5, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_527_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '528', "name": 'TAPE MOMENTUM NQ 1h', "category": 'Order Flow',
        "description": (
            'Tape speed momentum on NQ 1h. Measures urgency of order flow via volume EMA ratio (fast/slow). When tape accelerates significantly (ratio > threshold) in direction of trend (EMA slope), enters with momentum. Combines volume urgency with price direction.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'tape_momentum',
        "params": {'fast_vol': 8, 'slow_vol': 34, 'speed_thresh': 1.4, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_528_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '529', "name": 'TAPE MOMENTUM GC 5m', "category": 'Order Flow',
        "description": (
            'Tape speed momentum on GC 5m. Measures urgency of order flow via volume EMA ratio (fast/slow). When tape accelerates significantly (ratio > threshold) in direction of trend (EMA slope), enters with momentum. Combines volume urgency with price direction.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'tape_momentum',
        "params": {'fast_vol': 5, 'slow_vol': 20, 'speed_thresh': 1.5, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_529_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '530', "name": 'TAPE MOMENTUM GC 1h', "category": 'Order Flow',
        "description": (
            'Tape speed momentum on GC 1h. Measures urgency of order flow via volume EMA ratio (fast/slow). When tape accelerates significantly (ratio > threshold) in direction of trend (EMA slope), enters with momentum. Combines volume urgency with price direction.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'tape_momentum',
        "params": {'fast_vol': 8, 'slow_vol': 34, 'speed_thresh': 1.4, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_530_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '531', "name": 'TAPE MOMENTUM CL 5m', "category": 'Order Flow',
        "description": (
            'Tape speed momentum on CL 5m. Measures urgency of order flow via volume EMA ratio (fast/slow). When tape accelerates significantly (ratio > threshold) in direction of trend (EMA slope), enters with momentum. Combines volume urgency with price direction.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'tape_momentum',
        "params": {'fast_vol': 5, 'slow_vol': 20, 'speed_thresh': 1.5, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_531_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '532', "name": 'TAPE MOMENTUM CL 1h', "category": 'Order Flow',
        "description": (
            'Tape speed momentum on CL 1h. Measures urgency of order flow via volume EMA ratio (fast/slow). When tape accelerates significantly (ratio > threshold) in direction of trend (EMA slope), enters with momentum. Combines volume urgency with price direction.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'tape_momentum',
        "params": {'fast_vol': 8, 'slow_vol': 34, 'speed_thresh': 1.4, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_532_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '533', "name": 'EFFORT VS RESULT ES 5m', "category": 'Order Flow',
        "description": (
            'Effort vs Result reversal on ES 5m. When a bar shows extreme volume (effort) but fails to move price significantly (poor result), it reveals institutional absorption. This exhaustion signal triggers a counter-trend entry. Classic Wyckoff principle.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'evr_reversal',
        "params": {'vol_percentile': 90, 'move_percentile': 30, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_533_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '534', "name": 'EFFORT VS RESULT ES 1h', "category": 'Order Flow',
        "description": (
            'Effort vs Result reversal on ES 1h. When a bar shows extreme volume (effort) but fails to move price significantly (poor result), it reveals institutional absorption. This exhaustion signal triggers a counter-trend entry. Classic Wyckoff principle.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'evr_reversal',
        "params": {'vol_percentile': 85, 'move_percentile': 35, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_534_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '535', "name": 'EFFORT VS RESULT NQ 5m', "category": 'Order Flow',
        "description": (
            'Effort vs Result reversal on NQ 5m. When a bar shows extreme volume (effort) but fails to move price significantly (poor result), it reveals institutional absorption. This exhaustion signal triggers a counter-trend entry. Classic Wyckoff principle.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'evr_reversal',
        "params": {'vol_percentile': 90, 'move_percentile': 30, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_535_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '536', "name": 'EFFORT VS RESULT NQ 1h', "category": 'Order Flow',
        "description": (
            'Effort vs Result reversal on NQ 1h. When a bar shows extreme volume (effort) but fails to move price significantly (poor result), it reveals institutional absorption. This exhaustion signal triggers a counter-trend entry. Classic Wyckoff principle.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'evr_reversal',
        "params": {'vol_percentile': 85, 'move_percentile': 35, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_536_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '537', "name": 'EFFORT VS RESULT GC 5m', "category": 'Order Flow',
        "description": (
            'Effort vs Result reversal on GC 5m. When a bar shows extreme volume (effort) but fails to move price significantly (poor result), it reveals institutional absorption. This exhaustion signal triggers a counter-trend entry. Classic Wyckoff principle.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'evr_reversal',
        "params": {'vol_percentile': 90, 'move_percentile': 30, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_537_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '538', "name": 'EFFORT VS RESULT GC 1h', "category": 'Order Flow',
        "description": (
            'Effort vs Result reversal on GC 1h. When a bar shows extreme volume (effort) but fails to move price significantly (poor result), it reveals institutional absorption. This exhaustion signal triggers a counter-trend entry. Classic Wyckoff principle.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'evr_reversal',
        "params": {'vol_percentile': 85, 'move_percentile': 35, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_538_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '539', "name": 'EFFORT VS RESULT CL 5m', "category": 'Order Flow',
        "description": (
            'Effort vs Result reversal on CL 5m. When a bar shows extreme volume (effort) but fails to move price significantly (poor result), it reveals institutional absorption. This exhaustion signal triggers a counter-trend entry. Classic Wyckoff principle.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'evr_reversal',
        "params": {'vol_percentile': 90, 'move_percentile': 30, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_539_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '540', "name": 'EFFORT VS RESULT CL 1h', "category": 'Order Flow',
        "description": (
            'Effort vs Result reversal on CL 1h. When a bar shows extreme volume (effort) but fails to move price significantly (poor result), it reveals institutional absorption. This exhaustion signal triggers a counter-trend entry. Classic Wyckoff principle.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'evr_reversal',
        "params": {'vol_percentile': 85, 'move_percentile': 35, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_540_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '541', "name": 'ICEBERG DETECTOR ES 5m', "category": 'Order Flow',
        "description": (
            'Institutional iceberg order detection on ES 5m. Identifies hidden large orders that keep refilling at the same price level -- tight price range + repeated high volume = iceberg. Trades the breakout direction once the iceberg is consumed and price is free to move.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'iceberg_reversal',
        "params": {'price_threshold': 0.005, 'vol_mult': 1.5, 'consecutive': 2, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_541_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '542', "name": 'ICEBERG DETECTOR ES 1h', "category": 'Order Flow',
        "description": (
            'Institutional iceberg order detection on ES 1h. Identifies hidden large orders that keep refilling at the same price level -- tight price range + repeated high volume = iceberg. Trades the breakout direction once the iceberg is consumed and price is free to move.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'iceberg_reversal',
        "params": {'price_threshold': 0.005, 'vol_mult': 1.5, 'consecutive': 2, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_542_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '543', "name": 'ICEBERG DETECTOR NQ 5m', "category": 'Order Flow',
        "description": (
            'Institutional iceberg order detection on NQ 5m. Identifies hidden large orders that keep refilling at the same price level -- tight price range + repeated high volume = iceberg. Trades the breakout direction once the iceberg is consumed and price is free to move.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'iceberg_reversal',
        "params": {'price_threshold': 0.005, 'vol_mult': 1.5, 'consecutive': 2, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_543_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '544', "name": 'ICEBERG DETECTOR NQ 1h', "category": 'Order Flow',
        "description": (
            'Institutional iceberg order detection on NQ 1h. Identifies hidden large orders that keep refilling at the same price level -- tight price range + repeated high volume = iceberg. Trades the breakout direction once the iceberg is consumed and price is free to move.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'iceberg_reversal',
        "params": {'price_threshold': 0.005, 'vol_mult': 1.5, 'consecutive': 2, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_544_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '545', "name": 'ICEBERG DETECTOR GC 5m', "category": 'Order Flow',
        "description": (
            'Institutional iceberg order detection on GC 5m. Identifies hidden large orders that keep refilling at the same price level -- tight price range + repeated high volume = iceberg. Trades the breakout direction once the iceberg is consumed and price is free to move.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'iceberg_reversal',
        "params": {'price_threshold': 0.005, 'vol_mult': 1.5, 'consecutive': 2, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_545_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '546', "name": 'ICEBERG DETECTOR GC 1h', "category": 'Order Flow',
        "description": (
            'Institutional iceberg order detection on GC 1h. Identifies hidden large orders that keep refilling at the same price level -- tight price range + repeated high volume = iceberg. Trades the breakout direction once the iceberg is consumed and price is free to move.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'iceberg_reversal',
        "params": {'price_threshold': 0.005, 'vol_mult': 1.5, 'consecutive': 2, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_546_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '547', "name": 'ICEBERG DETECTOR CL 5m', "category": 'Order Flow',
        "description": (
            'Institutional iceberg order detection on CL 5m. Identifies hidden large orders that keep refilling at the same price level -- tight price range + repeated high volume = iceberg. Trades the breakout direction once the iceberg is consumed and price is free to move.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'iceberg_reversal',
        "params": {'price_threshold': 0.005, 'vol_mult': 1.5, 'consecutive': 2, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_547_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '548', "name": 'ICEBERG DETECTOR CL 1h', "category": 'Order Flow',
        "description": (
            'Institutional iceberg order detection on CL 1h. Identifies hidden large orders that keep refilling at the same price level -- tight price range + repeated high volume = iceberg. Trades the breakout direction once the iceberg is consumed and price is free to move.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'iceberg_reversal',
        "params": {'price_threshold': 0.005, 'vol_mult': 1.5, 'consecutive': 2, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_548_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '549', "name": 'DELTA EXHAUSTION ES 5m', "category": 'Order Flow',
        "description": (
            'CVD delta exhaustion reversal on ES 5m. When Cumulative Volume Delta reaches an extreme percentile (overbought/oversold buying or selling pressure) but price fails to confirm with a new high/low, the fuel is exhausted. Fades the move for a high-probability reversal entry.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'delta_exhaustion',
        "params": {'cvd_period': 20, 'cvd_pct': 90, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_549_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '550', "name": 'DELTA EXHAUSTION ES 1h', "category": 'Order Flow',
        "description": (
            'CVD delta exhaustion reversal on ES 1h. When Cumulative Volume Delta reaches an extreme percentile (overbought/oversold buying or selling pressure) but price fails to confirm with a new high/low, the fuel is exhausted. Fades the move for a high-probability reversal entry.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'delta_exhaustion',
        "params": {'cvd_period': 30, 'cvd_pct': 85, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_550_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '551', "name": 'DELTA EXHAUSTION NQ 5m', "category": 'Order Flow',
        "description": (
            'CVD delta exhaustion reversal on NQ 5m. When Cumulative Volume Delta reaches an extreme percentile (overbought/oversold buying or selling pressure) but price fails to confirm with a new high/low, the fuel is exhausted. Fades the move for a high-probability reversal entry.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'delta_exhaustion',
        "params": {'cvd_period': 20, 'cvd_pct': 90, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_551_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '552', "name": 'DELTA EXHAUSTION NQ 1h', "category": 'Order Flow',
        "description": (
            'CVD delta exhaustion reversal on NQ 1h. When Cumulative Volume Delta reaches an extreme percentile (overbought/oversold buying or selling pressure) but price fails to confirm with a new high/low, the fuel is exhausted. Fades the move for a high-probability reversal entry.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'delta_exhaustion',
        "params": {'cvd_period': 30, 'cvd_pct': 85, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_552_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '553', "name": 'DELTA EXHAUSTION GC 5m', "category": 'Order Flow',
        "description": (
            'CVD delta exhaustion reversal on GC 5m. When Cumulative Volume Delta reaches an extreme percentile (overbought/oversold buying or selling pressure) but price fails to confirm with a new high/low, the fuel is exhausted. Fades the move for a high-probability reversal entry.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'delta_exhaustion',
        "params": {'cvd_period': 20, 'cvd_pct': 90, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_553_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '554', "name": 'DELTA EXHAUSTION GC 1h', "category": 'Order Flow',
        "description": (
            'CVD delta exhaustion reversal on GC 1h. When Cumulative Volume Delta reaches an extreme percentile (overbought/oversold buying or selling pressure) but price fails to confirm with a new high/low, the fuel is exhausted. Fades the move for a high-probability reversal entry.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'delta_exhaustion',
        "params": {'cvd_period': 30, 'cvd_pct': 85, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_554_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '555', "name": 'DELTA EXHAUSTION CL 5m', "category": 'Order Flow',
        "description": (
            'CVD delta exhaustion reversal on CL 5m. When Cumulative Volume Delta reaches an extreme percentile (overbought/oversold buying or selling pressure) but price fails to confirm with a new high/low, the fuel is exhausted. Fades the move for a high-probability reversal entry.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'delta_exhaustion',
        "params": {'cvd_period': 20, 'cvd_pct': 90, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_555_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '556', "name": 'DELTA EXHAUSTION CL 1h', "category": 'Order Flow',
        "description": (
            'CVD delta exhaustion reversal on CL 1h. When Cumulative Volume Delta reaches an extreme percentile (overbought/oversold buying or selling pressure) but price fails to confirm with a new high/low, the fuel is exhausted. Fades the move for a high-probability reversal entry.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'delta_exhaustion',
        "params": {'cvd_period': 30, 'cvd_pct': 85, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_556_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '557', "name": 'STOP HUNT FADE ES 5m', "category": 'Order Flow',
        "description": (
            'Liquidity sweep / stop hunt reversal on ES 5m. Price wicks below the N-bar swing low (triggering retail stop orders) then closes back above it -- the classic institutional stop raid. Enters long on close-back-above. Short version fades wicks above swing highs. High win rate with defined risk.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'stop_hunt',
        "params": {'lookback': 20, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_557_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '558', "name": 'STOP HUNT FADE ES 1h', "category": 'Order Flow',
        "description": (
            'Liquidity sweep / stop hunt reversal on ES 1h. Price wicks below the N-bar swing low (triggering retail stop orders) then closes back above it -- the classic institutional stop raid. Enters long on close-back-above. Short version fades wicks above swing highs. High win rate with defined risk.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'stop_hunt',
        "params": {'lookback': 30, 'atr_period': 14, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_558_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '559', "name": 'STOP HUNT FADE NQ 5m', "category": 'Order Flow',
        "description": (
            'Liquidity sweep / stop hunt reversal on NQ 5m. Price wicks below the N-bar swing low (triggering retail stop orders) then closes back above it -- the classic institutional stop raid. Enters long on close-back-above. Short version fades wicks above swing highs. High win rate with defined risk.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'stop_hunt',
        "params": {'lookback': 20, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_559_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '560', "name": 'STOP HUNT FADE NQ 1h', "category": 'Order Flow',
        "description": (
            'Liquidity sweep / stop hunt reversal on NQ 1h. Price wicks below the N-bar swing low (triggering retail stop orders) then closes back above it -- the classic institutional stop raid. Enters long on close-back-above. Short version fades wicks above swing highs. High win rate with defined risk.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'stop_hunt',
        "params": {'lookback': 30, 'atr_period': 14, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_560_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '561', "name": 'STOP HUNT FADE GC 5m', "category": 'Order Flow',
        "description": (
            'Liquidity sweep / stop hunt reversal on GC 5m. Price wicks below the N-bar swing low (triggering retail stop orders) then closes back above it -- the classic institutional stop raid. Enters long on close-back-above. Short version fades wicks above swing highs. High win rate with defined risk.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'stop_hunt',
        "params": {'lookback': 20, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_561_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '562', "name": 'STOP HUNT FADE GC 1h', "category": 'Order Flow',
        "description": (
            'Liquidity sweep / stop hunt reversal on GC 1h. Price wicks below the N-bar swing low (triggering retail stop orders) then closes back above it -- the classic institutional stop raid. Enters long on close-back-above. Short version fades wicks above swing highs. High win rate with defined risk.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'stop_hunt',
        "params": {'lookback': 30, 'atr_period': 14, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_562_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '563', "name": 'STOP HUNT FADE CL 5m', "category": 'Order Flow',
        "description": (
            'Liquidity sweep / stop hunt reversal on CL 5m. Price wicks below the N-bar swing low (triggering retail stop orders) then closes back above it -- the classic institutional stop raid. Enters long on close-back-above. Short version fades wicks above swing highs. High win rate with defined risk.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'stop_hunt',
        "params": {'lookback': 20, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_563_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '564', "name": 'STOP HUNT FADE CL 1h', "category": 'Order Flow',
        "description": (
            'Liquidity sweep / stop hunt reversal on CL 1h. Price wicks below the N-bar swing low (triggering retail stop orders) then closes back above it -- the classic institutional stop raid. Enters long on close-back-above. Short version fades wicks above swing highs. High win rate with defined risk.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'stop_hunt',
        "params": {'lookback': 30, 'atr_period': 14, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_564_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '565', "name": 'ORDER BLOCK RETEST ES 5m', "category": 'Order Flow',
        "description": (
            'Smart Money Concept (SMC) order block retest on ES 5m. Identifies the last bearish candle before a bullish impulse move (bullish order block) and the last bullish candle before a bearish impulse. When price returns to retest these institutional accumulation zones, enters in the original impulse direction.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'order_block',
        "params": {'impulse_mult': 1.5, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_565_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '566', "name": 'ORDER BLOCK RETEST ES 1h', "category": 'Order Flow',
        "description": (
            'Smart Money Concept (SMC) order block retest on ES 1h. Identifies the last bearish candle before a bullish impulse move (bullish order block) and the last bullish candle before a bearish impulse. When price returns to retest these institutional accumulation zones, enters in the original impulse direction.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'order_block',
        "params": {'impulse_mult': 1.3, 'atr_period': 14, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_566_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '567', "name": 'ORDER BLOCK RETEST NQ 5m', "category": 'Order Flow',
        "description": (
            'Smart Money Concept (SMC) order block retest on NQ 5m. Identifies the last bearish candle before a bullish impulse move (bullish order block) and the last bullish candle before a bearish impulse. When price returns to retest these institutional accumulation zones, enters in the original impulse direction.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'order_block',
        "params": {'impulse_mult': 1.5, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_567_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '568', "name": 'ORDER BLOCK RETEST NQ 1h', "category": 'Order Flow',
        "description": (
            'Smart Money Concept (SMC) order block retest on NQ 1h. Identifies the last bearish candle before a bullish impulse move (bullish order block) and the last bullish candle before a bearish impulse. When price returns to retest these institutional accumulation zones, enters in the original impulse direction.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'order_block',
        "params": {'impulse_mult': 1.3, 'atr_period': 14, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_568_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '569', "name": 'ORDER BLOCK RETEST GC 5m', "category": 'Order Flow',
        "description": (
            'Smart Money Concept (SMC) order block retest on GC 5m. Identifies the last bearish candle before a bullish impulse move (bullish order block) and the last bullish candle before a bearish impulse. When price returns to retest these institutional accumulation zones, enters in the original impulse direction.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'order_block',
        "params": {'impulse_mult': 1.5, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_569_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '570', "name": 'ORDER BLOCK RETEST GC 1h', "category": 'Order Flow',
        "description": (
            'Smart Money Concept (SMC) order block retest on GC 1h. Identifies the last bearish candle before a bullish impulse move (bullish order block) and the last bullish candle before a bearish impulse. When price returns to retest these institutional accumulation zones, enters in the original impulse direction.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'order_block',
        "params": {'impulse_mult': 1.3, 'atr_period': 14, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_570_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '571', "name": 'ORDER BLOCK RETEST CL 5m', "category": 'Order Flow',
        "description": (
            'Smart Money Concept (SMC) order block retest on CL 5m. Identifies the last bearish candle before a bullish impulse move (bullish order block) and the last bullish candle before a bearish impulse. When price returns to retest these institutional accumulation zones, enters in the original impulse direction.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'order_block',
        "params": {'impulse_mult': 1.5, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_571_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '572', "name": 'ORDER BLOCK RETEST CL 1h', "category": 'Order Flow',
        "description": (
            'Smart Money Concept (SMC) order block retest on CL 1h. Identifies the last bearish candle before a bullish impulse move (bullish order block) and the last bullish candle before a bearish impulse. When price returns to retest these institutional accumulation zones, enters in the original impulse direction.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'order_block',
        "params": {'impulse_mult': 1.3, 'atr_period': 14, 'rr_ratio': 2.5},
        "script": None, "csv": p("results/algo_572_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '573', "name": 'FAIR VALUE GAP ES 5m', "category": 'Order Flow',
        "description": (
            'Fair Value Gap (FVG) fill strategy on ES 5m. Detects 3-bar price imbalances where the low of the current bar is above the high of 2 bars ago (bullish FVG) or vice versa -- gaps that institutions are compelled to fill. Enters on price return to the gap for a mean-reversion fill trade.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'fair_value_gap',
        "params": {'min_gap_atr': 0.5, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_573_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '574', "name": 'FAIR VALUE GAP ES 1h', "category": 'Order Flow',
        "description": (
            'Fair Value Gap (FVG) fill strategy on ES 1h. Detects 3-bar price imbalances where the low of the current bar is above the high of 2 bars ago (bullish FVG) or vice versa -- gaps that institutions are compelled to fill. Enters on price return to the gap for a mean-reversion fill trade.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'fair_value_gap',
        "params": {'min_gap_atr': 0.4, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_574_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '575', "name": 'FAIR VALUE GAP NQ 5m', "category": 'Order Flow',
        "description": (
            'Fair Value Gap (FVG) fill strategy on NQ 5m. Detects 3-bar price imbalances where the low of the current bar is above the high of 2 bars ago (bullish FVG) or vice versa -- gaps that institutions are compelled to fill. Enters on price return to the gap for a mean-reversion fill trade.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'fair_value_gap',
        "params": {'min_gap_atr': 0.5, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_575_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '576', "name": 'FAIR VALUE GAP NQ 1h', "category": 'Order Flow',
        "description": (
            'Fair Value Gap (FVG) fill strategy on NQ 1h. Detects 3-bar price imbalances where the low of the current bar is above the high of 2 bars ago (bullish FVG) or vice versa -- gaps that institutions are compelled to fill. Enters on price return to the gap for a mean-reversion fill trade.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'fair_value_gap',
        "params": {'min_gap_atr': 0.4, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_576_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '577', "name": 'FAIR VALUE GAP GC 5m', "category": 'Order Flow',
        "description": (
            'Fair Value Gap (FVG) fill strategy on GC 5m. Detects 3-bar price imbalances where the low of the current bar is above the high of 2 bars ago (bullish FVG) or vice versa -- gaps that institutions are compelled to fill. Enters on price return to the gap for a mean-reversion fill trade.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'fair_value_gap',
        "params": {'min_gap_atr': 0.5, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_577_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '578', "name": 'FAIR VALUE GAP GC 1h', "category": 'Order Flow',
        "description": (
            'Fair Value Gap (FVG) fill strategy on GC 1h. Detects 3-bar price imbalances where the low of the current bar is above the high of 2 bars ago (bullish FVG) or vice versa -- gaps that institutions are compelled to fill. Enters on price return to the gap for a mean-reversion fill trade.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'fair_value_gap',
        "params": {'min_gap_atr': 0.4, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_578_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '579', "name": 'FAIR VALUE GAP CL 5m', "category": 'Order Flow',
        "description": (
            'Fair Value Gap (FVG) fill strategy on CL 5m. Detects 3-bar price imbalances where the low of the current bar is above the high of 2 bars ago (bullish FVG) or vice versa -- gaps that institutions are compelled to fill. Enters on price return to the gap for a mean-reversion fill trade.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'fair_value_gap',
        "params": {'min_gap_atr': 0.5, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_579_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '580', "name": 'FAIR VALUE GAP CL 1h', "category": 'Order Flow',
        "description": (
            'Fair Value Gap (FVG) fill strategy on CL 1h. Detects 3-bar price imbalances where the low of the current bar is above the high of 2 bars ago (bullish FVG) or vice versa -- gaps that institutions are compelled to fill. Enters on price return to the gap for a mean-reversion fill trade.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'fair_value_gap',
        "params": {'min_gap_atr': 0.4, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_580_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '581', "name": 'VOL PROFILE POC ES 5m', "category": 'Order Flow',
        "description": (
            'Rolling Volume Profile Point of Control (POC) reversion on ES 5m. Identifies the price level with highest traded volume over a rolling window -- the magnet where most business is done. When price deviates significantly from POC, fades the deviation expecting a return to the high-volume node.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'volume_profile_poc',
        "params": {'profile_period': 50, 'dev_atr': 1.5, 'atr_period': 14, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_581_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '582', "name": 'VOL PROFILE POC ES 1h', "category": 'Order Flow',
        "description": (
            'Rolling Volume Profile Point of Control (POC) reversion on ES 1h. Identifies the price level with highest traded volume over a rolling window -- the magnet where most business is done. When price deviates significantly from POC, fades the deviation expecting a return to the high-volume node.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'volume_profile_poc',
        "params": {'profile_period': 100, 'dev_atr': 1.3, 'atr_period': 14, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_582_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '583', "name": 'VOL PROFILE POC NQ 5m', "category": 'Order Flow',
        "description": (
            'Rolling Volume Profile Point of Control (POC) reversion on NQ 5m. Identifies the price level with highest traded volume over a rolling window -- the magnet where most business is done. When price deviates significantly from POC, fades the deviation expecting a return to the high-volume node.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'volume_profile_poc',
        "params": {'profile_period': 50, 'dev_atr': 1.5, 'atr_period': 14, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_583_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '584', "name": 'VOL PROFILE POC NQ 1h', "category": 'Order Flow',
        "description": (
            'Rolling Volume Profile Point of Control (POC) reversion on NQ 1h. Identifies the price level with highest traded volume over a rolling window -- the magnet where most business is done. When price deviates significantly from POC, fades the deviation expecting a return to the high-volume node.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'volume_profile_poc',
        "params": {'profile_period': 100, 'dev_atr': 1.3, 'atr_period': 14, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_584_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '585', "name": 'VOL PROFILE POC GC 5m', "category": 'Order Flow',
        "description": (
            'Rolling Volume Profile Point of Control (POC) reversion on GC 5m. Identifies the price level with highest traded volume over a rolling window -- the magnet where most business is done. When price deviates significantly from POC, fades the deviation expecting a return to the high-volume node.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'volume_profile_poc',
        "params": {'profile_period': 50, 'dev_atr': 1.5, 'atr_period': 14, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_585_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '586', "name": 'VOL PROFILE POC GC 1h', "category": 'Order Flow',
        "description": (
            'Rolling Volume Profile Point of Control (POC) reversion on GC 1h. Identifies the price level with highest traded volume over a rolling window -- the magnet where most business is done. When price deviates significantly from POC, fades the deviation expecting a return to the high-volume node.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'volume_profile_poc',
        "params": {'profile_period': 100, 'dev_atr': 1.3, 'atr_period': 14, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_586_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '587', "name": 'VOL PROFILE POC CL 5m', "category": 'Order Flow',
        "description": (
            'Rolling Volume Profile Point of Control (POC) reversion on CL 5m. Identifies the price level with highest traded volume over a rolling window -- the magnet where most business is done. When price deviates significantly from POC, fades the deviation expecting a return to the high-volume node.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'volume_profile_poc',
        "params": {'profile_period': 50, 'dev_atr': 1.5, 'atr_period': 14, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_587_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '588', "name": 'VOL PROFILE POC CL 1h', "category": 'Order Flow',
        "description": (
            'Rolling Volume Profile Point of Control (POC) reversion on CL 1h. Identifies the price level with highest traded volume over a rolling window -- the magnet where most business is done. When price deviates significantly from POC, fades the deviation expecting a return to the high-volume node.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'volume_profile_poc',
        "params": {'profile_period': 100, 'dev_atr': 1.3, 'atr_period': 14, 'rr_ratio': 1.5},
        "script": None, "csv": p("results/algo_588_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '589', "name": 'BID/ASK IMBALANCE ES 5m', "category": 'Order Flow',
        "description": (
            'Bid/ask order flow imbalance momentum on ES 5m. Approximates bid vs ask pressure using bar close position relative to high-low range. When N consecutive bars show overwhelming one-sided imbalance, enters in that direction as a momentum breakout. Captures institutional accumulation runs.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bid_ask_imbalance',
        "params": {'imbalance_thresh': 0.7, 'consecutive': 3, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_589_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '590', "name": 'BID/ASK IMBALANCE ES 1h', "category": 'Order Flow',
        "description": (
            'Bid/ask order flow imbalance momentum on ES 1h. Approximates bid vs ask pressure using bar close position relative to high-low range. When N consecutive bars show overwhelming one-sided imbalance, enters in that direction as a momentum breakout. Captures institutional accumulation runs.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bid_ask_imbalance',
        "params": {'imbalance_thresh': 0.65, 'consecutive': 3, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_590_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '591', "name": 'BID/ASK IMBALANCE NQ 5m', "category": 'Order Flow',
        "description": (
            'Bid/ask order flow imbalance momentum on NQ 5m. Approximates bid vs ask pressure using bar close position relative to high-low range. When N consecutive bars show overwhelming one-sided imbalance, enters in that direction as a momentum breakout. Captures institutional accumulation runs.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bid_ask_imbalance',
        "params": {'imbalance_thresh': 0.7, 'consecutive': 3, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_591_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '592', "name": 'BID/ASK IMBALANCE NQ 1h', "category": 'Order Flow',
        "description": (
            'Bid/ask order flow imbalance momentum on NQ 1h. Approximates bid vs ask pressure using bar close position relative to high-low range. When N consecutive bars show overwhelming one-sided imbalance, enters in that direction as a momentum breakout. Captures institutional accumulation runs.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bid_ask_imbalance',
        "params": {'imbalance_thresh': 0.65, 'consecutive': 3, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_592_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '593', "name": 'BID/ASK IMBALANCE GC 5m', "category": 'Order Flow',
        "description": (
            'Bid/ask order flow imbalance momentum on GC 5m. Approximates bid vs ask pressure using bar close position relative to high-low range. When N consecutive bars show overwhelming one-sided imbalance, enters in that direction as a momentum breakout. Captures institutional accumulation runs.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bid_ask_imbalance',
        "params": {'imbalance_thresh': 0.7, 'consecutive': 3, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_593_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '594', "name": 'BID/ASK IMBALANCE GC 1h', "category": 'Order Flow',
        "description": (
            'Bid/ask order flow imbalance momentum on GC 1h. Approximates bid vs ask pressure using bar close position relative to high-low range. When N consecutive bars show overwhelming one-sided imbalance, enters in that direction as a momentum breakout. Captures institutional accumulation runs.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bid_ask_imbalance',
        "params": {'imbalance_thresh': 0.65, 'consecutive': 3, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_594_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '595', "name": 'BID/ASK IMBALANCE CL 5m', "category": 'Order Flow',
        "description": (
            'Bid/ask order flow imbalance momentum on CL 5m. Approximates bid vs ask pressure using bar close position relative to high-low range. When N consecutive bars show overwhelming one-sided imbalance, enters in that direction as a momentum breakout. Captures institutional accumulation runs.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'bid_ask_imbalance',
        "params": {'imbalance_thresh': 0.7, 'consecutive': 3, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_595_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '596', "name": 'BID/ASK IMBALANCE CL 1h', "category": 'Order Flow',
        "description": (
            'Bid/ask order flow imbalance momentum on CL 1h. Approximates bid vs ask pressure using bar close position relative to high-low range. When N consecutive bars show overwhelming one-sided imbalance, enters in that direction as a momentum breakout. Captures institutional accumulation runs.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'bid_ask_imbalance',
        "params": {'imbalance_thresh': 0.65, 'consecutive': 3, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_596_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '597', "name": 'EXHAUSTION GAP ES 5m', "category": 'Order Flow',
        "description": (
            'Declining volume gap exhaustion reversal on ES 5m. A gap in the direction of trend with declining volume signals that the trend is losing institutional sponsorship. The combination of structural gap + volume fade = exhaustion. Fades the move for a counter-trend entry at the gap level.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'exhaustion_gap',
        "params": {'vol_decline_pct': 0.7, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_597_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '598', "name": 'EXHAUSTION GAP ES 1h', "category": 'Order Flow',
        "description": (
            'Declining volume gap exhaustion reversal on ES 1h. A gap in the direction of trend with declining volume signals that the trend is losing institutional sponsorship. The combination of structural gap + volume fade = exhaustion. Fades the move for a counter-trend entry at the gap level.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'exhaustion_gap',
        "params": {'vol_decline_pct': 0.75, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_598_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '599', "name": 'EXHAUSTION GAP NQ 5m', "category": 'Order Flow',
        "description": (
            'Declining volume gap exhaustion reversal on NQ 5m. A gap in the direction of trend with declining volume signals that the trend is losing institutional sponsorship. The combination of structural gap + volume fade = exhaustion. Fades the move for a counter-trend entry at the gap level.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'exhaustion_gap',
        "params": {'vol_decline_pct': 0.7, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_599_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '600', "name": 'EXHAUSTION GAP NQ 1h', "category": 'Order Flow',
        "description": (
            'Declining volume gap exhaustion reversal on NQ 1h. A gap in the direction of trend with declining volume signals that the trend is losing institutional sponsorship. The combination of structural gap + volume fade = exhaustion. Fades the move for a counter-trend entry at the gap level.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'exhaustion_gap',
        "params": {'vol_decline_pct': 0.75, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_600_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '601', "name": 'EXHAUSTION GAP GC 5m', "category": 'Order Flow',
        "description": (
            'Declining volume gap exhaustion reversal on GC 5m. A gap in the direction of trend with declining volume signals that the trend is losing institutional sponsorship. The combination of structural gap + volume fade = exhaustion. Fades the move for a counter-trend entry at the gap level.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'exhaustion_gap',
        "params": {'vol_decline_pct': 0.7, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_601_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '602', "name": 'EXHAUSTION GAP GC 1h', "category": 'Order Flow',
        "description": (
            'Declining volume gap exhaustion reversal on GC 1h. A gap in the direction of trend with declining volume signals that the trend is losing institutional sponsorship. The combination of structural gap + volume fade = exhaustion. Fades the move for a counter-trend entry at the gap level.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'exhaustion_gap',
        "params": {'vol_decline_pct': 0.75, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_602_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '603', "name": 'EXHAUSTION GAP CL 5m', "category": 'Order Flow',
        "description": (
            'Declining volume gap exhaustion reversal on CL 5m. A gap in the direction of trend with declining volume signals that the trend is losing institutional sponsorship. The combination of structural gap + volume fade = exhaustion. Fades the move for a counter-trend entry at the gap level.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'exhaustion_gap',
        "params": {'vol_decline_pct': 0.7, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_603_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '604', "name": 'EXHAUSTION GAP CL 1h', "category": 'Order Flow',
        "description": (
            'Declining volume gap exhaustion reversal on CL 1h. A gap in the direction of trend with declining volume signals that the trend is losing institutional sponsorship. The combination of structural gap + volume fade = exhaustion. Fades the move for a counter-trend entry at the gap level.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'exhaustion_gap',
        "params": {'vol_decline_pct': 0.75, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_604_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '605', "name": 'CVD + DONCHIAN ES 5m', "category": 'Order Flow',
        "description": (
            'CVD trend with Donchian breakout confirmation on ES 5m. Combines Cumulative Volume Delta EMA direction with Donchian Channel breakout to enter only when both institutional flow direction and price structure agree. Reduces false breakouts by requiring buying pressure to accompany price breakout.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'cumulative_delta_trend',
        "params": {'cvd_period': 20, 'don_period': 20, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_605_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '606', "name": 'CVD + DONCHIAN ES 1h', "category": 'Order Flow',
        "description": (
            'CVD trend with Donchian breakout confirmation on ES 1h. Combines Cumulative Volume Delta EMA direction with Donchian Channel breakout to enter only when both institutional flow direction and price structure agree. Reduces false breakouts by requiring buying pressure to accompany price breakout.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'cumulative_delta_trend',
        "params": {'cvd_period': 30, 'don_period': 30, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_606_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '607', "name": 'CVD + DONCHIAN NQ 5m', "category": 'Order Flow',
        "description": (
            'CVD trend with Donchian breakout confirmation on NQ 5m. Combines Cumulative Volume Delta EMA direction with Donchian Channel breakout to enter only when both institutional flow direction and price structure agree. Reduces false breakouts by requiring buying pressure to accompany price breakout.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'cumulative_delta_trend',
        "params": {'cvd_period': 20, 'don_period': 20, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_607_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '608', "name": 'CVD + DONCHIAN NQ 1h', "category": 'Order Flow',
        "description": (
            'CVD trend with Donchian breakout confirmation on NQ 1h. Combines Cumulative Volume Delta EMA direction with Donchian Channel breakout to enter only when both institutional flow direction and price structure agree. Reduces false breakouts by requiring buying pressure to accompany price breakout.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'cumulative_delta_trend',
        "params": {'cvd_period': 30, 'don_period': 30, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_608_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '609', "name": 'CVD + DONCHIAN GC 5m', "category": 'Order Flow',
        "description": (
            'CVD trend with Donchian breakout confirmation on GC 5m. Combines Cumulative Volume Delta EMA direction with Donchian Channel breakout to enter only when both institutional flow direction and price structure agree. Reduces false breakouts by requiring buying pressure to accompany price breakout.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'cumulative_delta_trend',
        "params": {'cvd_period': 20, 'don_period': 20, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_609_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '610', "name": 'CVD + DONCHIAN GC 1h', "category": 'Order Flow',
        "description": (
            'CVD trend with Donchian breakout confirmation on GC 1h. Combines Cumulative Volume Delta EMA direction with Donchian Channel breakout to enter only when both institutional flow direction and price structure agree. Reduces false breakouts by requiring buying pressure to accompany price breakout.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'cumulative_delta_trend',
        "params": {'cvd_period': 30, 'don_period': 30, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_610_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '611', "name": 'CVD + DONCHIAN CL 5m', "category": 'Order Flow',
        "description": (
            'CVD trend with Donchian breakout confirmation on CL 5m. Combines Cumulative Volume Delta EMA direction with Donchian Channel breakout to enter only when both institutional flow direction and price structure agree. Reduces false breakouts by requiring buying pressure to accompany price breakout.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'cumulative_delta_trend',
        "params": {'cvd_period': 20, 'don_period': 20, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_611_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '612', "name": 'CVD + DONCHIAN CL 1h', "category": 'Order Flow',
        "description": (
            'CVD trend with Donchian breakout confirmation on CL 1h. Combines Cumulative Volume Delta EMA direction with Donchian Channel breakout to enter only when both institutional flow direction and price structure agree. Reduces false breakouts by requiring buying pressure to accompany price breakout.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'cumulative_delta_trend',
        "params": {'cvd_period': 30, 'don_period': 30, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_612_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '613', "name": 'TAPE EXHAUSTION ES 5m', "category": 'Order Flow',
        "description": (
            'Tape speed exhaustion reversal on ES 5m. When volume velocity (tape speed) spikes to extreme levels but price barely moves -- maximum urgency with minimal result -- the move is exhausted. Fades the direction of the tape spike for a high-R reversal. Combines volume urgency analysis with effort vs result.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'tape_exhaustion_reversal',
        "params": {'speed_pct': 90, 'move_pct': 20, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_613_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '614', "name": 'TAPE EXHAUSTION ES 1h', "category": 'Order Flow',
        "description": (
            'Tape speed exhaustion reversal on ES 1h. When volume velocity (tape speed) spikes to extreme levels but price barely moves -- maximum urgency with minimal result -- the move is exhausted. Fades the direction of the tape spike for a high-R reversal. Combines volume urgency analysis with effort vs result.'
        ),
        "market": 'ES=F', "tick_value": 50.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'tape_exhaustion_reversal',
        "params": {'speed_pct': 85, 'move_pct': 25, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_614_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '615', "name": 'TAPE EXHAUSTION NQ 5m', "category": 'Order Flow',
        "description": (
            'Tape speed exhaustion reversal on NQ 5m. When volume velocity (tape speed) spikes to extreme levels but price barely moves -- maximum urgency with minimal result -- the move is exhausted. Fades the direction of the tape spike for a high-R reversal. Combines volume urgency analysis with effort vs result.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'tape_exhaustion_reversal',
        "params": {'speed_pct': 90, 'move_pct': 20, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_615_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '616', "name": 'TAPE EXHAUSTION NQ 1h', "category": 'Order Flow',
        "description": (
            'Tape speed exhaustion reversal on NQ 1h. When volume velocity (tape speed) spikes to extreme levels but price barely moves -- maximum urgency with minimal result -- the move is exhausted. Fades the direction of the tape spike for a high-R reversal. Combines volume urgency analysis with effort vs result.'
        ),
        "market": 'NQ=F', "tick_value": 20.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'tape_exhaustion_reversal',
        "params": {'speed_pct': 85, 'move_pct': 25, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_616_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '617', "name": 'TAPE EXHAUSTION GC 5m', "category": 'Order Flow',
        "description": (
            'Tape speed exhaustion reversal on GC 5m. When volume velocity (tape speed) spikes to extreme levels but price barely moves -- maximum urgency with minimal result -- the move is exhausted. Fades the direction of the tape spike for a high-R reversal. Combines volume urgency analysis with effort vs result.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'tape_exhaustion_reversal',
        "params": {'speed_pct': 90, 'move_pct': 20, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_617_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '618', "name": 'TAPE EXHAUSTION GC 1h', "category": 'Order Flow',
        "description": (
            'Tape speed exhaustion reversal on GC 1h. When volume velocity (tape speed) spikes to extreme levels but price barely moves -- maximum urgency with minimal result -- the move is exhausted. Fades the direction of the tape spike for a high-R reversal. Combines volume urgency analysis with effort vs result.'
        ),
        "market": 'GC=F', "tick_value": 100.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'tape_exhaustion_reversal',
        "params": {'speed_pct': 85, 'move_pct': 25, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_618_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '619', "name": 'TAPE EXHAUSTION CL 5m', "category": 'Order Flow',
        "description": (
            'Tape speed exhaustion reversal on CL 5m. When volume velocity (tape speed) spikes to extreme levels but price barely moves -- maximum urgency with minimal result -- the move is exhausted. Fades the direction of the tape spike for a high-R reversal. Combines volume urgency analysis with effort vs result.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '5m', "period": '60d',
        "status": 'TESTING', "engine": 'tape_exhaustion_reversal',
        "params": {'speed_pct': 90, 'move_pct': 20, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_619_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
    {
        "id": '620', "name": 'TAPE EXHAUSTION CL 1h', "category": 'Order Flow',
        "description": (
            'Tape speed exhaustion reversal on CL 1h. When volume velocity (tape speed) spikes to extreme levels but price barely moves -- maximum urgency with minimal result -- the move is exhausted. Fades the direction of the tape spike for a high-R reversal. Combines volume urgency analysis with effort vs result.'
        ),
        "market": 'CL=F', "tick_value": 1000.0, "timeframe": '1h', "period": '730d',
        "status": 'TESTING', "engine": 'tape_exhaustion_reversal',
        "params": {'speed_pct': 85, 'move_pct': 25, 'atr_period': 14, 'rr_ratio': 2.0},
        "script": None, "csv": p("results/algo_620_trades.csv"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    },
]
