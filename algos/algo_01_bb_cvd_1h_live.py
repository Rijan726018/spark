"""
ALGO 01 — Bollinger Band + CVD Divergence | ES Futures | 1H LIVE
──────────────────────────────────────────────────────────────
Logic:
  Long  : price at/below lower BB + bullish CVD divergence
  Short : price at/above upper BB + bearish CVD divergence

Safety:
  LIVE_TRADING_ENABLED: If False, prints 'SIMULATED ORDER' to console.
  If True, sends order to NinjaTraderClient.
"""

import sys
import os
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.indicators import bollinger_bands, cumulative_volume_delta, detect_cvd_divergence
from server.broker import NinjaTraderClient

# ── Config ────────────────────────────────────────────────────────────────────
SYMBOL = "ES=F"
INTERVAL = "1h"
PERIOD = "730d"  # 1H allows much longer history on Yahoo
BB_PERIOD = 20
BB_STD = 2.0
CVD_LOOKBACK = 5

# CRITICAL SAFETY FLAG
LIVE_TRADING_ENABLED = False 

class CVDAlgoLive:
    def __init__(self, broker_client: NinjaTraderClient):
        self.broker = broker_client
        self.instrument = "ES"
        self.qty = 1

    async def run_tick(self):
        """Main execution loop for the strategy."""
        print(f"[{datetime.now()}] Refreshing {SYMBOL} {INTERVAL} data...")
        
        try:
            df = yf.download(SYMBOL, period=PERIOD, interval=INTERVAL, auto_adjust=True, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna()
            
            # Build indicators
            bb = bollinger_bands(df["Close"], BB_PERIOD, BB_STD)
            df = pd.concat([df, bb], axis=1)
            df["CVD"] = cumulative_volume_delta(df["High"], df["Low"], df["Close"], df["Volume"])
            df["signal"] = detect_cvd_divergence(df, CVD_LOOKBACK)
            
            last_signal = df["signal"].iloc[-1]
            last_price = df["Close"].iloc[-1]
            
            if last_signal == 1:
                await self.execute_trade("BUY")
            elif last_signal == -1:
                await self.execute_trade("SELL")
            else:
                print(f"  No signal. Current Price: {last_price}")
                
        except Exception as e:
            print(f"Error in strategy loop: {e}")

    async def execute_trade(self, action: str):
        if not LIVE_TRADING_ENABLED:
            print(f">>> SIMULATED ORDER: {action} {self.qty} {self.instrument} @ MARKET")
            return

        print(f">>> LIVE ORDER TRIGGERED: {action} {self.qty} {self.instrument}")
        res = await self.broker.place_order(self.instrument, action, self.qty)
        print(f"Broker Response: {res}")

def get_metadata():
    return {
        "id": "001",
        "name": "BB + CVD DIVERGENCE (LIVE)",
        "tf": "1H",
        "desc": "CVD Divergence at BB edges for ES Futures. Integrated with NinjaTrader Client."
    }

# Mocking run_strategy for the dashboard backtester
def run_strategy(df: pd.DataFrame, params: dict):
    df = df.copy()
    bb = bollinger_bands(df["close"], BB_PERIOD, BB_STD)
    df["BB_upper"] = bb["BB_upper"]
    df["BB_lower"] = bb["BB_lower"]
    df["CVD"] = cumulative_volume_delta(df["high"], df["low"], df["close"], df["volume"])
    
    # Simple backtest signal
    df["signal"] = 0
    df.loc[(df["close"] <= df["BB_lower"]), "signal"] = 1
    df.loc[(df["close"] >= df["BB_upper"]), "signal"] = -1
    
    df['returns'] = df['close'].pct_change()
    df['strategy_returns'] = df['signal'].shift(1) * df['returns']
    df['equity'] = (1 + df['strategy_returns'].fillna(0)).cumprod() * 100000
    return df

if __name__ == "__main__":
    import asyncio
    client = NinjaTraderClient()
    algo = CVDAlgoLive(client)
    asyncio.run(client.connect())
    asyncio.run(algo.run_tick())
