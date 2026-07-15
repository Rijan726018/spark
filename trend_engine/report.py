"""Render the daily digest: a Markdown file plus a short console summary."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .models import Idea, Opportunity


def render_markdown(today: str, niche: str, opportunities: list[Opportunity],
                    ideas: list[Idea]) -> str:
    lines: list[str] = []
    lines.append(f"# Daily Content Brief — {niche.title()} — {today}")
    lines.append("")
    lines.append(f"_{len(ideas)} ready-to-shoot ideas, ranked by momentum. "
                 f"Generated from {len(opportunities)} signals._")
    lines.append("")

    lines.append("## Today's ideas")
    for i, idea in enumerate(ideas, 1):
        lines.append(f"### {i}. {idea.titles[0]}")
        lines.append(f"- **Momentum:** {idea.score:.0f}/100 · **Format:** {idea.format}")
        lines.append(f"- **Why now:** {idea.why_now}")
        lines.append(f"- **Hook:** {idea.hook}")
        lines.append("- **Title options:**")
        for t in idea.titles:
            lines.append(f"    - {t}")
        lines.append("- **Outline:**")
        for step in idea.outline:
            lines.append(f"    - {step}")
        lines.append("")

    lines.append("## Raw signals")
    for opp in opportunities[:20]:
        ev = " · ".join(opp.evidence[:2])
        lines.append(f"- `{opp.score:5.1f}` [{opp.kind}] {opp.topic} — {ev}")
    lines.append("")
    return "\n".join(lines)


def render_console(niche: str, ideas: list[Idea]) -> str:
    out = [f"\n=== Daily Content Brief: {niche} — top {len(ideas)} ideas ===\n"]
    for i, idea in enumerate(ideas, 1):
        out.append(f"{i:>2}. [{idea.score:5.1f}] {idea.titles[0]}")
        out.append(f"      {idea.format} · {idea.why_now}")
    out.append("")
    return "\n".join(out)


def save_digest(out_dir: str, today: str, niche: str,
                opportunities: list[Opportunity], ideas: list[Idea]) -> dict:
    """Write both <date>.md and <date>.json. Returns the paths written."""
    d = Path(out_dir) / niche
    d.mkdir(parents=True, exist_ok=True)
    md_path = d / f"{today}.md"
    json_path = d / f"{today}.json"

    md_path.write_text(render_markdown(today, niche, opportunities, ideas), encoding="utf-8")
    json_path.write_text(json.dumps({
        "date": today,
        "niche": niche,
        "opportunities": [o.to_dict() for o in opportunities],
        "ideas": [i.to_dict() for i in ideas],
    }, indent=2), encoding="utf-8")

    return {"markdown": str(md_path), "json": str(json_path)}
