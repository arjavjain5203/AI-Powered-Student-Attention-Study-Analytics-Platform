import os
import importlib
import mongomock
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from jose import jwt
from pymongo.errors import ServerSelectionTimeoutError
from bson import ObjectId

from app.main import app, get_db


@pytest.fixture
def client():
    os.environ["JWT_SECRET"] = "test-secret-that-is-long-enough-for-hs256"
    db = mongomock.MongoClient(tz_aware=True).study_test
    db.users.create_index("email", unique=True)
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def register(client, email):
    response = client.post("/api/auth/register", json={"name":"Student", "email":email, "password":"password1234"})
    assert response.status_code == 201, response.text
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def test_auth_profile_and_validation(client):
    assert client.get("/api/profile").status_code in (401, 403)
    headers = register(client, "one@example.com")
    assert client.get("/api/profile", headers=headers).json()["name"] == "Student"
    assert client.patch("/api/profile", headers=headers, json={"daily_goal_minutes": 10}).status_code == 422
    assert client.patch("/api/profile", headers=headers, json={"daily_goal_minutes": 180}).json()["daily_goal_minutes"] == 180
    assert client.post("/api/auth/login", json={"email":"one@example.com", "password":"wrong"}).status_code == 401
    assert client.patch("/api/profile", headers=headers, json={"time_zone":"Not/AZone"}).status_code == 422
    assert client.patch("/api/profile", headers=headers, json={"time_zone":"Asia/Kolkata"}).json()["time_zone"] == "Asia/Kolkata"
    assert client.post("/api/auth/register", json={"name":"Again", "email":"one@example.com", "password":"password1234"}).status_code == 409
    expired = jwt.encode({"sub": client.get("/api/profile", headers=headers).json()["id"],
                          "exp": datetime.now(timezone.utc) - timedelta(seconds=1)}, os.environ["JWT_SECRET"], algorithm="HS256")
    assert client.get("/api/profile", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_owned_sessions_records_and_empty_analytics(client):
    a = register(client, "a@example.com")
    b = register(client, "b@example.com")
    assert client.get("/api/analytics", headers=a).json()["data_status"] == "empty"
    started = client.post("/api/sessions", headers=a, json={"subject":"Algebra", "topic":"Matrices", "goal_minutes":45})
    assert started.status_code == 201, started.text
    sid = started.json()["id"]
    assert client.post("/api/sessions", headers=a, json={"subject":"Another"}).status_code == 409
    assert client.get(f"/api/sessions/{sid}", headers=b).status_code == 404
    assert client.post(f"/api/sessions/{sid}/digital-records", headers=b, json={}).status_code == 404
    recorded = client.post(f"/api/sessions/{sid}/digital-records", headers=a, json={"mouse_moves":100})
    assert recorded.status_code == 201, recorded.text
    assert recorded.json()["visual_attention_score"] is None
    assert client.post(f"/api/sessions/{sid}/distractions", headers=a, json={"category":"idle"}).status_code == 201
    assert client.post(f"/api/sessions/{sid}/status/pause", headers=a).json()["status"] == "paused"
    assert client.post(f"/api/sessions/{sid}/status/pause", headers=a).status_code == 409
    assert client.post(f"/api/sessions/{sid}/status/resume", headers=a).json()["status"] == "active"
    assert client.post(f"/api/sessions/{sid}/status/end", headers=a).json()["status"] == "ended"
    report = client.get("/api/analytics?period=daily", headers=a).json()
    assert report["session_count"] == 1
    assert report["potential_distraction_count"] == 1
    assert report["average_visual_attention_score"] is None
    assert client.get("/api/focus/plan", headers=a).json()["score_source"] == "digital_engagement"
    assert client.get(f"/api/focus/plan?session_id={sid}", headers=b).status_code == 404
    assert client.get("/api/sessions/not-an-id", headers=a).status_code == 400
    assert client.post(f"/api/sessions/{sid}/digital-records", headers=a, json={"idle_seconds":-1}).status_code == 422
    assert client.post(f"/api/sessions/{sid}/distractions", headers=a, json={"category":"diagnosis"}).status_code == 422
    assert client.get("/api/analytics?period=yearly", headers=a).status_code == 422
    assert client.get(f"/api/sessions/{sid}/attention-records", headers=b).status_code == 404
    assert client.get("/api/analytics", headers=b).json()["session_count"] == 0


def test_database_failure_returns_503(client):
    app.dependency_overrides[get_db] = lambda: (_ for _ in ()).throw(ServerSelectionTimeoutError("offline"))
    response = client.post("/api/auth/login", json={"email":"one@example.com", "password":"password1234"})
    assert response.status_code == 503
    assert response.json() == {"detail":"Database unavailable"}


def test_development_lan_origin_can_preflight_login(client):
    if os.getenv("APP_ENV") != "development":
        pytest.skip("Development-only CORS rule")
    headers = {"Origin": "http://192.168.1.34:5173", "Access-Control-Request-Method": "POST",
               "Access-Control-Request-Headers": "content-type"}
    allowed = client.options("/api/auth/login", headers=headers)
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == headers["Origin"]
    rejected = client.options("/api/auth/login", headers={**headers, "Origin": "https://example.org"})
    assert rejected.status_code == 400


def test_session_time_counts_only_active_intervals(client, monkeypatch):
    headers = register(client, "timing@example.com")
    main_module = importlib.import_module("app.main")
    started_at = datetime.now(timezone.utc)
    now = [started_at]
    monkeypatch.setattr(main_module, "utcnow", lambda: now[0])

    created = client.post("/api/sessions", headers=headers, json={"subject": "Reading"})
    assert created.status_code == 201
    sid = created.json()["id"]
    now[0] = started_at + timedelta(seconds=12)
    active = client.get(f"/api/sessions/{sid}", headers=headers).json()
    assert active["active_seconds"] == 12
    assert active["estimated_focused_seconds"] is None

    paused = client.post(f"/api/sessions/{sid}/status/pause", headers=headers).json()
    assert paused["active_seconds"] == 12
    now[0] = started_at + timedelta(seconds=42)
    assert client.get(f"/api/sessions/{sid}", headers=headers).json()["active_seconds"] == 12

    client.post(f"/api/sessions/{sid}/status/resume", headers=headers)
    now[0] = started_at + timedelta(seconds=50)
    ended = client.post(f"/api/sessions/{sid}/status/end", headers=headers).json()
    assert ended["active_seconds"] == 20
    stored = client.app.dependency_overrides[get_db]().sessions.find_one({"_id": ObjectId(sid)})
    assert [round((part["started_at"] - started_at).total_seconds()) for part in stored["active_intervals"]] == [0, 42]
    assert [round((part["ended_at"] - part["started_at"]).total_seconds()) for part in stored["active_intervals"]] == [12, 8]
    now[0] = started_at + timedelta(seconds=80)
    assert client.get(f"/api/sessions/{sid}", headers=headers).json()["active_seconds"] == 20


def test_camera_gated_session_and_expired_lease(client, monkeypatch):
    headers = register(client, "camera-timer@example.com")
    main_module = importlib.import_module("app.main")
    started_at = datetime.now(timezone.utc)
    now = [started_at]
    monkeypatch.setattr(main_module, "utcnow", lambda: now[0])
    created = client.post("/api/sessions", headers=headers,
                          json={"subject": "Reading", "camera_required": True}).json()
    sid = created["id"]
    assert created["status"] == "awaiting_camera"
    assert created["active_seconds"] == 0
    assert client.post(f"/api/sessions/{sid}/activate", headers=headers).status_code == 409
    assert client.post(f"/api/sessions/{sid}/visual-consent", headers=headers).status_code == 200
    assert client.post(f"/api/sessions/{sid}/activate", headers=headers).json()["status"] == "active"
    now[0] = started_at + timedelta(seconds=12)
    assert client.get(f"/api/sessions/{sid}", headers=headers).json()["active_seconds"] == 12
    assert client.delete(f"/api/sessions/{sid}/visual-consent", headers=headers).json()["active"] is False
    assert client.get(f"/api/sessions/{sid}", headers=headers).json()["status"] == "paused"
    now[0] = started_at + timedelta(seconds=42)
    assert client.get(f"/api/sessions/{sid}", headers=headers).json()["active_seconds"] == 12
    assert client.post(f"/api/sessions/{sid}/status/resume", headers=headers).status_code == 409
    assert client.post(f"/api/sessions/{sid}/visual-consent", headers=headers).status_code == 200
    assert client.post(f"/api/sessions/{sid}/status/resume", headers=headers).json()["status"] == "active"
    now[0] = started_at + timedelta(seconds=112)
    expired = client.get(f"/api/sessions/{sid}", headers=headers).json()
    assert expired["status"] == "paused"
    assert expired["active_seconds"] == 72  # 12 seconds + 60-second consent lease
    stored = client.app.dependency_overrides[get_db]().sessions.find_one({"_id": ObjectId(sid)})
    assert [round((part["ended_at"] - part["started_at"]).total_seconds())
            for part in stored["active_intervals"]] == [12, 60]


def test_false_alarm_clip_requires_consent_and_is_admin_only(client, monkeypatch):
    a = register(client, "clip-owner@example.com")
    b = register(client, "clip-other@example.com")
    sid = client.post("/api/sessions", headers=a, json={"subject": "Algebra"}).json()["id"]
    endpoint = f"/api/sessions/{sid}/false-alarms"
    video = b"\x1a\x45\xdf\xa3" + b"sample-webm-data"
    assert client.post(endpoint, headers=b, data={"category": "face_not_visible"}).status_code == 404
    assert client.post(endpoint, headers=a, data={"category": "face_not_visible"}).status_code == 409
    db = app.dependency_overrides[get_db]()
    user_id = client.get("/api/profile", headers=a).json()["id"]
    db.visual_events.insert_one({"user_id": user_id, "session_id": sid, "category": "face_not_visible",
                                 "occurred_at": datetime.now(timezone.utc)})
    assert client.post(endpoint, headers=a, data={"category": "face_not_visible"},
                       files={"clip": ("clip.webm", video, "video/webm")}).status_code == 422
    assert client.post(endpoint, headers=a, data={"category": "face_not_visible", "share_clip": "true"},
                       files={"clip": ("clip.webm", b"not-webm", "video/webm")}).status_code == 422
    report = client.post(endpoint, headers=a, data={"category": "face_not_visible", "share_clip": "true"},
                         files={"clip": ("clip.webm", video, "video/webm")})
    assert report.status_code == 201, report.text
    rid = report.json()["id"]
    monkeypatch.setenv("REVIEW_ADMIN_TOKEN", "a-long-local-review-token-for-unit-testing")
    assert client.get("/api/admin/false-alarms").status_code == 401
    admin = {"X-Review-Token": "a-long-local-review-token-for-unit-testing"}
    assert client.get("/api/admin/false-alarms", headers=admin).json()[0]["clip_shared"] is True
    assert client.get(f"/api/admin/false-alarms/{rid}/clip", headers=admin).content == video
    assert client.delete(f"/api/sessions/{sid}/false-alarms/{rid}", headers=b).status_code == 404
    assert client.delete(f"/api/sessions/{sid}/false-alarms/{rid}", headers=a).json()["deleted"] is True
    assert client.get(f"/api/admin/false-alarms/{rid}/clip", headers=admin).status_code == 404
    metadata_only = client.post(endpoint, headers=a, data={"category": "face_not_visible"})
    assert metadata_only.status_code == 201
    assert metadata_only.json()["clip_shared"] is False
    assert client.get("/api/false-alarms/mine", headers=b).json() == []
    assert client.get("/api/false-alarms/mine", headers=a).json()[0]["clip_shared"] is False
