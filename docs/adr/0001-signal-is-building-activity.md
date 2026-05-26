# Signal is building activity, not popularity

gh-signal exists to surface what people are *building* on public GitHub, not what's getting attention.
We ingest only the events that represent code or collaboration (push, PR, issue, review, release,
commit-comment, branch/tag creation) and drop popularity events (watch, fork, sponsor, member, public).

Rejected alternative: store all event types and filter at query time. Cleaner from a flexibility
standpoint, but the database schema would no longer match the domain, and ~30–50% of inserts
would be data we never query. If we ever want a popularity endpoint, restore the dropped types
in the ingestion filter.
