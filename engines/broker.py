"""
Broker — Interactive Brokers connectivity via ib_insync.
Paper trading: port 7497. Live trading: port 7496.
TWS or IB Gateway must be running.

Usage:
    from engines.broker import get_broker, connect_broker, BROKER_STATE

    ok = connect_broker(paper=True)
    broker = get_broker()
    price = broker.get_last_price("ES=F")
    broker.place_bracket_order("ES=F", "BUY", 1, target=5110.0, stop=5090.0)
    disconnect_broker()
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional ib_insync import — platform degrades gracefully if not installed.
# ---------------------------------------------------------------------------
try:
    from ib_insync import IB, Contract, Future, LimitOrder, MarketOrder, StopOrder
    HAS_IB = True
except ImportError:
    HAS_IB = False
    # Stub out the Contract type so type hints in method signatures don't blow up
    class Contract:  # type: ignore
        pass
    logger.warning(
        "ib_insync is not installed. Broker functionality will be unavailable. "
        "Install with: pip install ib_insync"
    )

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PAPER_PORT = 7497
LIVE_PORT  = 7496

# YF ticker → IB futures spec
_YF_TO_IB: dict[str, dict] = {
    "ES=F":  {"symbol": "ES",  "exchange": "CME",   "currency": "USD"},
    "NQ=F":  {"symbol": "NQ",  "exchange": "CME",   "currency": "USD"},
    "RTY=F": {"symbol": "RTY", "exchange": "CME",   "currency": "USD"},
    "YM=F":  {"symbol": "YM",  "exchange": "CBOT",  "currency": "USD"},
    "GC=F":  {"symbol": "GC",  "exchange": "COMEX", "currency": "USD"},
    "SI=F":  {"symbol": "SI",  "exchange": "COMEX", "currency": "USD"},
    "CL=F":  {"symbol": "CL",  "exchange": "NYMEX", "currency": "USD"},
    "NG=F":  {"symbol": "NG",  "exchange": "NYMEX", "currency": "USD"},
    "ZB=F":  {"symbol": "ZB",  "exchange": "CBOT",  "currency": "USD"},
    "ZN=F":  {"symbol": "ZN",  "exchange": "CBOT",  "currency": "USD"},
}

# ---------------------------------------------------------------------------
# Module-level shared state — polled by the dashboard without instantiating
# ---------------------------------------------------------------------------
BROKER_STATE: dict = {
    "connected":    False,
    "paper_mode":   True,
    "account":      {},
    "positions":    [],
    "last_error":   "",
    "orders":       [],
}

_broker: Optional["IBBroker"] = None
_broker_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Quarterly expiry helper
# ---------------------------------------------------------------------------

def _nearest_quarterly_expiry() -> str:
    """
    Return the nearest CME quarterly expiry in YYYYMM format.
    Quarters: March (03), June (06), September (09), December (12).
    Rolls to next quarter when within 15 days of expiry.
    """
    now = datetime.now(tz=timezone.utc)
    year, month, day = now.year, now.month, now.day
    for q in (3, 6, 9, 12):
        if q > month or (q == month and day <= 15):
            return f"{year}{q:02d}"
    return f"{year + 1}03"


# ---------------------------------------------------------------------------
# IBBroker
# ---------------------------------------------------------------------------

class IBBroker:
    """
    Thread-safe wrapper around ib_insync for futures order management.

    All public methods catch all exceptions internally — they never raise.
    Errors are logged and stored in BROKER_STATE["last_error"].
    """

    def __init__(
        self,
        paper: bool = True,
        client_id: int = 1,
        host: str = "127.0.0.1",
    ) -> None:
        self._paper     = paper
        self._client_id = client_id
        self._host      = host
        self._port      = PAPER_PORT if paper else LIVE_PORT
        self._lock      = threading.Lock()
        self._ib: Optional["IB"] = None

        BROKER_STATE["paper_mode"] = paper

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """
        Connect to TWS / IB Gateway.
        Returns True on success, False on failure.
        """
        if not HAS_IB:
            self._set_error("ib_insync is not installed — cannot connect.")
            return False

        with self._lock:
            try:
                if self._ib and self._ib.isConnected():
                    BROKER_STATE["connected"] = True
                    return True

                self._ib = IB()
                self._ib.connect(
                    host=self._host,
                    port=self._port,
                    clientId=self._client_id,
                    readonly=False,
                    timeout=10,
                )
                connected = bool(self._ib.isConnected())
                BROKER_STATE["connected"] = connected
                if connected:
                    logger.info(
                        "Connected to IB (%s) on %s:%s clientId=%s",
                        "paper" if self._paper else "LIVE",
                        self._host, self._port, self._client_id,
                    )
                    BROKER_STATE["last_error"] = ""
                else:
                    self._set_error("connect() returned but isConnected() is False.")
                return connected
            except Exception as exc:
                self._set_error(f"connect() failed: {exc}")
                BROKER_STATE["connected"] = False
                return False

    def disconnect(self) -> None:
        """Disconnect from TWS / IB Gateway."""
        with self._lock:
            try:
                if self._ib and self._ib.isConnected():
                    self._ib.disconnect()
                    logger.info("Disconnected from IB.")
            except Exception as exc:
                self._set_error(f"disconnect() failed: {exc}")
            finally:
                BROKER_STATE["connected"] = False

    def is_connected(self) -> bool:
        """Return True if the IB connection is currently active."""
        try:
            if not HAS_IB or self._ib is None:
                return False
            return bool(self._ib.isConnected())
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Contract
    # ------------------------------------------------------------------

    def get_futures_contract(self, yf_symbol: str) -> "Contract":
        """
        Build and qualify an IB Future contract from a Yahoo Finance symbol.

        Maps YF tickers to IB root symbols and exchanges:
            ES=F  → ES  @ CME
            NQ=F  → NQ  @ CME
            YM=F  → YM  @ CBOT
            GC=F  → GC  @ COMEX
            CL=F  → CL  @ NYMEX
            SI=F  → SI  @ COMEX
            ZB=F  → ZB  @ CBOT
            ZN=F  → ZN  @ CBOT
            RTY=F → RTY @ CME
            NG=F  → NG  @ NYMEX

        Uses the nearest quarterly expiry.

        Returns:
            A qualified ib_insync Contract (or unqualified fallback).

        Raises:
            RuntimeError if ib_insync is not installed.
        """
        if not HAS_IB:
            raise RuntimeError("ib_insync is not installed.")

        info = _YF_TO_IB.get(yf_symbol)
        if info:
            symbol   = info["symbol"]
            exchange = info["exchange"]
            currency = info["currency"]
        else:
            # Best-effort fallback: strip "=F"
            symbol   = yf_symbol.replace("=F", "").upper()
            exchange = "CME"
            currency = "USD"

        expiry   = _nearest_quarterly_expiry()
        contract = Future(
            symbol=symbol,
            lastTradeDateOrContractMonth=expiry,
            exchange=exchange,
            currency=currency,
        )

        with self._lock:
            try:
                qualified = self._ib.qualifyContracts(contract)
                if qualified:
                    return qualified[0]
                logger.warning("Could not qualify contract for %s; using unqualified.", symbol)
                return contract
            except Exception as exc:
                self._set_error(f"get_futures_contract({yf_symbol}) qualify failed: {exc}")
                return contract

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    def place_bracket_order(
        self,
        yf_symbol: str,
        direction: str,
        qty: int,
        target: float,
        stop: float,
    ) -> dict:
        """
        Place a bracket order: MKT entry + LMT take-profit + STP stop-loss.

        Args:
            yf_symbol:  Yahoo Finance ticker, e.g. "ES=F".
            direction:  "BUY" or "SELL".
            qty:        Number of contracts.
            target:     Limit price for the profit-taker leg.
            stop:       Stop price for the stop-loss leg.

        Returns:
            {"order_id": int, "status": str, "error": str}
        """
        if not self._require_connection():
            return {"order_id": -1, "status": "NOT_CONNECTED", "error": BROKER_STATE["last_error"]}

        direction = direction.upper()
        if direction not in ("BUY", "SELL"):
            err = f"Invalid direction: {direction!r}"
            self._set_error(err)
            return {"order_id": -1, "status": "INVALID_DIRECTION", "error": err}

        try:
            contract = self.get_futures_contract(yf_symbol)

            # Exit direction is opposite to entry
            exit_action = "SELL" if direction == "BUY" else "BUY"

            with self._lock:
                # Parent market order
                parent = MarketOrder(action=direction, totalQuantity=qty)
                parent.transmit = False

                parent_trade = self._ib.placeOrder(contract, parent)
                parent_id    = parent_trade.order.orderId

                # Take-profit limit
                tp_order = LimitOrder(
                    action=exit_action,
                    totalQuantity=qty,
                    lmtPrice=round(target, 4),
                    parentId=parent_id,
                    transmit=False,
                )
                self._ib.placeOrder(contract, tp_order)

                # Stop-loss stop order
                sl_order = StopOrder(
                    action=exit_action,
                    totalQuantity=qty,
                    stopPrice=round(stop, 4),
                    parentId=parent_id,
                    transmit=True,   # transmit=True on last leg sends all three
                )
                self._ib.placeOrder(contract, sl_order)

                status = parent_trade.orderStatus.status or "Submitted"

            order_record = {
                "order_id":  parent_id,
                "symbol":    yf_symbol,
                "direction": direction,
                "qty":       qty,
                "target":    target,
                "stop":      stop,
                "status":    status,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            }
            BROKER_STATE["orders"].append(order_record)

            logger.info(
                "Bracket order placed: %s %s %s target=%.4f stop=%.4f orderId=%s status=%s",
                direction, qty, yf_symbol, target, stop, parent_id, status,
            )
            return {"order_id": parent_id, "status": status, "error": ""}

        except Exception as exc:
            self._set_error(f"place_bracket_order() failed: {exc}")
            return {"order_id": -1, "status": "ERROR", "error": str(exc)}

    def place_market_order(self, yf_symbol: str, direction: str, qty: int) -> dict:
        """
        Place a simple market order.

        Args:
            yf_symbol:  Yahoo Finance ticker, e.g. "ES=F".
            direction:  "BUY" or "SELL".
            qty:        Number of contracts.

        Returns:
            {"order_id": int, "status": str, "error": str}
        """
        if not self._require_connection():
            return {"order_id": -1, "status": "NOT_CONNECTED", "error": BROKER_STATE["last_error"]}

        direction = direction.upper()
        if direction not in ("BUY", "SELL"):
            err = f"Invalid direction: {direction!r}"
            self._set_error(err)
            return {"order_id": -1, "status": "INVALID_DIRECTION", "error": err}

        try:
            contract = self.get_futures_contract(yf_symbol)
            order    = MarketOrder(action=direction, totalQuantity=qty)

            with self._lock:
                trade    = self._ib.placeOrder(contract, order)
                order_id = trade.order.orderId
                status   = trade.orderStatus.status or "Submitted"

            order_record = {
                "order_id":  order_id,
                "symbol":    yf_symbol,
                "direction": direction,
                "qty":       qty,
                "status":    status,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            }
            BROKER_STATE["orders"].append(order_record)

            logger.info(
                "Market order placed: %s %s %s orderId=%s status=%s",
                direction, qty, yf_symbol, order_id, status,
            )
            return {"order_id": order_id, "status": status, "error": ""}

        except Exception as exc:
            self._set_error(f"place_market_order() failed: {exc}")
            return {"order_id": -1, "status": "ERROR", "error": str(exc)}

    def cancel_all_orders(self) -> bool:
        """
        Cancel every open order on the account via global cancel.

        Returns:
            True on success, False on failure.
        """
        if not self._require_connection():
            return False
        try:
            with self._lock:
                self._ib.reqGlobalCancel()
            logger.info("cancel_all_orders: global cancel sent.")
            return True
        except Exception as exc:
            self._set_error(f"cancel_all_orders() failed: {exc}")
            return False

    # ------------------------------------------------------------------
    # Account / Position queries
    # ------------------------------------------------------------------

    def get_positions(self) -> list[dict]:
        """
        Return all open positions.

        Returns:
            List of dicts: {symbol, side, qty, avg_price, unrealized_pnl}
        """
        if not self._require_connection():
            return []
        try:
            with self._lock:
                raw = self._ib.positions()

            result = []
            for pos in raw:
                qty  = pos.position
                side = "LONG" if qty > 0 else "SHORT"
                result.append({
                    "symbol":         pos.contract.symbol,
                    "side":           side,
                    "qty":            abs(qty),
                    "avg_price":      float(pos.avgCost),
                    "unrealized_pnl": float(getattr(pos, "unrealizedPNL", 0.0)),
                })

            BROKER_STATE["positions"] = result
            return result

        except Exception as exc:
            self._set_error(f"get_positions() failed: {exc}")
            return []

    def get_account(self) -> dict:
        """
        Return a summary of account balances.

        Returns:
            {cash, net_liq, unrealized_pnl, realized_pnl, buying_power}
        """
        if not self._require_connection():
            return {}
        try:
            with self._lock:
                summary = self._ib.accountSummary()

            values: dict[str, float] = {}
            for item in summary:
                if item.currency != "USD":
                    continue
                try:
                    values[item.tag] = float(item.value)
                except (ValueError, TypeError):
                    pass

            result = {
                "cash":           values.get("AvailableFunds", 0.0),
                "net_liq":        values.get("NetLiquidation", 0.0),
                "unrealized_pnl": values.get("UnrealizedPnL", 0.0),
                "realized_pnl":   values.get("RealizedPnL", 0.0),
                "buying_power":   values.get("BuyingPower", 0.0),
            }
            BROKER_STATE["account"] = result
            return result

        except Exception as exc:
            self._set_error(f"get_account() failed: {exc}")
            return {}

    def get_last_price(self, yf_symbol: str) -> float | None:
        """
        Return the last traded price for a futures contract via snapshot.

        Args:
            yf_symbol: Yahoo Finance ticker, e.g. "ES=F".

        Returns:
            Last price as float, or None on failure.
        """
        if not self._require_connection():
            return None
        try:
            contract = self.get_futures_contract(yf_symbol)
            with self._lock:
                ticker = self._ib.reqMktData(
                    contract, "", snapshot=True, regulatorySnapshot=False
                )
                self._ib.sleep(1.5)
                price = ticker.last if (ticker.last and ticker.last > 0) else ticker.close
                self._ib.cancelMktData(contract)

            return float(price) if price else None

        except Exception as exc:
            self._set_error(f"get_last_price({yf_symbol}) failed: {exc}")
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_connection(self) -> bool:
        """Return True if ready to trade; set last_error and return False otherwise."""
        if not HAS_IB:
            self._set_error("ib_insync is not installed.")
            return False
        if not self.is_connected():
            self._set_error("Not connected to IB. Call connect() first.")
            return False
        return True

    def _set_error(self, message: str) -> None:
        """Log an error and store it in BROKER_STATE."""
        logger.error(message)
        BROKER_STATE["last_error"] = message


# ---------------------------------------------------------------------------
# Module-level singleton helpers
# ---------------------------------------------------------------------------

def get_broker(paper: bool = True) -> IBBroker:
    """
    Return the module-level singleton IBBroker, creating it if necessary.

    Args:
        paper: True = paper trading (port 7497), False = live (port 7496).

    Returns:
        IBBroker instance (regardless of whether ib_insync is installed).
    """
    global _broker
    with _broker_lock:
        if _broker is None:
            _broker = IBBroker(paper=paper)
        return _broker


def connect_broker(paper: bool = True) -> bool:
    """
    Convenience function: create (if needed) and connect the singleton broker.

    Updates BROKER_STATE["connected"] and BROKER_STATE["paper_mode"].

    Args:
        paper: True for paper trading, False for live.

    Returns:
        True on successful connection, False otherwise.
    """
    broker = get_broker(paper=paper)
    result = broker.connect()
    BROKER_STATE["connected"]  = broker.is_connected()
    BROKER_STATE["paper_mode"] = paper
    return result


def disconnect_broker() -> None:
    """
    Convenience function: disconnect the singleton broker if it exists.
    Safe to call even if no broker has been created or already disconnected.
    """
    global _broker
    with _broker_lock:
        b = _broker
    if b is not None:
        b.disconnect()
    BROKER_STATE["connected"] = False
