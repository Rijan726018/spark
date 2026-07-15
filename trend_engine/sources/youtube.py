"""YouTube Data API v3 source — needs a free API key (env: YOUTUBE_API_KEY).

This is the niche workhorse: for each niche query we pull recently-published
videos ordered by view count, then fetch statistics to compute a velocity
(views per hour since publish). High-velocity recent videos tell a creator
exactly which angles/formats are catching fire *right now* in their lane.

Degrades gracefully: with no key it returns [] and logs a one-line note, so the
rest of the pipeline (Google Trends) still produces a digest.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import requests

from ..models import VideoItem

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


def _scrub(err: Exception, api_key: str) -> str:
    """Error messages can embed the request URL — never log the API key."""
    return str(err).replace(api_key, "***") if api_key else str(err)


def _age_hours(published_iso: str) -> float:
    try:
        pub = datetime.fromisoformat(published_iso.replace("Z", "+00:00"))
    except ValueError:
        return 24.0
    delta = datetime.now(timezone.utc) - pub
    return max(delta.total_seconds() / 3600.0, 0.5)


def search_videos(query: str, api_key: str, days: int = 7, max_results: int = 12,
                  region: str = "US", timeout: int = 10) -> list[VideoItem]:
    """Return recent high-view videos for `query`. [] if no key or on error."""
    if not api_key:
        return []
    published_after = (
        datetime.now(timezone.utc) - timedelta(days=days)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        s = requests.get(SEARCH_URL, params={
            "key": api_key, "q": query, "part": "snippet", "type": "video",
            "order": "viewCount", "maxResults": min(max_results, 50),
            "publishedAfter": published_after, "regionCode": region,
            "relevanceLanguage": "en",
        }, timeout=timeout)
        s.raise_for_status()
        search = s.json()
    except requests.RequestException as e:  # pragma: no cover - network
        print(f"[youtube] search failed for {query!r}: {_scrub(e, api_key)}")
        return []

    ids = [it["id"]["videoId"] for it in search.get("items", []) if it.get("id", {}).get("videoId")]
    if not ids:
        return []

    try:
        v = requests.get(VIDEOS_URL, params={
            "key": api_key, "id": ",".join(ids), "part": "snippet,statistics",
        }, timeout=timeout)
        v.raise_for_status()
        details = v.json()
    except requests.RequestException as e:  # pragma: no cover - network
        print(f"[youtube] details failed for {query!r}: {_scrub(e, api_key)}")
        return []

    out: list[VideoItem] = []
    for it in details.get("items", []):
        snip = it.get("snippet", {})
        stats = it.get("statistics", {})
        vid = it.get("id", "")
        out.append(VideoItem(
            video_id=vid,
            title=snip.get("title", "").strip(),
            channel=snip.get("channelTitle", "").strip(),
            views=int(stats.get("viewCount", 0) or 0),
            age_hours=_age_hours(snip.get("publishedAt", "")),
            query=query,
            url=f"https://www.youtube.com/watch?v={vid}",
        ))
    return out


def collect(queries: list[str], api_key: str, days: int = 7,
            max_results: int = 12, region: str = "US",
            timeout: int = 10) -> list[VideoItem]:
    """Run every niche query and flatten the results."""
    if not api_key:
        print("[youtube] no YOUTUBE_API_KEY set — skipping YouTube signal. "
              "Get a free key at https://console.cloud.google.com (enable 'YouTube Data API v3').")
        return []
    videos: list[VideoItem] = []
    for q in queries:
        videos.extend(search_videos(q, api_key, days, max_results, region, timeout))
    return videos
