"""
Generates algo_configs.py with 500 trading algorithm configurations.
Run: python generate_configs.py
"""
from pathlib import Path

BASE_DIR = Path(__file__).parent

# ─────────────────────────────────────────────────────────────────────────────
# Market definitions
# ─────────────────────────────────────────────────────────────────────────────
MARKETS = {
    "ES=F":  {"name": "E-mini S&P 500",     "tick": 50.0,   "cat": "Equity Index"},
    "NQ=F":  {"name": "E-mini NASDAQ 100",  "tick": 20.0,   "cat": "Equity Index"},
    "YM=F":  {"name": "E-mini Dow Jones",   "tick": 5.0,    "cat": "Equity Index"},
    "RTY=F": {"name": "E-mini Russell 2000","tick": 50.0,   "cat": "Equity Index"},
    "GC=F":  {"name": "Gold Futures",       "tick": 100.0,  "cat": "Commodity"},
    "SI=F":  {"name": "Silver Futures",     "tick": 50.0,   "cat": "Commodity"},
    "CL=F":  {"name": "Crude Oil Futures",  "tick": 1000.0, "cat": "Energy"},
    "NG=F":  {"name": "Natural Gas Futures","tick": 100.0,  "cat": "Energy"},
    "ZB=F":  {"name": "30-Year T-Bond",     "tick": 1000.0, "cat": "Fixed Income"},
    "ZN=F":  {"name": "10-Year T-Note",     "tick": 1000.0, "cat": "Fixed Income"},
}

# ─────────────────────────────────────────────────────────────────────────────
# Strategy templates: (engine, category, description_template, params_variants)
# ─────────────────────────────────────────────────────────────────────────────
STRATEGY_TEMPLATES = [
    {
        "engine": "bb_cvd",
        "category": "Mean Reversion",
        "desc": (
            "Bollinger Band ({bb_period},{bb_std}σ) with Cumulative Volume Delta divergence. "
            "Enters long when price tags the lower band while CVD makes a higher low, revealing hidden demand. "
            "Enters short at the upper band when CVD makes a lower high despite a price higher high. "
            "Target is always the opposite band; stop is just beyond the signal band. "
            "Effective on {market} {tf} bars during active sessions."
        ),
        "variants": [
            {"bb_period": 20, "bb_std": 2.0, "cvd_lookback": 5},
            {"bb_period": 14, "bb_std": 2.0, "cvd_lookback": 3},
            {"bb_period": 20, "bb_std": 1.5, "cvd_lookback": 8},
        ],
    },
    {
        "engine": "rsi_rev",
        "category": "Mean Reversion",
        "desc": (
            "RSI({rsi_period}) mean-reversion strategy on {market} {tf} bars. "
            "Enters long when RSI crosses back above the oversold level ({oversold}), signalling exhausted selling. "
            "Enters short when RSI crosses back below overbought ({overbought}), signalling exhausted buying. "
            "ATR-based {rr_ratio}:1 reward-to-risk on every trade. "
            "Performs best in ranging, non-trending market conditions."
        ),
        "variants": [
            {"rsi_period": 14, "overbought": 70, "oversold": 30, "rr_ratio": 2.0},
            {"rsi_period": 9,  "overbought": 75, "oversold": 25, "rr_ratio": 2.0},
            {"rsi_period": 21, "overbought": 65, "oversold": 35, "rr_ratio": 2.0},
        ],
    },
    {
        "engine": "macd",
        "category": "Trend Following",
        "desc": (
            "MACD({macd_fast},{macd_slow},{macd_signal}) crossover with histogram momentum filter on {market}. "
            "Goes long when the MACD line crosses above signal and the histogram is growing. "
            "Goes short on the inverse. Uses ATR({rr_ratio}:1 R:R) for dynamic profit targets and stops. "
            "Runs on {tf} bars for {period} of historical data. "
            "The histogram confirmation reduces false crossover signals significantly."
        ),
        "variants": [
            {"macd_fast": 12, "macd_slow": 26, "macd_signal": 9, "rr_ratio": 2.0},
            {"macd_fast": 8,  "macd_slow": 21, "macd_signal": 5, "rr_ratio": 2.0},
            {"macd_fast": 5,  "macd_slow": 13, "macd_signal": 3, "rr_ratio": 1.5},
        ],
    },
    {
        "engine": "ema_cross",
        "category": "Trend Following",
        "desc": (
            "Dual EMA crossover ({ema_fast}/{ema_slow}) with RSI(14) and volume confirmation on {market}. "
            "Long when fast EMA crosses above slow EMA, RSI > 50, and volume exceeds its 20-bar average. "
            "Short on the reverse. ATR-sized stops and {rr_ratio}:1 targets keep each trade well-defined. "
            "Runs on {tf} bars — fast enough to catch trends, slow enough to filter noise. "
            "Volume filter eliminates false breakouts in thin trading periods."
        ),
        "variants": [
            {"ema_fast": 9,  "ema_slow": 21, "rsi_period": 14, "vol_sma": 20, "rr_ratio": 2.0},
            {"ema_fast": 5,  "ema_slow": 13, "rsi_period": 14, "vol_sma": 20, "rr_ratio": 2.0},
            {"ema_fast": 13, "ema_slow": 34, "rsi_period": 14, "vol_sma": 20, "rr_ratio": 2.0},
        ],
    },
    {
        "engine": "supertrend",
        "category": "Trend Following",
        "desc": (
            "Supertrend({st_period},{st_mult}) trend filter on {market} {tf} bars. "
            "Enters on direction flip: long when price closes above the upper Supertrend band, "
            "short when it closes below the lower band. Stop is set at the Supertrend value. "
            "The ATR-based trailing stop adapts to volatility, keeping trades in longer trends. "
            "Clean and mechanical — no ambiguity about trade direction."
        ),
        "variants": [
            {"st_period": 10, "st_mult": 3.0, "rr_ratio": 2.0},
            {"st_period": 7,  "st_mult": 2.5, "rr_ratio": 2.0},
            {"st_period": 14, "st_mult": 3.5, "rr_ratio": 2.5},
        ],
    },
    {
        "engine": "keltner",
        "category": "Mean Reversion",
        "desc": (
            "Keltner Channel({kc_period},{kc_mult}) mean-reversion on {market} {tf} bars. "
            "Enters long when price closes below the lower Keltner band and targets the middle EMA. "
            "Enters short on touches above the upper band. "
            "Because Keltner bands use ATR (not standard deviation), they are more stable in volatile regimes. "
            "Pairs well with a trend filter to avoid fighting strong directional moves."
        ),
        "variants": [
            {"kc_period": 20, "kc_mult": 2.0, "mode": "reversion", "rr_ratio": 2.0},
            {"kc_period": 14, "kc_mult": 1.5, "mode": "reversion", "rr_ratio": 2.0},
            {"kc_period": 20, "kc_mult": 2.0, "mode": "breakout",  "rr_ratio": 2.0},
        ],
    },
    {
        "engine": "cci",
        "category": "Oscillator",
        "desc": (
            "CCI({cci_period}) oscillator reversal on {market} {tf} bars. "
            "Enters long when CCI crosses back above {oversold} from below, confirming exhaustion of sellers. "
            "Enters short when CCI crosses back below {overbought}. "
            "The Commodity Channel Index measures deviation from the typical price mean — extreme readings "
            "reliably identify overbought/oversold conditions in futures markets."
        ),
        "variants": [
            {"cci_period": 20, "overbought": 100, "oversold": -100, "rr_ratio": 2.0},
            {"cci_period": 14, "overbought": 150, "oversold": -150, "rr_ratio": 2.0},
            {"cci_period": 20, "overbought": 200, "oversold": -200, "rr_ratio": 2.5},
        ],
    },
    {
        "engine": "stochastic",
        "category": "Oscillator",
        "desc": (
            "Stochastic(%K={k_period},%D={d_period}) crossover strategy on {market} {tf} bars. "
            "Enters long when %K crosses above %D while both are below {oversold}, signalling a bullish turn. "
            "Enters short when %K crosses below %D above {overbought}. "
            "The dual-line crossover reduces noise compared to raw %K reversals. "
            "ATR-based stops prevent being stopped out by normal oscillations."
        ),
        "variants": [
            {"k_period": 14, "d_period": 3, "overbought": 80, "oversold": 20, "rr_ratio": 2.0},
            {"k_period": 5,  "d_period": 3, "overbought": 80, "oversold": 20, "rr_ratio": 1.5},
            {"k_period": 21, "d_period": 5, "overbought": 75, "oversold": 25, "rr_ratio": 2.0},
        ],
    },
    {
        "engine": "williams_r",
        "category": "Oscillator",
        "desc": (
            "Williams %R({wr_period}) reversal on {market} {tf} bars. "
            "Signals long when %R recovers from below {oversold} — indicating exhausted short sellers. "
            "Signals short when %R drops back from above {overbought}. "
            "Williams %R is particularly sensitive to price extremes in choppy intraday conditions. "
            "Combined with ATR targets, each trade has a well-defined risk/reward profile."
        ),
        "variants": [
            {"wr_period": 14, "overbought": -20, "oversold": -80, "rr_ratio": 2.0},
            {"wr_period": 9,  "overbought": -15, "oversold": -85, "rr_ratio": 2.0},
            {"wr_period": 21, "overbought": -25, "oversold": -75, "rr_ratio": 2.0},
        ],
    },
    {
        "engine": "mfi",
        "category": "Volume",
        "desc": (
            "Money Flow Index({mfi_period}) reversal on {market} {tf} bars. "
            "MFI combines price and volume to identify overbought/oversold conditions. "
            "Enters long when MFI crosses back above {oversold} — cash is flowing back in. "
            "Enters short on the MFI drop from {overbought}. "
            "Volume weighting makes MFI more reliable than pure price oscillators for futures."
        ),
        "variants": [
            {"mfi_period": 14, "overbought": 80, "oversold": 20, "rr_ratio": 2.0},
            {"mfi_period": 10, "overbought": 75, "oversold": 25, "rr_ratio": 2.0},
            {"mfi_period": 20, "overbought": 80, "oversold": 20, "rr_ratio": 2.5},
        ],
    },
    {
        "engine": "ichimoku",
        "category": "Trend Following",
        "desc": (
            "Ichimoku Cloud TK crossover system on {market} {tf} bars. "
            "Enters long on a Tenkan/Kijun bullish crossover when price is above the cloud (Kumo). "
            "Enters short on the bearish TK crossover below the cloud. "
            "The cloud acts as dynamic support/resistance — only trading with the cloud aligns entries "
            "with the dominant trend and significantly improves trade quality on {market}."
        ),
        "variants": [
            {"conversion": 9, "base": 26, "rr_ratio": 2.0},
            {"conversion": 7, "base": 22, "rr_ratio": 2.0},
        ],
    },
    {
        "engine": "triple_ema",
        "category": "Trend Following",
        "desc": (
            "Triple EMA ({fast}/{mid}/{slow}) alignment system on {market} {tf} bars. "
            "Enters when all three EMAs achieve full alignment: fast > mid > slow for longs, "
            "fast < mid < slow for shorts. Entry is on the first bar of full alignment. "
            "ATR-based stops trail below the mid EMA. "
            "Triple alignment eliminates most choppy counter-trend entries that plague single-EMA strategies."
        ),
        "variants": [
            {"fast": 5,  "mid": 13, "slow": 34, "rr_ratio": 2.0},
            {"fast": 8,  "mid": 21, "slow": 55, "rr_ratio": 2.0},
            {"fast": 3,  "mid": 8,  "slow": 21, "rr_ratio": 1.5},
        ],
    },
    {
        "engine": "donchian",
        "category": "Breakout",
        "desc": (
            "Donchian Channel({dc_period}) breakout with {vol_mult}x volume confirmation on {market}. "
            "Goes long on a close above the {dc_period}-bar high when volume exceeds its average by {vol_mult}x. "
            "Goes short on a close below the {dc_period}-bar low. "
            "Volume requirement ensures breakouts represent genuine institutional participation. "
            "ATR-based {rr_ratio}:1 targets hold positions through normal pullbacks."
        ),
        "variants": [
            {"dc_period": 20, "vol_mult": 1.5, "rr_ratio": 2.0},
            {"dc_period": 10, "vol_mult": 2.0, "rr_ratio": 2.0},
            {"dc_period": 40, "vol_mult": 1.5, "rr_ratio": 2.5},
        ],
    },
    {
        "engine": "atr_channel",
        "category": "Breakout",
        "desc": (
            "ATR Channel breakout on {market} {tf} bars. "
            "EMA({ema_period}) forms the centerline; ATR({atr_period}) × {multiplier} creates the bands. "
            "Enters long when price closes above the upper band for the first time — momentum breakout. "
            "Enters short on close below lower band. Stop is set at the EMA centerline. "
            "ATR-adaptive bands make this strategy self-calibrating to changing volatility regimes."
        ),
        "variants": [
            {"ema_period": 20, "atr_period": 14, "multiplier": 1.5, "rr_ratio": 2.0},
            {"ema_period": 20, "atr_period": 14, "multiplier": 2.0, "rr_ratio": 2.0},
            {"ema_period": 50, "atr_period": 14, "multiplier": 1.5, "rr_ratio": 2.5},
        ],
    },
    {
        "engine": "obv",
        "category": "Volume",
        "desc": (
            "On-Balance Volume divergence strategy on {market} {tf} bars. "
            "Monitors OBV vs. price over a {lookback}-bar window for divergence. "
            "Bullish: price makes a new low but OBV does not — hidden accumulation. "
            "Bearish: price makes a new high but OBV does not — distribution. "
            "OBV divergence is one of the oldest and most robust leading indicators in markets."
        ),
        "variants": [
            {"lookback": 20, "rr_ratio": 2.0},
            {"lookback": 10, "rr_ratio": 2.0},
        ],
    },
    {
        "engine": "elder_ray",
        "category": "Hybrid",
        "desc": (
            "Elder Ray (Bull Power / Bear Power) on {market} {tf} bars. "
            "Uses a {er_period}-period EMA as the baseline; "
            "Bull Power = High - EMA, Bear Power = Low - EMA. "
            "Enters long when Bull Power crosses from negative to positive (bulls are in control). "
            "Enters short when Bear Power crosses from positive to negative. "
            "Developed by Dr. Alexander Elder — combines trend and momentum in one system."
        ),
        "variants": [
            {"er_period": 13, "rr_ratio": 2.0},
            {"er_period": 21, "rr_ratio": 2.0},
        ],
    },
    {
        "engine": "rsi_macd",
        "category": "Hybrid",
        "desc": (
            "RSI + MACD confluence system on {market} {tf} bars. "
            "Requires both: MACD line crossing above signal AND RSI between 40-70 for longs. "
            "Short requires MACD cross below signal AND RSI between 30-60. "
            "The RSI filter prevents buying into extreme overbought conditions. "
            "Dual-confirmation strategies typically have higher win rates at the cost of fewer signals."
        ),
        "variants": [
            {"rsi_period": 14, "macd_fast": 12, "macd_slow": 26, "macd_signal": 9, "rr_ratio": 2.0},
            {"rsi_period": 9,  "macd_fast": 8,  "macd_slow": 21, "macd_signal": 5, "rr_ratio": 2.0},
        ],
    },
    {
        "engine": "bb_squeeze",
        "category": "Breakout",
        "desc": (
            "Bollinger Band Squeeze breakout on {market} {tf} bars. "
            "Detects when BB narrows inside Keltner Channels (squeeze = low volatility compression). "
            "On squeeze release — when BB expands past KC — trades the direction of momentum. "
            "Momentum is measured as price minus its rolling mean (positive = bullish release). "
            "Squeeze plays often produce the highest-velocity moves in any market."
        ),
        "variants": [
            {"bb_period": 20, "bb_std": 2.0, "kc_period": 20, "kc_mult": 1.5, "rr_ratio": 2.0},
            {"bb_period": 20, "bb_std": 2.0, "kc_period": 20, "kc_mult": 1.0, "rr_ratio": 2.5},
        ],
    },
    {
        "engine": "volume_surge",
        "category": "Volume",
        "desc": (
            "Volume surge breakout on {market} {tf} bars. "
            "Triggers when a single bar's volume exceeds {vol_mult}x its {lookback}-bar average — "
            "a signal of institutional market orders hitting the tape. "
            "Direction determined by bar close vs open: bullish bar → long, bearish bar → short. "
            "Volume spikes at key levels often mark the true start of significant moves in futures."
        ),
        "variants": [
            {"vol_mult": 3.0, "lookback": 20, "rr_ratio": 2.0},
            {"vol_mult": 2.5, "lookback": 20, "rr_ratio": 2.0},
        ],
    },
    {
        "engine": "inside_bar",
        "category": "Price Action",
        "desc": (
            "Inside bar breakout strategy on {market} {tf} bars. "
            "An inside bar (range contained within prior bar) signals a pause in momentum. "
            "Entries trigger on the first bar that closes beyond the mother bar's range. "
            "Stop is placed one ATR beyond the entry bar; target is {rr_ratio}x the risk. "
            "Inside bars at key support/resistance levels or after trending moves are highest probability."
        ),
        "variants": [
            {"rr_ratio": 2.0},
            {"rr_ratio": 1.5},
        ],
    },
    {
        "engine": "market_structure",
        "category": "Price Action",
        "desc": (
            "Market structure breakout on {market} {tf} bars. "
            "Identifies Higher Highs / Higher Lows (uptrend) and Lower Lows / Lower Highs (downtrend) "
            "using a {swing_period}-bar swing detection window. "
            "Enters when the market makes a clear structural break — HH + HL for longs, LL + LH for shorts. "
            "Trading with market structure eliminates most false breakouts by requiring structural confirmation."
        ),
        "variants": [
            {"swing_period": 5,  "rr_ratio": 2.0},
            {"swing_period": 10, "rr_ratio": 2.0},
        ],
    },
    {
        "engine": "gap_fill",
        "category": "Mean Reversion",
        "desc": (
            "Gap fill strategy on {market} {tf} bars. "
            "Detects overnight or session gaps where price opens more than {min_gap_pct:.1%} away from prior close. "
            "Statistical edge: gaps fill (price returns to prior close) in majority of cases. "
            "Enters counter to the gap direction; target is the gap fill (prior close); "
            "stop is placed beyond the gap open. Best results on equity index futures."
        ),
        "variants": [
            {"min_gap_pct": 0.002, "rr_ratio": 1.5},
            {"min_gap_pct": 0.003, "rr_ratio": 1.5},
        ],
    },
    {
        "engine": "orderflow_delta",
        "category": "Order Flow",
        "desc": (
            "Pure order flow strategy using CVD delta divergence confirmed by absorption on {market}. "
            "Requires three simultaneous conditions: price at Keltner Channel extreme, "
            "delta divergence (CVD disagrees with price direction), and absorption (high vol, no progress). "
            "This triple confirmation represents institutional activity reversing against retail flow. "
            "The most sophisticated signal generator in the suite — requires active institutional participation."
        ),
        "variants": [
            {"kc_period": 20, "kc_mult": 2.0, "lookback": 10, "vol_threshold": 1.5, "rr_ratio": 2.0},
        ],
    },
    {
        "engine": "absorption_reversal",
        "category": "Order Flow",
        "desc": (
            "Absorption reversal at Bollinger Band extremes on {market} {tf} bars. "
            "Detects bars with high volume ({vol_threshold}x average) but minimal price movement, "
            "placed at the outer Bollinger Band — a signature of institutional absorption. "
            "When large players absorb selling at support (or buying at resistance), "
            "reversals tend to be sharp and fast. Target is the midline BB; stop is just beyond the band."
        ),
        "variants": [
            {"bb_period": 20, "bb_std": 2.0, "vol_threshold": 2.0, "move_threshold": 0.3, "rr_ratio": 2.0},
        ],
    },
    {
        "engine": "trapped_breakout",
        "category": "Order Flow",
        "desc": (
            "Trapped trader breakout on {market} {tf} bars. "
            "Inside bars with high volume ({vol_mult}x average) indicate traders entering within a tight range "
            "who become trapped when price breaks the mother bar's range. "
            "Their forced exits (stop-loss orders) fuel the breakout momentum. "
            "Entry is on the bar that breaks the mother bar high or low. "
            "Stops are tight — just below the inside bar's range."
        ),
        "variants": [
            {"vol_mult": 1.5, "rr_ratio": 2.0},
        ],
    },
    {
        "engine": "tape_momentum",
        "category": "Order Flow",
        "desc": (
            "Tape acceleration + order flow confluence strategy on {market} {tf} bars. "
            "Requires tape speed (fast vol EMA / slow vol EMA) to exceed {speed_threshold}x "
            "AND the composite order flow score to exceed {score_threshold} in magnitude. "
            "High tape speed means market participants are urgently transacting — "
            "aligned with a strong directional order flow score, this identifies institutional momentum entries."
        ),
        "variants": [
            {"speed_threshold": 1.8, "score_threshold": 20, "rr_ratio": 2.0},
        ],
    },
    {
        "engine": "evr_reversal",
        "category": "Order Flow",
        "desc": (
            "Effort vs Result (Wyckoff) reversal on {market} {tf} bars. "
            "Measures the ratio of volume effort to price result — when high effort produces little price movement, "
            "absorption is occurring. Triggered at Bollinger Band extremes where EVR ratio is low. "
            "Wyckoff called this 'effort without result' — a sign large operators are absorbing the bar. "
            "One of the oldest and most battle-tested concepts in technical analysis applied systematically."
        ),
        "variants": [
            {"evr_threshold": -0.5, "bb_period": 20, "rr_ratio": 2.0},
        ],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# Timeframe configurations
# ─────────────────────────────────────────────────────────────────────────────
TIMEFRAME_CONFIGS = [
    {"tf": "5m",  "period": "60d",  "label": "5m/60d"},
    {"tf": "15m", "period": "60d",  "label": "15m/60d"},
    {"tf": "1h",  "period": "730d", "label": "1h/730d"},
]

# Engines that don't work well on 5m (too noisy) or need hourly data
HOURLY_ONLY_ENGINES = {"orb", "ichimoku", "triple_ema", "market_structure"}
SHORT_TF_ONLY = set()


def p(rel):
    return str(BASE_DIR / rel) if rel else None


def build_name(engine, market, tf, params, variant_idx):
    market_short = market.replace("=F", "").replace("=", "")
    engine_display = {
        "bb_cvd": "BB+CVD", "rsi_rev": "RSI REV", "macd": "MACD",
        "ema_cross": "EMA CROSS", "supertrend": "SUPERTREND",
        "keltner": "KELTNER", "cci": "CCI", "stochastic": "STOCHASTIC",
        "williams_r": "WILLIAMS %R", "mfi": "MFI", "ichimoku": "ICHIMOKU",
        "triple_ema": "TRIPLE EMA", "donchian": "DONCHIAN",
        "atr_channel": "ATR CHANNEL", "obv": "OBV DIV",
        "elder_ray": "ELDER RAY", "rsi_macd": "RSI+MACD",
        "bb_squeeze": "BB SQUEEZE", "volume_surge": "VOL SURGE",
        "inside_bar": "INSIDE BAR", "market_structure": "MKT STRUCT",
        "gap_fill": "GAP FILL",
        "orderflow_delta": "OF DELTA", "absorption_reversal": "ABSORPTION",
        "trapped_breakout": "TRAPPED", "tape_momentum": "TAPE MOM",
        "evr_reversal": "EVR REV",
    }.get(engine, engine.upper())
    letter = chr(65 + variant_idx) if variant_idx > 0 else ""
    return f"{engine_display} {market_short} {tf}{letter}"


def build_desc(template_desc, engine, market, params, tf, period):
    market_name = MARKETS[market]["name"]
    d = template_desc.replace("{market}", market_name)
    d = d.replace("{tf}", tf).replace("{period}", period)
    # Replace param placeholders
    for k, v in params.items():
        d = d.replace(f"{{{k}}}", str(v))
    return d


def generate_configs():
    configs = []
    algo_id = 101  # Start after existing 100

    for tmpl in STRATEGY_TEMPLATES:
        engine = tmpl["engine"]
        category = tmpl["category"]
        variants = tmpl["variants"]

        for market, minfo in MARKETS.items():
            tick = minfo["tick"]

            for tf_cfg in TIMEFRAME_CONFIGS:
                tf     = tf_cfg["tf"]
                period = tf_cfg["period"]

                # Skip hourly-only engines on short TFs
                if engine in HOURLY_ONLY_ENGINES and tf != "1h":
                    continue
                # Skip 1h for 5m-only engines
                if engine in SHORT_TF_ONLY and tf == "1h":
                    continue
                # Skip 5m timeframe for bond/note markets (too noisy, low data quality)
                if market in ("ZB=F", "ZN=F") and tf == "5m":
                    continue

                for vi, params in enumerate(variants):
                    if algo_id > 500:
                        break

                    name   = build_name(engine, market, tf, params, vi)
                    desc   = build_desc(tmpl["desc"], engine, market, params, tf, period)
                    csv_fn = f"results/algo_{algo_id:03d}_trades.csv"

                    configs.append({
                        "id": str(algo_id),
                        "name": name,
                        "category": category,
                        "description": desc,
                        "market": market,
                        "tick_value": tick,
                        "timeframe": tf,
                        "period": period,
                        "status": "TESTING",
                        "engine": engine,
                        "params": params,
                        "script": None,
                        "csv": p(csv_fn),
                        "alt_csv": None,
                        "chart": None,
                        "alt_chart": None,
                    })
                    algo_id += 1

    return configs


# ─────────────────────────────────────────────────────────────────────────────
# First 100 configs (existing)
# ─────────────────────────────────────────────────────────────────────────────

def get_live_configs():
    """Returns the original 5 LIVE configs + 15 TESTING + 80 DEV."""
    from algo_configs import ALGO_CONFIGS
    return ALGO_CONFIGS


if __name__ == "__main__":
    new_configs = generate_configs()
    print(f"Generated {len(new_configs)} new algo configs (IDs 101–{100 + len(new_configs)})")

    # Print sample
    for c in new_configs[:3]:
        print(f"  [{c['id']}] {c['name']} ({c['engine']}, {c['market']}, {c['timeframe']})")
    print("  ...")
    print(f"\nTotal configs will be: 100 (existing) + {len(new_configs)} (new) = {100 + len(new_configs)}")
