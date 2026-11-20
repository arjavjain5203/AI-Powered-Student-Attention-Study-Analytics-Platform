# Phase 04 — Intelligence, personalization, GenAI, and gamification

## Objective and status

**A and B engineering implemented provisionally; C–F upcoming.** The baseline and pattern tracker use owned Phase 2 history and provisional Phase 3 camera windows. Physical-camera validation remains open. No output is called validated attention, mental focus, or estimated focused time.

## Scope, features, and order

1. Calculate a provisional personal visual-signal baseline from eligible 30-day windows; show insufficient-data states with counts.
2. Calibrate the Phase 2 focus planner against recorded history and study outcomes; retain reasons, trend, sample count, and provisional heuristic status.
3. Adapt FlowFocus's rule-based recommendation structure to shorter sessions, manageable targets, breaks, and practice. Exclude quiz-course actions unless that product area is explicitly added.
4. Add one GenAI Study Coach provider behind a service boundary. Send structured, minimal analytics; validate response shape, cite input metrics in explanations, and use a deterministic fallback on provider failure. No raw webcam frames.
5. Define XP, levels, badges, streaks, daily challenges, and records with server-side anti-gaming rules. Reward verified meaningful progress rather than elapsed timer alone.
6. Consider prediction only after a dataset, target, baseline model, and evaluation plan exist.

## Files, dependencies, APIs, database

Expected modules: baseline, planner calibration, recommendation rules, coach adapter, reward rules, and tests. Add a provider SDK only when a provider is selected. Extend owned analytics storage for baseline and reward events with rule version and timestamps. APIs should return reasons, data eligibility, and provenance for each recommendation or reward. The React Coach, Goals, and Achievements screens consume these APIs after the backend rules pass tests.

### Implemented A–B contract

`backend/app/services/patterns.py` calculates an equal-window 30-day mean of `visual_signal_index` from completed camera sessions. Eligible windows use the current face algorithm, `quality=usable`, at least 10 valid samples, and at least 80% coverage. The baseline needs 30 windows across three completed sessions on three local dates. Before that, the API returns `insufficient_history` and counts. A seven-day recent versus preceding-history comparison needs at least 10 recent and 20 prior windows; its delta is descriptive, not statistical confidence. `visual_attention_score` and `estimated_focused_seconds` remain `null`.

New sessions record completed `active_intervals` on pause, warning, consent expiry, or end. `active_since` represents the current open interval. The pattern service splits active time by minute in the student's IANA time zone, including midnight and daylight-saving changes. Older real sessions without intervals contribute to duration and subject totals but not precise time-of-day or weekday study time; no historical intervals are guessed.

Authenticated `GET /api/analytics/patterns` returns the baseline, hourly and weekday active-study totals, completed-session duration buckets and median, subject totals and eligible medians, later-versus-earlier provisional signal change, eligible recurring higher-signal six-hour periods, and up to three deterministic insights with evidence counts. Within-session change needs six eligible windows spanning 10 active minutes in each of at least three sessions. A higher-signal period needs 20 eligible windows across three days and a mean five points above the provisional baseline. Subject medians need three sessions on two days. Insights are withheld if the 1000-session or 10000-window query cap is reached.

`src/PatternTracker.jsx` displays the owned results with Recharts and clear missing-history labels. Three fictional presentation accounts receive idempotent labeled sample intervals and windows; `test@gmail.com` history is untouched. No provider SDK, ML training package, or duplicate pattern collection was added.

## Tests and acceptance

For implemented A–B, tests cover interval lifecycle, midnight splitting, sparse and low-quality windows, comparisons, within-session changes, subject eligibility, API ownership, idempotent sample seeding, and responsive synthetic-camera browser flows. Later phases must test conflicting recommendations, provider failures, and duplicate rewards. Acceptance requires grounded explanations and no unsupported psychological conclusions. Physical-camera signal validation remains pending before promoting any attention or focused-time metric.

## Risks and checklist

Historical bias, noisy visual signals, cost, prompt leakage, and reward gaming are key risks.

- [x] Provisional visual-signal baseline eligibility and calculation.
- [x] Study pattern tracker with interval, duration, subject, and provisional signal summaries.
- [ ] Physical-camera calibration and validated attention baseline.
- [ ] Study-specific recommendation rules.
- [ ] Structured-data AI Coach with fallback.
- [ ] Server-side gamification with anti-gaming tests.
- [ ] Prediction evaluation if sufficient data exists.

