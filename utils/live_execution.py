import os
from typing import Optional, Dict
from utils.ninjatrader_api import NinjaTraderAPI

class LiveExecutionManager:
    """
    Manages live execution flow for algorithms.
    Handles the transition from backtesting to live NinjaTrader execution.
    """
    def __init__(self, api_key: Optional[str] = None, account_id: str = "Sim101"):
        # Prioritize passed API key, then environment variable
        self.api_key = api_key or os.getenv("CROSSTRADE_SECRET_KEY")
        self.account_id = account_id
        
        if not self.api_key:
            print("(!) LiveExecutionManager: CROSSTRADE_SECRET_KEY not found. Operating in DRY RUN mode.")
            self.api = None
        else:
            self.api = NinjaTraderAPI(self.api_key)
            print(f"(+) LiveExecutionManager: Connected to CrossTrade.io (Account: {self.account_id})")

    def execute_signal(self, instrument: str, signal: int, quantity: int = 1, strategy_tag: Optional[str] = None) -> Dict:
        """
        Executes a trade based on a signal.
        :param instrument: NinjaTrader instrument string (e.g., 'MNQ 06-26' or 'MNQ1!')
        :param signal: 1 for BUY (Long), -1 for SELL (Short)
        :param quantity: Number of contracts
        :param strategy_tag: Optional identifier for the specific algo
        """
        if signal == 0:
            return {"status": "no_signal"}

        action = "BUY" if signal > 0 else "SELL"
        
        if not self.api:
            print(f"[DRY RUN] Would execute {action} {quantity} x {instrument}")
            return {"status": "dry_run", "action": action, "instrument": instrument, "quantity": quantity}

        print(f"[LIVE] Executing {action} {quantity} x {instrument} on {self.account_id}...")
        
        response = self.api.place_order(
            account_id=self.account_id,
            instrument=instrument,
            action=action,
            quantity=quantity,
            order_type="MARKET",
            strategy_tag=strategy_tag
        )
        
        if response.get("status") == "error":
            print(f"[ERROR] Execution failed: {response.get('message')}")
        else:
            print(f"[SUCCESS] Order placed. ID: {response.get('id', 'N/A')}")
            
        return response

    def flatten(self) -> Dict:
        """Closes all positions for the configured account."""
        if not self.api:
            print("[DRY RUN] Would flatten all positions.")
            return {"status": "dry_run"}
            
        print(f"[LIVE] Flattening account {self.account_id}...")
        return self.api.flatten_account(self.account_id)
