# Running GH-Signal Locally

The fastest path is Docker Compose. Native setup instructions follow if you'd rather run Python on the host.

## Option A: Docker Compose (recommended)

### Prerequisites

- Docker Desktop (or Docker Engine + Compose v2)

### 1. Start everything

From the project root:

```bash
docker compose up --build
```

This brings up these services:

| Service     | URL                          | Notes                                              |
|-------------|------------------------------|----------------------------------------------------|
| `postgres`  | `localhost:5433`             | Data persisted in the `postgres_data` named volume |
| `migrate`   | —                            | One-shot: runs `alembic upgrade head`, then exits  |
| `api`       | <http://localhost:8000>      | FastAPI, with `--reload` enabled in dev            |
| `ingestor`  | —                            | Polls GitHub Events every 60s                      |
| `enricher`  | —                            | Calls GitHub repo API to fill in language/topics   |
| `dashboard` | <http://localhost:8501>      | Streamlit, auto-reloads on save                    |

Schema is managed by Alembic ([migrations/](migrations/)). The `migrate` service runs before `api`, `ingestor`, `enricher`, and `dashboard` start, and they only launch after it exits successfully.

The `enricher` service needs a GitHub personal access token in [.env](.env) as `GITHUB_TOKEN=...` — without it, it falls back to unauthenticated requests (60/hour) and will mostly hit rate limits.

### 2. Hit the endpoints

- Health check: <http://127.0.0.1:8000/>
- Top repos: <http://127.0.0.1:8000/top-repos>
- Top repos with custom limit: <http://127.0.0.1:8000/top-repos?limit=25>
- Interactive docs: <http://127.0.0.1:8000/docs>
- Streamlit dashboard: <http://localhost:8501>

The `/top-repos` endpoint and the dashboard return empty until the ingestor has written at least one batch.

### Common commands

```bash
docker compose logs -f ingestor       # follow a single service's logs
docker compose restart api            # restart one service
docker compose down                   # stop everything (data persists)
docker compose down -v                # stop and wipe the database volume
```

`docker-compose.override.yml` is loaded automatically and mounts `./app`, `./ingestion`, and `./dashboard.py` into the containers, so edits on the host trigger reloads inside.

---

## Option B: Native Python

### Prerequisites

- Python 3.10+
- PostgreSQL running locally (the default `.env` expects it on port **5433**)
- `pip` available on your PATH

### 1. Set up the database

Create a database named `github_events` on the PostgreSQL instance referenced by `DATABASE_URL` in [.env](.env).

Using `psql`:

```bash
psql -h localhost -p 5433 -U postgres -c "CREATE DATABASE github_events;"
```

### 2. Install dependencies

From the project root:

```bash
python -m venv .venv
source .venv/Scripts/activate   # Git Bash on Windows
# or: .venv\Scripts\activate     # PowerShell / cmd
pip install -r requirements.txt
```

### 3. Verify environment

Confirm [.env](.env) contains a working connection string:

```
DATABASE_URL=postgresql://<user>:<password>@localhost:5433/github_events
```

Both the API and the ingestor load this via `python-dotenv` in [app/db.py:6](app/db.py#L6).

For the enricher, also set:

```
GITHUB_TOKEN=ghp_your_personal_access_token
```

### 4. Apply database migrations

Schema is managed by Alembic. Before starting any of the services, bring the database up to the latest revision:

```bash
alembic upgrade head
```

This creates the `events` and `repos` tables (or any newer migrations you've added).

### 5. Start the ingestion service

```bash
python -m ingestion.fetch_events
```

Leave it running in its own terminal. You should see `Fetching events...` every minute.

> Run from the project root so that `from app.db import SessionLocal` in [ingestion/fetch_events.py:3](ingestion/fetch_events.py#L3) resolves correctly.

### 6. Start the API server

In a second terminal (with the venv activated):

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 7. Start the enricher (optional but recommended)

In another terminal:

```bash
python -m ingestion.enrich_repos
```

Pulls repo metadata (language, topics) for repos that have appeared in the events stream. Requires `GITHUB_TOKEN` in `.env`.

### 8. (Optional) Start the Streamlit dashboard

In a third terminal (with the venv activated):

```bash
streamlit run dashboard.py
```

Streamlit opens <http://localhost:8501> with charts for events-per-minute, event-type breakdown, top repos/actors, and an hour-by-day activity heatmap. Data is cached for 30 seconds — use the **Refresh** button to clear the cache and re-query Postgres.

---

## Troubleshooting

- **`connection refused` / `password authentication failed`** (native) — check Postgres is listening on 5433 and that `DATABASE_URL` credentials match your local install.
- **`ModuleNotFoundError: app`** when running the ingestor — make sure you're invoking `python -m ingestion.fetch_events` from the repo root, not `python ingestion/fetch_events.py`.
- **No rows appearing** — GitHub's public events endpoint is unauthenticated and rate-limited to 60 requests/hour per IP. Wait a minute between runs.
- **Port 5433 already in use** (Docker) — you already have a Postgres on the host. Either stop it, or change the host-side mapping in `docker-compose.yml` (`"5434:5432"`).
- **`migrate` service exits 1 with `relation "events" already exists`** — the database volume predates Alembic. Tell Alembic the existing schema matches the baseline revision, then re-run:
  ```bash
  docker compose run --rm migrate alembic stamp 0001
  docker compose up -d
  ```
  Use `alembic stamp head` instead if `repos` *also* already exists from the pre-Alembic `create_all` call.
- **Enricher logs `HTTP 401`** — `GITHUB_TOKEN` missing or invalid. Confirm it's set in `.env` and that `docker compose` is loading `.env` from the project root.
- **Enricher logs `HTTP 404` on some repos** — expected. The repo was deleted or made private after the event was recorded. The enricher skips and moves on.

## Adding a schema change

1. Edit [app/models.py](app/models.py).
2. Generate a migration: `docker compose run --rm migrate alembic revision -m "describe change" --autogenerate`
3. Review the generated file in [migrations/versions/](migrations/versions/).
4. `docker compose up -d` — the `migrate` service applies it before anything else starts.
