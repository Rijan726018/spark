"""Writes a clean algo_configs.py from scratch."""
import sys
sys.path.insert(0, '.')
from generate_configs import generate_configs

# ─── The 5 real LIVE algos (actual scripts/CSVs exist) ───────────────────────
LIVE_CONFIGS = [
    {
        "id": "01", "name": "BB + CVD DIVERGENCE", "category": "Mean Reversion",
        "description": (
            "Enters when price touches the outer Bollinger Band (20-period, 2 sigma) "
            "while Cumulative Volume Delta diverges -- price makes a new extreme but CVD does not, "
            "revealing hidden absorption. Long at lower band when price makes lower low but CVD "
            "makes higher low; short at upper band when price makes higher high but CVD makes lower "
            "high. Target is always the opposite Bollinger Band. Stop is placed just beyond the "
            "signal band. Works best in liquid sessions with real volume data."
        ),
        "market": "ES=F", "tick_value": 50.0, "timeframe": "5m", "period": "60d",
        "status": "LIVE", "engine": "bb_cvd",
        "params": {"bb_period": 20, "bb_std": 2.0, "cvd_lookback": 5},
        "script": "algos/algo_01_bb_cvd.py",
        "csv": "results/algo_01_trades.csv",
        "alt_csv": "results/algo_01_1h_trades.csv",
        "alt_timeframe": "1h", "alt_period": "730d",
        "chart": "results/algo_01_bb_cvd.png",
        "alt_chart": "results/algo_01_bb_cvd_1h.png",
    },
    {
        "id": "02", "name": "VWAP REVERSION", "category": "Mean Reversion",
        "description": (
            "Identifies extreme VWAP deviations using intraday volume-weighted standard deviation "
            "bands that reset each session. When price crosses 2.5-sigma below VWAP and the next bar "
            "shows recovery (close > prior close), a long is entered targeting VWAP itself. "
            "The reverse applies for shorts above 2.5-sigma. Stop is placed 30% of the band width "
            "beyond the signal level. Filters out the first bar of each day where std is zero. "
            "Designed to capture rubber-band snapbacks to fair value."
        ),
        "market": "ES=F", "tick_value": 50.0, "timeframe": "5m", "period": "60d",
        "status": "LIVE", "engine": "vwap_rev",
        "params": {"upper_band": 2.5, "lower_band": 2.5, "stop_buffer": 0.3},
        "script": "algos/algo_02_vwap_reversion.py",
        "csv": "results/algo_02_trades.csv",
        "alt_csv": None, "chart": "results/algo_02_vwap_reversion.png", "alt_chart": None,
    },
    {
        "id": "03", "name": "MOMENTUM BREAKOUT", "category": "Breakout",
        "description": (
            "Uses a 20-bar Donchian Channel on 15-minute bars. A long signal fires when price "
            "closes above the prior channel high with volume exceeding 1.5x its 20-bar average, "
            "confirming institutional participation. ATR(14) sizes the trade: target is entry "
            "plus 2x ATR, stop is entry minus 1x ATR, giving a 2:1 reward-to-risk. "
            "The same logic inverted triggers shorts below the channel low. "
            "Volume filter eliminates false breakouts during thin overnight sessions."
        ),
        "market": "ES=F", "tick_value": 50.0, "timeframe": "15m", "period": "60d",
        "status": "LIVE", "engine": "donchian",
        "params": {"dc_period": 20, "vol_mult": 1.5, "rr_ratio": 2.0},
        "script": "algos/algo_03_momentum_breakout.py",
        "csv": "results/algo_03_trades.csv",
        "alt_csv": None, "chart": "results/algo_03_momentum_breakout.png", "alt_chart": None,
    },
    {
        "id": "04", "name": "OPENING RANGE BREAKOUT", "category": "Breakout",
        "description": (
            "Defines the opening range as the high and low of the first two hourly RTH bars "
            "(9AM and 10AM ET). A long triggers on the first hourly bar that closes above OR High; "
            "a short triggers on the first close below OR Low. "
            "Target equals the OR range projected from the breakout level; stop is the opposite OR level. "
            "Only one trade per day, no entries after 3 PM ET. "
            "Skips days with OR range below 3 points. Backtested on both ES and NQ across 730 days."
        ),
        "market": "ES=F", "tick_value": 50.0, "timeframe": "1h", "period": "730d",
        "status": "LIVE", "engine": "orb",
        "params": {"or_minutes": 30, "min_range": 3.0, "cutoff_hour": 15},
        "script": "algos/algo_04_opening_range.py",
        "csv": "results/algo_04_trades.csv",
        "alt_csv": None, "chart": "results/algo_04_opening_range.png", "alt_chart": None,
    },
    {
        "id": "05", "name": "EMA CROSSOVER", "category": "Trend Following",
        "description": (
            "A classic dual-EMA crossover system refined with RSI and volume confirmation. "
            "Enters long when the 9-period EMA crosses above the 21-period EMA, RSI(14) is above 50 "
            "(confirming momentum), and volume exceeds its 20-bar average. "
            "Target is 2x ATR(14) above entry; stop is 1x ATR below. "
            "Short signals use the reverse logic. Runs on 15-minute bars to filter out "
            "microstructure noise while remaining responsive to intraday trends."
        ),
        "market": "ES=F", "tick_value": 50.0, "timeframe": "15m", "period": "60d",
        "status": "LIVE", "engine": "ema_cross",
        "params": {"ema_fast": 9, "ema_slow": 21, "rsi_period": 14, "vol_sma": 20, "rr_ratio": 2.0},
        "script": "algos/algo_05_ema_crossover.py",
        "csv": "results/algo_05_trades.csv",
        "alt_csv": None, "chart": "results/algo_05_ema_crossover.png", "alt_chart": None,
    },
]

# Generate 495 new configs (101-595 → we'll use 101-500 to get to 505 total, take first 495)
new_cfgs = generate_configs()  # returns 400

# Combine
all_configs = LIVE_CONFIGS + new_cfgs
print(f"Total configs: {len(all_configs)} (5 LIVE + {len(new_cfgs)} generated)")

# Write the file
header = '''\"""
ALGO CONFIGS -- 500 Trading Algorithm Registry
Each config defines a fully described strategy for ES/NQ/Gold/Oil/Bond futures.
\"""
from pathlib import Path

BASE = Path(__file__).parent

def p(rel):
    return str(BASE / rel) if rel else None

ALGO_CONFIGS = [
'''

lines = [header]

for c in all_configs:
    cid = c["id"]
    lines.append('    {')
    lines.append(f'        "id": {repr(str(cid))}, "name": {repr(c["name"])}, "category": {repr(c["category"])},')
    lines.append(f'        "description": (')
    lines.append(f'            {repr(c["description"])}')
    lines.append(f'        ),')
    lines.append(f'        "market": {repr(c["market"])}, "tick_value": {c["tick_value"]}, "timeframe": {repr(c["timeframe"])}, "period": {repr(c["period"])},')
    lines.append(f'        "status": {repr(c["status"])}, "engine": {repr(c.get("engine",""))},')
    lines.append(f'        "params": {repr(c.get("params",{}))},')

    def pval(val):
        if val is None:
            return 'None'
        val = str(val).replace('\\', '/')
        for prefix in ['C:/Users/rijan/Claude/', 'C:\\Users\\rijan\\Claude\\']:
            if val.startswith(prefix):
                rel = val[len(prefix):]
                return f'p("{rel}")'
        import re
        m = re.search(r'(algos|results|engines)/', val)
        if m:
            rel = val[val.index(m.group()):]
            return f'p("{rel}")'
        return repr(val)

    script   = pval(c.get("script"))
    csv      = pval(c.get("csv"))
    alt_csv  = pval(c.get("alt_csv")) if c.get("alt_csv") else 'None'
    chart    = pval(c.get("chart"))   if c.get("chart")   else 'None'
    alt_chart= pval(c.get("alt_chart")) if c.get("alt_chart") else 'None'

    lines.append(f'        "script": {script}, "csv": {csv}, "alt_csv": {alt_csv},')
    lines.append(f'        "chart": {chart}, "alt_chart": {alt_chart},')

    if c.get("alt_timeframe"):
        lines.append(f'        "alt_timeframe": {repr(c["alt_timeframe"])}, "alt_period": {repr(c.get("alt_period",""))},')

    lines.append('    },')

lines.append(']')
lines.append('')

content = '\n'.join(lines)
with open('algo_configs.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Wrote algo_configs.py ({len(content):,} bytes)")

# Verify
import importlib, sys
if 'algo_configs' in sys.modules:
    del sys.modules['algo_configs']
import algo_configs
statuses = {}
for a in algo_configs.ALGO_CONFIGS:
    s = a.get('status','?')
    statuses[s] = statuses.get(s,0) + 1
print(f"Verification: {len(algo_configs.ALGO_CONFIGS)} total | {statuses}")
