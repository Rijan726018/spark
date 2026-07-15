"""Google Trends realtime RSS source — free, no API key.

The realtime feed (https://trends.google.com/trending/rss?geo=US) returns, per
trending topic: the title, an approximate search-traffic figure (e.g. "2000+"),
and a handful of related news headlines. That's enough to (a) measure how hot a
topic is and (b) score how relevant it is to a creator's niche.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import requests

from ..models import TrendItem


def _local(tag: str) -> str:
    """Strip any XML namespace, returning just the local tag name."""
    return tag.rsplit("}", 1)[-1].lower()


def _parse_traffic(text: str | None) -> int:
    if not text:
        return 0
    # "2,000+" / "20K+" / "1M+" -> integer
    t = text.strip().upper().replace(",", "").replace("+", "")
    m = re.match(r"([\d.]+)\s*([KM]?)", t)
    if not m:
        return 0
    num = float(m.group(1))
    mult = {"": 1, "K": 1_000, "M": 1_000_000}[m.group(2)]
    return int(num * mult)


def fetch_realtime_trends(geo: str = "US", timeout: int = 10,
                          user_agent: str = "trend-engine/0.1") -> list[TrendItem]:
    """Fetch and parse the realtime trends RSS. Returns [] on any failure."""
    url = f"https://trends.google.com/trending/rss?geo={geo}"
    try:
        resp = requests.get(url, headers={"User-Agent": user_agent}, timeout=timeout)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except (requests.RequestException, ET.ParseError) as e:  # pragma: no cover - network
        print(f"[google_trends] fetch failed: {e}")
        return []

    items: list[TrendItem] = []
    for item in root.iter():
        if _local(item.tag) != "item":
            continue
        title = ""
        traffic = 0
        news: list[str] = []
        for child in item:
            name = _local(child.tag)
            if name == "title":
                title = (child.text or "").strip()
            elif name == "approx_traffic":
                traffic = _parse_traffic(child.text)
            elif name == "news_item":
                for gc in child:
                    if _local(gc.tag) == "news_item_title" and gc.text:
                        news.append(gc.text.strip())
            elif name == "news_item_title" and child.text:
                news.append(child.text.strip())
        if title:
            items.append(TrendItem(title=title, approx_traffic=traffic, news_titles=news))
    return items
