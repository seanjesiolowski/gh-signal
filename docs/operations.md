# Operations

How to run gh-signal locally and deploy it to Railway. For what the endpoints
return, see the [README](../README.md); for domain terms, see [CONTEXT.md](../CONTEXT.md).

## Local development

### Option A: Docker Compose (recommended)

Prerequisite: Docker Desktop (or Docker Engine + Compose v2).

First copy `.env.example` to `.env` and set `POSTGRES_PASSWORD` (compose fails
fast if it's unset). Then, from the project root:

```bash
cp .env.example .env
# edit .env: set POSTGRES_PASSWORD (any non-empty value for local dev)
docker compose up --build
```

This brings up:

| Service     | URL                          | Notes                                              |
|-------------|------------------------------|----------------------------------------------------|
| `postgres`  | `localhost:5433`             | Data persisted in the `postgres_data` named volume |
| `migrate`   | —                            | One-shot: runs `alembic upgrade head`, then exits  |
| `api`       | <http://localhost:8000>      | FastAPI, with `--reload` enabled in dev            |
| `ingestor`  | —                            | Polls GitHub Events every 60s                      |
| `enricher`  | —                            | Calls GitHub repo API to fill in language/topics   |
| `dashboard` | <http://localhost:8501>      | Streamlit, auto-reloads on save                    |

Schema is managed by Alembic ([migrations/](../migrations/)). The `migrate`
service runs first; the others launch only after it exits successfully.

The `enricher` needs a GitHub personal access token in `.env` as `GITHUB_TOKEN=...`
— without it, it falls back to unauthenticated requests (60/hour) and mostly hits
rate limits.

`docker-compose.override.yml` is loaded automatically and mounts `./app`,
`./ingestion`, and `./dashboard.py` into the containers, so host edits trigger
reloads inside.

Common commands:

```bash
docker compose logs -f ingestor       # follow a single service's logs
docker compose restart api            # restart one service
docker compose down                   # stop everything (data persists)
docker compose down -v                # stop and wipe the database volume
```

`/top-repos` returns data as soon as the ingestor has written one batch.
`/languages/trending` and `/topics/trending` return data only after the enricher
has populated the `repos` table.

### Option B: Native Python

Prerequisites: Python 3.10+, PostgreSQL on port **5433** (the default `.env`),
`pip` on your PATH.

```bash
# 1. Create the database
psql -h localhost -p 5433 -U postgres -c "CREATE DATABASE github_events;"

# 2. Install dependencies
python -m venv .venv
source .venv/Scripts/activate    # Git Bash on Windows; PowerShell: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Apply migrations
alembic upgrade head

# 4. Run the services (each in its own terminal, venv activated)
python -m ingestion.fetch_events                              # ingestor
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000    # API
python -m ingestion.enrich_repos                              # enricher (needs GITHUB_TOKEN)
streamlit run dashboard.py                                    # dashboard (optional)
```

`.env` must contain a working connection string, loaded via `python-dotenv` in
[app/db.py](../app/db.py):

```
DATABASE_URL=postgresql://<user>:<password>@localhost:5433/github_events
GITHUB_TOKEN=ghp_your_personal_access_token   # for the enricher
```

> Run ingestion from the repo root (`python -m ingestion.fetch_events`, not
> `python ingestion/fetch_events.py`) so `from app.db import SessionLocal` resolves.

### Troubleshooting

- **`connection refused` / `password authentication failed`** (native) — check
  Postgres is listening on 5433 and `DATABASE_URL` credentials match.
- **`ModuleNotFoundError: app`** — invoke `python -m ingestion.fetch_events` from
  the repo root.
- **No rows appearing** — GitHub's public events endpoint is rate-limited to
  60 req/hour per IP when unauthenticated. Set `GITHUB_TOKEN` and wait a minute.
- **Port 5433 already in use** (Docker) — a host Postgres is running. Stop it or
  change the host-side mapping in `docker-compose.yml` (`"5434:5432"`).
- **`migrate` exits 1 with `relation "events" already exists`** — the volume
  predates Alembic. Stamp the baseline, then re-run:
  ```bash
  docker compose run --rm migrate alembic stamp 0001   # or `head` if repos also exists
  docker compose up -d
  ```
- **Enricher logs `HTTP 401`** — `GITHUB_TOKEN` missing or invalid.
- **Enricher logs `HTTP 404` on some repos** — expected; the repo was deleted or
  made private after the event was recorded. The enricher skips and moves on.

### Adding a schema change

1. Edit [app/models.py](../app/models.py).
2. `docker compose run --rm migrate alembic revision -m "describe change" --autogenerate`
3. Review the generated file in [migrations/versions/](../migrations/versions/).
4. `docker compose up -d` — the `migrate` service applies it before anything starts.

## Deploying to Railway

This deploys to Railway's Hobby plan ($5/mo flat, $5 of metered usage included).
The shape: **one always-on API service**, **one Postgres plugin**, **two cron
services** for ingestion and enrichment, and the **dashboard runs locally**
against the Railway database.

### Why this shape

A naive port of `docker-compose.yml` would create five always-on services, which
exceeds the included usage. Two changes keep it in budget:

1. **Cron, not loops.** `fetch_events.py` and `enrich_repos.py` are one-shot
   scripts. Railway's cron triggers a run, the script does one cycle and exits.
   You pay only for execution time, not idle baseline.
2. **No dashboard service.** Streamlit is the heaviest container. Run it locally
   against Railway's public Postgres URL when you want a chart.

```
┌─────────────────────────────────────────────────┐
│ Railway project                                 │
│  ┌───────────┐    ┌──────────┐    ┌──────────┐  │
│  │ api       │    │ ingestor │    │ enricher │  │
│  │ always-on │    │ cron 1m  │    │ cron 5m  │  │
│  └─────┬─────┘    └─────┬────┘    └────┬─────┘  │
│        └────────────────┼──────────────┘        │
│                         ▼                       │
│                 ┌───────────────┐               │
│                 │ Postgres      │ ◄──────────────── local Streamlit
│                 │ (plugin)      │   (public TCP proxy URL)
│                 └───────────────┘               │
└─────────────────────────────────────────────────┘
```

### Step-by-step

1. **Provision.** New Railway project → **+ New → Database → PostgreSQL** (exposes
   `DATABASE_URL`). Then **+ New → GitHub Repo → gh-signal** for the `api` service
   (Railway detects the `Procfile`; its entry runs `alembic upgrade head` first).
   Add two more services from the same repo for `ingestor` and `enricher`.
2. **Variables.** For every service, link `Postgres.DATABASE_URL` (**Variables →
   Add Reference**). Add `GITHUB_TOKEN` (classic token, `public_repo` scope) to
   `enricher` and `ingestor`.
3. **Configure each service:**
   - `api` — start command blank (Procfile handles it); enable a public domain;
     health check path `/`.
   - `ingestor` — start `python -m ingestion.fetch_events`; cron `* * * * *`; no
     networking; cron mode (runs on schedule, not continuously).
   - `enricher` — start `python -m ingestion.enrich_repos`; cron `*/5 * * * *`;
     no networking.
4. **Verify.** Hit `https://<your-api>.up.railway.app/` (returns
   `{"message": "GitHub Events API is running"}`). After a few cron firings,
   `/top-repos` shows data; after ~10 minutes `/languages/trending` and
   `/topics/trending` start returning rows.

**Why `GITHUB_TOKEN` on the ingestor too:** unauthenticated `/events` is capped at
60/hour per IP, and Railway's egress IP is shared, so the pool is usually
exhausted. A token gives 5,000/hour.

### Dashboard against the Railway database

The dashboard reads from the same Postgres, so you don't deploy it:

1. Railway Postgres plugin → **Connect** → copy the **Public Network** string (a
   `postgresql://...@<host>.proxy.rlwy.net:<port>/railway` URL).
2. `DATABASE_URL="<public-postgres-url>" streamlit run dashboard.py`
3. Open <http://localhost:8501>.

`@st.cache_data(ttl=30)` means each render only hits the DB if cached results are
older than 30 seconds, so read load on production stays trivial.

### Cost expectations

| Service    | Mode       | Approx RAM | Notes                          |
|------------|------------|------------|--------------------------------|
| `api`      | always-on  | ~120 MB    | FastAPI + SQLAlchemy idle      |
| `ingestor` | cron 1m    | ~80 MB×s   | ~5–10s of execution per minute |
| `enricher` | cron 5m    | ~80 MB×s   | ~10–15s per run                |
| Postgres   | always-on  | ~150 MB    | Managed                        |

Expect $3–5/month, inside the included usage. If you run over, move the ingestor
to `*/2 * * * *` — `/events` only delivers ~300 events per call regardless, so
polling more often mostly buys freshness, not coverage.

### Intentionally not here

- **No retry/backoff.** A rate-limit or 5xx is logged; the next cron run picks up.
- **No queue or orchestrator.** Railway cron + Postgres is enough at this scale.
- **No HTTPS/auth on the API.** Railway terminates TLS, but endpoints are public.
  Add a token check in `app/main.py` or front it with Cloudflare Access if needed.

Local development still works: `docker-compose.yml` wraps the one-shot scripts in a
`while true; do ...; sleep 60; done` loop, so `docker compose up --build` behaves
as before. The Procfile/cron split is Railway-specific.
