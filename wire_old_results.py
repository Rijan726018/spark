"""
Maps the existing Gemini-generated CSV files (algo_1 through algo_100)
onto the first N testing configs (IDs 101+) so the dashboard shows data immediately.
Also renames files that use 3-digit padding (algo_001) to 2-digit (algo_01) etc.
"""
import os, shutil, sys
from pathlib import Path

BASE    = Path(__file__).parent
RESULTS = BASE / "results"

sys.path.insert(0, str(BASE))
import algo_configs as _ac

# Files from Gemini batch (old format: algo_1 through algo_99, no zero-pad)
old_files = sorted(
    [f for f in RESULTS.iterdir()
     if f.name.startswith("algo_") and f.name.endswith("_trades.csv")
     and not f.name.startswith("algo_0")  # skip algo_01, algo_02, etc.
     and "_1h_" not in f.name
    ],
    key=lambda f: int(f.stem.split("_")[1]) if f.stem.split("_")[1].isdigit() else 9999
)

print(f"Found {len(old_files)} old-format CSVs")

# Our new TESTING configs
testing = [a for a in _ac.ALGO_CONFIGS if a.get("status") == "TESTING"]
print(f"Found {len(testing)} TESTING configs")

# Copy old files to match the TESTING config CSV paths
mapped = 0
for algo, old_file in zip(testing, old_files):
    target = algo.get("csv")
    if not target:
        continue
    target_path = Path(target)
    if not target_path.exists():
        shutil.copy2(old_file, target_path)
        mapped += 1

print(f"Mapped {mapped} old CSVs -> new config paths")

# Verify
import importlib
if "algo_configs" in sys.modules:
    del sys.modules["algo_configs"]
import algo_configs
matched = [(a["id"], a["csv"]) for a in algo_configs.ALGO_CONFIGS
           if a.get("csv") and Path(a["csv"]).exists()]
print(f"Configs with data: {len(matched)}/{len(algo_configs.ALGO_CONFIGS)}")
