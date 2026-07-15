import requests
from typing import Optional, Dict, List, Any

class NinjaTraderAPI:
    """
    A Python client for the NinjaTrader REST API via CrossTrade.io.
    Documentation: https://docs.crosstrade.io/api/overview
    """
    
    BASE_URL = "https://app.crosstrade.io/v1/api"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _request(self, method: str, path: str, params: Optional[Dict] = None, json: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/{path.lstrip('/')}"
        try:
            response = requests.request(method, url, headers=self.headers, params=params, json=json)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # In a real app, you might want more granular error handling
            return {"status": "error", "message": str(e)}

    # --- Account Methods ---

    def get_accounts(self) -> List[Dict]:
        """Retrieve a list of all connected NinjaTrader accounts."""
        return self._request("GET", "accounts")

    def get_account_summary(self) -> Dict:
        """Retrieve a high-level snapshot of all accounts including balances and P/L."""
        return self._request("GET", "accounts/snapshot")

    def get_account_details(self, account_id: str) -> Dict:
        """Retrieve detailed statistics for a specific account (e.g., 'Sim101')."""
        return self._request("GET", f"accounts/{account_id}")

    # --- Position Methods ---

    def get_positions(self, account_id: Optional[str] = None) -> List[Dict]:
        """Retrieve open positions for all accounts or a specific account."""
        path = f"accounts/{account_id}/positions" if account_id else "positions"
        return self._request("GET", path)

    # --- Order Methods ---

    def get_orders(self, account_id: Optional[str] = None, active_only: bool = True) -> List[Dict]:
        """Retrieve orders. Defaults to active (working) orders only."""
        path = f"accounts/{account_id}/orders" if account_id else "orders"
        params = {"activeOnly": str(active_only).lower()}
        return self._request("GET", path, params=params)

    def place_order(
        self, 
        account_id: str, 
        instrument: str, 
        action: str, 
        quantity: int, 
        order_type: str = "MARKET", 
        tif: str = "DAY",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        atm_strategy: Optional[str] = None,
        strategy_tag: Optional[str] = None,
        flatten_first: bool = False
    ) -> Dict:
        """
        Execute a new order in NinjaTrader.
        :param action: 'BUY' or 'SELL'
        :param instrument: e.g., 'ES 03-26' or 'ES1!'
        :param order_type: 'MARKET', 'LIMIT', 'STOPMARKET', 'STOPLIMIT'
        :param tif: 'DAY', 'GTC'
        """
        payload = {
            "instrument": instrument,
            "action": action.upper(),
            "quantity": quantity,
            "order_type": order_type.upper(),
            "tif": tif.upper(),
            "flatten_first": flatten_first
        }
        
        if limit_price: payload["limit_price"] = limit_price
        if stop_price: payload["stop_price"] = stop_price
        if atm_strategy: payload["atm_strategy"] = atm_strategy
        if strategy_tag: payload["strategy_tag"] = strategy_tag

        return self._request("POST", f"accounts/{account_id}/orders", json=payload)

    def cancel_order(self, account_id: str, order_id: str) -> Dict:
        """Cancel a specific working order."""
        return self._request("POST", f"accounts/{account_id}/orders/{order_id}/cancel")

    def cancel_all_orders(self, account_id: str) -> Dict:
        """Cancel all working orders for an account."""
        return self._request("POST", f"accounts/{account_id}/orders/cancel-all")

    def flatten_account(self, account_id: str) -> Dict:
        """Close all open positions and cancel all pending orders for an account."""
        return self._request("POST", f"accounts/{account_id}/flatten")
