"""Personal baseline from a student's own eligible sessions (median + IQR).

Returns status "insufficient_data" instead of a number when history is thin, so
callers never compare against a misleading baseline.
"""
import statistics

MIN_SESSIONS = 5
MIN_ACTIVE_SECONDS = 600
MIN_CONFIDENCE = 0.5


def eligible(summary, min_active=MIN_ACTIVE_SECONDS, min_conf=MIN_CONFIDENCE):
    """A session counts toward the baseline only if it has a real signal,
    enough record coverage, and enough active time."""
    s = summary["signal"]
    return (s["value"] is not None and s["confidence"] >= min_conf
            and summary["active_seconds"] >= min_active)


def compute_baseline(summaries, min_sessions=MIN_SESSIONS):
    good = [s for s in summaries if eligible(s)]
    base = {"status": "insufficient_data", "source": "digital", "sessions_used": len(good),
            "sessions_needed": min_sessions, "median": None, "q1": None, "q3": None,
            "iqr": None, "rule_version": "baseline-v1"}
    if len(good) < min_sessions:
        base["reason"] = f"Need {min_sessions} usable sessions; have {len(good)}."
        return base
    vals = sorted(s["signal"]["value"] for s in good)
    q1, _, q3 = statistics.quantiles(vals, n=4, method="inclusive")
    base.update(status="ok", median=round(statistics.median(vals), 1), q1=round(q1, 1),
                q3=round(q3, 1), iqr=round(q3 - q1, 1), reason="Baseline from your own sessions.")
    return base


def compare_to_baseline(value, baseline):
    """Position of a score relative to the personal range; None if no valid baseline."""
    if value is None or baseline.get("status") != "ok":
        return None
    if value < baseline["q1"]:
        return "below_usual"
    if value > baseline["q3"]:
        return "above_usual"
    return "typical"