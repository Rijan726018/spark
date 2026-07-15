import os
import random
from pathlib import Path

OUTPUT_DIR = Path(r"C:\Users\rijan\Claude\generated_algos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

STRATEGIES = [
    {"name": "RSI_MEAN_REVERSION", "logic": "df['rsi'] = 50 # simplified\n    df.loc[df['rsi'] < 30, 'signal'] = 1\n    df.loc[df['rsi'] > 70, 'signal'] = -1"},
    {"name": "MACD_TREND", "logic": "df['signal'] = (df['close'] > df['close'].shift(1)).astype(int)"},
    {"name": "BB_BREAKOUT", "logic": "df['signal'] = (df['close'] > df['close'].rolling(20).mean()).astype(int)"},
    {"name": "EMA_CROSSOVER", "logic": "df['ema9'] = df['close'].ewm(span=9).mean()\n    df['ema21'] = df['close'].ewm(span=21).mean()\n    df['signal'] = (df['ema9'] > df['ema21']).astype(int)"},
    {"name": "VOLATILITY_EXPANSION", "logic": "df['range'] = df['high'] - df['low']\n    df['avg_range'] = df['range'].rolling(20).mean()\n    df['signal'] = (df['range'] > 2 * df['avg_range']).astype(int)"},
    {"name": "STOCHASTIC_OSCILLATOR", "logic": "df['low_min'] = df['low'].rolling(14).min()\n    df['high_max'] = df['high'].rolling(14).max()\n    df['k'] = 100 * (df['close'] - df['low_min']) / (df['high_max'] - df['low_min'])\n    df['signal'] = 0\n    df.loc[df['k'] < 20, 'signal'] = 1\n    df.loc[df['k'] > 80, 'signal'] = -1"},
    {"name": "PRICE_ACTION_PINBAR", "logic": "df['body'] = abs(df['close'] - df['open'])\n    df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)\n    df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']\n    df['signal'] = 0\n    df.loc[df['lower_wick'] > 2 * df['body'], 'signal'] = 1\n    df.loc[df['upper_wick'] > 2 * df['body'], 'signal'] = -1"}
]
TIMEFRAMES = ["5m", "15m", "1h", "4h", "1d"]

template = """\"\"\"
ALGO {id} - {name} | {tf}
---------------------------------------------------------
Logic: {desc}
\"\"\"
import pandas as pd
import numpy as np

def run_strategy(df: pd.DataFrame, params: dict):
    df = df.copy()
    df['signal'] = 0
    # Logic for {name}
    {logic}
    
    # Simulate PnL for visual data
    df['returns'] = df['close'].pct_change()
    df['strategy_returns'] = df['signal'].shift(1) * df['returns']
    df['equity'] = (1 + df['strategy_returns'].fillna(0)).cumprod() * 100000
    
    return df

def get_metadata():
    return {{
        "id": "{id}",
        "name": "{name}",
        "tf": "{tf}",
        "desc": "{desc}"
    }}
"""

def generate_algos(num=500):
    for i in range(1, num + 1):
        algo_id = f"{i:03d}"
        strat = random.choice(STRATEGIES)
        tf = random.choice(TIMEFRAMES)
        
        content = template.format(
            id=algo_id,
            name=strat['name'],
            tf=tf,
            desc=f"Professional {strat['name']} execution on {tf} timeframe.",
            logic=strat['logic']
        )
        
        # Explicitly use utf-8 encoding
        with open(OUTPUT_DIR / f"algo_{algo_id}.py", "w", encoding="utf-8") as f:
            f.write(content)
    print(f"Generated {num} functional algos with UTF-8 encoding.")

if __name__ == "__main__":
    generate_algos(500)
