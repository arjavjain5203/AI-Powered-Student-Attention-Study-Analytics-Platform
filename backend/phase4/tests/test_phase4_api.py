import os
from datetime import datetime, timedelta, timezone

import mongomock
import pytest
from fastapi.testclient import TestClient

from phase4.main import app, get_db  # importing phase4.main attaches the Phase 4 routes

T0 = datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc)


@pytest.fixture
def env():
    os.environ["JWT_SECRET"] = "test-secret-that-is-long-enough-for-hs256"
    db = mongomock.MongoClient(tz_aware=True).phase4_test
    db.users.create_index("email", unique=True)
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        yield client, db
    app.dependency_overrides.clear()


def register(client, email):
    response = client.post("/api/auth/register",
                           json={"name": "Student", "email": email, "password": "password1234"})
    assert response.status_code == 201, response.text
    headers = {"Authorization": "Bearer " + response.json()["access_token"]}
    return headers, response.json()["user"]["id"]


def seed_records(db, user_id, session_id, scores, start):
    db.attention_records.insert_many([
        {"user_id": user_id, "session_id": session_id,
         "captured_at": start + timedelta(seconds=30 * (k + 1)), "digital_engagement_score": s}
        for k, s in enumerate(scores)])


def seed_ended_sessions(db, user_id, count=6, level=70, length=60):
    """Ended 30-minute sessions with full record coverage."""
    ids = []
    for i in range(count):
        start = T0 + timedelta(days=i)
        sid = db.sessions.insert_one({
            "user_id": user_id, "subject": "Math", "goal_minutes": 30, "status": "ended",
            "started_at": start, "active_seconds": 30 * length,
            "ended_at": start + timedelta(seconds=30 * length)}).inserted_id
        seed_records(db, user_id, str(sid), [level] * length, start)
        ids.append(str(sid))
    return ids


def seed_live_session(db, user_id, scores):
    start = T0 + timedelta(days=30)
    sid = db.sessions.insert_one({
        "user_id": user_id, "subject": "Physics", "goal_minutes": 30, "status": "active",
        "started_at": start, "active_since": start, "active_seconds": 0, "ended_at": None}).inserted_id
    seed_records(db, user_id, str(sid), scores, start)
    return str(sid)


def test_endpoints_require_login(env):
    client, _ = env
    assert client.get("/api/planner/personalized").status_code in (401, 403)
    assert client.get("/api/planner/break-check?session_id=abc&elapsed_minutes=5").status_code in (401, 403)


def test_new_user_gets_fallback_plan(env):
    client, _ = env
    headers, _ = register(client, "new@example.com")
    plan = client.get("/api/planner/personalized", headers=headers).json()
    assert plan["personalized"] is False
    assert plan["baseline"]["status"] == "insufficient_data"
    assert plan["focus_minutes"] == 25
    assert plan["reasons"]


def test_history_produces_personalized_plan(env):
    client, db = env
    headers, user_id = register(client, "a@example.com")
    seed_ended_sessions(db, user_id)
    plan = client.get("/api/planner/personalized", headers=headers).json()
    assert plan["personalized"] is True
    assert plan["baseline"]["status"] == "ok"
    assert plan["focus_minutes"] == 30
    assert plan["score_source"] == "digital_engagement"
    assert plan["reasons"]


def test_one_students_history_does_not_leak_to_another(env):
    client, db = env
    headers_a, id_a = register(client, "a@example.com")
    headers_b, _ = register(client, "b@example.com")
    seed_ended_sessions(db, id_a)
    assert client.get("/api/planner/personalized", headers=headers_a).json()["personalized"] is True
    assert client.get("/api/planner/personalized", headers=headers_b).json()["personalized"] is False


def test_break_check_early_break_with_personal_baseline(env):
    client, db = env
    headers, user_id = register(client, "a@example.com")
    seed_ended_sessions(db, user_id)  # baseline floor = 70
    live = seed_live_session(db, user_id, [20, 20, 20])
    result = client.get(f"/api/planner/break-check?session_id={live}&elapsed_minutes=12",
                        headers=headers).json()
    assert result["personalized"] is True
    assert result["plan_focus_minutes"] == 30
    assert result["take_break"] is True
    assert result["urgency"] == "early"


def test_break_check_falls_back_for_new_user(env):
    client, db = env
    headers, user_id = register(client, "new@example.com")
    live = seed_live_session(db, user_id, [20, 20, 20])
    result = client.get(f"/api/planner/break-check?session_id={live}&elapsed_minutes=13",
                        headers=headers).json()
    assert result["personalized"] is False
    assert result["plan_focus_minutes"] == 25
    assert result["urgency"] == "early"  # Phase 2 rule applies


def test_break_check_validation_and_ownership(env):
    client, db = env
    headers_a, id_a = register(client, "a@example.com")
    headers_b, _ = register(client, "b@example.com")
    live = seed_live_session(db, id_a, [70, 70, 70])
    url = "/api/planner/break-check"
    assert client.get(f"{url}?session_id={live}&elapsed_minutes=5", headers=headers_b).status_code == 404
    assert client.get(f"{url}?session_id=not-an-id&elapsed_minutes=5", headers=headers_a).status_code == 400
    assert client.get(f"{url}?session_id={live}&elapsed_minutes=-1", headers=headers_a).status_code == 422
    assert client.get(f"{url}?session_id={live}", headers=headers_a).status_code == 422