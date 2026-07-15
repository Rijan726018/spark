import subprocess
import sys
import tempfile
import os
import json
import pandas as pd
import numpy as np
from pydantic import BaseModel
from typing import Dict, Any
from pathlib import Path

class BacktestResult(BaseModel):
    sharpe_ratio: float
    max_drawdown: float
    net_profit: float

def vectorized_backtest_engine(df: pd.DataFrame, signals: pd.Series) -> Dict[str, float]:
    """
    Vectorized backtest engine using pandas operations.
    
    Parameters:
    df: DataFrame with 'Close', 'High', 'Low' columns
    signals: Series of trading signals (-1, 0, 1)
    
    Returns:
    Dict with net_profit, max_drawdown, sharpe_ratio
    """
    # Calculate daily returns
    returns = df['Close'].pct_change().fillna(0)
    
    # Strategy returns (shift signals by 1 to avoid lookahead bias)
    strategy_returns = signals.shift(1).fillna(0) * returns
    
    # Cumulative returns
    cumulative_returns = (1 + strategy_returns).cumprod()
    
    # Portfolio value assuming $10,000 initial capital
    initial_capital = 10000
    portfolio_value = initial_capital * cumulative_returns
    
    # Net profit
    net_profit = portfolio_value.iloc[-1] - initial_capital
    
    # Maximum drawdown
    running_max = portfolio_value.expanding().max()
    drawdown = (portfolio_value - running_max) / running_max
    max_drawdown = abs(drawdown.min()) * 100  # Convert to percentage
    
    # Sharpe ratio (annualized, 252 trading days)
    if strategy_returns.std() > 0:
        sharpe_ratio = (strategy_returns.mean() / strategy_returns.std()) * np.sqrt(252)
    else:
        sharpe_ratio = 0.0
    
    return {
        "net_profit": float(net_profit),
        "max_drawdown": float(max_drawdown),
        "sharpe_ratio": float(sharpe_ratio)
    }

def run_backtest(strategy_code: str, data_path: str = "data_cache/ES_F_1d_5y.csv") -> BacktestResult:
    """
    Execute strategy code with real data using vectorized backtesting.
    """
    # Prepare the strategy code by ensuring it's properly indented
    # We'll split the strategy code by lines and indent each line by 4 spaces
    indented_strategy = '\n'.join(['    ' + line for line in strategy_code.split('\n')])
    
    # Create a temporary file with the strategy code and backtest logic
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(f'''import pandas as pd
import numpy as np
import sys
import json

# Load market data
try:
    df = pd.read_csv("{data_path}")
    
    # Normalize column names to have capital first letter for compatibility
    df.columns = [col.capitalize() for col in df.columns]
    
    # Ensure required columns exist
    required_cols = ['Close', 'High', 'Low']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {{col}}")
    
    # Execute the strategy code
{indented_strategy}
    
    # The strategy code must define a function called generate_signals(df) 
    # that returns a pandas Series of signals (-1, 0, 1)
    if 'generate_signals' not in locals() and 'generate_signals' not in globals():
        raise ValueError("Strategy code must define a function called 'generate_signals(df)'")
    
    # Generate signals
    signals = generate_signals(df)
    
    # Validate signals
    if not isinstance(signals, pd.Series):
        signals = pd.Series(signals, index=df.index)
    
    # Vectorized backtest
    returns = df['Close'].pct_change().fillna(0)
    strategy_returns = signals.shift(1).fillna(0) * returns
    
    # Cumulative returns
    cumulative_returns = (1 + strategy_returns).cumprod()
    initial_capital = 10000
    portfolio_value = initial_capital * cumulative_returns
    net_profit = portfolio_value.iloc[-1] - initial_capital
    
    # Maximum drawdown
    running_max = portfolio_value.expanding().max()
    drawdown = (portfolio_value - running_max) / running_max
    max_drawdown = abs(drawdown.min()) * 100
    
    # Sharpe ratio
    if strategy_returns.std() > 0:
        sharpe_ratio = (strategy_returns.mean() / strategy_returns.std()) * np.sqrt(252)
    else:
        sharpe_ratio = 0.0
    
    # Return results
    result = {{
        "sharpe_ratio": float(sharpe_ratio),
        "max_drawdown": float(max_drawdown),
        "net_profit": float(net_profit)
    }}
    
    print(json.dumps(result))
    
except Exception as e:
    print(json.dumps({{
        "error": str(e),
        "sharpe_ratio": 0.0,
        "max_drawdown": 100.0,
        "net_profit": -1000.0
    }}))
''')
        temp_file = f.name

    try:
        # Run the backtest in a subprocess with timeout
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=30  # Increased timeout for data loading
        )
        
        # Parse JSON output
        output_lines = result.stdout.strip().split('\n')
        for line in output_lines:
            if line.startswith('{'):
                data = json.loads(line)
                if "error" in data:
                    print(f"Backtest error: {data['error']}")
                return BacktestResult(**data)
        
        # If no valid JSON, return failure
        print(f"Invalid output: {result.stdout}")
        return BacktestResult(
            sharpe_ratio=0.0,
            max_drawdown=100.0,
            net_profit=-1000.0
        )
        
    except subprocess.TimeoutExpired:
        print("Backtest execution timed out.")
        return BacktestResult(
            sharpe_ratio=0.0,
            max_drawdown=100.0,
            net_profit=-1000.0
        )
    except Exception as e:
        print(f"Unexpected error during backtest: {str(e)}")
        return BacktestResult(
            sharpe_ratio=0.0,
            max_drawdown=100.0,
            net_profit=-1000.0
        )
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file)
        except Exception as e:
            print(f"Failed to delete temporary file: {str(e)}")

# Example strategy function for testing
def example_strategy():
    return '''
def generate_signals(df):
    """Simple moving average crossover strategy"""
    # Calculate moving averages
    short_ma = df['Close'].rolling(window=10).mean()
    long_ma = df['Close'].rolling(window=30).mean()
    
    # Generate signals: 1 when short MA > long MA, -1 when short MA < long MA
    signals = pd.Series(0, index=df.index)
    signals[short_ma > long_ma] = 1
    signals[short_ma < long_ma] = -1
    
    return signals
'''

if __name__ == "__main__":
    # Test with example strategy
    test_code = example_strategy()
    result = run_backtest(test_code)
    print(f"Backtest result: {result}")
    
    # Test performance
    print(f"\nPerformance metrics:")
    print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"  Max Drawdown: {result.max_drawdown:.1f}%")
    print(f"  Net Profit: ${result.net_profit:,.2f}")