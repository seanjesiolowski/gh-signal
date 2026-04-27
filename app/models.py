from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, index=True)
    type = Column(String, index=True)
    actor = Column(String, index=True)
    repo = Column(String, index=True)
    created_at = Column(DateTime)

class Repo(Base):
    __tablename__ = "repos"

    name = Column(String, primary_key=True, index=True)
    language = Column(String, index=True)
    topics = Column(JSON)
    fetched_at = Column(DateTime)
