"""
Session Manager — trading session definitions and scheduling.

All session times are US/Eastern. Overnight sessions (e.g. Asian 18:00–03:00)
that cross midnight are handled correctly.

Usage:
    from engines.session import is_in_session, is_in_any_session, get_active_sessions
    from engines.session import seconds_until_session, get_session_info, filter_df_to_session

    if is_in_session("ny"):
        print("NY session is active.")

    active = get_active_sessions()
    df_ny = filter_df_to_session(df, "ny")
"""

from __future__ import annotations

import logging
from datetime import datetime, time, timedelta
from typing import Optional

import pandas as pd
import pytz

logger = logging.getLogger(__name__)

TZ = "America/New_York"
_EASTERN = pytz.timezone(TZ)

# ---------------------------------------------------------------------------
# Session definitions — all times in US/Eastern
# ---------------------------------------------------------------------------
SESSIONS: dict[str, dict] = {
    "asian": {
        "name":  "Asian Session",
        "start": "18:00",
        "end":   "03:00",   # overnight — crosses midnight
    },
    "london": {
        "name":  "London Session",
        "start": "03:00",
        "end":   "12:00",
    },
    "ny": {
        "name":  "NY Session",
        "start": "09:30",
        "end":   "16:00",
    },
    "ny_open": {
        "name":  "NY Open",
        "start": "09:30",
        "end":   "11:30",
    },
    "ny_close": {
        "name":  "NY Close",
        "start": "14:00",
        "end":   "16:30",
    },
    "globex": {
        "name":  "Globex (24hr)",
        "start": "00:00",
        "end":   "23:59",
    },
    "custom": {
        "name":  "Custom",
        "start": "09:30",
        "end":   "16:00",
    },
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_hhmm(t_str: str) -> time:
    """Parse an "HH:MM" string into a datetime.time object."""
    h, m = t_str.split(":")
    return time(int(h), int(m))


def _to_eastern(dt: Optional[datetime]) -> datetime:
    """
    Convert *dt* to US/Eastern. If dt is None, return now() in Eastern.
    Naive datetimes are assumed to be UTC.
    """
    if dt is None:
        return datetime.now(tz=_EASTERN)
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(_EASTERN)


def _time_in_range(start: time, end: time, current: time) -> bool:
    """
    Return True if *current* falls within [start, end).
    Handles overnight ranges where end < start (e.g. 18:00–03:00).
    """
    if start <= end:
        return start <= current < end
    # Overnight: in-session if after start OR before end
    return current >= start or current < end


def _seconds_between(t1: time, t2: time) -> int:
    """Return seconds from time t1 to time t2 (next occurrence, positive)."""
    d1 = timedelta(hours=t1.hour, minutes=t1.minute, seconds=t1.second)
    d2 = timedelta(hours=t2.hour, minutes=t2.minute, seconds=t2.second)
    delta = (d2 - d1).total_seconds()
    if delta < 0:
        delta += 86400  # wrap to next day
    return int(delta)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_in_session(session_key: str, dt: Optional[datetime] = None) -> bool:
    """
    Return True if *dt* (defaults to now ET) falls within the named session.

    Overnight sessions that cross midnight (e.g. Asian 18:00–03:00) are
    handled correctly.

    Args:
        session_key: One of the keys defined in SESSIONS.
        dt:          Timezone-aware or naïve datetime; naïve treated as UTC.
                     Defaults to current time in US/Eastern.

    Returns:
        bool — True if within session window, False otherwise (incl. unknown key).
    """
    session = SESSIONS.get(session_key)
    if session is None:
        logger.warning("is_in_session: unknown session key %r", session_key)
        return False
    try:
        local_dt = _to_eastern(dt)
        current  = local_dt.time().replace(second=0, microsecond=0)
        start    = _parse_hhmm(session["start"])
        end      = _parse_hhmm(session["end"])
        return _time_in_range(start, end, current)
    except Exception as exc:
        logger.error("is_in_session(%r) error: %s", session_key, exc)
        return False


def is_in_any_session(session_keys: list[str], dt: Optional[datetime] = None) -> bool:
    """
    Return True if *dt* falls within ANY of the listed sessions.

    Args:
        session_keys: List of session key strings.
        dt:           Datetime to check; defaults to now ET.

    Returns:
        bool
    """
    return any(is_in_session(k, dt) for k in session_keys)


def get_active_sessions(dt: Optional[datetime] = None) -> list[str]:
    """
    Return a list of session keys that are currently active.

    Args:
        dt: Datetime to check; defaults to now ET.

    Returns:
        List of active session key strings (may be empty).
    """
    return [k for k in SESSIONS if is_in_session(k, dt)]


def seconds_until_session(session_key: str, dt: Optional[datetime] = None) -> int:
    """
    Return the number of whole seconds until the named session next opens.
    Returns 0 if the session is already active.

    Args:
        session_key: One of the keys in SESSIONS.
        dt:          Reference datetime; defaults to now ET.

    Returns:
        int >= 0. Returns 0 for unknown keys (and logs a warning).
    """
    session = SESSIONS.get(session_key)
    if session is None:
        logger.warning("seconds_until_session: unknown session key %r", session_key)
        return 0

    try:
        local_dt = _to_eastern(dt)

        if is_in_session(session_key, local_dt):
            return 0

        start      = _parse_hhmm(session["start"])
        today      = local_dt.date()
        next_start = _EASTERN.localize(datetime.combine(today, start))

        # If that start time has already passed today, try tomorrow
        if next_start <= local_dt:
            next_start = _EASTERN.localize(
                datetime.combine(today + timedelta(days=1), start)
            )

        return max(0, int((next_start - local_dt).total_seconds()))

    except Exception as exc:
        logger.error("seconds_until_session(%r) error: %s", session_key, exc)
        return 0


def get_session_info(session_key: str, dt: Optional[datetime] = None) -> dict:
    """
    Return a rich info dict for a single session.

    Returns:
        {
            name:               str  — human-readable name
            start:              str  — "HH:MM"
            end:                str  — "HH:MM"
            active:             bool — whether the session is currently open
            opens_in_seconds:   int  — seconds until session opens (0 if active)
            closes_in_seconds:  int  — seconds until session closes (0 if not active)
        }
        Empty dict if session_key is unknown.
    """
    session = SESSIONS.get(session_key)
    if session is None:
        logger.warning("get_session_info: unknown session key %r", session_key)
        return {}

    try:
        local_dt = _to_eastern(dt)
        active   = is_in_session(session_key, local_dt)
        opens_in = 0 if active else seconds_until_session(session_key, local_dt)

        # Calculate seconds until session closes
        closes_in = 0
        if active:
            end   = _parse_hhmm(session["end"])
            today = local_dt.date()
            next_end = _EASTERN.localize(datetime.combine(today, end))
            if next_end <= local_dt:
                # Overnight session: end time is tomorrow
                next_end = _EASTERN.localize(
                    datetime.combine(today + timedelta(days=1), end)
                )
            closes_in = max(0, int((next_end - local_dt).total_seconds()))

        return {
            "name":              session["name"],
            "start":             session["start"],
            "end":               session["end"],
            "active":            active,
            "opens_in_seconds":  opens_in,
            "closes_in_seconds": closes_in,
        }

    except Exception as exc:
        logger.error("get_session_info(%r) error: %s", session_key, exc)
        return {}


def get_all_session_info(dt: Optional[datetime] = None) -> dict[str, dict]:
    """
    Return info dicts for all sessions.

    Args:
        dt: Reference datetime; defaults to now ET.

    Returns:
        {session_key: info_dict} for all keys in SESSIONS.
    """
    return {k: get_session_info(k, dt) for k in SESSIONS}


def filter_df_to_session(df: pd.DataFrame, session_key: str) -> pd.DataFrame:
    """
    Filter a tz-aware DatetimeIndex DataFrame to rows within the named session.

    The DataFrame index must be timezone-aware (or will be treated as UTC).

    Args:
        df:          DataFrame with a tz-aware DatetimeIndex.
        session_key: Session key string from SESSIONS.

    Returns:
        Filtered DataFrame (copy). May be empty.

    Raises:
        KeyError: if session_key is not in SESSIONS.
    """
    if session_key not in SESSIONS:
        raise KeyError(
            f"Unknown session key: {session_key!r}. Valid keys: {list(SESSIONS)}"
        )

    if df.empty:
        return df.copy()

    session = SESSIONS[session_key]
    start   = _parse_hhmm(session["start"])
    end     = _parse_hhmm(session["end"])

    def _in_session(ts: pd.Timestamp) -> bool:
        try:
            if ts.tzinfo is None:
                ts = ts.tz_localize("UTC")
            local_t = ts.astimezone(_EASTERN).time().replace(second=0, microsecond=0)
            return _time_in_range(start, end, local_t)
        except Exception:
            return False

    mask = df.index.map(_in_session)
    return df.loc[mask].copy()
