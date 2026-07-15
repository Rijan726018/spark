"""
ResultsDB — SQLite store for backtest trade results.

Replaces the results/ directory of per-algo CSV files with a single queryable
database. One file, no 739-subdir sprawl, full SQL query capability.

Usage:
    db = ResultsDB()  # creates nexus_results.db at project root by default
    db.insert_trades("001", trades_list_of_dicts)
    df = db.get_trades("001", limit=100)
    summary = db.get_summary("001")
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger("nexus.results_db")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DB   = _PROJECT_ROOT / "nexus_results.db"

_DDL = """
CREATE TABLE IF NOT EXISTS trades (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    algo_id     TEXT    NOT NULL,
    symbol      TEXT    NOT NULL,
    side        TEXT    NOT NULL CHECK(side IN ('BUY','SELL')),
    price       REAL    NOT NULL,
    qty         INTEGER NOT NULL DEFAULT 1,
    ts          INTEGER NOT NULL,     -- Unix timestamp (seconds)
    run_id      TEXT,                 -- optional: group by backtest run
    created_at  INTEGER DEFAULT (strftime('%s','now'))
);

CREATE INDEX IF NOT EXISTS idx_trades_algo_ts ON trades(algo_id, ts);
CREATE INDEX IF NOT EXISTS idx_trades_run     ON trades(run_id);

CREATE TABLE IF NOT EXISTS backtest_runs (
    run_id      TEXT    PRIMARY KEY,
    algo_id     TEXT    NOT NULL,
    started_at  INTEGER NOT NULL,
    ended_at    INTEGER,
    total_pnl   REAL,
    win_rate    REAL,
    max_dd      REAL,
    params      TEXT    -- JSON string of algo params used
);
"""


class ResultsDB:
    def __init__(self, db_path: Optional[Path] = None):
        self._path = db_path or _DEFAULT_DB
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()
        logger.info("ResultsDB initialised at %s", self._path)

    # ── Writes ─────────────────────────────────────────────────────────────────

    def insert_trades(self, algo_id: str, trades: list[dict], run_id: Optional[str] = None):
        """Bulk-insert a list of trade dicts. Idempotent on duplicate (ts, algo, price)."""
        rows = [
            (
                algo_id,
                t.get("symbol", "ES"),
                t.get("side", "BUY").upper(),
                float(t.get("price", 0)),
                int(t.get("qty", 1)),
                int(t.get("time", t.get("ts", 0))),
                run_id,
            )
            for t in trades
        ]
        self._conn.executemany(
            """INSERT OR IGNORE INTO trades
               (algo_id, symbol, side, price, qty, ts, run_id)
               VALUES (?,?,?,?,?,?,?)""",
            rows,
        )
        self._conn.commit()
        logger.debug("Inserted %d trades for algo %s", len(rows), algo_id)

    def save_run(self, run_id: str, algo_id: str, params: dict,
                 total_pnl: float, win_rate: float, max_dd: float):
        import json
        self._conn.execute(
            """INSERT OR REPLACE INTO backtest_runs
               (run_id, algo_id, started_at, ended_at, total_pnl, win_rate, max_dd, params)
               VALUES (?, ?, strftime('%s','now'), strftime('%s','now'), ?, ?, ?, ?)""",
            (run_id, algo_id, total_pnl, win_rate, max_dd, json.dumps(params)),
        )
        self._conn.commit()

    # ── Reads ──────────────────────────────────────────────────────────────────

    def get_trades(self, algo_id: str, limit: int = 200,
                   run_id: Optional[str] = None) -> list[dict]:
        q = "SELECT * FROM trades WHERE algo_id = ?"
        params: list = [algo_id]
        if run_id:
            q += " AND run_id = ?"
            params.append(run_id)
        q += " ORDER BY ts DESC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]

    def get_summary(self, algo_id: str) -> dict:
        row = self._conn.execute(
            "SELECT COUNT(*) as n, MIN(price) as low, MAX(price) as high "
            "FROM trades WHERE algo_id = ?",
            (algo_id,),
        ).fetchone()
        return dict(row) if row else {}

    def get_all_algo_ids(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT algo_id FROM trades ORDER BY algo_id"
        ).fetchall()
        return [r[0] for r in rows]

    # ── Cleanup ────────────────────────────────────────────────────────────────

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
