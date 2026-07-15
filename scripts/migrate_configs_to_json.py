#!/usr/bin/env python3
"""
One-time migration: algo_configs.py  →  algo_configs.json

Run once from the project root:
    python scripts/migrate_configs_to_json.py

After success, algo_configs.py can be deleted (or kept as a backup).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import importlib.util

def main():
    py_path   = ROOT / "algo_configs.py"
    json_path = ROOT / "algo_configs.json"

    if not py_path.exists():
        print(f"ERROR: {py_path} not found")
        sys.exit(1)

    if json_path.exists():
        ans = input(f"{json_path} already exists. Overwrite? [y/N] ")
        if ans.strip().lower() != "y":
            print("Aborted.")
            sys.exit(0)

    spec = importlib.util.spec_from_file_location("algo_configs", py_path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    raw = getattr(mod, "ALGO_CONFIGS", None)
    if raw is None:
        print("ERROR: ALGO_CONFIGS not found in algo_configs.py")
        sys.exit(1)

    # Convert Path objects to strings so json.dumps works
    def make_serializable(obj):
        if isinstance(obj, Path):
            return str(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    output = json.dumps(raw, indent=2, default=make_serializable)
    json_path.write_text(output, encoding="utf-8")

    print(f"✅  Migrated {len(raw)} configs → {json_path}")
    print("   You can now delete algo_configs.py (keep a backup if unsure).")


if __name__ == "__main__":
    main()
