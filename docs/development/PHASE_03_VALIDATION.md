# Phase 3 visual-signal validation protocol

## Purpose and boundary

This protocol evaluates whether the **observable** face-presence and coarse head-orientation proxy behaves consistently. It does not validate mental attention, comprehension, distraction, or a focused-time metric. The current thresholds and index are provisional. Do not mark Phase 3 complete or promote `visual_attention_score` from `null` until actual consented results are reviewed.

## Consent and setup

Use only volunteers who explicitly agree to camera use and to recording derived 10-second counts. No raw footage, screenshots of people, facial landmarks, names, email addresses, or account tokens belong in the results. Use a dedicated test account and delete its visual records after export. Participants can stop at any time. Record the browser and device class, ambient light category, camera quality, and optional self-described eyewear/skin-tone group only if the participant consents; keep group reporting aggregate and avoid small identifiable cells.

Run the app over localhost or HTTPS with the local backend and MongoDB. Create a study session, click **Start camera and timer**, and verify the browser camera indicator and live clock. Confirm setup time is zero, the clock stops on manual pause, camera stop, denial, disconnect, route exit, and provisional alert, and resume requires camera startup. In browser developer tools, confirm that five bounded count/version fields reach `/visual-records`, only category/version reach `/visual-events`, the face model/WASM load from the app origin, and the phone model downloads from Google's host for local inference. No image/landmark/video payload or browser storage entry should appear by default. A false-alarm clip must remain local until the student previews it, checks the sharing agreement, and clicks **Send clip and continue**; verify the separate upload, seven-day expiry field, restricted review access, and student deletion. Verify stop, pause, end, route change, reload, device switch, denial, and disconnect states with physical cameras.

## Observation blocks

For each available device and participant, use 10-second blocks with a spoken or written instruction and a separate observer label. Suggested blocks: face centered toward screen, turn left/right, look down at a book, move out of camera view, cover camera, dim light, ordinary free study, phone held visibly at several angles, and phone outside the frame. Repeat blocks to sample variation. Do not label free study as mentally focused or distracted. Record only the server's aggregate window values, provisional warning category/time, and observer labels for visible face, coarse orientation, and visible phone. Note when a window overlaps a transition; exclude it from threshold analysis and report the exclusion count.

Minimum exploratory coverage before threshold review: at least three consenting participants, two camera/device classes including one mobile device, and repeated blocks in normal and dim light. Seek eyewear and skin-tone variation where participation is available; document missing groups rather than inferring fairness. This is an exploratory engineering gate, not evidence of scientific validity.

## Analysis and decision

Compare `face_samples / valid_samples` to observer face-visible labels and `forward_samples / face_samples` to observer coarse-orientation labels. Report confusion matrices, false-positive and false-negative counts/rates, missing-signal rate, and average sample coverage overall and by available conditions. Include the number of windows and participants; do not present a percentage without its denominator. Inspect every provisional visual event against the observed block and note ordinary-study false alerts. Measure average inference milliseconds per frame, browser main-thread task time, and battery/CPU impact on each physical device.

Save de-identified observed windows as CSV with this header (one row per 10-second window):

```csv
total_samples,valid_samples,face_samples,forward_samples,observer_face_visible,observer_head_forward,condition
```

Use `yes`/`no` observer labels; leave `observer_head_forward` blank when it cannot be judged. `condition` can describe a non-identifying setup such as `normal_light`, `dim_light`, or `glasses`. Run `python backend/scripts/evaluate_visual_signals.py observations.csv` from the project root. The script prints overall and per-condition confusion matrices, sensitivity, specificity, and missing-window rates. Its default 0.5 comparison thresholds are exploratory and can be changed with `--face-threshold` and `--forward-threshold`; they do not validate attention. Keep participant identity and raw camera data out of the CSV.

If the proxy misses ordinary study posture, performs inconsistently across conditions, or produces frequent false events, revise or disable the rules. Keep `visual_attention_score` and `estimated_focused_seconds` unavailable until an explicit product review defines a target observable construct, acceptable error bounds, and calibration data. Eye/gaze estimation should be explored separately: the current nose/eye geometry is not eye tracking. The MediaPipe phone detector is a provisional prototype; test its misses and false warnings before calling it reliable. YOLO remains excluded.

## Evidence to save

Store a dated, de-identified results table outside the public repository, plus a summary in this directory: device/browser versions, number of participants and windows, conditions covered, confusion matrices, latency/CPU measurements, privacy-network findings, and decisions. Do not fabricate missing observations. Update `TODO.md` only for checks supported by this evidence.
