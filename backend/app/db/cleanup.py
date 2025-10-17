"""
Background task for cleaning up old game sessions.

Periodically removes abandoned/stale games from the database.
"""

import asyncio
from typing import Optional


from app.constants import GameConfig
from app.db.config import AsyncSessionLocal
from app.db.repository import GameRepository
from app.logging_config import get_logger

logger = get_logger(__name__)


class GameCleanupTask:
    """Background task that periodically cleans up old games."""

    def __init__(
        self,
        interval_minutes: int = 30,
        lobby_hours: int = GameConfig.LOBBY_TIMEOUT_HOURS,
        active_hours: int = GameConfig.ACTIVE_GAME_TIMEOUT_HOURS,
        completed_hours: int = GameConfig.COMPLETED_GAME_RETENTION_HOURS,
    ):
        """
        Initialize cleanup task.

        Args:
            interval_minutes: How often to run cleanup (default: 30 minutes)
            lobby_hours: Delete lobby games older than this (default: 1 hour)
            active_hours: Delete active games with no activity (default: 2 hours)
            completed_hours: Delete completed games (default: 24 hours)
        """
        self.interval_minutes = interval_minutes
        self.lobby_hours = lobby_hours
        self.active_hours = active_hours
        self.completed_hours = completed_hours
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start the cleanup task."""
        if self._running:
            logger.warning("cleanup_task_already_running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            "cleanup_task_started",
            interval_minutes=self.interval_minutes,
            lobby_hours=self.lobby_hours,
            active_hours=self.active_hours,
            completed_hours=self.completed_hours,
        )

    async def stop(self):
        """Stop the cleanup task."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("cleanup_task_stopped")

    async def _run_loop(self):
        """Main cleanup loop."""
        while self._running:
            try:
                await self._run_cleanup()
            except Exception as e:
                logger.error("cleanup_task_error", error=str(e))

            # Wait for next interval
            await asyncio.sleep(self.interval_minutes * 60)

    async def _run_cleanup(self):
        """Run a single cleanup cycle."""
        async with AsyncSessionLocal() as session:
            try:
                repo = GameRepository(session)
                deleted = await repo.cleanup_old_games(
                    lobby_hours=self.lobby_hours,
                    active_hours=self.active_hours,
                    completed_hours=self.completed_hours,
                )
                await session.commit()

                if deleted > 0:
                    logger.info("cleanup_completed", games_deleted=deleted)
                else:
                    logger.debug("cleanup_completed_no_deletions")

            except Exception as e:
                await session.rollback()
                logger.error("cleanup_failed", error=str(e))
                raise


# Global instance
_cleanup_task: Optional[GameCleanupTask] = None


async def start_cleanup_task():
    """Start the global cleanup task."""
    global _cleanup_task
    if _cleanup_task is None:
        _cleanup_task = GameCleanupTask()
    await _cleanup_task.start()


async def stop_cleanup_task():
    """Stop the global cleanup task."""
    global _cleanup_task
    if _cleanup_task:
        await _cleanup_task.stop()
