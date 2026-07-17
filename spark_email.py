"""Token delivery for Spark: email the Pro access token after checkout.

Same design rules as spark_billing:
  * Zero new dependencies — Resend's REST API via `requests`, SMTP via stdlib
    `smtplib`. Pick a provider with env vars, no code changes.
  * Fail soft: a payment webhook must never 500 because email is down. The
    token is already persisted in the user store; the manual recovery runbook
    (read spark_users.db on the volume) covers any gap. send_token_email()
    logs and returns False instead of raising.
  * Dev mode: with no provider configured, sending is a logged no-op so the
    whole flow stays testable without an email account.

Providers, first match wins:
  RESEND_API_KEY set -> Resend REST (free tier covers launch volume)
  SMTP_HOST set      -> stdlib smtplib, STARTTLS, optional SMTP_USER/SMTP_PASS
"""
from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

import requests

logger = logging.getLogger("spark.email")

RESEND_API = "https://api.resend.com/emails"
_TIMEOUT = 20


def _from_addr() -> str:
    return os.getenv("SPARK_EMAIL_FROM", "Spark <onboarding@resend.dev>").strip()


def _public_url() -> str:
    return os.getenv("SPARK_PUBLIC_URL", "https://sparkbrief.fly.dev").strip().rstrip("/")


def email_configured() -> bool:
    return bool(os.getenv("RESEND_API_KEY", "").strip() or os.getenv("SMTP_HOST", "").strip())


def _token_email_body(token: str) -> str:
    return (
        "You're in — Spark Pro is active.\n"
        "\n"
        "Your access token:\n"
        "\n"
        f"    {token}\n"
        "\n"
        f"Open {_public_url()} on your phone, tap Pro, and paste the token.\n"
        "(Share -> Add to Home Screen gets you the full-screen app.)\n"
        "\n"
        "Keep this email — the token is your login. If you ever clear your\n"
        "browser data, paste it again and you're back in.\n"
        "\n"
        "Questions? Just reply to this email.\n"
    )


def _digest_email_body(niche: str, day: str, ideas: list[dict]) -> str:
    lines = [
        f"Your Spark brief — {niche} — {day}",
        "",
        f"{len(ideas)} ready-to-shoot ideas, ranked by momentum:",
        "",
    ]
    for i, idea in enumerate(ideas, 1):
        titles = idea.get("titles") or [idea.get("topic", "")]
        lines.append(f"{i}. {titles[0]}")
        lines.append(f"   Format: {idea.get('format', '')}")
        if idea.get("hook"):
            lines.append(f"   Hook:   {idea['hook']}")
        if idea.get("why_now"):
            lines.append(f"   Why:    {idea['why_now']}")
        lines.append("")
    lines += [
        f"Full outlines, scripts and more: {_public_url()}",
        "",
        "— Spark",
        "",
        "To stop these emails, open the app and turn off the daily digest.",
    ]
    return "\n".join(lines)


def send_digest_email(to: str, niche: str, day: str, ideas: list[dict]) -> bool:
    """Email the day's brief. Fails soft like send_token_email. Never raises."""
    subject = f"⚡ Today's {niche} brief — {len(ideas)} ideas ({day})"
    body = _digest_email_body(niche, day, ideas)
    try:
        if os.getenv("RESEND_API_KEY", "").strip():
            _send_resend(to, subject, body)
        elif os.getenv("SMTP_HOST", "").strip():
            _send_smtp(to, subject, body)
        else:
            logger.warning("No email provider configured — digest for %s NOT sent.", to)
            return False
        logger.info("Digest email sent to %s", to)
        return True
    except Exception as e:
        logger.error("Digest email to %s failed (%s).", to, e)
        return False


def _send_resend(to: str, subject: str, body: str) -> None:
    resp = requests.post(
        RESEND_API,
        headers={"Authorization": f"Bearer {os.getenv('RESEND_API_KEY', '').strip()}"},
        json={"from": _from_addr(), "to": [to], "subject": subject, "text": body},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()


def _send_smtp(to: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = _from_addr()
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASS", "")
    with smtplib.SMTP(host, port, timeout=_TIMEOUT) as smtp:
        smtp.starttls()
        if user:
            smtp.login(user, password)
        smtp.send_message(msg)


def send_token_email(to: str, token: str) -> bool:
    """Email `token` to `to`. Returns True on send, False otherwise. Never raises."""
    subject = "Your Spark Pro access token"
    body = _token_email_body(token)
    try:
        if os.getenv("RESEND_API_KEY", "").strip():
            _send_resend(to, subject, body)
        elif os.getenv("SMTP_HOST", "").strip():
            _send_smtp(to, subject, body)
        else:
            logger.warning(
                "No email provider configured (RESEND_API_KEY or SMTP_HOST) — "
                "token for %s NOT emailed; use the manual recovery runbook.", to)
            return False
        logger.info("Token email sent to %s", to)
        return True
    except Exception as e:
        logger.error("Token email to %s failed (%s) — token is safe in the "
                     "user store; recover manually if the customer asks.", to, e)
        return False
