"""Time-series metrics for Spark: real view velocity + outlier score.

Two numbers the single-call API can't give us:

  * **Real velocity** — views gained per hour *right now*, from consecutive
    snapshots of the same video. A single API call only supports lifetime
    average (views ÷ age), which flatters old videos and hides today's risers.
  * **Outlier score** — a video's views ÷ its channel's median recent views.
    This is what separates "a big channel posted" from "this format is
    winning": 15x on a 2k-subscriber channel is a format signal, while 1.1x
    on MrBeast is just Tuesday.

Same design rules as the other spark_* modules: stdlib sqlite3 only, shares
the volume-backed database file, every write path capped, and every failure
degrades to None so the brief still renders. Quota-aware by construction —
channel medians cost 3 units per channel and are cached for a week.
"""
from __future__ import annotations

import os
import sqlite3
import statistics
import time
from pathlib import Path

import requests

_DB_PATH = Path(__file__).parent / "spark_users.db"

_YT = "https://www.googleapis.com/youtube/v3"
_TIMEOUT = 10

# A snapshot pair must straddle this gap for a velocity reading to be stable —
# closer together and rounding noise in viewCount dominates the delta.
MIN_SNAPSHOT_GAP_H = 0.5
# Beyond this, the pair is too stale to describe "right now".
MAX_SNAPSHOT_AGE_H = 72.0
# Videos are only tracked while they can still be a live signal.
SNAPSHOT_RETENTION_DAYS = 21
# Channel medians drift slowly; a week-old median is fine and saves quota.
CHANNEL_TTL_S = 7 * 86400
MEDIAN_SAMPLE = 15          # last N uploads define "normal" for a channel
MAX_SNAPSHOT_ROWS = 400_000


def _db() -> sqlite3.Connection:
    path = Path(os.getenv("SPARK_DB_PATH") or _DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS snapshots (
            video_id TEXT NOT NULL,
            at REAL NOT NULL,
            views INTEGER NOT NULL,
            PRIMARY KEY (video_id, at)
        );
        CREATE INDEX IF NOT EXISTS idx_snapshots_at ON snapshots(at);
        CREATE TABLE IF NOT EXISTS channels (
            channel_id TEXT PRIMARY KEY,
            title TEXT NOT NULL DEFAULT '',
            median_views REAL NOT NULL DEFAULT 0,
            sample_n INTEGER NOT NULL DEFAULT 0,
            refreshed REAL NOT NULL DEFAULT 0
        );
    """)
    return conn


# ── snapshots → real velocity ─────────────────────────────────────────────────

def record_snapshots(videos: list) -> int:
    """Store one (video_id, now, views) row per video. Returns rows written.

    Called on every brief run, so consecutive runs build the time series that
    makes real velocity possible. Never raises.
    """
    now = time.time()
    rows = [(getattr(v, "video_id", ""), now, int(getattr(v, "views", 0) or 0))
            for v in videos if getattr(v, "video_id", "")]
    if not rows:
        return 0
    try:
        conn = _db()
        try:
            conn.executemany(
                "INSERT OR REPLACE INTO snapshots (video_id, at, views) VALUES (?,?,?)",
                rows)
            # Prune on write so the volume can't grow without bound.
            conn.execute("DELETE FROM snapshots WHERE at < ?",
                         (now - SNAPSHOT_RETENTION_DAYS * 86400,))
            if conn.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0] > MAX_SNAPSHOT_ROWS:
                conn.execute(
                    "DELETE FROM snapshots WHERE at < "
                    "(SELECT MIN(at) FROM (SELECT at FROM snapshots "
                    " ORDER BY at DESC LIMIT ?))", (MAX_SNAPSHOT_ROWS // 2,))
            conn.commit()
            return len(rows)
        finally:
            conn.close()
    except sqlite3.Error:
        return 0


def measured_velocity(video_id: str, current_views: int) -> float | None:
    """Views/hour measured between the newest usable prior snapshot and now.

    None when there's no prior snapshot old enough — the caller then falls back
    to the lifetime average, so the feed works on day one and sharpens as the
    history fills in.
    """
    if not video_id:
        return None
    now = time.time()
    try:
        conn = _db()
        try:
            row = conn.execute(
                "SELECT at, views FROM snapshots WHERE video_id=? AND at<=? AND at>=? "
                "ORDER BY at DESC LIMIT 1",
                (video_id, now - MIN_SNAPSHOT_GAP_H * 3600,
                 now - MAX_SNAPSHOT_AGE_H * 3600)).fetchone()
        finally:
            conn.close()
    except sqlite3.Error:
        return None
    if not row:
        return None
    hours = (now - row["at"]) / 3600.0
    if hours <= 0:
        return None
    delta = int(current_views) - int(row["views"])
    if delta < 0:          # view counts can be revised down; not a signal
        return None
    return delta / hours


# ── channel medians → outlier score ───────────────────────────────────────────

def _fetch_channel_median(channel_id: str, api_key: str) -> tuple[float, int] | None:
    """(median_views, sample_n) over the channel's last MEDIAN_SAMPLE uploads.

    3 quota units: channels.list → uploads playlist, playlistItems.list → ids,
    videos.list → their view counts.
    """
    try:
        c = requests.get(f"{_YT}/channels", params={
            "key": api_key, "id": channel_id, "part": "contentDetails"},
            timeout=_TIMEOUT)
        c.raise_for_status()
        items = c.json().get("items") or []
        if not items:
            return None
        uploads = (items[0].get("contentDetails", {})
                   .get("relatedPlaylists", {}).get("uploads"))
        if not uploads:
            return None

        p = requests.get(f"{_YT}/playlistItems", params={
            "key": api_key, "playlistId": uploads, "part": "contentDetails",
            "maxResults": MEDIAN_SAMPLE}, timeout=_TIMEOUT)
        p.raise_for_status()
        ids = [it.get("contentDetails", {}).get("videoId")
               for it in (p.json().get("items") or [])]
        ids = [i for i in ids if i]
        if not ids:
            return None

        v = requests.get(f"{_YT}/videos", params={
            "key": api_key, "id": ",".join(ids), "part": "statistics"},
            timeout=_TIMEOUT)
        v.raise_for_status()
        views = [int((it.get("statistics", {}) or {}).get("viewCount", 0) or 0)
                 for it in (v.json().get("items") or [])]
        views = [n for n in views if n > 0]
        if len(views) < 3:     # too thin to call anything "normal"
            return None
        return float(statistics.median(views)), len(views)
    except (requests.RequestException, ValueError, KeyError, TypeError,
            statistics.StatisticsError):
        return None


def channel_medians(channel_ids: list[str], api_key: str,
                    max_fetches: int = 40) -> dict[str, float]:
    """Median recent views per channel, cached for a week.

    max_fetches bounds quota spend per brief run (3 units each); channels that
    miss the cutoff simply have no outlier score this run and get picked up on
    a later run.
    """
    wanted = [c for c in dict.fromkeys(channel_ids) if c]
    if not wanted:
        return {}
    out: dict[str, float] = {}
    stale: list[str] = []
    now = time.time()
    try:
        conn = _db()
        try:
            marks = ",".join("?" * len(wanted))
            rows = conn.execute(
                f"SELECT channel_id, median_views, refreshed FROM channels "
                f"WHERE channel_id IN ({marks})", wanted).fetchall()
            cached = {r["channel_id"]: r for r in rows}
            for cid in wanted:
                r = cached.get(cid)
                if r and now - r["refreshed"] < CHANNEL_TTL_S and r["median_views"] > 0:
                    out[cid] = r["median_views"]
                else:
                    stale.append(cid)
        finally:
            conn.close()
    except sqlite3.Error:
        stale = wanted

    if not api_key or not stale:
        return out

    fetched: list[tuple[str, float, int, float]] = []
    for cid in stale[:max_fetches]:
        got = _fetch_channel_median(cid, api_key)
        if got:
            median, n = got
            out[cid] = median
            fetched.append((cid, median, n, now))
    if fetched:
        try:
            conn = _db()
            try:
                conn.executemany(
                    "INSERT INTO channels (channel_id, median_views, sample_n, refreshed) "
                    "VALUES (?,?,?,?) ON CONFLICT(channel_id) DO UPDATE SET "
                    "median_views=excluded.median_views, sample_n=excluded.sample_n, "
                    "refreshed=excluded.refreshed",
                    [(cid, m, n, ts) for cid, m, n, ts in fetched])
                conn.commit()
            finally:
                conn.close()
        except sqlite3.Error:
            pass
    return out


def outlier_score(views: int, channel_median: float | None) -> float | None:
    """views ÷ channel median. None when the median is unknown/unusable."""
    if not channel_median or channel_median <= 0:
        return None
    return float(views) / float(channel_median)


# ── the provider the trend engine consumes ────────────────────────────────────

class MetricsProvider:
    """Adapter passed into the pipeline so `trend_engine` stays dependency-free.

    Holds one run's worth of state: it records snapshots, resolves channel
    medians in a single batch, and then answers per-video questions.
    """

    def __init__(self, api_key: str = "", enabled: bool = True):
        self.api_key = api_key
        self.enabled = enabled
        self._medians: dict[str, float] = {}

    def observe(self, videos: list) -> None:
        """Record this run's snapshots and batch-resolve channel medians."""
        if not self.enabled or not videos:
            return
        record_snapshots(videos)
        self._medians = channel_medians(
            [getattr(v, "channel_id", "") for v in videos], self.api_key)

    def velocity(self, video) -> float | None:
        if not self.enabled:
            return None
        return measured_velocity(getattr(video, "video_id", ""),
                                 int(getattr(video, "views", 0) or 0))

    def outlier(self, video) -> float | None:
        if not self.enabled:
            return None
        return outlier_score(int(getattr(video, "views", 0) or 0),
                             self._medians.get(getattr(video, "channel_id", "")))
