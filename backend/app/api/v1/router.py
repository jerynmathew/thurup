"""
Main router for API v1.

All global state has been migrated to GameServer (see app/core/game_server.py).
"""

from fastapi import APIRouter

# Create the main router
router = APIRouter(prefix="/api/v1")


# Import and register sub-routers
from app.api.v1 import admin, history, rest, websocket  # noqa: E402, F401

# Note: The rest, websocket, history, and admin modules register their routes on the main router
# via decorators like @router.post(...) and @router.websocket(...)
