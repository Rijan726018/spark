"""Spark API — serves the mobile PWA, runs the trend engine, handles billing.

Run:
    uvicorn trend_api:app --port 8100

Plans:
    free — today's cached brief per niche (one shared engine run/day/niche).
    pro  — force-fresh regeneration, LLM polish, personalized ideas.
With no Stripe keys configured the server runs in DEV MODE: everyone is pro
and "Upgrade" simulates a purchase. Paste STRIPE_* keys in .env to go live.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import sys
import threading
import time
from datetime import date, datetime
from pathlib import Path

from fastapi import FastAPI, Header, Query, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import spark_analyze
import spark_billing as billing
import spark_email
import spark_expand
import spark_store
from trend_engine.config import NICHE_PRESETS, Settings
from trend_engine.llm import llm_provider
from trend_engine.pipeline import run

BASE = Path(__file__).parent
MOBILE = BASE / "mobile"
# SPARK_CACHE_DIR points the brief cache at the deploy volume so cached briefs
# survive redeploys (free-plan serving depends on them).
CACHE_DIR = Path(os.getenv("SPARK_CACHE_DIR") or BASE / "brief_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL_SECONDS = 6 * 3600          # refresh shared brief at most 4x/day
MAX_NICHE_LEN = 60                    # resolve_niche() turns any string into live queries

app = FastAPI(title="Spark API", version="1.0.0")

_mem_cache: dict[str, dict] = {}


@app.on_event("startup")
def _billing_config_guard() -> None:
    """Refuse to boot half-configured: ANY partial Stripe config is an error.
    Missing webhook secret = cancellations never downgrade; missing price/secret
    = silent dev mode where a public server gives Pro away free. Only all-three
    (live) or none (dev) are valid states."""
    configured = {
        "STRIPE_SECRET_KEY": bool(billing.stripe_secret()),
        "STRIPE_PRICE_ID": bool(billing.stripe_price_id()),
        "STRIPE_WEBHOOK_SECRET": bool(billing.webhook_secret()),
    }
    if any(configured.values()) and not all(configured.values()):
        missing = ", ".join(k for k, v in configured.items() if not v)
        raise RuntimeError(
            f"Stripe is partially configured — missing: {missing}. "
            "Set all three of STRIPE_SECRET_KEY, STRIPE_PRICE_ID, "
            "STRIPE_WEBHOOK_SECRET to go live, or none of them for dev mode. "
            "Refusing to boot: a half-configured server either gives Pro away "
            "free or never downgrades churned customers.")
    if not all(configured.values()):
        print("=" * 74, file=sys.stderr)
        print("SPARK DEV MODE — Stripe keys not configured: EVERYONE GETS PRO, "
              "checkout is simulated.\nDo NOT expose this server publicly. "
              "Set STRIPE_SECRET_KEY, STRIPE_PRICE_ID, STRIPE_WEBHOOK_SECRET "
              "to go live.", file=sys.stderr)
        print("=" * 74, file=sys.stderr)


class Profile(BaseModel):
    channel: str = Field(default="", max_length=300)
    audience: str = Field(default="", max_length=200)
    tone: str = Field(default="", max_length=60)


class BriefRequest(BaseModel):
    niche: str = "fitness"
    top: int = Field(default=12, ge=1, le=25)
    refresh: bool = False
    geo: str = ""                     # 2-letter country code; Pro for non-default
    profile: Profile | None = None


_GEO_RE = re.compile(r"^[A-Za-z]{2}$")


def _auth_token(authorization: str) -> str:
    return authorization.removeprefix("Bearer ").strip()


# ── cache ─────────────────────────────────────────────────────────────────────

def _cache_key(niche: str, geo: str) -> str:
    return f"{niche}:{geo}:{date.today().isoformat()}"


def _cache_path(key: str) -> Path:
    return CACHE_DIR / (key.replace(":", "_").replace("/", "_") + ".json")


def _cache_get(key: str, max_age: float = CACHE_TTL_SECONDS) -> dict | None:
    entry = _mem_cache.get(key)
    if entry and time.time() - entry["at"] < max_age:
        return entry["data"]
    p = _cache_path(key)
    if p.exists() and time.time() - p.stat().st_mtime < max_age:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            _mem_cache[key] = {"at": p.stat().st_mtime, "data": data}
            return data
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _cache_put(key: str, data: dict) -> None:
    # Never clobber a richer brief with a degraded one (e.g. a run made while
    # the YouTube quota is exhausted returns few or zero videos).
    old = _cache_get(key)
    if old and (old.get("counts", {}).get("videos", 0)
                > data.get("counts", {}).get("videos", 0)):
        return
    _mem_cache[key] = {"at": time.time(), "data": data}
    try:
        _cache_path(key).write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass


# ── abuse protection ──────────────────────────────────────────────────────────
# The open API spends real money (YouTube quota + LLM calls). Three caps:
#   1. per-IP token bucket on the spending routes,
#   2. free/anon users locked to preset niches (arbitrary strings = live queries),
#   3. per-cache-key generation lock so concurrent misses run the engine once.

RATE_LIMIT_PER_MIN = int(os.getenv("SPARK_RATE_LIMIT_PER_MIN", "30"))

_rl_guard = threading.Lock()
_rl_buckets: dict[str, tuple[float, float]] = {}   # ip -> (tokens, last_ts)


def _client_ip(request: Request) -> str:
    # Fly's proxy sets Fly-Client-IP; direct/local connections fall back to peer.
    ip = (request.headers.get("fly-client-ip", "").strip()
          or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
          or (request.client.host if request.client else "unknown"))
    if ":" in ip:   # bucket IPv6 by /64 — rotating within a prefix is free
        ip = ":".join(ip.split(":")[:4]) + "::/64"
    return ip


def _rate_limited(ip: str) -> bool:
    now = time.time()
    with _rl_guard:
        if len(_rl_buckets) > 5000:   # prune idle IPs so the dict can't grow unbounded
            cutoff = now - 600
            for stale in [k for k, (_, ts) in _rl_buckets.items() if ts < cutoff]:
                del _rl_buckets[stale]
        tokens, last = _rl_buckets.get(ip, (float(RATE_LIMIT_PER_MIN), now))
        tokens = min(float(RATE_LIMIT_PER_MIN),
                     tokens + (now - last) * RATE_LIMIT_PER_MIN / 60.0)
        if tokens < 1.0:
            _rl_buckets[ip] = (tokens, now)
            return True
        _rl_buckets[ip] = (tokens - 1.0, now)
        return False


def _rate_limit_response() -> JSONResponse:
    return JSONResponse({"error": "Too many requests — try again in a minute."},
                        status_code=429, headers={"Retry-After": "60"})


_gen_guard = threading.Lock()
_gen_locks: dict[str, threading.Lock] = {}


def _gen_lock(key: str) -> threading.Lock:
    with _gen_guard:
        if len(_gen_locks) > 2048:
            # Keys embed the date, so anything not from today can never be
            # re-requested; today's keys are never pruned (a handed-out lock
            # being evicted would mint a duplicate and re-enable the stampede).
            today = date.today().isoformat()
            for stale in [k for k, l in _gen_locks.items()
                          if not k.endswith(today) and not l.locked()]:
                del _gen_locks[stale]
        return _gen_locks.setdefault(key, threading.Lock())


# The rate limit is best-effort (IP rotation defeats any per-IP cap); the hard
# ceiling on founder spend is a global daily budget of engine runs. One fitness
# run ≈ 1,200 YouTube quota units, so the free 10k/day quota supports ~8 rich
# runs; cached briefs keep serving after the budget is gone.
DAILY_RUN_BUDGET = int(os.getenv("SPARK_DAILY_RUN_BUDGET", "10"))

_budget_guard = threading.Lock()
_run_counts: dict[str, int] = {}   # iso date -> engine runs today


def _try_reserve_run() -> bool:
    today = date.today().isoformat()
    with _budget_guard:
        for old in [d for d in _run_counts if d != today]:
            del _run_counts[old]
        if _run_counts.get(today, 0) >= DAILY_RUN_BUDGET:
            return False
        _run_counts[today] = _run_counts.get(today, 0) + 1
        return True


def _budget_response() -> JSONResponse:
    return JSONResponse(
        {"error": "Today's fresh-brief capacity is used up. Cached briefs "
                  "still work — try a preset niche, or come back tomorrow."},
        status_code=503, headers={"Retry-After": "3600"})


# Idea expansion is LLM-only spend (no YouTube quota), so it gets its own,
# larger daily budget.
DAILY_EXPAND_BUDGET = int(os.getenv("SPARK_DAILY_EXPAND_BUDGET", "200"))

_expand_counts: dict[str, int] = {}   # iso date -> expansions today


def _try_reserve_expand() -> bool:
    today = date.today().isoformat()
    with _budget_guard:
        for old in [d for d in _expand_counts if d != today]:
            del _expand_counts[old]
        if _expand_counts.get(today, 0) >= DAILY_EXPAND_BUDGET:
            return False
        _expand_counts[today] = _expand_counts.get(today, 0) + 1
        return True


# Deep video analysis spends a Supadata transcript credit + a (vision) LLM
# call per uncached video, so it gets its own daily budget.
DAILY_ANALYZE_BUDGET = int(os.getenv("SPARK_DAILY_ANALYZE_BUDGET", "40"))

_analyze_counts: dict[str, int] = {}   # iso date -> analyses today


def _try_reserve_analyze() -> bool:
    today = date.today().isoformat()
    with _budget_guard:
        for old in [d for d in _analyze_counts if d != today]:
            del _analyze_counts[old]
        if _analyze_counts.get(today, 0) >= DAILY_ANALYZE_BUDGET:
            return False
        _analyze_counts[today] = _analyze_counts.get(today, 0) + 1
        return True


def _release_analyze() -> None:
    """Give a reserved slot back when the analysis produced nothing and spent
    nothing (bad/dead video id, YouTube outage)."""
    today = date.today().isoformat()
    with _budget_guard:
        if _analyze_counts.get(today, 0) > 0:
            _analyze_counts[today] -= 1


# ── engine ────────────────────────────────────────────────────────────────────

def _run_brief(niche: str, top: int, profile: dict | None, use_llm: bool,
               geo: str = "") -> dict:
    settings = Settings.from_env()
    if geo:
        settings.geo = geo
    result = run(niche, settings=settings, top=top, use_llm=use_llm, profile=profile)
    return {
        "niche": result["niche"],
        "date": result["date"],
        "counts": result["counts"],
        "ideas": [i.to_dict() for i in result["ideas"]],
        "signals": [o.to_dict() for o in result["opportunities"][:20]],
        "has_youtube": bool(settings.youtube_api_key),
        "llm_used": result.get("llm_used", False),
    }


def _user_hash(token: str, profile: dict | None) -> str:
    """Stable per-user+profile cache suffix; changing the profile invalidates it."""
    raw = token + "|" + json.dumps(profile or {}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _brief_response(req: BriefRequest, token: str) -> JSONResponse:
    plan = billing.effective_plan(token)
    settings = Settings.from_env()

    # Canonicalize BEFORE the gate, the cache key, and the gen lock all use it:
    # resolve_niche() lowercases anyway, and a case-variant ("Fitness") must not
    # become a separate cache key — that would turn each variant into a fresh
    # engine run and let anonymous users burn the whole YouTube quota.
    niche = req.niche.strip().lower()
    if not niche or len(niche) > MAX_NICHE_LEN or not re.fullmatch(
            r"[a-z0-9][a-z0-9 &+\-'.]*", niche):
        return JSONResponse(
            {"error": f"Niche must be 1-{MAX_NICHE_LEN} letters, numbers, "
                      "spaces, or &+-'. characters."},
            status_code=422)
    # Free/anon users get preset niches only: any other string becomes live
    # YouTube queries (~100 quota units each) plus a founder-paid LLM call.
    if plan != "pro" and niche not in NICHE_PRESETS:
        return JSONResponse(
            {"error": "Custom niches are a Pro feature. Free plan includes: "
                      + ", ".join(NICHE_PRESETS) + "."},
            status_code=403)

    profile = req.profile.model_dump() if req.profile else None
    # Pro users with saved preferences get them applied automatically: an
    # explicit inline profile always wins, saved prefs fill the gap.
    prefs = spark_store.get_prefs(token) if plan == "pro" and token else None
    if not (profile and any(profile.values())) and prefs:
        profile = {k: prefs.get(k, "") for k in ("channel", "audience", "tone")}

    geo = req.geo.strip().upper()
    if geo and not _GEO_RE.match(geo):
        return JSONResponse({"error": "geo must be a 2-letter country code."},
                            status_code=422)
    if not geo and prefs and prefs.get("geo"):
        geo = prefs["geo"]
    if not geo:
        geo = settings.geo
    # A non-default geo is fresh engine spend per country — Pro only, like
    # custom niches.
    if plan != "pro" and geo != settings.geo:
        return JSONResponse({"error": "Region selection is a Pro feature."},
                            status_code=403)

    has_profile = bool(profile and any(profile.values()))
    personalized = plan == "pro" and has_profile

    key = _cache_key(niche, geo)

    if personalized or (plan == "pro" and req.refresh):
        # Personalized briefs are cached per user+profile for the day, so a
        # Pro user re-opening the app doesn't burn an engine run each time.
        ukey = key + ":u" + _user_hash(token, profile) if personalized else key
        data = None if req.refresh else (_cache_get(ukey) if personalized else None)
        if data is None and _try_reserve_run():
            data = _run_brief(niche, req.top, profile if personalized else None,
                              use_llm=True, geo=geo)
            # Cache under the user key (personalized) or update the shared
            # brief (forced refresh).
            _cache_put(ukey, data)
        if data is None:
            data = _cache_get(key, max_age=86400)   # same-day key: any age today
            if data is None:
                return _budget_response()
            personalized = False
    else:
        data = _cache_get(key)
        if data is None:
            # One engine run per key: concurrent cache misses (launch-day spike)
            # queue briefly instead of stampeding the quota — but never park a
            # threadpool thread for a whole 10-30s engine run.
            lock = _gen_lock(key)
            if not lock.acquire(timeout=5):
                return JSONResponse(
                    {"error": "This brief is being generated — try again in a "
                              "few seconds."},
                    status_code=503, headers={"Retry-After": "15"})
            try:
                data = _cache_get(key)
                if data is None:
                    if not _try_reserve_run():
                        data = _cache_get(key, max_age=86400)
                        if data is None:
                            return _budget_response()
                    else:
                        data = _run_brief(niche, req.top, None, use_llm=True,
                                          geo=geo)
                        _cache_put(key, data)
            finally:
                lock.release()

    return JSONResponse({
        **data,
        "plan": plan,
        "geo": geo,
        "dev_mode": not billing.live_mode(),
        "personalized": personalized,
        "llm_available": bool(llm_provider()),
    })


# ── routes ────────────────────────────────────────────────────────────────────

@app.get("/healthz")
async def healthz() -> JSONResponse:
    # async: served straight off the event loop, so Fly health checks stay
    # green even when engine runs have the threadpool saturated.
    return JSONResponse({"ok": True})


@app.get("/api/niches")
def niches() -> JSONResponse:
    return JSONResponse({"niches": list(NICHE_PRESETS.keys())})


@app.post("/api/brief")
def brief_post(req: BriefRequest, request: Request,
               authorization: str = Header(default="")) -> JSONResponse:
    if _rate_limited(_client_ip(request)):
        return _rate_limit_response()
    token = _auth_token(authorization)
    return _brief_response(req, token)


@app.get("/api/brief")
def brief_get(request: Request,
              niche: str = Query("fitness"), top: int = Query(12, ge=1, le=25),
              authorization: str = Header(default="")) -> JSONResponse:
    """GET kept for the CLI / curl convenience; same behavior as POST without profile."""
    if _rate_limited(_client_ip(request)):
        return _rate_limit_response()
    token = _auth_token(authorization)
    return _brief_response(BriefRequest(niche=niche, top=top), token)


@app.get("/api/me")
def me(authorization: str = Header(default="")) -> JSONResponse:
    token = _auth_token(authorization)
    user = billing.user_by_token(token)
    return JSONResponse({
        "plan": billing.effective_plan(token),
        "email": user["email"] if user else "",
        "dev_mode": not billing.live_mode(),
        "llm_available": bool(llm_provider()),
    })


class CheckoutRequest(BaseModel):
    email: str


@app.post("/api/checkout")
def checkout(req: CheckoutRequest, request: Request) -> JSONResponse:
    if _rate_limited(_client_ip(request)):
        return _rate_limit_response()
    email = req.email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        return JSONResponse({"error": "Enter a valid email."}, status_code=400)
    origin = str(request.base_url).rstrip("/")
    try:
        out = billing.create_checkout_session(
            email,
            success_url=f"{origin}/api/billing/success",
            cancel_url=origin,
        )
    except Exception as e:  # surface Stripe errors readably
        return JSONResponse({"error": f"Checkout failed: {e}"}, status_code=502)
    return JSONResponse(out)


@app.get("/api/billing/success")
def billing_success(session_id: str = Query("")):
    """Stripe redirects here after payment; we verify and hand the app its token."""
    token = billing.confirm_checkout_session(session_id) if session_id else None
    # Return to the app with the token in the URL fragment (never logged server-side).
    dest = f"/#token={token}" if token else "/#billing=failed"
    return JSONResponse(status_code=307, headers={"Location": dest}, content={})


@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request) -> JSONResponse:
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    if not billing.verify_webhook(payload, sig):
        return JSONResponse({"error": "bad signature"}, status_code=400)
    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        return JSONResponse({"error": "bad payload"}, status_code=400)
    billing.handle_webhook_event(event)
    return JSONResponse({"received": True})


class RecoverRequest(BaseModel):
    email: str


@app.post("/api/token/recover")
def recover_token(req: RecoverRequest, request: Request) -> JSONResponse:
    """Re-email an existing token (cleared browser data, new phone, etc.).

    The response is identical whether or not the email has an account, so this
    endpoint can't be used to enumerate customers. Rate-limited like the other
    spending routes because each hit can trigger an outbound email.
    """
    if _rate_limited(_client_ip(request)):
        return _rate_limit_response()
    email = req.email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        return JSONResponse({"error": "Enter a valid email."}, status_code=400)
    user = billing.user_by_email(email)
    if user:
        spark_email.send_token_email(email, user["token"])
    return JSONResponse({"ok": True,
                         "message": "If that email has an account, the token is on its way."})


# ── billing portal ────────────────────────────────────────────────────────────

@app.post("/api/billing/portal")
def billing_portal(request: Request,
                   authorization: str = Header(default="")) -> JSONResponse:
    """Stripe Billing Portal link: update card, see invoices, cancel — self-serve."""
    if _rate_limited(_client_ip(request)):
        return _rate_limit_response()
    token = _auth_token(authorization)
    if not token:
        return JSONResponse({"error": "Sign in with your Pro token first."},
                            status_code=401)
    try:
        out = billing.create_portal_session(
            token, return_url=str(request.base_url).rstrip("/"))
    except Exception as e:
        return JSONResponse({"error": f"Portal failed: {e}"}, status_code=502)
    if "error" in out:
        return JSONResponse(out, status_code=400)
    return JSONResponse(out)


# ── brief history + export ───────────────────────────────────────────────────
# Both read the on-disk cache only — no engine spend, safe for every plan.

_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})\.json$")


def _valid_niche(niche: str) -> str | None:
    niche = niche.strip().lower()
    if niche and len(niche) <= MAX_NICHE_LEN and re.fullmatch(
            r"[a-z0-9][a-z0-9 &+\-'.]*", niche):
        return niche
    return None


@app.get("/api/history")
def history(niche: str = Query("fitness"), geo: str = Query("")) -> JSONResponse:
    """Dates that have a cached brief for this niche, newest first."""
    n = _valid_niche(niche)
    if n is None:
        return JSONResponse({"error": "Invalid niche."}, status_code=422)
    g = geo.strip().upper() or Settings.from_env().geo
    if not _GEO_RE.match(g):
        return JSONResponse({"error": "Invalid geo."}, status_code=422)
    dates = []
    for p in CACHE_DIR.glob(f"{n}_{g}_*.json"):
        m = _DATE_RE.search(p.name)
        if m:
            dates.append(m.group(1))
    return JSONResponse({"niche": n, "geo": g,
                         "dates": sorted(dates, reverse=True)[:60]})


def _archived_brief(niche: str, geo: str, day: str) -> dict | None:
    p = _cache_path(f"{niche}:{geo}:{day}")
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


@app.get("/api/brief/archive")
def brief_archive(niche: str = Query("fitness"), date_: str = Query("", alias="date"),
                  geo: str = Query("")) -> JSONResponse:
    """A past day's cached brief (default: today's, any age)."""
    n = _valid_niche(niche)
    if n is None:
        return JSONResponse({"error": "Invalid niche."}, status_code=422)
    g = geo.strip().upper() or Settings.from_env().geo
    day = date_.strip() or date.today().isoformat()
    if not _GEO_RE.match(g) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        return JSONResponse({"error": "Invalid geo or date."}, status_code=422)
    data = _archived_brief(n, g, day)
    if data is None:
        return JSONResponse({"error": f"No cached brief for {n} on {day}."},
                            status_code=404)
    return JSONResponse({**data, "archived": True})


def _brief_markdown(data: dict) -> str:
    lines = [f"# Spark Brief — {str(data.get('niche', '')).title()} — "
             f"{data.get('date', '')}", ""]
    for i, idea in enumerate(data.get("ideas", []), 1):
        titles = idea.get("titles") or [idea.get("topic", "")]
        lines.append(f"## {i}. {titles[0]}")
        lines.append(f"- **Momentum:** {idea.get('score', 0):.0f}/100 · "
                     f"**Format:** {idea.get('format', '')}")
        if idea.get("why_now"):
            lines.append(f"- **Why now:** {idea['why_now']}")
        if idea.get("hook"):
            lines.append(f"- **Hook:** {idea['hook']}")
        if len(titles) > 1:
            lines.append("- **Title options:**")
            lines += [f"    - {t}" for t in titles]
        if idea.get("outline"):
            lines.append("- **Outline:**")
            lines += [f"    - {step}" for step in idea["outline"]]
        if idea.get("source_url"):
            lines.append(f"- **Reference:** {idea['source_url']} "
                         f"({idea.get('source_stat', '')})")
        lines.append("")
    return "\n".join(lines)


@app.get("/api/brief.md")
def brief_markdown(niche: str = Query("fitness"), date_: str = Query("", alias="date"),
                   geo: str = Query("")) -> PlainTextResponse:
    """A cached brief as Markdown — paste straight into Notion/Obsidian."""
    n = _valid_niche(niche)
    g = geo.strip().upper() or Settings.from_env().geo
    day = date_.strip() or date.today().isoformat()
    if n is None or not _GEO_RE.match(g) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        return PlainTextResponse("Invalid niche, geo, or date.", status_code=422)
    data = _archived_brief(n, g, day)
    if data is None:
        return PlainTextResponse(f"No cached brief for {n} on {day}.",
                                 status_code=404)
    return PlainTextResponse(_brief_markdown(data), media_type="text/markdown")


# ── idea expansion (Pro) ──────────────────────────────────────────────────────

class ExpandRequest(BaseModel):
    niche: str = "fitness"
    idea: dict


@app.post("/api/expand")
def expand(req: ExpandRequest, request: Request,
           authorization: str = Header(default="")) -> JSONResponse:
    """Turn one brief idea into a full shooting script (beats, b-roll,
    description, hashtags). Pro-only: each call can be an LLM request."""
    if _rate_limited(_client_ip(request)):
        return _rate_limit_response()
    token = _auth_token(authorization)
    if billing.effective_plan(token) != "pro":
        return JSONResponse({"error": "Full scripts are a Pro feature."},
                            status_code=403)
    niche = _valid_niche(req.niche)
    if niche is None:
        return JSONResponse({"error": "Invalid niche."}, status_code=422)
    try:
        raw = json.dumps(req.idea)
    except (TypeError, ValueError):
        return JSONResponse({"error": "Invalid idea payload."}, status_code=422)
    if not str(req.idea.get("topic", "")).strip() or len(raw) > 6000:
        return JSONResponse({"error": "Send one idea object from /api/brief."},
                            status_code=422)
    if not _try_reserve_expand():
        return JSONResponse(
            {"error": "Today's script capacity is used up — try again tomorrow."},
            status_code=503, headers={"Retry-After": "3600"})
    prefs = spark_store.get_prefs(token) if token else None
    profile = ({k: prefs.get(k, "") for k in ("channel", "audience", "tone")}
               if prefs else None)
    script = spark_expand.expand_idea(req.idea, niche, profile=profile)
    return JSONResponse({"niche": niche, "script": script})


# ── deep video analysis (Pro) ─────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    video: str = Field(..., max_length=200)   # YouTube URL or 11-char video id
    niche: str = "fitness"


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest, request: Request,
            authorization: str = Header(default="")) -> JSONResponse:
    """Why is this exact video working — hook, structure, title/thumbnail
    formula, audience read, and how to make your version. Pro-only: each
    uncached call spends a transcript credit + a vision LLM request."""
    if _rate_limited(_client_ip(request)):
        return _rate_limit_response()
    token = _auth_token(authorization)
    if billing.effective_plan(token) != "pro":
        return JSONResponse({"error": "Video breakdowns are a Pro feature."},
                            status_code=403)
    niche = _valid_niche(req.niche)
    if niche is None:
        return JSONResponse({"error": "Invalid niche."}, status_code=422)
    vid = spark_analyze.video_id_from(req.video)
    if vid is None:
        return JSONResponse({"error": "Send a YouTube video URL or id."},
                            status_code=422)
    if not os.getenv("YOUTUBE_API_KEY", "").strip():
        return JSONResponse({"error": "Video analysis needs the YouTube API "
                                      "configured on the server."},
                            status_code=503)

    # One analysis per video+niche per day; an analysis barely changes
    # intraday, and the cache is what makes launch-day traffic affordable.
    key = f"analysis:{vid}:{niche}:{date.today().isoformat()}"
    cached = _cache_get(key, max_age=86400)
    if cached is not None:
        return JSONResponse({**cached, "cached": True})

    # One generation per video+niche: without this, every Pro user tapping the
    # same card during the 15-45s pipeline spends their own transcript credit
    # and vision call, and a slow failing racer can overwrite a good analysis.
    lock = _gen_lock(key)
    if not lock.acquire(timeout=8):
        return JSONResponse(
            {"error": "This breakdown is being generated — try again in a few "
                      "seconds."},
            status_code=503, headers={"Retry-After": "10"})
    try:
        cached = _cache_get(key, max_age=86400)
        if cached is not None:
            return JSONResponse({**cached, "cached": True})

        if not _try_reserve_analyze():
            return JSONResponse(
                {"error": "Today's video-analysis capacity is used up — try "
                          "again tomorrow."},
                status_code=503, headers={"Retry-After": "3600"})
        try:
            result = spark_analyze.analyze_video(vid, niche)
        except Exception as e:                      # never 500 on a paid route
            print(f"[analyze] {vid}: {e}")
            result = None
        if result is None:
            # Nothing was produced and nothing was spent (the pipeline stops at
            # metadata) — a dead link must not burn the day's capacity.
            _release_analyze()
            return JSONResponse({"error": "Couldn't fetch that video — check "
                                          "the link and try again."},
                                status_code=404)
        # A template analysis while an LLM IS configured means the provider
        # failed: serve it, keep the budget (a transcript credit was spent),
        # but never cache it — otherwise one blip serves a stub all day.
        if result["analysis"].get("llm_used") or not llm_provider():
            _cache_put(key, result)
        return JSONResponse(result)
    finally:
        lock.release()


# ── saved ideas (requires an account token) ──────────────────────────────────

def _require_user(authorization: str) -> tuple[str, dict] | JSONResponse:
    token = _auth_token(authorization)
    user = billing.user_by_token(token)
    if not user:
        return JSONResponse(
            {"error": "This needs an account — upgrade to Pro (or use the dev "
                      "checkout) to get a token."}, status_code=401)
    return token, user


class SaveRequest(BaseModel):
    niche: str = ""
    idea: dict


@app.post("/api/saves")
def save_idea(req: SaveRequest, request: Request,
              authorization: str = Header(default="")) -> JSONResponse:
    if _rate_limited(_client_ip(request)):
        return _rate_limit_response()
    auth = _require_user(authorization)
    if isinstance(auth, JSONResponse):
        return auth
    token, _ = auth
    try:
        raw = json.dumps(req.idea)
    except (TypeError, ValueError):
        return JSONResponse({"error": "Invalid idea payload."}, status_code=422)
    if not str(req.idea.get("topic", "")).strip() or len(raw) > 6000:
        return JSONResponse({"error": "Send one idea object from /api/brief."},
                            status_code=422)
    out = spark_store.save_idea(token, req.niche.strip().lower()[:MAX_NICHE_LEN],
                                req.idea)
    if not out["saved"]:
        return JSONResponse({"error": "Saved-ideas limit reached — delete a few "
                                      "before saving more."}, status_code=409)
    return JSONResponse(out)


@app.get("/api/saves")
def get_saves(authorization: str = Header(default="")) -> JSONResponse:
    auth = _require_user(authorization)
    if isinstance(auth, JSONResponse):
        return auth
    token, _ = auth
    return JSONResponse({"saves": spark_store.list_saves(token)})


@app.delete("/api/saves/{save_id}")
def delete_save(save_id: int,
                authorization: str = Header(default="")) -> JSONResponse:
    auth = _require_user(authorization)
    if isinstance(auth, JSONResponse):
        return auth
    token, _ = auth
    if not spark_store.delete_save(token, save_id):
        return JSONResponse({"error": "Not found."}, status_code=404)
    return JSONResponse({"ok": True})


# ── preferences ───────────────────────────────────────────────────────────────

class PrefsRequest(BaseModel):
    niche: str = Field(default="", max_length=MAX_NICHE_LEN)
    geo: str = Field(default="", max_length=2)
    channel: str = Field(default="", max_length=300)
    audience: str = Field(default="", max_length=200)
    tone: str = Field(default="", max_length=60)


@app.get("/api/prefs")
def get_prefs(authorization: str = Header(default="")) -> JSONResponse:
    auth = _require_user(authorization)
    if isinstance(auth, JSONResponse):
        return auth
    token, _ = auth
    prefs = spark_store.get_prefs(token) or {}
    return JSONResponse({k: prefs.get(k, "") for k in
                         ("niche", "geo", "channel", "audience", "tone")})


@app.put("/api/prefs")
def put_prefs(req: PrefsRequest, request: Request,
              authorization: str = Header(default="")) -> JSONResponse:
    """Save default niche/region + creator profile. Once saved, every brief is
    personalized automatically — no need to resend the profile per request."""
    if _rate_limited(_client_ip(request)):
        return _rate_limit_response()
    auth = _require_user(authorization)
    if isinstance(auth, JSONResponse):
        return auth
    token, _ = auth
    niche = req.niche.strip().lower()
    if niche and _valid_niche(niche) is None:
        return JSONResponse({"error": "Invalid niche."}, status_code=422)
    geo = req.geo.strip().upper()
    if geo and not _GEO_RE.match(geo):
        return JSONResponse({"error": "geo must be a 2-letter country code."},
                            status_code=422)
    out = spark_store.set_prefs(token, niche=niche, geo=geo,
                                channel=req.channel.strip(),
                                audience=req.audience.strip(),
                                tone=req.tone.strip())
    return JSONResponse(out)


# ── daily email digest (Pro) ──────────────────────────────────────────────────

class DigestRequest(BaseModel):
    niche: str = "fitness"
    hour: int = Field(default=7, ge=0, le=23)   # server time (UTC on Fly)


@app.get("/api/digest")
def get_digest(authorization: str = Header(default="")) -> JSONResponse:
    auth = _require_user(authorization)
    if isinstance(auth, JSONResponse):
        return auth
    _, user = auth
    sub = spark_store.get_digest(user["email"])
    return JSONResponse({"subscribed": sub is not None,
                         "niche": sub["niche"] if sub else "",
                         "hour": sub["hour"] if sub else 7,
                         "email_configured": spark_email.email_configured()})


@app.post("/api/digest")
def subscribe_digest(req: DigestRequest, request: Request,
                     authorization: str = Header(default="")) -> JSONResponse:
    """Subscribe the account's own email to a daily brief. Pro-only (digests
    can trigger engine runs), and only ever sends to the verified paying email."""
    if _rate_limited(_client_ip(request)):
        return _rate_limit_response()
    auth = _require_user(authorization)
    if isinstance(auth, JSONResponse):
        return auth
    token, user = auth
    if billing.effective_plan(token) != "pro":
        return JSONResponse({"error": "The daily email digest is a Pro feature."},
                            status_code=403)
    niche = _valid_niche(req.niche)
    if niche is None:
        return JSONResponse({"error": "Invalid niche."}, status_code=422)
    spark_store.upsert_digest(user["email"], token, niche, req.hour)
    return JSONResponse({"ok": True, "niche": niche, "hour": req.hour,
                         "email": user["email"],
                         "email_configured": spark_email.email_configured()})


@app.delete("/api/digest")
def unsubscribe_digest(authorization: str = Header(default="")) -> JSONResponse:
    auth = _require_user(authorization)
    if isinstance(auth, JSONResponse):
        return auth
    _, user = auth
    spark_store.delete_digest(user["email"])
    return JSONResponse({"ok": True})


DIGEST_CHECK_SECONDS = 300
_digest_thread: threading.Thread | None = None


def _digest_tick(now: datetime | None = None) -> int:
    """Send every due digest. Returns how many were sent. Runs on the scheduler
    thread; separated so tests can drive it directly with a fake clock."""
    now = now or datetime.now()
    today = now.date().isoformat()
    sent = 0
    for sub in spark_store.digests_due(today, now.hour):
        if billing.effective_plan(sub["token"]) != "pro":
            continue   # churned — stop sending; row stays in case they return
        key = _cache_key(sub["niche"], Settings.from_env().geo)
        data = _cache_get(key, max_age=86400)
        if data is None and _try_reserve_run():
            # A paying subscriber's morning brief is worth an engine run.
            try:
                data = _run_brief(sub["niche"], 12, None, use_llm=True)
                _cache_put(key, data)
            except Exception as e:
                print(f"[digest] engine run for {sub['niche']} failed: {e}",
                      file=sys.stderr)
        if not data or not data.get("ideas"):
            continue   # nothing to send — retry on a later tick today
        if spark_email.send_digest_email(sub["email"], sub["niche"],
                                         data.get("date", today), data["ideas"]):
            spark_store.mark_digest_sent(sub["email"], today)
            sent += 1
    return sent


def _digest_loop() -> None:
    while True:
        time.sleep(DIGEST_CHECK_SECONDS)
        try:
            _digest_tick()
        except Exception as e:   # the scheduler must survive anything
            print(f"[digest] tick failed: {e}", file=sys.stderr)


@app.on_event("startup")
def _start_digest_scheduler() -> None:
    global _digest_thread
    if not spark_email.email_configured():
        return   # no provider configured — nothing would ever send
    if _digest_thread is None or not _digest_thread.is_alive():
        _digest_thread = threading.Thread(target=_digest_loop, daemon=True,
                                          name="spark-digest")
        _digest_thread.start()


# ── idea feedback ─────────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    niche: str = "fitness"
    topic: str = Field(min_length=1, max_length=200)
    vote: int


@app.post("/api/feedback")
def feedback(req: FeedbackRequest, request: Request,
             authorization: str = Header(default="")) -> JSONResponse:
    """👍/👎 an idea. One vote per user (or IP) per topic; re-voting updates."""
    if _rate_limited(_client_ip(request)):
        return _rate_limit_response()
    if req.vote not in (-1, 1):
        return JSONResponse({"error": "vote must be 1 or -1."}, status_code=422)
    niche = _valid_niche(req.niche)
    if niche is None:
        return JSONResponse({"error": "Invalid niche."}, status_code=422)
    token = _auth_token(authorization)
    actor = token if billing.user_by_token(token) else "ip:" + _client_ip(request)
    spark_store.record_feedback(actor, niche, req.topic.strip(), req.vote)
    return JSONResponse({"ok": True})


# ── founder/admin stats ───────────────────────────────────────────────────────

@app.get("/api/admin/stats")
def admin_stats(x_admin_token: str = Header(default="")) -> JSONResponse:
    """Operational counters. Enabled only when SPARK_ADMIN_TOKEN is set; the
    route 404s otherwise so it doesn't advertise itself."""
    expected = os.getenv("SPARK_ADMIN_TOKEN", "").strip()
    if not expected or not hmac.compare_digest(x_admin_token.encode(),
                                               expected.encode()):
        return JSONResponse({"error": "Not found."}, status_code=404)
    today = date.today().isoformat()
    return JSONResponse({
        **spark_store.counts(),
        "runs_today": _run_counts.get(today, 0),
        "run_budget": DAILY_RUN_BUDGET,
        "expansions_today": _expand_counts.get(today, 0),
        "expand_budget": DAILY_EXPAND_BUDGET,
        "cached_briefs": len(list(CACHE_DIR.glob("*.json"))),
        "live_mode": billing.live_mode(),
        "email_configured": spark_email.email_configured(),
    })


# ── PWA ───────────────────────────────────────────────────────────────────────

@app.get("/")
def index() -> FileResponse:
    return FileResponse(MOBILE / "index.html")


if MOBILE.exists():
    app.mount("/", StaticFiles(directory=str(MOBILE)), name="mobile")
