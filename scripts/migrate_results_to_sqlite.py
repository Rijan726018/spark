#!/usr/bin/env python3
"""
One-time migration: results/**/*.csv  →  nexus_results.db

Run from the project root:
    python scripts/migrate_results_to_sqlite.py

Safe to re-run (uses INSERT OR IGNORE).
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.results_db import ResultsDB


def parse_ts(raw: str) -> int | None:
    """Try common date/time formats, return Unix timestamp or None."""
    from datetime import datetime
    for fmt in ("%Y%m%d %H%M%S", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%Y%m%d"):
        try:
            return int(datetime.strptime(raw.strip(), fmt).timestamp())
        except ValueError:
            continue
    try:
        return int(float(raw))
    except (ValueError, TypeError):
        return None


def load_csv(fpath: Path, algo_id: str) -> list[dict]:
    trades = []
    with open(fpath, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = {h.strip().lower(): h for h in (reader.fieldnames or [])}

        def gcol(*names):
            for n in names:
                if n in fields:
                    return fields[n]
            return None

        tc = gcol("time", "datetime", "date", "entry time", "entrytime")
        sc = gcol("side", "direction", "type", "action")
        pc = gcol("price", "entry price", "entryprice", "fill price")
        qc = gcol("qty", "quantity", "size", "contracts")

        if not (tc and sc and pc):
            print(f"  Skipping {fpath.name}: missing required columns")
            return []

        for row in reader:
            ts = parse_ts(row[tc])
            if ts is None:
                continue
            try:
                trades.append({
                    "algo_id": algo_id,
                    "symbol":  "ES",
                    "side":    str(row[sc]).upper().strip(),
                    "price":   float(row[pc]),
                    "qty":     int(float(row[qc])) if qc and row.get(qc) else 1,
                    "time":    ts,
                })
            except (ValueError, KeyError):
                continue
    return trades


def main():
    results_dir = ROOT / "results"
    if not results_dir.exists():
        print(f"No results directory found at {results_dir}")
        sys.exit(0)

    csv_files = list(results_dir.rglob("*.csv"))
    if not csv_files:
        print("No CSV files found in results/")
        sys.exit(0)

    print(f"Found {len(csv_files)} CSV files. Migrating to nexus_results.db...")

    total_rows = 0
    with ResultsDB() as db:
        for fpath in csv_files:
            # Extract algo_id from filename, e.g. algo_01_trades.csv → 001
            stem = fpath.stem.lower()
            algo_id = "000"
            for part in stem.split("_"):
                try:
                    algo_id = str(int(part)).zfill(3)
                    break
                except ValueError:
                    continue

            trades = load_csv(fpath, algo_id)
            if trades:
                db.insert_trades(algo_id, trades)
                total_rows += len(trades)
                print(f"  {fpath.relative_to(ROOT)}: {len(trades)} trades (algo {algo_id})")

    print(f"\n✅  Migrated {total_rows} trades from {len(csv_files)} files.")
    print("   nexus_results.db is now the source of truth.")
    print("   You can delete the results/ directory (add it to .gitignore first).")


if __name__ == "__main__":
    main()
