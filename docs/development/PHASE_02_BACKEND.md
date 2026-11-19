# Phase 02 — Backend and database foundation

## Objective and status

Local foundation and browser acceptance checks pass. Production security/deployment review remains Phase 5. The local MongoDB integration test and isolated suite pass. Do not create validated visual scores, AI responses, or production XP from demo fixtures.

## Scope and features

FastAPI under `backend/app`, MongoDB collections (`users`, `sessions`, `attention_records`, `distractions`), JWT, profile preferences, session state transitions, derived digital score, period analytics, and an explainable focus plan. The current implementation is in `backend/app/main.py` and pure services under `backend/app/services/`.

## Execution order

1. Finish API contracts and split the current foundation into routers, schemas, and repositories when the behavior is stable; keep one scoring implementation.
2. Run indexes and authentication against a real test MongoDB; verify duplicate email handling and connection errors.
3. Add source, consent, and quality metadata before accepting future visual signals. Until then `visual_attention_score` stays `null`.
4. Extend analytics with timezone-aware calendar boundaries, focused time when validated visual records exist, baseline eligibility, and distraction categories. Return `null` where unavailable.
5. Add a frontend data adapter and login/register flow. Dashboard, Study Session, Analytics, and Settings now open in the backend-connected workspace. The original Phase 1 sample pages for Coach, Goals, and Achievements remain labeled previews. Handle loading, empty, and error states.
6. Add integration tests for each endpoint, race conditions, ownership, expired tokens, invalid input, and a real MongoDB instance.

## Dependencies and API

Install `backend/requirements-dev.txt` for tests and `backend/requirements.txt` for runtime. Set `MONGO_URI`, `MONGO_DB`, `JWT_SECRET` (32+ characters), and `CORS_ORIGINS`; never commit secrets. Current endpoints: `/api/health`, `/api/auth/register`, `/api/auth/login`, `/api/profile`, `/api/sessions`, `/api/sessions/{id}`, `/api/sessions/{id}/status/{pause|resume|end}`, `/api/sessions/{id}/digital-records`, `/api/sessions/{id}/attention-records`, `/api/sessions/{id}/distractions`, `/api/analytics?period=daily|weekly|monthly`, and `/api/focus/plan`. Except health and register/login, use Bearer JWT. IDs in dependent requests must identify a session owned by the token subject.

## Database and integration points

Users have a unique email index. Sessions and records index `user_id` and time/session keys. Durations are seconds, times are UTC, and returned times are ISO 8601. A live client must not submit `src/data.js` fixture values to these endpoints. No raw video field or upload endpoint exists.

## Testing, acceptance, and risks

Current results: the isolated backend suite, opt-in real MongoDB test, frontend tests, and Vite build pass. `npm run test:browser` uses headless Chrome, a temporary MongoDB database, and isolated local servers to check authentication, recorded sessions, 375/768/1440-pixel layouts, 409/503/401 UI errors, and reload behavior. `npm audit --omit=dev` found no runtime dependency advisories; the full audit previously reported development-chain advisories. Risks: client-reported signals can be forged; heuristic weights are not validated; session time depends on server clock; JWTs are held only in memory and expire after 12 hours. See [data and trust contract](PHASE_02_DATA_CONTRACT.md).

## Checklist

- [x] FastAPI, configuration, indexes, JWT, profile, sessions and owned record endpoints.
- [x] Digital engagement separated from visual attention; focus-plan fallback and reasons.
- [x] Isolated service and API tests.
- [x] Real MongoDB test and connection/error handling.
- [x] Frontend auth and recorded-first Dashboard, Study Session, Analytics, and Settings.
- [x] Calendar/timezone aggregation and explicit unavailable focused-time contract.
- [x] Expanded failure-path, ownership, and token tests; local configuration review.
- [x] Local headless Chrome interaction, responsive, and error-state QA.

Depends on Phase 1 UI contracts. Phase 3 can begin only after consent and derived-signal contracts are documented.

