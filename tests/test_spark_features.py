"""Tests for the Spark feature set: saves, prefs, history/export, expansion,
digest, feedback, billing portal, admin stats. No network, no engine runs."""
import json
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

import spark_billing as billing
import spark_email
import spark_expand
import spark_store
import trend_api


IDEA = {
    "topic": "high protein meal prep",
    "hook": "Stop wasting your Sundays.",
    "titles": ["High Protein Meal Prep: The Complete Guide",
               "Meal Prep Mistakes", "I Tried Meal Prep for 30 Days"],
    "format": "Short (<60s)",
    "outline": ["0–3s  : Hook — claim", "3–15s : The insight",
                "15–45s: Proof", "45–60s: CTA"],
    "why_now": "Top video at 12k views/hr.",
    "score": 82.0,
    "kind": "working_format",
}

FAKE_BRIEF = {
    "niche": "fitness", "date": "2026-07-16",
    "counts": {"videos": 5, "trends": 3},
    "ideas": [IDEA], "signals": [], "has_youtube": True, "llm_used": False,
}


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    """No Stripe/email env, temp DB + cache, fresh limiter/budget state."""
    for var in ("STRIPE_SECRET_KEY", "STRIPE_PRICE_ID", "STRIPE_WEBHOOK_SECRET",
                "SPARK_DB_PATH", "SPARK_CACHE_DIR", "SPARK_ADMIN_TOKEN",
                "RESEND_API_KEY", "SMTP_HOST",
                "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(billing, "_DB_PATH", tmp_path / "users.db")
    monkeypatch.setattr(spark_store, "_DB_PATH", tmp_path / "users.db")
    monkeypatch.setattr(trend_api, "CACHE_DIR", tmp_path / "cache")
    trend_api.CACHE_DIR.mkdir()
    monkeypatch.setattr(trend_api, "_mem_cache", {})
    monkeypatch.setattr(trend_api, "_rl_buckets", {})
    monkeypatch.setattr(trend_api, "_gen_locks", {})
    monkeypatch.setattr(trend_api, "_run_counts", {})
    monkeypatch.setattr(trend_api, "_expand_counts", {})
    monkeypatch.setattr(trend_api, "DAILY_RUN_BUDGET", 100)
    monkeypatch.setattr(trend_api, "DAILY_EXPAND_BUDGET", 100)
    monkeypatch.setattr(trend_api, "_run_brief",
                        lambda niche, top, profile, use_llm, geo="": dict(FAKE_BRIEF))
    yield


@pytest.fixture()
def client():
    with TestClient(trend_api.app) as c:
        yield c


def _token(email="user@x.com") -> str:
    return billing.issue_token(email, plan="pro")


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── saved ideas ───────────────────────────────────────────────────────────────

def test_saves_roundtrip(client):
    tok = _token()
    r = client.post("/api/saves", headers=_auth(tok),
                    json={"niche": "fitness", "idea": IDEA})
    assert r.status_code == 200 and r.json()["saved"]

    r = client.get("/api/saves", headers=_auth(tok))
    saves = r.json()["saves"]
    assert len(saves) == 1 and saves[0]["idea"]["topic"] == IDEA["topic"]

    r = client.delete(f"/api/saves/{saves[0]['id']}", headers=_auth(tok))
    assert r.status_code == 200
    assert client.get("/api/saves", headers=_auth(tok)).json()["saves"] == []


def test_saves_require_token(client):
    assert client.get("/api/saves").status_code == 401
    assert client.post("/api/saves", json={"idea": IDEA}).status_code == 401


def test_saves_dedupe_by_topic(client):
    tok = _token()
    for _ in range(3):
        client.post("/api/saves", headers=_auth(tok), json={"idea": IDEA})
    assert len(client.get("/api/saves", headers=_auth(tok)).json()["saves"]) == 1


def test_saves_scoped_per_user(client):
    a, b = _token("a@x.com"), _token("b@x.com")
    client.post("/api/saves", headers=_auth(a), json={"idea": IDEA})
    assert client.get("/api/saves", headers=_auth(b)).json()["saves"] == []
    # b cannot delete a's save
    sid = client.get("/api/saves", headers=_auth(a)).json()["saves"][0]["id"]
    assert client.delete(f"/api/saves/{sid}", headers=_auth(b)).status_code == 404


def test_saves_cap_enforced(client, monkeypatch):
    monkeypatch.setattr(spark_store, "MAX_SAVES_PER_USER", 2)
    tok = _token()
    for i in range(2):
        idea = dict(IDEA, topic=f"topic {i}")
        assert client.post("/api/saves", headers=_auth(tok),
                           json={"idea": idea}).status_code == 200
    r = client.post("/api/saves", headers=_auth(tok),
                    json={"idea": dict(IDEA, topic="one too many")})
    assert r.status_code == 409


def test_save_rejects_oversized_or_topicless(client):
    tok = _token()
    assert client.post("/api/saves", headers=_auth(tok),
                       json={"idea": {"hook": "no topic"}}).status_code == 422
    big = dict(IDEA, hook="x" * 7000)
    assert client.post("/api/saves", headers=_auth(tok),
                       json={"idea": big}).status_code == 422


# ── preferences ───────────────────────────────────────────────────────────────

def test_prefs_roundtrip_and_validation(client):
    tok = _token()
    r = client.put("/api/prefs", headers=_auth(tok),
                   json={"niche": "vegan cooking", "geo": "gb",
                         "channel": "My channel", "audience": "busy parents",
                         "tone": "funny"})
    assert r.status_code == 200
    got = client.get("/api/prefs", headers=_auth(tok)).json()
    assert got["niche"] == "vegan cooking" and got["geo"] == "GB"
    assert client.put("/api/prefs", headers=_auth(tok),
                      json={"geo": "USA"}).status_code == 422
    assert client.put("/api/prefs", headers=_auth(tok),
                      json={"niche": "<bad>"}).status_code == 422


def test_saved_profile_personalizes_brief(client, monkeypatch):
    seen = {}

    def spy_engine(niche, top, profile, use_llm, geo=""):
        seen["profile"] = profile
        seen["geo"] = geo
        return dict(FAKE_BRIEF)

    monkeypatch.setattr(trend_api, "_run_brief", spy_engine)
    tok = _token()
    client.put("/api/prefs", headers=_auth(tok),
               json={"audience": "busy parents", "geo": "GB"})
    r = client.post("/api/brief", headers=_auth(tok), json={"niche": "fitness"})
    assert r.status_code == 200
    assert r.json()["personalized"] is True
    assert seen["profile"]["audience"] == "busy parents"
    assert seen["geo"] == "GB"


def test_personalized_brief_cached_per_user(client, monkeypatch):
    calls = {"n": 0}

    def counting_engine(niche, top, profile, use_llm, geo=""):
        calls["n"] += 1
        return dict(FAKE_BRIEF)

    monkeypatch.setattr(trend_api, "_run_brief", counting_engine)
    tok = _token()
    body = {"niche": "fitness", "profile": {"audience": "busy parents"}}
    for _ in range(3):
        assert client.post("/api/brief", headers=_auth(tok),
                           json=body).status_code == 200
    assert calls["n"] == 1        # cached after the first run
    # refresh forces a new run
    client.post("/api/brief", headers=_auth(tok), json={**body, "refresh": True})
    assert calls["n"] == 2


# ── geo ───────────────────────────────────────────────────────────────────────

def test_geo_validation_and_free_gate(client, monkeypatch):
    assert client.post("/api/brief",
                       json={"niche": "fitness", "geo": "GBR"}).status_code == 422
    monkeypatch.setattr(billing, "effective_plan", lambda token: "free")
    r = client.post("/api/brief", json={"niche": "fitness", "geo": "GB"})
    assert r.status_code == 403
    # default geo still fine for free users
    assert client.post("/api/brief",
                       json={"niche": "fitness", "geo": "US"}).status_code == 200


def test_geo_gets_its_own_cache_key(client):
    r_us = client.post("/api/brief", json={"niche": "fitness", "geo": "US"})
    r_gb = client.post("/api/brief", json={"niche": "fitness", "geo": "GB"})
    assert r_us.json()["geo"] == "US" and r_gb.json()["geo"] == "GB"
    files = {p.name for p in trend_api.CACHE_DIR.glob("*.json")}
    assert any("_US_" in f for f in files) and any("_GB_" in f for f in files)


# ── history + export ──────────────────────────────────────────────────────────

def test_history_and_archive(client):
    client.post("/api/brief", json={"niche": "fitness"})   # populates cache
    r = client.get("/api/history", params={"niche": "fitness"})
    dates = r.json()["dates"]
    assert len(dates) == 1
    r = client.get("/api/brief/archive",
                   params={"niche": "fitness", "date": dates[0]})
    assert r.status_code == 200 and r.json()["archived"] is True
    r = client.get("/api/brief/archive",
                   params={"niche": "fitness", "date": "1999-01-01"})
    assert r.status_code == 404


def test_markdown_export(client):
    client.post("/api/brief", json={"niche": "fitness"})
    r = client.get("/api/brief.md", params={"niche": "fitness"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/markdown")
    assert "# Spark Brief" in r.text and IDEA["titles"][0] in r.text
    assert client.get("/api/brief.md",
                      params={"niche": "neverran"}).status_code == 404


def test_history_rejects_bad_input(client):
    assert client.get("/api/history",
                      params={"niche": "../etc"}).status_code == 422
    assert client.get("/api/history",
                      params={"niche": "fitness", "geo": "USA"}).status_code == 422


# ── idea expansion ────────────────────────────────────────────────────────────

def test_expand_template_fallback(client):
    r = client.post("/api/expand", json={"niche": "fitness", "idea": IDEA})
    assert r.status_code == 200
    script = r.json()["script"]
    assert script["llm_used"] is False
    assert script["hook"] and len(script["beats"]) >= 3
    assert script["hashtags"] and script["description"]


def test_expand_is_pro_only(client, monkeypatch):
    monkeypatch.setattr(billing, "effective_plan", lambda token: "free")
    r = client.post("/api/expand", json={"niche": "fitness", "idea": IDEA})
    assert r.status_code == 403


def test_expand_budget_caps_spend(client, monkeypatch):
    monkeypatch.setattr(trend_api, "DAILY_EXPAND_BUDGET", 2)
    for _ in range(2):
        assert client.post("/api/expand",
                           json={"niche": "fitness", "idea": IDEA}).status_code == 200
    r = client.post("/api/expand", json={"niche": "fitness", "idea": IDEA})
    assert r.status_code == 503 and "Retry-After" in r.headers


def test_expand_llm_path(monkeypatch):
    script = {"title": "T", "hook": "H",
              "beats": [{"t": "0-3s", "say": "a", "show": "b"}] * 4,
              "broll": ["x"], "description": "d", "hashtags": ["h"],
              "posting_tip": "p"}
    monkeypatch.setattr(spark_expand, "llm_provider", lambda: "anthropic")
    monkeypatch.setattr(spark_expand, "_call_anthropic",
                        lambda prompt: json.dumps(script))
    out = spark_expand.expand_idea(IDEA, "fitness")
    assert out["llm_used"] is True and out["title"] == "T"


def test_expand_llm_garbage_falls_back(monkeypatch):
    monkeypatch.setattr(spark_expand, "llm_provider", lambda: "anthropic")
    monkeypatch.setattr(spark_expand, "_call_anthropic", lambda prompt: "not json")
    out = spark_expand.expand_idea(IDEA, "fitness")
    assert out["llm_used"] is False and len(out["beats"]) >= 3


# ── daily digest ──────────────────────────────────────────────────────────────

def test_digest_subscribe_roundtrip(client):
    tok = _token()
    r = client.post("/api/digest", headers=_auth(tok),
                    json={"niche": "fitness", "hour": 8})
    assert r.status_code == 200 and r.json()["email"] == "user@x.com"
    got = client.get("/api/digest", headers=_auth(tok)).json()
    assert got["subscribed"] and got["hour"] == 8
    assert client.delete("/api/digest", headers=_auth(tok)).status_code == 200
    assert client.get("/api/digest",
                      headers=_auth(tok)).json()["subscribed"] is False


def test_digest_tick_sends_once_per_day(client, monkeypatch):
    sent = []
    monkeypatch.setattr(spark_email, "send_digest_email",
                        lambda to, niche, day, ideas: sent.append(to) or True)
    tok = _token()
    client.post("/api/digest", headers=_auth(tok),
                json={"niche": "fitness", "hour": 7})
    client.post("/api/brief", json={"niche": "fitness"})   # cache today's brief

    before = datetime.now().replace(hour=6)
    after = datetime.now().replace(hour=9)
    assert trend_api._digest_tick(before) == 0      # not due yet
    assert trend_api._digest_tick(after) == 1       # due -> sends
    assert trend_api._digest_tick(after) == 0       # already sent today
    assert sent == ["user@x.com"]


def test_digest_tick_generates_brief_if_budget_allows(client, monkeypatch):
    sent = []
    monkeypatch.setattr(spark_email, "send_digest_email",
                        lambda to, niche, day, ideas: sent.append(to) or True)
    tok = _token()
    client.post("/api/digest", headers=_auth(tok),
                json={"niche": "fitness", "hour": 0})
    # nothing cached: the tick runs the (fake) engine itself
    assert trend_api._digest_tick(datetime.now().replace(hour=9)) == 1
    assert sent == ["user@x.com"]


def test_digest_tick_skips_churned_subscribers(client, monkeypatch):
    tok = _token()
    client.post("/api/digest", headers=_auth(tok),
                json={"niche": "fitness", "hour": 0})
    client.post("/api/brief", json={"niche": "fitness"})
    monkeypatch.setattr(billing, "effective_plan", lambda token: "free")
    sent = []
    monkeypatch.setattr(spark_email, "send_digest_email",
                        lambda to, niche, day, ideas: sent.append(to) or True)
    assert trend_api._digest_tick(datetime.now().replace(hour=9)) == 0
    assert sent == []


# ── feedback ──────────────────────────────────────────────────────────────────

def test_feedback_stored_and_revote_updates(client):
    r = client.post("/api/feedback",
                    json={"niche": "fitness", "topic": "meal prep", "vote": 1})
    assert r.status_code == 200
    client.post("/api/feedback",
                json={"niche": "fitness", "topic": "meal prep", "vote": -1})
    summary = spark_store.feedback_summary("fitness")
    assert len(summary) == 1 and summary[0]["score"] == -1
    assert client.post("/api/feedback",
                       json={"niche": "fitness", "topic": "x",
                             "vote": 5}).status_code == 422


# ── billing portal ────────────────────────────────────────────────────────────

def test_portal_requires_token_and_dev_mode_message(client):
    assert client.post("/api/billing/portal").status_code == 401
    tok = _token()
    r = client.post("/api/billing/portal", headers=_auth(tok))
    assert r.status_code == 400 and "Dev mode" in r.json()["error"]


# ── admin stats ───────────────────────────────────────────────────────────────

def test_admin_stats_hidden_without_config(client):
    assert client.get("/api/admin/stats").status_code == 404


def test_admin_stats_with_token(client, monkeypatch):
    monkeypatch.setenv("SPARK_ADMIN_TOKEN", "sekrit")
    assert client.get("/api/admin/stats",
                      headers={"X-Admin-Token": "wrong"}).status_code == 404
    r = client.get("/api/admin/stats", headers={"X-Admin-Token": "sekrit"})
    assert r.status_code == 200
    body = r.json()
    assert {"users", "pro_users", "saves", "digest_subs", "runs_today",
            "expand_budget"} <= set(body)
