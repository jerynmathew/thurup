"""
Core application services and state management.
"""

from app.core.game_server import GameServer, get_game_server

__all__ = ["GameServer", "get_game_server"]
