# Spark — daily content brief for creators

Mobile-first **PWA** that tells creators what to make today: pulls Google Trends
realtime RSS + YouTube Data API signals, ranks momentum per niche, synthesizes
ready-to-shoot ideas (hook, titles, format, outline). $9/mo Pro via Stripe.
This is the current **launch product** (pivoted here from the Nexus terminal, July 2026).

## Run / deploy

```
uvicorn trend_api:app --port 8100        # local — open http://localhost:8100
fly deploy                               # prod: app "sparkbrief" on Fly.io (sparkbrief.fly.dev)
.venv\Scripts\python -m pytest tests/    # test suite
```

Deploy image installs `requirements-spark.txt` (lean); dev extras in `requirements-dev.txt`.
Prod state lives on the Fly volume `spark_data` at `/data`. See `RUNBOOK.md` for ops.

## Layout (what's actually Spark)

| Path | Purpose |
|---|---|
| `trend_api.py` | FastAPI app: PWA serving + run/expand/analyze/billing/token routes |
| `trend_engine/` | Signal pipeline: sources → relevance gate → velocity ranking → idea synthesis |
| `spark_billing.py` / `spark_store.py` / `spark_email.py` | Stripe checkout+webhook, sqlite user store, token email (Resend/SMTP) |
| `spark_analyze.py` / `spark_expand.py` / `spark_metrics.py` | Deep video analysis (Pro), idea expansion, usage metrics |
| `mobile/` | PWA shell: manifest, icons |
| `tests/` | Spark test suite (pytest) |
| `marketing/` | Founding-member offer, hit list, UTM links |
| `content_digests/`, `brief_cache/`, `spark_users.db` | Runtime output/state — gitignored |

Config via `.env` (see `.env.example`): `YOUTUBE_API_KEY` required; Stripe/Resend/
Supadata optional (dev mode simulates checkout). Daily spend caps via `SPARK_DAILY_*`.

## Heads-up: stale Nexus copies on disk

This repo was seeded from the Nexus terminal codebase. On 2026-07-30 those copies
(`engines/`, `server/`, `frontend/`, `algos/`, etc.) were **untracked from git and
gitignored** — the live originals are in `C:/Users/rijan/Claude`
(github.com/Rijan726018/Claude). The local folders here are dead weight, safe to
delete, and must never be re-added to this repo. Don't edit Nexus code here.

## Product judgment calls already made

- Honest-claims standard applies to marketing copy (no invented numbers).
- Research feed must stay genuinely fresh per day (see commits around outlier
  score: compare rates, not raw counts).
- Related repos: Nexus terminal `C:/Users/rijan/Claude` · ADK business
  `C:/Users/rijan/adk-industries` · Alpaca bot `C:/Users/rijan/alpaca-paper`.
