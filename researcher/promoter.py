import os
import time
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from .sandbox import BacktestResult

class PromotionLogger:
    def __init__(self, log_path: str = "researcher/evolution_log.txt"):
        self.log_path = log_path
        Path(os.path.dirname(log_path)).mkdir(parents=True, exist_ok=True)

    def log_entry(self, strategy_name: str, result: BacktestResult, promoted: bool):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {strategy_name} - " \
                f"Sharpe: {result.sharpe_ratio:.2f}, " \
                f"Drawdown: {result.max_drawdown:.1f}%, " \
                f"Profit: ${result.net_profit:,.2f} - " \
                f"Status: {'PROMOTED' if promoted else 'REJECTED'}\n"
        
        with open(self.log_path, 'a') as f:
            f.write(entry)

def promote_strategy(strategy_code: str, result: BacktestResult, strategy_name: str) -> bool:
    """Save strategy to incubation if it meets criteria and log result"""
    logger = PromotionLogger()
    
    try:
        meets_criteria = result.sharpe_ratio > 1.5 and result.max_drawdown < 15.0
        incubation_dir = "registry/incubation"
        
        # Create incubation directory if needed
        Path(incubation_dir).mkdir(parents=True, exist_ok=True)
        
        if meets_criteria:
            # Generate unique filename
            timestamp = int(time.time())
            filename = f"{incubation_dir}/strat_{timestamp}_{strategy_name}.py"
            
            # Save the promoted strategy
            with open(filename, 'w') as f:
                f.write(strategy_code)
            
            logger.log_entry(strategy_name, result, promoted=True)
            return True
        else:
            logger.log_entry(strategy_name, result, promoted=False)
            return False
            
    except Exception as e:
        print(f"Promotion failed: {str(e)}")
        logger.log_entry(strategy_name, result, promoted=False)
        return False

if __name__ == "__main__":
    # Test promotion system
    test_result = BacktestResult(
        sharpe_ratio=1.8,
        max_drawdown=12.5,
        net_profit=5400.0
    )
    
    promote_strategy(
        strategy_code="print('test strategy')",
        result=test_result,
        strategy_name="test_strategy"
    )