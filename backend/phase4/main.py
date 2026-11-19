"""Phase 4 entry point: the existing app plus the Phase 4 routes.

Run with:  uvicorn phase4.main:app --reload
app/main.py is not modified. Switching over later is one include_router line there.
"""
from app.main import app, current_user, get_db
from phase4.routes import build_router

app.include_router(build_router(current_user, get_db))