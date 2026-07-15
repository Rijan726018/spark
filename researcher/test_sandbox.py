import subprocess
import sys
import tempfile
import os
import json

# Create a simple test strategy that should definitely work
simple_strategy = '''
def generate_signals(df):
    """Simple strategy: always long"""
    import pandas as pd
    signals = pd.Series(1, index=df.index)
    return signals
'''

# Create a temporary file with the strategy code and backtest logic
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    f.write(f'''
import pandas as pd
import numpy as np
import sys
import json

# Load market data
try:
    df = pd.read_csv("data_cache/ES_F_1d_5y.csv")
    print(f"Data loaded, shape: {{df.shape}}", file=sys.stderr)
    print(f"Columns: {{df.columns.tolist()}}", file=sys.stderr)
    
    # Normalize column names to have capital first letter for compatibility
    df.columns = [col.capitalize() for col in df.columns]
    print(f"After capitalizing: {{df.columns.tolist()}}", file=sys.stderr)
    
    # Ensure required columns exist
    required_cols = ['Close', 'High', 'Low']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {{col}}")
    
    # Execute the strategy code
{simple_strategy}
    
    # The strategy code must define a function called generate_signals(df) 
    # that returns a pandas Series of signals (-1, 0, 1)
    if 'generate_signals' not in locals() and 'generate_signals' not in globals():
        raise ValueError("Strategy code must define a function called 'generate_signals(df)'")
    
    # Generate signals
    signals = generate_signals(df)
    print(f"Signals generated, type: {{type(signals)}}", file=sys.stderr)
    print(f"Signals head: {{signals.head()}}", file=sys.stderr)
    
    # Validate signals
    if not isinstance(signals, pd.Series):
        signals = pd.Series(signals, index=df.index)
    
    # Vectorized backtest
    returns = df['Close'].pct_change().fillna(0)
    print(f"Returns head: {{returns.head()}}", file=sys.stderr)
    strategy_returns = signals.shift(1).fillna(0) * returns
    print(f"Strategy returns head: {{strategy_returns.head()}}", file=sys.stderr)
    
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
    print("JSON printed", file=sys.stderr)
    
except Exception as e:
    import traceback
    print(traceback.format_exc(), file=sys.stderr)
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
        timeout=30
    )
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    
    # Parse JSON output
    output_lines = result.stdout.strip().split('\n')
    for line in output_lines:
        if line.startswith('{'):
            data = json.loads(line)
            print("Parsed JSON:", data)
            break
        
except subprocess.TimeoutExpired:
    print("Backtest execution timed out.")
except Exception as e:
    print(f"Unexpected error during backtest: {str(e)}")
finally:
    # Clean up temporary file
    try:
        os.unlink(temp_file)
    except Exception as e:
        print(f"Failed to delete temporary file: {str(e)}")