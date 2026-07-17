"""Configuration: niche presets + runtime settings.

A niche is just a bundle of seed keywords (for relevance scoring against trends)
and YouTube search queries (for pulling working-format signals). Add a new niche
by dropping another entry into NICHE_PRESETS — the rest of the pipeline is generic.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class NicheConfig:
    name: str
    seed_keywords: list[str] = field(default_factory=list)
    youtube_queries: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)


NICHE_PRESETS: dict[str, NicheConfig] = {
    "fitness": NicheConfig(
        name="fitness",
        seed_keywords=[
            "fitness", "workout", "gym", "muscle", "weight loss", "diet",
            "protein", "nutrition", "calories", "cardio", "strength",
            "bodybuilding", "creatine", "supplement", "running", "yoga",
            "fat loss", "abs", "physique", "health", "ozempic", "glp-1",
            "cut", "bulk", "shred", "gains", "macro", "intermittent fasting",
        ],
        youtube_queries=[
            "fat loss tips",
            "muscle building workout for beginners",
            "what i eat in a day",
            "gym mistakes beginners make",
            "creatine benefits science",
            "beginner workout routine at home",
            "how to lose belly fat",
            "best exercises for abs",
            "high protein meal prep",
            "intermittent fasting results",
            "natural bodybuilding transformation",
            "gym motivation",
        ],
        exclude=["nsfw", "porn", "casino", "betting"],
    ),
    "trading": NicheConfig(
        name="trading",
        seed_keywords=[
            "trading", "stocks", "crypto", "bitcoin", "futures", "options",
            "day trading", "prop firm", "investing", "market", "ES", "NASDAQ",
            "S&P", "forex", "scalping", "recession", "fed", "interest rates",
        ],
        youtube_queries=[
            "day trading strategy",
            "prop firm challenge",
            "stock market analysis today",
            "crypto news",
            "trading psychology",
        ],
        exclude=["casino", "lottery"],
    ),
    "personal finance": NicheConfig(
        name="personal finance",
        seed_keywords=[
            "money", "budget", "budgeting", "investing", "saving", "savings",
            "debt", "credit score", "credit card", "side hustle",
            "passive income", "salary", "paycheck", "401k", "roth ira",
            "index fund", "net worth", "frugal", "cash stuffing",
            "financial freedom", "inflation", "rent", "mortgage", "taxes",
            "high yield savings", "emergency fund", "retire", "cost of living",
        ],
        youtube_queries=[
            "how to budget for beginners",
            "cash stuffing budget",
            "side hustles that actually work",
            "passive income ideas",
            "how i paid off debt",
            "roth ira explained",
            "index funds for beginners",
            "money mistakes to avoid",
            "no spend challenge",
            "how much i make",
            "living on one income",
            "financial freedom plan",
        ],
        exclude=["casino", "lottery", "betting", "get rich quick"],
    ),
    "faceless shorts": NicheConfig(
        name="faceless shorts",
        seed_keywords=[
            "faceless", "youtube automation", "cash cow", "shorts",
            "reddit stories", "ai voice", "text to speech", "stock footage",
            "monetization", "rpm", "cpm", "niche channel", "viral",
            "youtube shorts", "tiktok", "compilation", "storytelling",
            "ai video", "channel ideas", "watch hours", "subscribers",
        ],
        youtube_queries=[
            "faceless youtube channel ideas",
            "youtube automation step by step",
            "reddit stories channel tutorial",
            "make shorts with ai",
            "cash cow channel niches",
            "youtube shorts monetization explained",
            "best niches for youtube automation",
            "ai voiceover for youtube",
            "how to make faceless videos",
            "shorts that went viral",
            "youtube shorts strategy",
            "tiktok faceless account",
        ],
        exclude=["nsfw", "porn"],
    ),
    "ai news": NicheConfig(
        name="ai news",
        seed_keywords=[
            "AI", "artificial intelligence", "openai", "anthropic", "claude",
            "chatgpt", "gemini", "llm", "model", "agents", "robotics",
            "machine learning", "deepmind", "nvidia", "gpu", "benchmark",
            "open source", "regulation", "agi",
        ],
        youtube_queries=[
            "AI news this week",
            "openai announcement",
            "new AI model released",
            "AI agents explained",
            "best AI tools 2026",
            "AI replacing jobs",
            "anthropic claude news",
            "AI breakthrough",
        ],
        exclude=[],
    ),
    "tech": NicheConfig(
        name="tech",
        seed_keywords=[
            "AI", "artificial intelligence", "chatgpt", "claude", "coding",
            "programming", "software", "gadget", "iphone", "app", "startup",
            "machine learning", "developer", "tech", "gpu", "openai",
        ],
        youtube_queries=[
            "best AI tools",
            "coding tutorial",
            "best tech gadgets",
            "build app with AI",
            "software engineer day in the life",
            "AI news this week",
        ],
        exclude=[],
    ),
}


@dataclass
class Settings:
    geo: str = "US"
    youtube_api_key: str = ""
    youtube_days: int = 7              # only consider videos published in last N days
    max_videos_per_query: int = 12
    rss_url_tmpl: str = "https://trends.google.com/trending/rss?geo={geo}"
    out_dir: str = "content_digests"
    request_timeout: int = 10
    user_agent: str = "trend-engine/0.1 (+content research)"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            geo=os.getenv("TREND_GEO", "US"),
            youtube_api_key=os.getenv("YOUTUBE_API_KEY", "").strip(),
            youtube_days=int(os.getenv("TREND_YOUTUBE_DAYS", "7")),
            out_dir=os.getenv("TREND_OUT_DIR", "content_digests"),
        )


def resolve_niche(name: str) -> NicheConfig:
    """Look up a preset; if unknown, build a generic niche from the name itself."""
    key = (name or "").strip().lower()
    if key in NICHE_PRESETS:
        return NICHE_PRESETS[key]
    # Unknown niche: treat the words as both seeds and a YouTube query.
    words = [w for w in key.replace(",", " ").split() if w]
    return NicheConfig(
        name=key or "general",
        seed_keywords=words or ["news"],
        youtube_queries=[key] if key else [],
        exclude=[],
    )
