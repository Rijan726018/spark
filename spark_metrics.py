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
import re
import sqlite3
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


def _parse_duration(iso: str) -> int:
    """ISO-8601 duration → seconds (handles the day component and 'P0D')."""
    m = re.match(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$",
                 (iso or "").strip())
    if not m:
        return 0
    d, h, mi, s = (int(g or 0) for g in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s

_DB_PATH = Path(__file__).parent / "spark_users.db"

_YT = "https://www.googleapis.com/youtube/v3"
_TIMEOUT = 5          # these are extra calls inside a request handler — fail fast
_SESSION = requests.Session()   # connection reuse: 3 calls per channel, up to 40

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
# A median over fewer than this many uploads is noise, not "normal".
MIN_SAMPLE_N = 5
# Below this the score is shrunk toward 1.0 rather than trusted outright.
TRUSTED_SAMPLE_N = 10
# Shorts accumulate views far faster than long-form, so they are never
# compared against each other — bucketed by this duration boundary.
SHORT_MAX_S = 60


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
        CREATE TABLE IF NOT EXISTS channel_rates (
            channel_id TEXT PRIMARY KEY,
            median_vel_short REAL NOT NULL DEFAULT 0,
            n_short INTEGER NOT NULL DEFAULT 0,
            median_vel_long REAL NOT NULL DEFAULT 0,
            n_long INTEGER NOT NULL DEFAULT 0,
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
    if delta == 0 and hours < 2:
        # YouTube's public viewCount advances in coarse, cached steps, so a
        # zero delta over a short window means "no reading yet", NOT "this
        # video is dead". Reporting 0.0 would bury a genuine riser.
        return None
    return delta / hours


# ── channel medians → outlier score ───────────────────────────────────────────

class QuotaExhausted(Exception):
    """The API key is out of quota — stop making calls for this run."""


def _age_hours(published_iso: str) -> float:
    try:
        pub = datetime.fromisoformat((published_iso or "").replace("Z", "+00:00"))
    except ValueError:
        return 0.0
    return max((datetime.now(timezone.utc) - pub).total_seconds() / 3600.0, 1.0)


def _get(path: str, params: dict, api_key: str) -> dict:
    r = _SESSION.get(f"{_YT}/{path}", params=params, timeout=_TIMEOUT)
    if r.status_code == 403:
        reason = ""
        try:
            reason = ((r.json().get("error", {}).get("errors") or [{}])[0]
                      .get("reason", ""))
        except ValueError:
            pass
        if "quota" in reason.lower():
            raise QuotaExhausted(reason)
    r.raise_for_status()
    return r.json()


def _fetch_channel_rates(channel_id: str, api_key: str) -> dict | None:
    """Median views-per-hour of the channel's recent uploads, split by format.

    Returns {"short": (median_vel, n), "long": (median_vel, n)}.

    Velocity — not raw views — because the videos we score are hours old while
    a channel's back catalogue is fully matured; comparing raw counts would
    make every fresh video look like an underperformer. Bucketed by duration
    because Shorts and long-form accumulate views at completely different rates.

    3 quota units: channels.list → uploads playlist, playlistItems.list → ids,
    videos.list → stats + duration + publish time.
    """
    try:
        items = _get("channels", {"key": api_key, "id": channel_id,
                                  "part": "contentDetails"}, api_key).get("items") or []
        if not items:
            return None
        uploads = (items[0].get("contentDetails", {})
                   .get("relatedPlaylists", {}).get("uploads"))
        if not uploads:
            return None

        pl = _get("playlistItems", {
            "key": api_key, "playlistId": uploads, "part": "contentDetails",
            "maxResults": MEDIAN_SAMPLE}, api_key)
        ids = [it.get("contentDetails", {}).get("videoId")
               for it in (pl.get("items") or [])]
        ids = [i for i in ids if i]
        if not ids:
            return None

        vids = _get("videos", {
            "key": api_key, "id": ",".join(ids),
            "part": "statistics,contentDetails,snippet"}, api_key)

        short: list[float] = []
        long_: list[float] = []
        for it in (vids.get("items") or []):
            views = int((it.get("statistics", {}) or {}).get("viewCount", 0) or 0)
            if views <= 0:
                continue
            age = _age_hours((it.get("snippet", {}) or {}).get("publishedAt", ""))
            if age <= 0:
                continue
            dur = _parse_duration((it.get("contentDetails", {}) or {})
                                  .get("duration", ""))
            (short if 0 < dur <= SHORT_MAX_S else long_).append(views / age)

        out: dict = {}
        if short:
            out["short"] = (float(statistics.median(short)), len(short))
        if long_:
            out["long"] = (float(statistics.median(long_)), len(long_))
        return out or None
    except QuotaExhausted:
        raise
    except (requests.RequestException, ValueError, KeyError, TypeError,
            statistics.StatisticsError):
        return None


def channel_rates(channel_ids: list[str], api_key: str,
                  max_fetches: int = 40) -> dict[str, dict]:
    """Per-channel median upload velocity by format, cached for a week.

    Returns {channel_id: {"short": (vel, n), "long": (vel, n)}}. max_fetches
    bounds quota AND latency per run (3 calls each); channels past the cutoff
    simply have no outlier score this run and get picked up on a later one.
    A jittered TTL keeps a whole cohort of channels from expiring together.
    """
    wanted = [c for c in dict.fromkeys(channel_ids) if c]
    if not wanted:
        return {}
    out: dict[str, dict] = {}
    stale: list[str] = []
    now = time.time()
    try:
        conn = _db()
        try:
            marks = ",".join("?" * len(wanted))
            rows = conn.execute(
                f"SELECT * FROM channel_rates WHERE channel_id IN ({marks})",
                wanted).fetchall()
            cached = {r["channel_id"]: r for r in rows}
            for cid in wanted:
                r = cached.get(cid)
                # Jitter (±12.5%) derived from the id so refreshes spread out
                # instead of stampeding on the same day every week.
                ttl = CHANNEL_TTL_S * (0.875 + 0.25 * ((hash(cid) % 1000) / 1000.0))
                if r and now - r["refreshed"] < ttl:
                    got = {}
                    if r["median_vel_short"] > 0:
                        got["short"] = (r["median_vel_short"], r["n_short"])
                    if r["median_vel_long"] > 0:
                        got["long"] = (r["median_vel_long"], r["n_long"])
                    if got:
                        out[cid] = got
                        continue
                stale.append(cid)
        finally:
            conn.close()
    except sqlite3.Error:
        stale = wanted

    if not api_key or not stale:
        return out

    fetched = []
    for cid in stale[:max_fetches]:
        try:
            got = _fetch_channel_rates(cid, api_key)
        except QuotaExhausted as e:
            # Every remaining call would fail the same way — stop burning
            # latency, and make it visible instead of silently degrading.
            print(f"[metrics] YouTube quota exhausted ({e}) — "
                  f"skipping {len(stale) - len(fetched)} channel lookups")
            break
        if got:
            out[cid] = got
            s = got.get("short", (0.0, 0))
            l = got.get("long", (0.0, 0))
            fetched.append((cid, s[0], s[1], l[0], l[1], now))
    if fetched:
        try:
            conn = _db()
            try:
                conn.executemany(
                    "INSERT INTO channel_rates (channel_id, median_vel_short, "
                    "n_short, median_vel_long, n_long, refreshed) VALUES (?,?,?,?,?,?) "
                    "ON CONFLICT(channel_id) DO UPDATE SET "
                    "median_vel_short=excluded.median_vel_short, n_short=excluded.n_short, "
                    "median_vel_long=excluded.median_vel_long, n_long=excluded.n_long, "
                    "refreshed=excluded.refreshed", fetched)
                conn.commit()
            finally:
                conn.close()
        except sqlite3.Error:
            pass
    return out


def outlier_score(velocity: float, rates: dict | None, is_short: bool) -> float | None:
    """This video's views/hr ÷ its channel's median views/hr for the same format.

    Both sides are rates, so a 6-hour-old video is compared fairly against a
    mature back catalogue. None when there's no comparable, large-enough
    sample — a wrong number here is worse than no number.
    """
    if not rates or velocity <= 0:
        return None
    bucket = rates.get("short" if is_short else "long")
    if not bucket:
        return None                     # no same-format history to compare against
    median_vel, n = bucket
    if not median_vel or median_vel <= 0 or n < MIN_SAMPLE_N:
        return None
    raw = float(velocity) / float(median_vel)
    if n < TRUSTED_SAMPLE_N:
        # Thin sample: shrink toward 1.0 so a 6-upload channel can't mint a
        # 12x claim off noise.
        weight = (n - MIN_SAMPLE_N) / float(TRUSTED_SAMPLE_N - MIN_SAMPLE_N)
        raw = 1.0 + (raw - 1.0) * weight
    return raw


# ── the provider the trend engine consumes ────────────────────────────────────

class MetricsProvider:
    """Adapter passed into the pipeline so `trend_engine` stays dependency-free.

    Holds one run's worth of state: it records snapshots, resolves channel
    medians in a single batch, and then answers per-video questions.
    """

    def __init__(self, api_key: str = "", enabled: bool = True):
        self.api_key = api_key
        self.enabled = enabled
        self._rates: dict[str, dict] = {}

    def observe(self, videos: list) -> None:
        """Record this run's snapshots and batch-resolve channel rates."""
        if not self.enabled or not videos:
            return
        record_snapshots(videos)
        self._rates = channel_rates(
            [getattr(v, "channel_id", "") for v in videos], self.api_key)

    def velocity(self, video) -> float | None:
        if not self.enabled:
            return None
        return measured_velocity(getattr(video, "video_id", ""),
                                 int(getattr(video, "views", 0) or 0))

    def outlier(self, video) -> float | None:
        if not self.enabled:
            return None
        # Compare like with like: this video's rate against its channel's
        # median rate for the same format.
        dur = int(getattr(video, "duration_s", 0) or 0)
        is_short = 0 < dur <= SHORT_MAX_S
        return outlier_score(getattr(video, "lifetime_velocity", 0.0),
                             self._rates.get(getattr(video, "channel_id", "")),
                             is_short)
