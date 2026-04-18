from sqlalchemy.orm import Session
from .models import Event

def create_event(db: Session, event_data: dict): # pyright: ignore[reportMissingTypeArgument, reportUnknownParameterType]
    event = Event(
        id=event_data["id"],
        type=event_data["type"],
        actor=event_data["actor"]["login"],
        repo=event_data["repo"]["name"],
        created_at=event_data["created_at"]
    )
    db.merge(event)  # avoids duplicates (important)
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
