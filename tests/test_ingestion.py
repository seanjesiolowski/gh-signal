from unittest.mock import MagicMock

from app.models import Event
from ingestion import fetch_events as fe


def test_fetch_and_store_writes_events(db_session, db_sessionmaker, make_event, monkeypatch):
    monkeypatch.setattr(fe, "SessionLocal", db_sessionmaker)

    payload = [make_event(id="1", repo="org/a"), make_event(id="2", repo="org/b")]
    fake_response = MagicMock()
    fake_response.json.return_value = payload
    monkeypatch.setattr(fe.requests, "get", lambda *a, **kw: fake_response)

    fe.fetch_and_store()

    rows = db_session.query(Event).order_by(Event.id).all()
    assert [(r.id, r.repo) for r in rows] == [("1", "org/a"), ("2", "org/b")]


def test_fetch_and_store_continues_after_bad_event(db_session, db_sessionmaker, make_event, monkeypatch):
    monkeypatch.setattr(fe, "SessionLocal", db_sessionmaker)

    payload = [
        {"id": "bad"},  # missing fields → KeyError inside create_event
        make_event(id="2", repo="org/b"),
    ]
    fake_response = MagicMock()
    fake_response.json.return_value = payload
    monkeypatch.setattr(fe.requests, "get", lambda *a, **kw: fake_response)

    fe.fetch_and_store()

    rows = db_session.query(Event).all()
    assert [r.id for r in rows] == ["2"]


def test_fetch_and_store_calls_github_events_url(db_session, db_sessionmaker, monkeypatch):
    monkeypatch.setattr(fe, "SessionLocal", db_sessionmaker)

    fake_response = MagicMock()
    fake_response.json.return_value = []
    mock_get = MagicMock(return_value=fake_response)
    monkeypatch.setattr(fe.requests, "get", mock_get)

    fe.fetch_and_store()

    mock_get.assert_called_once_with(fe.GITHUB_EVENTS_URL, headers=fe.HEADERS, timeout=fe.REQUEST_TIMEOUT)
