"""Idea expansion for Spark Pro: turn one brief idea into a full shooting script.

Follows the trend_engine.llm pattern: if an LLM key is configured the script is
written by the model; any failure (or no key) falls back to a structured
template built from the idea itself, so the endpoint always returns something
shootable. One request per expansion — the caller budgets these.
"""
from __future__ import annotations

import json
import re

from trend_engine.llm import _call_anthropic, _call_openai, llm_provider


def _extract_obj(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text.strip(), re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None


def _build_prompt(idea: dict, niche: str, profile: dict | None) -> str:
    persona = ""
    if profile:
        bits = [f"- Their {k}: {str(v)[:200]}" for k, v in
                (("channel", profile.get("channel")),
                 ("audience", profile.get("audience")),
                 ("tone", profile.get("tone"))) if v]
        if bits:
            persona = ("\nWrite it in THIS creator's voice, aimed at their "
                       "audience:\n" + "\n".join(bits) + "\n")
    is_short = "Short" in str(idea.get("format", ""))
    length = ("a 45-60 second short-form video: ~150 spoken words"
              if is_short else "an 8-12 minute video: section-by-section beats")
    return (
        f"You are a {niche} content scriptwriter. Expand this idea into a "
        f"complete, ready-to-shoot script for {length}.\n"
        f"{persona}\n"
        f"Idea:\n{json.dumps(idea, ensure_ascii=False)}\n\n"
        "Return ONLY valid JSON, one object with keys:\n"
        '  "title"       (the strongest single title),\n'
        '  "hook"        (word-for-word opening line, first 3 seconds),\n'
        '  "beats"       (array of {"t": timestamp string, "say": what to say, '
        '"show": what is on screen} — 5-8 beats),\n'
        '  "broll"       (array of 3-5 specific b-roll/visual ideas),\n'
        '  "description" (2-3 sentence video description with a CTA),\n'
        '  "hashtags"    (array of 5-8 hashtags without the # symbol),\n'
        '  "posting_tip" (one sentence: best time/format/platform note).'
    )


def _valid(script: dict) -> bool:
    return (isinstance(script.get("beats"), list) and len(script["beats"]) >= 3
            and bool(str(script.get("hook", "")).strip()))


def _template_script(idea: dict, niche: str) -> dict:
    """No-LLM fallback: a structured script assembled from the idea's own parts."""
    topic = str(idea.get("topic", "your topic"))
    titles = idea.get("titles") or [topic]
    outline = idea.get("outline") or []
    is_short = "Short" in str(idea.get("format", ""))

    beats = []
    for step in outline:
        # Outline lines look like "0–3s  : Hook — ..." or "Intro (0–30s): ..."
        t, _, say = str(step).partition(":")
        beats.append({"t": t.strip(), "say": say.strip() or str(step),
                      "show": "You on camera — cut every 2-3 seconds"})
    if not beats:
        beats = [
            {"t": "0-3s", "say": str(idea.get("hook", topic)),
             "show": "Best visual you have — result first"},
            {"t": "3-20s", "say": f"The one thing about {topic} most people miss.",
             "show": "Demo or screen recording"},
            {"t": "20-45s", "say": "Prove it: show the before/after or the numbers.",
             "show": "Proof shot"},
            {"t": "45-60s", "say": f"Follow for daily {niche} ideas.",
             "show": "You on camera, point at follow button"},
        ]

    return {
        "title": titles[0],
        "hook": str(idea.get("hook", f"Here's what nobody tells you about {topic}.")),
        "beats": beats,
        "broll": [
            f"Close-up of the key moment in {topic}",
            "Screen text overlay repeating the main number or claim",
            "Reaction shot / before-and-after split screen",
        ],
        "description": (f"{titles[0]} — everything you need to know, fast. "
                        f"Save this for later and follow for daily {niche} ideas."),
        "hashtags": [w for w in re.findall(r"[a-z0-9]+", topic.lower())][:4]
                    + [niche.replace(" ", ""), "shorts" if is_short else "youtube"],
        "posting_tip": ("Post Shorts in the morning your audience wakes up; "
                        "reply to the first 10 comments to feed the algorithm."),
        "llm_used": False,
    }


def expand_idea(idea: dict, niche: str, profile: dict | None = None) -> dict:
    """Expand an idea dict into a full script dict. Never raises."""
    provider = llm_provider()
    if provider:
        prompt = _build_prompt(idea, niche, profile)
        raw = _call_anthropic(prompt) if provider == "anthropic" else _call_openai(prompt)
        script = _extract_obj(raw or "")
        if script and _valid(script):
            script["llm_used"] = True
            return script
    return _template_script(idea, niche)
