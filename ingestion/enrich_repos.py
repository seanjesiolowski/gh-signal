import os
import time
import requests
from app.db import SessionLocal
from app.crud import repos_needing_enrichment, upsert_repo

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
REQUEST_TIMEOUT = (5, 30)  # (connect, read) seconds

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
                else:
                    print(f"Skipping {name}: HTTP {r.status_code}")
            except Exception as e:
                print(f"Error enriching {name}: {e}")
                db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    while True:
        print("Enriching repos...")
        enrich_batch()
        time.sleep(60)
