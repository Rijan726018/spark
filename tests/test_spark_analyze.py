"""Deep video analysis — no network; YouTube/Supadata/LLM monkeypatched."""
import json
import time

import pytest
from fastapi.testclient import TestClient

import spark_analyze
import spark_billing as billing
import trend_api

VID = "dQw4w9WgXcQ"

META = {
    "video_id": VID, "url": f"https://www.youtube.com/watch?v={VID}",
    "title": "I Tried Cash Stuffing for 30 Days", "channel": "BudgetGirl",
    "description": "desc", "tags": ["budget"], "published_at": "2026-07-15T00:00:00Z",
    "age_hours": 48.0, "duration_s": 52, "views": 480000, "likes": 21000,
    "comment_count": 900, "views_per_hour": 10000.0,
}

LLM_JSON = json.dumps({
    "verdict": "Curiosity-gap title paid off in the first five seconds.",
    "hook": {"quote": "I put every dollar I own into envelopes.",
             "why": "Immediate visual stakes."},
    "structure": [{"t": "0:00", "beat": "hook"}, {"t": "0:10", "beat": "method"}],
    "title_formula": {"pattern": "I Tried X for N Days", "why": "proof promise"},
    "thumbnail": {"elements": ["cash envelopes", "shocked face"], "why": "contrast"},
    "audience": {"loved": ["honesty"], "wanted": ["a printable template"]},
    "velocity": "10k/hr at 48h is breakout velocity.",
    "steal_this": ["Open on the money visual", "Promise a number", "Answer top comment"],
    "confidence": "high",
})


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    for var in ("STRIPE_SECRET_KEY", "STRIPE_PRICE_ID", "STRIPE_WEBHOOK_SECRET",
                "SUPADATA_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("YOUTUBE_API_KEY", "yt_test_key")
    monkeypatch.setattr(billing, "_DB_PATH", tmp_path / "users.db")
    monkeypatch.setattr(trend_api, "CACHE_DIR", tmp_path / "cache")
    trend_api.CACHE_DIR.mkdir()
    monkeypatch.setattr(trend_api, "_mem_cache", {})
    monkeypatch.setattr(trend_api, "_rl_buckets", {})
    monkeypatch.setattr(trend_api, "_analyze_counts", {})
    monkeypatch.setattr(trend_api, "DAILY_ANALYZE_BUDGET", 40)
    yield


@pytest.fixture()
def client():
    return TestClient(trend_api.app)


# ── video id parsing ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("given", [
    VID,
    f"https://www.youtube.com/watch?v={VID}",
    f"https://www.youtube.com/watch?v={VID}&t=42s",
    f"https://youtu.be/{VID}",
    f"https://youtube.com/shorts/{VID}",
    f"https://www.youtube.com/embed/{VID}",
])
def test_video_id_parsing(given):
    assert spark_analyze.video_id_from(given) == VID


@pytest.mark.parametrize("bad", ["", "not a url", "https://vimeo.com/12345",
                                 "tooshort", "x" * 300,
                                 # a v= param on a non-YouTube host is not a
                                 # YouTube link — accepting it only buys a 404
                                 f"https://evil.example.com/?v={VID}"])
def test_video_id_rejects_garbage(bad):
    assert spark_analyze.video_id_from(bad) is None


@pytest.mark.parametrize("iso,secs", [
    ("PT52S", 52), ("PT1M30S", 90), ("PT2H10M5S", 7805),
    ("P1DT2H10M", 94200),        # >24h livestream VOD
    ("P0D", 0),                  # live broadcast sentinel
    ("", 0), ("garbage", 0),
])
def test_parse_duration(iso, secs):
    assert spark_analyze._parse_duration(iso) == secs


# ── analyze_video degradation ladder ──────────────────────────────────────────

def _patch_fetchers(monkeypatch, transcript="words " * 40, comments=True,
                    thumb=True):
    monkeypatch.setattr(spark_analyze, "fetch_video_meta", lambda v: dict(META))
    monkeypatch.setattr(spark_analyze, "fetch_transcript", lambda v: transcript)
    monkeypatch.setattr(spark_analyze, "fetch_comments",
                        lambda v, max_n=40: ([{"text": "loved it", "likes": 9}]
                                             if comments else []))
    monkeypatch.setattr(spark_analyze, "fetch_thumbnail_b64",
                        lambda v: "aGk=" if thumb else None)


def test_llm_path(monkeypatch):
    _patch_fetchers(monkeypatch)
    monkeypatch.setattr(spark_analyze, "llm_provider", lambda: "anthropic")
    monkeypatch.setattr(spark_analyze, "_call_llm", lambda p, img: LLM_JSON)
    out = spark_analyze.analyze_video(VID, "personal finance")
    a = out["analysis"]
    assert a["llm_used"] is True
    assert a["hook"]["quote"].startswith("I put every dollar")
    assert a["evidence"] == {"transcript": True, "comments": True, "thumbnail": True}
    assert out["meta"]["views_per_hour"] == 10000.0


def test_llm_failure_falls_back_to_template(monkeypatch):
    _patch_fetchers(monkeypatch)
    monkeypatch.setattr(spark_analyze, "llm_provider", lambda: "anthropic")
    monkeypatch.setattr(spark_analyze, "_call_llm", lambda p, img: None)
    out = spark_analyze.analyze_video(VID, "fitness")
    assert out["analysis"]["llm_used"] is False
    assert out["analysis"]["hook"]["quote"].startswith("words")


def test_no_llm_no_transcript_still_answers(monkeypatch):
    _patch_fetchers(monkeypatch, transcript=None, comments=False, thumb=False)
    out = spark_analyze.analyze_video(VID, "fitness")
    a = out["analysis"]
    assert a["llm_used"] is False
    assert a["confidence"] == "low"
    assert a["evidence"] == {"transcript": False, "comments": False,
                             "thumbnail": False}
    assert len(a["steal_this"]) >= 2


def test_unfetchable_video_returns_none(monkeypatch):
    monkeypatch.setattr(spark_analyze, "fetch_video_meta", lambda v: None)
    assert spark_analyze.analyze_video(VID, "fitness") is None


def test_no_transcript_prompt_forbids_quotes():
    prompt = spark_analyze._build_prompt(META, "fitness", None, [], False)
    assert "do NOT invent quotes" in prompt


@pytest.mark.parametrize("payload", [
    {"content": {"unexpected": "object"}},     # API shape change
    {"content": ["plain", "strings"]},         # list of non-dicts
    {"content": 42},
    {},
])
def test_transcript_survives_unexpected_shapes(monkeypatch, payload):
    """A 200 with a surprising body must degrade to None, never raise."""
    monkeypatch.setenv("SUPADATA_API_KEY", "sd_test")

    class R:
        status_code = 200
        def json(self):
            return payload

    monkeypatch.setattr(spark_analyze.requests, "get", lambda *a, **k: R())
    assert spark_analyze.fetch_transcript(VID) is None


# ── the route ─────────────────────────────────────────────────────────────────

def _fake_result():
    return {"video_id": VID, "niche": "fitness",
            "analysis": {"verdict": "v", "steal_this": ["a", "b"]},
            "meta": {"url": META["url"], "title": META["title"]}}


def test_route_free_user_gets_403(client, monkeypatch):
    monkeypatch.setattr(billing, "effective_plan", lambda token: "free")
    r = client.post("/api/analyze", json={"video": VID})
    assert r.status_code == 403


def test_route_happy_path_and_cache(client, monkeypatch):
    calls = {"n": 0}

    def fake_analyze(vid, niche):
        calls["n"] += 1
        return _fake_result()

    monkeypatch.setattr(trend_api.spark_analyze, "analyze_video", fake_analyze)
    r1 = client.post("/api/analyze", json={"video": META["url"]})
    r2 = client.post("/api/analyze", json={"video": VID})
    assert r1.status_code == r2.status_code == 200
    assert calls["n"] == 1                    # second hit served from cache
    assert r2.json()["cached"] is True


def test_route_rejects_bad_video(client):
    assert client.post("/api/analyze",
                       json={"video": "https://vimeo.com/1"}).status_code == 422


def test_route_503_without_youtube_key(client, monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    r = client.post("/api/analyze", json={"video": VID})
    assert r.status_code == 503


def test_route_budget_exhausted(client, monkeypatch):
    monkeypatch.setattr(trend_api, "DAILY_ANALYZE_BUDGET", 1)
    monkeypatch.setattr(trend_api.spark_analyze, "analyze_video",
                        lambda vid, niche: _fake_result())
    assert client.post("/api/analyze", json={"video": VID}).status_code == 200
    r = client.post("/api/analyze", json={"video": "aaaaaaaaaaa"})
    assert r.status_code == 503


def test_route_404_when_video_missing(client, monkeypatch):
    monkeypatch.setattr(trend_api.spark_analyze, "analyze_video",
                        lambda vid, niche: None)
    r = client.post("/api/analyze", json={"video": VID})
    assert r.status_code == 404


def test_failed_analysis_does_not_burn_budget(client, monkeypatch):
    """A dead link spends nothing, so it must not consume the day's capacity —
    otherwise 40 bad links lock every Pro user out until tomorrow."""
    monkeypatch.setattr(trend_api, "DAILY_ANALYZE_BUDGET", 2)
    monkeypatch.setattr(trend_api.spark_analyze, "analyze_video",
                        lambda vid, niche: None)
    for i in range(5):
        assert client.post("/api/analyze",
                           json={"video": f"vid{i:08d}"}).status_code == 404
    # Budget untouched: a real analysis still goes through.
    monkeypatch.setattr(trend_api.spark_analyze, "analyze_video",
                        lambda vid, niche: _fake_result())
    assert client.post("/api/analyze", json={"video": VID}).status_code == 200


def test_route_survives_analyzer_exception(client, monkeypatch):
    def boom(vid, niche):
        raise RuntimeError("supadata exploded")

    monkeypatch.setattr(trend_api.spark_analyze, "analyze_video", boom)
    r = client.post("/api/analyze", json={"video": VID})
    assert r.status_code == 404          # not a 500


def test_degraded_analysis_is_not_cached(client, monkeypatch):
    """A transient LLM failure yields a template stub. Serve it, but never
    cache it — otherwise one blip serves a stub for the rest of the day."""
    monkeypatch.setattr(trend_api, "llm_provider", lambda: "anthropic")
    calls = {"n": 0}

    def flaky(vid, niche):
        calls["n"] += 1
        r = _fake_result()
        # First call degrades (LLM down), second succeeds.
        r["analysis"]["llm_used"] = calls["n"] > 1
        return r

    monkeypatch.setattr(trend_api.spark_analyze, "analyze_video", flaky)
    first = client.post("/api/analyze", json={"video": VID})
    assert first.json()["analysis"]["llm_used"] is False
    second = client.post("/api/analyze", json={"video": VID})
    assert calls["n"] == 2                                # not served from cache
    assert second.json()["analysis"]["llm_used"] is True
    third = client.post("/api/analyze", json={"video": VID})
    assert calls["n"] == 2                                # good one IS cached
    assert third.json()["cached"] is True


def test_template_is_cached_when_no_llm_configured(client, monkeypatch):
    """With no LLM key the template IS the product — cache it normally."""
    monkeypatch.setattr(trend_api, "llm_provider", lambda: None)
    calls = {"n": 0}

    def counting(vid, niche):
        calls["n"] += 1
        r = _fake_result()
        r["analysis"]["llm_used"] = False
        return r

    monkeypatch.setattr(trend_api.spark_analyze, "analyze_video", counting)
    client.post("/api/analyze", json={"video": VID})
    client.post("/api/analyze", json={"video": VID})
    assert calls["n"] == 1


def test_concurrent_same_video_runs_engine_once(client, monkeypatch):
    """Launch day: N Pro users tap the same card. One generation, not N
    transcript credits + N vision calls."""
    import threading
    calls = {"n": 0}
    started = threading.Barrier(4, timeout=5)

    def slow(vid, niche):
        calls["n"] += 1
        time.sleep(0.3)
        return _fake_result()

    monkeypatch.setattr(trend_api.spark_analyze, "analyze_video", slow)

    codes = []

    def hit():
        started.wait()
        codes.append(client.post("/api/analyze", json={"video": VID}).status_code)

    threads = [threading.Thread(target=hit) for _ in range(4)]
    [t.start() for t in threads]
    [t.join(timeout=15) for t in threads]
    assert codes == [200, 200, 200, 200]
    assert calls["n"] == 1
