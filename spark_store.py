"""User data for Spark: saved ideas, preferences, digest subscriptions, feedback.

Same design rules as spark_billing:
  * Zero new dependencies — stdlib sqlite3, one file, per-call connections.
  * Shares the billing database file (SPARK_DB_PATH / spark_users.db) so a
    single volume mount persists everything; tables are namespaced and
    created lazily, so this module never touches billing's schema.
  * Every write path is capped (rows per user / total rows) — user data must
    never let one client grow the volume unbounded.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path

_DB_PATH = Path(__file__).parent / "spark_users.db"

MAX_SAVES_PER_USER = 300
MAX_FEEDBACK_ROWS = 50_000


def _db() -> sqlite3.Connection:
    # SPARK_DB_PATH points the store at the deploy volume; resolved per-call so
    # tests can monkeypatch _DB_PATH and the env can be set after import.
    path = Path(os.getenv("SPARK_DB_PATH") or _DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS saves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT NOT NULL,
            niche TEXT NOT NULL DEFAULT '',
            topic TEXT NOT NULL,
            idea TEXT NOT NULL,
            created REAL NOT NULL,
            UNIQUE(token, topic)
        );
        CREATE TABLE IF NOT EXISTS prefs (
            token TEXT PRIMARY KEY,
            niche TEXT NOT NULL DEFAULT '',
            geo TEXT NOT NULL DEFAULT '',
            channel TEXT NOT NULL DEFAULT '',
            audience TEXT NOT NULL DEFAULT '',
            tone TEXT NOT NULL DEFAULT '',
            updated REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS digest_subs (
            email TEXT PRIMARY KEY,
            token TEXT NOT NULL,
            niche TEXT NOT NULL,
            hour INTEGER NOT NULL DEFAULT 7,
            last_sent TEXT NOT NULL DEFAULT '',
            created REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS feedback (
            actor TEXT NOT NULL,
            niche TEXT NOT NULL,
            topic TEXT NOT NULL,
            vote INTEGER NOT NULL,
            created REAL NOT NULL,
            PRIMARY KEY (actor, niche, topic)
        );
    """)
    return conn


# ── saved ideas ───────────────────────────────────────────────────────────────

def save_idea(token: str, niche: str, idea: dict) -> dict:
    """Upsert one saved idea (keyed by topic). Returns {'id': ..., 'saved': bool}.

    saved=False means the per-user cap was hit and nothing was written.
    """
    topic = str(idea.get("topic", "")).strip()
    conn = _db()
    try:
        n = conn.execute("SELECT COUNT(*) FROM saves WHERE token=?",
                         (token,)).fetchone()[0]
        existing = conn.execute(
            "SELECT id FROM saves WHERE token=? AND topic=?",
            (token, topic)).fetchone()
        if existing is None and n >= MAX_SAVES_PER_USER:
            return {"id": None, "saved": False}
        if existing:
            conn.execute("UPDATE saves SET niche=?, idea=?, created=? WHERE id=?",
                         (niche, json.dumps(idea), time.time(), existing["id"]))
            conn.commit()
            return {"id": existing["id"], "saved": True}
        cur = conn.execute(
            "INSERT INTO saves (token, niche, topic, idea, created) VALUES (?,?,?,?,?)",
            (token, niche, topic, json.dumps(idea), time.time()))
        conn.commit()
        return {"id": cur.lastrowid, "saved": True}
    finally:
        conn.close()


def list_saves(token: str) -> list[dict]:
    conn = _db()
    try:
        rows = conn.execute(
            "SELECT id, niche, topic, idea, created FROM saves "
            "WHERE token=? ORDER BY created DESC", (token,)).fetchall()
        out = []
        for r in rows:
            try:
                idea = json.loads(r["idea"])
            except json.JSONDecodeError:
                continue
            out.append({"id": r["id"], "niche": r["niche"],
                        "created": r["created"], "idea": idea})
        return out
    finally:
        conn.close()


def delete_save(token: str, save_id: int) -> bool:
    conn = _db()
    try:
        cur = conn.execute("DELETE FROM saves WHERE token=? AND id=?",
                           (token, save_id))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ── preferences ───────────────────────────────────────────────────────────────

def get_prefs(token: str) -> dict | None:
    conn = _db()
    try:
        row = conn.execute("SELECT * FROM prefs WHERE token=?", (token,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def set_prefs(token: str, niche: str = "", geo: str = "", channel: str = "",
              audience: str = "", tone: str = "") -> dict:
    conn = _db()
    try:
        conn.execute(
            "INSERT INTO prefs (token, niche, geo, channel, audience, tone, updated) "
            "VALUES (?,?,?,?,?,?,?) "
            "ON CONFLICT(token) DO UPDATE SET niche=excluded.niche, "
            "geo=excluded.geo, channel=excluded.channel, "
            "audience=excluded.audience, tone=excluded.tone, updated=excluded.updated",
            (token, niche, geo, channel, audience, tone, time.time()))
        conn.commit()
    finally:
        conn.close()
    return {"niche": niche, "geo": geo, "channel": channel,
            "audience": audience, "tone": tone}


# ── daily digest subscriptions ────────────────────────────────────────────────

def upsert_digest(email: str, token: str, niche: str, hour: int) -> None:
    conn = _db()
    try:
        conn.execute(
            "INSERT INTO digest_subs (email, token, niche, hour, created) "
            "VALUES (?,?,?,?,?) "
            "ON CONFLICT(email) DO UPDATE SET token=excluded.token, "
            "niche=excluded.niche, hour=excluded.hour",
            (email, token, niche, hour, time.time()))
        conn.commit()
    finally:
        conn.close()


def get_digest(email: str) -> dict | None:
    conn = _db()
    try:
        row = conn.execute("SELECT * FROM digest_subs WHERE email=?",
                           (email,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_digest(email: str) -> bool:
    conn = _db()
    try:
        cur = conn.execute("DELETE FROM digest_subs WHERE email=?", (email,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def digests_due(today: str, hour_now: int) -> list[dict]:
    """Subscriptions not yet sent today whose send hour has arrived.

    `hour <= hour_now` (not ==) so a brief that wasn't cached at 07:00 still
    goes out later the same day once one exists — a late digest beats none.
    """
    conn = _db()
    try:
        rows = conn.execute(
            "SELECT * FROM digest_subs WHERE last_sent != ? AND hour <= ?",
            (today, hour_now)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def mark_digest_sent(email: str, today: str) -> None:
    conn = _db()
    try:
        conn.execute("UPDATE digest_subs SET last_sent=? WHERE email=?",
                     (today, email))
        conn.commit()
    finally:
        conn.close()


# ── idea feedback ─────────────────────────────────────────────────────────────

def record_feedback(actor: str, niche: str, topic: str, vote: int) -> None:
    """Store a 👍/👎 (+1/-1). One vote per actor+niche+topic; re-voting updates."""
    conn = _db()
    try:
        n = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
        if n >= MAX_FEEDBACK_ROWS:
            # Cap total feedback: drop the oldest tenth rather than refuse —
            # recent votes are the ones that inform ranking.
            conn.execute(
                "DELETE FROM feedback WHERE rowid IN "
                "(SELECT rowid FROM feedback ORDER BY created ASC LIMIT ?)",
                (MAX_FEEDBACK_ROWS // 10,))
        conn.execute(
            "INSERT INTO feedback (actor, niche, topic, vote, created) "
            "VALUES (?,?,?,?,?) "
            "ON CONFLICT(actor, niche, topic) DO UPDATE SET vote=excluded.vote, "
            "created=excluded.created",
            (actor, niche, topic, vote, time.time()))
        conn.commit()
    finally:
        conn.close()


def feedback_summary(niche: str, limit: int = 50) -> list[dict]:
    """Aggregate votes per topic for a niche, most-voted first."""
    conn = _db()
    try:
        rows = conn.execute(
            "SELECT topic, SUM(vote) AS score, COUNT(*) AS votes FROM feedback "
            "WHERE niche=? GROUP BY topic ORDER BY votes DESC LIMIT ?",
            (niche, limit)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ── founder stats ─────────────────────────────────────────────────────────────

def counts() -> dict:
    conn = _db()
    try:
        def one(sql: str) -> int:
            try:
                return conn.execute(sql).fetchone()[0]
            except sqlite3.OperationalError:   # table not created yet
                return 0
        return {
            "users": one("SELECT COUNT(*) FROM users"),
            "pro_users": one("SELECT COUNT(*) FROM users "
                             "WHERE plan='pro' AND status='active'"),
            "saves": one("SELECT COUNT(*) FROM saves"),
            "digest_subs": one("SELECT COUNT(*) FROM digest_subs"),
            "feedback": one("SELECT COUNT(*) FROM feedback"),
        }
    finally:
        conn.close()
