from __future__ import annotations

from pathlib import Path
import pandas as pd
import yfinance as yf


BASE_DIR = Path(__file__).parent
NT_EXPORT_DIR = BASE_DIR / "ninjatrader_exports"


def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    out = df.copy()
    out.columns = [str(c).lower().strip() for c in out.columns]

    # Accept common NinjaTrader / broker naming variations
    col_map = {
        "date": "datetime",
        "time": "datetime",
        "timestamp": "datetime",
        "open price": "open",
        "high price": "high",
        "low price": "low",
        "close price": "close",
        "vol": "volume",
    }
    out = out.rename(columns={k: v for k, v in col_map.items() if k in out.columns})

    if "datetime" in out.columns:
        out["datetime"] = pd.to_datetime(out["datetime"], errors="coerce", utc=True)
        out = out.dropna(subset=["datetime"]).set_index("datetime")
    elif not isinstance(out.index, pd.DatetimeIndex):
        out.index = pd.to_datetime(out.index, errors="coerce", utc=True)
        out = out[~out.index.isna()]

    needed = ["open", "high", "low", "close", "volume"]
    for c in needed:
        if c not in out.columns:
            if c == "volume":
                out[c] = 0.0
            else:
                return pd.DataFrame()

    out = out[needed].dropna(subset=["open", "high", "low", "close"]).sort_index()
    return out


def fetch_yfinance(market: str, timeframe: str, start: str, end: str) -> pd.DataFrame:
    df = yf.download(
        market,
        start=start,
        end=end,
        interval=timeframe,
        auto_adjust=False,
        progress=False,
    )
    out = normalize_ohlcv(df)
    if out.empty and timeframe != "1d":
        df = yf.download(
            market,
            start=start,
            end=end,
            interval="1d",
            auto_adjust=False,
            progress=False,
        )
        out = normalize_ohlcv(df)
    return out


def _nt_candidates(market: str, timeframe: str) -> list[Path]:
    mk = market.replace("=", "").replace("-", "").replace("/", "").lower()
    tf = timeframe.lower()
    cands = [
        NT_EXPORT_DIR / f"{mk}_{tf}.csv",
        NT_EXPORT_DIR / f"{market}_{timeframe}.csv",
        NT_EXPORT_DIR / f"{market}.csv",
    ]
    existing = [p for p in cands if p.exists()]
    if existing:
        return existing
    # fallback: latest csv in export dir
    if NT_EXPORT_DIR.exists():
        all_csv = sorted(NT_EXPORT_DIR.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
        return all_csv[:1]
    return []


def fetch_ninjatrader_csv(market: str, timeframe: str, start: str, end: str, explicit_file: str | None = None) -> pd.DataFrame:
    candidates = [Path(explicit_file)] if explicit_file else _nt_candidates(market, timeframe)
    for p in candidates:
        if not p.exists():
            continue
        try:
            raw = pd.read_csv(p)
            df = normalize_ohlcv(raw)
            if df.empty:
                continue
            s = pd.to_datetime(start, utc=True)
            e = pd.to_datetime(end, utc=True)
            df = df[(df.index >= s) & (df.index <= e)]
            if not df.empty:
                return df
        except Exception:
            continue
    return pd.DataFrame()


def fetch_market_data(
    source: str,
    market: str,
    timeframe: str,
    start: str,
    end: str,
    nt_file: str | None = None,
) -> pd.DataFrame:
    src = str(source or "yfinance").lower()
    if src == "ninjatrader":
        df = fetch_ninjatrader_csv(market, timeframe, start, end, explicit_file=nt_file)
        if not df.empty:
            return df
        # fallback so user can still run while NT export is missing
        return fetch_yfinance(market, timeframe, start, end)
    return fetch_yfinance(market, timeframe, start, end)

