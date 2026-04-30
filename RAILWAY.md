# Deploying GH-Signal to Railway

This guide deploys gh-signal to Railway's Hobby plan ($5/mo flat, $5 of metered usage included). The shape: **one always-on API service**, **one Postgres plugin**, **two cron services** for ingestion and enrichment, and the **dashboard runs locally** against the Railway database when you want to look at it.

## Why this shape

The naive port of `docker-compose.yml` would create five always-on services — that comfortably exceeds the included $5 of usage on Hobby. Two changes keep it inside the budget:

1. **Cron, not loops.** `fetch_events.py` and `enrich_repos.py` are one-shot scripts. Railway's cron schedule triggers a fresh run, the script does one cycle, exits. You only pay for actual execution time, not idle baseline.
2. **No dashboard service.** Streamlit is the heaviest container. Run it locally against Railway's public Postgres URL whenever you want a chart.

## Architecture on Railway

```
┌─────────────────────────────────────────────────┐
│ Railway project                                 │
│                                                 │
│  ┌───────────┐    ┌──────────┐    ┌──────────┐  │
│  │ api       │    │ ingestor │    │ enricher │  │
│  │ always-on │    │ cron 1m  │    │ cron 5m  │  │
│  └─────┬─────┘    └─────┬────┘    └────┬─────┘  │
│        │                │              │        │
│        └────────────────┼──────────────┘        │
│                         ▼                       │
│                 ┌───────────────┐               │
│                 │ Postgres      │ ◄────────────────── local Streamlit
│                 │ (plugin)      │     (public TCP proxy URL)
│                 └───────────────┘               │
└─────────────────────────────────────────────────┘
```

## Step-by-step

### 1. Provision

1. Create a new Railway project.
2. **+ New → Database → PostgreSQL**. Wait for it to come up. This exposes a `DATABASE_URL` variable.
3. **+ New → GitHub Repo → gh-signal**. This is the `api` service. Railway should detect the `Procfile`. Pick the `api` process. The Procfile entry runs `alembic upgrade head` first, so migrations apply on every deploy.
4. Add another service from the same repo for `ingestor`. Same for `enricher`. (Railway lets you create multiple services pointing at the same source.)

### 2. Wire up environment variables

For **every** service, link `DATABASE_URL` from the Postgres plugin:

- In the service's **Variables** tab → **+ New Variable** → **Add Reference** → `Postgres.DATABASE_URL`.

For `enricher` (and ideally `ingestor` too — see "Why both" below) add a **GitHub personal access token** as `GITHUB_TOKEN`. A classic token with `public_repo` scope is sufficient.

### 3. Configure each service

#### `api`
- **Start command**: leave blank — Procfile handles it.
- **Networking**: enable a public domain. Railway assigns `$PORT`.
- **Health check path**: `/`

#### `ingestor`
- **Start command**: `python -m ingestion.fetch_events`
- **Cron schedule**: `* * * * *` (every minute)
- **Networking**: none.
- The service should be in **cron mode** — the container runs on schedule, not continuously.

#### `enricher`
- **Start command**: `python -m ingestion.enrich_repos`
- **Cron schedule**: `*/5 * * * *` (every 5 minutes — repo metadata changes slowly)
- **Networking**: none.

### 4. Why `GITHUB_TOKEN` on the ingestor too

Unauthenticated requests to `https://api.github.com/events` are capped at **60/hour per IP**. Railway's egress IP is shared across customers, so the global pool is usually exhausted. With a token you get **5,000/hour**, which is plenty for a 1-minute cron.

### 5. Verify the deploy

After the API service finishes building:
- Hit `https://<your-api>.up.railway.app/` — should return `{"message": "GitHub Events API is running"}`.
- After a few minutes (let cron fire a couple of times): `https://<your-api>.up.railway.app/top-repos` should show data.
- After ~10 minutes (enricher needs to catch up): `/languages/trending` and `/topics/trending` start returning rows.

## Running the dashboard locally against Railway's database

The dashboard reads from the same Postgres, so you don't need to deploy it to see the data.

1. In the Railway Postgres plugin → **Connect** tab → copy the **Public Network** connection string (a `postgresql://...@<host>.proxy.rlwy.net:<port>/railway` URL — distinct from the internal `DATABASE_URL`).
2. Locally:
   ```bash
   DATABASE_URL="<public-postgres-url>" streamlit run dashboard.py
   ```
3. Open <http://localhost:8501>.

The dashboard's `@st.cache_data(ttl=30)` decorators mean each page render only hits the DB if cached results are older than 30 seconds, so the read load on the production DB stays trivial.

## Cost expectations

Rough monthly figures on the Hobby plan:

| Service    | Mode       | Approx RAM | Notes                                  |
|------------|------------|------------|----------------------------------------|
| `api`      | always-on  | ~120 MB    | FastAPI + SQLAlchemy idle              |
| `ingestor` | cron 1m    | ~80 MB×s   | ~5–10s of execution per minute         |
| `enricher` | cron 5m    | ~80 MB×s   | ~10–15s per run                        |
| Postgres   | always-on  | ~150 MB    | Managed                                |

Expect total spend in the $3–5/month range, comfortably inside the $5 of included usage.

If you start running over budget, the easiest knob is moving the ingestor to `*/2 * * * *` (every 2 minutes) — `/events` only delivers ~300 events per call regardless, so polling more often mostly buys freshness, not coverage.

## What's intentionally not here

- **No retry/backoff.** If the GitHub API rate-limits or 5xx's, the cron run logs the error and exits. The next scheduled run picks up.
- **No queue or orchestrator.** The README's "(Planned) Redis / Kafka / Airflow" line stays planned. For a project at this scale, Railway cron + Postgres is enough.
- **No HTTPS/auth on the API.** Railway terminates TLS for you, but the endpoints are public. If this matters, add a token check in `app/main.py` or front it with Cloudflare Access.

## Local development still works

`docker-compose.yml` wraps the now-one-shot scripts in a shell `while true; do ...; sleep 60; done` loop, so `docker compose up --build` continues to behave identically to before. The Procfile/cron split is Railway-specific.
