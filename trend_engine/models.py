"""Shared data models for the trend engine."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict


@dataclass
class TrendItem:
    """A single trending search topic from Google Trends realtime RSS."""
    title: str
    approx_traffic: int = 0
    news_titles: list[str] = field(default_factory=list)
    source: str = "google_trends"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class VideoItem:
    """A YouTube video used as a 'what format is working right now' signal."""
    video_id: str
    title: str
    channel: str
    views: int
    age_hours: float
    query: str          # the niche query that surfaced it
    url: str = ""
    source: str = "youtube"

    @property
    def velocity(self) -> float:
        """Views per hour since publish — the core momentum signal."""
        return self.views / max(self.age_hours, 1.0)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["velocity"] = round(self.velocity, 2)
        return d


@dataclass
class Opportunity:
    """A ranked content opportunity backed by one or more signals."""
    topic: str
    score: float                  # 0-100 normalised
    kind: str                     # "rising_search" | "working_format"
    evidence: list[str] = field(default_factory=list)
    raw_metric: float = 0.0       # traffic or avg-velocity, pre-normalisation
    age_hours: float = 0.0        # age of the freshest supporting signal

    def to_dict(self) -> dict:
        d = asdict(self)
        d["score"] = round(self.score, 1)
        return d


@dataclass
class Idea:
    """A concrete, ready-to-shoot content idea derived from an Opportunity."""
    topic: str
    hook: str
    titles: list[str]
    format: str                   # "Short (<60s)" | "Long-form (8-12 min)"
    outline: list[str]
    why_now: str
    score: float = 0.0
    kind: str = ""                # propagated from Opportunity
    source_url: str = ""          # YouTube URL of the best reference video
    source_stat: str = ""         # human-readable stat, e.g. "12.7M views · 152h"
    source_age_hours: float = 0.0 # age of the freshest supporting signal

    def to_dict(self) -> dict:
        d = asdict(self)
        d["score"] = round(self.score, 1)
        return d
