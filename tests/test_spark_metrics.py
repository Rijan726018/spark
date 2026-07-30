"""Snapshot velocity + outlier score — no network, temp database."""
import time

import pytest

import spark_metrics as m
from trend_engine.aggregate import build_opportunities
from trend_engine.config import resolve_niche
from trend_engine.ideas import generate_ideas
from trend_engine.models import VideoItem

FITNESS = resolve_niche("fitness")


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(m, "_DB_PATH", tmp_path / "metrics.db")
    monkeypatch.delenv("SPARK_DB_PATH", raising=False)
    yield


def _v(vid="abc", views=10000, age=24.0, query="fat loss tips", ch="ch1",
       outlier=None, measured=None):
    return VideoItem(video_id=vid, title="A video", channel="Chan",
                     channel_id=ch, views=views, age_hours=age, query=query,
                     url=f"https://youtube.com/watch?v={vid}",
                     outlier=outlier, measured_velocity=measured)


# ── snapshots → measured velocity ─────────────────────────────────────────────

def test_first_sighting_has_no_measured_velocity():
    m.record_snapshots([_v(views=1000)])
    assert m.measured_velocity("abc", 1000) is None, "no prior snapshot yet"


def test_measured_velocity_from_two_snapshots(monkeypatch):
    # Write a snapshot as if it happened 2 hours ago.
    real = time.time
    monkeypatch.setattr(m.time, "time", lambda: real() - 2 * 3600)
    m.record_snapshots([_v(views=1000)])
    monkeypatch.setattr(m.time, "time", real)
    # +600 views in 2h = 300/hr
    v = m.measured_velocity("abc", 1600)
    assert v is not None and 290 < v < 310


def test_snapshot_too_recent_is_ignored():
    m.record_snapshots([_v(views=1000)])          # now
    assert m.measured_velocity("abc", 5000) is None, "gap under 30min is noise"


def test_snapshot_too_old_is_ignored(monkeypatch):
    real = time.time
    monkeypatch.setattr(m.time, "time", lambda: real() - 200 * 3600)
    m.record_snapshots([_v(views=1000)])
    monkeypatch.setattr(m.time, "time", real)
    assert m.measured_velocity("abc", 9000) is None, "beyond MAX_SNAPSHOT_AGE_H"


def test_revised_down_views_do_not_produce_negative_velocity(monkeypatch):
    real = time.time
    monkeypatch.setattr(m.time, "time", lambda: real() - 2 * 3600)
    m.record_snapshots([_v(views=5000)])
    monkeypatch.setattr(m.time, "time", real)
    assert m.measured_velocity("abc", 4000) is None


def test_record_snapshots_is_resilient():
    assert m.record_snapshots([]) == 0
    assert m.record_snapshots([_v(vid="")]) == 0        # no id → skipped


def test_video_velocity_prefers_measured_over_lifetime():
    v = _v(views=100000, age=100.0)                    # lifetime = 1000/hr
    assert v.velocity == pytest.approx(1000, rel=.01)
    v.measured_velocity = 5000.0
    assert v.velocity == 5000.0                        # measured wins
    assert v.lifetime_velocity == pytest.approx(1000, rel=.01)


# ── outlier score ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("views,median,expected", [
    (100000, 10000.0, 10.0),
    (5000, 10000.0, 0.5),
    (100000, 0.0, None),
    (100000, None, None),
])
def test_outlier_score(views, median, expected):
    assert m.outlier_score(views, median) == expected


def test_channel_medians_uses_cache_and_skips_api(monkeypatch):
    """A cached median must not spend quota."""
    conn = m._db()
    conn.execute("INSERT INTO channels (channel_id, median_views, sample_n, refreshed) "
                 "VALUES (?,?,?,?)", ("ch1", 4000.0, 15, time.time()))
    conn.commit(); conn.close()

    def boom(*a, **k):
        raise AssertionError("must not hit the API when cached")

    monkeypatch.setattr(m, "_fetch_channel_median", boom)
    assert m.channel_medians(["ch1"], "key") == {"ch1": 4000.0}


def test_channel_medians_respects_fetch_cap(monkeypatch):
    calls = {"n": 0}

    def fake(cid, key):
        calls["n"] += 1
        return (1000.0, 15)

    monkeypatch.setattr(m, "_fetch_channel_median", fake)
    got = m.channel_medians([f"c{i}" for i in range(10)], "key", max_fetches=3)
    assert calls["n"] == 3, "quota cap must bound fetches per run"
    assert len(got) == 3


def test_channel_medians_without_key_returns_only_cached(monkeypatch):
    monkeypatch.setattr(m, "_fetch_channel_median",
                        lambda c, k: (_ for _ in ()).throw(AssertionError("no key!")))
    assert m.channel_medians(["ch1", "ch2"], "") == {}


def test_provider_disabled_is_inert():
    p = m.MetricsProvider(api_key="", enabled=False)
    p.observe([_v()])
    assert p.velocity(_v()) is None and p.outlier(_v()) is None


# ── ranking + copy use the outlier ────────────────────────────────────────────

def test_outlier_boosts_ranking_over_raw_velocity():
    """A modest video crushing its channel's normal beats a bigger video that is
    merely normal for a huge channel — the core 'format is winning' claim."""
    breakout = [_v(vid="b", views=48000, age=24, query="fat loss tips",
                   ch="small", outlier=12.0)]          # 2,000/hr but 12x normal
    routine = [_v(vid="r", views=60000, age=24, query="gym motivation",
                  ch="huge", outlier=1.0)]             # 2,500/hr and unremarkable
    opps = build_opportunities([], breakout + routine, FITNESS)
    assert opps[0].topic == "fat loss tips"
    assert opps[0].outlier == 12.0


def test_underperforming_video_is_penalised():
    weak = [_v(vid="w", views=24000, age=24, query="fat loss tips", outlier=0.2)]
    fine = [_v(vid="f", views=22000, age=24, query="gym motivation", outlier=1.0)]
    opps = build_opportunities([], weak + fine, FITNESS)
    assert opps[0].topic == "gym motivation", "sub-0.5x outlier should be discounted"


def test_outlier_appears_in_evidence_and_why_now():
    vids = [_v(vid="b", views=90000, age=20, outlier=8.4)]
    opps = build_opportunities([], vids, FITNESS)
    assert any("8.4x that channel's normal" in e for e in opps[0].evidence)
    idea = generate_ideas(opps, FITNESS, top=1)[0]
    assert idea.outlier == 8.4
    assert "8.4x its channel's normal" in idea.why_now
    assert "format winning" in idea.why_now


def test_pipeline_day1_then_day2_sharpens_velocity(monkeypatch):
    """End-to-end: run 1 has no history (estimates), run 2 measures real
    velocity from run 1's snapshots. This is the whole point of the feature."""
    from trend_engine import pipeline
    from trend_engine.config import Settings

    day1 = [_v(vid="vid1", views=10000, age=48.0)]
    day2 = [_v(vid="vid1", views=13000, age=51.0)]     # +3000 views in 3h
    seq = [day1, day2]

    monkeypatch.setattr(pipeline.google_trends, "fetch_realtime_trends",
                        lambda **k: [])
    monkeypatch.setattr(pipeline.youtube, "collect",
                        lambda *a, **k: [v for v in seq.pop(0)])
    monkeypatch.setattr(pipeline, "save_digest", lambda *a, **k: {})
    monkeypatch.setattr(pipeline, "llm_provider", lambda: None)

    settings = Settings(geo="US", youtube_api_key="")
    provider = m.MetricsProvider(api_key="")           # no key → medians skipped

    real = time.time
    monkeypatch.setattr(m.time, "time", lambda: real() - 3 * 3600)
    r1 = pipeline.run("fitness", settings=settings, top=3, use_llm=False,
                      metrics=provider)
    assert r1["ideas"], "run 1 must still produce ideas with no history"
    assert r1["ideas"][0].measured is False, "day 1 has nothing to measure"

    monkeypatch.setattr(m.time, "time", real)
    r2 = pipeline.run("fitness", settings=settings, top=3, use_llm=False,
                      metrics=provider)
    assert r2["ideas"][0].measured is True, "day 2 should measure real velocity"


def test_pipeline_survives_broken_metrics_provider(monkeypatch):
    """A metrics failure must never cost the user their brief."""
    from trend_engine import pipeline
    from trend_engine.config import Settings

    class Broken:
        def observe(self, videos):
            raise RuntimeError("db on fire")
        def velocity(self, v):
            raise RuntimeError("nope")
        def outlier(self, v):
            raise RuntimeError("nope")

    monkeypatch.setattr(pipeline.google_trends, "fetch_realtime_trends",
                        lambda **k: [])
    monkeypatch.setattr(pipeline.youtube, "collect",
                        lambda *a, **k: [_v(vid="x", views=50000, age=20)])
    monkeypatch.setattr(pipeline, "save_digest", lambda *a, **k: {})
    monkeypatch.setattr(pipeline, "llm_provider", lambda: None)

    out = pipeline.run("fitness", settings=Settings(youtube_api_key=""), top=3,
                       use_llm=False, metrics=Broken())
    assert out["ideas"], "brief must render despite metrics blowing up"


def test_no_outlier_data_leaves_ranking_and_copy_clean():
    """Day-one behaviour: no medians yet, so nothing mentions outliers."""
    vids = [_v(vid="a", views=50000, age=20)]
    opps = build_opportunities([], vids, FITNESS)
    idea = generate_ideas(opps, FITNESS, top=1)[0]
    assert opps[0].outlier is None
    assert idea.outlier is None
    assert "normal views" not in idea.why_now
    assert "x its channel" not in idea.why_now
