"""End-to-end pipeline: sources -> aggregate -> ideas -> digest."""
from __future__ import annotations

from datetime import date

from .aggregate import build_opportunities
from .config import NicheConfig, Settings, resolve_niche
from .ideas import generate_ideas
from .llm import llm_provider, rewrite_ideas
from .report import render_console, save_digest
from .sources import google_trends, youtube


def run(niche_name: str, settings: Settings | None = None, top: int = 10,
        use_youtube: bool = True, use_llm: bool = True,
        profile: dict | None = None) -> dict:
    settings = settings or Settings.from_env()
    niche: NicheConfig = resolve_niche(niche_name)
    today = date.today().isoformat()

    trends = google_trends.fetch_realtime_trends(
        geo=settings.geo, timeout=settings.request_timeout,
        user_agent=settings.user_agent)

    videos = []
    if use_youtube:
        videos = youtube.collect(
            niche.youtube_queries, settings.youtube_api_key,
            days=settings.youtube_days, max_results=settings.max_videos_per_query,
            region=settings.geo, timeout=settings.request_timeout)

    opportunities = build_opportunities(trends, videos, niche)
    ideas = generate_ideas(opportunities, niche, top=top)

    llm_used = False
    if use_llm and ideas and llm_provider():
        rewrite_ideas(ideas, niche, profile=profile)
        llm_used = True
    elif profile and profile.get("audience") and ideas:
        # Template-level personalization fallback: aim the CTA at their audience.
        aud = str(profile["audience"])[:60]
        for idea in ideas:
            if idea.outline:
                idea.outline[-1] = idea.outline[-1].split("CTA")[0] + f"CTA aimed at {aud}"

    paths = save_digest(settings.out_dir, today, niche.name, opportunities, ideas)

    return {
        "niche": niche.name,
        "date": today,
        "llm_used": llm_used,
        "counts": {"trends": len(trends), "videos": len(videos),
                   "opportunities": len(opportunities), "ideas": len(ideas)},
        "paths": paths,
        "console": render_console(niche.name, ideas),
        "ideas": ideas,
        "opportunities": opportunities,
    }
