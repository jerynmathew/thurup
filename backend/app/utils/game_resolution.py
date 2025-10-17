"""
Game identifier resolution utility.

Provides unified logic for resolving game identifiers (UUID or short code)
to game UUIDs across REST and WebSocket endpoints.
"""

from typing import Dict, Optional

from fastapi import HTTPException

from app.constants import ErrorMessage
from app.db.config import get_db
from app.db.repository import GameRepository
from app.game.session import GameSession


async def resolve_game_identifier(
    identifier: str,
    sessions: Dict[str, GameSession],
    raise_on_not_found: bool = False
) -> Optional[str]:
    """
    Resolve game identifier (UUID or short code) to game UUID.

    This function provides a unified way to resolve game identifiers across
    the application. It checks in-memory sessions first, then falls back to
    database lookups.

    Resolution order:
    1. Check in-memory sessions by UUID key
    2. Check in-memory sessions by short_code attribute
    3. Check database by UUID
    4. Check database by short_code

    Args:
        identifier: Either a game UUID or short code (e.g., "royal-turtle-65")
        sessions: Dictionary of active game sessions
        raise_on_not_found: If True, raises HTTPException when not found;
                          if False, returns the original identifier

    Returns:
        Game UUID if found, None or original identifier otherwise

    Raises:
        HTTPException: If raise_on_not_found=True and game not found (404)

    Examples:
        >>> # For REST endpoints (raises on not found)
        >>> game_id = await resolve_game_identifier(
        ...     "royal-turtle-65", SESSIONS, raise_on_not_found=True
        ... )

        >>> # For WebSocket endpoints (returns identifier for compatibility)
        >>> game_id = await resolve_game_identifier(
        ...     "royal-turtle-65", SESSIONS, raise_on_not_found=False
        ... )
    """
    # Check in-memory sessions by UUID key
    if identifier in sessions:
        return identifier

    # Check in-memory sessions by short_code attribute
    for game_id, session in sessions.items():
        if session.short_code == identifier:
            return game_id

    # Check database
    async for db in get_db():
        repo = GameRepository(db)

        # Try UUID lookup
        game = await repo.get_game(identifier)
        if game:
            return game.id

        # Try short code lookup
        game = await repo.get_game_by_short_code(identifier)
        if game:
            return game.id

        break  # Exit after one iteration

    # Handle not found case
    if raise_on_not_found:
        raise HTTPException(status_code=404, detail=ErrorMessage.GAME_NOT_FOUND)

    # For WebSocket compatibility, return original identifier
    return identifier
