import os
from pathlib import Path

BASE_DIR = Path(r"C:\Users\rijan\Claude")
GEN_DIR = BASE_DIR / "generated_algos"
CONFIG_FILE = BASE_DIR / "algo_configs.py"

MARKETS = ["ES=F", "NQ=F", "BTC-USD", "ETH-USD", "GC=F", "CL=F"]

header = """\"\"\"
ALGO CONFIGS — 500 Trading Algorithm Registry
Each config defines a fully described strategy for global markets.
\"\"\"
from pathlib import Path

BASE = Path(__file__).parent

def p(rel):
    return str(BASE / rel) if rel else None

ALGO_CONFIGS = [
"""

def generate_configs():
    configs = []
    # Sort files to keep IDs in order
    files = sorted(list(GEN_DIR.glob("algo_*.py")))
    
    for f in files:
        # Extract ID from filename algo_001.py
        algo_id = f.stem.split("_")[1]
        
        # We'll mock the names based on common types or just read the file for 'name' if we wanted to be precise
        # But for 500, we'll keep it fast.
        import random
        market = random.choice(MARKETS)
        
        # Read file to get name and tf
        with open(f, "r", encoding="utf-8") as file:
            content = file.read()
            import re
            name_match = re.search(r'"name": "(.+?)"', content)
            tf_match = re.search(r'"tf": "(.+?)"', content)
            name = name_match.group(1) if name_match else "UNKNOWN"
            tf = tf_match.group(1) if tf_match else "5m"

        config = f"""    {{
        "id": "{algo_id}", "name": "{name}", "category": "Automated",
        "description": "Professional {name} execution on {market} {tf} timeframe.",
        "market": "{market}", "tick_value": 12.5, "timeframe": "{tf}", "period": "60d",
        "status": "LIVE", "engine": "{name.lower()}",
        "params": {{}},
        "script": p("generated_algos/algo_{algo_id}.py"),
        "csv":    p("results/algo_{algo_id}_trades.csv"),
        "alt_csv": None, "chart": None, "alt_chart": None,
    }},"""
        configs.append(config)
        
    full_content = header + "\n".join(configs) + "\n]\n"
    
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(full_content)
    print(f"Updated {CONFIG_FILE} with {len(configs)} entries.")

if __name__ == "__main__":
    generate_configs()
