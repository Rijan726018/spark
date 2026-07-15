"""Optional LLM polish for content ideas.

If ANTHROPIC_API_KEY or OPENAI_API_KEY is set, this rewrites the templated
hook + titles into sharper, scroll-stopping copy. One batched request per run
(all topics together) to keep token cost low. Any failure falls back silently
to the template output, so the tool never hard-depends on an LLM.
"""
from __future__ import annotations

import json
import os
import re

import requests

from .config import NicheConfig
from .models import Idea

_TIMEOUT = 30


def llm_provider() -> str | None:
    if os.getenv("ANTHROPIC_API_KEY", "").strip():
        return "anthropic"
    if os.getenv("OPENAI_API_KEY", "").strip():
        return "openai"
    return None


def _build_prompt(ideas: list[Idea], niche: NicheConfig,
                  profile: dict | None = None) -> str:
    rows = [
        {"i": n, "topic": idea.topic, "why_now": idea.why_now, "format": idea.format}
        for n, idea in enumerate(ideas)
    ]
    persona = ""
    if profile:
        bits = []
        if profile.get("channel"):
            bits.append(f"Their channel: {profile['channel'][:300]}")
        if profile.get("audience"):
            bits.append(f"Their audience: {profile['audience'][:200]}")
        if profile.get("tone"):
            bits.append(f"Their tone: {profile['tone'][:60]}")
        if bits:
            persona = (
                "\nPersonalize every hook and title for THIS creator — make it sound "
                "like something they would publish, angled at their audience:\n"
                + "\n".join(f"- {b}" for b in bits) + "\n"
            )
    return (
        f"You are a viral short-form content strategist for the '{niche.name}' niche.\n"
        f"{persona}"
        f"For each item below, write copy that stops the scroll. Never mention any year "
        f"except the current one. Return ONLY valid JSON: "
        f'an array of objects with keys "i" (int, matching input), "hook" (one punchy '
        f'sentence, no "hey guys"), and "titles" (array of exactly 3 distinct, '
        f"curiosity-driven titles under 70 chars each).\n\n"
        f"Items:\n{json.dumps(rows, ensure_ascii=False)}"
    )


def _extract_json(text: str):
    text = text.strip()
    # tolerate code fences or leading prose
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def _call_anthropic(prompt: str) -> str | None:
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    base = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
    model = os.getenv("TREND_LLM_MODEL", "claude-sonnet-4-5")
    try:
        r = requests.post(
            f"{base}/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": model, "max_tokens": 1500,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        return "".join(b.get("text", "") for b in data.get("content", []))
    except requests.RequestException as e:  # pragma: no cover - network
        print(f"[llm] anthropic call failed: {e}")
        return None


def _call_openai(prompt: str) -> str | None:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("TREND_LLM_MODEL", "gpt-4o-mini")
    try:
        r = requests.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "content-type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 1500},
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except (requests.RequestException, KeyError, IndexError) as e:  # pragma: no cover
        print(f"[llm] openai call failed: {e}")
        return None


def rewrite_ideas(ideas: list[Idea], niche: NicheConfig,
                  profile: dict | None = None) -> list[Idea]:
    """Polish hooks/titles in place via the available LLM. No-op if none/failure."""
    provider = llm_provider()
    if not provider or not ideas:
        return ideas

    prompt = _build_prompt(ideas, niche, profile)
    raw = _call_anthropic(prompt) if provider == "anthropic" else _call_openai(prompt)
    parsed = _extract_json(raw or "")
    if not parsed:
        return ideas

    by_i = {obj.get("i"): obj for obj in parsed if isinstance(obj, dict)}
    for n, idea in enumerate(ideas):
        obj = by_i.get(n)
        if not obj:
            continue
        hook = obj.get("hook")
        titles = obj.get("titles")
        if isinstance(hook, str) and hook.strip():
            idea.hook = hook.strip()
        if isinstance(titles, list) and len(titles) >= 1:
            idea.titles = [str(t).strip() for t in titles[:3] if str(t).strip()] or idea.titles
    return ideas
