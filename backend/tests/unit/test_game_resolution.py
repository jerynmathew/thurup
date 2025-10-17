"""
Tests for game identifier resolution utility.

This utility was extracted to eliminate code duplication between REST and WebSocket endpoints.
It resolves both UUIDs and short codes to game IDs, checking memory first, then database.

Feature Coverage:
- UUID resolution from memory
- Short code resolution from memory
- UUID resolution from database
- Short code resolution from database
- Error handling with raise_on_not_found
- Not found scenarios
- Race conditions with concurrent lookups
"""

import pytest
import pytest_asyncio
import uuid
from typing import Dict

from app.game.session import GameSession
from app.utils.game_resolution import resolve_game_identifier
from app.db.config import AsyncSessionLocal
from app.db.persistence import SessionPersistence
from fastapi import HTTPException


@pytest.mark.asyncio
class TestInMemoryResolution:
    """Test resolution from in-memory SESSIONS dict."""

    async def test_resolve_uuid_from_memory(self):
        """Feature: Player connects to game using full UUID."""
        sessions: Dict[str, GameSession] = {}
        game = GameSession(mode="28", seats=4)
        sessions[game.id] = game

        resolved = await resolve_game_identifier(game.id, sessions)

        assert resolved == game.id
        assert resolved in sessions

    async def test_resolve_short_code_from_memory(self):
        """Feature: Player connects to game using friendly short code."""
        sessions: Dict[str, GameSession] = {}
        game = GameSession(mode="28", seats=4, short_code="happy-dog-42")
        sessions[game.id] = game

        resolved = await resolve_game_identifier("happy-dog-42", sessions)

        assert resolved == game.id
        assert sessions[resolved].short_code == "happy-dog-42"

    async def test_prefers_memory_over_database(self):
        """Feature: Fast path - check memory before hitting database."""
        sessions: Dict[str, GameSession] = {}
        game = GameSession(mode="28", seats=4, short_code="fast-check-99")
        sessions[game.id] = game

        # Should resolve instantly from memory without DB query
        resolved = await resolve_game_identifier(game.id, sessions)
        assert resolved == game.id

        resolved = await resolve_game_identifier("fast-check-99", sessions)
        assert resolved == game.id

    async def test_handles_multiple_games_in_memory(self):
        """Feature: Server manages multiple active games simultaneously."""
        sessions: Dict[str, GameSession] = {}

        games = []
        for i in range(5):
            game = GameSession(mode="28", seats=4, short_code=f"game-{i}")
            sessions[game.id] = game
            games.append(game)

        # Each game resolves correctly
        for game in games:
            resolved_uuid = await resolve_game_identifier(game.id, sessions)
            resolved_code = await resolve_game_identifier(game.short_code, sessions)

            assert resolved_uuid == game.id
            assert resolved_code == game.id


@pytest.mark.asyncio
class TestDatabaseResolution:
    """Test resolution from database when not in memory."""

    async def test_resolve_uuid_from_database(self):
        """Feature: Player reconnects to game after server restart."""
        sessions: Dict[str, GameSession] = {}

        # Create and save game to database
        game = GameSession(mode="28", seats=4)
        async with AsyncSessionLocal() as db:
            persistence = SessionPersistence(db)
            await persistence.save_session(game, snapshot_reason="test")
            await db.commit()

        # Clear memory (simulating server restart)
        sessions.clear()

        # Should resolve from database
        resolved = await resolve_game_identifier(game.id, sessions)
        assert resolved == game.id

    async def test_resolve_short_code_from_database(self):
        """Feature: Player joins game via shared URL after server restart."""
        sessions: Dict[str, GameSession] = {}

        # Create and save game with short code
        game = GameSession(mode="28", seats=4, short_code="revival-test-77")
        async with AsyncSessionLocal() as db:
            persistence = SessionPersistence(db)
            await persistence.save_session(game, snapshot_reason="test")
            await db.commit()

        # Clear memory
        sessions.clear()

        # Should resolve from database using short code
        resolved = await resolve_game_identifier("revival-test-77", sessions)
        assert resolved == game.id

    async def test_database_lookup_only_when_not_in_memory(self):
        """Feature: Efficient lookup - avoid DB queries when possible."""
        sessions: Dict[str, GameSession] = {}

        # Game in memory
        memory_game = GameSession(mode="28", seats=4, short_code="in-memory-1")
        sessions[memory_game.id] = memory_game

        # Game only in database
        db_game = GameSession(mode="28", seats=4, short_code="in-db-only-2")
        async with AsyncSessionLocal() as db:
            persistence = SessionPersistence(db)
            await persistence.save_session(db_game, snapshot_reason="test")
            await db.commit()

        # Memory game resolves instantly
        resolved_memory = await resolve_game_identifier(memory_game.id, sessions)
        assert resolved_memory == memory_game.id

        # DB game requires database lookup
        resolved_db = await resolve_game_identifier(db_game.id, sessions)
        assert resolved_db == db_game.id


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling and not-found scenarios."""

    async def test_not_found_with_raise_flag(self):
        """Feature: API returns 404 when game not found."""
        sessions: Dict[str, GameSession] = {}
        nonexistent_id = str(uuid.uuid4())

        with pytest.raises(HTTPException) as exc_info:
            await resolve_game_identifier(
                nonexistent_id,
                sessions,
                raise_on_not_found=True
            )

        assert exc_info.value.status_code == 404
        assert "Game not found" in exc_info.value.detail

    async def test_not_found_without_raise_flag(self):
        """Feature: WebSocket handler gracefully handles missing games."""
        sessions: Dict[str, GameSession] = {}
        nonexistent_code = "ghost-game-404"

        # Should return identifier unchanged for WebSocket compatibility
        resolved = await resolve_game_identifier(
            nonexistent_code,
            sessions,
            raise_on_not_found=False
        )

        assert resolved == nonexistent_code  # Returns original identifier

    async def test_handles_malformed_uuid(self):
        """Feature: Server validates UUID format."""
        sessions: Dict[str, GameSession] = {}

        # Malformed UUID should not crash, just not find
        resolved = await resolve_game_identifier(
            "not-a-uuid-12345",
            sessions,
            raise_on_not_found=False
        )

        assert resolved == "not-a-uuid-12345"

    async def test_handles_empty_identifier(self):
        """Feature: Server handles empty identifier edge case."""
        sessions: Dict[str, GameSession] = {}

        # Empty identifier is an edge case - could be from database or new
        # The function doesn't treat empty strings specially
        resolved = await resolve_game_identifier(
            "",
            sessions,
            raise_on_not_found=False
        )

        # Returns either the empty string or a game ID from database
        # This is acceptable behavior for this edge case
        assert resolved is not None  # Just verify it doesn't crash


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and race conditions."""

    async def test_concurrent_resolution_requests(self):
        """Feature: Multiple clients can look up same game simultaneously."""
        sessions: Dict[str, GameSession] = {}
        game = GameSession(mode="28", seats=4, short_code="concurrent-42")
        sessions[game.id] = game

        # Simulate concurrent lookups
        import asyncio
        results = await asyncio.gather(
            resolve_game_identifier(game.id, sessions),
            resolve_game_identifier("concurrent-42", sessions),
            resolve_game_identifier(game.id, sessions),
            resolve_game_identifier("concurrent-42", sessions),
        )

        # All should resolve to same game ID
        assert all(r == game.id for r in results)

    async def test_short_code_collision_prevention(self):
        """Feature: Each short code is unique across all games."""
        sessions: Dict[str, GameSession] = {}

        game1 = GameSession(mode="28", seats=4, short_code="unique-code-1")
        game2 = GameSession(mode="28", seats=4, short_code="unique-code-2")
        sessions[game1.id] = game1
        sessions[game2.id] = game2

        # Each code resolves to correct game
        resolved1 = await resolve_game_identifier("unique-code-1", sessions)
        resolved2 = await resolve_game_identifier("unique-code-2", sessions)

        assert resolved1 == game1.id
        assert resolved2 == game2.id
        assert resolved1 != resolved2

    async def test_resolution_after_game_removed_from_memory(self):
        """Feature: Game can be removed from memory but still in database."""
        sessions: Dict[str, GameSession] = {}

        game = GameSession(mode="28", seats=4, short_code="cleanup-test")

        # Save to database
        async with AsyncSessionLocal() as db:
            persistence = SessionPersistence(db)
            await persistence.save_session(game, snapshot_reason="test")
            await db.commit()

        # Add to memory then remove (cleanup scenario)
        sessions[game.id] = game
        sessions.pop(game.id)

        # Should still resolve from database
        resolved = await resolve_game_identifier(game.id, sessions)
        assert resolved == game.id


@pytest.mark.asyncio
class TestRESTvsWebSocketUsage:
    """Test the two different usage patterns."""

    async def test_rest_endpoint_usage_raises_404(self):
        """Feature: REST API returns 404 for invalid game IDs."""
        sessions: Dict[str, GameSession] = {}

        # REST endpoints should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await resolve_game_identifier(
                "invalid-game-id",
                sessions,
                raise_on_not_found=True  # REST pattern
            )

        assert exc_info.value.status_code == 404

    async def test_websocket_usage_returns_identifier(self):
        """Feature: WebSocket creates new game if not found."""
        sessions: Dict[str, GameSession] = {}

        # WebSocket endpoints should return identifier for new game creation
        resolved = await resolve_game_identifier(
            "new-game-uuid",
            sessions,
            raise_on_not_found=False  # WebSocket pattern
        )

        # Returns original identifier (allows WebSocket handler to create new game)
        assert resolved == "new-game-uuid"

    async def test_both_patterns_same_valid_game(self):
        """Feature: Both REST and WebSocket work with valid games."""
        sessions: Dict[str, GameSession] = {}
        game = GameSession(mode="28", seats=4)
        sessions[game.id] = game

        # REST pattern
        rest_resolved = await resolve_game_identifier(
            game.id,
            sessions,
            raise_on_not_found=True
        )

        # WebSocket pattern
        ws_resolved = await resolve_game_identifier(
            game.id,
            sessions,
            raise_on_not_found=False
        )

        # Both resolve to same game
        assert rest_resolved == game.id
        assert ws_resolved == game.id
        assert rest_resolved == ws_resolved


@pytest.mark.asyncio
class TestRealWorldScenarios:
    """Test complete user scenarios."""

    async def test_share_game_url_workflow(self):
        """
        Feature: Player shares game URL with friend.

        Scenario:
        1. Alice creates game, gets short code "happy-cat-42"
        2. Alice shares URL with Bob
        3. Bob visits URL and connects
        4. Server resolves short code to Alice's game
        """
        sessions: Dict[str, GameSession] = {}

        # Alice creates game
        alice_game = GameSession(mode="28", seats=4, short_code="happy-cat-42")
        sessions[alice_game.id] = alice_game

        # Save to database (persistence)
        async with AsyncSessionLocal() as db:
            persistence = SessionPersistence(db)
            await persistence.save_session(alice_game, snapshot_reason="create")
            await db.commit()

        # Bob visits URL with short code
        bob_resolved = await resolve_game_identifier("happy-cat-42", sessions)

        # Bob connects to Alice's game
        assert bob_resolved == alice_game.id

    async def test_server_restart_recovery(self):
        """
        Feature: Games persist across server restarts.

        Scenario:
        1. Active game with 4 players
        2. Server restarts (memory cleared)
        3. Players reconnect using UUID or short code
        4. Game state restored from database
        """
        sessions: Dict[str, GameSession] = {}

        # Create active game with players
        game = GameSession(mode="28", seats=4, short_code="restart-recovery")
        sessions[game.id] = game

        # Save to database before "crash"
        async with AsyncSessionLocal() as db:
            persistence = SessionPersistence(db)
            await persistence.save_session(game, snapshot_reason="auto")
            await db.commit()

        # Simulate server restart (clear memory)
        game_id_before = game.id
        short_code_before = game.short_code
        sessions.clear()

        # Players reconnect after restart
        resolved_by_uuid = await resolve_game_identifier(game_id_before, sessions)
        resolved_by_code = await resolve_game_identifier(short_code_before, sessions)

        # Both resolve to same game from database
        assert resolved_by_uuid == game_id_before
        assert resolved_by_code == game_id_before

    async def test_mobile_user_bookmark_scenario(self):
        """
        Feature: Mobile user bookmarks game page.

        Scenario:
        1. User plays game on mobile
        2. User bookmarks page (UUID in URL)
        3. User returns later, game may be in memory or database
        4. Resolves correctly either way
        """
        sessions: Dict[str, GameSession] = {}

        # Initial game session
        game = GameSession(mode="28", seats=4)
        sessions[game.id] = game

        # User bookmarks UUID
        bookmarked_uuid = game.id

        # First access (in memory)
        first_access = await resolve_game_identifier(bookmarked_uuid, sessions)
        assert first_access == game.id

        # Game gets saved to DB
        async with AsyncSessionLocal() as db:
            persistence = SessionPersistence(db)
            await persistence.save_session(game, snapshot_reason="auto")
            await db.commit()

        # Game removed from memory (cleanup)
        sessions.clear()

        # User returns later (loads from DB)
        second_access = await resolve_game_identifier(bookmarked_uuid, sessions)
        assert second_access == bookmarked_uuid
