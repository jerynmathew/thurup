"""
API v1 package - Refactored into separate modules.

Structure:
- router.py: Main router and shared state
- rest.py: REST HTTP endpoints
- websocket.py: WebSocket handler
- bot_runner.py: Bot AI automation logic
"""

from app.api.v1.router import router

__all__ = ["router"]
