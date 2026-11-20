# Phase 3 local QA record

## Camera-first and prompt-warning update — 2026-11-19

The Study Session screen now places the live clock over the main camera preview. An accepted provisional camera warning pauses the MongoDB-backed session immediately after two consecutive processed observations, and a warning banner appears on the preview. The browser initializes the face model and Google's downloadable EfficientDet-Lite0 phone model before starting time. The local Chrome synthetic-camera run passed at 375, 768, and 1440 CSS pixels without horizontal overflow or unexpected console errors. Its blank video exercised the `face_not_visible` path, not real phone or head recognition. It also verified the paused clock, explicitly consented false-alarm clip upload, admin retrieval, owner deletion, permission denial, 503/401 handling, and reload behavior. `backend/` tests: 17 passed, 1 optional real-Mongo test skipped; frontend tests: 3 passed; Vite build passed. Physical-camera phone/head accuracy and dual-model performance remain unverified. The earlier results below refer to the prior two-window alert implementation.

The later development run added QA-only injected head and phone categories to exercise their full warning/API/timer paths, plus a blocked face-model check. These injections do not test actual recognition accuracy. The same run checked the recorded Analytics pattern tracker at 375, 768, and 1440 CSS pixels with no horizontal overflow. Phase 4A–B backend tests and the isolated presentation seed check are recorded in the [Phase 4 QA record](PHASE_04_QA.md).

## Recorded-first and false-alarm update

The latest isolated Chrome run opened directly at sign-in with no mode toggle or separate Recorded workspace navigation item. It verified zero timer time before camera readiness, a clock that advanced without refresh, automatic pause after the synthetic `face_not_visible` event, a stable paused clock, a loadable local clip preview, an explicit clip-sharing checkbox, a successful local admin clip retrieval, student deletion of the report and clip, resume after camera restart, manual pause, permission-denial behavior, 503/401 error states, and ended-session persistence after reload. Sign-in and session screenshots at 375, 768, and 1440 CSS pixels had no horizontal overflow. Backend tests now include camera-gated lifecycle, consent-lease expiry capping, recent-event and owner checks for false-alarm reports, clip consent, admin access, and deletion. The previous Chrome/Edge benchmark notes below describe earlier runs of the camera prototype; the current UI and clip flow has only been rerun in Chrome.

## Automated results

- `python -m pytest -q` in `backend/`: 16 passed, 1 optional real-Mongo test skipped in the isolated run. This includes controlled-clock timing, camera-gated lifecycle, and false-alarm authorization tests.
- `python backend/scripts/run_real_mongo_check.py`: 1 passed against local MongoDB, including visual-record creation, no raw-data fields, TTL indexes, and deletion.
- `npm test`: 2 frontend signal-rule tests passed.
- `npm run build`: passed. Vite reports a JavaScript chunk over 500 kB; this is a performance follow-up, not a build failure.
- `python backend/scripts/evaluate_visual_signals.py <csv>`: CLI smoke passed on two explicitly synthetic rows; this does not substitute for participant observations.
- `npm run test:browser`: the updated recorded-first and false-alarm flow passed in local Chrome 157.0.8103.79. Earlier camera-only smoke runs also passed in Edge 157.0.4341.60. Each run created isolated API/Vite servers and a temporary MongoDB database, which the script removed afterward.

The browser test visited every presentation route, checked keyboard navigation and visible focus, and inspected 375, 768, and 1440 CSS-pixel screenshots of demo, recorded sign-in, and recorded session views. There was no horizontal overflow or unexpected console error. A clipped mobile Recharts axis was fixed after screenshot review. The recorded session clock advanced during an active session, stayed fixed during pause, and advanced again after resume.

The browser test used a generated blank Y4M video as a **synthetic camera**. It confirmed explicit opt-in, two 10-second derived windows, a provisional `face_not_visible` event, consent-gated API ingestion, a same-origin model/WASM load, and a request body containing only `algorithm_version`, `total_samples`, `valid_samples`, `face_samples`, and `forward_samples`. It also checked camera cleanup on disconnect, route change, pause, end, and reload; permission denial; missing device; model-load failure; and empty browser storage. The UI hides the new-session form while a session is open; the API's second-session 409 remains covered by backend tests. Deliberately injected 503 and 401 API responses produced the expected UI states.

In headless runs, Chrome averaged 15–29 ms per processed frame (29 ms in the latest timer regression run) and previously reported about 0.82–0.87 seconds of task time over a 21-second synthetic capture window; Edge averaged 17 ms per frame and reported about 0.90 seconds of task time. The latest Chrome run reported about 13 MB of JavaScript heap at measurement time. These are environment-specific smoke measurements, **not** physical-device CPU or battery benchmarks. The generated video has no face, so the test does not verify face-detection accuracy or head-orientation thresholds.

## Remaining acceptance evidence

Test with consenting people and physical cameras on a laptop and mobile device. Follow [Phase 3 validation protocol](PHASE_03_VALIDATION.md) to measure missing-signal and false-event rates across lighting, camera quality, posture, eyewear, and available participant variation. Verify the real permission prompt, device switching between working cameras, developer-tools network payloads, CPU/battery impact, and latency. Do not promote the provisional index to `visual_attention_score` or derive focused time until those results support a reviewed rule.

Local screenshots and the latest machine-readable run report are in ignored `.local/browser-qa/`; they contain synthetic UI/camera data and no participant imagery.
