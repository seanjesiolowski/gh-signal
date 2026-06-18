from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Event(Base):
    __tablename__ = "events"

    id = Column(String(255), primary_key=True, index=True)
    type = Column(String(255), index=True)
    actor = Column(String(255), index=True)
    repo = Column(String(255), index=True)
    created_at = Column(DateTime, index=True)

class Repo(Base):
    __tablename__ = "repos"

    name = Column(String(255), primary_key=True, index=True)
    language = Column(String(255), index=True)
    topics = Column(JSON)
    fetched_at = Column(DateTime)
