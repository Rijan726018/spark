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
    channel_id: str = ""
    duration_s: int = 0
    # Views/hr measured between two snapshots — the "rising right now" number.
    # Only ever compared against the SAME video's lifetime rate, never against
    # another video's, because the two are different quantities.
    measured_velocity: float | None = None
    # This video's views/hr ÷ its channel's median views/hr for the same
    # format. >1 means it is beating its own channel's normal — the real
    # "this format is winning" signal, independent of channel size.
    outlier: float | None = None

    @property
    def velocity(self) -> float:
        """Lifetime views/hour. Deliberately NOT the measured rate: ranking
        compares videos against each other, so every video must be measured on
        the same basis or first-sighted videos would outrank observed ones."""
        return self.views / max(self.age_hours, 1.0)

    # Kept as an explicit alias so callers reading ranking code see the basis.
    lifetime_velocity = velocity

    @property
    def current_velocity(self) -> float:
        """Best available views/hr for DISPLAY — measured when we have it."""
        return (self.measured_velocity if self.measured_velocity is not None
                else self.velocity)

    @property
    def acceleration(self) -> float | None:
        """measured ÷ lifetime rate. >1 means it is speeding up right now.
        Dimensionless, so it IS comparable between videos."""
        if self.measured_velocity is None:
            return None
        base = self.velocity
        return (self.measured_velocity / base) if base > 0 else None

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
    outlier: float | None = None  # best supporting video's views ÷ channel median
    measured: bool = False        # True when velocity came from snapshot history

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
    outlier: float | None = None  # e.g. 14.2 → "14x this channel's normal"
    measured: bool = False        # velocity is snapshot-measured, not estimated

    def to_dict(self) -> dict:
        d = asdict(self)
        d["score"] = round(self.score, 1)
        return d
