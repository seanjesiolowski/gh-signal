import requests
import time
from app.db import SessionLocal
from app.crud import create_event

GITHUB_EVENTS_URL = "https://api.github.com/events"

def fetch_and_store():
    db = SessionLocal()

    response = requests.get(GITHUB_EVENTS_URL)
    events = response.json()

    for event in events:
        try:
            create_event(db, event)
        except Exception as e:
            print(f"Error: {e}")
            db.rollback()

    db.close()

if __name__ == "__main__":
    while True:
        print("Fetching events...")
        fetch_and_store()
        time.sleep(60)  # poll every minute
