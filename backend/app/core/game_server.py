"""
GameServer - Centralized state management for game sessions.

Encapsulates previously global state (SESSIONS, bot_tasks) and provides
dependency injection for better testing and lifecycle management.
"""

import asyncio
from typing import Dict, Optional

from app.game.session import GameSession
from app.logging_config import get_logger

logger = get_logger(__name__)


class GameServer:
    """
    Centralized game server managing all active sessions and bot tasks.

    This class encapsulates what were previously global dictionaries:
    - SESSIONS: Active game sessions by game_id
    - bot_tasks: Running bot tasks by game_id
    - sessions_lock: Lock for thread-safe access

    Usage:
        server = GameServer()
        async with server.lock():
            session = server.get_session(game_id)
    """

    def __init__(self):
        """Initialize empty game server state."""
        self._sessions: Dict[str, GameSession] = {}
        self._bot_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        logger.info("game_server_initialized")

    # Session management

    def get_session(self, game_id: str) -> Optional[GameSession]:
        """Get a session by game_id. Returns None if not found."""
        return self._sessions.get(game_id)

    def add_session(self, game_id: str, session: GameSession) -> None:
        """Add a new session to the server."""
        self._sessions[game_id] = session
        logger.info("session_added", game_id=game_id, total_sessions=len(self._sessions))

    def remove_session(self, game_id: str) -> Optional[GameSession]:
        """Remove and return a session. Returns None if not found."""
        session = self._sessions.pop(game_id, None)
        if session:
            logger.info("session_removed", game_id=game_id, total_sessions=len(self._sessions))
        return session

    def has_session(self, game_id: str) -> bool:
        """Check if a session exists."""
        return game_id in self._sessions

    def get_all_sessions(self) -> Dict[str, GameSession]:
        """Get all active sessions (returns reference, use with lock!)."""
        return self._sessions

    def session_count(self) -> int:
        """Get the number of active sessions."""
        return len(self._sessions)

    # Bot task management

    def get_bot_task(self, game_id: str) -> Optional[asyncio.Task]:
        """Get a bot task by game_id. Returns None if not found."""
        return self._bot_tasks.get(game_id)

    def add_bot_task(self, game_id: str, task: asyncio.Task) -> None:
        """Add a bot task for a game."""
        self._bot_tasks[game_id] = task
        logger.debug("bot_task_added", game_id=game_id)

    def remove_bot_task(self, game_id: str) -> Optional[asyncio.Task]:
        """Remove and return a bot task. Returns None if not found."""
        task = self._bot_tasks.pop(game_id, None)
        if task:
            logger.debug("bot_task_removed", game_id=game_id)
        return task

    def has_bot_task(self, game_id: str) -> bool:
        """Check if a bot task exists."""
        return game_id in self._bot_tasks

    def get_all_bot_tasks(self) -> Dict[str, asyncio.Task]:
        """Get all bot tasks (returns reference, use with lock!)."""
        return self._bot_tasks

    def bot_task_count(self) -> int:
        """Get the number of running bot tasks."""
        return len(self._bot_tasks)

    # Lock management

    def lock(self) -> asyncio.Lock:
        """
        Get the server lock for thread-safe operations.

        Usage:
            async with server.lock():
                session = server.get_session(game_id)
                # ... modify session ...
        """
        return self._lock

    # Lifecycle management

    async def shutdown(self) -> None:
        """
        Shutdown the game server, canceling all bot tasks.

        Should be called during application shutdown.
        """
        logger.info("game_server_shutting_down",
                   sessions=len(self._sessions),
                   bot_tasks=len(self._bot_tasks))

        # Cancel all bot tasks
        for game_id, task in list(self._bot_tasks.items()):
            if not task.done():
                task.cancel()
                logger.debug("bot_task_cancelled", game_id=game_id)

        # Wait for tasks to complete cancellation
        if self._bot_tasks:
            await asyncio.gather(*self._bot_tasks.values(), return_exceptions=True)

        self._bot_tasks.clear()
        logger.info("game_server_shutdown_complete")


# Global instance (singleton pattern)
_game_server: Optional[GameServer] = None


def get_game_server() -> GameServer:
    """
    Get the global GameServer instance.

    This is a dependency injection function for FastAPI.

    Usage in endpoints:
        @router.get("/endpoint")
        async def endpoint(server: GameServer = Depends(get_game_server)):
            async with server.lock():
                session = server.get_session(game_id)
    """
    global _game_server
    if _game_server is None:
        _game_server = GameServer()
    return _game_server


def init_game_server() -> GameServer:
    """
    Initialize the global GameServer instance.

    Called during application startup in main.py.
    """
    global _game_server
    _game_server = GameServer()
    logger.info("global_game_server_initialized")
    return _game_server


async def shutdown_game_server() -> None:
    """
    Shutdown the global GameServer instance.

    Called during application shutdown in main.py.
    """
    global _game_server
    if _game_server is not None:
        await _game_server.shutdown()
        _game_server = None
