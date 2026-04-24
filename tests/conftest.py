import os
from datetime import datetime, timezone

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import db as app_db
from app.models import Base


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)
    eng.dispose()


@pytest.fixture
def db_sessionmaker(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session(db_sessionmaker):
    session = db_sessionmaker()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(engine, db_sessionmaker):
    app_db.engine = engine
    app_db.SessionLocal = db_sessionmaker

    from app.main import app, get_db

    def override_get_db():
        session = db_sessionmaker()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def make_event():
    def _make(
        id="1",
        type="PushEvent",
        actor="alice",
        repo="org/repo",
        created_at=datetime(2026, 4, 23, tzinfo=timezone.utc),
    ):
        return {
            "id": id,
            "type": type,
            "actor": {"login": actor},
            "repo": {"name": repo},
            "created_at": created_at,
        }

    return _make
