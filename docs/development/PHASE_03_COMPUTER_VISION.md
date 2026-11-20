# Phase 03 — Computer vision and visual signals

## Objective and status

**ACTIVE; physical-camera and labeled-signal validation pending.** Browser-local camera monitoring is required to run the Study Session timer; permission still requires an explicit student click. The implementation has provisional face-presence, head-orientation, and visible-phone warnings. It does not measure comprehension, mental focus, gaze, or validated visual attention. Phase 2 authenticated sessions and MongoDB are prerequisites.

## Scope and implementation order

1. Create a camera-required session in `awaiting_camera`. Request browser permission only after the student clicks **Start camera and timer**. Activate server time after the camera, model, and consent lease are ready. On resume, restart the camera before changing from paused to active.
2. Load the bundled MediaPipe Face Landmarker model and WASM assets in the browser. Download Google's EfficientDet-Lite0 phone model on camera start; run both models locally. Sample at approximately 2 Hz and aggregate 10-second windows. Keep frames and landmarks in memory only.
3. Estimate face presence and a coarse forward head-orientation proxy from nose and eye landmarks. Count unusable samples separately. Recognize only the visible `cell phone` class from object detection. Two consecutive qualifying observations produce a prompt warning. This does not establish phone use or mental distraction.
4. Register server-side visual consent; submit only nested sample counts and an algorithm version. FastAPI calculates the provisional index. Consent expires after 60 seconds without a successful window upload, and is revoked on stop, pause, or session end. Camera loss or lease expiry pauses server-tracked session time.
5. Store derived visual windows and client-reported provisional camera warnings in separate MongoDB collections with 90-day TTL indexes. Offer earlier per-session deletion. The warning API atomically pauses the server timer and displays a false-alarm choice; a warning is not a validated distraction. Keep digital engagement records, validated visual attention, and combined engagement separate.
6. Keep a browser-memory WebM segment of at most eight seconds while monitoring. On a false alarm, preview it and send it only after explicit sharing agreement. A recent owned event is required for either a clip or metadata-only report. Store sent clips in a separate seven-day TTL collection, with owner deletion and a restricted admin review API.
7. Evaluate accuracy, usability, CPU cost, lighting, eyewear, skin tones, and device variation with consented participants before treating any threshold as reliable.

## Relevant files and dependencies

- `src/VisualMonitor.jsx`: opt-in UI, local preview, stream and inference lifecycle.
- `src/visualSignals.js`: count aggregation and coarse orientation proxy.
- `public/mediapipe/`: bundled Google model and WASM runtime. See [asset provenance](../MEDIAPIPE_ASSETS.md) for source, version, checksum, and license boundary.
- Google's EfficientDet-Lite0 int8 model is fetched from its official model host at runtime; its weights are not bundled. See [feasibility findings](PHASE_03_FEASIBILITY.md).
- `backend/app/services/visual.py`: versioned provisional index and missing-quality behavior.
- `backend/app/main.py`: consent and visual-record endpoints, owned-session checks, TTL index.
- `backend/tests/test_visual.py`, `src/visualSignals.test.js`: deterministic rule and API tests.
- `tests/browser-smoke.mjs`: isolated Chrome/Edge smoke test with a synthetic camera and a temporary MongoDB database.
- `backend/scripts/evaluate_visual_signals.py`: de-identified observation evaluator for the remaining validation gate.

No Python OpenCV, YOLO, or GenAI dependency is needed for browser-local Phase 3. Camera access requires a browser secure context (HTTPS or localhost) and student permission.

## API and database contract

Student endpoints require the existing Bearer JWT and an owned session. `POST /api/sessions` accepts `camera_required`; the website sends `true`, creating `awaiting_camera`. `POST /api/sessions/{id}/visual-consent` accepts awaiting or paused camera-required sessions and starts a 60-second consent lease. `POST /api/sessions/{id}/activate` and resume require a current lease. Each accepted visual window renews it. `DELETE /api/sessions/{id}/visual-consent` revokes authorization and pauses a camera-required active session. Pausing or ending also revokes it. Server reads reconcile an expired lease and cap active time at expiry. A browser reload clears the in-memory JWT and stops the camera.

`POST /api/sessions/{id}/visual-records` requires active consent and accepts only `algorithm_version`, `total_samples`, `valid_samples`, `face_samples`, and `forward_samples`. Counts are bounded to 0–50 and must be nested. The server timestamps the record, calculates `visual_signal_index`, sample coverage, quality, and explanations, and enforces an eight-second minimum between windows. It does not accept a client-supplied score or image. `GET` lists up to 100 recent windows; `DELETE` removes all visual windows and visual events for the owned session. MongoDB `visual_records.expires_at` and `visual_events.expires_at` have 90-day expiry indexes. Existing digital records are not migrated or reinterpreted.

`POST /api/sessions/{id}/visual-events` accepts only `category` (`face_not_visible`, `head_not_forward`, or `phone_visible`) and the matching algorithm version from an owned active camera session with current consent. The server pauses the session when it saves the event and revokes consent. The browser triggers after two consecutive processed observations, typically about one second. `GET` lists the provisional events. They are client-reported, not validated detections, and do not claim the student was distracted. The old two-window event rule is retained only as diagnostic `event_candidate` on window records; it no longer creates alerts.

The index is `round(100 × (0.4 × face_samples/valid_samples + 0.6 × forward_samples/valid_samples))`. It is `null` when fewer than five valid samples or less than half the samples are usable. `sample_coverage` is the usable-sample fraction, not calibrated confidence. The coefficients and geometry bounds are provisional engineering heuristics, not validated scientific thresholds. `visual_attention_score`, `combined_study_engagement`, and `estimated_focused_seconds` remain `null` until later validation and calibration.

## Integration and privacy

The camera is stopped on explicit stop, route change, tab hiding, pause/end, sign-out, or component cleanup. A server consent flag alone cannot prove that a browser is capturing; a browser client can forge warning or count payloads, so these records must not grant rewards or carry clinical claims. Raw frames and landmarks are not sent to the APIs. A video segment exists only in volatile browser memory until a student explicitly sends it after a false alarm. `POST /api/sessions/{id}/false-alarms` requires a recent owned event, and clips require `share_clip=true`, WebM format, and a maximum 5 MB size. `GET /api/false-alarms/mine` and owner deletion provide student control. The local admin review endpoints require a separate 32+ character `REVIEW_ADMIN_TOKEN`; no review credential reaches the frontend. The backend does not verify clip duration or visual content. The face model and WASM load from app assets; the phone model downloads from Google and runs locally. A detector or record failure stops monitoring and pauses the timer.

## Testing and acceptance

Automated: test scoring and missing quality; nested-count and arbitrary-score rejection; user ownership; missing and expired consent; camera-gated timing; revocation; rate limiting; prompt warning pause; per-session deletion; false-alarm clip access and consent; real MongoDB expiry indexes; frontend geometry and warning classification; production build. `npm run test:browser` starts isolated app/API servers and a temporary MongoDB database, then tests navigation, responsive overflow, camera setup, blank-camera face absence, injected synthetic head/phone warning categories, paused timer, model-load failure, explicit clip sharing and deletion, reload, and camera denial. Its injection is enabled only by a Vite QA environment flag; it tests event/timer integration, not real head/phone recognition. It writes screenshots and a JSON run report under ignored `.local/browser-qa/`.

Manual acceptance still required: repeat camera permission, device switching, disconnect, tab hiding, pause/end, phone presentation, head turns, and network inspection with physical cameras and supported browsers. Record inference latency and CPU load with both models on a typical laptop and mobile browser; the synthetic headless benchmark is not a device benchmark. Conduct a consented labeled evaluation across lighting, eyewear, skin tones, posture, and phone placements before promoting any metric. Follow the [validation protocol](PHASE_03_VALIDATION.md). The [feasibility review](PHASE_03_FEASIBILITY.md) documents remaining phone-model and gaze limitations.

## Known risks and completion checklist

Face visibility can fail for ordinary study posture, lighting, occlusion, camera placement, or assistive use. Coarse facial geometry is not calibrated head pose. Phone recognition can miss small, obscured, rear-facing, or off-frame phones. The current index and warnings are not suitable for student ranking, grades, or punitive alerts. The phone model requires a network download at camera start; clarify its weight redistribution terms before bundling it for offline/deployed use.

- [x] Explicit permission and revoke UX implemented in camera-required timed sessions.
- [x] Automatic provisional alert pause, false-alarm review, and optional clip submission implemented with backend tests and synthetic Chrome QA.
- [x] Browser-local face-presence and coarse orientation prototype implemented.
- [x] Owned derived-signal API, validation, consent, deletion, and 90-day expiry implemented.
- [x] Deterministic service/API and frontend signal tests added.
- [x] Isolated synthetic-camera browser QA, responsive screenshots, and exact network-payload check recorded.
- [ ] Physical-camera, mobile-device performance, and manual privacy-network QA recorded.
- [ ] Consented labeled evaluation and fairness review completed.
- [x] Eye/gaze desk review and provisional visible-phone prototype documented.
- [ ] Physical-phone accuracy, false-warning rate, and dual-model performance validated.
