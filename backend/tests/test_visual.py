from datetime import timedelta

from app.services.visual import candidate_visual_event, summarize_visual_window
from test_api import client, register


def test_visual_scoring_and_missing_quality():
    assert summarize_visual_window(20, 20, 20, 20)["visual_signal_index"] == 100
    assert summarize_visual_window(20, 20, 0, 0)["visual_signal_index"] == 0
    assert summarize_visual_window(20, 8, 8, 8)["visual_signal_index"] is None
    assert summarize_visual_window(20, 8, 8, 8)["sample_coverage"] == 0.4
    assert summarize_visual_window(20, 10, 10, 5)["visual_signal_index"] == 70
    assert candidate_visual_event(20, 2, 0, "usable") == "face_not_visible"
    assert candidate_visual_event(20, 18, 2, "usable") == "head_not_forward"
    assert candidate_visual_event(20, 0, 0, "insufficient") is None
    assert candidate_visual_event(20, 18, 17, "usable") is None


def test_visual_events_need_two_windows_and_cooldown(client):
    from datetime import datetime, timedelta, timezone
    from app.main import get_db
    a = register(client, "events@example.com")
    b = register(client, "events-other@example.com")
    sid = client.post("/api/sessions", headers=a, json={"subject": "History"}).json()["id"]
    url = f"/api/sessions/{sid}"
    client.post(f"{url}/visual-consent", headers=a)
    payload = {"algorithm_version": "face-presence-head-orientation-v1", "total_samples": 20,
               "valid_samples": 20, "face_samples": 0, "forward_samples": 0}
    assert client.post(f"{url}/visual-records", headers=a, json=payload).json()["potential_visual_event"] is None
    db = client.app.dependency_overrides[get_db]()
    db.visual_records.update_many({"session_id": sid}, {"$set": {"captured_at": datetime.now(timezone.utc) - timedelta(seconds=10)}})
    second = client.post(f"{url}/visual-records", headers=a, json=payload)
    assert second.json()["potential_visual_event"] == "face_not_visible"
    assert len(client.get(f"{url}/visual-events", headers=a).json()) == 1
    assert client.get(f"{url}/visual-events", headers=b).status_code == 404
    db.visual_records.update_many({"session_id": sid}, {"$set": {"captured_at": datetime.now(timezone.utc) - timedelta(seconds=10)}})
    assert client.post(f"{url}/visual-records", headers=a, json=payload).json()["potential_visual_event"] is None
    assert len(client.get(f"{url}/visual-events", headers=a).json()) == 1
    assert client.delete(f"{url}/visual-records", headers=a).json()["deleted_event_count"] == 1


def test_visual_consent_validation_ownership_expiry_and_deletion(client):
    a = register(client, "visual-a@example.com")
    b = register(client, "visual-b@example.com")
    sid = client.post("/api/sessions", headers=a, json={"subject": "Calculus"}).json()["id"]
    url = f"/api/sessions/{sid}"
    payload = {"algorithm_version": "face-presence-head-orientation-v1", "total_samples": 20,
               "valid_samples": 20, "face_samples": 18, "forward_samples": 12}
    assert client.post(f"{url}/visual-records", headers=a, json=payload).status_code == 409


    assert client.post(f"{url}/visual-consent", headers=b).status_code == 404
    assert client.post(f"{url}/visual-consent", headers=a).status_code == 200
    assert client.post(f"{url}/visual-records", headers=b, json=payload).status_code == 404
    assert client.post(f"{url}/visual-records", headers=a, json={**payload, "visual_attention_score": 100}).status_code == 422
    assert client.post(f"{url}/visual-records", headers=a, json={**payload, "forward_samples": 19}).status_code == 422
    result = client.post(f"{url}/visual-records", headers=a, json=payload)
    assert result.status_code == 201, result.text
    assert result.json()["visual_signal_index"] == 72
    assert result.json()["visual_attention_score"] is None
    assert client.post(f"{url}/visual-records", headers=a, json=payload).status_code == 429
    assert len(client.get(f"{url}/visual-records", headers=a).json()) == 1
    assert client.get(f"{url}/visual-records", headers=b).status_code == 404
    from app.main import get_db
    db = client.app.dependency_overrides[get_db]()
    doc = db.visual_records.find_one({"session_id": sid})
    assert timedelta(days=89) < doc["expires_at"] - doc["captured_at"] <= timedelta(days=90)
    assert client.delete(f"{url}/visual-records", headers=b).status_code == 404
    assert client.delete(f"{url}/visual-records", headers=a).json()["deleted_count"] == 1
    assert client.delete(f"{url}/visual-consent", headers=a).json()["active"] is False
    assert client.post(f"{url}/visual-records", headers=a, json=payload).status_code == 409


def test_visual_consent_lease_expires(client):
    from datetime import datetime, timezone
    from app.main import get_db
    a = register(client, "lease@example.com")
    sid = client.post("/api/sessions", headers=a, json={"subject": "Chemistry"}).json()["id"]
    url = f"/api/sessions/{sid}"
    client.post(f"{url}/visual-consent", headers=a)
    db = client.app.dependency_overrides[get_db]()
    db.sessions.update_one({"user_id": client.get("/api/profile", headers=a).json()["id"]},
                           {"$set": {"visual_consent_expires_at": datetime(2000, 1, 1, tzinfo=timezone.utc)}})
    payload = {"algorithm_version": "face-presence-head-orientation-v1", "total_samples": 20,
               "valid_samples": 20, "face_samples": 18, "forward_samples": 12}
    assert client.post(f"{url}/visual-records", headers=a, json=payload).status_code == 409
    assert client.post(f"{url}/visual-consent", headers=a).status_code == 200
    assert client.post(f"{url}/status/pause", headers=a).status_code == 200
    assert client.post(f"{url}/visual-records", headers=a, json=payload).status_code == 409
