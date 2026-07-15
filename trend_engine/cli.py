"""CLI entry point.

Examples:
    python -m trend_engine --niche fitness
    python -m trend_engine --niche trading --top 8 --no-youtube
    YOUTUBE_API_KEY=xxx python -m trend_engine --niche fitness
"""
from __future__ import annotations

import argparse

from .config import NICHE_PRESETS, Settings
from .pipeline import run


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="trend_engine",
        description="Daily content-idea generator from live trend signals.")
    ap.add_argument("--niche", default="fitness",
                    help=f"Niche name. Presets: {', '.join(NICHE_PRESETS)}. "
                         "Unknown names become a generic niche from the words given.")
    ap.add_argument("--geo", default=None, help="Region code (default US / $TREND_GEO).")
    ap.add_argument("--top", type=int, default=10, help="How many ideas to generate.")
    ap.add_argument("--youtube-days", type=int, default=None,
                    help="Only consider videos published in the last N days.")
    ap.add_argument("--no-youtube", action="store_true",
                    help="Skip YouTube even if a key is set (Trends only).")
    ap.add_argument("--out-dir", default=None, help="Output directory for digests.")
    args = ap.parse_args(argv)

    settings = Settings.from_env()
    if args.geo:
        settings.geo = args.geo
    if args.youtube_days is not None:
        settings.youtube_days = args.youtube_days
    if args.out_dir:
        settings.out_dir = args.out_dir

    result = run(args.niche, settings=settings, top=args.top,
                 use_youtube=not args.no_youtube)

    print(result["console"])
    c = result["counts"]
    print(f"Signals: {c['trends']} trends, {c['videos']} videos -> "
          f"{c['opportunities']} opportunities -> {c['ideas']} ideas")
    print(f"Saved:\n  {result['paths']['markdown']}\n  {result['paths']['json']}")
    if c["videos"] == 0:
        print("\nTip: set YOUTUBE_API_KEY for niche-specific video momentum "
              "(free key from console.cloud.google.com -> 'YouTube Data API v3').")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
