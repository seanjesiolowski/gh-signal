# Security fixes — 2026-04-29

Snapshot of the security review on this date and the fixes applied. Everything not in the "Fixed" section is still open.

## Fixed

### 1. Unbounded `limit` / `window` on API endpoints
[app/main.py](../app/main.py)

`/top-repos` and `/languages/trending` accepted arbitrary integer values for `limit` and `window`. A request like `/languages/trending?window=999999&limit=999999` would force a full-table group/scan — cheap DoS.

Switched both to `fastapi.Query` with bounds:
- `limit`: `ge=1, le=100`
- `window` (hours): `ge=1, le=24*30` (30-day max)

Out-of-range values now return HTTP 422 instead of running the query.

### 2. Missing `timeout=` on outbound HTTP
[ingestion/fetch_events.py](../ingestion/fetch_events.py), [ingestion/enrich_repos.py](../ingestion/enrich_repos.py)

Both ingestion workers called `requests.get(...)` with no timeout. If GitHub stalled, the workers would hang indefinitely with no recovery.

Added `REQUEST_TIMEOUT = (5, 30)` (connect, read) to both modules and passed it to every `requests.get` call. Updated test stubs in [tests/test_ingestion.py](../tests/test_ingestion.py) accordingly. All 17 tests pass.

## Still open (noted, not fixed)

Tracked here so they don't get lost:

- **Hardcoded DB password.** `password` is baked into [docker-compose.yml](../docker-compose.yml) and as the default in [app/db.py](../app/db.py). Move to `.env` with a strong default; ensure `.env` is in `.gitignore`.
- **Postgres port published to host.** `5433:5432` is fine for local dev; do not carry into any deployed compose file.
- **Container runs as root.** [Dockerfile](../Dockerfile) has no `USER` directive. Add a non-root user before deployment.
- **No `.dockerignore`** verified — confirm `.env`, `.git`, and `tests/` aren't being copied into the image.
- **Streamlit dashboard is unauthenticated** and binds `0.0.0.0:8501` ([docker-compose.yml](../docker-compose.yml)). Loopback-only on any non-laptop host.
- **No length caps on string columns.** [app/models.py](../app/models.py) uses bare `String` for `repo`, `actor`, etc. A malformed GitHub payload could insert oversized rows. Consider `String(255)`.
- **Defensive parsing in workers.** [app/crud.py](../app/crud.py) `create_event` indexes `event_data["id"]` etc. directly — a malformed payload crashes the worker (availability, not confidentiality).
- **No rate-limit handling for the GitHub API.** [ingestion/enrich_repos.py](../ingestion/enrich_repos.py) burns through the 5k/hr token budget silently on 403/429.
- **Dependency audit.** Run `pip-audit` against [requirements.txt](../requirements.txt) and pin versions.
