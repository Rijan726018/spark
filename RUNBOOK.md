# Spark runbook — production operations

App: `sparkbrief` on Fly.io · https://sparkbrief.fly.dev · volume `spark_data` mounted at `/data`

## Token recovery (customer lost their Pro token)

Normal path (works once `RESEND_API_KEY` is set): the customer taps
**"Already Pro? Restore your access"** in the app and enters their email —
`/api/token/recover` re-sends the token. Nothing for you to do.

Manual path (email provider down or not yet configured):

```powershell
# 1. Read the token straight off the production volume:
& "$env:USERPROFILE\.fly\bin\flyctl.exe" ssh console -a sparkbrief -C `
  "python3 -c \"import sqlite3; r = sqlite3.connect('/data/spark_users.db').execute('SELECT email, token, plan, status FROM users WHERE email = ?', ('CUSTOMER@EMAIL.COM',)).fetchone(); print(r)\""

# 2. Email the token to the customer BY HAND from your own inbox.
#    Subject: Your Spark Pro access token
#    Body: paste the token + "Open https://sparkbrief.fly.dev, tap Pro,
#    paste the token under 'Or paste your access token', hit Activate."
```

## Missed webhook (paid but not Pro / canceled but still Pro)

Webhooks can be replayed from the Stripe dashboard: Developers → Webhooks →
the endpoint → pick the event → **Resend**. If Stripe and the DB still
disagree, fix the row directly (same ssh pattern as above):

```python
# upgrade:   UPDATE users SET plan='pro',  status='active'   WHERE email=?
# downgrade: UPDATE users SET plan='free', status='canceled' WHERE email=?
```
(run with .execute(...) followed by .commit() on the connection)

## Health / logs / deploy

```powershell
$fly = "$env:USERPROFILE\.fly\bin\flyctl.exe"
& $fly status -a sparkbrief          # machine state
& $fly logs   -a sparkbrief          # live logs — token emails log as
                                     # "Token email sent to ..." / "... failed"
& $fly secrets list -a sparkbrief    # which secrets are set (names only)
cd C:\Users\rijan\spark; & $fly deploy --depot=false --yes   # deploy
```

`--depot=false` is required on the desktop — the default Depot builder fails
TLS verification through this network. Deploys restart the machine (~15s).

Setting/rotating secrets also restarts the app:

```powershell
& $fly secrets set -a sparkbrief NAME=VALUE ...
```

## Data safety

Everything that must survive a redeploy lives on the volume: user store at
`/data/spark_users.db`, brief cache at `/data/brief_cache/`. The image is
disposable; the volume is not. Never `fly volumes destroy spark_data`.
Snapshot before risky changes: `& $fly volumes snapshots create <volume-id>`.
