# Phase 03 — Computer vision and visual signals

## Objective and status

**ACTIVE; physical-camera and labeled-signal validation pending.** Browser-local camera monitoring is required to run the Study Session timer; permission still requires an explicit student click. The implementation is a provisional face-presence and head-orientation *proxy*. It does not measure comprehension, mental focus, gaze, or validated visual attention. Phase 2 authenticated sessions and MongoDB are prerequisites.

## Scope and implementation order

1. Create a camera-required session in `awaiting_camera`. Request browser permission only after the student clicks **Start camera and timer**. Activate server time after the camera, model, and consent lease are ready. On resume, restart the camera before changing from paused to active.
2. Load the bundled MediaPipe Face Landmarker model and WASM assets in the browser. Sample at approximately 2 Hz and aggregate 10-second windows. Keep frames and landmarks in memory only.
3. Estimate face presence and a coarse forward head-orientation proxy from nose and eye landmarks. Count unusable samples separately. Do not infer eye gaze, blink, phone use, or mental distraction from this prototype.
4. Register server-side visual consent; submit only nested sample counts and an algorithm version. FastAPI calculates the provisional index. Consent expires after 60 seconds without a successful window upload, and is revoked on stop, pause, or session end. Camera loss or lease expiry pauses server-tracked session time.
5. Store derived visual windows and provisional camera-observed events in separate MongoDB collections with 90-day TTL indexes. Offer earlier per-session deletion. A provisional event pauses the timer and displays a false-alarm choice; it is not a validated distraction. Keep digital engagement records, validated visual attention, and combined engagement separate.
6. Keep a browser-memory WebM segment of at most eight seconds while monitoring. On a false alarm, preview it and send it only after explicit sharing agreement. A recent owned event is required for either a clip or metadata-only report. Store sent clips in a separate seven-day TTL collection, with owner deletion and a restricted admin review API.
7. Evaluate accuracy, usability, CPU cost, lighting, eyewear, skin tones, and device variation with consented participants before treating any threshold as reliable.

## Relevant files and dependencies

- `src/VisualMonitor.jsx`: opt-in UI, local preview, stream and inference lifecycle.
- `src/visualSignals.js`: count aggregation and coarse orientation proxy.
- `public/mediapipe/`: bundled Google model and WASM runtime. See [asset provenance](../MEDIAPIPE_ASSETS.md) for source, version, checksum, and license boundary.
- `backend/app/services/visual.py`: versioned provisional index and missing-quality behavior.
- `backend/app/main.py`: consent and visual-record endpoints, owned-session checks, TTL index.
- `backend/tests/test_visual.py`, `src/visualSignals.test.js`: deterministic rule and API tests.
- `tests/browser-smoke.mjs`: isolated Chrome/Edge smoke test with a synthetic camera and a temporary MongoDB database.
- `backend/scripts/evaluate_visual_signals.py`: de-identified observation evaluator for the remaining validation gate.

No Python OpenCV, YOLO, or GenAI dependency is needed for browser-local Phase 3. Camera access requires a browser secure context (HTTPS or localhost) and student permission.

## API and database contract

Student endpoints require the existing Bearer JWT and an owned session. `POST /api/sessions` accepts `camera_required`; the website sends `true`, creating `awaiting_camera`. `POST /api/sessions/{id}/visual-consent` accepts awaiting or paused camera-required sessions and starts a 60-second consent lease. `POST /api/sessions/{id}/activate` and resume require a current lease. Each accepted visual window renews it. `DELETE /api/sessions/{id}/visual-consent` revokes authorization and pauses a camera-required active session. Pausing or ending also revokes it. Server reads reconcile an expired lease and cap active time at expiry. A browser reload clears the in-memory JWT and stops the camera.

`POST /api/sessions/{id}/visual-records` requires active consent and accepts only `algorithm_version`, `total_samples`, `valid_samples`, `face_samples`, and `forward_samples`. Counts are bounded to 0–50 and must be nested. The server timestamps the record, calculates `visual_signal_index`, sample coverage, quality, and explanations, and enforces an eight-second minimum between windows. It does not accept a client-supplied score or image. `GET` lists up to 100 recent windows; `DELETE` removes all visual windows and visual events for the owned session. MongoDB `visual_records.expires_at` and `visual_events.expires_at` have 90-day expiry indexes. Existing digital records are not migrated or reinterpreted.

`GET /api/sessions/{id}/visual-events` lists separate provisional camera-observed events. Two consecutive usable windows with face presence at most 20% generate `face_not_visible`; two with presence at least 80% and forward proxy at most 20% of face samples generate `head_not_forward`. Events require windows within 30 seconds and have a 60-second cooldown per category. They are **not** counted in the existing client-reported distraction analytics and do not claim the student was distracted. These thresholds are provisional and may be discarded after validation.

The index is `round(100 × (0.4 × face_samples/valid_samples + 0.6 × forward_samples/valid_samples))`. It is `null` when fewer than five valid samples or less than half the samples are usable. `sample_coverage` is the usable-sample fraction, not calibrated confidence. The coefficients and geometry bounds are provisional engineering heuristics, not validated scientific thresholds. `visual_attention_score`, `combined_study_engagement`, and `estimated_focused_seconds` remain `null` until later validation and calibration.

## Integration and privacy

The camera is stopped on explicit stop, route change, tab hiding, pause/end, sign-out, or component cleanup. A server consent flag alone cannot prove that a browser is capturing; a browser client can forge count payloads, so these records must not grant rewards or carry clinical claims. Raw frames and landmarks are not sent to the visual-record API. A video segment exists only in volatile browser memory until a student explicitly sends it after a false alarm. `POST /api/sessions/{id}/false-alarms` requires a recent owned event, and clips require `share_clip=true`, WebM format, and a maximum 5 MB size. `GET /api/false-alarms/mine` and owner deletion provide student control. The local admin review endpoints require a separate 32+ character `REVIEW_ADMIN_TOKEN`; no review credential reaches the frontend. The backend does not verify clip duration or visual content. The source model and WASM are loaded from this app's own static assets. When a record submission fails, monitoring stops and an error is shown.

## Testing and acceptance

Automated: test scoring and unknown quality; nested-count and arbitrary-score rejection; user ownership; missing and expired consent; camera-gated timing; revocation; rate limiting; event duration/cooldown; per-session deletion; false-alarm clip access and consent; real MongoDB expiry indexes; frontend geometry and count aggregation; production build. `npm run test:browser` starts isolated app/API servers and a temporary MongoDB database, then tests recorded-first navigation, responsive overflow, camera setup, live timer, provisional alert pause, explicit clip sharing, manual pause, reload, and the exact outbound count payload. It writes screenshots and a JSON run report under ignored `.local/browser-qa/`. Chrome and Edge results are summarized in the [local QA record](PHASE_03_QA.md). Existing Phase 2 backend tests must continue passing.

Manual acceptance still required: repeat camera permission, device switching, disconnect, tab hiding, pause/end, and network inspection with physical cameras and supported browsers. Record inference latency and CPU load on a typical laptop and mobile browser; the synthetic headless benchmark is not a device benchmark. Conduct a consented labeled evaluation across lighting, eyewear, skin tones, and posture before promoting the index to visual-attention analytics. Follow the [validation protocol](PHASE_03_VALIDATION.md). The [eye/gaze and optional phone-detection review](PHASE_03_FEASIBILITY.md) explains why neither is included in the current runtime.

## Known risks and completion checklist

Face visibility can fail for ordinary study posture, lighting, occlusion, camera placement, or assistive use. Coarse facial geometry is not calibrated head pose. The current index is not suitable for student ranking, grades, or punitive alerts. The bundled model and WASM add substantial static asset size. Review model distribution terms before deployment.

- [x] Explicit permission and revoke UX implemented in camera-required timed sessions.
- [x] Automatic provisional alert pause, false-alarm review, and optional clip submission implemented with backend tests and synthetic Chrome QA.
- [x] Browser-local face-presence and coarse orientation prototype implemented.
- [x] Owned derived-signal API, validation, consent, deletion, and 90-day expiry implemented.
- [x] Deterministic service/API and frontend signal tests added.
- [x] Isolated synthetic-camera browser QA, responsive screenshots, and exact network-payload check recorded.
- [ ] Physical-camera, mobile-device performance, and manual privacy-network QA recorded.
- [ ] Consented labeled evaluation and fairness review completed.
- [x] Eye/gaze and optional phone-detection desk review documented with official sources; any implementation remains conditional on validation.
