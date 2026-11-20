"""Opt-in integration test against a real local MongoDB server.

Set RUN_REAL_MONGO_TESTS=1. Uses and drops only a uniquely named test database.
"""
import os
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from bson import ObjectId
from pymongo import MongoClient

from app.main import app, get_client, get_db


@pytest.mark.skipif(os.getenv("RUN_REAL_MONGO_TESTS") != "1", reason="Set RUN_REAL_MONGO_TESTS=1 for real MongoDB")
def test_real_mongo_api_roundtrip(monkeypatch):
    name = f"study_attention_test_{uuid4().hex[:12]}"
    monkeypatch.setenv("MONGO_DB", name)
    uri = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/?directConnection=true")
    client = MongoClient(uri, serverSelectionTimeoutMS=3000, tz_aware=True)
    client.admin.command("ping")
    get_db.cache_clear()
    get_client.cache_clear()
    try:
        with TestClient(app) as http:
            assert http.get("/api/health/db").json() == {"status": "ok", "database": name}
            body = {"name": "Integration Student", "email": "integration@example.com", "password": "test-password-123"}
            registered = http.post("/api/auth/register", json=body)
            assert registered.status_code == 201, registered.text
            assert http.post("/api/auth/register", json=body).status_code == 409
            assert client[name].users.index_information()["email_1"]["unique"]
            token = registered.json()["access_token"]
            auth = {"Authorization": f"Bearer {token}"}
            assert http.post("/api/auth/login", json={"email": body["email"], "password": body["password"]}).status_code == 200
            created = http.post("/api/sessions", headers=auth, json={"subject": "Physics", "goal_minutes": 45})
            assert created.status_code == 201, created.text
            sid = created.json()["id"]
            assert http.post("/api/sessions", headers=auth, json={"subject":"Second"}).status_code == 409
            snapshot = http.post(f"/api/sessions/{sid}/digital-records", headers=auth, json={"mouse_moves": 10, "tab_visible": True})
            assert snapshot.status_code == 201, snapshot.text
            assert snapshot.json()["visual_attention_score"] is None
            with ThreadPoolExecutor(max_workers=2) as pool:
                statuses = list(pool.map(lambda _: http.post(f"/api/sessions/{sid}/status/pause", headers=auth).status_code, range(2)))
            assert sorted(statuses) == [200, 409]
            assert http.post(f"/api/sessions/{sid}/status/resume", headers=auth).status_code == 200
            assert http.post(f"/api/sessions/{sid}/visual-consent", headers=auth).status_code == 200
            visual = http.post(f"/api/sessions/{sid}/visual-records", headers=auth, json={
                "algorithm_version": "face-presence-head-orientation-v1", "total_samples": 20,
                "valid_samples": 20, "face_samples": 18, "forward_samples": 12})
            assert visual.status_code == 201, visual.text
            assert visual.json()["visual_signal_index"] == 72
            assert client[name].visual_records.index_information()["expires_at_1"]["expireAfterSeconds"] == 0
            assert client[name].visual_events.index_information()["expires_at_1"]["expireAfterSeconds"] == 0
            assert client[name].false_alarm_reports.index_information()["expires_at_1"]["expireAfterSeconds"] == 0
            assert client[name].visual_records.count_documents({"session_id": sid}) == 1
            stored = client[name].visual_records.find_one({"session_id": sid})
            assert stored["sample_coverage"] == 1.0
            assert not set(stored).intersection({"frame", "image", "video", "landmarks", "raw_webcam"})
            assert http.delete(f"/api/sessions/{sid}/visual-records", headers=auth).json()["deleted_count"] == 1
            assert http.post(f"/api/sessions/{sid}/status/end", headers=auth).status_code == 200
            stored_session = client[name].sessions.find_one({"_id": ObjectId(sid)})
            assert len(stored_session["active_intervals"]) == 2
            assert http.get("/api/analytics?period=daily", headers=auth).json()["session_count"] == 1
            patterns = http.get("/api/analytics/patterns", headers=auth)
            assert patterns.status_code == 200
            assert patterns.json()["baseline"]["status"] == "insufficient_history"
            assert patterns.json()["visual_attention_score"] is None
            assert http.get("/api/focus/plan", headers=auth).json()["score_source"] == "digital_engagement"
            assert client[name].sessions.count_documents({}) == 1
    finally:
        client.drop_database(name)
        client.close()
        get_db.cache_clear()
        get_client.cache_clear()
