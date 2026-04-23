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

This brings up four services:

| Service     | URL                          | Notes                                              |
|-------------|------------------------------|----------------------------------------------------|
| `postgres`  | `localhost:5433`             | Data persisted in the `postgres_data` named volume |
| `api`       | <http://localhost:8000>      | FastAPI, with `--reload` enabled in dev            |
| `ingestor`  | —                            | Polls GitHub Events every 60s                      |
| `dashboard` | <http://localhost:8501>      | Streamlit, auto-reloads on save                    |

The `events` table is created automatically at API startup by [app/main.py:7](app/main.py#L7).

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

### 4. Start the ingestion service

```bash
python -m ingestion.fetch_events
```

Leave it running in its own terminal. You should see `Fetching events...` every minute.

> Run from the project root so that `from app.db import SessionLocal` in [ingestion/fetch_events.py:3](ingestion/fetch_events.py#L3) resolves correctly.

### 5. Start the API server

In a second terminal (with the venv activated):

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 6. (Optional) Start the Streamlit dashboard

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
