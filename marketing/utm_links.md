# UTM-tagged links — one per channel, never reuse across channels

Every public link carries UTM tags from day one so launch day (Aug 4) has
real attribution data. Funnel check: which channel produced signups, which
produced *payers*.

| Channel | Link |
|---|---|
| X bio | https://sparkbrief.fly.dev/?utm_source=x&utm_medium=bio&utm_campaign=founding |
| X posts/threads | https://sparkbrief.fly.dev/?utm_source=x&utm_medium=post&utm_campaign=founding |
| Reddit bio | https://sparkbrief.fly.dev/?utm_source=reddit&utm_medium=bio&utm_campaign=founding |
| Reddit posts (Aug 3+ only) | https://sparkbrief.fly.dev/?utm_source=reddit&utm_medium=post&utm_campaign=launch |
| DMs (all platforms) | https://sparkbrief.fly.dev/?utm_source=dm&utm_medium=outreach&utm_campaign=founding |
| Discord (self-promo channels only) | https://sparkbrief.fly.dev/?utm_source=discord&utm_medium=post&utm_campaign=founding |
| TikTok/Shorts bio | https://sparkbrief.fly.dev/?utm_source=shorts&utm_medium=bio&utm_campaign=founding |
| Indie Hackers | https://sparkbrief.fly.dev/?utm_source=ih&utm_medium=post&utm_campaign=launch |
| Directories (Aug 4) | https://sparkbrief.fly.dev/?utm_source=directory&utm_medium=listing&utm_campaign=launch |

Waitlist (Tally) — create the form, then use the same discipline:
`https://tally.so/r/FORM_ID?utm_source=<channel>` — paste final links here: `TODO`

Reading the data: server logs record the full request path; check
`fly logs -a sparkbrief` or the admin stats route (`SPARK_ADMIN_TOKEN` +
`GET /api/admin/stats`) once set.
