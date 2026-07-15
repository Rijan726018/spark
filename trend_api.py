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

import json
import os
import re
import sys
import threading
import time
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Header, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import spark_billing as billing
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
    channel: str = ""
    audience: str = ""
    tone: str = ""


class BriefRequest(BaseModel):
    niche: str = "fitness"
    top: int = Field(default=12, ge=1, le=25)
    refresh: bool = False
    profile: Profile | None = None


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


# ── engine ────────────────────────────────────────────────────────────────────

def _run_brief(niche: str, top: int, profile: dict | None, use_llm: bool) -> dict:
    settings = Settings.from_env()
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
    has_profile = bool(profile and any(profile.values()))
    personalized = plan == "pro" and has_profile

    key = _cache_key(niche, settings.geo)

    if personalized or (plan == "pro" and req.refresh):
        # Pro + personalization/refresh runs the engine for this user — if the
        # daily budget allows; otherwise degrade to today's shared brief.
        if _try_reserve_run():
            data = _run_brief(niche, req.top, profile if personalized else None,
                              use_llm=True)
            if not personalized:
                _cache_put(key, data)   # a forced refresh updates the shared brief
        else:
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
                        data = _run_brief(niche, req.top, None, use_llm=True)
                        _cache_put(key, data)
            finally:
                lock.release()

    return JSONResponse({
        **data,
        "plan": plan,
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
    token = authorization.removeprefix("Bearer ").strip()
    return _brief_response(req, token)


@app.get("/api/brief")
def brief_get(request: Request,
              niche: str = Query("fitness"), top: int = Query(12, ge=1, le=25),
              authorization: str = Header(default="")) -> JSONResponse:
    """GET kept for the CLI / curl convenience; same behavior as POST without profile."""
    if _rate_limited(_client_ip(request)):
        return _rate_limit_response()
    token = authorization.removeprefix("Bearer ").strip()
    return _brief_response(BriefRequest(niche=niche, top=top), token)


@app.get("/api/me")
def me(authorization: str = Header(default="")) -> JSONResponse:
    token = authorization.removeprefix("Bearer ").strip()
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


# ── PWA ───────────────────────────────────────────────────────────────────────

@app.get("/")
def index() -> FileResponse:
    return FileResponse(MOBILE / "index.html")


if MOBILE.exists():
    app.mount("/", StaticFiles(directory=str(MOBILE)), name="mobile")
