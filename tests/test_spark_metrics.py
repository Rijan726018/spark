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
       outlier=None, measured=None, dur=600):
    return VideoItem(video_id=vid, title="A video", channel="Chan",
                     channel_id=ch, views=views, age_hours=age, query=query,
                     url=f"https://youtube.com/watch?v={vid}", duration_s=dur,
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


def test_zero_delta_over_short_window_is_no_reading_not_zero(monkeypatch):
    """YouTube's public viewCount moves in coarse steps. A flat 35-minute
    window means 'no reading yet' — reporting 0.0 would bury a real riser."""
    real = time.time
    monkeypatch.setattr(m.time, "time", lambda: real() - 0.6 * 3600)
    m.record_snapshots([_v(views=40000)])
    monkeypatch.setattr(m.time, "time", real)
    assert m.measured_velocity("abc", 40000) is None


def test_zero_delta_over_long_window_is_a_real_zero(monkeypatch):
    """Flat for 6 hours genuinely means stalled — that IS a measurement."""
    real = time.time
    monkeypatch.setattr(m.time, "time", lambda: real() - 6 * 3600)
    m.record_snapshots([_v(views=40000)])
    monkeypatch.setattr(m.time, "time", real)
    assert m.measured_velocity("abc", 40000) == 0.0


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


def test_ranking_velocity_is_always_lifetime_basis():
    """Ranking compares videos against each other, so every video must be on
    the same basis. The measured rate is exposed separately for display."""
    v = _v(views=100000, age=100.0)                    # lifetime = 1000/hr
    assert v.velocity == pytest.approx(1000, rel=.01)
    v.measured_velocity = 5000.0
    assert v.velocity == pytest.approx(1000, rel=.01), "ranking basis unchanged"
    assert v.current_velocity == 5000.0                # display shows measured
    assert v.acceleration == pytest.approx(5.0, rel=.01)


def test_acceleration_is_none_without_measurement():
    assert _v().acceleration is None


# ── outlier score (rate-vs-rate, format-bucketed) ─────────────────────────────

def _rates(short=None, long=None):
    out = {}
    if short:
        out["short"] = short
    if long:
        out["long"] = long
    return out


def test_outlier_compares_rate_against_same_format_rate():
    # 5,000 views/hr against a channel whose long-form median is 500/hr.
    assert m.outlier_score(5000.0, _rates(long=(500.0, 15)), is_short=False) == 10.0


def test_outlier_none_when_no_same_format_history():
    """A Shorts-only channel gives no basis for judging a long-form video."""
    assert m.outlier_score(5000.0, _rates(short=(900.0, 15)), is_short=False) is None


def test_outlier_none_on_thin_sample():
    assert m.outlier_score(5000.0, _rates(long=(500.0, 3)), is_short=False) is None


def test_outlier_shrinks_toward_one_on_small_sample():
    """A 7-upload channel can't mint a 10x claim off noise."""
    full = m.outlier_score(5000.0, _rates(long=(500.0, 15)), is_short=False)
    thin = m.outlier_score(5000.0, _rates(long=(500.0, 7)), is_short=False)
    assert full == 10.0
    assert 1.0 < thin < full, f"expected shrinkage toward 1.0, got {thin}"


def test_outlier_none_without_rates():
    assert m.outlier_score(5000.0, None, is_short=False) is None
    assert m.outlier_score(0.0, _rates(long=(500.0, 15)), is_short=False) is None


def test_fresh_video_is_not_penalised_for_being_young():
    """The bug this rewrite fixes: a 6h-old breakout used to be compared
    against fully matured uploads and scored as an underperformer."""
    fresh = _v(vid="f", views=12000, age=6.0)          # 2,000 views/hr
    rates = _rates(long=(400.0, 15))                   # channel normal: 400/hr
    score = m.outlier_score(fresh.lifetime_velocity, rates, is_short=False)
    assert score == pytest.approx(5.0, rel=.01), "young breakout must score high"


def test_channel_rates_uses_cache_and_skips_api(monkeypatch):
    """A cached entry must not spend quota."""
    conn = m._db()
    conn.execute("INSERT INTO channel_rates (channel_id, median_vel_short, n_short, "
                 "median_vel_long, n_long, refreshed) VALUES (?,?,?,?,?,?)",
                 ("ch1", 0.0, 0, 400.0, 15, time.time()))
    conn.commit(); conn.close()

    def boom(*a, **k):
        raise AssertionError("must not hit the API when cached")

    monkeypatch.setattr(m, "_fetch_channel_rates", boom)
    assert m.channel_rates(["ch1"], "key") == {"ch1": {"long": (400.0, 15)}}


def test_channel_rates_respects_fetch_cap(monkeypatch):
    calls = {"n": 0}

    def fake(cid, key):
        calls["n"] += 1
        return {"long": (1000.0, 15)}

    monkeypatch.setattr(m, "_fetch_channel_rates", fake)
    got = m.channel_rates([f"c{i}" for i in range(10)], "key", max_fetches=3)
    assert calls["n"] == 3, "quota AND latency cap must bound fetches per run"
    assert len(got) == 3


def test_channel_rates_stops_immediately_on_quota_exhaustion(monkeypatch):
    """One quotaExceeded means every remaining call fails too — stop, don't
    burn 100+ round trips inside a request handler."""
    calls = {"n": 0}

    def fake(cid, key):
        calls["n"] += 1
        raise m.QuotaExhausted("quotaExceeded")

    monkeypatch.setattr(m, "_fetch_channel_rates", fake)
    got = m.channel_rates([f"c{i}" for i in range(20)], "key")
    assert calls["n"] == 1, "must break out after the first quota error"
    assert got == {}


def test_channel_rates_without_key_returns_only_cached(monkeypatch):
    monkeypatch.setattr(m, "_fetch_channel_rates",
                        lambda c, k: (_ for _ in ()).throw(AssertionError("no key!")))
    assert m.channel_rates(["ch1", "ch2"], "") == {}


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


def test_low_outlier_is_not_penalised():
    """A low/absent outlier usually means thin data, not a weak topic —
    penalising on sparsity buried real signals."""
    strong_vel = [_v(vid="w", views=48000, age=24, query="fat loss tips", outlier=0.2)]
    weak_vel = [_v(vid="f", views=22000, age=24, query="gym motivation", outlier=1.0)]
    opps = build_opportunities([], strong_vel + weak_vel, FITNESS)
    assert opps[0].topic == "fat loss tips", "velocity should still win"


def test_acceleration_boosts_a_spiking_topic():
    """Measured acceleration is dimensionless, so it IS comparable between
    videos — a topic gaining 4x its own average rate outranks a steady one."""
    spiking = [_v(vid="s", views=24000, age=24, query="fat loss tips",
                  measured=4000.0)]          # lifetime 1,000/hr, now 4,000/hr
    steady = [_v(vid="t", views=26000, age=24, query="gym motivation",
                 measured=1050.0)]           # lifetime ~1,083/hr, flat
    opps = build_opportunities([], spiking + steady, FITNESS)
    assert opps[0].topic == "fat loss tips"


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
