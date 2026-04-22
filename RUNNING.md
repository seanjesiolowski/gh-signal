# Running GH-Signal Locally

## Prerequisites

- Python 3.10+
- PostgreSQL running locally (the default `.env` expects it on port **5433**)
- `pip` available on your PATH

## 1. Set up the database

Create a database named `github_events` on the PostgreSQL instance referenced by `DATABASE_URL` in [.env](.env).

Using `psql`:

```bash
psql -h localhost -p 5433 -U postgres -c "CREATE DATABASE github_events;"
```

The `events` table is created automatically at app startup by [app/main.py:7](app/main.py#L7).

## 2. Install dependencies

From the project root:

```bash
python -m venv .venv
source .venv/Scripts/activate   # Git Bash on Windows
# or: .venv\Scripts\activate     # PowerShell / cmd
pip install -r requirements.txt
```

## 3. Verify environment

Confirm [.env](.env) contains a working connection string:

```
DATABASE_URL=postgresql://<user>:<password>@localhost:5433/github_events
```

Both the API and the ingestor load this via `python-dotenv` in [app/db.py:6](app/db.py#L6).

## 4. Start the ingestion service

This polls the GitHub Events API every 60 seconds and writes rows into the `events` table.

```bash
python -m ingestion.fetch_events
```

Leave it running in its own terminal. You should see `Fetching events...` every minute.

> Run from the project root so that `from app.db import SessionLocal` in [ingestion/fetch_events.py:3](ingestion/fetch_events.py#L3) resolves correctly.

## 5. Start the API server

In a second terminal (with the venv activated):

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 6. Hit the endpoints

- Health check: <http://127.0.0.1:8000/>
- Top repos: <http://127.0.0.1:8000/top-repos>
- Top repos with custom limit: <http://127.0.0.1:8000/top-repos?limit=25>
- Interactive docs: <http://127.0.0.1:8000/docs>

The `/top-repos` endpoint returns empty until the ingestor has run at least once and written events.

## Troubleshooting

- **`connection refused` / `password authentication failed`** — check Postgres is listening on 5433 and that `DATABASE_URL` credentials match your local install.
- **`ModuleNotFoundError: app`** when running the ingestor — make sure you're invoking `python -m ingestion.fetch_events` from the repo root, not `python ingestion/fetch_events.py`.
- **No rows appearing** — GitHub's public events endpoint is unauthenticated and rate-limited to 60 requests/hour per IP. Wait a minute between runs.
