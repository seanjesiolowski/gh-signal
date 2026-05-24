from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Event, Repo


# CONSIDER USING DATACLASSES FOR THE FUNCTIONS TO IMPROVE TYPE SAFETY AND CLARITY
def prune_old_events(db: Session, days: int = 7) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    deleted = (
        db.query(Event)
        .filter(Event.created_at < cutoff)
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted


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


def get_trending_languages(db: Session, hours: int = 24, limit: int = 10):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return (
        db.query(Repo.language, func.count(Event.id).label("count"))
        .join(Repo, Repo.name == Event.repo)
        .filter(Event.created_at >= cutoff)
        .filter(Repo.language.isnot(None))
        .group_by(Repo.language)
        .order_by(func.count(Event.id).desc())
        .limit(limit)
        .all()
    )


def get_trending_topics(db: Session, hours: int = 24, limit: int = 10):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    # json_array_elements_text is PostgreSQL-specific
    topic = func.json_array_elements_text(Repo.topics).column_valued("topic")
    return (
        db.query(topic, func.count(Event.id).label("count"))
        .select_from(Event)
        .join(Repo, Repo.name == Event.repo)
        .filter(Event.created_at >= cutoff)
        .filter(Repo.topics.isnot(None))
        .group_by(topic)
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
