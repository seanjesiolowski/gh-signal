# Trending = current window vs prior-baseline ratio

The /languages/trending and /topics/trending endpoints rank by *trending up* — a building-activity
rate materially higher than the recent baseline — not raw volume.

Formula: rank by current_count / scaled_baseline_count, where current_count is events in the
request's window and scaled_baseline_count is events in the rest of the retention horizon,
normalized to window length. A minimum-volume floor on current_count suppresses noise from items
with tiny denominators (one event vs zero baseline = infinity).

Rejected alternatives:
- Top by volume (the prior behavior, a defect-by-naming): Python is always #1 because it's popular,
  not because anything changed. Not what "trending" means.
- Absolute delta (current - prior): high-volume items dominate. A small repo spiking 10× loses to
  torvalds/linux gaining 50 events. Loses the "spike" sense entirely.
- Log ratio: smoother but doesn't change the ranking shape meaningfully at this scale; adds math
  without paying for it.

Consequence: the request window is meaningful only when a baseline exists. With 7-day retention,
windows above ~84h have no comparable baseline. The endpoint should clamp or reject such requests.
