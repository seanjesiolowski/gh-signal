import os
import requests
from app.db import SessionLocal
from app.crud import create_event

GITHUB_EVENTS_URL = "https://api.github.com/events"
REQUEST_TIMEOUT = (5, 30)  # (connect, read) seconds
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

def fetch_and_store():
    db = SessionLocal()
    try:
        response = requests.get(GITHUB_EVENTS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        events = response.json()

        for event in events:
            try:
                create_event(db, event)
            except Exception as e:
                print(f"Error: {e}")
                db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Fetching events...")
    try:
        fetch_and_store()
    except requests.RequestException as e:
        print(f"Fetch failed: {e}")
