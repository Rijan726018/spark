"""Deterministic tests for the trend engine — no network required.

These feed synthetic Google Trends + YouTube signals through the real
aggregation and idea-generation code, validating the path that activates
once a YouTube API key is configured.
"""
from trend_engine.aggregate import build_opportunities, relevance
from trend_engine.config import resolve_niche
from trend_engine.ideas import _keyphrase, generate_ideas
from trend_engine.models import TrendItem, VideoItem


FITNESS = resolve_niche("fitness")


def _video(title, views, age_hours, query="fat loss tips", vid="abc"):
    return VideoItem(video_id=vid, title=title, channel="FitChan", views=views,
                     age_hours=age_hours, query=query,
                     url=f"https://youtube.com/watch?v={vid}")


def test_relevance_counts_niche_keywords():
    assert relevance("Best protein for muscle growth", FITNESS) >= 2
    assert relevance("Red Sox win the game", FITNESS) == 0


def test_relevance_hard_excludes():
    niche = resolve_niche("fitness")
    assert relevance("casino bonus workout", niche) == -1


def test_velocity_orders_query_groups():
    vids = [
        _video("Slow video about creatine", views=1000, age_hours=100,
               query="creatine benefits science", vid="slow"),
        _video("Viral fat loss truth", views=500000, age_hours=10,
               query="fat loss tips", vid="fast"),
    ]
    opps = build_opportunities([], vids, FITNESS)
    assert len(opps) == 2, "one opportunity per query group"
    # The higher-velocity query group must rank first, topic = clean query.
    assert opps[0].topic == "fat loss tips"
    assert opps[0].score >= opps[-1].score


def test_groups_by_query_and_surfaces_best_video():
    vids = [
        _video("Slow video about creatine", views=1000, age_hours=100,
               query="fat loss tips", vid="slow"),
        _video("Viral fat loss truth", views=500000, age_hours=10,
               query="fat loss tips", vid="fast"),
    ]
    opps = build_opportunities([], vids, FITNESS)
    assert len(opps) == 1, "same query collapses to one opportunity"
    opp = opps[0]
    assert opp.topic == "fat loss tips"
    # Best (highest-velocity) video is the reference link in the evidence.
    assert any("watch?v=fast" in e for e in opp.evidence)
    assert not any("watch?v=slow" in e for e in opp.evidence)


def test_trends_gated_by_relevance():
    trends = [
        TrendItem(title="New diet trend everyone loves", approx_traffic=5000,
                  news_titles=["This weight loss diet is spiking"]),
        TrendItem(title="Soccer match result", approx_traffic=90000,
                  news_titles=["Big game last night"]),
    ]
    opps = build_opportunities(trends, [], FITNESS)
    topics = [o.topic for o in opps]
    assert "New diet trend everyone loves" in topics
    assert "Soccer match result" not in topics  # off-niche, excluded despite high traffic


def test_dedupe_collapses_similar_topics():
    vids = [
        _video("The truth about creatine supplements", 100000, 5, vid="a"),
        _video("The truth about creatine supplements!!!", 90000, 5, vid="b"),
    ]
    opps = build_opportunities([], vids, FITNESS)
    assert len(opps) == 1, "near-identical titles should collapse to one"


def test_generate_ideas_shape():
    vids = [_video("5 fat loss mistakes you're making", 200000, 8)]
    opps = build_opportunities([], vids, FITNESS)
    ideas = generate_ideas(opps, FITNESS, top=5)
    assert ideas
    idea = ideas[0]
    assert len(idea.titles) == 3
    assert len(set(idea.titles)) == 3, "titles must be distinct"
    assert idea.hook
    assert idea.outline
    assert idea.format in ("Short (<60s)", "Long-form (8-12 min)")
    # v2: source link + stat propagate so the UI can render evidence.
    assert idea.kind == "working_format"
    assert idea.source_url.startswith("http")
    assert idea.source_stat


def test_idea_titles_built_from_clean_query():
    """Titles come from the clean query phrase, not the messy viral title."""
    vids = [_video("POV: can these Gen Z boys eat \U0001f525 #shorts", 900000, 12,
                   query="high protein meal prep")]
    opps = build_opportunities([], vids, FITNESS)
    ideas = generate_ideas(opps, FITNESS, top=3)
    blob = " ".join(ideas[0].titles).lower()
    assert "protein meal prep" in blob
    assert "pov" not in blob and "gen z boys" not in blob


def test_keyphrase_strips_noise():
    kp = _keyphrase("[OFFICIAL] The BEST workout for abs (2026) | Part 1")
    assert "workout" in kp
    assert "official" not in kp.lower()


def test_empty_inputs_dont_crash():
    opps = build_opportunities([], [], FITNESS)
    ideas = generate_ideas(opps, FITNESS)
    assert opps == []
    assert ideas == []


def test_stale_years_scrubbed_from_titles():
    """No generated copy should ever contain a year older than the current one."""
    from datetime import date
    vids = [_video("Best AI tools you need", 50000, 24, query="best ai tools 2025")]
    opps = build_opportunities([], vids, resolve_niche("tech"))
    ideas = generate_ideas(opps, resolve_niche("tech"), top=3)
    blob = " ".join(ideas[0].titles) + ideas[0].hook
    for y in range(2020, date.today().year):
        assert str(y) not in blob, f"stale year {y} leaked into: {blob}"


def test_recency_boost_prefers_fresher_topic():
    """At equal velocity, the topic with the fresher best-video ranks higher."""
    fresh = [_video(f"Fresh video {i}", 24000, 24, query="fat loss tips", vid=f"f{i}")
             for i in range(3)]           # 1000/hr each, 1 day old
    stale = [_video(f"Stale video {i}", 144000, 144, query="gym motivation", vid=f"s{i}")
             for i in range(3)]           # 1000/hr each, 6 days old
    opps = build_opportunities([], fresh + stale, FITNESS)
    assert opps[0].topic == "fat loss tips"
    assert opps[0].score > opps[1].score


def test_idea_carries_source_age():
    vids = [_video("A video", 100000, 30)]
    opps = build_opportunities([], vids, FITNESS)
    ideas = generate_ideas(opps, FITNESS, top=1)
    assert ideas[0].source_age_hours == 30
