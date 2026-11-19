from phase4.services.baseline import compare_to_baseline, compute_baseline, eligible


def summary(value, conf=1.0, active=900):
    """Minimal session summary in the shape produced by signals.session_summary."""
    return {
        "signal": {"value": value, "source": "digital", "confidence": conf, "sample_count": 10},
        "active_seconds": active,
    }


def good_sessions(values):
    return [summary(v) for v in values]


def test_baseline_ok_with_exact_numbers():
    base = compute_baseline(good_sessions([60, 65, 70, 75, 80]))
    assert base["status"] == "ok"
    assert base["median"] == 70.0
    assert base["q1"] == 65.0
    assert base["q3"] == 75.0
    assert base["iqr"] == 10.0
    assert base["sessions_used"] == 5
    assert base["rule_version"] == "baseline-v1"


def test_too_few_sessions_gives_no_numbers():
    base = compute_baseline(good_sessions([60, 65, 70, 75]))
    assert base["status"] == "insufficient_data"
    assert base["median"] is None
    assert base["q1"] is None
    assert base["q3"] is None
    assert base["iqr"] is None
    assert base["sessions_used"] == 4
    assert "4" in base["reason"] and "5" in base["reason"]


def test_empty_history_is_insufficient():
    base = compute_baseline([])
    assert base["status"] == "insufficient_data"
    assert base["sessions_used"] == 0


def test_ineligible_sessions_are_not_counted():
    sessions = good_sessions([60, 65, 70, 75, 80]) + [
        summary(None),             # no signal
        summary(90, conf=0.2),     # timer ran, few records
        summary(90, active=120),   # too short
    ]
    base = compute_baseline(sessions)
    assert base["sessions_used"] == 5
    assert base["median"] == 70.0  # the three bad sessions did not move it


def test_timer_only_sessions_cannot_create_a_baseline():
    timer_only = [summary(70, conf=0.1) for _ in range(10)]
    assert compute_baseline(timer_only)["status"] == "insufficient_data"


def test_eligibility_boundaries_are_inclusive():
    assert eligible(summary(70, conf=0.5, active=600)) is True
    assert eligible(summary(70, conf=0.49, active=600)) is False
    assert eligible(summary(70, conf=0.5, active=599)) is False


def test_outlier_does_not_drag_the_median():
    base = compute_baseline(good_sessions([70, 70, 70, 70, 70, 10]))
    assert base["status"] == "ok"
    assert base["median"] == 70.0


def test_custom_minimum_sessions():
    base = compute_baseline(good_sessions([60, 70, 80]), min_sessions=3)
    assert base["status"] == "ok"
    assert base["sessions_needed"] == 3


def test_compare_to_baseline_positions():
    base = compute_baseline(good_sessions([60, 65, 70, 75, 80]))  # q1=65, q3=75
    assert compare_to_baseline(50, base) == "below_usual"
    assert compare_to_baseline(64.9, base) == "below_usual"
    assert compare_to_baseline(65, base) == "typical"
    assert compare_to_baseline(75, base) == "typical"
    assert compare_to_baseline(75.1, base) == "above_usual"
    assert compare_to_baseline(95, base) == "above_usual"


def test_compare_returns_none_without_valid_baseline_or_value():
    ok = compute_baseline(good_sessions([60, 65, 70, 75, 80]))
    thin = compute_baseline(good_sessions([60, 65]))
    assert compare_to_baseline(70, thin) is None
    assert compare_to_baseline(None, ok) is None