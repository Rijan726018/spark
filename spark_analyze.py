"""Deep video analysis for Spark Pro: why is this exact video working?

Four evidence streams for one YouTube video, one LLM synthesis:
  * metadata + stats — YouTube Data API videos.list (1 quota unit)
  * top comments    — commentThreads.list (1 unit; comments can be disabled)
  * transcript      — Supadata API (optional; SUPADATA_API_KEY, 1 credit/video)
  * thumbnail       — public i.ytimg.com CDN, sent to the LLM as an image

Same rules as the sibling modules: zero new dependencies, fail soft at every
layer. Each evidence stream that drops out lowers confidence instead of
failing the call, and with no LLM key the endpoint still returns a
stats-grounded template. The caller budgets these (LLM + Supadata spend).
"""
from __future__ import annotations

import base64
import json
import os
import re

import requests

from trend_engine.llm import llm_provider

_TIMEOUT = 20
_YT_API = "https://www.googleapis.com/youtube/v3"
_SUPADATA_API = "https://api.supadata.ai/v1/youtube/transcript"

_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
# Host-anchored: a bare "?v=<11 chars>" on any other domain is not a YouTube
# link, and accepting it only produces a guaranteed-404 analysis attempt.
_YT_HOST = r"(?:www\.|m\.)?(?:youtube(?:-nocookie)?\.com|youtu\.be)"
_URL_PATTERNS = [
    re.compile(_YT_HOST + r"\S*[?&]v=([A-Za-z0-9_-]{11})"),
    re.compile(r"youtu\.be/([A-Za-z0-9_-]{11})"),
    re.compile(_YT_HOST + r"/(?:shorts|embed|live|v|watch)/([A-Za-z0-9_-]{11})"),
]

# Transcript budget for the prompt: the hook lives in the first minutes, the
# payoff/CTA in the last — keep both ends when a transcript runs long.
_TRANSCRIPT_HEAD = 7000
_TRANSCRIPT_TAIL = 1500


def video_id_from(video: str) -> str | None:
    """Accept a raw 11-char video id or any common YouTube URL form."""
    v = (video or "").strip()
    if _ID_RE.match(v):
        return v
    for pat in _URL_PATTERNS:
        m = pat.search(v)
        if m:
            return m.group(1)
    return None


def _yt_key() -> str:
    return os.getenv("YOUTUBE_API_KEY", "").strip()


def _supadata_key() -> str:
    return os.getenv("SUPADATA_API_KEY", "").strip()


def _parse_duration(iso: str) -> int:
    """ISO-8601 duration -> seconds. Handles the day component (P1DT2H, long
    livestreams) and returns 0 for the live-broadcast sentinel 'P0D'."""
    m = re.match(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$",
                 (iso or "").strip())
    if not m:
        return 0
    d, h, mi, s = (int(g or 0) for g in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def fetch_video_meta(video_id: str) -> dict | None:
    """videos.list snippet+statistics+contentDetails. None if not found/errored."""
    try:
        r = requests.get(
            f"{_YT_API}/videos",
            params={"part": "snippet,statistics,contentDetails", "id": video_id,
                    "key": _yt_key()},
            timeout=_TIMEOUT)
        r.raise_for_status()
        items = r.json().get("items") or []
        if not items:
            return None
        sn, st = items[0].get("snippet", {}), items[0].get("statistics", {})
        import datetime as _dt
        published = sn.get("publishedAt", "")
        age_hours = 0.0
        try:
            dt = _dt.datetime.fromisoformat(published.replace("Z", "+00:00"))
            age_hours = max(0.5, (_dt.datetime.now(_dt.timezone.utc) - dt)
                            .total_seconds() / 3600)
        except ValueError:
            pass
        views = int(st.get("viewCount", 0) or 0)
        return {
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "title": sn.get("title", ""),
            "channel": sn.get("channelTitle", ""),
            "description": (sn.get("description", "") or "")[:800],
            "tags": (sn.get("tags") or [])[:15],
            "published_at": published,
            "age_hours": round(age_hours, 1),
            "duration_s": _parse_duration(
                items[0].get("contentDetails", {}).get("duration", "")),
            "views": views,
            "likes": int(st.get("likeCount", 0) or 0),
            "comment_count": int(st.get("commentCount", 0) or 0),
            "views_per_hour": round(views / age_hours, 1) if age_hours else 0.0,
        }
    except (requests.RequestException, ValueError, KeyError):
        return None


def fetch_comments(video_id: str, max_n: int = 40) -> list[dict]:
    """Top comments by relevance. Empty list when disabled or errored."""
    try:
        r = requests.get(
            f"{_YT_API}/commentThreads",
            params={"part": "snippet", "videoId": video_id, "key": _yt_key(),
                    "order": "relevance", "maxResults": min(max_n, 100),
                    "textFormat": "plainText"},
            timeout=_TIMEOUT)
        if r.status_code == 403:
            # 403 is both "comments disabled" (expected, harmless) and
            # "quotaExceeded" (an outage worth seeing in the logs).
            try:
                reason = (r.json().get("error", {}).get("errors") or
                          [{}])[0].get("reason", "")
            except ValueError:
                reason = ""
            if reason and reason != "commentsDisabled":
                print(f"[analyze] commentThreads 403: {reason}")
            return []
        r.raise_for_status()
        out = []
        for item in r.json().get("items", []):
            top = (item.get("snippet", {}).get("topLevelComment", {})
                   .get("snippet", {}))
            text = (top.get("textDisplay", "") or "").strip()
            if text:
                out.append({"text": text[:300],
                            "likes": int(top.get("likeCount", 0) or 0)})
        return out[:max_n]
    except (requests.RequestException, ValueError):
        return []


def fetch_transcript(video_id: str) -> str | None:
    """Transcript text via Supadata. None when no key / no captions / errored."""
    key = _supadata_key()
    if not key:
        return None
    try:
        r = requests.get(
            _SUPADATA_API,
            params={"videoId": video_id, "text": "true"},
            headers={"x-api-key": key},
            timeout=_TIMEOUT + 10)
        if r.status_code != 200:
            return None
        content = r.json().get("content")
        if isinstance(content, list):   # segment mode fallback
            content = " ".join(str(seg.get("text", "")) for seg in content
                               if isinstance(seg, dict))
        if not isinstance(content, str):   # unexpected shape — degrade, don't crash
            return None
        text = content.strip()
        if not text:
            return None
        if len(text) > _TRANSCRIPT_HEAD + _TRANSCRIPT_TAIL:
            text = (text[:_TRANSCRIPT_HEAD] + "\n[... middle trimmed ...]\n"
                    + text[-_TRANSCRIPT_TAIL:])
        return text
    except (requests.RequestException, ValueError, AttributeError, TypeError):
        return None


def fetch_thumbnail_b64(video_id: str) -> str | None:
    """Highest-res thumbnail from the public CDN, base64 for the vision call."""
    for name in ("maxresdefault", "hqdefault"):
        try:
            r = requests.get(
                f"https://i.ytimg.com/vi/{video_id}/{name}.jpg",
                timeout=_TIMEOUT)
            if r.status_code == 200 and r.content and len(r.content) < 4_000_000:
                return base64.b64encode(r.content).decode()
        except requests.RequestException:
            pass
    return None


# ── LLM synthesis ─────────────────────────────────────────────────────────────

def _build_prompt(meta: dict, niche: str, transcript: str | None,
                  comments: list[dict], has_thumbnail: bool) -> str:
    evidence = [f"VIDEO METADATA:\n{json.dumps(meta, ensure_ascii=False)}"]
    if transcript:
        evidence.append(f"TRANSCRIPT (start and end):\n{transcript}")
    else:
        evidence.append("TRANSCRIPT: not available — do NOT invent quotes; "
                        "infer the hook only from title/thumbnail and say so.")
    if comments:
        top = sorted(comments, key=lambda c: -c["likes"])[:25]
        evidence.append("TOP COMMENTS (by likes):\n" + "\n".join(
            f"[{c['likes']} likes] {c['text']}" for c in top))
    else:
        evidence.append("COMMENTS: not available.")
    if has_thumbnail:
        evidence.append("THUMBNAIL: attached as the image above — analyze what "
                        "is actually in it.")
    return (
        "You are a short-form/YouTube growth analyst. A creator in the "
        f"'{niche}' niche wants to understand WHY this specific video is "
        "performing, grounded ONLY in the evidence below — never fabricate "
        "quotes, numbers, or visual details you cannot see.\n\n"
        + "\n\n".join(evidence) +
        "\n\nReturn ONLY valid JSON, one object with keys:\n"
        '  "verdict"        (one sentence: the single biggest reason this video works),\n'
        '  "hook"           ({"quote": the actual opening words if the transcript shows them, else your best inference marked "(inferred)", "why": 2-3 sentences on why it stops the scroll}),\n'
        '  "structure"      (array of {"t": rough timestamp, "beat": what happens} — the video\'s real beat structure, 4-8 beats; [] if no transcript),\n'
        '  "title_formula"  ({"pattern": the reusable title pattern, "why": one sentence}),\n'
        '  "thumbnail"      ({"elements": array of what is visually in it, "why": one sentence} — only from the attached image; null if none),\n'
        '  "audience"       ({"loved": 2-4 things commenters actually praise, "wanted": 1-3 things they ask for — the content gaps}),\n'
        '  "velocity"       (one sentence putting views_per_hour and age in context),\n'
        '  "steal_this"     (array of 3-5 concrete, specific instructions for making YOUR version in this niche without copying),\n'
        '  "confidence"     ("high" with transcript+comments, "medium" missing one, "low" metadata-only).'
    )


def _call_llm(prompt: str, image_b64: str | None) -> str | None:
    """Provider call with optional vision block. None on any failure."""
    provider = llm_provider()
    model = os.getenv("TREND_LLM_MODEL",
                      "claude-sonnet-4-5" if provider == "anthropic" else "gpt-4o-mini")
    try:
        if provider == "anthropic":
            content: list[dict] = []
            if image_b64:
                content.append({"type": "image", "source": {
                    "type": "base64", "media_type": "image/jpeg",
                    "data": image_b64}})
            content.append({"type": "text", "text": prompt})
            r = requests.post(
                os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
                + "/v1/messages",
                headers={"x-api-key": os.getenv("ANTHROPIC_API_KEY", "").strip(),
                         "anthropic-version": "2023-06-01",
                         "content-type": "application/json"},
                json={"model": model, "max_tokens": 2500,
                      "messages": [{"role": "user", "content": content}]},
                timeout=_TIMEOUT + 40)
            r.raise_for_status()
            return "".join(b.get("text", "") for b in r.json().get("content", []))
        if provider == "openai":
            content = [{"type": "text", "text": prompt}]
            if image_b64:
                content.insert(0, {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{image_b64}"}})
            r = requests.post(
                os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
                + "/chat/completions",
                headers={"Authorization":
                         f"Bearer {os.getenv('OPENAI_API_KEY', '').strip()}",
                         "content-type": "application/json"},
                json={"model": model, "max_completion_tokens": 2500,
                      "messages": [{"role": "user", "content": content}]},
                timeout=_TIMEOUT + 40)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except (requests.RequestException, KeyError, IndexError, ValueError) as e:
        print(f"[analyze] llm call failed: {e}")
    return None


def _extract_obj(text: str) -> dict | None:
    m = re.search(r"\{.*\}", (text or "").strip(), re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None


def _valid(analysis: dict) -> bool:
    return (bool(str(analysis.get("verdict", "")).strip())
            and isinstance(analysis.get("hook"), dict)
            and isinstance(analysis.get("steal_this"), list)
            and len(analysis["steal_this"]) >= 2)


def _template_analysis(meta: dict, transcript: str | None,
                       comments: list[dict]) -> dict:
    """No-LLM fallback: honest, stats-grounded, clearly limited."""
    vph = meta.get("views_per_hour", 0)
    first_words = ""
    if transcript:
        first_words = " ".join(transcript.split()[:25])
    top_comments = [c["text"] for c in
                    sorted(comments, key=lambda c: -c["likes"])[:3]]
    return {
        "verdict": (f"Earning ~{vph:,.0f} views/hour at {meta.get('age_hours', 0):.0f}h "
                    "old — momentum well above a typical upload; connect an LLM "
                    "key for the full breakdown."),
        "hook": {"quote": first_words or f"(no transcript) Title: {meta.get('title', '')}",
                 "why": "The opening seconds carry the click-through promise of "
                        "the title — study how fast it pays that promise off."},
        "structure": [],
        "title_formula": {"pattern": meta.get("title", ""),
                          "why": "Reverse-engineer the title's promise/curiosity split."},
        "thumbnail": None,
        "audience": {"loved": top_comments, "wanted": []},
        "velocity": f"{meta.get('views', 0):,} views in {meta.get('age_hours', 0):.0f} "
                    f"hours ≈ {vph:,.0f}/hr.",
        "steal_this": [
            "Open with the exact same promise the title makes — pay it off in "
            "the first 10 seconds.",
            "Match the format: "
            + ("Short (<60s)." if meta.get("duration_s", 0) <= 75
               else f"~{meta.get('duration_s', 0) // 60} minute video."),
            "Read the top comments and make the follow-up they're asking for.",
        ],
        "confidence": "low",
        "llm_used": False,
    }


def analyze_video(video: str, niche: str) -> dict | None:
    """Full analysis for one video. None only when the video itself is
    invalid/unfetchable; every other failure degrades gracefully."""
    vid = video_id_from(video)
    if not vid or not _yt_key():
        return None
    meta = fetch_video_meta(vid)
    if not meta:
        return None

    transcript = fetch_transcript(vid)
    comments = fetch_comments(vid)
    thumb = fetch_thumbnail_b64(vid)

    analysis = None
    if llm_provider():
        raw = _call_llm(_build_prompt(meta, niche, transcript, comments,
                                      has_thumbnail=bool(thumb)), thumb)
        analysis = _extract_obj(raw or "")
        if analysis is not None and _valid(analysis):
            analysis["llm_used"] = True
        else:
            analysis = None
    if analysis is None:
        analysis = _template_analysis(meta, transcript, comments)

    analysis["evidence"] = {
        "transcript": bool(transcript),
        "comments": bool(comments),
        "thumbnail": bool(thumb),
    }
    return {"video_id": vid, "niche": niche, "analysis": analysis,
            "meta": {k: meta[k] for k in
                     ("url", "title", "channel", "views", "views_per_hour",
                      "age_hours", "duration_s")}}
