# Phase 3 signal feasibility decisions

## Eye and gaze direction

Google's [Face Landmarker documentation](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker) describes facial landmarks, optional blendshapes, and optional face transformation matrices. It does not provide a calibrated screen-gaze or reading-attention output. Iris landmarks are available through the [Face Landmarker API](https://developers.google.com/edge/api/mediapipe/js/tasks-vision.facelandmarker), but turning their geometry into gaze direction would require per-device/person calibration and labeled evaluation. **Decision:** do not add eye/gaze or blink to the Phase 3 score or events. The current nose/eye calculation is only a coarse head-orientation proxy, and downward posture cannot be reliably distinguished from normal book or note reading.

## Optional phone detection

[Ultralytics documents](https://docs.ultralytics.com/integrations/onnx) that YOLO models can be exported to ONNX and run in a web browser. Their [license documentation](https://docs.ultralytics.com/help/contributing) describes AGPL-3.0 and enterprise options, so YOLO remains excluded. The owner requested phone detection, and the implementation now uses the existing MediaPipe Object Detector with Google's recommended EfficientDet-Lite0 model. The model is downloaded from Google's host when monitoring starts, then inference occurs in the browser. The model weights are not redistributed in this repository because their redistribution terms are not clearly stated in the [official MediaPipe discussion](https://github.com/google-ai-edge/mediapipe/issues/6306). A phone outside the camera frame cannot be detected, and a visible phone does not prove distraction. This is an unvalidated prototype; real-camera false-positive and missed-detection testing is pending.

## Head pose and reliability

The [Face Landmarker output](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker) can include a 4×4 facial transformation matrix, but the current code uses only a normalized nose/eye geometry proxy. It must not be described as calibrated yaw/pitch estimation. The provisional index and `head_not_forward` event are labeled as camera-observed heuristics. Their thresholds must be checked against the [consented validation protocol](PHASE_03_VALIDATION.md), including ordinary writing and reading postures, before any attention or focused-time metric is enabled.
