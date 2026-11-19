# Development roadmap

## Product and current state

The platform is a privacy-first study companion. It records owned study sessions and browser-local derived visual signals. Timed sessions now require an explicit camera start; no video is uploaded by default. It cannot measure a student's mental state. Phase 1 and the local Phase 2 foundation pass automated browser and database checks. Phase 3 is ACTIVE: camera-gated timing, provisional event pause, explicit false-alarm feedback, and owned APIs are implemented; physical-camera and labeled-signal validation remain open.

## Phase sequence and dependency

| Phase | Status | Depends on | Major deliverable and exit gate |
| --- | --- | --- | --- |
| [1 UI](PHASE_01_UI.md) | Completed; headless browser QA passed | None | Navigable demo, responsive UI, honest mock labels, successful build |
| [2 Backend](PHASE_02_BACKEND.md) | Local implementation and browser QA passed | Phase 1 contracts | Authenticated owned sessions, records, analytics, API integration, test Mongo verification |
| [3 CV](PHASE_03_COMPUTER_VISION.md) | ACTIVE, device evaluation pending | Phase 2 records and consent model | Opt-in local processing and derived visual signals; validation before attention claims |
| [4 Intelligence](PHASE_04_AI_PERSONALIZATION.md) | Upcoming | Sufficient valid Phase 2/3 data | Calibrated baseline, explainable plans, coach, gamification |
| [5 Integration](PHASE_05_INTEGRATION_DEPLOYMENT.md) | Upcoming | Phases 2–4 | End-to-end, security/privacy checks, deployment |

## Current progress and next tasks

Phase 2 implemented FastAPI, MongoDB, JWT accounts, owned sessions, digital records, analytics, and backend-connected frontend views. The app opens at sign-in; the separate Demo and Recorded workspaces were removed. Three fictional local accounts have labeled sample history, while the existing test account keeps its recorded history. The updated headless browser test covers camera-gated timing, provisional alert pause, explicitly shared false-alarm clips, API errors, and responsive layouts. The camera uses a consent lease and a provisional visual-signal index. Validated visual attention and focused-time estimates remain unavailable. Next: run the [physical-device and labeled-observation protocol](PHASE_03_VALIDATION.md) and review whether the visual heuristics should be kept, adjusted, or disabled.

## Cross-phase acceptance and testing

Each phase needs documented API/data contracts, validation, authorization where applicable, tests for business rules and failure paths, build/start commands, and evidence for real integrations. Mock output is never evidence that a camera, AI model, or reward engine works. See each phase document for its gate.

## Known risks

- FlowFocus thresholds are unvalidated heuristics; copy only with attribution and adaptation.
- Client-reported digital activity and distractions can be forged; do not treat them as verified attention.
- The current frontend is a monolithic React component with local fixtures; its data-access seam needs care to preserve the presentation flow.
- The local MongoDB test passed, but staging/deployed MongoDB has not been verified.
- The Phase 1 build warns about a large JavaScript bundle; optimize only after the live flow is stable.

