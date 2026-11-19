from datetime import datetime, timedelta, timezone

from phase4.services.focus_planner import decline_onset, early_break_check, personalized_plan
from phase4.services.signals import session_summary

T0 = datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc)


def make_session(i, scores, step_s=30):
    """Build a session summary from a list of scores, one record every `step_s` seconds."""
    start = T0 + timedelta(days=i)
    records = [{"captured_at": start + timedelta(seconds=step_s * (k + 1)), "digital_engagement_score": s}
               for k, s in enumerate(scores)]
    session = {"_id": f"s{i}", "started_at": start, "active_seconds": step_s * len(scores)}
    return session_summary(session, records)


def steady(n, level=70, length=60):
    return [make_session(i, [level] * length) for i in range(n)]


def test_new_user_gets_fallback_with_reasons():
    plan = personalized_plan([])
    assert plan["personalized"] is False
    assert plan["baseline"]["status"] == "insufficient_data"
    assert plan["focus_minutes"] == 25 and plan["break_minutes"] == 5
    assert plan["reasons"]
    assert plan["score_source"] == "digital_engagement"


def test_steady_history_without_drop_uses_session_length():
    plan = personalized_plan(steady(6))  # 30-minute sessions, never below the floor
    assert plan["personalized"] is True
    assert plan["focus_minutes"] == 30
    assert plan["break_minutes"] == 10
    assert plan["long_break_minutes"] == 15
    assert plan["cycles_before_long_break"] == 3
    assert plan["trend"] == "steady"
    assert any("did not" in r for r in plan["reasons"])


def test_block_length_is_capped_at_fifty():
    plan = personalized_plan(steady(6, length=120))  # 60-minute sessions, no drop
    assert plan["focus_minutes"] == 50
    assert plan["long_break_minutes"] == 20


def test_drop_after_about_twenty_minutes_shapes_the_plan():
    crash = [80] * 40 + [20] * 20  # drops at minute 20 of a 30-minute session
    plan = personalized_plan([make_session(i, crash) for i in range(6)])
    assert plan["personalized"] is True
    assert plan["focus_minutes"] == 20
    assert plan["break_minutes"] == 5
    assert plan["cycles_before_long_break"] == 4
    assert any("typically held" in r for r in plan["reasons"])


def test_very_early_drop_is_clamped_to_minimum():
    crash = [80] * 8 + [10] * 52  # drops after about 5 minutes
    plan = personalized_plan([make_session(i, crash) for i in range(6)])
    assert plan["focus_minutes"] == 15


def test_declining_trend_shortens_block():
    levels = [80, 80, 78, 60, 55, 50]
    plan = personalized_plan([make_session(i, [lv] * 60) for i, lv in enumerate(levels)])
    assert plan["trend"] == "declining"
    assert plan["focus_minutes"] == 25  # 30 minus 5
    assert any("shortened" in r for r in plan["reasons"])


def test_improving_trend_does_not_change_block():
    levels = [50, 52, 55, 70, 75, 80]
    plan = personalized_plan([make_session(i, [lv] * 60) for i, lv in enumerate(levels)])
    assert plan["trend"] == "improving"
    assert plan["focus_minutes"] == 30
    assert any("higher" in r for r in plan["reasons"])


def test_baseline_ok_but_no_in_session_records_keeps_general_value():
    sessions = [{"session_id": f"s{i}", "started_at": T0 + timedelta(days=i), "active_seconds": 900,
                 "signal": {"value": 70.0, "source": "digital", "confidence": 1.0, "sample_count": 10},
                 "series": []} for i in range(6)]
    plan = personalized_plan(sessions)
    assert plan["personalized"] is True
    assert plan["sample_count"] == 0
    assert plan["focus_minutes"] == 25
    assert plan["confidence"] == "low"
    assert any("Not enough sessions" in r for r in plan["reasons"])


def test_decline_onset_needs_consecutive_low_readings():
    baseline = {"q1": 60, "iqr": 10}  # floor = 55
    assert decline_onset([(1, 70), (2, 50), (3, 50), (4, 50)], baseline) == 4
    assert decline_onset([(1, 50), (2, 50), (3, 70), (4, 50), (5, 50)], baseline) is None
    assert decline_onset([], baseline) is None


def test_early_break_uses_personal_floor():
    plan = personalized_plan(steady(6))  # floor = 70, focus = 30
    early = early_break_check(12, plan, [20, 20, 20])
    assert early["take_break"] is True and early["urgency"] == "early"
    assert early_break_check(12, plan, [70, 70, 20])["urgency"] == "none"
    assert early_break_check(9, plan, [20, 20, 20])["urgency"] == "none"  # too early in the block
    assert early_break_check(12, plan, [20, 20])["urgency"] == "none"     # not enough readings


def test_scheduled_break_at_end_of_block():
    plan = personalized_plan(steady(6))
    result = early_break_check(30, plan, [70])
    assert result["take_break"] is True and result["urgency"] == "scheduled"


def test_no_break_reports_minutes_left():
    plan = personalized_plan(steady(6))
    result = early_break_check(12, plan, [70, 70, 70])
    assert result["take_break"] is False
    assert result["minutes_left"] == 18.0


def test_break_check_falls_back_without_baseline():
    plan = personalized_plan([])
    assert early_break_check(13, plan, [20, 20, 20])["urgency"] == "early"  # Phase 2 rule
    assert early_break_check(25, plan, [80])["urgency"] == "scheduled"