# Phase 4A–B engineering QA — 2026-11-20

## What was checked

- Backend unit/API suite: 21 passed, one optional real-Mongo test skipped in the unit run. New checks cover baseline eligibility and missing data, recent-versus-prior comparison, session interval lifecycle, midnight splitting in Asia/Kolkata, within-session provisional signal change, recurring higher-signal hours, subject grouping, and account isolation.
- Isolated local MongoDB seed check: ran the presentation seed twice in a temporary database. Each fictional account had exactly three refreshed sample sessions and 48 labeled synthetic visual windows after each run; each produced an eligible sample baseline. Sample session IDs changed on rerun. `test@gmail.com` had no seeded sessions. The temporary database was dropped afterward.
- Browser smoke: a temporary MongoDB database and synthetic Chrome camera exercised sign-in, recorded Analytics empty state at 375/768/1440 CSS pixels, camera warnings for face absence plus QA-injected head/phone categories, model-load failure, paused timer, false-alarm clip consent/deletion, and API errors. No horizontal overflow or unexpected browser console error remained. The QA-only category injection is enabled only for the browser test Vite process; it does not prove detector accuracy.
- Frontend unit tests: `npm test` passed 3/3.
- Production build: `npm run build` passed with Analytics tracker loaded as a separate chunk.
- Real MongoDB integration: `python backend/scripts/run_real_mongo_check.py` passed 1/1 against an isolated temporary database.
- `git diff --check` passed (Windows line-ending conversion notices only).

## Evidence boundaries

The data in presentation accounts are explicitly labeled synthetic examples. Current real-user visual history may be too sparse for a baseline because prompt warnings can pause a session before a 10-second window is stored. Baseline and higher-signal thresholds are provisional engineering eligibility rules, not scientific validation. Physical-camera face/head/phone accuracy, false-alert rate, participant variation, CPU/battery impact, and the meaning of any attention metric remain for the later real-testing phase. Validated visual attention and estimated focused time remain unavailable.
