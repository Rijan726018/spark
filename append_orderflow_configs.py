"""
Appends ~60 Order Flow configs (IDs 501-560) to algo_configs.py
"""
from pathlib import Path

BASE = Path(__file__).parent

OF_MARKETS = [
    ("ES=F", 50.0),
    ("NQ=F", 20.0),
    ("GC=F", 100.0),
    ("CL=F", 1000.0),
]

# (engine, short_name, description_template, params_5m, params_1h)
OF_STRATEGIES = [
    (
        "orderflow_delta",
        "CVD DELTA TREND",
        "Cumulative Volume Delta trend-following on {market} {tf}. Measures buying vs selling pressure via CVD EMA crossover. Long when fast CVD EMA crosses above slow, confirming bullish delta dominance. Short on bearish cross. Stops set at 1 ATR, targets at 2 ATR.",
        {"cvd_fast": 5, "cvd_slow": 20, "atr_period": 14, "rr_ratio": 2.0},
        {"cvd_fast": 8, "cvd_slow": 34, "atr_period": 14, "rr_ratio": 2.0},
    ),
    (
        "absorption_reversal",
        "ABSORPTION REVERSAL",
        "Detects institutional absorption on {market} {tf}. High effort (volume spike) with minimal result (tiny body) signals hidden buyers/sellers absorbing flow. Fades the direction of absorption for a mean-reversion entry. Uses Wyckoff effort-vs-result analysis.",
        {"atr_period": 14, "vol_mult": 2.0, "body_pct": 0.3, "rr_ratio": 2.0},
        {"atr_period": 14, "vol_mult": 1.8, "body_pct": 0.35, "rr_ratio": 2.0},
    ),
    (
        "trapped_breakout",
        "TRAPPED TRADERS",
        "Trapped trader squeeze on {market} {tf}. Identifies bars that break to new highs/lows then close back inside the range, trapping breakout traders. Fades the breakout once price reverses back through the trap level. High-probability mean-reversion setup.",
        {"lookback": 20, "atr_period": 14, "rr_ratio": 2.0},
        {"lookback": 30, "atr_period": 14, "rr_ratio": 2.5},
    ),
    (
        "tape_momentum",
        "TAPE MOMENTUM",
        "Tape speed momentum on {market} {tf}. Measures urgency of order flow via volume EMA ratio (fast/slow). When tape accelerates significantly (ratio > threshold) in direction of trend (EMA slope), enters with momentum. Combines volume urgency with price direction.",
        {"fast_vol": 5, "slow_vol": 20, "speed_thresh": 1.5, "atr_period": 14, "rr_ratio": 2.0},
        {"fast_vol": 8, "slow_vol": 34, "speed_thresh": 1.4, "atr_period": 14, "rr_ratio": 2.0},
    ),
    (
        "evr_reversal",
        "EFFORT VS RESULT",
        "Effort vs Result reversal on {market} {tf}. When a bar shows extreme volume (effort) but fails to move price significantly (poor result), it reveals institutional absorption. This exhaustion signal triggers a counter-trend entry. Classic Wyckoff principle.",
        {"vol_percentile": 90, "move_percentile": 30, "atr_period": 14, "rr_ratio": 2.0},
        {"vol_percentile": 85, "move_percentile": 35, "atr_period": 14, "rr_ratio": 2.0},
    ),
    (
        "iceberg_reversal",
        "ICEBERG DETECTOR",
        "Institutional iceberg order detection on {market} {tf}. Identifies hidden large orders that keep refilling at the same price level -- tight price range + repeated high volume = iceberg. Trades the breakout direction once the iceberg is consumed and price is free to move.",
        {"price_threshold": 0.002, "vol_mult": 3.0, "consecutive": 3, "atr_period": 14, "rr_ratio": 2.0},
        {"price_threshold": 0.003, "vol_mult": 2.5, "consecutive": 3, "atr_period": 14, "rr_ratio": 2.0},
    ),
    (
        "delta_exhaustion",
        "DELTA EXHAUSTION",
        "CVD delta exhaustion reversal on {market} {tf}. When Cumulative Volume Delta reaches an extreme percentile (overbought/oversold buying or selling pressure) but price fails to confirm with a new high/low, the fuel is exhausted. Fades the move for a high-probability reversal entry.",
        {"cvd_period": 20, "cvd_pct": 90, "atr_period": 14, "rr_ratio": 2.0},
        {"cvd_period": 30, "cvd_pct": 85, "atr_period": 14, "rr_ratio": 2.0},
    ),
    (
        "stop_hunt",
        "STOP HUNT FADE",
        "Liquidity sweep / stop hunt reversal on {market} {tf}. Price wicks below the N-bar swing low (triggering retail stop orders) then closes back above it -- the classic institutional stop raid. Enters long on close-back-above. Short version fades wicks above swing highs. High win rate with defined risk.",
        {"lookback": 20, "atr_period": 14, "rr_ratio": 2.0},
        {"lookback": 30, "atr_period": 14, "rr_ratio": 2.5},
    ),
    (
        "order_block",
        "ORDER BLOCK RETEST",
        "Smart Money Concept (SMC) order block retest on {market} {tf}. Identifies the last bearish candle before a bullish impulse move (bullish order block) and the last bullish candle before a bearish impulse. When price returns to retest these institutional accumulation zones, enters in the original impulse direction.",
        {"impulse_mult": 1.5, "atr_period": 14, "rr_ratio": 2.0},
        {"impulse_mult": 1.3, "atr_period": 14, "rr_ratio": 2.5},
    ),
    (
        "fair_value_gap",
        "FAIR VALUE GAP",
        "Fair Value Gap (FVG) fill strategy on {market} {tf}. Detects 3-bar price imbalances where the low of the current bar is above the high of 2 bars ago (bullish FVG) or vice versa -- gaps that institutions are compelled to fill. Enters on price return to the gap for a mean-reversion fill trade.",
        {"min_gap_atr": 0.5, "atr_period": 14, "rr_ratio": 2.0},
        {"min_gap_atr": 0.4, "atr_period": 14, "rr_ratio": 2.0},
    ),
    (
        "volume_profile_poc",
        "VOL PROFILE POC",
        "Rolling Volume Profile Point of Control (POC) reversion on {market} {tf}. Identifies the price level with highest traded volume over a rolling window -- the magnet where most business is done. When price deviates significantly from POC, fades the deviation expecting a return to the high-volume node.",
        {"profile_period": 50, "dev_atr": 1.5, "atr_period": 14, "rr_ratio": 1.5},
        {"profile_period": 100, "dev_atr": 1.3, "atr_period": 14, "rr_ratio": 1.5},
    ),
    (
        "bid_ask_imbalance",
        "BID/ASK IMBALANCE",
        "Bid/ask order flow imbalance momentum on {market} {tf}. Approximates bid vs ask pressure using bar close position relative to high-low range. When N consecutive bars show overwhelming one-sided imbalance, enters in that direction as a momentum breakout. Captures institutional accumulation runs.",
        {"imbalance_thresh": 0.7, "consecutive": 3, "atr_period": 14, "rr_ratio": 2.0},
        {"imbalance_thresh": 0.65, "consecutive": 3, "atr_period": 14, "rr_ratio": 2.0},
    ),
    (
        "exhaustion_gap",
        "EXHAUSTION GAP",
        "Declining volume gap exhaustion reversal on {market} {tf}. A gap in the direction of trend with declining volume signals that the trend is losing institutional sponsorship. The combination of structural gap + volume fade = exhaustion. Fades the move for a counter-trend entry at the gap level.",
        {"vol_decline_pct": 0.7, "atr_period": 14, "rr_ratio": 2.0},
        {"vol_decline_pct": 0.75, "atr_period": 14, "rr_ratio": 2.0},
    ),
    (
        "cumulative_delta_trend",
        "CVD + DONCHIAN",
        "CVD trend with Donchian breakout confirmation on {market} {tf}. Combines Cumulative Volume Delta EMA direction with Donchian Channel breakout to enter only when both institutional flow direction and price structure agree. Reduces false breakouts by requiring buying pressure to accompany price breakout.",
        {"cvd_period": 20, "don_period": 20, "atr_period": 14, "rr_ratio": 2.0},
        {"cvd_period": 30, "don_period": 30, "atr_period": 14, "rr_ratio": 2.0},
    ),
    (
        "tape_exhaustion_reversal",
        "TAPE EXHAUSTION",
        "Tape speed exhaustion reversal on {market} {tf}. When volume velocity (tape speed) spikes to extreme levels but price barely moves -- maximum urgency with minimal result -- the move is exhausted. Fades the direction of the tape spike for a high-R reversal. Combines volume urgency analysis with effort vs result.",
        {"speed_pct": 90, "move_pct": 20, "atr_period": 14, "rr_ratio": 2.0},
        {"speed_pct": 85, "move_pct": 25, "atr_period": 14, "rr_ratio": 2.0},
    ),
]

# Build configs starting at ID 501
configs = []
algo_id = 501

for engine, short_name, desc_tpl, params_5m, params_1h in OF_STRATEGIES:
    for market, tick_value in OF_MARKETS:
        mkt_short = market.replace("=F", "")

        # 5m version
        name_5m = f"{short_name} {mkt_short} 5m"
        desc_5m = desc_tpl.format(market=mkt_short, tf="5m")
        cfg_5m = {
            "id": str(algo_id),
            "name": name_5m,
            "category": "Order Flow",
            "description": desc_5m,
            "market": market,
            "tick_value": tick_value,
            "timeframe": "5m",
            "period": "60d",
            "status": "TESTING",
            "engine": engine,
            "params": params_5m,
            "csv": f"results/algo_{algo_id}_trades.csv",
        }
        configs.append(cfg_5m)
        algo_id += 1

        # 1h version
        name_1h = f"{short_name} {mkt_short} 1h"
        desc_1h = desc_tpl.format(market=mkt_short, tf="1h")
        cfg_1h = {
            "id": str(algo_id),
            "name": name_1h,
            "category": "Order Flow",
            "description": desc_1h,
            "market": market,
            "tick_value": tick_value,
            "timeframe": "1h",
            "period": "730d",
            "status": "TESTING",
            "engine": engine,
            "params": params_1h,
            "csv": f"results/algo_{algo_id}_trades.csv",
        }
        configs.append(cfg_1h)
        algo_id += 1

print(f"Generated {len(configs)} Order Flow configs (IDs 501-{algo_id-1})")

# --- Append to algo_configs.py ---
configs_path = BASE / "algo_configs.py"
content = configs_path.read_text(encoding="utf-8")

# Find the closing bracket of ALGO_CONFIGS
last_bracket = content.rfind("]")
if last_bracket == -1:
    raise RuntimeError("Could not find closing ] in algo_configs.py")

# Build the block to insert
lines = []
for c in configs:
    iid   = c["id"]
    name  = c["name"]
    cat   = c["category"]
    desc  = c["description"].replace("'", "\\'")
    mkt   = c["market"]
    tv    = c["tick_value"]
    tf    = c["timeframe"]
    per   = c["period"]
    st    = c["status"]
    eng   = c["engine"]
    pms   = c["params"]
    csv   = c["csv"]
    lines.append(f"""    {{
        "id": '{iid}', "name": '{name}', "category": '{cat}',
        "description": (
            '{desc}'
        ),
        "market": '{mkt}', "tick_value": {tv}, "timeframe": '{tf}', "period": '{per}',
        "status": '{st}', "engine": '{eng}',
        "params": {pms},
        "script": None, "csv": p("{csv}"), "alt_csv": None,
        "chart": None, "alt_chart": None,
    }},""")

insert_block = "\n" + "\n".join(lines) + "\n"

new_content = content[:last_bracket] + insert_block + content[last_bracket:]
configs_path.write_text(new_content, encoding="utf-8")
print(f"Appended {len(configs)} Order Flow configs to algo_configs.py")

# Quick verify
import importlib, sys
if "algo_configs" in sys.modules:
    del sys.modules["algo_configs"]
import algo_configs
of_count = sum(1 for a in algo_configs.ALGO_CONFIGS if a.get("category") == "Order Flow")
print(f"Total configs: {len(algo_configs.ALGO_CONFIGS)}  |  Order Flow: {of_count}")
