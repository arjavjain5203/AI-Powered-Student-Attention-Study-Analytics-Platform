"""Phase 4 routes. Attached to the existing app by phase4/main.py.

Dependencies are passed in (build_router) so this file never imports app.main,
which avoids a circular import and leaves the teammate's code untouched.
"""
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from phase4.services.baseline import compute_baseline
from phase4.services.focus_planner import early_break_check, personalized_plan
from phase4.services.signals import session_summary


def _summaries(db, user_id, limit=30):
    """Session summaries for this user's most recent ended sessions, oldest first."""
    sessions = list(db.sessions.find({"user_id": user_id, "status": "ended"})
                    .sort("started_at", -1).limit(limit))
    ids = [str(s["_id"]) for s in sessions]
    by_session = {}
    for r in db.attention_records.find({"user_id": user_id, "session_id": {"$in": ids}}):
        by_session.setdefault(r["session_id"], []).append(r)
    return [session_summary(s, by_session.get(str(s["_id"]), [])) for s in reversed(sessions)]


def build_router(current_user, get_db):
    router = APIRouter(prefix="/api/planner", tags=["phase4-planner"])

    @router.get("/personalized")
    def personalized(user=Depends(current_user), db=Depends(get_db)):
        summaries = _summaries(db, str(user["_id"]))
        return personalized_plan(summaries, compute_baseline(summaries))

    @router.get("/break-check")
    def break_check_route(session_id: str, elapsed_minutes: float = Query(ge=0),
                          user=Depends(current_user), db=Depends(get_db)):
        if not ObjectId.is_valid(session_id):
            raise HTTPException(400, "Invalid ID")
        user_id = str(user["_id"])
        if not db.sessions.find_one({"_id": ObjectId(session_id), "user_id": user_id}):
            raise HTTPException(404, "Session not found")
        plan = personalized_plan(_summaries(db, user_id))
        recent = [r["digital_engagement_score"] for r in db.attention_records.find(
            {"user_id": user_id, "session_id": session_id}).sort("captured_at", -1).limit(5)
            if r.get("digital_engagement_score") is not None][::-1]
        return {"plan_focus_minutes": plan["focus_minutes"], "personalized": plan["personalized"],
                **early_break_check(elapsed_minutes, plan, recent)}

    return router