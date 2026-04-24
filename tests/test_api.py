from app.crud import create_event


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
