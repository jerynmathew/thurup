"""
Comprehensive integration tests for admin.py endpoints.

Tests all admin endpoints with various scenarios:
- Authentication (success and failure)
- Health checks and metrics
- Session management and inspection
- Connection monitoring
- Database statistics
- Manual operations (save, delete, kill bots)
- Game history browsing
- Error handling
"""

import base64

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Test client for REST endpoints."""
    return TestClient(app)


@pytest.fixture
def admin_auth():
    """Admin authentication headers with correct credentials."""
    credentials = base64.b64encode(b"admin:changeme").decode("utf-8")
    return {"Authorization": f"Basic {credentials}"}


@pytest.fixture
def invalid_auth():
    """Invalid authentication headers."""
    credentials = base64.b64encode(b"admin:wrongpassword").decode("utf-8")
    return {"Authorization": f"Basic {credentials}"}


@pytest.fixture
def sample_game(client):
    """Create a sample game for testing."""
    response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
    game_id = response.json()["game_id"]

    # Join some players
    for i in range(2):
        client.post(
            f"/api/v1/game/{game_id}/join",
            json={"name": f"Player{i}", "is_bot": False}
        )

    return game_id


class TestAdminAuthentication:
    """Tests for admin authentication."""

    def test_health_with_valid_auth(self, client, admin_auth):
        """Test that valid credentials work."""
        response = client.get("/api/v1/admin/health", headers=admin_auth)
        assert response.status_code == 200

    def test_health_without_auth(self, client):
        """Test that missing auth is rejected."""
        response = client.get("/api/v1/admin/health")
        assert response.status_code == 401

    def test_health_with_invalid_auth(self, client, invalid_auth):
        """Test that wrong credentials are rejected."""
        response = client.get("/api/v1/admin/health", headers=invalid_auth)
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_sessions_with_invalid_username(self, client):
        """Test invalid username in basic auth."""
        credentials = base64.b64encode(b"wronguser:changeme").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}

        response = client.get("/api/v1/admin/sessions", headers=headers)
        assert response.status_code == 401

    def test_all_endpoints_require_auth(self, client):
        """Test that all admin endpoints require authentication."""
        endpoints = [
            "/api/v1/admin/health",
            "/api/v1/admin/sessions",
            "/api/v1/admin/connections",
            "/api/v1/admin/database/stats",
            "/api/v1/admin/games/history",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"{endpoint} should require auth"


class TestServerHealth:
    """Tests for GET /admin/health endpoint."""

    def test_health_check_structure(self, client, admin_auth):
        """Test health check response structure."""
        response = client.get("/api/v1/admin/health", headers=admin_auth)
        assert response.status_code == 200

        health = response.json()
        assert "status" in health
        assert "uptime_seconds" in health
        assert "in_memory_sessions" in health
        assert "total_connections" in health
        assert "running_bot_tasks" in health
        assert "database_connected" in health

        # Verify types
        assert isinstance(health["status"], str)
        assert isinstance(health["uptime_seconds"], (int, float))
        assert isinstance(health["in_memory_sessions"], int)
        assert isinstance(health["total_connections"], int)
        assert isinstance(health["running_bot_tasks"], int)
        assert isinstance(health["database_connected"], bool)

    def test_health_status_values(self, client, admin_auth):
        """Test that health status is healthy or degraded."""
        response = client.get("/api/v1/admin/health", headers=admin_auth)
        health = response.json()
        assert health["status"] in ["healthy", "degraded"]

    def test_health_with_active_game(self, client, admin_auth, sample_game):
        """Test health check reflects active sessions."""
        response = client.get("/api/v1/admin/health", headers=admin_auth)
        health = response.json()

        # Should show at least 1 in-memory session
        assert health["in_memory_sessions"] >= 1

    def test_health_database_connected(self, client, admin_auth):
        """Test database connection check."""
        response = client.get("/api/v1/admin/health", headers=admin_auth)
        health = response.json()

        # In test environment, database should be connected
        assert health["database_connected"] is True
        assert health["status"] == "healthy"


class TestListSessions:
    """Tests for GET /admin/sessions endpoint."""

    def test_list_sessions_empty(self, client, admin_auth):
        """Test listing sessions when none exist."""
        response = client.get("/api/v1/admin/sessions", headers=admin_auth)
        assert response.status_code == 200
        sessions = response.json()
        assert isinstance(sessions, list)

    def test_list_sessions_with_game(self, client, admin_auth, sample_game):
        """Test listing sessions with active game."""
        response = client.get("/api/v1/admin/sessions", headers=admin_auth)
        assert response.status_code == 200
        sessions = response.json()

        # Should find our sample game
        assert len(sessions) >= 1
        found = any(s["game_id"] == sample_game for s in sessions)
        assert found

    def test_list_sessions_response_structure(self, client, admin_auth, sample_game):
        """Test that session info has correct structure."""
        response = client.get("/api/v1/admin/sessions", headers=admin_auth)
        sessions = response.json()

        for session in sessions:
            assert "game_id" in session
            assert "short_code" in session
            assert "mode" in session
            assert "seats" in session
            assert "state" in session
            assert "player_count" in session
            assert "connection_count" in session
            assert "connected_seats" in session
            assert "has_bot_task" in session

    def test_list_sessions_player_count(self, client, admin_auth, sample_game):
        """Test that player count is accurate."""
        response = client.get("/api/v1/admin/sessions", headers=admin_auth)
        sessions = response.json()

        game_session = next(s for s in sessions if s["game_id"] == sample_game)
        assert game_session["player_count"] == 2  # We added 2 players in fixture


class TestSessionDetail:
    """Tests for GET /admin/sessions/{game_id}/detail endpoint."""

    def test_get_session_detail_success(self, client, admin_auth, sample_game):
        """Test getting detailed session info."""
        response = client.get(f"/api/v1/admin/sessions/{sample_game}/detail", headers=admin_auth)
        assert response.status_code == 200

        detail = response.json()
        assert "game_id" in detail
        assert "public_state" in detail
        assert "all_hands" in detail
        assert "connection_count" in detail
        assert "connected_seats" in detail
        assert "has_bot_task" in detail

        assert detail["game_id"] == sample_game

    def test_get_session_detail_not_found(self, client, admin_auth):
        """Test getting detail for non-existent session."""
        response = client.get("/api/v1/admin/sessions/nonexistent-game/detail", headers=admin_auth)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_session_detail_includes_all_hands(self, client, admin_auth, sample_game):
        """Test that admin can see all player hands."""
        # Start the game so players have hands
        client.post(f"/api/v1/game/{sample_game}/join", json={"name": "Player2", "is_bot": False})
        client.post(f"/api/v1/game/{sample_game}/join", json={"name": "Player3", "is_bot": False})
        client.post(f"/api/v1/game/{sample_game}/start", json={"dealer": 0})

        response = client.get(f"/api/v1/admin/sessions/{sample_game}/detail", headers=admin_auth)
        detail = response.json()

        # all_hands should be a dict mapping seat to cards
        assert isinstance(detail["all_hands"], dict)


class TestListConnections:
    """Tests for GET /admin/connections endpoint."""

    def test_list_connections_structure(self, client, admin_auth):
        """Test connections endpoint structure."""
        response = client.get("/api/v1/admin/connections", headers=admin_auth)
        assert response.status_code == 200

        data = response.json()
        assert "connections" in data
        assert "total" in data
        assert isinstance(data["connections"], list)
        assert isinstance(data["total"], int)

    def test_list_connections_empty(self, client, admin_auth):
        """Test connections list when none are active."""
        response = client.get("/api/v1/admin/connections", headers=admin_auth)
        data = response.json()

        # Should be zero or very few connections
        assert data["total"] >= 0


class TestDatabaseStats:
    """Tests for GET /admin/database/stats endpoint."""

    def test_database_stats_structure(self, client, admin_auth):
        """Test database stats response structure."""
        response = client.get("/api/v1/admin/database/stats", headers=admin_auth)
        assert response.status_code == 200

        stats = response.json()
        assert "total_games" in stats
        assert "total_players" in stats
        assert "total_snapshots" in stats
        assert "db_size_bytes" in stats

    def test_database_stats_values(self, client, admin_auth):
        """Test that database stats contain valid values."""
        response = client.get("/api/v1/admin/database/stats", headers=admin_auth)
        stats = response.json()

        # All counts should be non-negative
        assert stats["total_games"] >= 0
        assert stats["total_players"] >= 0
        assert stats["total_snapshots"] >= 0

    def test_database_stats_with_game(self, client, admin_auth, sample_game):
        """Test stats reflect created games."""
        response = client.get("/api/v1/admin/database/stats", headers=admin_auth)
        stats = response.json()

        # Should have at least 1 game and 2 players
        assert stats["total_games"] >= 1
        assert stats["total_players"] >= 2


class TestForceSaveSession:
    """Tests for POST /admin/sessions/{game_id}/save endpoint."""

    def test_force_save_success(self, client, admin_auth, sample_game):
        """Test manually saving a session."""
        response = client.post(f"/api/v1/admin/sessions/{sample_game}/save", headers=admin_auth)
        assert response.status_code == 200

        result = response.json()
        assert result["ok"] is True
        assert "message" in result

    def test_force_save_not_found(self, client, admin_auth):
        """Test saving non-existent session."""
        response = client.post("/api/v1/admin/sessions/nonexistent-game/save", headers=admin_auth)
        assert response.status_code == 404


class TestDeleteSession:
    """Tests for DELETE /admin/sessions/{game_id} endpoint."""

    def test_delete_session_success(self, client, admin_auth):
        """Test deleting a session."""
        # Create a game to delete
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        game_id = response.json()["game_id"]

        # Delete it
        response = client.delete(f"/api/v1/admin/sessions/{game_id}", headers=admin_auth)
        assert response.status_code == 200

        result = response.json()
        assert result["ok"] is True
        assert "deleted_from_memory" in result
        assert "deleted_from_database" in result

    def test_delete_session_not_found(self, client, admin_auth):
        """Test deleting non-existent session."""
        response = client.delete("/api/v1/admin/sessions/nonexistent-game", headers=admin_auth)
        assert response.status_code == 200  # Succeeds even if not found

        result = response.json()
        assert result["deleted_from_memory"] is False

    def test_delete_session_removes_from_memory(self, client, admin_auth):
        """Test that deleted session is removed from memory."""
        # Create game
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        game_id = response.json()["game_id"]

        # Verify it's in memory
        response = client.get("/api/v1/admin/sessions", headers=admin_auth)
        sessions = response.json()
        assert any(s["game_id"] == game_id for s in sessions)

        # Delete it
        client.delete(f"/api/v1/admin/sessions/{game_id}", headers=admin_auth)

        # Verify it's gone from memory
        response = client.get("/api/v1/admin/sessions", headers=admin_auth)
        sessions = response.json()
        assert not any(s["game_id"] == game_id for s in sessions)


class TestKillBotTask:
    """Tests for POST /admin/sessions/{game_id}/kill_bots endpoint."""

    def test_kill_bot_task_not_found(self, client, admin_auth, sample_game):
        """Test killing bot task when none is running."""
        response = client.post(f"/api/v1/admin/sessions/{sample_game}/kill_bots", headers=admin_auth)
        assert response.status_code == 404
        assert "No bot task" in response.json()["detail"]


class TestRecentLogs:
    """Tests for GET /admin/logs/recent endpoint."""

    def test_recent_logs_placeholder(self, client, admin_auth):
        """Test recent logs endpoint (placeholder implementation)."""
        response = client.get("/api/v1/admin/logs/recent", headers=admin_auth)
        assert response.status_code == 200

        data = response.json()
        assert "message" in data

    def test_recent_logs_with_limit(self, client, admin_auth):
        """Test recent logs with custom limit."""
        response = client.get("/api/v1/admin/logs/recent?limit=100", headers=admin_auth)
        assert response.status_code == 200


class TestMaintenanceCleanup:
    """Tests for POST /admin/maintenance/cleanup endpoint."""

    def test_trigger_cleanup(self, client, admin_auth):
        """Test manual cleanup trigger."""
        response = client.post("/api/v1/admin/maintenance/cleanup", headers=admin_auth)
        assert response.status_code == 200

        result = response.json()
        assert result["ok"] is True
        assert "deleted_games" in result
        assert isinstance(result["deleted_games"], int)
        assert result["deleted_games"] >= 0


class TestGameHistory:
    """Tests for GET /admin/games/history endpoint."""

    def test_list_game_history(self, client, admin_auth, sample_game):
        """Test listing game history."""
        response = client.get("/api/v1/admin/games/history", headers=admin_auth)
        assert response.status_code == 200

        history = response.json()
        assert isinstance(history, list)
        assert len(history) >= 1

    def test_list_game_history_structure(self, client, admin_auth, sample_game):
        """Test game history item structure."""
        response = client.get("/api/v1/admin/games/history", headers=admin_auth)
        history = response.json()

        for item in history:
            assert "game_id" in item
            assert "short_code" in item
            assert "mode" in item
            assert "seats" in item
            assert "state" in item
            assert "rounds_played" in item
            assert "created_at" in item
            assert "last_activity_at" in item
            assert "player_names" in item

    def test_list_game_history_pagination(self, client, admin_auth):
        """Test game history pagination."""
        # Create multiple games
        for i in range(3):
            client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})

        # Test with limit
        response = client.get("/api/v1/admin/games/history?limit=2", headers=admin_auth)
        history = response.json()
        assert len(history) <= 2

        # Test with offset
        response = client.get("/api/v1/admin/games/history?limit=1&offset=1", headers=admin_auth)
        history = response.json()
        assert len(history) <= 1

    def test_list_game_history_ordered(self, client, admin_auth):
        """Test that games are ordered by last_activity_at descending."""
        response = client.get("/api/v1/admin/games/history?limit=10", headers=admin_auth)
        history = response.json()

        if len(history) >= 2:
            from datetime import datetime
            for i in range(len(history) - 1):
                time1 = datetime.fromisoformat(history[i]["last_activity_at"])
                time2 = datetime.fromisoformat(history[i + 1]["last_activity_at"])
                assert time1 >= time2


class TestGameRounds:
    """Tests for GET /admin/games/{game_id}/rounds endpoint."""

    def test_get_game_rounds_success(self, client, admin_auth, sample_game):
        """Test getting game rounds."""
        response = client.get(f"/api/v1/admin/games/{sample_game}/rounds", headers=admin_auth)
        assert response.status_code == 200

        data = response.json()
        assert "game_id" in data
        assert "short_code" in data
        assert "mode" in data
        assert "seats" in data
        assert "state" in data
        assert "players" in data
        assert "rounds" in data
        assert "total_rounds" in data

        assert data["game_id"] == sample_game

    def test_get_game_rounds_not_found(self, client, admin_auth):
        """Test getting rounds for non-existent game."""
        response = client.get("/api/v1/admin/games/nonexistent-game/rounds", headers=admin_auth)
        assert response.status_code == 404

    def test_get_game_rounds_players(self, client, admin_auth, sample_game):
        """Test that players are included in response."""
        response = client.get(f"/api/v1/admin/games/{sample_game}/rounds", headers=admin_auth)
        data = response.json()

        # Should have 2 players from fixture
        assert len(data["players"]) == 2

        for player in data["players"]:
            assert "player_id" in player
            assert "name" in player
            assert "seat" in player
            assert "is_bot" in player
            assert "joined_at" in player


class TestAdminErrorHandling:
    """Tests for error handling in admin endpoints."""

    def test_invalid_game_id_format(self, client, admin_auth):
        """Test handling of malformed game IDs."""
        # SQL injection attempt
        response = client.get("/api/v1/admin/sessions/'; DROP TABLE games;--/detail", headers=admin_auth)
        assert response.status_code == 404

    def test_concurrent_admin_requests(self, client, admin_auth, sample_game):
        """Test handling multiple concurrent admin requests."""
        # Make multiple requests in sequence (simulating concurrent access)
        responses = []
        for _ in range(5):
            r = client.get("/api/v1/admin/health", headers=admin_auth)
            responses.append(r)

        # All should succeed
        for r in responses:
            assert r.status_code == 200


class TestAdminEndToEnd:
    """End-to-end integration tests for admin workflows."""

    def test_full_admin_workflow(self, client, admin_auth):
        """Test complete admin workflow."""
        # 1. Check health
        response = client.get("/api/v1/admin/health", headers=admin_auth)
        assert response.status_code == 200

        # 2. Create a game
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        game_id = response.json()["game_id"]

        # 3. Check it appears in sessions
        response = client.get("/api/v1/admin/sessions", headers=admin_auth)
        sessions = response.json()
        assert any(s["game_id"] == game_id for s in sessions)

        # 4. Get session detail
        response = client.get(f"/api/v1/admin/sessions/{game_id}/detail", headers=admin_auth)
        assert response.status_code == 200

        # 5. Force save
        response = client.post(f"/api/v1/admin/sessions/{game_id}/save", headers=admin_auth)
        assert response.status_code == 200

        # 6. Check database stats
        response = client.get("/api/v1/admin/database/stats", headers=admin_auth)
        stats = response.json()
        assert stats["total_games"] >= 1

        # 7. Delete session
        response = client.delete(f"/api/v1/admin/sessions/{game_id}", headers=admin_auth)
        assert response.status_code == 200

    def test_monitor_active_game(self, client, admin_auth):
        """Test monitoring an active game through admin endpoints."""
        # Create game with players
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        game_id = response.json()["game_id"]

        for i in range(4):
            client.post(
                f"/api/v1/game/{game_id}/join",
                json={"name": f"Player{i}", "is_bot": i >= 2}
            )

        # Monitor through admin
        # Check sessions list
        response = client.get("/api/v1/admin/sessions", headers=admin_auth)
        sessions = response.json()
        game_session = next(s for s in sessions if s["game_id"] == game_id)
        assert game_session["player_count"] == 4

        # Get detailed state
        response = client.get(f"/api/v1/admin/sessions/{game_id}/detail", headers=admin_auth)
        detail = response.json()
        assert detail["game_id"] == game_id

        # Check game history
        response = client.get("/api/v1/admin/games/history", headers=admin_auth)
        history = response.json()
        assert any(g["game_id"] == game_id for g in history)
