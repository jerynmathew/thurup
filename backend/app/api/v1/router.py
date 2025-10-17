"""
Main router and shared state for API v1.

Centralizes the session store, websocket connections, and locks.
"""

import asyncio
from typing import Dict, Optional

from fastapi import APIRouter, WebSocket

from app.game.session import GameSession

# Create the main router
router = APIRouter(prefix="/api/v1")

# In-memory sessions
SESSIONS: Dict[str, GameSession] = {}

# Locks for thread-safe access to shared state
sessions_lock = asyncio.Lock()

# Track running bot tasks to prevent duplicates
bot_tasks: Dict[str, asyncio.Task] = {}  # game_id -> task


# Import and register sub-routers
from app.api.v1 import admin, history, rest, websocket  # noqa: E402, F401

# Note: The rest, websocket, history, and admin modules register their routes on the main router
# via decorators like @router.post(...) and @router.websocket(...)
