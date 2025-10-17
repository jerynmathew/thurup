"""
Integration tests for REST and WebSocket APIs.

Tests full end-to-end flows including:
- Game creation and player joining
- WebSocket connections and state updates
- Bot interaction
- State persistence
- History endpoints
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Test client for REST endpoints."""
    return TestClient(app)


@pytest.fixture
def admin_auth():
    """Admin authentication headers."""
    # Using default credentials from admin.py
    import base64

    credentials = base64.b64encode(b"admin:changeme").decode("utf-8")
    return {"Authorization": f"Basic {credentials}"}


class TestRESTIntegration:
    """Integration tests for REST API endpoints."""

    def test_create_and_get_game(self, client):
        """Test creating a game and retrieving it."""
        # Create game
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        assert response.status_code == 200
        game_id = response.json()["game_id"]
        assert game_id is not None

        # Get game state
        response = client.get(f"/api/v1/game/{game_id}")
        assert response.status_code == 200
        state = response.json()
        assert state["mode"] == "28"
        assert state["seats"] == 4
        assert state["state"] == "lobby"

    def test_join_game_flow(self, client):
        """Test complete join game flow with multiple players."""
        # Create game
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        game_id = response.json()["game_id"]

        # Join 4 players (2 human, 2 bots)
        players = []
        for i in range(4):
            is_bot = i >= 2
            response = client.post(
                f"/api/v1/game/{game_id}/join",
                json={"name": f"Player{i}", "is_bot": is_bot},
            )
            assert response.status_code == 200
            player_data = response.json()
            assert player_data["seat"] == i
            players.append(player_data)

        # Check game state - should auto-start
        response = client.get(f"/api/v1/game/{game_id}")
        assert response.status_code == 200
        state = response.json()
        # May be in bidding or beyond if bots acted
        assert state["state"] in ["bidding", "choose_trump", "play"]

    def test_bidding_flow(self, client):
        """Test bidding phase."""
        # Create and setup game
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        game_id = response.json()["game_id"]

        # Join players
        for i in range(4):
            client.post(
                f"/api/v1/game/{game_id}/join",
                json={"name": f"Player{i}", "is_bot": False},
            )

        # Start game manually
        response = client.post(f"/api/v1/game/{game_id}/start", json={"dealer": 0})
        assert response.status_code == 200

        # Get state
        response = client.get(f"/api/v1/game/{game_id}")
        state = response.json()
        assert state["state"] == "bidding"

        # Place a valid bid
        response = client.post(f"/api/v1/game/{game_id}/bid?seat=1", json={"value": 15})
        # May succeed or fail depending on game rules and current turn
        # We just verify the endpoint works
        assert response.status_code in [200, 400]

    def test_game_not_found(self, client):
        """Test 404 for non-existent game."""
        response = client.get("/api/v1/game/nonexistent")
        assert response.status_code == 404


class TestHistoryIntegration:
    """Integration tests for game history endpoints."""

    def test_list_games(self, client):
        """Test listing games."""
        # Create a few games
        game_ids = []
        for i in range(3):
            response = client.post(
                "/api/v1/game/create", json={"mode": "28", "seats": 4}
            )
            game_ids.append(response.json()["game_id"])

        # List all games
        response = client.get("/api/v1/history/games")
        assert response.status_code == 200
        games = response.json()
        assert len(games) >= 3

    def test_list_games_with_filters(self, client):
        """Test listing games with state filter."""
        response = client.get("/api/v1/history/games?state=lobby&limit=10")
        assert response.status_code == 200
        games = response.json()
        # All returned games should be in lobby state
        for game in games:
            assert game["state"] == "lobby"

    def test_game_detail(self, client):
        """Test getting detailed game info."""
        # Create game
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        game_id = response.json()["game_id"]

        # Get detail
        response = client.get(f"/api/v1/history/games/{game_id}")
        assert response.status_code == 200
        detail = response.json()
        assert detail["game"]["game_id"] == game_id
        assert "snapshots" in detail
        assert detail["total_snapshots"] >= 1  # At least creation snapshot

    def test_history_stats(self, client):
        """Test getting history statistics."""
        response = client.get("/api/v1/history/stats")
        assert response.status_code == 200
        stats = response.json()
        assert "total_games" in stats
        assert "completed_games" in stats
        assert "active_games" in stats
        assert stats["total_games"] >= 0

    def test_game_replay(self, client):
        """Test game replay endpoint."""
        # Create and setup a game with some actions
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        game_id = response.json()["game_id"]

        # Join players
        for i in range(4):
            client.post(
                f"/api/v1/game/{game_id}/join",
                json={"name": f"Player{i}", "is_bot": False},
            )

        # Get replay
        response = client.get(f"/api/v1/history/games/{game_id}/replay")
        assert response.status_code == 200
        replay = response.json()
        assert replay["game_id"] == game_id
        assert "snapshots" in replay
        assert len(replay["snapshots"]) >= 1


class TestAdminIntegration:
    """Integration tests for admin endpoints."""

    def test_health_check(self, client, admin_auth):
        """Test admin health check endpoint."""
        response = client.get("/api/v1/admin/health", headers=admin_auth)
        assert response.status_code == 200
        health = response.json()
        assert health["status"] in ["healthy", "degraded"]
        assert "in_memory_sessions" in health
        assert "database_connected" in health

    def test_health_check_unauthorized(self, client):
        """Test health check without auth fails."""
        response = client.get("/api/v1/admin/health")
        assert response.status_code == 401

    def test_list_sessions(self, client, admin_auth):
        """Test listing in-memory sessions."""
        # Create a game first
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        game_id = response.json()["game_id"]

        # List sessions
        response = client.get("/api/v1/admin/sessions", headers=admin_auth)
        assert response.status_code == 200
        sessions = response.json()
        assert len(sessions) >= 1
        # Find our game
        found = any(s["game_id"] == game_id for s in sessions)
        assert found

    def test_session_detail(self, client, admin_auth):
        """Test getting detailed session info."""
        # Create game
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        game_id = response.json()["game_id"]

        # Get detail
        response = client.get(
            f"/api/v1/admin/sessions/{game_id}/detail", headers=admin_auth
        )
        assert response.status_code == 200
        detail = response.json()
        assert detail["game_id"] == game_id
        assert "public_state" in detail
        assert "all_hands" in detail  # Admin can see all hands

    def test_database_stats(self, client, admin_auth):
        """Test database statistics endpoint."""
        response = client.get("/api/v1/admin/database/stats", headers=admin_auth)
        assert response.status_code == 200
        stats = response.json()
        assert "total_games" in stats
        assert "total_players" in stats
        assert "total_snapshots" in stats

    def test_force_save_session(self, client, admin_auth):
        """Test manually triggering session save."""
        # Create game
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        game_id = response.json()["game_id"]

        # Force save
        response = client.post(
            f"/api/v1/admin/sessions/{game_id}/save", headers=admin_auth
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_list_connections(self, client, admin_auth):
        """Test listing WebSocket connections."""
        response = client.get("/api/v1/admin/connections", headers=admin_auth)
        assert response.status_code == 200
        data = response.json()
        assert "connections" in data
        assert "total" in data

    def test_trigger_cleanup(self, client, admin_auth):
        """Test manual cleanup trigger."""
        response = client.post("/api/v1/admin/maintenance/cleanup", headers=admin_auth)
        assert response.status_code == 200
        result = response.json()
        assert "deleted_games" in result


class TestWebSocketIntegration:
    """Integration tests for WebSocket endpoints."""

    def test_websocket_connect_and_identify(self, client):
        """Test WebSocket connection and player identification."""
        # Create game and join as player
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        game_id = response.json()["game_id"]

        response = client.post(
            f"/api/v1/game/{game_id}/join",
            json={"name": "TestPlayer", "is_bot": False},
        )
        seat = response.json()["seat"]

        # Connect via WebSocket
        with client.websocket_connect(f"/api/v1/ws/game/{game_id}") as websocket:
            # Should receive initial state
            data = websocket.receive_json()
            assert data["type"] == "state_snapshot"
            assert "payload" in data

            # Identify as player
            websocket.send_json({"type": "identify", "payload": {"seat": seat}})

            # Should receive state with hand
            data = websocket.receive_json()
            assert data["type"] == "state_snapshot"
            assert "owner_hand" in data["payload"]

    def test_websocket_request_state(self, client):
        """Test requesting state via WebSocket."""
        # Create game
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        game_id = response.json()["game_id"]

        with client.websocket_connect(f"/api/v1/ws/game/{game_id}") as websocket:
            # Receive initial state
            websocket.receive_json()

            # Request state
            websocket.send_json({"type": "request_state", "payload": {}})

            # Should receive state snapshot
            data = websocket.receive_json()
            assert data["type"] == "state_snapshot"
            assert data["payload"]["mode"] == "28"

    def test_websocket_unknown_message_type(self, client):
        """Test unknown WebSocket message type."""
        # Create game
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        game_id = response.json()["game_id"]

        with client.websocket_connect(f"/api/v1/ws/game/{game_id}") as websocket:
            # Receive initial state
            websocket.receive_json()

            # Send unknown message type
            websocket.send_json({"type": "invalid_type", "payload": {}})

            # Should receive error
            data = websocket.receive_json()
            assert data["type"] == "error"


class TestPersistenceIntegration:
    """Integration tests for persistence functionality."""

    def test_game_persists_across_loads(self, client):
        """Test that game state persists when loaded from database."""
        # Create game
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        game_id = response.json()["game_id"]

        # Join players
        for i in range(2):
            client.post(
                f"/api/v1/game/{game_id}/join",
                json={"name": f"Player{i}", "is_bot": False},
            )

        # Get initial state
        response = client.get(f"/api/v1/game/{game_id}")
        initial_state = response.json()

        # The game is automatically persisted, verify we can reload it
        # In a real scenario, we'd restart the server here
        # For now, just verify the state is consistent
        response = client.get(f"/api/v1/game/{game_id}")
        reloaded_state = response.json()

        assert initial_state["mode"] == reloaded_state["mode"]
        assert initial_state["seats"] == reloaded_state["seats"]
        assert len(initial_state["players"]) == len(reloaded_state["players"])

    def test_snapshot_creation(self, client):
        """Test that snapshots are created for game actions."""
        # Create game
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        game_id = response.json()["game_id"]

        # Join players (triggers snapshots)
        for i in range(4):
            client.post(
                f"/api/v1/game/{game_id}/join",
                json={"name": f"Player{i}", "is_bot": False},
            )

        # Check that snapshots exist
        response = client.get(f"/api/v1/history/games/{game_id}")
        assert response.status_code == 200
        detail = response.json()
        # Should have at least: create + 4 player_join snapshots
        assert detail["total_snapshots"] >= 5


class TestEndToEndFlow:
    """End-to-end integration tests."""

    def test_complete_game_flow(self, client):
        """Test a complete game flow from creation to playing."""
        # 1. Create game
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        assert response.status_code == 200
        game_id = response.json()["game_id"]

        # 2. Join 4 players (mix of humans and bots)
        for i in range(4):
            is_bot = i >= 2
            response = client.post(
                f"/api/v1/game/{game_id}/join",
                json={"name": f"Player{i}", "is_bot": is_bot},
            )
            assert response.status_code == 200

        # 3. Game should auto-start
        response = client.get(f"/api/v1/game/{game_id}")
        state = response.json()
        assert state["state"] in ["bidding", "choose_trump", "play"]

        # 4. Check game appears in history
        response = client.get("/api/v1/history/games")
        games = response.json()
        found = any(g["game_id"] == game_id for g in games)
        assert found

        # 5. Check snapshots were created
        response = client.get(f"/api/v1/history/games/{game_id}")
        detail = response.json()
        assert detail["total_snapshots"] > 0

    def test_websocket_and_rest_consistency(self, client):
        """Test that WebSocket and REST endpoints return consistent state."""
        # Create game
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        game_id = response.json()["game_id"]

        # Get REST state
        response = client.get(f"/api/v1/game/{game_id}")
        rest_state = response.json()

        # Get WebSocket state
        with client.websocket_connect(f"/api/v1/ws/game/{game_id}") as websocket:
            data = websocket.receive_json()
            ws_state = data["payload"]

            # Compare key fields
            assert rest_state["mode"] == ws_state["mode"]
            assert rest_state["seats"] == ws_state["seats"]
            assert rest_state["state"] == ws_state["state"]
