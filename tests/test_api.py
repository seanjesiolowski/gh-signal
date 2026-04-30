from datetime import datetime, timezone

import pytest

from app.crud import create_event, upsert_repo


def test_root(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "GitHub Events API is running"}


def test_top_repos_empty(client):
    response = client.get("/top-repos")

    assert response.status_code == 200
    assert response.json() == []


def test_top_repos_returns_aggregated_counts(client, db_session, make_event):
    for i in range(2):
        create_event(db_session, make_event(id=f"a{i}", repo="org/popular"))
    create_event(db_session, make_event(id="b", repo="org/quiet"))

    response = client.get("/top-repos")

    assert response.status_code == 200
    assert response.json() == [
        {"repo": "org/popular", "count": 2},
        {"repo": "org/quiet", "count": 1},
    ]


def test_top_repos_respects_limit(client, db_session, make_event):
    for name in ["a", "b", "c"]:
        create_event(db_session, make_event(id=name, repo=f"org/{name}"))

    response = client.get("/top-repos?limit=2")

    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.skip(reason="requires PostgreSQL — json_array_elements_text not available in SQLite test env")
def test_topics_trending_aggregates_by_topic(client, db_session, make_event):
    upsert_repo(db_session, "org/web", {"language": "Python", "topics": ["web", "api"]})
    upsert_repo(db_session, "org/ml", {"language": "Python", "topics": ["ml", "web"]})

    create_event(db_session, make_event(id="e1", repo="org/web", created_at=datetime.now(timezone.utc)))
    create_event(db_session, make_event(id="e2", repo="org/web", created_at=datetime.now(timezone.utc)))
    create_event(db_session, make_event(id="e3", repo="org/ml", created_at=datetime.now(timezone.utc)))

    response = client.get("/topics/trending?window=24")

    assert response.status_code == 200
    assert response.json() == [
        {"topic": "web", "count": 3},
        {"topic": "api", "count": 2},
        {"topic": "ml", "count": 1},
    ]


def test_languages_trending_joins_repos_and_filters_window(client, db_session, make_event):
    upsert_repo(db_session, "org/python", {"language": "Python", "topics": []})
    upsert_repo(db_session, "org/js", {"language": "JavaScript", "topics": []})

    create_event(db_session, make_event(id="e1", repo="org/python", created_at=datetime.now(timezone.utc)))
    create_event(db_session, make_event(id="e2", repo="org/python", created_at=datetime.now(timezone.utc)))
    create_event(db_session, make_event(id="e3", repo="org/js", created_at=datetime.now(timezone.utc)))
    create_event(db_session, make_event(id="e4", repo="org/python", created_at=datetime(2026, 4, 22, tzinfo=timezone.utc)))

    response = client.get("/languages/trending?window=24")

    assert response.status_code == 200
    assert response.json() == [
        {"language": "Python", "count": 2},
        {"language": "JavaScript", "count": 1},
    ]
