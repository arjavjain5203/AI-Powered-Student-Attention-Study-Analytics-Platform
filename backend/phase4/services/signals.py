"""Phase 4 signal adapter: turns stored records into a uniform FocusSignal.

A FocusSignal is {value, source, confidence, sample_count}. ``value`` is None when
unavailable (never 0). Sources stay separate and are never blended:
  "digital"            digital_engagement_score heuristic (Phase 2)
  "visual_provisional" visual_signal_index heuristic (Phase 3, unvalidated)
  "validated"          reserved; nothing produces it until Phase 3 validation is done
"""
import math

# ASSUMPTION: expected spacing of digital records while a session is active.
# The current frontend does not post digital records, so confirm this value.
DIGITAL_RECORD_INTERVAL_SECONDS = 30
VISUAL_WINDOW_SECONDS = 10


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def make_signal(value, source, confidence, sample_count):
    return {"value": None if value is None else round(float(value), 1), "source": source,
            "confidence": round(max(0.0, min(1.0, float(confidence))), 2),
            "sample_count": int(sample_count)}


def digital_session_signal(active_seconds, records):
    """Mean digital engagement for one session; confidence = record coverage."""
    scores = [r["digital_engagement_score"] for r in records or []
              if _num(r.get("digital_engagement_score"))]
    if not scores:
        return make_signal(None, "digital", 0, 0)
    expected = max(1.0, (active_seconds or 0) / DIGITAL_RECORD_INTERVAL_SECONDS)
    return make_signal(sum(scores) / len(scores), "digital", len(scores) / expected, len(scores))


def visual_session_signal(active_seconds, records):
    """Mean provisional visual index over usable windows. Never validated attention."""
    usable = [r["visual_signal_index"] for r in records or []
              if r.get("quality") == "usable" and _num(r.get("visual_signal_index"))]
    if not usable:
        return make_signal(None, "visual_provisional", 0, 0)
    expected = max(1.0, (active_seconds or 0) / VISUAL_WINDOW_SECONDS)
    return make_signal(sum(usable) / len(usable), "visual_provisional", len(usable) / expected, len(usable))


def session_series(session, records):
    """[(elapsed_minute, score)] from digital records, ordered. Elapsed is wall-clock
    since start, so paused time is included (approximation)."""
    start = session.get("started_at")
    out = []
    for r in records or []:
        if start and r.get("captured_at") and _num(r.get("digital_engagement_score")):
            out.append((max(0.0, (r["captured_at"] - start).total_seconds() / 60),
                        float(r["digital_engagement_score"])))
    return sorted(out)


def session_summary(session, records):
    """One row per session for the baseline and planner."""
    active = session.get("active_seconds", 0)
    return {"session_id": str(session.get("_id")), "started_at": session.get("started_at"),
            "active_seconds": active, "signal": digital_session_signal(active, records),
            "series": session_series(session, records)}