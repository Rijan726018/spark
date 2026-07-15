from .execution import execute_order
import math

# Mocked state of users and their balances
MOCK_USERS = [
    {"user_id": 1, "balance": 5000},
    {"user_id": 2, "balance": 15000},
    {"user_id": 3, "balance": 30000},
    {"user_id": 4, "balance": 50000},
    {"user_id": 5, "balance": 100000},
]

def convert_to_tradable_contracts(fractional_es_size, original_symbol="ES"):
    """
    Converts fractional ES allocations into whole integer MES contracts.
    """
    # If they are trading something else, just return the rounded number
    if "ES" not in original_symbol:
        return original_symbol, math.floor(fractional_es_size)

    # 1. Convert the ES size to MES size
    mes_size = fractional_es_size * 10
    
    # 2. The Risk Protocol (Rounding)
    # We use math.floor() to round DOWN. If a $5k account is allocated 0.9 MES, 
    # we round to 0 to protect them from over-leveraging. 
    # They only get a contract if their math clears 1.0 full MES.
    tradable_integer = math.floor(mes_size)
    
    # 3. Swap the ticker symbol for the exchange
    new_symbol = original_symbol.replace("ES", "MES")
    
    return new_symbol, tradable_integer

def parse_signal(master_signal: str) -> tuple:
    """
    Extracts action, quantity, and symbol from signal.
    For example: 'BUY 2 ES Contract at Market' -> ('Buy', 2.0, 'ES')
    """
    parts = master_signal.split()
    action = "Buy"
    quantity = 1.0
    symbol = "ES"
    
    if len(parts) >= 3:
        action = parts[0].capitalize()
        try:
            quantity = float(parts[1])
        except ValueError:
            pass
        symbol = parts[2].upper()
        
    return action, quantity, symbol

def process_master_signal(master_signal: str):
    """
    Receives a master trade signal and fans it out to all users 
    based on their proportional pool balance.
    """
    total_pool_balance = sum(user["balance"] for user in MOCK_USERS)
    action, master_quantity, symbol = parse_signal(master_signal)

    print(f"--- Processing Master Signal: '{master_signal}' ---")
    print(f"Total Pool Balance: ${total_pool_balance:,.2f}")
    print(f"Parsed Signal -> Action: {action}, Asset: {symbol}, Qty: {master_quantity}")

    # Pro-rata distribution
    for user in MOCK_USERS:
        weight = user["balance"] / total_pool_balance
        allocated_quantity = weight * master_quantity
        
        # Fractional Futures Reality Check
        micro_symbol, integer_qty = convert_to_tradable_contracts(allocated_quantity, symbol)

        # We assume we need a whole number representing the final qty
        if integer_qty >= 1:
            contract_symbol = f"{micro_symbol}M4"  # Dummy maturity for API completeness
            
            # Dispatch asynchronous task to Celery queue
            execute_order.delay(
                user_account_id=user["user_id"],
                symbol=contract_symbol,
                integer_qty=integer_qty,
                action=action
            )

            print(f"Dispatched task for User {user['user_id']}: {allocated_quantity:.4f} {symbol} allocated -> Executing {integer_qty} {contract_symbol} (Weight: {weight*100:.2f}%)")
        else:
            print(f"Skipped User {user['user_id']}: Ineligible amount ({allocated_quantity:.4f} {symbol} rounds to 0 micro contracts)")
