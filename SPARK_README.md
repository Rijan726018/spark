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

## API surface

Free (cached data only, no founder spend):

- `POST/GET /api/brief` — today's brief (preset niches; custom niche/geo/profile are Pro)
- `GET /api/niches` — preset list
- `GET /api/history?niche=` — dates with a cached brief
- `GET /api/brief/archive?niche=&date=` — a past day's brief
- `GET /api/brief.md?niche=&date=` — Markdown export (paste into Notion/Obsidian)
- `POST /api/feedback` — 👍/👎 an idea (`{niche, topic, vote: 1|-1}`)

Pro (Bearer token from checkout):

- `POST /api/brief` with `refresh`, `geo` (2-letter country), and/or `profile`
  — personalized briefs are cached per user per day, so refreshes are cheap
- `POST /api/expand` — one idea → full shooting script (beats, b-roll,
  description, hashtags); LLM-written when a key is set, template otherwise
- `GET/POST/DELETE /api/saves` — server-side saved-ideas library
- `GET/PUT /api/prefs` — default niche/geo + creator profile; once saved,
  every brief is personalized automatically
- `GET/POST/DELETE /api/digest` — daily brief emailed each morning
  (`{niche, hour}`, server-time; needs an email provider configured)
- `POST /api/billing/portal` — Stripe self-serve portal (cancel, card, invoices)

Ops:

- `GET /healthz` — health check
- `GET /api/admin/stats` — counters (users, spend, cache); enabled by setting
  `SPARK_ADMIN_TOKEN`, sent back only to the matching `X-Admin-Token` header

Spend caps: `SPARK_DAILY_RUN_BUDGET` (engine runs/day, default 10),
`SPARK_DAILY_EXPAND_BUDGET` (script expansions/day, default 200),
`SPARK_RATE_LIMIT_PER_MIN` (per-IP, default 30).

## Niches

Presets live in `trend_engine/config.py` (`fitness`, `trading`, `tech`), each a
bundle of seed keywords (relevance gate) + YouTube queries (momentum probes).
Add a niche by adding one entry — everything else is generic. Unknown niche
names become a generic niche built from the words given.

## Tests

```bash
python3 -m pytest tests/test_trend_engine.py tests/test_trend_api.py \
    tests/test_spark_features.py tests/test_spark_billing.py \
    tests/test_spark_email.py            # no network needed
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
trend_api.py       # FastAPI server: briefs, history, expand, digest, billing; serves the PWA
spark_billing.py   # Stripe checkout/webhooks/portal + user store (sqlite, zero deps)
spark_store.py     # user data: saved ideas, prefs, digest subs, feedback (same sqlite file)
spark_expand.py    # idea -> full shooting script (LLM with template fallback)
spark_email.py     # token + daily-digest email (Resend or SMTP, fails soft)
mobile/index.html  # the PWA (no build step — vanilla HTML/CSS/JS)
tests/test_trend_engine.py
```
