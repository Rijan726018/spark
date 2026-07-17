"""Route-layer tests for the Spark API money path — no network, no engine runs."""
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

import spark_billing as billing
import spark_store
import trend_api


FAKE_BRIEF = {
    "niche": "fitness", "date": "2026-07-15",
    "counts": {"videos": 5, "trends": 3},
    "ideas": [], "signals": [], "has_youtube": True, "llm_used": False,
}


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    """No Stripe env, temp DB + cache, fresh rate-limit buckets, fake engine."""
    for var in ("STRIPE_SECRET_KEY", "STRIPE_PRICE_ID", "STRIPE_WEBHOOK_SECRET",
                "SPARK_DB_PATH", "SPARK_CACHE_DIR"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(billing, "_DB_PATH", tmp_path / "users.db")
    monkeypatch.setattr(spark_store, "_DB_PATH", tmp_path / "users.db")
    monkeypatch.setattr(trend_api, "CACHE_DIR", tmp_path / "cache")
    trend_api.CACHE_DIR.mkdir()
    monkeypatch.setattr(trend_api, "_mem_cache", {})
    monkeypatch.setattr(trend_api, "_rl_buckets", {})
    monkeypatch.setattr(trend_api, "_gen_locks", {})
    monkeypatch.setattr(trend_api, "_run_counts", {})
    monkeypatch.setattr(trend_api, "DAILY_RUN_BUDGET", 100)
    monkeypatch.setattr(trend_api, "_run_brief",
                        lambda niche, top, profile, use_llm, geo="": dict(FAKE_BRIEF))
    yield


@pytest.fixture()
def client():
    with TestClient(trend_api.app) as c:
        yield c


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200 and r.json() == {"ok": True}


def test_post_top_clamped(client):
    assert client.post("/api/brief", json={"niche": "fitness", "top": 999}).status_code == 422
    assert client.post("/api/brief", json={"niche": "fitness", "top": 0}).status_code == 422
    assert client.post("/api/brief", json={"niche": "fitness", "top": 12}).status_code == 200


def test_niche_length_clamped(client):
    r = client.post("/api/brief", json={"niche": "x" * 200})
    assert r.status_code == 422
    assert client.post("/api/brief", json={"niche": "   "}).status_code == 422


def test_free_user_locked_to_presets(client, monkeypatch):
    monkeypatch.setattr(billing, "effective_plan", lambda token: "free")
    r = client.post("/api/brief", json={"niche": "totally custom niche"})
    assert r.status_code == 403
    assert "Pro" in r.json()["error"]
    assert client.post("/api/brief", json={"niche": "Fitness"}).status_code == 200


def test_pro_user_can_use_custom_niche(client, monkeypatch):
    monkeypatch.setattr(billing, "effective_plan", lambda token: "pro")
    assert client.post("/api/brief", json={"niche": "vegan cooking"}).status_code == 200


def test_rate_limit_kicks_in(client, monkeypatch):
    monkeypatch.setattr(trend_api, "RATE_LIMIT_PER_MIN", 3)
    codes = [client.get("/api/brief", params={"niche": "fitness"}).status_code
             for _ in range(5)]
    assert codes[:3] == [200, 200, 200]
    assert 429 in codes[3:]
    body = client.get("/api/brief", params={"niche": "fitness"}).json()
    assert "error" in body


def test_rate_limit_applies_to_checkout(client, monkeypatch):
    monkeypatch.setattr(trend_api, "RATE_LIMIT_PER_MIN", 2)
    for _ in range(2):
        client.post("/api/checkout", json={"email": "a@b.com"})
    assert client.post("/api/checkout", json={"email": "a@b.com"}).status_code == 429


def test_cache_miss_stampede_runs_engine_once(monkeypatch):
    calls = {"n": 0}
    started = threading.Barrier(5, timeout=5)

    def slow_engine(niche, top, profile, use_llm, geo=""):
        calls["n"] += 1
        return dict(FAKE_BRIEF)

    monkeypatch.setattr(trend_api, "_run_brief", slow_engine)

    def hit():
        started.wait()
        req = trend_api.BriefRequest(niche="fitness")
        return trend_api._brief_response(req, "")

    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(lambda _: hit(), range(5)))
    assert calls["n"] == 1
    assert all(r.status_code == 200 for r in results)


@pytest.mark.parametrize("present", [
    ("STRIPE_SECRET_KEY", "STRIPE_PRICE_ID"),          # missing webhook secret
    ("STRIPE_SECRET_KEY",),                            # secret only
    ("STRIPE_PRICE_ID", "STRIPE_WEBHOOK_SECRET"),      # missing secret
])
def test_startup_guard_refuses_any_partial_stripe_config(monkeypatch, present):
    for var in present:
        monkeypatch.setenv(var, "x_" + var.lower())
    with pytest.raises(RuntimeError, match="partially configured"):
        with TestClient(trend_api.app):
            pass


def test_startup_guard_allows_full_config_and_dev_mode(monkeypatch):
    with TestClient(trend_api.app):    # all empty = dev mode boots
        pass
    for var in ("STRIPE_SECRET_KEY", "STRIPE_PRICE_ID", "STRIPE_WEBHOOK_SECRET"):
        monkeypatch.setenv(var, "x")
    with TestClient(trend_api.app):    # all three = live mode boots
        pass


def test_case_variants_share_one_cache_key_and_engine_run(client, monkeypatch):
    calls = {"n": 0}

    def counting_engine(niche, top, profile, use_llm, geo=""):
        calls["n"] += 1
        return dict(FAKE_BRIEF)

    monkeypatch.setattr(trend_api, "_run_brief", counting_engine)
    for variant in ("fitness", "Fitness", "FITNESS", "fItNeSs"):
        assert client.post("/api/brief", json={"niche": variant}).status_code == 200
    assert calls["n"] == 1


def test_hostile_niche_strings_rejected(client):
    for bad in ("../../etc/passwd", "a\x00b", "niche;rm -rf /", "<script>x"):
        r = client.post("/api/brief", json={"niche": bad})
        assert r.status_code == 422, bad


def test_daily_run_budget_caps_engine_spend(client, monkeypatch):
    monkeypatch.setattr(trend_api, "DAILY_RUN_BUDGET", 1)
    monkeypatch.setattr(billing, "effective_plan", lambda token: "pro")
    calls = {"n": 0}

    def counting_engine(niche, top, profile, use_llm, geo=""):
        calls["n"] += 1
        return dict(FAKE_BRIEF)

    monkeypatch.setattr(trend_api, "_run_brief", counting_engine)
    # First fresh run consumes the budget.
    assert client.post("/api/brief",
                       json={"niche": "fitness", "refresh": True}).status_code == 200
    # Second fresh request: budget gone, no cache for this niche -> 503.
    r = client.post("/api/brief", json={"niche": "trading", "refresh": True})
    assert r.status_code == 503 and "Retry-After" in r.headers
    # Same niche falls back to today's cached brief instead of a fresh run.
    r = client.post("/api/brief", json={"niche": "fitness", "refresh": True})
    assert r.status_code == 200
    assert calls["n"] == 1


def test_db_path_env_override(tmp_path, monkeypatch):
    target = tmp_path / "vol" / "users.db"
    monkeypatch.setenv("SPARK_DB_PATH", str(target))
    billing.issue_token("vol@x.com", plan="free")
    assert target.exists()
