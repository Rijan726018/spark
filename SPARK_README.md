# ⚡ Spark — Daily Content Brief

A mobile-first PWA that tells creators **what to make today**, without hours of
doomscrolling for research. It pulls live momentum signals, ranks what's rising
in your niche, and turns the top signals into ready-to-shoot ideas — hook,
3 title options, format call (Short vs Long-form), and a timed outline.

## How it works

```
Google Trends (free, no key)──┐
                              ├─► relevance gate ─► velocity ranking ─► idea
YouTube Data API (free key) ──┘    (niche keywords)   (views/hr,        synthesis ─► PWA / Markdown / JSON
                                                       query-grouped)   (+ optional LLM polish)
```

- **Google Trends realtime RSS** — what's spiking in search right now (traffic + news context).
- **YouTube Data API v3** — for each niche query, recent videos ranked by
  views-per-hour. Videos are grouped **by query**, so ideas are anchored to clean
  phrases ("high protein meal prep"), with the hottest video surfaced as a
  reference link.
- **Idea synthesis** — kind-aware templates (trend ideas get "ride the wave"
  framing; YouTube ideas get "make your version" framing). If `ANTHROPIC_API_KEY`
  or `OPENAI_API_KEY` is set, an LLM rewrites hooks/titles for extra punch; with
  no key it falls back to templates silently.

## Run it

```bash
# 1. Keys (.env in project root, git-ignored)
YOUTUBE_API_KEY=...        # required for niche signal — free from console.cloud.google.com
ANTHROPIC_API_KEY=...      # optional — LLM-polished hooks/titles

# 2. Start the app
uvicorn trend_api:app --port 8100

# 3. Open http://localhost:8100  (on your phone: http://<your-mac-ip>:8100,
#    then Share → Add to Home Screen for the full-screen app)
```

CLI (no server needed):

```bash
python3 -m trend_engine --niche fitness --top 10        # writes content_digests/fitness/<date>.{md,json}
python3 -m trend_engine --niche trading --no-youtube    # trends only
python3 -m trend_engine --niche "vegan cooking"         # any custom niche
```

## Niches

Presets live in `trend_engine/config.py` (`fitness`, `trading`, `tech`), each a
bundle of seed keywords (relevance gate) + YouTube queries (momentum probes).
Add a niche by adding one entry — everything else is generic. Unknown niche
names become a generic niche built from the words given.

## Tests

```bash
python3 -m pytest tests/test_trend_engine.py   # 10 tests, no network needed
```

## Daily automation

Drop a cron line to get a fresh brief every morning:

```bash
0 7 * * * cd /path/to/project && python3 -m trend_engine --niche fitness --top 10
```

## Launch checklist (before charging money)

- [ ] Restrict the YouTube key to the YouTube Data API v3 (console.cloud.google.com → key → API restrictions)
- [ ] YouTube quota is 10,000 units/day free ≈ 90 brief generations/day (12 queries × ~100 units + details). Cache briefs per niche/day server-side before going multi-user.
- [ ] Deploy: any host that runs `uvicorn trend_api:app` (Fly.io / Railway / a $5 VPS). Put the `.env` on the server, never in git.
- [ ] Add auth + Stripe before public launch — currently the API is open.

## Layout

```
trend_engine/
  config.py        # niche presets + Settings (env-driven)
  env.py           # zero-dep .env loader
  sources/
    google_trends.py
    youtube.py
  aggregate.py     # relevance gate, query grouping, velocity ranking, dedupe
  ideas.py         # template idea synthesis (casing-aware, kind-aware)
  llm.py           # optional LLM hook/title rewrite (Anthropic or OpenAI)
  report.py        # Markdown + JSON digests
  pipeline.py      # end-to-end run()
  cli.py           # python -m trend_engine
trend_api.py       # FastAPI server: /api/brief, /api/niches, serves the PWA
mobile/index.html  # the PWA (no build step — vanilla HTML/CSS/JS)
tests/test_trend_engine.py
```
