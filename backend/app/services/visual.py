"""Provisional, explainable visual-signal index from bounded window summaries.

This is an observable camera-signal heuristic, not a measure of comprehension.
"""

ALGORITHM_VERSION = "face-presence-head-orientation-v1"


def candidate_visual_event(valid_samples, face_samples, forward_samples, quality):
    """Classify an observable two-window candidate, without claiming distraction."""
    if quality != "usable" or valid_samples < 10:
        return None
    if face_samples / valid_samples <= 0.2:
        return "face_not_visible"
    if face_samples / valid_samples >= 0.8 and forward_samples / face_samples <= 0.2:
        return "head_not_forward"
    return None


def summarize_visual_window(total_samples, valid_samples, face_samples, forward_samples):
    if not (0 <= forward_samples <= face_samples <= valid_samples <= total_samples):
        raise ValueError("Sample counts must be nested and nonnegative")
    coverage = round(valid_samples / total_samples, 2) if total_samples else 0.0
    if total_samples == 0 or valid_samples < 5 or coverage < 0.5:
        return {"visual_signal_index": None, "quality": "insufficient",
                "sample_coverage": coverage, "reasons": ["Too few usable camera samples"]}
    presence = face_samples / valid_samples
    forward = forward_samples / valid_samples
    index = round(100 * (0.4 * presence + 0.6 * forward))
    reasons = []
    if face_samples < valid_samples:
        reasons.append("Face absent in some usable samples")
    if forward_samples < face_samples:
        reasons.append("Head orientation outside the provisional forward range in some samples")
    if not reasons:
        reasons.append("Face detected with provisional forward orientation")
    return {"visual_signal_index": index, "quality": "usable", "sample_coverage": coverage,
            "reasons": reasons}
