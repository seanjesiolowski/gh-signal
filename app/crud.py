from datetime import datetime
from sqlalchemy.orm import Session
from .models import Event, Repo

def create_event(db: Session, event_data: dict): # pyright: ignore[reportMissingTypeArgument, reportUnknownParameterType]
    event = Event(
        id=event_data["id"],  # "natural key" design // The upstream ID is already unique, stable, and opaque — it meets every requirement for a primary key.
        type=event_data["type"],
        actor=event_data["actor"]["login"],
        repo=event_data["repo"]["name"],
        created_at=event_data["created_at"]
    )
    db.merge(event)  # avoids duplicates (important) // GitHub is the source of truth for event identity, and the app trusts it.
    db.commit()

def get_top_repos(db: Session, limit: int = 10):
    from sqlalchemy import func
    return (
        db.query(Event.repo, func.count(Event.id).label("count"))
        .group_by(Event.repo)
        .order_by(func.count(Event.id).desc())
        .limit(limit)
        .all()
    )

def repos_needing_enrichment(db: Session, limit: int = 20):
    enriched = db.query(Repo.name).subquery()
    return [
        r[0] for r in
        db.query(Event.repo)
          .filter(Event.repo.notin_(enriched)) # pyright: ignore[reportArgumentType]
          .distinct()
          .limit(limit)
          .all()
    ]

def upsert_repo(db: Session, name: str, data: dict): # pyright: ignore[reportMissingTypeArgument, reportUnknownParameterType]
    repo = Repo(
        name=name,
        language=data.get("language"), # pyright: ignore[reportUnknownMemberType]
        topics=data.get("topics", []), # pyright: ignore[reportUnknownMemberType]
        fetched_at=datetime.utcnow(), # pyright: ignore[reportDeprecated]
    )
    db.merge(repo)
    db.commit()
