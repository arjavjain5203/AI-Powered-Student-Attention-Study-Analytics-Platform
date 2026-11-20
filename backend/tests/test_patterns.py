from datetime import datetime, timedelta, timezone

from bson import ObjectId

from app.main import get_db
from app.services.patterns import summarize_patterns
from app.services.visual import ALGORITHM_VERSION
from test_api import client, register


NOW = datetime(2026, 11, 19, 12, tzinfo=timezone.utc)


def session(days_ago, subject="Math", hour=9):
    start = (NOW - timedelta(days=days_ago)).replace(hour=hour)
    end = start + timedelta(minutes=35)
    return {"_id": ObjectId(), "subject": subject, "camera_required": True,
            "status": "ended", "started_at": start, "ended_at": end,
            "active_seconds": 2100, "active_intervals": [{"started_at": start, "ended_at": end}]}


def windows(item, score, count=12):
    return [{"session_id": str(item["_id"]), "captured_at": item["started_at"] + timedelta(minutes=5, seconds=10 * i),
             "algorithm_version": ALGORITHM_VERSION, "quality": "usable", "sample_coverage": 1.0,
             "valid_samples": 20, "visual_signal_index": score} for i in range(count)]


def test_baseline_requires_distinct_sessions_days_and_usable_windows():
    old = session(20)
    middle = session(15)
    recent = session(2)
    rows = windows(old, 60) + windows(middle, 60) + windows(recent, 70)
    report = summarize_patterns([old, middle, recent], rows, now=NOW)
    assert report["baseline"]["status"] == "ready"
    assert report["baseline"]["value"] == 63.3
    assert report["baseline"]["delta"] == 10
    assert report["baseline"]["trend"] == "higher"
    assert report["visual_attention_score"] is None
    assert report["estimated_focused_seconds"] is None
    invalid = [{**row, "sample_coverage": 0.4} for row in windows(recent, 70)]
    sparse = summarize_patterns([old, middle, recent], windows(old, 60) + windows(middle, 60) + invalid, now=NOW)
    assert sparse["baseline"]["status"] == "insufficient_history"
    assert sparse["baseline"]["value"] is None


def test_midnight_split_and_legacy_sessions_do_not_invent_study_time():
    start = datetime(2026, 11, 18, 18, 20, tzinfo=timezone.utc)  # 23:50 in Kolkata
    crossing = {"_id": ObjectId(), "subject": "Physics", "camera_required": True, "status": "ended",
                "started_at": start, "active_seconds": 1800,
                "active_intervals": [{"started_at": start, "ended_at": start + timedelta(minutes=30)}]}
    legacy = {"_id": ObjectId(), "subject": "History", "camera_required": False,
              "status": "ended", "started_at": start, "active_seconds": 1200}
    report = summarize_patterns([crossing, legacy], [], now=NOW, time_zone="Asia/Kolkata")
    assert report["study_time"]["by_hour"][23]["study_seconds"] == 600
    assert report["study_time"]["by_hour"][0]["study_seconds"] == 1200
    assert report["study_time"]["by_weekday"][2]["study_seconds"] == 600
    assert report["study_time"]["by_weekday"][3]["study_seconds"] == 1200
    assert report["study_time"]["legacy_session_count"] == 1
    assert report["session_duration"]["count"] == 2


def test_repeated_signal_decline_and_higher_signal_hours_need_evidence():
    sessions = [session(day, "Math", 9) for day in (1, 2, 3)] + [
        session(day, "Physics", 15) for day in (4, 5, 6)]
    records = []
    for item in sessions:
        high = item["subject"] == "Math"
        for index in range(16):
            captured = item["started_at"] + timedelta(minutes=5 if index < 8 else 25,
                                                        seconds=(index % 8) * 10)
            records.append({"session_id": str(item["_id"]), "captured_at": captured,
                            "algorithm_version": ALGORITHM_VERSION, "quality": "usable",
                            "sample_coverage": 1.0, "valid_samples": 20,
                            "visual_signal_index": (80 if high else 60) - (10 if index >= 8 else 0)})
    report = summarize_patterns(sessions, records, now=NOW)
    assert report["visual_decline"]["status"] == "ready"
    assert report["visual_decline"]["late_minus_early"] == -10
    assert report["higher_signal_windows"][0]["start_hour"] == 6
    assert report["higher_signal_windows"][0]["day_count"] == 3
    assert {row["subject"]: row["sessions"] for row in report["subjects"]} == {"Math": 3, "Physics": 3}
    assert any(item["source"] == "provisional_visual_signal" for item in report["insights"])


def test_api_patterns_are_owned_and_empty_for_new_user(client):
    a = register(client, "pattern-owner@example.com")
    b = register(client, "pattern-other@example.com")
    empty = client.get("/api/analytics/patterns", headers=b)
    assert empty.status_code == 200
    assert empty.json()["baseline"]["value"] is None
    user_id = client.get("/api/profile", headers=a).json()["id"]
    db = client.app.dependency_overrides[get_db]()
    seeded = session(2)
    db.sessions.insert_one({**seeded, "user_id": user_id})
    own = client.get("/api/analytics/patterns", headers=a).json()
    other = client.get("/api/analytics/patterns", headers=b).json()
    assert own["session_duration"]["count"] == 1
    assert other["session_duration"]["count"] == 0
    assert other["study_time"]["day_count"] == 0
