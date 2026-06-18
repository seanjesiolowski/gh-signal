from datetime import datetime, timedelta, timezone

import pytest

from app.crud import (
    create_event,
    get_top_repos,
    prune_old_events,
    repos_needing_enrichment,
    upsert_repo,
)
from app.models import Event, Repo


@pytest.mark.parametrize(
    "payload",
    [
        {"id": "x"},  # missing type/actor/repo/created_at
        {"id": "x", "type": "PushEvent", "actor": "alice", "repo": {"name": "org/r"}, "created_at": "t"},  # actor not a dict
        {"id": "x", "type": "PushEvent", "actor": {"login": "a"}, "repo": "org/r", "created_at": "t"},  # repo not a dict
        {"id": "x", "type": "PushEvent", "actor": {}, "repo": {"name": "org/r"}, "created_at": "t"},  # actor.login missing
    ],
)
def test_create_event_raises_valueerror_on_malformed(db_session, payload):
    with pytest.raises(ValueError):
        create_event(db_session, payload)

    assert db_session.query(Event).count() == 0


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


def test_prune_old_events_removes_rows_past_cutoff(db_session, make_event):
    now = datetime.now(timezone.utc)
    create_event(db_session, make_event(id="old", created_at=now - timedelta(days=8)))
    create_event(db_session, make_event(id="fresh", created_at=now - timedelta(days=1)))

    deleted = prune_old_events(db_session, days=7)

    remaining = [r.id for r in db_session.query(Event).all()]
    assert deleted == 1
    assert remaining == ["fresh"]


def test_prune_old_events_keeps_rows_exactly_at_cutoff(db_session, make_event):
    now = datetime.now(timezone.utc)
    create_event(db_session, make_event(id="edge", created_at=now - timedelta(days=7) + timedelta(seconds=1)))

    deleted = prune_old_events(db_session, days=7)

    assert deleted == 0
    assert db_session.query(Event).count() == 1


def test_prune_old_events_no_op_when_table_empty(db_session):
    assert prune_old_events(db_session, days=7) == 0


def test_repos_needing_enrichment_includes_stale_with_recent_events(db_session, make_event):
    # Per ADR-0003: a repo enriched longer ago than the retention horizon,
    # but with recent activity, should be re-enriched.
    now = datetime.now(timezone.utc)
    create_event(db_session, make_event(id="recent", repo="org/stale", created_at=now))
    upsert_repo(db_session, "org/stale", {"language": "Python", "topics": []})
    db_session.query(Repo).filter_by(name="org/stale").update({"fetched_at": now - timedelta(days=10)})
    db_session.commit()

    assert "org/stale" in repos_needing_enrichment(db_session)


def test_repos_needing_enrichment_excludes_recently_enriched(db_session, make_event):
    # Enriched within the retention horizon — no refresh needed.
    create_event(db_session, make_event(id="1", repo="org/fresh"))
    upsert_repo(db_session, "org/fresh", {"language": "Python", "topics": []})

    assert repos_needing_enrichment(db_session) == []


def test_repos_needing_enrichment_excludes_dormant_repos(db_session):
    # Per ADR-0003: dormant repos (no recent events) stay cached indefinitely.
    # With retention pruning, "no recent events" means no events at all.
    upsert_repo(db_session, "org/dormant", {"language": "Python", "topics": []})

    assert repos_needing_enrichment(db_session) == []
