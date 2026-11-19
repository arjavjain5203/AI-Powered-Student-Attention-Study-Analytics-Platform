from datetime import datetime, timedelta, timezone

from phase4.services.signals import (
    digital_session_signal,
    make_signal,
    session_series,
    session_summary,
    visual_session_signal,
)

T0 = datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc)


def digital(score):
    return {"digital_engagement_score": score}


def test_make_signal_shape_and_clamping():
    sig = make_signal(70, "digital", 1.7, 3)
    assert sig == {"value": 70.0, "source": "digital", "confidence": 1.0, "sample_count": 3}
    assert make_signal(None, "digital", -2, 0)["value"] is None
    assert make_signal(None, "digital", -2, 0)["confidence"] == 0.0


def test_missing_data_is_none_not_zero():
    assert digital_session_signal(600, [])["value"] is None
    assert digital_session_signal(600, None)["value"] is None
    assert digital_session_signal(600, [digital(None)])["value"] is None


def test_invalid_numbers_are_ignored():
    records = [digital(float("nan")), digital(True), digital("80")]
    assert digital_session_signal(600, records)["value"] is None


def test_full_coverage_gives_full_confidence():
    # 300 s of activity at one record per 30 s = 10 expected records
    sig = digital_session_signal(300, [digital(70)] * 10)
    assert sig["value"] == 70.0
    assert sig["confidence"] == 1.0
    assert sig["sample_count"] == 10
    assert sig["source"] == "digital"


def test_low_coverage_gives_low_confidence():
    # timer ran for 20 minutes but only 4 records arrived
    sig = digital_session_signal(1200, [digital(70)] * 4)
    assert sig["confidence"] == 0.1


def test_confidence_never_exceeds_one():
    assert digital_session_signal(60, [digital(70)] * 100)["confidence"] == 1.0


def test_visual_signal_is_labeled_provisional():
    sig = visual_session_signal(100, [{"quality": "usable", "visual_signal_index": 80}])
    assert sig["source"] == "visual_provisional"
    assert sig["value"] == 80.0
    assert sig["confidence"] == 0.1  # 1 usable window of 10 expected


def test_visual_ignores_insufficient_windows():
    records = [
        {"quality": "usable", "visual_signal_index": 80},
        {"quality": "usable", "visual_signal_index": 60},
        {"quality": "insufficient", "visual_signal_index": None},
    ]
    sig = visual_session_signal(100, records)
    assert sig["value"] == 70.0
    assert sig["sample_count"] == 2


def test_visual_with_no_usable_windows_is_none():
    sig = visual_session_signal(100, [{"quality": "insufficient", "visual_signal_index": None}])
    assert sig["value"] is None
    assert sig["source"] == "visual_provisional"


def test_session_series_is_ordered_and_skips_bad_rows():
    session = {"started_at": T0}
    records = [
        {"captured_at": T0 + timedelta(seconds=120), "digital_engagement_score": 60},
        {"captured_at": T0 + timedelta(seconds=60), "digital_engagement_score": 50},
        {"captured_at": T0 + timedelta(seconds=90), "digital_engagement_score": None},
        {"digital_engagement_score": 40},  # no timestamp
    ]
    assert session_series(session, records) == [(1.0, 50.0), (2.0, 60.0)]


def test_session_summary_shape():
    session = {"_id": "abc", "started_at": T0, "active_seconds": 60}
    records = [
        {"captured_at": T0 + timedelta(seconds=30), "digital_engagement_score": 70},
        {"captured_at": T0 + timedelta(seconds=60), "digital_engagement_score": 80},
    ]
    summary = session_summary(session, records)
    assert summary["session_id"] == "abc"
    assert summary["active_seconds"] == 60
    assert summary["signal"]["value"] == 75.0
    assert len(summary["series"]) == 2