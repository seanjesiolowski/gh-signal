from unittest.mock import MagicMock

import pytest
import requests

from app.crud import create_event
from app.models import Event, Repo
from ingestion import enrich_repos as er
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


def test_fetch_and_store_raises_on_http_error(db_session, db_sessionmaker, monkeypatch):
    monkeypatch.setattr(fe, "SessionLocal", db_sessionmaker)

    fake_response = MagicMock()
    fake_response.raise_for_status.side_effect = requests.HTTPError("403 rate limited")
    monkeypatch.setattr(fe.requests, "get", lambda *a, **kw: fake_response)

    with pytest.raises(requests.HTTPError):
        fe.fetch_and_store()

    # No events should have been written, and the session should be closed cleanly.
    assert db_session.query(Event).count() == 0


def test_enrich_batch_writes_repo_on_success(db_session, db_sessionmaker, make_event, monkeypatch):
    monkeypatch.setattr(er, "SessionLocal", db_sessionmaker)
    create_event(db_session, make_event(id="1", repo="org/needs-enrich"))

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"language": "Python", "topics": ["api", "cli"]}
    monkeypatch.setattr(er.requests, "get", lambda *a, **kw: fake_response)

    er.enrich_batch()

    repo = db_session.query(Repo).filter_by(name="org/needs-enrich").one()
    assert repo.language == "Python"
    assert repo.topics == ["api", "cli"]


def test_enrich_batch_skips_non_200_responses(db_session, db_sessionmaker, make_event, monkeypatch):
    monkeypatch.setattr(er, "SessionLocal", db_sessionmaker)
    create_event(db_session, make_event(id="1", repo="org/deleted"))

    fake_response = MagicMock()
    fake_response.status_code = 404
    monkeypatch.setattr(er.requests, "get", lambda *a, **kw: fake_response)

    er.enrich_batch()

    assert db_session.query(Repo).count() == 0


def test_enrich_batch_calls_repos_api_with_headers(db_session, db_sessionmaker, make_event, monkeypatch):
    monkeypatch.setattr(er, "SessionLocal", db_sessionmaker)
    create_event(db_session, make_event(id="1", repo="org/foo"))

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"language": "Go", "topics": []}
    mock_get = MagicMock(return_value=fake_response)
    monkeypatch.setattr(er.requests, "get", mock_get)

    er.enrich_batch()

    mock_get.assert_called_once_with(
        "https://api.github.com/repos/org/foo",
        headers=er.HEADERS,
        timeout=er.REQUEST_TIMEOUT,
    )
