"""Idempotently seed four LOCAL presentation logins; never target a hosted database."""
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.uri_parser import parse_uri

backend = Path(__file__).resolve().parents[1]
load_dotenv(backend / ".env")
uri = os.getenv("MONGO_URI", "")
if not uri.startswith("mongodb://") or not all(host in {"127.0.0.1", "localhost"} for host, _port in parse_uri(uri)["nodelist"]):
    raise SystemExit("Refusing to seed a non-local MongoDB URI")

db = MongoClient(uri, serverSelectionTimeoutMS=3000, tz_aware=True)[os.getenv("MONGO_DB", "study_attention")]
db.command("ping")
db.users.create_index("email", unique=True)
password = os.getenv("PRESENTATION_PASSWORD", "StudyDemo123!")
if len(password) < 10:
    raise SystemExit("PRESENTATION_PASSWORD must be at least 10 characters")
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
now = datetime.now(timezone.utc)

students = [
    ("maya.student@example.com", "Maya Sharma", 180, 35,
     [("Mathematics", "Linear algebra", 38, 1), ("Physics", "Waves", 52, 3), ("Mathematics", "Vectors", 27, 5)]),
    ("arjun.student@example.com", "Arjun Mehta", 240, 50,
     [("Computer Science", "Data structures", 61, 1), ("Programming", "Python practice", 44, 2), ("Statistics", "Probability", 36, 4)]),
    ("zoya.student@example.com", "Zoya Khan", 150, 25,
     [("Biology", "Cell division", 31, 1), ("Chemistry", "Organic reactions", 42, 3), ("Biology", "Genetics", 29, 6)]),
]

test_user = db.users.find_one({"email": "test@gmail.com"})
if test_user:
    db.users.update_one({"_id": test_user["_id"]}, {"$set": {"password_hash": password_hash}})
    db.sessions.update_many({"user_id": str(test_user["_id"]), "status": "active",
                             "camera_required": {"$ne": True}},
                            {"$set": {"status": "paused", "active_since": None,
                                      "camera_required": True, "legacy_unmonitored": True,
                                      "visual_consent_active": False, "visual_consent_expires_at": None}})
else:
    db.users.insert_one({"name": "Test Student", "email": "test@gmail.com", "password_hash": password_hash,
                         "daily_goal_minutes": 240, "preferred_session_minutes": 45,
                         "notifications_enabled": True, "time_zone": "Asia/Kolkata",
                         "presentation_account": False, "created_at": now})

for email, name, goal, preferred, history in students:
    user = db.users.find_one({"email": email})
    old_email = email.replace(".student@example.com", "@example.test")
    if not user:
        old_user = db.users.find_one({"email": old_email, "presentation_account": True})
        if old_user:
            db.users.update_one({"_id": old_user["_id"]}, {"$set": {"email": email}})
            user = db.users.find_one({"_id": old_user["_id"]})
    if not user:
        user_id = db.users.insert_one({"name": name, "email": email, "password_hash": password_hash,
                                       "daily_goal_minutes": goal, "preferred_session_minutes": preferred,
                                       "notifications_enabled": True, "time_zone": "Asia/Kolkata",
                                       "presentation_account": True, "created_at": now}).inserted_id
    else:
        user_id = user["_id"]
        db.users.update_one({"_id": user_id}, {"$set": {"password_hash": password_hash,
                                                         "presentation_account": True}})
    if not db.sessions.count_documents({"user_id": str(user_id), "presentation_seed": True}):
        for subject, topic, minutes, days_ago in history:
            started = now - timedelta(days=days_ago, minutes=minutes)
            db.sessions.insert_one({"user_id": str(user_id), "subject": subject, "topic": topic,
                                    "goal_minutes": max(25, minutes), "camera_required": False,
                                    "status": "ended", "started_at": started, "active_since": None,
                                    "active_seconds": minutes * 60, "ended_at": started + timedelta(minutes=minutes),
                                    "presentation_seed": True})

print("Local presentation accounts ready: test@gmail.com, maya.student@example.com, arjun.student@example.com, zoya.student@example.com")
print("Development-only password:", password)
