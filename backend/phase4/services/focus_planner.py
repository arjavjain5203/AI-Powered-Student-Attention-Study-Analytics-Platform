"""Personalized focus planner (rule-based, explainable, provisional).

Falls back to the Phase 2 heuristic when there is no valid personal baseline.
Every recommendation carries human-readable reasons. Not validated attention.
"""
import statistics

from app.services.planner import break_check, recommend_plan  # teammate's code, read-only
from phase4.services.baseline import compute_baseline

MIN_FOCUS, MAX_FOCUS = 15, 50
DECLINE_WINDOWS = 3          # consecutive records below the personal floor
TREND_DELTA = 5.0            # points between older and newer sessions
MIN_ONSET_SESSIONS = 3


def _round5(x):
    return int(5 * round(x / 5))


def _floor(baseline):
    """Personal 'low' line: a little under the student's usual range."""
    return max(0.0, baseline["q1"] - 0.5 * baseline["iqr"])


def decline_onset(series, baseline, windows=DECLINE_WINDOWS):
    """Elapsed minute where `windows` consecutive scores fall below the personal floor, else None."""
    low, floor = 0, _floor(baseline)
    for minute, score in series:
        low = low + 1 if score < floor else 0
        if low >= windows:
            return minute
    return None


def _trend(summaries):
    vals = [s["signal"]["value"] for s in summaries if s["signal"]["value"] is not None][-6:]
    if len(vals) < 4:
        return "unknown"
    half = len(vals) // 2
    delta = sum(vals[-half:]) / half - sum(vals[:half]) / half
    return "declining" if delta <= -TREND_DELTA else "improving" if delta >= TREND_DELTA else "steady"


def personalized_plan(summaries, baseline=None):
    summaries = sorted(summaries, key=lambda s: s["started_at"])
    baseline = baseline or compute_baseline(summaries)
    fallback = recommend_plan([s["signal"]["value"] for s in summaries if s["signal"]["value"] is not None])
    if baseline["status"] != "ok":
        return {**fallback, "personalized": False, "baseline": baseline, "score_source": "digital_engagement",
                "reasons": [baseline["reason"], "Using the general starting suggestion."] + fallback["reasons"]}

    durations, censored = [], 0
    for s in summaries[-10:]:
        if s["active_seconds"] < 600 or not s["series"]:
            continue
        onset = decline_onset(s["series"], baseline)
        if onset is None:
            censored += 1  # engagement never dropped, so the block could have been at least this long
        durations.append(onset if onset is not None else s["active_seconds"] / 60)

    reasons = []
    focus = fallback["focus_minutes"]
    if len(durations) >= MIN_ONSET_SESSIONS:
        focus = _round5(statistics.median(durations))
        found = len(durations) - censored
        reasons.append(f"Across {len(durations)} recent sessions your engagement typically held for about "
                       f"{statistics.median(durations):.0f} min ({found} showed a drop, {censored} did not).")
    else:
        reasons.append("Not enough sessions with in-session records to personalize block length; kept the general value.")

    trend = _trend(summaries)
    if trend == "declining":
        focus -= 5
        reasons.append("Recent session averages are lower than earlier ones; block shortened by 5 minutes.")
    elif trend == "improving":
        reasons.append("Recent session averages are higher than earlier ones; no change needed.")

    focus = max(MIN_FOCUS, min(MAX_FOCUS, _round5(focus)))
    brk = 5 if focus <= 25 else 10
    return {"focus_minutes": focus, "break_minutes": brk,
            "long_break_minutes": 15 if focus <= 30 else 20,
            "cycles_before_long_break": 4 if focus <= 25 else 3,
            "trend": trend, "personalized": True, "baseline": baseline,
            "sample_count": len(durations), "score_source": "digital_engagement",
            "confidence": "low" if len(durations) < 6 else "medium", "heuristic": True,
            "reasons": reasons + [f"Break lengths scale with block length ({brk} min short break)."]}


def early_break_check(elapsed_minutes, plan, recent_scores):
    """Break advice: personal-floor rule when a baseline exists, else the Phase 2 rule."""
    base = plan.get("baseline") or {}
    if not plan.get("personalized") or base.get("status") != "ok":
        return break_check(elapsed_minutes, plan["focus_minutes"], recent_scores)
    if elapsed_minutes >= plan["focus_minutes"]:
        return {"take_break": True, "urgency": "scheduled", "reason": "Your planned block has ended."}
    last = [s for s in recent_scores if isinstance(s, (int, float))][-DECLINE_WINDOWS:]
    if (elapsed_minutes >= 10 and len(last) == DECLINE_WINDOWS
            and all(s < _floor(base) for s in last)):
        return {"take_break": True, "urgency": "early",
                "reason": f"Last {DECLINE_WINDOWS} readings are below your usual range ({_floor(base):.0f}); consider a short break."}
    return {"take_break": False, "urgency": "none",
            "minutes_left": round(plan["focus_minutes"] - elapsed_minutes, 1), "reason": "No break suggested yet."}