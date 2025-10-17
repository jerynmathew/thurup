"""
Persistence integration for API v1.

Handles automatic saving/loading of game sessions to/from database.
"""

from typing import Optional


from app.api.v1.router import SESSIONS, sessions_lock
from app.db.config import AsyncSessionLocal
from app.db.persistence import SessionPersistence
from app.game.session import GameSession
from app.logging_config import get_logger

logger = get_logger(__name__)


async def save_game_state(game_id: str, reason: str = "auto"):
    """
    Save game state to database.

    Args:
        game_id: Game ID to save
        reason: Reason for snapshot (e.g., "bid", "trump", "play", "auto")
    """
    sess = SESSIONS.get(game_id)
    if not sess:
        logger.warning("save_game_state_no_session", game_id=game_id)
        return False

    try:
        async with AsyncSessionLocal() as db:
            persistence = SessionPersistence(db)
            success = await persistence.save_session(sess, snapshot_reason=reason)
            if success:
                logger.debug("game_state_saved", game_id=game_id, reason=reason)
            return success
    except Exception as e:
        logger.error("save_game_state_failed", game_id=game_id, error=str(e))
        return False


async def load_game_from_db(game_id: str) -> Optional[GameSession]:
    """
    Load game session from database.

    Args:
        game_id: Game ID to load

    Returns:
        GameSession if found, None otherwise
    """
    try:
        async with AsyncSessionLocal() as db:
            persistence = SessionPersistence(db)
            sess = await persistence.load_session(game_id)
            if sess:
                logger.info("game_loaded_from_db", game_id=game_id)
            return sess
    except Exception as e:
        logger.error("load_game_failed", game_id=game_id, error=str(e))
        return None


async def restore_active_games():
    """
    Restore all active games from database on server startup.

    Loads games that are not in terminal states (completed, abandoned).
    """
    try:
        async with AsyncSessionLocal() as db:
            from app.db.repository import GameRepository

            repo = GameRepository(db)
            active_games = await repo.get_active_games()

            restored_count = 0
            async with sessions_lock:
                for game_model in active_games:
                    sess = await load_game_from_db(game_model.id)
                    if sess:
                        SESSIONS[game_model.id] = sess
                        restored_count += 1

            logger.info("active_games_restored", count=restored_count)
            return restored_count
    except Exception as e:
        logger.error("restore_active_games_failed", error=str(e))
        return 0


async def delete_game_from_db(game_id: str) -> bool:
    """
    Delete game from database.

    Args:
        game_id: Game ID to delete

    Returns:
        True if deleted, False otherwise
    """
    try:
        async with AsyncSessionLocal() as db:
            persistence = SessionPersistence(db)
            success = await persistence.delete_session(game_id)
            if success:
                logger.info("game_deleted_from_db", game_id=game_id)
            return success
    except Exception as e:
        logger.error("delete_game_failed", game_id=game_id, error=str(e))
        return False
