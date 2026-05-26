# Enrichment refresh: activity-triggered, bounded by retention horizon

Repos are re-enriched when they have an event newer than `fetched_at + retention_horizon`.
Dormant repos (no recent events) stay cached indefinitely.

Why this shape:
- The freshness bound is coupled to the retention horizon. Metadata staleness shouldn't outlive
  the events it describes. If retention changes, this policy follows.
- Activity-triggered (not pure TTL) means we only spend GitHub API quota on repos that actually
  appear in current signals. The /events firehose is the natural filter — quiet repos cost nothing.
- The authenticated GitHub rate limit is 5000 req/hr. Always-refresh on every enrichment pass
  would burn through this on a busy day. Bounded refresh keeps the budget headroom intact.

Rejected alternatives:
- Never refresh (the prior behavior): wrong as soon as any repo's language or topics change.
  A Python-to-Rust rewrite would forever count as Python.
- Pure TTL (refresh every N days regardless of activity): same outcome at this scale because
  active repos almost always reappear in events, but doesn't scale if retention shrinks or the
  firehose widens.
- Always refresh on every pass: blows the rate-limit budget on popular afternoons.
