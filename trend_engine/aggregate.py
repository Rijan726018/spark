"""Aggregation & ranking — turn raw signals into a ranked list of Opportunities.

Key design decision (v2):
  YouTube videos are now grouped BY QUERY, not one-per-video.
  The query ("fat loss tips") becomes the idea topic — clean and grammatical.
  The best video in the group (highest velocity) is surfaced as a reference link.

Two signal types:
  * Google Trends items  -> "rising_search"  (metric = approx_traffic, gated by relevance)
  * YouTube groups       -> "working_format" (metric = average views/hr across the group)
"""
from __future__ import annotations

import re
from collections import defaultdict

from .config import NicheConfig
from .models import Opportunity, TrendItem, VideoItem

_WORD = re.compile(r"[a-z0-9']+")

# Recency weight: half-life 48h, floor 0.4. A video rising *today* is worth up
# to ~2.5x a week-old video at the same raw velocity, so momentum outranks size
# and the feed reorders daily as new videos catch fire — instead of perennial
# giants ("what i eat in a day") pinning the top spot for a week straight.
_RECENCY_HALF_LIFE_H = 48.0
_RECENCY_FLOOR = 0.4


def _recency_weight(age_hours: float) -> float:
    return _RECENCY_FLOOR + (1.0 - _RECENCY_FLOOR) * (
        0.5 ** (max(age_hours, 0.0) / _RECENCY_HALF_LIFE_H))


def _tokens(text: str) -> set[str]:
    return set(_WORD.findall((text or "").lower()))


def relevance(text: str, niche: NicheConfig) -> int:
    """Count how many niche seed keywords appear in `text` (phrase-aware)."""
    low = (text or "").lower()
    if any(x and x.lower() in low for x in niche.exclude):
        return -1  # hard-exclude
    hits = 0
    for kw in niche.seed_keywords:
        kw = kw.lower()
        if " " in kw:
            hits += (1 if kw in low else 0)
        elif kw in _tokens(low):
            hits += 1
    return hits


def _normalize(values: list[float]) -> list[float]:
    if not values:
        return []
    hi = max(values)
    return [100.0 * v / hi if hi > 0 else 0.0 for v in values]


def _dedupe(opps: list[Opportunity]) -> list[Opportunity]:
    """Collapse near-duplicate topics (Jaccard ≥ 0.6 on word tokens)."""
    kept: list[Opportunity] = []
    seen: list[set[str]] = []
    for opp in opps:
        toks = _tokens(opp.topic)
        dup_idx = -1
        for i, prev in enumerate(seen):
            if toks and prev:
                j = len(toks & prev) / len(toks | prev)
                if j >= 0.6:
                    dup_idx = i
                    break
        if dup_idx >= 0:
            kept[dup_idx].evidence.extend(opp.evidence)
            kept[dup_idx].score = max(kept[dup_idx].score, opp.score)
        else:
            kept.append(opp)
            seen.append(toks)
    return kept


def _fmt_views(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.0f}K"
    return str(n)


def build_opportunities(trends: list[TrendItem], videos: list[VideoItem],
                        niche: NicheConfig, min_trend_relevance: int = 1) -> list[Opportunity]:
    opps: list[Opportunity] = []

    # ── Google Trends → rising_search (niche-gated) ───────────────────────
    relevant = []
    for t in trends:
        blob = t.title + " " + " ".join(t.news_titles)
        rel = relevance(blob, niche)
        if rel >= min_trend_relevance:
            relevant.append((t, rel))

    trend_scores = _normalize([t.approx_traffic for t, _ in relevant])
    for (t, rel), norm in zip(relevant, trend_scores):
        score = 0.7 * norm + 0.3 * min(rel * 25, 100)
        ev = [f"~{t.approx_traffic:,} searches right now"]
        if t.news_titles:
            ev.append(t.news_titles[0])
        opps.append(Opportunity(topic=t.title, score=score, kind="rising_search",
                                evidence=ev, raw_metric=float(t.approx_traffic)))

    # ── YouTube → working_format, grouped BY QUERY ────────────────────────
    # The query is already a clean niche phrase ("fat loss tips"), so using it
    # as the idea topic produces grammatical, useful titles — unlike raw video
    # titles which are noisy ("POV: can these Gen Z boys eat 🔥 #shorts").
    query_groups: dict[str, list[VideoItem]] = defaultdict(list)
    for v in videos:
        if relevance(v.title, niche) >= 0:  # drop hard-excluded
            query_groups[v.query].append(v)

    # Outlier multiplier: a video beating its own channel's normal is a format
    # signal, not just a big-channel artifact. Bounded so one freak 50x video
    # can't dominate the whole feed, and neutral (1.0) when unknown.
    def _outlier_mult(group: list[VideoItem]) -> float:
        scores = [v.outlier for v in group if v.outlier]
        if not scores:
            return 1.0
        best = max(scores)
        if best >= 10:
            return 1.5
        if best >= 5:
            return 1.35
        if best >= 2:
            return 1.2
        if best < 0.5:      # underperforming its own channel — weak signal
            return 0.85
        return 1.0

    group_metrics: list[tuple[str, list[VideoItem], float, float]] = []
    for query, group in query_groups.items():
        # Rank by recency-weighted velocity so a video rising today outranks a
        # week-old mega-hit at the same raw velocity. Sorting by the weighted
        # value also makes the surfaced reference video (group[0]) the freshest
        # riser, not the biggest evergreen — so the card's stat changes daily.
        group.sort(key=lambda v: v.velocity * _recency_weight(v.age_hours),
                   reverse=True)
        weighted = [v.velocity * _recency_weight(v.age_hours) for v in group]
        # The group's strength is its single hottest fresh video (a breakout
        # surfaces), lightly blended with the average so a consistently-hot
        # format isn't penalised for having depth.
        rank_metric = 0.75 * max(weighted) + 0.25 * (sum(weighted) / len(weighted))
        rank_metric *= _outlier_mult(group)
        avg_vel = sum(v.velocity for v in group) / len(group)   # raw, for display
        group_metrics.append((query, group, rank_metric, avg_vel))

    vel_scores = _normalize([m for _, _, m, _ in group_metrics])
    for (query, group, rank_metric, avg_vel), norm in zip(group_metrics, vel_scores):
        best = group[0]
        age_days = best.age_hours / 24
        age_str = f"{age_days:.0f}d" if age_days >= 1 else f"{best.age_hours:.0f}h"
        ev = [
            f"{_fmt_views(best.views)} views · {age_str} old · {best.velocity:,.0f}/hr",
            f'"{best.title[:60]}{"…" if len(best.title) > 60 else ""}"',
            best.channel,
            best.url,
        ]
        if len(group) > 1:
            ev.insert(1, f"{len(group)} videos averaging {avg_vel:,.0f} views/hr")
        if best.outlier and best.outlier >= 1.5:
            ev.insert(1, f"{best.outlier:.1f}x that channel's normal views")
        opps.append(Opportunity(topic=query, score=norm, kind="working_format",
                                evidence=ev, raw_metric=avg_vel,
                                age_hours=best.age_hours,
                                outlier=best.outlier,
                                measured=best.measured_velocity is not None))

    opps.sort(key=lambda o: o.score, reverse=True)
    return _dedupe(opps)
