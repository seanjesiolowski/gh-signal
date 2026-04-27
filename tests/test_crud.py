from app.crud import create_event, get_top_repos, repos_needing_enrichment, upsert_repo
from app.models import Event


def test_create_event_inserts_row(db_session, make_event):
    create_event(db_session, make_event(id="1", repo="org/repo"))

    rows = db_session.query(Event).all()
    assert len(rows) == 1
    assert rows[0].id == "1"
    assert rows[0].repo == "org/repo"
    assert rows[0].actor == "alice"
    assert rows[0].type == "PushEvent"


def test_create_event_dedupes_on_id(db_session, make_event):
    create_event(db_session, make_event(id="1", repo="org/a"))
    create_event(db_session, make_event(id="1", repo="org/b"))

    rows = db_session.query(Event).all()
    assert len(rows) == 1
    assert rows[0].repo == "org/b"


def test_get_top_repos_orders_by_count_desc(db_session, make_event):
    for i in range(3):
        create_event(db_session, make_event(id=f"a{i}", repo="org/popular"))
    create_event(db_session, make_event(id="b1", repo="org/quiet"))

    top = get_top_repos(db_session)

    assert top[0] == ("org/popular", 3)
    assert top[1] == ("org/quiet", 1)


def test_get_top_repos_respects_limit(db_session, make_event):
    for name in ["a", "b", "c"]:
        create_event(db_session, make_event(id=name, repo=f"org/{name}"))

    assert len(get_top_repos(db_session, limit=2)) == 2


def test_get_top_repos_empty(db_session):
    assert get_top_repos(db_session) == []


def test_repos_needing_enrichment_excludes_already_enriched(db_session, make_event):
    create_event(db_session, make_event(id="1", repo="org/done"))
    create_event(db_session, make_event(id="2", repo="org/pending"))
    upsert_repo(db_session, "org/done", {"language": "Python", "topics": []})

    assert repos_needing_enrichment(db_session) == ["org/pending"]


def test_repos_needing_enrichment_deduplicates(db_session, make_event):
    create_event(db_session, make_event(id="1", repo="org/repo"))
    create_event(db_session, make_event(id="2", repo="org/repo"))

    assert repos_needing_enrichment(db_session) == ["org/repo"]


def test_repos_needing_enrichment_respects_limit(db_session, make_event):
    for i in range(5):
        create_event(db_session, make_event(id=str(i), repo=f"org/r{i}"))

    assert len(repos_needing_enrichment(db_session, limit=3)) == 3


def test_repos_needing_enrichment_empty_when_all_enriched(db_session, make_event):
    create_event(db_session, make_event(id="1", repo="org/done"))
    upsert_repo(db_session, "org/done", {"language": "Go", "topics": []})

    assert repos_needing_enrichment(db_session) == []
