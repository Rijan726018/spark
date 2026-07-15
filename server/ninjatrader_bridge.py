"""
NinjaTrader Data Bridge
=======================
Receives live market data from NinjaTrader via multiple channels:

1. TCP SERVER mode (default, port 9090):
   NT "Data Feeder 8" or custom NinjaScript indicator connects here and pushes data.
   Line-delimited text protocol (UTF-8):
     BAR|<symbol>|<open>|<high>|<low>|<close>|<volume>|<timestamp_unix>
     TICK|<symbol>|<price>|<volume>|<bid>|<ask>|<timestamp_unix>
     EXEC|<algo_id>|<symbol>|<side>|<price>|<qty>|<timestamp_unix>
     TRADE|<symbol>|<side>|<price>|<qty>|<timestamp_unix>

2. TCP CLIENT mode (optional):
   Connect to NT's built-in broadcast server (configurable host:port).
   Same line protocol expected.

3. Named Pipe (NT ATI):
   Reads from \\\\.\\pipe\\NinjaTrader\\MarketData on Windows.
   Same line protocol.

4. CSV Watcher:
   Watches ninjatrader_exports/ folder for new/modified CSV files.
   Expected CSV columns (flexible): Time, Open, High, Low, Close, Volume
"""

import asyncio
import logging
import os
import sys
import time
import threading
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Dict, Any

logger = logging.getLogger("nt_bridge")

# ─── Normalise symbol names ────────────────────────────────────────────────────

_SYMBOL_MAP = {
    "ES": "ES", "NQ": "NQ", "MES": "MES", "MNQ": "MNQ",
    "GC": "GC", "CL": "CL", "ZB": "ZB", "YM": "YM",
    "RTY": "RTY", "M2K": "M2K",
}

def normalise_symbol(raw: str) -> str:
    """'NQ 03-25' → 'NQ',  'ES=F' → 'ES',  'MNQ JUN25' → 'MNQ'."""
    if not raw:
        return "UNKNOWN"
    # Strip futures contract suffix  e.g. " 03-25", " JUN25", " SEP24"
    parts = raw.strip().upper().split()
    base = parts[0].rstrip("=")
    return _SYMBOL_MAP.get(base, base)


# ─── Bar / Tick / Execution data classes ──────────────────────────────────────

class Bar:
    __slots__ = ("symbol", "time", "open", "high", "low", "close", "volume", "tf")
    def __init__(self, symbol, time_, open_, high, low, close, volume, tf="5m"):
        self.symbol = symbol
        self.time   = int(time_)
        self.open   = float(open_)
        self.high   = float(high)
        self.low    = float(low)
        self.close  = float(close)
        self.volume = int(float(volume))
        self.tf     = tf

    def to_dict(self):
        return {
            "type":   "bar",
            "symbol": self.symbol,
            "tf":     self.tf,
            "bar": {
                "time":   self.time,
                "open":   self.open,
                "high":   self.high,
                "low":    self.low,
                "close":  self.close,
                "volume": self.volume,
            }
        }


class Tick:
    __slots__ = ("symbol", "price", "volume", "bid", "ask", "time")
    def __init__(self, symbol, price, volume, bid, ask, time_):
        self.symbol = symbol
        self.price  = float(price)
        self.volume = int(float(volume))
        self.bid    = float(bid) if bid else 0.0
        self.ask    = float(ask) if ask else 0.0
        self.time   = int(time_)

    def to_dict(self):
        return {
            "type":   "tick",
            "symbol": self.symbol,
            "tick": {
                "time":   self.time,
                "price":  self.price,
                "volume": self.volume,
                "bid":    self.bid,
                "ask":    self.ask,
            }
        }


class Execution:
    __slots__ = ("algo_id", "symbol", "side", "price", "qty", "time", "stop", "target")
    def __init__(self, algo_id, symbol, side, price, qty, time_, stop=None, target=None):
        self.algo_id = str(algo_id)
        self.symbol  = symbol
        self.side    = side.upper()   # "BUY" or "SELL"
        self.price   = float(price)
        self.qty     = int(float(qty))
        self.time    = int(time_)
        self.stop    = float(stop)   if stop   else None
        self.target  = float(target) if target else None

    def to_dict(self):
        d = {
            "type":    "execution",
            "algo_id": self.algo_id,
            "symbol":  self.symbol,
            "side":    self.side,
            "price":   self.price,
            "qty":     self.qty,
            "time":    self.time,
        }
        if self.stop is not None:   d["stop"]   = self.stop
        if self.target is not None: d["target"] = self.target
        return d


# ─── Line Parser ──────────────────────────────────────────────────────────────

def parse_line(line: str):
    """Parse a pipe-delimited NT data line into a Bar/Tick/Execution or None."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    parts = line.split("|")
    msg_type = parts[0].upper()

    try:
        if msg_type == "BAR" and len(parts) >= 8:
            sym = normalise_symbol(parts[1])
            return Bar(sym, parts[7], parts[2], parts[3], parts[4], parts[5], parts[6])

        elif msg_type == "TICK" and len(parts) >= 7:
            sym = normalise_symbol(parts[1])
            bid = parts[4] if len(parts) > 4 else 0
            ask = parts[5] if len(parts) > 5 else 0
            ts  = parts[6] if len(parts) > 6 else int(time.time())
            return Tick(sym, parts[2], parts[3], bid, ask, ts)

        elif msg_type in ("EXEC", "TRADE") and len(parts) >= 6:
            if msg_type == "EXEC" and len(parts) >= 7:
                # EXEC|algo_id|symbol|side|price|qty|timestamp
                algo_id = parts[1]
                sym     = normalise_symbol(parts[2])
                side    = parts[3]
                price   = parts[4]
                qty     = parts[5]
                ts      = parts[6]
            else:
                # TRADE|symbol|side|price|qty|timestamp
                algo_id = "unknown"
                sym     = normalise_symbol(parts[1])
                side    = parts[2]
                price   = parts[3]
                qty     = parts[4]
                ts      = parts[5]
            return Execution(algo_id, sym, side, price, qty, ts)

    except (IndexError, ValueError) as e:
        logger.debug("parse_line error: %s  line=%r", e, line)

    return None


# ─── Main Bridge Class ─────────────────────────────────────────────────────────

class NinjaTraderBridge:
    """
    Central bridge that aggregates data from:
    - TCP server (NT indicator connects IN to us)
    - TCP client (we connect OUT to NT broadcast)
    - Windows named pipe (NT ATI)
    - CSV file watcher (ninjatrader_exports/)

    Usage:
        bridge = NinjaTraderBridge(exports_dir="ninjatrader_exports")
        bridge.add_callback(my_async_handler)
        await bridge.start()
    """

    MAX_BARS_PER_SYMBOL = 2000   # ring buffer size per symbol

    def __init__(
        self,
        exports_dir: str = "ninjatrader_exports",
        tcp_server_port: int = 9090,
        tcp_client_host: Optional[str] = None,
        tcp_client_port: int = 9091,
        pipe_name: str = r"\\.\pipe\NinjaTrader\MarketData",
        enable_pipe: bool = True,
        enable_csv: bool = True,
    ):
        self.exports_dir      = Path(exports_dir)
        self.tcp_server_port  = tcp_server_port
        self.tcp_client_host  = tcp_client_host
        self.tcp_client_port  = tcp_client_port
        self.pipe_name        = pipe_name
        self.enable_pipe      = enable_pipe
        self.enable_csv       = enable_csv

        # Per-symbol bar history (newest = rightmost)
        self._bars:  Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.MAX_BARS_PER_SYMBOL))
        self._ticks: Dict[str, dict]  = {}      # last tick per symbol

        self._callbacks: List[Callable] = []
        self._tasks: List[asyncio.Task] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Track CSV mtimes so we only re-read changed files
        self._csv_mtimes: Dict[str, float] = {}

        # Connection counts for status reporting
        self.tcp_server_connections = 0
        self.pipe_connected         = False
        self.client_connected       = False

    # ── Callback management ────────────────────────────────────────────────────

    def add_callback(self, fn: Callable):
        """Register an async function(data_dict) to be called on each update."""
        self._callbacks.append(fn)

    async def _emit(self, obj):
        """Fire all registered callbacks with the serialised object."""
        if obj is None:
            return
        data = obj.to_dict() if hasattr(obj, "to_dict") else obj
        for cb in self._callbacks:
            try:
                await cb(data)
            except Exception as e:
                logger.warning("Callback error: %s", e)

        # Update internal bar cache
        if isinstance(obj, Bar):
            self._bars[obj.symbol].append({
                "time":   obj.time,
                "open":   obj.open,
                "high":   obj.high,
                "low":    obj.low,
                "close":  obj.close,
                "volume": obj.volume,
            })
        elif isinstance(obj, Tick):
            self._ticks[obj.symbol] = obj.to_dict()["tick"]

    # ── Public API ─────────────────────────────────────────────────────────────

    def get_last_bars(self, symbol: str, limit: int = 500) -> List[dict]:
        """Return up to `limit` most-recent bars for a symbol."""
        sym = normalise_symbol(symbol)
        bars = list(self._bars[sym])
        return bars[-limit:] if len(bars) > limit else bars

    def get_all_symbols(self) -> List[str]:
        return list(self._bars.keys())

    def get_status(self) -> dict:
        return {
            "tcp_server_port":        self.tcp_server_port,
            "tcp_server_connections": self.tcp_server_connections,
            "pipe_connected":         self.pipe_connected,
            "client_connected":       self.client_connected,
            "symbols":                self.get_all_symbols(),
            "bar_counts":             {s: len(v) for s, v in self._bars.items()},
        }

    # ── Start / Stop ───────────────────────────────────────────────────────────

    async def start(self):
        """Start all enabled data channels."""
        self._loop = asyncio.get_running_loop()
        logger.info("NinjaTrader bridge starting...")

        # Always start TCP server
        t = asyncio.create_task(self._run_tcp_server())
        self._tasks.append(t)

        # Optionally start TCP client
        if self.tcp_client_host:
            t = asyncio.create_task(self._run_tcp_client())
            self._tasks.append(t)

        # Named pipe (Windows only)
        if self.enable_pipe and sys.platform == "win32":
            t = asyncio.create_task(self._run_pipe_reader())
            self._tasks.append(t)

        # CSV watcher
        if self.enable_csv:
            t = asyncio.create_task(self._run_csv_watcher())
            self._tasks.append(t)

        logger.info("NinjaTrader bridge started. TCP server on port %d", self.tcp_server_port)

    async def stop(self):
        """Cancel all running tasks."""
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("NinjaTrader bridge stopped.")

    # ── Channel 1: TCP Server ──────────────────────────────────────────────────

    async def _handle_tcp_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info("peername")
        logger.info("NT TCP client connected from %s", peer)
        self.tcp_server_connections += 1
        buf = b""
        try:
            while True:
                chunk = await asyncio.wait_for(reader.read(4096), timeout=60)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    obj = parse_line(line.decode("utf-8", errors="replace"))
                    if obj:
                        await self._emit(obj)
        except (asyncio.TimeoutError, asyncio.IncompleteReadError, ConnectionResetError):
            pass
        except Exception as e:
            logger.warning("TCP client handler error: %s", e)
        finally:
            self.tcp_server_connections = max(0, self.tcp_server_connections - 1)
            logger.info("NT TCP client disconnected from %s", peer)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _run_tcp_server(self):
        retry_delay = 2
        while True:
            try:
                server = await asyncio.start_server(
                    self._handle_tcp_client,
                    "0.0.0.0",
                    self.tcp_server_port,
                    reuse_address=True,
                )
                addrs = [s.getsockname() for s in server.sockets]
                logger.info("NT TCP server listening on %s", addrs)
                async with server:
                    await server.serve_forever()
            except asyncio.CancelledError:
                return
            except OSError as e:
                logger.error("TCP server bind failed: %s — retrying in %ds", e, retry_delay)
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)

    # ── Channel 2: TCP Client ─────────────────────────────────────────────────

    async def _run_tcp_client(self):
        retry_delay = 5
        while True:
            try:
                logger.info("Connecting to NT broadcast server %s:%d ...",
                            self.tcp_client_host, self.tcp_client_port)
                reader, writer = await asyncio.open_connection(
                    self.tcp_client_host, self.tcp_client_port
                )
                self.client_connected = True
                logger.info("Connected to NT broadcast server.")
                buf = b""
                while True:
                    chunk = await asyncio.wait_for(reader.read(4096), timeout=30)
                    if not chunk:
                        break
                    buf += chunk
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        obj = parse_line(line.decode("utf-8", errors="replace"))
                        if obj:
                            await self._emit(obj)
            except asyncio.CancelledError:
                return
            except (ConnectionRefusedError, OSError, asyncio.TimeoutError) as e:
                self.client_connected = False
                logger.info("NT broadcast client error: %s — retry in %ds", e, retry_delay)
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)
            except Exception as e:
                self.client_connected = False
                logger.warning("NT broadcast client unexpected error: %s", e)
                await asyncio.sleep(retry_delay)

    # ── Channel 3: Named Pipe ─────────────────────────────────────────────────

    async def _run_pipe_reader(self):
        """Read NT ATI named pipe in a background thread to avoid blocking the event loop."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._pipe_reader_thread)

    def _pipe_reader_thread(self):
        import time as _time
        retry_delay = 5
        while True:
            try:
                logger.info("Opening named pipe: %s", self.pipe_name)
                with open(self.pipe_name, "rb", buffering=0) as pipe:
                    self.pipe_connected = True
                    logger.info("Named pipe connected.")
                    buf = b""
                    while True:
                        chunk = pipe.read(4096)
                        if not chunk:
                            _time.sleep(0.01)
                            continue
                        buf += chunk
                        while b"\n" in buf:
                            line, buf = buf.split(b"\n", 1)
                            obj = parse_line(line.decode("utf-8", errors="replace"))
                            if obj:
                                # Schedule emit on the event loop from this thread
                                if self._loop and not self._loop.is_closed():
                                    asyncio.run_coroutine_threadsafe(self._emit(obj), self._loop)
            except FileNotFoundError:
                self.pipe_connected = False
                logger.debug("Named pipe not found (NT not running?). Retry in %ds", retry_delay)
                _time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)
            except (OSError, IOError) as e:
                self.pipe_connected = False
                logger.info("Named pipe error: %s — retry in %ds", e, retry_delay)
                _time.sleep(retry_delay)
            except Exception as e:
                self.pipe_connected = False
                logger.warning("Named pipe thread error: %s", e)
                _time.sleep(retry_delay)

    # ── Channel 4: CSV Watcher ────────────────────────────────────────────────

    async def _run_csv_watcher(self):
        """
        Poll ninjatrader_exports/ every 5 seconds.
        When a CSV file is new or modified, parse it and emit bars.
        """
        import csv as _csv

        self.exports_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Watching CSV export dir: %s", self.exports_dir.resolve())

        while True:
            try:
                csv_files = list(self.exports_dir.glob("*.csv"))
                for fpath in csv_files:
                    try:
                        mtime = fpath.stat().st_mtime
                        key   = str(fpath)
                        if self._csv_mtimes.get(key) == mtime:
                            continue   # unchanged
                        self._csv_mtimes[key] = mtime
                        logger.info("CSV changed, loading: %s", fpath.name)
                        await self._load_csv(fpath)
                    except Exception as e:
                        logger.warning("CSV load error (%s): %s", fpath.name, e)
            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.warning("CSV watcher error: %s", e)

            await asyncio.sleep(5)

    async def _load_csv(self, fpath: Path):
        """
        Load a NinjaTrader-exported CSV file and emit bars.
        Supports multiple column name conventions.
        """
        import csv as _csv

        # Derive symbol from filename, e.g. "NQ_5m_backtest.csv" → "NQ"
        sym_raw = fpath.stem.split("_")[0].upper()
        symbol  = normalise_symbol(sym_raw)

        bars_emitted = 0
        with open(fpath, "r", encoding="utf-8-sig", newline="") as f:
            reader = _csv.DictReader(f)
            if reader.fieldnames is None:
                return

            # Normalise column names to lowercase
            field_map = {h.strip().lower(): h for h in (reader.fieldnames or [])}

            def get_col(*names):
                for n in names:
                    if n.lower() in field_map:
                        return field_map[n.lower()]
                return None

            col_time   = get_col("time", "datetime", "date", "timestamp")
            col_open   = get_col("open")
            col_high   = get_col("high")
            col_low    = get_col("low")
            col_close  = get_col("close", "last")
            col_volume = get_col("volume", "vol")

            if not (col_time and col_open and col_high and col_low and col_close):
                logger.warning("CSV %s missing required columns. Fields: %s",
                               fpath.name, reader.fieldnames)
                return

            for row in reader:
                try:
                    # Parse timestamp — handle many NT formats
                    raw_ts = row[col_time].strip()
                    ts = _parse_timestamp(raw_ts)
                    if ts is None:
                        continue

                    vol = float(row[col_volume]) if col_volume and row.get(col_volume) else 0
                    bar = Bar(
                        symbol,
                        ts,
                        row[col_open],
                        row[col_high],
                        row[col_low],
                        row[col_close],
                        vol,
                    )
                    await self._emit(bar)
                    bars_emitted += 1
                except Exception:
                    continue

        logger.info("Loaded %d bars from %s (symbol=%s)", bars_emitted, fpath.name, symbol)


def _parse_timestamp(raw: str) -> Optional[int]:
    """Try multiple date/timestamp formats. Returns Unix timestamp int or None."""
    # Already a unix timestamp
    if raw.isdigit():
        return int(raw)

    fmts = [
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
    ]
    for fmt in fmts:
        try:
            dt = datetime.strptime(raw, fmt)
            return int(dt.timestamp())
        except ValueError:
            continue

    logger.debug("Could not parse timestamp: %r", raw)
    return None


# ─── Standalone test / demo ───────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    async def demo_callback(data):
        print(f"[DEMO] {data}")

    async def main():
        bridge = NinjaTraderBridge(exports_dir="../ninjatrader_exports")
        bridge.add_callback(demo_callback)
        await bridge.start()
        print("Bridge running. Send lines to localhost:9090 or drop CSVs in ninjatrader_exports/")
        print("Ctrl+C to stop.")
        try:
            await asyncio.Event().wait()  # block forever
        except KeyboardInterrupt:
            pass
        await bridge.stop()

    asyncio.run(main())
