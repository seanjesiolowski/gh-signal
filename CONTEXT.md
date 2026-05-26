# gh-signal

gh-signal surfaces a *building activity* signal — the volume of code and collaboration on public GitHub repos, over a rolling time window — sliced by repo, language, and topic.

## Language

**Building activity**:
The signal gh-signal exists to surface. The volume of code-and-collaboration events on public repos — pushes, pull requests, issues, releases, code review. Distinguishes "what's being built" from "what's being noticed."
_Avoid_: Trending (overloaded), activity (too broad)

**Popularity**:
Consumption signals on a repo — stars, watches, forks-as-bookmarks. Explicitly NOT what gh-signal measures.
_Avoid_: Trending, hype, engagement

**Event**:
A single record from GitHub's public events firehose representing a building-activity action by an actor on a repo. Identified by GitHub's event ID; immutable once issued.
_Avoid_: Activity, action

**Actor**:
The GitHub user who performed an event. Stored as the login string (`alice`), not the numeric ID.
_Avoid_: User, author

**Repo**:
A public GitHub repository, identified by its full name (`owner/name`). The primary unit of aggregation for building activity.
_Avoid_: Project, package; use "repository" only in formal prose

**Window**:
The rolling time range over which building activity is summed. Default 24 hours. Bounded by the retention horizon.
_Avoid_: Period, range, lookback

**Trending up**:
A building-activity rate in the current window that is materially higher than the recent baseline (the rest of the retention horizon, scaled to the window length). What `/languages/trending` and `/topics/trending` rank by.
_Avoid_: Trending (use the full phrase to distinguish from common usage), hot, popular

**Top by volume**:
Raw event count in a window, with no comparison to a baseline. Useful internally but NOT what the trending endpoints return. Reserved as a possible separate concept if a future endpoint exposes it.
_Avoid_: Trending, leaderboard

**Retention horizon**:
The maximum age of stored events. Events older than this are pruned on each ingestion run. Currently 7 days.
_Avoid_: TTL (ambiguous), cutoff

**Enrichment freshness**:
A Repo's metadata (`language`, `topics`) is considered fresh if `fetched_at` is no older than the retention horizon relative to the repo's most recent event. Stale enrichment is re-fetched on the next enrichment pass; dormant repos (no recent events) stay cached indefinitely.
_Avoid_: Cache TTL, expiry

## Example dialogue

> **Dev:** "Top repos endpoint is showing torvalds/linux at the top all week."
> **Domain expert:** "Expected — Linux gets continuous push activity. The signal is *building activity*, not novelty."
> **Dev:** "Should we drop watch events? They're inflating counts on whatever hits Hacker News."
> **Domain expert:** "Yes — watches are *popularity*. We track who's building, not who's looking."

## Flagged ambiguities

- **Fork events**: A fork can mean "I'm about to build on this" (building) or "saving for later" (popularity). Currently excluded from building activity. Revisit if the signal feels under-counted.
