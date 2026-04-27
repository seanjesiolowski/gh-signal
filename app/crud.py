from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Event, Repo


def create_event(db: Session, event_data: dict[str, Any]) -> None:
    event = Event(
        id=event_data["id"],
        type=event_data["type"],
        actor=event_data["actor"]["login"],
        repo=event_data["repo"]["name"],
        created_at=event_data["created_at"],
    )
    db.merge(event)
    db.commit()


def get_top_repos(db: Session, limit: int = 10):
    return (
        db.query(Event.repo, func.count(Event.id).label("count"))
        .group_by(Event.repo)
        .order_by(func.count(Event.id).desc())
        .limit(limit)
        .all()
    )


def repos_needing_enrichment(db: Session, limit: int = 20) -> list[str]:
    enriched = select(Repo.name)
    return [
        r[0] for r in
        db.query(Event.repo)
          .filter(Event.repo.notin_(enriched))
          .distinct()
          .limit(limit)
          .all()
    ]


def upsert_repo(db: Session, name: str, data: dict[str, Any]) -> None:
    repo = Repo(
        name=name,
        language=data.get("language"),
        topics=data.get("topics", []),
        fetched_at=datetime.now(timezone.utc),
    )
    db.merge(repo)
    db.commit()
