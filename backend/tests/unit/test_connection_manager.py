"""
Unit tests for WebSocket connection manager.

Tests the ConnectionManager and ConnectionInfo classes which handle
WebSocket connection tracking, player presence, and reconnection support.

Feature Coverage:
- Connection registration and unregistration
- Player identification and presence tracking
- Activity tracking and idle detection
- Connection info retrieval
- Multi-game connection management
- Reconnection scenarios
"""

import time
from unittest.mock import MagicMock

import pytest

from app.api.v1.connection_manager import ConnectionInfo, ConnectionManager


class TestConnectionInfo:
    """Test ConnectionInfo data class."""

    def test_connection_info_initialization(self):
        """Feature: Track basic connection metadata."""
        ws = MagicMock()
        game_id = "test-game-123"
        seat = 2

        info = ConnectionInfo(ws, game_id, seat)

        assert info.websocket == ws
        assert info.game_id == game_id
        assert info.seat == seat
        assert info.player_id is None
        assert info.connected_at > 0
        assert info.last_activity > 0

    def test_connection_info_without_seat(self):
        """Feature: Connection can exist before player identification."""
        ws = MagicMock()
        game_id = "test-game-123"

        info = ConnectionInfo(ws, game_id)

        assert info.websocket == ws
        assert info.game_id == game_id
        assert info.seat is None

    def test_update_activity(self):
        """Feature: Track when connection last sent a message."""
        ws = MagicMock()
        info = ConnectionInfo(ws, "game-1")

        initial_activity = info.last_activity
        time.sleep(0.01)  # Small delay to ensure time difference
        info.update_activity()

        assert info.last_activity > initial_activity

    def test_is_idle_false(self):
        """Feature: Detect active connections."""
        ws = MagicMock()
        info = ConnectionInfo(ws, "game-1")
        info.update_activity()

        # Should not be idle with 5 second timeout
        assert not info.is_idle(timeout_seconds=5)

    def test_is_idle_true(self):
        """Feature: Detect stale connections for cleanup."""
        ws = MagicMock()
        info = ConnectionInfo(ws, "game-1")

        # Set last activity to 10 seconds ago
        info.last_activity = time.time() - 10

        # Should be idle with 5 second timeout
        assert info.is_idle(timeout_seconds=5)

    def test_is_idle_custom_timeout(self):
        """Feature: Configurable idle timeout."""
        ws = MagicMock()
        info = ConnectionInfo(ws, "game-1")

        # Set last activity to 2 seconds ago
        info.last_activity = time.time() - 2

        # Should not be idle with 5 second timeout
        assert not info.is_idle(timeout_seconds=5)

        # Should be idle with 1 second timeout
        assert info.is_idle(timeout_seconds=1)


@pytest.mark.asyncio
class TestConnectionRegistration:
    """Test connection registration and unregistration."""

    async def test_register_connection_without_seat(self):
        """Feature: Register connection before player identifies."""
        manager = ConnectionManager()
        ws = MagicMock()
        game_id = "game-123"

        await manager.register(ws, game_id)

        info = manager.get_connection_info(ws)
        assert info is not None
        assert info.game_id == game_id
        assert info.seat is None

    async def test_register_connection_with_seat(self):
        """Feature: Register connection with immediate identification."""
        manager = ConnectionManager()
        ws = MagicMock()
        game_id = "game-123"
        seat = 2

        await manager.register(ws, game_id, seat)

        info = manager.get_connection_info(ws)
        assert info is not None
        assert info.game_id == game_id
        assert info.seat == seat

        # Should update presence tracking
        assert manager.is_player_connected(game_id, seat)

    async def test_register_multiple_connections_same_game(self):
        """Feature: Multiple players connect to same game."""
        manager = ConnectionManager()
        ws1 = MagicMock()
        ws2 = MagicMock()
        game_id = "game-123"

        await manager.register(ws1, game_id, seat=0)
        await manager.register(ws2, game_id, seat=1)

        assert manager.get_connection_count(game_id) == 2
        assert manager.is_player_connected(game_id, 0)
        assert manager.is_player_connected(game_id, 1)

    async def test_register_connections_different_games(self):
        """Feature: Server manages multiple concurrent games."""
        manager = ConnectionManager()
        ws1 = MagicMock()
        ws2 = MagicMock()

        await manager.register(ws1, "game-1", seat=0)
        await manager.register(ws2, "game-2", seat=0)

        assert manager.get_connection_count("game-1") == 1
        assert manager.get_connection_count("game-2") == 1
        assert manager.is_player_connected("game-1", 0)
        assert manager.is_player_connected("game-2", 0)

    async def test_unregister_connection(self):
        """Feature: Clean up connection on disconnect."""
        manager = ConnectionManager()
        ws = MagicMock()
        game_id = "game-123"

        await manager.register(ws, game_id, seat=2)
        assert manager.is_player_connected(game_id, 2)

        await manager.unregister(ws)

        assert manager.get_connection_info(ws) is None
        assert not manager.is_player_connected(game_id, 2)

    async def test_unregister_unknown_connection(self):
        """Feature: Handle unregister of already-removed connection."""
        manager = ConnectionManager()
        ws = MagicMock()

        # Should not raise error
        await manager.unregister(ws)

    async def test_unregister_connection_without_seat(self):
        """Feature: Clean up unidentified connections."""
        manager = ConnectionManager()
        ws = MagicMock()
        game_id = "game-123"

        await manager.register(ws, game_id)  # No seat
        await manager.unregister(ws)

        assert manager.get_connection_info(ws) is None


@pytest.mark.asyncio
class TestPlayerIdentification:
    """Test player identification after initial connection."""

    async def test_identify_connection(self):
        """Feature: Player identifies after connecting."""
        manager = ConnectionManager()
        ws = MagicMock()
        game_id = "game-123"

        # Connect without seat
        await manager.register(ws, game_id)
        assert manager.get_connection_info(ws).seat is None

        # Identify with seat
        await manager.identify(ws, seat=2)

        info = manager.get_connection_info(ws)
        assert info.seat == 2
        assert manager.is_player_connected(game_id, 2)

    async def test_identify_unknown_connection(self):
        """Feature: Handle identify from unknown connection."""
        manager = ConnectionManager()
        ws = MagicMock()

        # Should not crash, just log warning
        await manager.identify(ws, seat=2)

        # Connection should not be tracked
        assert manager.get_connection_info(ws) is None

    async def test_identify_changes_seat(self):
        """Feature: Player re-identifies with different seat."""
        manager = ConnectionManager()
        ws = MagicMock()
        game_id = "game-123"

        # Register with seat 0
        await manager.register(ws, game_id, seat=0)
        assert manager.is_player_connected(game_id, 0)

        # Re-identify as seat 2
        await manager.identify(ws, seat=2)

        info = manager.get_connection_info(ws)
        assert info.seat == 2
        assert not manager.is_player_connected(game_id, 0)
        assert manager.is_player_connected(game_id, 2)

    async def test_identify_multiple_connections_same_seat(self):
        """Feature: Multiple tabs for same player (reconnection)."""
        manager = ConnectionManager()
        ws1 = MagicMock()
        ws2 = MagicMock()
        game_id = "game-123"

        await manager.register(ws1, game_id, seat=2)
        await manager.register(ws2, game_id, seat=2)

        # Both connections should be tracked
        assert manager.get_connection_info(ws1).seat == 2
        assert manager.get_connection_info(ws2).seat == 2

        # Presence should show seat 2 is connected
        assert manager.is_player_connected(game_id, 2)


@pytest.mark.asyncio
class TestPresenceTracking:
    """Test player presence and connection queries."""

    async def test_get_present_seats_empty(self):
        """Feature: Game with no connections."""
        manager = ConnectionManager()

        present = manager.get_present_seats("game-123")

        assert present == set()

    async def test_get_present_seats_multiple_players(self):
        """Feature: Track which players are online."""
        manager = ConnectionManager()
        game_id = "game-123"

        ws0 = MagicMock()
        ws1 = MagicMock()
        ws2 = MagicMock()

        await manager.register(ws0, game_id, seat=0)
        await manager.register(ws1, game_id, seat=1)
        await manager.register(ws2, game_id, seat=2)

        present = manager.get_present_seats(game_id)

        assert present == {0, 1, 2}

    async def test_get_present_seats_after_disconnect(self):
        """Feature: Presence updates when player disconnects."""
        manager = ConnectionManager()
        game_id = "game-123"

        ws0 = MagicMock()
        ws1 = MagicMock()

        await manager.register(ws0, game_id, seat=0)
        await manager.register(ws1, game_id, seat=1)

        await manager.unregister(ws0)

        present = manager.get_present_seats(game_id)
        assert present == {1}

    async def test_is_player_connected(self):
        """Feature: Check if specific player is online."""
        manager = ConnectionManager()
        game_id = "game-123"
        ws = MagicMock()

        await manager.register(ws, game_id, seat=2)

        assert manager.is_player_connected(game_id, 2)
        assert not manager.is_player_connected(game_id, 0)
        assert not manager.is_player_connected(game_id, 1)

    async def test_is_player_connected_unknown_game(self):
        """Feature: Check connection in non-existent game."""
        manager = ConnectionManager()

        assert not manager.is_player_connected("unknown-game", 0)

    async def test_get_connection_count(self):
        """Feature: Count connections per game."""
        manager = ConnectionManager()
        game_id = "game-123"

        assert manager.get_connection_count(game_id) == 0

        ws1 = MagicMock()
        ws2 = MagicMock()
        await manager.register(ws1, game_id, seat=0)
        await manager.register(ws2, game_id, seat=1)

        assert manager.get_connection_count(game_id) == 2

    async def test_get_game_connections(self):
        """Feature: Get all WebSocket instances for a game."""
        manager = ConnectionManager()
        game_id = "game-123"

        ws1 = MagicMock()
        ws2 = MagicMock()
        ws3 = MagicMock()

        await manager.register(ws1, game_id, seat=0)
        await manager.register(ws2, game_id, seat=1)
        await manager.register(ws3, "other-game", seat=0)

        connections = manager.get_game_connections(game_id)

        assert len(connections) == 2
        assert ws1 in connections
        assert ws2 in connections
        assert ws3 not in connections


@pytest.mark.asyncio
class TestActivityTracking:
    """Test activity timestamp updates."""

    async def test_update_activity(self):
        """Feature: Track when players send messages."""
        manager = ConnectionManager()
        ws = MagicMock()

        await manager.register(ws, "game-1", seat=0)

        info = manager.get_connection_info(ws)
        initial_activity = info.last_activity

        time.sleep(0.01)
        manager.update_activity(ws)

        assert info.last_activity > initial_activity

    async def test_update_activity_unknown_connection(self):
        """Feature: Handle activity update for unknown connection."""
        manager = ConnectionManager()
        ws = MagicMock()

        # Should not crash
        manager.update_activity(ws)


@pytest.mark.asyncio
class TestReconnectionScenarios:
    """Test real-world reconnection scenarios."""

    async def test_player_refreshes_page(self):
        """
        Feature: Player refreshes page and reconnects.

        Scenario:
        1. Player connected with seat 2
        2. Page refresh disconnects WebSocket
        3. New WebSocket connects
        4. Player re-identifies with seat 2
        """
        manager = ConnectionManager()
        game_id = "game-123"

        # Initial connection
        ws_old = MagicMock()
        await manager.register(ws_old, game_id, seat=2)
        assert manager.is_player_connected(game_id, 2)

        # Disconnect (page refresh)
        await manager.unregister(ws_old)
        assert not manager.is_player_connected(game_id, 2)

        # Reconnect with new WebSocket
        ws_new = MagicMock()
        await manager.register(ws_new, game_id)
        await manager.identify(ws_new, seat=2)

        assert manager.is_player_connected(game_id, 2)
        assert manager.get_connection_info(ws_new).seat == 2

    async def test_player_has_multiple_tabs(self):
        """
        Feature: Player opens multiple tabs for same game.

        Scenario:
        1. Player opens tab 1, connects as seat 2
        2. Player opens tab 2, also connects as seat 2
        3. Both tabs remain connected
        4. Closing one tab marks player offline (current simple implementation)

        Note: Current implementation uses simple set-based presence tracking,
        so ANY disconnect removes the seat from presence. This is acceptable
        since game state is preserved and player can reconnect.
        """
        manager = ConnectionManager()
        game_id = "game-123"

        # Tab 1 connects
        ws_tab1 = MagicMock()
        await manager.register(ws_tab1, game_id, seat=2)

        # Tab 2 connects
        ws_tab2 = MagicMock()
        await manager.register(ws_tab2, game_id, seat=2)

        # Both connections tracked
        assert manager.get_connection_count(game_id) == 2
        assert manager.is_player_connected(game_id, 2)

        # Close tab 1
        await manager.unregister(ws_tab1)

        # Current implementation: presence removed even though tab 2 still open
        # This is acceptable behavior - player will still receive updates via tab 2
        assert not manager.is_player_connected(game_id, 2)  # Presence shows offline
        assert manager.get_connection_count(game_id) == 1   # But connection exists

    async def test_all_players_disconnect_and_reconnect(self):
        """
        Feature: Game persists after all players disconnect.

        Scenario:
        1. 4 players connected
        2. All players disconnect (server restart, network issues)
        3. Players reconnect one by one
        4. Presence tracking updates correctly
        """
        manager = ConnectionManager()
        game_id = "game-123"

        # All players connect
        players = [MagicMock() for _ in range(4)]
        for seat, ws in enumerate(players):
            await manager.register(ws, game_id, seat=seat)

        assert manager.get_present_seats(game_id) == {0, 1, 2, 3}

        # All players disconnect
        for ws in players:
            await manager.unregister(ws)

        assert manager.get_present_seats(game_id) == set()

        # Players reconnect one by one
        new_players = [MagicMock() for _ in range(4)]
        for seat, ws in enumerate(new_players):
            await manager.register(ws, game_id, seat=seat)
            # Presence should update after each reconnection
            assert manager.is_player_connected(game_id, seat)

        assert manager.get_present_seats(game_id) == {0, 1, 2, 3}


@pytest.mark.asyncio
class TestMultiGameManagement:
    """Test managing multiple concurrent games."""

    async def test_multiple_games_independent_presence(self):
        """Feature: Each game has independent presence tracking."""
        manager = ConnectionManager()

        # Game 1 with 2 players
        ws_g1_p0 = MagicMock()
        ws_g1_p1 = MagicMock()
        await manager.register(ws_g1_p0, "game-1", seat=0)
        await manager.register(ws_g1_p1, "game-1", seat=1)

        # Game 2 with 3 players
        ws_g2_p0 = MagicMock()
        ws_g2_p1 = MagicMock()
        ws_g2_p2 = MagicMock()
        await manager.register(ws_g2_p0, "game-2", seat=0)
        await manager.register(ws_g2_p1, "game-2", seat=1)
        await manager.register(ws_g2_p2, "game-2", seat=2)

        # Each game has independent presence
        assert manager.get_present_seats("game-1") == {0, 1}
        assert manager.get_present_seats("game-2") == {0, 1, 2}

        # Disconnect from game 1 doesn't affect game 2
        await manager.unregister(ws_g1_p0)
        assert manager.get_present_seats("game-1") == {1}
        assert manager.get_present_seats("game-2") == {0, 1, 2}

    async def test_connection_count_per_game(self):
        """Feature: Track connections separately per game."""
        manager = ConnectionManager()

        ws1 = MagicMock()
        ws2 = MagicMock()
        ws3 = MagicMock()

        await manager.register(ws1, "game-1", seat=0)
        await manager.register(ws2, "game-1", seat=1)
        await manager.register(ws3, "game-2", seat=0)

        assert manager.get_connection_count("game-1") == 2
        assert manager.get_connection_count("game-2") == 1
        assert manager.get_connection_count("game-3") == 0

    async def test_get_game_connections_isolated(self):
        """Feature: Get connections only for specific game."""
        manager = ConnectionManager()

        ws_g1 = MagicMock()
        ws_g2 = MagicMock()

        await manager.register(ws_g1, "game-1", seat=0)
        await manager.register(ws_g2, "game-2", seat=0)

        game1_conns = manager.get_game_connections("game-1")
        game2_conns = manager.get_game_connections("game-2")

        assert ws_g1 in game1_conns
        assert ws_g1 not in game2_conns
        assert ws_g2 in game2_conns
        assert ws_g2 not in game1_conns


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and error conditions."""

    async def test_register_same_websocket_twice(self):
        """Feature: Re-registering same WebSocket overwrites."""
        manager = ConnectionManager()
        ws = MagicMock()

        await manager.register(ws, "game-1", seat=0)
        await manager.register(ws, "game-2", seat=1)

        # Should use latest registration
        info = manager.get_connection_info(ws)
        assert info.game_id == "game-2"
        assert info.seat == 1

    async def test_identify_without_register(self):
        """Feature: Identify without prior registration."""
        manager = ConnectionManager()
        ws = MagicMock()

        # Should not crash
        await manager.identify(ws, seat=2)

        # Should not create connection
        assert manager.get_connection_info(ws) is None

    async def test_unregister_twice(self):
        """Feature: Unregister same connection twice."""
        manager = ConnectionManager()
        ws = MagicMock()

        await manager.register(ws, "game-1", seat=0)
        await manager.unregister(ws)
        await manager.unregister(ws)  # Should not crash

        assert manager.get_connection_info(ws) is None

    async def test_presence_copy_isolation(self):
        """Feature: get_present_seats returns copy, not reference."""
        manager = ConnectionManager()
        ws = MagicMock()
        game_id = "game-1"

        await manager.register(ws, game_id, seat=0)

        present1 = manager.get_present_seats(game_id)
        present1.add(99)  # Modify copy

        present2 = manager.get_present_seats(game_id)

        # Original should be unchanged
        assert 99 not in present2
        assert present2 == {0}
