# Project TODO
# AI-Powered Student Attention & Study Analytics Platform

## Current Project Status

| Phase | Description | Status |
|---|---|---|
| Phase 1 | Complete UI Development | Completed; headless Chrome QA passed |
| Phase 2 | Backend and Data Layer | Local implementation and browser QA passed; deployment review remains Phase 5 |
| Phase 3 | Browser-local Computer Vision | ACTIVE — implementation and synthetic-camera QA passed; physical-device and labeled validation pending |
| Phase 4 | ML, Personalization, GenAI & Gamification | 4A–B provisional engineering implemented and tested; 4C–F upcoming |
| Phase 5 | Integration, Testing & Deployment | Upcoming |

---

## Phase 1 — Complete UI Development and Presentation

**Status: OWNER-COMPLETED; build and headless Chrome visual QA verified.**

See [Phase 1](docs/development/PHASE_01_UI.md).

- [x] Inspect the existing repository and identify the current frontend setup.
- [x] Complete the student-facing UI.
- [x] Implement the global app shell, navigation, responsive layout, and reusable components.
- [x] Implement Dashboard.
- [x] Implement Study Session screen.
- [x] Implement Analytics screen.
- [x] Implement AI Study Coach screen.
- [x] Implement Goals & Challenges screen.
- [x] Implement Achievements and Gamification screen.
- [x] Implement Profile and Settings.
- [x] Add realistic, consistent mock data for attention scores, focus time, distraction events, charts, AI insights, XP, levels, streaks, and badges.
- [x] Make primary navigation and key UI controls interactive using frontend state.
- [x] Implement empty states and camera-permission preview states.
- [x] Add desktop, tablet, and mobile responsive layouts.
- [x] Verify the production build succeeds with Vite.
- [x] Prepare a presentation/demo flow requiring no backend or webcam.
- [x] Clearly distinguish simulated data and simulated AI/CV features from real functionality.
- [x] Perform browser interaction testing across all screens in headless Chrome.
- [x] Inspect screenshots and verify no horizontal overflow at 375, 768, and 1440 pixels.
- [x] Check browser console errors and failed network requests; intentional API-error cases are asserted.
- [x] Verify keyboard navigation, visible focus, labeled forms, and basic accessibility in the browser smoke test.

**Phase 1 Exit Criteria:**

The complete UI must be navigable, visually consistent, responsive, and demonstrable without backend or webcam-processing services.

---

## Phase 2 — Backend and Data Layer

**Status: LOCAL IMPLEMENTATION AND BROWSER QA COMPLETED; production deployment review remains Phase 5.**

See:
- [Phase 2 Implementation Guide](docs/development/PHASE_02_BACKEND.md)
- [Phase 2 Data Contract](docs/development/PHASE_02_DATA_CONTRACT.md)
- [FlowFocus Integration](docs/FLOWFOCUS_INTEGRATION.md)

### Backend Foundation

- [x] Establish FastAPI application.
- [x] Configure backend dependencies and environment example.
- [x] Add health endpoint.
- [x] Integrate MongoDB client.
- [x] Create project collections and indexes.
- [x] Verify MongoDB using a local instance.

### Authentication

- [x] Implement student registration.
- [x] Implement login.
- [x] Implement JWT authentication.
- [x] Implement authorization for protected endpoints.
- [x] Implement profile APIs.
- [x] Test duplicate email handling and expired-token behavior.

### Study Session Management

- [x] Implement session creation.
- [x] Implement session listing.
- [x] Implement session detail retrieval.
- [x] Implement pause and resume.
- [x] Implement session completion.
- [x] Implement session ownership validation.
- [x] Test concurrent session transitions.

### Digital Activity and Distraction Records

- [x] Implement owned digital activity-record APIs.
- [x] Implement client-reported distraction-record APIs.
- [x] Validate incoming records.
- [x] Keep visual attention score unavailable until validated visual signals exist.

### Analytics and Focus Planning

- [x] Implement provisional digital engagement scoring.
- [x] Implement explainable focus-planning service adapted from FlowFocus.
- [x] Implement daily analytics.
- [x] Implement weekly analytics.
- [x] Implement monthly analytics.
- [x] Support the user's configured timezone.
- [x] Handle missing signals appropriately.
- [x] Define the future visual-signal and focused-time data boundaries.

### Frontend Integration

- [x] Add shared API client.
- [x] Open directly in the backend-connected workspace; remove the Demo/Recorded switch and separate Recorded workspace navigation item.
- [x] Connect Dashboard to recorded data.
- [x] Connect Study Session to recorded data.
- [x] Show a live server-backed session timer without refresh; exclude setup, paused, and ended intervals.
- [x] Gate new session timing on camera startup and pause on camera stop, lost permission, route exit, lease expiry, or provisional alert.
- [x] Connect Analytics to recorded data.
- [x] Connect Profile and Settings to recorded data.
- [x] Keep AI Coach, Goals, and Achievements visibly labeled as previews until real features are implemented.
- [x] Seed three isolated fictional presentation accounts and preserve the local test account's session history.

### Testing and Database Verification

- [x] Add API and service tests.
- [x] Verify initial tests with mongomock (7 passing).
- [x] Expand authorization and validation tests.
- [x] Expand expired-token and database-error tests.
- [x] Verify local MongoDB startup.
- [x] Verify database indexes.
- [x] Verify duplicate-email behavior.
- [x] Verify API flows against real MongoDB.
- [x] Verify concurrent session transitions against real MongoDB.
- [x] Add local environment configuration and deployment examples.

### Remaining QA

- [x] Browser-test recorded-data mode with an isolated local MongoDB database.
- [x] Verify frontend behavior for a simulated backend 503 and recovery.
- [x] Test expired and invalid JWT handling in the UI with a simulated 401.
- [x] Test API validation and database errors, including a second-session 409 and simulated 503.
- [x] Verify ended session state persists after page refresh and sign-in; camera remains off.
- [x] Verify desktop, tablet, and mobile layouts in recorded-data mode at 1440, 768, and 375 pixels.
- [ ] Review API authorization and environment configuration before production deployment.

**Phase 2 Exit Criteria:**

The backend must reliably support authentication, session management, validated records, and analytics. The frontend must correctly consume recorded data and handle API failures.

---

## Phase 3 — Browser-Local Computer Vision and Attention Signals

**Status: ACTIVE — camera-first screen and prompt provisional warnings pass synthetic-camera QA; physical face/head/phone validation and performance checks remain pending.**

See [Phase 3 Computer Vision Guide](docs/development/PHASE_03_COMPUTER_VISION.md).

### A. Webcam Integration

- [x] Add explicit webcam opt-in.
- [x] Add local webcam preview.
- [x] Put the study clock over the main camera preview and keep it live while the session is active.
- [x] Add camera start and stop controls.
- [x] Integrate webcam controls with active recorded study sessions.
- [x] Test camera permission granted with a synthetic Chrome camera.
- [x] Test camera permission denied with a browser API rejection.
- [x] Test a missing selected camera device in the browser.
- [x] Test synthetic camera disconnection during a session.
- [x] Add camera device selection and test unavailable-device handling.
- [ ] Test switching between two physical cameras.
- [x] Verify camera stops when a session ends.
- [x] Verify camera stops when a session is paused.
- [x] Verify camera stops on route changes and component unmount.
- [x] Test that page refresh stops capture and requires sign-in again.
- [ ] Repeat camera permission and lifecycle checks with a physical camera.

### B. Browser-Local MediaPipe Processing

- [x] Integrate browser-local MediaPipe face-presence detection.
- [x] Implement a coarse head-orientation proxy.
- [x] Process webcam frames locally.
- [x] Aggregate derived signals into 10-second windows.
- [x] Keep raw frames and facial landmarks out of API payloads.
- [x] Test MediaPipe model initialization and a blocked-model loading failure in headless Chrome.
- [x] Run the synthetic-camera browser suite in local Chrome and Edge.
- [ ] Test supported browsers with physical cameras, including mobile Safari/Chrome.
- [ ] Test low-light and poor-camera conditions.
- [x] Record a headless synthetic-camera task-duration and heap benchmark; show local inference milliseconds in the UI.
- [ ] Measure CPU usage and inference latency on physical devices.
- [ ] Evaluate performance on lower-end laptops and mobile devices.

### C. Visual Signal Processing

- [x] Add derived visual-signal aggregation.
- [x] Implement an explainable provisional visual-signal index.
- [x] Keep visual signals separate from digital engagement.
- [x] Keep the provisional index separate from validated visual attention.
- [ ] Evaluate geometry thresholds using consented, labeled data.
- [ ] Test different lighting conditions.
- [ ] Test eyewear-related variations.
- [ ] Test variations in skin tones and camera quality.
- [ ] Test different face positions and postures.
- [x] Review eye/gaze feasibility and document why calibrated gaze is excluded from the current score.
- [ ] Evaluate false-positive and false-negative rates.
- [x] Document signal limitations, sample coverage, and the validation protocol.
- [x] Add a derived-count CSV evaluator for future consented observation results.

### D. Privacy and Backend Integration

- [x] Implement consent-related functionality.
- [x] Add owned visual-record APIs.
- [x] Add 90-day expiry handling.
- [x] Add visual-record deletion APIs.
- [x] Add validation and corresponding tests.
- [x] Assert 10-second window uploads contain only five bounded count/version fields; prompt warning uploads contain only category and algorithm version.
- [x] Verify real MongoDB visual records contain no frame, image, video, or landmark fields.
- [x] Inspect synthetic-camera network requests: the face model and WASM load from the app origin; the phone model downloads from Google's model host for local inference.
- [x] Verify browser storage stays empty and app logs contain no camera payloads in the smoke test.
- [x] Verify consent and its 60-second lease are required before visual-record ingestion.
- [x] Verify another student cannot access visual records or events.
- [x] Verify deletion and 90-day TTL indexes against real MongoDB; elapsed 90-day expiry remains unobserved.
- [x] Add explicitly consented false-alarm clip upload, local admin review API, student deletion, and seven-day expiry.
- [x] Require a recent camera alert and owner authentication before accepting a false-alarm report.
- [ ] Review physical-camera clip preview, media compatibility, privacy notice, and admin access before deployment.
- [ ] Repeat network and storage inspection with a physical camera.

### E. Distraction Detection

- [x] Define **provisional camera-observed event** rules, explicitly separate from validated distractions.
- [x] Detect a missing face across two processed observations as a prompt provisional warning.
- [x] Detect a turned head across two processed observations as a prompt provisional warning.
- [x] Add a browser-local visible-phone detector prototype and warn after two qualifying observations.
- [ ] Evaluate looking-away events.
- [ ] Evaluate prolonged downward head orientation.
- [x] Atomically pause the owned camera session when a client-reported provisional warning is accepted.
- [x] Prevent duplicate warnings while the session is paused.
- [x] Pause the study timer on a provisional camera alert and show a false-alarm path; keep paused time excluded.
- [x] Keep YOLO excluded; use the existing MediaPipe runtime for the phone prototype.
- [ ] Validate real-camera phone detections and false warnings before treating the prototype as reliable.
- [ ] Resolve the EfficientDet model-weight redistribution terms before bundling it for offline/deployed use.

### F. Attention Engine Validation

- [x] Finalize separate provisional visual, digital, and validated-attention contracts.
- [x] Define missing-signal handling and keep validated scores `null`.
- [x] Expose sample coverage and usable/insufficient quality, without calling them calibrated confidence.
- [ ] Evaluate the provisional visual-signal index against labeled observations.
- [ ] Determine whether a validated estimated-attention score can be produced.
- [ ] Define focused-time calculation only after its underlying signal rules are validated.
- [x] Document the scoring formula, event thresholds, and limitations.
- [x] Ensure that unvalidated signals are not presented as scientifically established attention measurements.

**Important distinction:**

The current visual-signal index is provisional. It must not automatically be treated as a validated Attention Score or used to claim that the system knows whether a student is mentally concentrating.

**Phase 3 Exit Criteria:**

- Browser-local webcam processing works reliably.
- Raw webcam footage is not transmitted or persistently stored by default.
- Derived signals are validated and appropriately labeled.
- Camera permission and failure states work correctly.
- Performance is acceptable on supported devices.
- Attention-related metrics have documented limitations and validation evidence.

---

## Phase 4 — Personalization, ML, GenAI, and Gamification

**Status: A–B ENGINEERING IMPLEMENTED PROVISIONALLY; physical-signal validation and C–F remain upcoming.**

See [Phase 4 AI Personalization Guide](docs/development/PHASE_04_AI_PERSONALIZATION.md).

### A. Personal Attention Baseline

- [x] Define the provisional visual-signal baseline calculation methodology and source/version labels.
- [x] Require 30 eligible windows across three completed sessions and three local dates.
- [x] Calculate individual **provisional visual-signal** baselines from owned 30-day history.
- [x] Compare recent seven-day provisional signals against earlier non-overlapping history only when both groups qualify.
- [x] Report descriptive higher/lower/similar changes with actual sample counts.
- [x] Handle new users with explicit insufficient-history states.
- [x] Avoid numeric baseline comparisons when data is incomplete or truncated.
- [ ] Validate camera signals before calling any baseline a personal attention baseline.

### B. Study Pattern Detection

- [x] Track active study intervals across pauses, warnings, consent expiry, and session end.
- [x] Analyze local time-of-day study totals and provisional camera-signal periods.
- [x] Analyze active study time by local weekday, including sessions crossing midnight.
- [x] Describe later-versus-earlier provisional signal changes when at least three sessions qualify.
- [x] Analyze completed-session duration distributions and medians.
- [x] Identify recurring **higher provisional signal** windows with sufficient observations.
- [ ] Validate signals before calling those windows high-focus or attention-decline periods.
- [x] Analyze subject totals and medians only where sufficient history exists.
- [x] Generate deterministic, evidence-counted study-history insights.
- [x] Display responsive recorded pattern charts and honest empty states.
- [x] Seed labeled presentation-only sample patterns idempotently without changing test-account history.

### C. Personalized Focus Planner

- [ ] Adapt FlowFocus focus-planning logic to validated attention metrics.
- [ ] Recommend personalized focus durations.
- [ ] Recommend personalized break durations.
- [ ] Detect declining attention trends.
- [ ] Implement early-break recommendations.
- [ ] Implement long-break scheduling.
- [ ] Provide explanations for recommendations.
- [ ] Test recommendations with historical study data.

### D. Machine Learning and Prediction

- [ ] Define prediction objectives and target variables.
- [ ] Prepare reliable historical training data.
- [ ] Establish baseline model performance.
- [ ] Evaluate Scikit-learn models.
- [ ] Evaluate XGBoost if justified.
- [ ] Predict potential attention patterns.
- [ ] Evaluate model accuracy.
- [ ] Monitor prediction quality.
- [ ] Avoid making predictions when insufficient data exists.

### E. GenAI Study Coach

- [ ] Select one GenAI provider: Gemini or OpenAI.
- [ ] Implement structured analytics input.
- [ ] Generate daily study summaries.
- [ ] Generate weekly and monthly insights.
- [ ] Explain attention patterns.
- [ ] Generate personalized study recommendations.
- [ ] Recommend focus and break strategies.
- [ ] Add context-aware recommendations.
- [ ] Handle API errors and rate limits.
- [ ] Ensure raw webcam footage is never sent to the LLM.
- [ ] Validate that recommendations are grounded in actual student metrics.

### F. Gamification

- [ ] Implement XP calculation logic.
- [ ] Implement level progression.
- [ ] Implement achievement badges.
- [ ] Implement focus streak calculation.
- [ ] Implement daily study goals.
- [ ] Implement weekly goals.
- [ ] Implement daily challenges.
- [ ] Implement personal records.
- [ ] Add personalized AI-generated challenges.
- [ ] Prevent timer-only activity from earning focus rewards.
- [ ] Test XP and achievement calculations.

**Phase 4 Exit Criteria:**

The application must provide explainable personalization based on actual student history, grounded AI recommendations, and consistent gamification rules.

---

## Phase 5 — Integration, Testing, Privacy, and Deployment

**Status: UPCOMING.**

See [Phase 5 Integration and Deployment Guide](docs/development/PHASE_05_INTEGRATION_DEPLOYMENT.md).

### A. Complete System Integration

- [ ] Integrate React frontend and FastAPI backend.
- [ ] Integrate browser-local computer vision with backend APIs.
- [ ] Integrate attention and analytics services.
- [ ] Integrate personal baseline and pattern detection.
- [ ] Integrate AI Study Coach.
- [ ] Integrate gamification.
- [ ] Replace remaining demonstration data with actual recorded data where appropriate.

### B. Testing

- [ ] Complete unit tests.
- [ ] Complete API integration tests.
- [ ] Complete frontend component tests.
- [ ] Add end-to-end user workflow tests.
- [ ] Test multiple concurrent study sessions and users.
- [ ] Test camera permission and processing failure scenarios.
- [ ] Test database failure and recovery.
- [ ] Test browser compatibility.
- [ ] Test responsive layouts.
- [ ] Perform performance testing.

### C. Privacy and Security

- [ ] Perform authentication and authorization review.
- [ ] Review user-data isolation.
- [ ] Review consent management.
- [ ] Validate data-retention and deletion behavior.
- [ ] Verify no raw webcam footage is stored by default.
- [ ] Secure environment variables and API keys.
- [ ] Configure HTTPS and secure CORS policies.
- [ ] Review API rate limiting and abuse protection.
- [ ] Review MongoDB access and deployment security.

### D. Deployment

- [ ] Prepare Docker configuration.
- [ ] Prepare frontend production build.
- [ ] Deploy frontend.
- [ ] Deploy FastAPI backend.
- [ ] Configure MongoDB Atlas.
- [ ] Configure environment variables.
- [ ] Verify production API connectivity.
- [ ] Test production authentication.
- [ ] Test browser-local webcam processing in deployment.
- [ ] Add application monitoring and logging.
- [ ] Validate error handling in production.

**Phase 5 Exit Criteria:**

All major features must work together, testing must pass, privacy and security requirements must be checked, and the deployed application must be stable.

---

## Current Immediate Priorities

Complete these tasks in order:

1. [x] Run isolated browser QA for Phase 1 UI, Phase 2 recorded data, and synthetic Phase 3 camera flow.
2. [x] Assert synthetic-camera privacy payload, cleanup behavior, and local MongoDB deletion/indexes.
3. [ ] Repeat permission, device switch, disconnect, pause/end, route, and network checks with a physical camera.
4. [ ] Benchmark browser-local inference and CPU/battery impact on a laptop and mobile device.
5. [ ] Validate provisional visual signals using consented observations and the [Phase 3 protocol](docs/development/PHASE_03_VALIDATION.md).
6. [ ] Review false visual events, eye/gaze feasibility, and optional phone detection based on evidence.
7. [ ] Only then decide whether visual attention and focused-time metrics can be published.

## Scope and Development Rules

1. Phase 1 and Phase 2 implementations must not be unnecessarily rewritten.
2. Phase 3 physical-signal validation is still active; do not mark it complete from synthetic tests.
3. Phase 4A–B provisional engineering may run on recorded history, while validated attention claims wait for real testing.
4. Phase 5 must follow integration of the major modules.
5. Do not treat mock data as real measurements.
6. Do not confuse digital engagement with visual attention.
7. Do not claim to measure a student's actual mental state.
8. Keep raw webcam footage out of persistent storage by default.
9. Maintain user consent and data ownership.
10. Update this TODO whenever implementation status changes.
11. Mark features completed only after implementation and appropriate verification.
12. Keep phase documentation synchronized with the actual codebase.

---

## Final Project Objective

Build a privacy-first AI-powered student study companion that combines browser-local computer vision, behavioral analytics, personalized focus planning, machine learning, and Generative AI to help students understand and improve their study habits.

The platform should measure observable study behavior, identify potential distractions, explain individual patterns, and provide actionable recommendations without claiming to directly measure mental concentration.
