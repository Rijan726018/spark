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
CACHE_DIR = BASE / "brief_cache"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL_SECONDS = 6 * 3600          # refresh shared brief at most 4x/day

app = FastAPI(title="Spark API", version="1.0.0")

_mem_cache: dict[str, dict] = {}


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


def _cache_get(key: str) -> dict | None:
    entry = _mem_cache.get(key)
    if entry and time.time() - entry["at"] < CACHE_TTL_SECONDS:
        return entry["data"]
    p = _cache_path(key)
    if p.exists() and time.time() - p.stat().st_mtime < CACHE_TTL_SECONDS:
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
    profile = req.profile.model_dump() if req.profile else None
    has_profile = bool(profile and any(profile.values()))
    personalized = plan == "pro" and has_profile

    key = _cache_key(req.niche, settings.geo)

    if personalized or (plan == "pro" and req.refresh):
        # Pro + personalization/refresh always runs the engine for this user.
        data = _run_brief(req.niche, req.top, profile if personalized else None,
                          use_llm=True)
        if not personalized:
            _cache_put(key, data)   # a forced refresh updates the shared brief too
    else:
        data = _cache_get(key)
        if data is None:
            data = _run_brief(req.niche, req.top, None, use_llm=True)
            _cache_put(key, data)

    return JSONResponse({
        **data,
        "plan": plan,
        "dev_mode": not billing.live_mode(),
        "personalized": personalized,
        "llm_available": bool(llm_provider()),
    })


# ── routes ────────────────────────────────────────────────────────────────────

@app.get("/healthz")
def healthz() -> JSONResponse:
    return JSONResponse({"ok": True})


@app.get("/api/niches")
def niches() -> JSONResponse:
    return JSONResponse({"niches": list(NICHE_PRESETS.keys())})


@app.post("/api/brief")
def brief_post(req: BriefRequest,
               authorization: str = Header(default="")) -> JSONResponse:
    token = authorization.removeprefix("Bearer ").strip()
    return _brief_response(req, token)


@app.get("/api/brief")
def brief_get(niche: str = Query("fitness"), top: int = Query(12, ge=1, le=25),
              authorization: str = Header(default="")) -> JSONResponse:
    """GET kept for the CLI / curl convenience; same behavior as POST without profile."""
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
