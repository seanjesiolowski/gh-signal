# TODO

## Rotate GITHUB_TOKEN after Railway deploy

The token currently in `.env` and pasted into Railway's `ingestor` + `enricher` Variables was echoed in a Claude Code chat transcript on **2026-05-06**. Treat as semi-exposed.

**Steps once gh-signal is up and stable on Railway:**

1. Visit <https://github.com/settings/tokens> and **revoke** the token starting `ghp_RetJL...` (classic PAT, `public_repo` scope).
2. Generate a fresh classic PAT with the same `public_repo` scope.
3. Update local `.env` → `GITHUB_TOKEN=<new>`.
4. Update Railway service variables:
   - `ingestor` → Variables → `GITHUB_TOKEN` → paste new value
   - `enricher` → Variables → `GITHUB_TOKEN` → paste new value
5. Verify: trigger a manual run of each cron service or wait for the next scheduled fire. Confirm logs show no `HTTP 401`.

**Why bother:** scope is small (`public_repo` on a personal account), so worst case is "someone reads public GitHub at 5k req/hr as you" — not catastrophic, but free hygiene.
