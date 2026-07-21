"""Idea synthesis — turn ranked Opportunities into ready-to-shoot content ideas.

v2 improvements:
  * Topics are now clean query phrases ("fat loss tips") not raw viral titles,
    so templates produce grammatical, usable copy without an LLM.
  * Kind-aware templates: YouTube format signals get "make your version" framing;
    rising search trends get "ride this wave now" framing.
  * Titles are title-cased and deduplicated per idea.
  * Source URL and stat are propagated so the UI can show a reference link.
"""
from __future__ import annotations

import os
import re
from datetime import date

from .config import NicheConfig
from .models import Idea, Opportunity

_WORD = re.compile(r"[a-z0-9']+")
_STOP = {
    "the","a","an","of","to","for","and","or","in","on","with","is","are",
    "this","that","your","you","my","how","what","why","best","vs","shorts",
    "official","video","ep","part","we","it","at","by","as","so","do",
    "top","new","full","real","life","day","days","week","year","time",
}

# ── templates keyed by kind ────────────────────────────────────────────────────
_TMPLS: dict[str, list[str]] = {
    "working_format": [
        "{kp}: the complete guide ({year})",
        "{kp} — everything you're doing wrong",
        "I tried {kp} for 30 days (honest results)",
        "The science of {kp} nobody explains properly",
        "{kp}: 5 mistakes that are costing you results",
        "Stop approaching {kp} like this — do this instead",
        "The {kp} method that's actually working right now",
        "{kp} explained in under 60 seconds",
        "Why your {kp} isn't working (and how to fix it)",
        "I tested every {kp} method — here's what won",
    ],
    "rising_search": [
        "Everyone's talking about {kp} — here's why",
        "{kp}: the real story behind the trend",
        "Is {kp} actually worth it? I found out so you don't have to",
        "{kp} — what no one is telling you",
        "The truth about {kp} (most people get this wrong)",
        "{kp} explained for beginners",
    ],
}

_HOOKS: dict[str, list[str]] = {
    "working_format": [
        "Cut straight to your best result — no intro. Show the outcome of {kp}, then walk back to how.",
        "Lead with the mistake: 'You're doing {kp} wrong, and it's quietly killing your results.'",
        "Open with the number: state one shocking stat about {kp} before anything else.",
        "Start mid-action on {kp} — show yourself already doing it, then cut to the setup.",
        "Contrast hook: show a common {kp} fail, then your version that worked.",
    ],
    "rising_search": [
        "Open with: 'If you haven't heard about {kp} yet, you will — and here's what matters.'",
        "Lead with urgency: '{kp} is trending for a reason. Here's what the algorithm isn't showing you.'",
        "Start with a take: 'Everyone's sharing {kp} content right now. Here's the part that's actually true.'",
    ],
}

_YEAR = str(date.today().year)


# Conventional small words that stay lowercase mid-title ("What I Eat in a Day").
_SMALL = {"a", "an", "the", "and", "but", "or", "for", "nor", "on", "at",
          "to", "from", "by", "of", "in", "with", "as", "is", "vs"}

# Words that must render fully uppercase regardless of position.
_ACRONYMS = {"ai", "llm", "gpu", "cpu", "api", "vr", "ar", "pc", "ps5", "tv",
             "es", "nq", "spy", "qqq", "etf", "ipo", "glp-1", "hiit", "bmi"}


def _title_case(s: str) -> str:
    """Title-case: capitalize words except small words mid-title; keep acronyms upper."""
    words = s.split()
    out = []
    for i, w in enumerate(words):
        low = w.lower()
        if low in _ACRONYMS:
            out.append(low.upper())
        elif i == 0 or low not in _SMALL:
            out.append("I" if low == "i" else w.capitalize())
        else:
            out.append(low)
    return " ".join(out)


def _keyphrase(topic: str) -> str:
    """Extract a clean 3-5 word phrase from a messy topic (trend titles)."""
    cleaned = re.sub(r"[\[\(\|].*?[\]\)\|]", " ", topic).lower()
    words = [w for w in _WORD.findall(cleaned) if w not in _STOP and len(w) > 1]
    phrase = " ".join(words[:6]).strip()
    return phrase or topic.strip()


_LEAD_FILLER = re.compile(r"^(how to|best|top \d*|the)\s+", re.IGNORECASE)
_ANY_YEAR = re.compile(r"\b20\d{2}\b")


def _scrub_years(text: str) -> str:
    """Remove any year mention that isn't the current year.

    Stale years ('best AI tools 2025') make ideas look outdated even when the
    underlying signal is hot today. We strip the old year rather than swap it
    — templates re-add the current year where it reads naturally.
    """
    current = _YEAR
    out = _ANY_YEAR.sub(lambda m: m.group(0) if m.group(0) == current else "", text)
    return re.sub(r"\s{2,}", " ", out).strip(" -–—:")


def _clean_query(topic: str) -> str:
    """Light cleanup for topics that are already grammatical query phrases.

    Unlike _keyphrase, this never strips stop-words — 'what i eat in a day'
    must survive intact. Only leading filler ('how to', 'best') and stale
    years are removed so the phrase slots into templates.
    """
    q = _scrub_years(topic.strip().lower())
    q = _LEAD_FILLER.sub("", q, count=1)
    return q.strip() or topic.strip().lower()


def _pick(lst: list[str], idx: int) -> str:
    return lst[idx % len(lst)]


def _mid_case(kp: str) -> str:
    """Lowercase a phrase for mid-sentence use, preserving acronyms and 'I'."""
    out = []
    for w in kp.lower().split():
        if w in _ACRONYMS:
            out.append(w.upper())
        elif w == "i":
            out.append("I")
        else:
            out.append(w)
    return " ".join(out)


def _fill(tmpl: str, kp: str, year: str) -> str:
    """Fill a template with position-aware casing.

    Title-case the keyphrase when it opens the title; keep it lowercase
    mid-sentence ('I tried lose belly fat…' not 'I tried Lose Belly Fat…').
    The final string always starts with a capital letter.
    """
    val = _title_case(kp) if tmpl.startswith("{kp}") else _mid_case(kp)
    s = tmpl.format(kp=val, year=year)
    return s[0].upper() + s[1:]


def _source_from_evidence(ev: list[str]) -> tuple[str, str]:
    """Extract (source_url, source_stat) from an evidence list."""
    url = next((e for e in ev if e.startswith("http")), "")
    stat = ev[0] if ev else ""
    return url, stat


def _make_idea(opp: Opportunity, niche: NicheConfig, idx: int) -> Idea:
    kind = opp.kind or "working_format"
    # Query topics are already grammatical phrases — clean lightly. Trend
    # titles are messy and need keyword extraction. Both get stale years scrubbed.
    kp = _clean_query(opp.topic) if kind == "working_format" else _scrub_years(_keyphrase(opp.topic))
    kp_title = _title_case(kp)

    tmpls = _TMPLS.get(kind, _TMPLS["working_format"])
    hooks = _HOOKS.get(kind, _HOOKS["working_format"])

    # Three distinct titles (spread across the template list)
    seen_titles: set[str] = set()
    titles: list[str] = []
    for offset in range(len(tmpls)):
        candidate = _fill(_pick(tmpls, idx + offset), kp, _YEAR)
        if candidate not in seen_titles:
            seen_titles.add(candidate)
            titles.append(candidate)
        if len(titles) == 3:
            break

    hook = _pick(hooks, idx).format(kp=_mid_case(kp))

    is_short = kind == "rising_search" or opp.score >= 70
    fmt = "Short (<60s)" if is_short else "Long-form (8-12 min)"

    if is_short:
        outline = [
            f"0–3s  : Hook — {kp_title} claim or surprising result",
            "3–15s : The one insight — deliver value immediately",
            "15–45s: Quick proof, demo, or before/after",
            f"45–60s: CTA — 'follow for daily {niche.name} tips'",
        ]
    else:
        outline = [
            f"Intro (0–30s): Hook — why {kp_title} matters right now",
            "Section 1 (30s–2m): The common mistake everyone makes",
            "Section 2 (2–6m): Your method — step by step with evidence",
            "Section 3 (6–9m): Results, proof, real-world example",
            "Outro (9–12m): Recap + CTA + next-video tease",
        ]

    if kind == "rising_search":
        stat = opp.evidence[0] if opp.evidence else "rising interest"
        why = f"Spiking in search right now — {stat}. Ride the wave before it peaks."
    else:
        # Lead with recency when the surfaced video is fresh — this is what
        # makes the card visibly change day to day as new videos catch fire.
        # Deliberately does NOT repeat source_stat (shown as the hero metric).
        age_h = opp.age_hours or 0
        if 0 < age_h <= 48:
            why = f"Rising right now — the hottest video is only {round(age_h)}h old."
        else:
            why = "This format is peaking in your niche right now."
        group = next((e for e in opp.evidence if e.endswith("views/hr")), None)
        if group:
            why += f" Across the topic: {group}."

    url, source_stat = _source_from_evidence(opp.evidence)

    return Idea(
        topic=opp.topic,
        hook=hook,
        titles=titles,
        format=fmt,
        outline=outline,
        why_now=why,
        score=opp.score,
        kind=kind,
        source_url=url,
        source_stat=source_stat,
        source_age_hours=opp.age_hours,
    )


def generate_ideas(opportunities: list[Opportunity], niche: NicheConfig,
                   top: int = 10) -> list[Idea]:
    return [_make_idea(opp, niche, i) for i, opp in enumerate(opportunities[:top])]


def llm_available() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY", "").strip()
                or os.getenv("OPENAI_API_KEY", "").strip())
