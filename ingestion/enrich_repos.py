import os
import requests
from app.db import SessionLocal
from app.crud import repos_needing_enrichment, upsert_repo

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
REQUEST_TIMEOUT = (5, 30)  # (connect, read) seconds


def _is_rate_limited(response) -> bool:
    # GitHub signals an exhausted budget with 403/429 and X-RateLimit-Remaining: 0.
    return (
        response.status_code in (403, 429)
        and response.headers.get("X-RateLimit-Remaining") == "0"
    )


def enrich_batch():
    db = SessionLocal()
    try:
        names = repos_needing_enrichment(db, limit=20)
        for name in names:
            try:
                r = requests.get(
                    f"https://api.github.com/repos/{name}",
                    headers=HEADERS,
                    timeout=REQUEST_TIMEOUT,
                )
                if r.status_code == 200:
                    upsert_repo(db, name, r.json())
                elif _is_rate_limited(r):
                    reset = r.headers.get("X-RateLimit-Reset", "?")
                    print(f"Rate limited; stopping batch (resets at {reset})")
                    break
                else:
                    print(f"Skipping {name}: HTTP {r.status_code}")
            except Exception as e:
                print(f"Error enriching {name}: {e}")
                db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Enriching repos...")
    enrich_batch()
