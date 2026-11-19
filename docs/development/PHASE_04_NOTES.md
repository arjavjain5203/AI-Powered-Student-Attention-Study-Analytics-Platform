# Phase 4 notes (owner: <Anvi>)

All Phase 4 code lives in `backend/phase4/`. Nothing under `backend/app/` is modified.
Run with: `uvicorn phase4.main:app --reload`

## 4C Personalized Focus Planner: implemented, provisional

- `signals.py`: converts stored records into FocusSignal (value, source, confidence, sample_count).
  Missing data is None, never 0. Digital and provisional visual signals stay separate.
- `baseline.py`: median + IQR over eligible sessions (>= 5 sessions, >= 10 min active,
  >= 50% record coverage). Otherwise status "insufficient_data" with no numbers.
- `focus_planner.py`: block length from where engagement usually drops below the personal
  floor (Q1 - 0.5*IQR); 15-50 min clamp; trend adjustment; break and long-break rules;
  `reasons[]` on every plan. Falls back to `app/services/planner.py` without a baseline.
- Endpoints: `GET /api/planner/personalized`, `GET /api/planner/break-check`.
- Tests: `phase4/tests/` (41 tests). Full suite: 50 passed, 1 skipped.

## Known limitations

- All thresholds are provisional and unvalidated; tested on synthetic histories only.
- The planner reads digital engagement. The frontend does not currently post digital records,
  so real users get the fallback plan until it does.
- Assumed digital record interval: 30 s (`DIGITAL_RECORD_INTERVAL_SECONDS` in signals.py).
- Elapsed time includes paused time.
- Not validated attention; no claims about mental state.