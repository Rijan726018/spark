import os
import json
import requests
from .celery_app import celery_app
from backend.router.auth import redis_client

# In production, these live in a secure .env file
TRADOVATE_API_URL = "https://demo.tradovateapi.com/v1"

from .auth import get_tradovate_token
@celery_app.task(name="backend.router.execution.execute_order")
def execute_order(user_account_id, symbol, integer_qty, action):
    """
    Fires the routed order directly to the Tradovate API.
    """
    endpoint = f"{TRADOVATE_API_URL}/order/placeorder"
    bearer_token = get_tradovate_token()
    
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    
    # Tradovate's strict payload structure
    payload = {
        "accountSpec": str(user_account_id),
        "accountId": user_account_id, # The specific user's funded account
        "action": action,             # "Buy" or "Sell"
        "symbol": symbol,             # e.g., "MESM4"
        "orderQty": integer_qty,      # MUST be a whole number
        "orderType": "Market",        # Or "Limit", "Stop"
        "isAutomated": True
    }
    
    # Simple console output to simulate execution since this is a demo environment
    print(f"Executing order to Tradovate: {payload}")
    
    try:
        # Mocking the request so we don't spam the API in this demo
        class MockResponse:
            def raise_for_status(self): pass
            def json(self): return {"orderId": 123456, "status": "Working"}
            
        response = MockResponse()
        # In actual production: 
        # response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        
        # Broadcast the fill to the 'pamm_updates' channel
        fill_data = {
            "status": "FILLED",
            "account": user_account_id,
            "symbol": symbol,
            "qty": integer_qty
        }
        redis_client.publish("pamm_updates", json.dumps(fill_data))
        
        return {"status": "success", "exchange_response": response.json()}
    except Exception as e:
        # Crucial for Celery: Log the failure so the queue can retry if it was a network drop
        return {"status": "failed", "error": str(e)}
