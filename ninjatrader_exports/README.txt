NinjaTrader Data Drop Zone
==========================

Put your NinjaTrader-exported OHLCV CSV files in this folder to drive backtests
from actual NT data.

Accepted filename patterns:
1) <market>_<timeframe>.csv       (preferred)
   Example: ESF_5m.csv, NQF_1h.csv
2) <market>.csv
   Example: ES=F.csv
3) Any CSV (latest file fallback)

Accepted columns (case-insensitive):
- datetime (or date / time / timestamp)
- open
- high
- low
- close
- volume

Also accepted aliases:
- open price, high price, low price, close price
- vol

How to use in GUI:
1) Select "NinjaTrader Export" in Data Source.
2) Pick your date range.
3) Run Backtest.

If no NT file is found, the system automatically falls back to Yahoo Finance
so the platform keeps running.
