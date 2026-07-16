"""Billing + access for Spark: Stripe subscriptions with a no-keys dev mode.

Design goals:
  * Zero new dependencies — Stripe's REST API via `requests`, HMAC webhook
    verification via stdlib `hmac`, user store via stdlib `sqlite3`.
  * Dev mode: with no STRIPE_SECRET_KEY set, /api/checkout instantly issues a
    pro token so the whole flow is testable end-to-end before going live.
  * Going live = paste STRIPE_SECRET_KEY, STRIPE_PRICE_ID, STRIPE_WEBHOOK_SECRET
    into .env and restart. No code changes.

Plans:
  free — cached daily briefs only, template ideas.
  pro  — fresh regeneration, LLM polish, personalized ideas.
"""
from __future__ import annotations

import hmac
import hashlib
import os
import secrets
import sqlite3
import time
from pathlib import Path

import requests

import spark_email

STRIPE_API = "https://api.stripe.com/v1"
_DB_PATH = Path(__file__).parent / "spark_users.db"
_TIMEOUT = 20


# ── config ────────────────────────────────────────────────────────────────────

def stripe_secret() -> str:
    return os.getenv("STRIPE_SECRET_KEY", "").strip()


def stripe_price_id() -> str:
    return os.getenv("STRIPE_PRICE_ID", "").strip()


def webhook_secret() -> str:
    return os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()


def live_mode() -> bool:
    """True when Stripe is configured; False = dev mode (everything unlocked)."""
    return bool(stripe_secret() and stripe_price_id())


# ── user store ────────────────────────────────────────────────────────────────

def _db() -> sqlite3.Connection:
    # SPARK_DB_PATH points the store at the deploy volume; resolved per-call so
    # tests can monkeypatch _DB_PATH and the env can be set after import.
    path = Path(os.getenv("SPARK_DB_PATH") or _DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            token TEXT UNIQUE NOT NULL,
            plan TEXT NOT NULL DEFAULT 'free',
            status TEXT NOT NULL DEFAULT 'active',
            stripe_customer TEXT DEFAULT '',
            stripe_subscription TEXT DEFAULT '',
            created REAL NOT NULL
        )""")
    return conn


def issue_token(email: str, plan: str = "free",
                stripe_customer: str = "", stripe_subscription: str = "") -> str:
    """Create or update a user; returns their (possibly existing) access token."""
    email = email.strip().lower()
    conn = _db()
    try:
        row = conn.execute("SELECT token FROM users WHERE email=?", (email,)).fetchone()
        if row:
            conn.execute(
                "UPDATE users SET plan=?, status='active', stripe_customer=?, "
                "stripe_subscription=? WHERE email=?",
                (plan, stripe_customer, stripe_subscription, email))
            conn.commit()
            return row["token"]
        token = "spk_" + secrets.token_urlsafe(24)
        conn.execute(
            "INSERT INTO users (email, token, plan, status, stripe_customer, "
            "stripe_subscription, created) VALUES (?,?,?,?,?,?,?)",
            (email, token, plan, "active", stripe_customer, stripe_subscription, time.time()))
        conn.commit()
        return token
    finally:
        conn.close()


def user_by_token(token: str) -> dict | None:
    if not token:
        return None
    conn = _db()
    try:
        row = conn.execute("SELECT * FROM users WHERE token=?", (token,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def user_by_email(email: str) -> dict | None:
    email = email.strip().lower()
    if not email:
        return None
    conn = _db()
    try:
        row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def set_status_by_subscription(sub_id: str, status: str, plan: str | None = None) -> None:
    conn = _db()
    try:
        if plan:
            conn.execute("UPDATE users SET status=?, plan=? WHERE stripe_subscription=?",
                         (status, plan, sub_id))
        else:
            conn.execute("UPDATE users SET status=? WHERE stripe_subscription=?",
                         (status, sub_id))
        conn.commit()
    finally:
        conn.close()


def effective_plan(token: str) -> str:
    """'pro' | 'free'. In dev mode everyone is pro so the full flow is testable."""
    if not live_mode():
        return "pro"
    u = user_by_token(token)
    if u and u["plan"] == "pro" and u["status"] == "active":
        return "pro"
    return "free"


# ── Stripe REST ───────────────────────────────────────────────────────────────

def create_checkout_session(email: str, success_url: str, cancel_url: str) -> dict:
    """Returns {'url': ..., 'dev': bool, 'token': ...?}.

    Live mode → a real Stripe Checkout URL.
    Dev mode  → instantly activates a pro token (simulated purchase).
    """
    email = email.strip().lower()
    if not live_mode():
        token = issue_token(email, plan="pro")
        return {"url": "", "dev": True, "token": token}

    resp = requests.post(
        f"{STRIPE_API}/checkout/sessions",
        auth=(stripe_secret(), ""),
        data={
            "mode": "subscription",
            "customer_email": email,
            "line_items[0][price]": stripe_price_id(),
            "line_items[0][quantity]": "1",
            "success_url": success_url + "?session_id={CHECKOUT_SESSION_ID}",
            "cancel_url": cancel_url,
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return {"url": resp.json()["url"], "dev": False}


def confirm_checkout_session(session_id: str) -> str | None:
    """Verify a completed Checkout session with Stripe; returns a pro token."""
    if not live_mode():
        return None
    resp = requests.get(f"{STRIPE_API}/checkout/sessions/{session_id}",
                        auth=(stripe_secret(), ""), timeout=_TIMEOUT)
    resp.raise_for_status()
    s = resp.json()
    if s.get("payment_status") not in ("paid", "no_payment_required"):
        return None
    email = (s.get("customer_details") or {}).get("email") or s.get("customer_email")
    if not email:
        return None
    return issue_token(email, plan="pro",
                       stripe_customer=str(s.get("customer") or ""),
                       stripe_subscription=str(s.get("subscription") or ""))


def verify_webhook(payload: bytes, sig_header: str, tolerance: int = 300) -> bool:
    """Verify a Stripe webhook signature (Stripe-Signature: t=...,v1=...)."""
    secret = webhook_secret()
    if not secret or not sig_header:
        return False
    parts = dict(p.split("=", 1) for p in sig_header.split(",") if "=" in p)
    ts, v1 = parts.get("t", ""), parts.get("v1", "")
    if not ts or not v1:
        return False
    try:
        if abs(time.time() - int(ts)) > tolerance:
            return False
    except ValueError:
        return False
    signed = f"{ts}.".encode() + payload
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, v1)


def handle_webhook_event(event: dict) -> None:
    """Apply subscription lifecycle events to the user store."""
    etype = event.get("type", "")
    obj = (event.get("data") or {}).get("object") or {}
    if etype == "checkout.session.completed":
        email = (obj.get("customer_details") or {}).get("email") or obj.get("customer_email")
        if email:
            token = issue_token(email, plan="pro",
                                stripe_customer=str(obj.get("customer") or ""),
                                stripe_subscription=str(obj.get("subscription") or ""))
            try:
                spark_email.send_token_email(email, token)
            except Exception:
                # send_token_email already fails soft; this guard keeps any
                # surprise from ever failing a paid webhook.
                pass
    elif etype in ("customer.subscription.deleted", "customer.subscription.paused"):
        sub_id = str(obj.get("id") or "")
        if sub_id:
            set_status_by_subscription(sub_id, "canceled", plan="free")
    elif etype == "customer.subscription.updated":
        sub_id = str(obj.get("id") or "")
        status = str(obj.get("status") or "")
        if sub_id and status:
            if status in ("active", "trialing"):
                set_status_by_subscription(sub_id, "active", plan="pro")
            elif status in ("canceled", "unpaid", "incomplete_expired"):
                set_status_by_subscription(sub_id, "canceled", plan="free")
