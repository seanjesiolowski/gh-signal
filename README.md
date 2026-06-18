# GH Signal

A real-time data pipeline that ingests public GitHub events, processes them, and exposes analytics via an API.

*Signals recent language activity observed across public Github repos*

## Overview

This project builds a lightweight backend/data engineering system using the GitHub Events API. It demonstrates:

- Analytics queries over event streams
- API ingestion with rate limiting
- Idempotent data processing
- Relational data modeling
- REST API for insights

## Architecture

```
GitHub Events API ──► Ingestion Service ──┐
                                          ├──► PostgreSQL ──► FastAPI ──► Analytics Endpoints
GitHub Repos API  ──► Enrichment Service ─┘                       │
                                                                  └──► Streamlit Dashboard
```

## Tech Stack

- Backend: FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- Migrations: Alembic
- Ingestion + enrichment: Python + Requests
- Dashboard: Streamlit

## Running it

- **[docs/operations.md](docs/operations.md)** — run locally (Docker or native) and deploy to Railway.
- **[CONTEXT.md](CONTEXT.md)** — domain language and the signal this project measures.
- **[docs/adr/](docs/adr/)** — architecture decision records.

## Features

### Data Ingestion
- Polls GitHub Events API every minute
- Handles duplicate events using upsert logic
- Extracts key fields: repo, actor, event type, timestamp

### Repo Enrichment
- Background worker fetches repo metadata (language, topics) for repos that appear in the events stream
- Authenticated against GitHub with a personal access token (5,000 req/hr)
- Skips deleted/private repos and rate-limit responses gracefully

### Storage
- Normalized `events` schema with indexed fields for fast queries
- Separate `repos` table for enrichment data, joined on repo name
- Schema versioned via Alembic migrations

### API Endpoints

#### `GET /top-repos`
Returns most active repositories by event count. Accepts `limit` (default 10, max 100).

#### `GET /languages/trending`
Returns the most active programming languages over a rolling time window, ranked by event count. Accepts `window` (hours, default 24, max 720) and `limit` (default 10, max 100). Requires the enricher to have run.

#### `GET /topics/trending`
Returns the most active GitHub topics over a rolling time window, ranked by event count. Topics are unnested from each repo's topic list so a single repo can contribute to multiple topic counts. Accepts `window` and `limit` with the same bounds as `/languages/trending`. Requires the enricher to have run.

#### `GET /`
Health check endpoint.

## Example Responses

**`GET /top-repos`**
```json
[
  {"repo": "torvalds/linux", "count": 42},
  {"repo": "microsoft/vscode", "count": 35}
]
```

**`GET /languages/trending?window=24&limit=3`**
```json
[
  {"language": "Python", "count": 198},
  {"language": "TypeScript", "count": 154},
  {"language": "Go", "count": 87}
]
```

**`GET /topics/trending?window=24&limit=3`**
```json
[
  {"topic": "machine-learning", "count": 73},
  {"topic": "api", "count": 61},
  {"topic": "cli", "count": 44}
]
```
