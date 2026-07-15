"""
Live Trader — executes algorithm signals in real-time via IB.

Each LiveTrader runs one algo config in a background daemon thread. Every 60
seconds it downloads fresh OHLCV bars (yfinance), computes the strategy signal,
and places a bracket order through the IBBroker singleton when a new signal
fires and no position is already open.

Usage:
    from engines.live_trader import start_algo, stop_algo, get_all_status

    ok, msg = start_algo("007", paper=True, sessions=["ny", "ny_open"])
    statuses = get_all_status()
    ok, msg = stop_algo("007")
"""

from __future__ import annotations

import csv
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from engines.broker import get_broker, BROKER_STATE
from engines.session import is_in_any_session
from engines.runner import run_strategy_on_df, _get_data

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RESULTS_DIR          = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TICK_INTERVAL_SECONDS = 60  # main loop cadence

# ---------------------------------------------------------------------------
# Module-level registry
# ---------------------------------------------------------------------------
LIVE_TRADERS: dict[str, "LiveTrader"] = {}
_registry_lock = threading.Lock()


# ---------------------------------------------------------------------------
# LiveTrader
# ---------------------------------------------------------------------------

class LiveTrader:
    """
    Background trading loop for a single algo config.

    The loop runs every 60 seconds and:
    1. Checks whether the current time is within allowed sessions (if set).
    2. Downloads the latest OHLCV bars via _get_data from engines.runner.
    3. Runs run_strategy_on_df to produce signal / target / stop columns.
    4. If the last bar has a non-zero signal and no position is open, places
       a bracket order via IBBroker.
    5. Logs every bar + outcome to results/live_{algo_id}.csv.
    6. Handles exceptions gracefully — continues looping on error.
    """

    def __init__(
        self,
        algo_config: dict,
        paper: bool = True,
        sessions: Optional[list[str]] = None,
    ) -> None:
        """
        Args:
            algo_config: A single entry from ALGO_CONFIGS.
            paper:       True = paper trading (port 7497), False = live.
            sessions:    Optional list of session keys to restrict trading hours,
                         e.g. ["ny", "london"]. None means trade at any time.
        """
        self._config         = algo_config
        self._paper          = paper
        self._session_filter = sessions or []

        self._algo_id   = str(algo_config.get("id",     "unknown"))
        self._algo_name = str(algo_config.get("name",   "UNKNOWN"))
        self._market    = str(algo_config.get("market", "ES=F"))
        self._engine    = str(algo_config.get("engine", ""))
        self._params    = dict(algo_config.get("params", {}))
        self._timeframe = str(algo_config.get("timeframe", "1h"))
        self._period    = str(algo_config.get("period",    "5d"))
        self._tick_val  = float(algo_config.get("tick_value", 50.0))
        self._qty       = int(algo_config.get("qty", 1))

        # Threading
        self._thread:     Optional[threading.Thread] = None
        self._stop_event  = threading.Event()
        self._state_lock  = threading.Lock()

        # Runtime state (protected by _state_lock)
        self._running           = False
        self._started_at:       Optional[str] = None
        self._trades_today      = 0
        self._pnl_today         = 0.0
        self._last_signal       = 0
        self._last_signal_time: Optional[str] = None
        self._bars_processed    = 0
        self._error             = ""

        # CSV log
        self._log_path        = RESULTS_DIR / f"live_{self._algo_id}.csv"
        self._csv_header_done = False

    # ------------------------------------------------------------------
    # Public control interface
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the background trading loop in a daemon thread."""
        with self._state_lock:
            if self._running:
                logger.warning("LiveTrader[%s] is already running.", self._algo_id)
                return
            self._stop_event.clear()
            self._running    = True
            self._started_at = datetime.now(tz=timezone.utc).isoformat()

        self._thread = threading.Thread(
            target=self._loop,
            name=f"LiveTrader-{self._algo_id}",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            "LiveTrader[%s] started (%s, sessions=%s).",
            self._algo_id,
            "paper" if self._paper else "LIVE",
            self._session_filter or "all",
        )

    def stop(self) -> None:
        """Signal the loop to stop and wait up to 5 s for the thread to join."""
        logger.info("LiveTrader[%s] stop requested.", self._algo_id)
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        with self._state_lock:
            self._running = False
        logger.info("LiveTrader[%s] stopped.", self._algo_id)

    def is_running(self) -> bool:
        """Return True if the background loop is active."""
        with self._state_lock:
            return self._running

    def get_status(self) -> dict:
        """
        Return a snapshot of the trader's current runtime state.

        Keys:
            running, algo_id, algo_name, market, engine,
            session_filter, trades_today, pnl_today,
            last_signal_time, last_signal, bars_processed,
            error, started_at
        """
        with self._state_lock:
            return {
                "running":          self._running,
                "algo_id":          self._algo_id,
                "algo_name":        self._algo_name,
                "market":           self._market,
                "engine":           self._engine,
                "session_filter":   list(self._session_filter),
                "trades_today":     self._trades_today,
                "pnl_today":        round(self._pnl_today, 2),
                "last_signal_time": self._last_signal_time,
                "last_signal":      self._last_signal,
                "bars_processed":   self._bars_processed,
                "error":            self._error,
                "started_at":       self._started_at,
            }

    # ------------------------------------------------------------------
    # Internal loop
    # ------------------------------------------------------------------

    def _loop(self) -> None:
        """Main execution loop — runs until _stop_event is set."""
        logger.info("LiveTrader[%s] loop started.", self._algo_id)

        while not self._stop_event.is_set():
            try:
                self._tick()
            except Exception as exc:
                logger.exception(
                    "LiveTrader[%s] unhandled error in tick: %s", self._algo_id, exc
                )
                with self._state_lock:
                    self._error = str(exc)

            # Sleep for the interval, but wake immediately if stop is requested
            self._stop_event.wait(timeout=TICK_INTERVAL_SECONDS)

        with self._state_lock:
            self._running = False
        logger.info("LiveTrader[%s] loop exited.", self._algo_id)

    def _tick(self) -> None:
        """Execute one tick: session check → data → signal → order → log."""

        # 1. Session gate
        if self._session_filter and not is_in_any_session(self._session_filter):
            logger.debug(
                "LiveTrader[%s] outside sessions %s — skipping.",
                self._algo_id, self._session_filter,
            )
            return

        # 2. Download latest bars
        df = _get_data(self._market, self._timeframe, self._period)
        if df is None or df.empty:
            logger.warning(
                "LiveTrader[%s] no data returned for %s.", self._algo_id, self._market
            )
            with self._state_lock:
                self._error = f"No data for {self._market}"
            return

        # 3. Run strategy
        try:
            df = run_strategy_on_df(df, self._engine, self._params)
        except Exception as exc:
            logger.error(
                "LiveTrader[%s] strategy error: %s", self._algo_id, exc
            )
            with self._state_lock:
                self._error = f"Strategy error: {exc}"
            return

        if df.empty or "signal" not in df.columns:
            with self._state_lock:
                self._error = "Strategy returned no signal column."
            return

        # 4. Read last bar
        latest   = df.iloc[-1]
        signal   = int(latest.get("signal", 0))
        bar_time = df.index[-1]
        if hasattr(bar_time, "to_pydatetime"):
            bar_time = bar_time.to_pydatetime()

        close  = float(latest.get("Close",  0.0))
        target = float(latest.get("target", close))
        stop   = float(latest.get("stop",   close))

        with self._state_lock:
            self._last_signal      = signal
            self._last_signal_time = (
                bar_time.isoformat() if hasattr(bar_time, "isoformat") else str(bar_time)
            )
            self._bars_processed  += 1
            self._error            = ""

        order_id     = -1
        order_status = "NO_ORDER"
        direction    = "NONE"

        # 5. Check open position and maybe place bracket order
        if signal != 0:
            broker    = get_broker(paper=self._paper)
            positions = broker.get_positions()
            root_sym  = self._market.replace("=F", "").upper()
            has_pos   = any(
                p.get("symbol", "").upper() == root_sym for p in positions
            )

            if not has_pos:
                direction = "BUY" if signal > 0 else "SELL"

                logger.info(
                    "LiveTrader[%s] signal=%+d → %s %s qty=%s target=%.4f stop=%.4f",
                    self._algo_id, signal, direction, self._market,
                    self._qty, target, stop,
                )

                result = broker.place_bracket_order(
                    yf_symbol=self._market,
                    direction=direction,
                    qty=self._qty,
                    target=target,
                    stop=stop,
                )

                order_id     = result.get("order_id", -1)
                order_status = result.get("status",   "UNKNOWN")

                with self._state_lock:
                    if order_id > 0:
                        self._trades_today += 1
            else:
                order_status = "POSITION_OPEN"
                logger.debug(
                    "LiveTrader[%s] signal=%+d but position already open — skipping.",
                    self._algo_id, signal,
                )

        # 6. Log to CSV
        self._log_row(
            bar_time=bar_time,
            signal=signal,
            direction=direction,
            close=close,
            target=target,
            stop=stop,
            order_id=order_id,
            order_status=order_status,
        )

    # ------------------------------------------------------------------
    # CSV logging
    # ------------------------------------------------------------------

    _CSV_FIELDS = [
        "timestamp", "algo_id", "algo_name", "market",
        "signal", "direction", "close", "target", "stop",
        "order_id", "order_status",
    ]

    def _log_row(
        self,
        bar_time,
        signal: int,
        direction: str,
        close: float,
        target: float,
        stop: float,
        order_id: int,
        order_status: str,
    ) -> None:
        """Append one row to the per-algo CSV log."""
        try:
            needs_header = not self._csv_header_done and not self._log_path.exists()
            with open(self._log_path, "a", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=self._CSV_FIELDS)
                if needs_header:
                    writer.writeheader()
                writer.writerow({
                    "timestamp":    (
                        bar_time.isoformat()
                        if hasattr(bar_time, "isoformat")
                        else str(bar_time)
                    ),
                    "algo_id":      self._algo_id,
                    "algo_name":    self._algo_name,
                    "market":       self._market,
                    "signal":       signal,
                    "direction":    direction,
                    "close":        round(close,  4),
                    "target":       round(target, 4),
                    "stop":         round(stop,   4),
                    "order_id":     order_id,
                    "order_status": order_status,
                })
            self._csv_header_done = True
        except Exception as exc:
            logger.error("LiveTrader[%s] CSV write failed: %s", self._algo_id, exc)


# ---------------------------------------------------------------------------
# Module-level convenience functions (used by the dashboard)
# ---------------------------------------------------------------------------

def start_algo(
    algo_id: str,
    paper: bool = True,
    sessions: Optional[list[str]] = None,
) -> tuple[bool, str]:
    """
    Start live trading for *algo_id*.

    Looks up the algo config from ALGO_CONFIGS. If a trader for this algo_id
    is already running, this is a no-op and returns (True, "already running").

    Args:
        algo_id:  The string ID from ALGO_CONFIGS.
        paper:    True for paper trading, False for live.
        sessions: Optional list of session keys to restrict trading hours.

    Returns:
        (success: bool, message: str)
    """
    with _registry_lock:
        existing = LIVE_TRADERS.get(algo_id)
        if existing and existing.is_running():
            return True, f"Algo {algo_id} is already running."

    # Resolve config
    try:
        from algo_configs import ALGO_CONFIGS
        matches = [c for c in ALGO_CONFIGS if str(c.get("id")) == str(algo_id)]
        if not matches:
            return False, f"Algo ID {algo_id!r} not found in ALGO_CONFIGS."
        cfg = matches[0]
    except Exception as exc:
        return False, f"Could not load ALGO_CONFIGS: {exc}"

    try:
        trader = LiveTrader(algo_config=cfg, paper=paper, sessions=sessions)
        trader.start()
        with _registry_lock:
            LIVE_TRADERS[algo_id] = trader
        mode = "paper" if paper else "LIVE"
        sess = sessions or ["all"]
        return True, f"Algo {algo_id} ({cfg.get('name','')}) started in {mode} mode. Sessions: {sess}"
    except Exception as exc:
        return False, f"Failed to start algo {algo_id}: {exc}"


def stop_algo(algo_id: str) -> tuple[bool, str]:
    """
    Stop the live trader for *algo_id*.

    Args:
        algo_id: The string ID of the algo to stop.

    Returns:
        (success: bool, message: str)
    """
    with _registry_lock:
        trader = LIVE_TRADERS.get(algo_id)

    if trader is None:
        return True, f"Algo {algo_id} is not running."

    try:
        trader.stop()
        with _registry_lock:
            LIVE_TRADERS.pop(algo_id, None)
        return True, f"Algo {algo_id} stopped."
    except Exception as exc:
        return False, f"Failed to stop algo {algo_id}: {exc}"


def get_all_status() -> list[dict]:
    """
    Return a list of status dicts for all registered traders.

    Returns:
        list[dict] — one entry per registered LiveTrader.
    """
    with _registry_lock:
        snapshot = dict(LIVE_TRADERS)
    return [trader.get_status() for trader in snapshot.values()]
