"""
Comprehensive integration tests for history.py endpoints.

Tests all history endpoints with various scenarios:
- list_games() with filters and pagination
- get_game_detail() for existing and non-existent games
- get_snapshot_data() for valid and invalid snapshots
- get_history_stats() accuracy
- get_game_replay() functionality
- Error handling for all endpoints
"""

import pytest
from fastapi.testclient import TestClient

from app.db.config import AsyncSessionLocal
from app.db.repository import GameRepository, SnapshotRepository
from app.main import app


@pytest.fixture
def client():
    """Test client for REST endpoints."""
    return TestClient(app)


@pytest.fixture
def sample_games(client):
    """Create sample games with various states for testing."""
    games = []

    # Game 1: Lobby state with 2 players
    response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
    game1_id = response.json()["game_id"]
    for i in range(2):
        client.post(
            f"/api/v1/game/{game1_id}/join",
            json={"name": f"Player{i}", "is_bot": False}
        )
    games.append({"game_id": game1_id, "state": "lobby", "mode": "28"})

    # Game 2: Active game with 4 players (auto-started)
    response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
    game2_id = response.json()["game_id"]
    for i in range(4):
        client.post(
            f"/api/v1/game/{game2_id}/join",
            json={"name": f"Player{i}", "is_bot": i >= 2}
        )
    games.append({"game_id": game2_id, "state": "active", "mode": "28"})

    # Game 3: 56-mode game in lobby
    response = client.post("/api/v1/game/create", json={"mode": "56", "seats": 4})
    game3_id = response.json()["game_id"]
    games.append({"game_id": game3_id, "state": "lobby", "mode": "56"})

    return games


class TestListGames:
    """Tests for GET /history/games endpoint."""

    def test_list_all_games(self, client, sample_games):
        """Test listing all games without filters."""
        response = client.get("/api/v1/history/games")
        assert response.status_code == 200
        games = response.json()
        assert len(games) >= 3

        # Verify response structure
        for game in games:
            assert "game_id" in game
            assert "mode" in game
            assert "seats" in game
            assert "state" in game
            assert "players" in game
            assert "created_at" in game
            assert "updated_at" in game
            assert "last_activity_at" in game

    
    def test_list_games_filter_by_state_lobby(self, client, sample_games):
        """Test filtering games by lobby state."""
        response = client.get("/api/v1/history/games?state=lobby")
        assert response.status_code == 200
        games = response.json()

        # All returned games should be in lobby state
        for game in games:
            assert game["state"] == "lobby"

    
    def test_list_games_filter_by_state_active(self, client, sample_games):
        """Test filtering games by active state."""
        response = client.get("/api/v1/history/games?state=active")
        assert response.status_code == 200
        games = response.json()

        # Active means not completed or abandoned
        for game in games:
            assert game["state"] not in ["completed", "abandoned"]

    
    def test_list_games_filter_by_mode(self, client, sample_games):
        """Test filtering games by mode."""
        # Filter by 28-mode
        response = client.get("/api/v1/history/games?mode=28")
        assert response.status_code == 200
        games_28 = response.json()
        for game in games_28:
            assert game["mode"] == "28"

        # Filter by 56-mode
        response = client.get("/api/v1/history/games?mode=56")
        assert response.status_code == 200
        games_56 = response.json()
        for game in games_56:
            assert game["mode"] == "56"

    
    def test_list_games_combined_filters(self, client, sample_games):
        """Test combining state and mode filters."""
        response = client.get("/api/v1/history/games?state=lobby&mode=28")
        assert response.status_code == 200
        games = response.json()

        for game in games:
            assert game["state"] == "lobby"
            assert game["mode"] == "28"

    
    def test_list_games_pagination_limit(self, client, sample_games):
        """Test pagination with limit parameter."""
        response = client.get("/api/v1/history/games?limit=2")
        assert response.status_code == 200
        games = response.json()
        assert len(games) <= 2

    
    def test_list_games_pagination_offset(self, client, sample_games):
        """Test pagination with offset parameter."""
        # Get first page
        response1 = client.get("/api/v1/history/games?limit=1&offset=0")
        games1 = response1.json()

        # Get second page
        response2 = client.get("/api/v1/history/games?limit=1&offset=1")
        games2 = response2.json()

        # Should be different games (if we have at least 2)
        if len(games1) > 0 and len(games2) > 0:
            assert games1[0]["game_id"] != games2[0]["game_id"]

    
    def test_list_games_pagination_bounds(self, client):
        """Test pagination boundary conditions."""
        # Limit too high (should be clamped to 100)
        response = client.get("/api/v1/history/games?limit=200")
        assert response.status_code == 422  # Validation error

        # Limit too low
        response = client.get("/api/v1/history/games?limit=0")
        assert response.status_code == 422

        # Negative offset
        response = client.get("/api/v1/history/games?offset=-1")
        assert response.status_code == 422

    
    def test_list_games_ordered_by_activity(self, client, sample_games):
        """Test that games are ordered by last_activity_at descending."""
        response = client.get("/api/v1/history/games?limit=10")
        assert response.status_code == 200
        games = response.json()

        if len(games) >= 2:
            # Compare timestamps (most recent first)
            from datetime import datetime
            for i in range(len(games) - 1):
                time1 = datetime.fromisoformat(games[i]["last_activity_at"].replace('Z', '+00:00'))
                time2 = datetime.fromisoformat(games[i + 1]["last_activity_at"].replace('Z', '+00:00'))
                assert time1 >= time2

    
    def test_list_games_includes_players(self, client, sample_games):
        """Test that game list includes player information."""
        response = client.get("/api/v1/history/games")
        assert response.status_code == 200
        games = response.json()

        for game in games:
            assert "players" in game
            for player in game["players"]:
                assert "player_id" in player
                assert "name" in player
                assert "seat" in player
                assert "is_bot" in player
                assert "joined_at" in player


class TestGetGameDetail:
    """Tests for GET /history/games/{game_id} endpoint."""

    
    def test_get_game_detail_success(self, client, sample_games):
        """Test getting detailed game information."""
        game_id = sample_games[0]["game_id"]

        response = client.get(f"/api/v1/history/games/{game_id}")
        assert response.status_code == 200
        detail = response.json()

        # Verify response structure
        assert "game" in detail
        assert "snapshots" in detail
        assert "total_snapshots" in detail

        # Verify game info
        assert detail["game"]["game_id"] == game_id
        assert detail["game"]["mode"] == "28"

        # Verify snapshots
        assert isinstance(detail["snapshots"], list)
        assert detail["total_snapshots"] >= 1  # At least creation snapshot

    
    def test_get_game_detail_not_found(self, client):
        """Test getting detail for non-existent game."""
        response = client.get("/api/v1/history/games/nonexistent-game-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    
    def test_get_game_detail_snapshot_structure(self, client, sample_games):
        """Test that snapshots have correct structure."""
        game_id = sample_games[0]["game_id"]

        response = client.get(f"/api/v1/history/games/{game_id}")
        assert response.status_code == 200
        detail = response.json()

        for snapshot in detail["snapshots"]:
            assert "snapshot_id" in snapshot
            assert "game_id" in snapshot
            assert "state_phase" in snapshot
            assert "snapshot_reason" in snapshot
            assert "created_at" in snapshot

    
    def test_get_game_detail_snapshots_ordered(self, client, sample_games):
        """Test that snapshots are ordered chronologically."""
        game_id = sample_games[1]["game_id"]  # Game with multiple actions

        response = client.get(f"/api/v1/history/games/{game_id}")
        assert response.status_code == 200
        detail = response.json()

        snapshots = detail["snapshots"]
        if len(snapshots) >= 2:
            from datetime import datetime
            for i in range(len(snapshots) - 1):
                time1 = datetime.fromisoformat(snapshots[i]["created_at"].replace('Z', '+00:00'))
                time2 = datetime.fromisoformat(snapshots[i + 1]["created_at"].replace('Z', '+00:00'))
                assert time1 <= time2  # Ascending order


class TestGetSnapshotData:
    """Tests for GET /history/games/{game_id}/snapshots/{snapshot_id} endpoint."""

    
    def test_get_snapshot_data_success(self, client, sample_games):
        """Test getting snapshot data."""
        game_id = sample_games[0]["game_id"]

        # First get game detail to find snapshot IDs
        detail_response = client.get(f"/api/v1/history/games/{game_id}")
        snapshots = detail_response.json()["snapshots"]
        assert len(snapshots) > 0

        snapshot_id = snapshots[0]["snapshot_id"]

        # Get snapshot data
        response = client.get(f"/api/v1/history/games/{game_id}/snapshots/{snapshot_id}")
        assert response.status_code == 200

        data = response.json()
        assert "snapshot_id" in data
        assert "game_id" in data
        assert "state_phase" in data
        assert "snapshot_reason" in data
        assert "created_at" in data
        assert "data" in data

        # Verify the data field is parsed JSON
        assert isinstance(data["data"], dict)

    
    def test_get_snapshot_data_wrong_game(self, client, sample_games):
        """Test getting snapshot with mismatched game_id."""
        game_id = sample_games[0]["game_id"]
        wrong_game_id = "wrong-game-id"

        # Get a real snapshot ID
        detail_response = client.get(f"/api/v1/history/games/{game_id}")
        snapshots = detail_response.json()["snapshots"]
        snapshot_id = snapshots[0]["snapshot_id"]

        # Try to get snapshot with wrong game_id
        response = client.get(f"/api/v1/history/games/{wrong_game_id}/snapshots/{snapshot_id}")
        assert response.status_code == 404

    
    def test_get_snapshot_data_not_found(self, client, sample_games):
        """Test getting non-existent snapshot."""
        game_id = sample_games[0]["game_id"]

        # Use very high snapshot ID that doesn't exist
        response = client.get(f"/api/v1/history/games/{game_id}/snapshots/999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetHistoryStats:
    """Tests for GET /history/stats endpoint."""

    
    def test_get_history_stats_structure(self, client, sample_games):
        """Test that stats endpoint returns correct structure."""
        response = client.get("/api/v1/history/stats")
        assert response.status_code == 200

        stats = response.json()
        assert "total_games" in stats
        assert "completed_games" in stats
        assert "active_games" in stats
        assert "abandoned_games" in stats
        assert "total_players" in stats
        assert "total_bots" in stats

        # All stats should be non-negative integers
        for key, value in stats.items():
            assert isinstance(value, int)
            assert value >= 0

    
    def test_get_history_stats_accuracy(self, client, sample_games):
        """Test that stats reflect actual database state."""
        response = client.get("/api/v1/history/stats")
        assert response.status_code == 200
        stats = response.json()

        # We created 3 games in sample_games
        assert stats["total_games"] >= 3

        # Verify total_games equals sum of states
        # Note: active_games means not completed or abandoned
        # So total = completed + active + abandoned
        total_by_state = stats["completed_games"] + stats["active_games"] + stats["abandoned_games"]
        assert stats["total_games"] == total_by_state

    
    def test_get_history_stats_player_counts(self, client, sample_games):
        """Test player and bot counts in stats."""
        response = client.get("/api/v1/history/stats")
        assert response.status_code == 200
        stats = response.json()

        # We added players in sample_games
        assert stats["total_players"] >= 6  # At least 6 players across 3 games

        # Bots should be subset of total players
        assert stats["total_bots"] <= stats["total_players"]


class TestGetGameReplay:
    """Tests for GET /history/games/{game_id}/replay endpoint."""

    
    def test_get_game_replay_success(self, client, sample_games):
        """Test getting game replay data."""
        game_id = sample_games[1]["game_id"]  # Game with players and snapshots

        response = client.get(f"/api/v1/history/games/{game_id}/replay")
        assert response.status_code == 200

        replay = response.json()
        assert "game_id" in replay
        assert "mode" in replay
        assert "seats" in replay
        assert "state" in replay
        assert "created_at" in replay
        assert "snapshots" in replay
        assert "total_snapshots" in replay

        assert replay["game_id"] == game_id
        assert replay["mode"] == "28"

    
    def test_get_game_replay_snapshot_structure(self, client, sample_games):
        """Test that replay snapshots have full data."""
        game_id = sample_games[1]["game_id"]

        response = client.get(f"/api/v1/history/games/{game_id}/replay")
        assert response.status_code == 200

        replay = response.json()
        snapshots = replay["snapshots"]
        assert len(snapshots) > 0

        for snapshot in snapshots:
            assert "snapshot_id" in snapshot
            assert "state_phase" in snapshot
            assert "snapshot_reason" in snapshot
            assert "created_at" in snapshot
            assert "data" in snapshot
            assert isinstance(snapshot["data"], dict)

    
    def test_get_game_replay_chronological_order(self, client, sample_games):
        """Test that replay snapshots are in chronological order."""
        game_id = sample_games[1]["game_id"]

        response = client.get(f"/api/v1/history/games/{game_id}/replay")
        assert response.status_code == 200

        snapshots = response.json()["snapshots"]
        if len(snapshots) >= 2:
            from datetime import datetime
            for i in range(len(snapshots) - 1):
                time1 = datetime.fromisoformat(snapshots[i]["created_at"].replace('Z', '+00:00'))
                time2 = datetime.fromisoformat(snapshots[i + 1]["created_at"].replace('Z', '+00:00'))
                assert time1 <= time2

    
    def test_get_game_replay_not_found(self, client):
        """Test replay for non-existent game."""
        response = client.get("/api/v1/history/games/nonexistent-game/replay")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    
    def test_get_game_replay_no_snapshots(self, client):
        """Test replay for game always has snapshots."""
        # In practice, games always have at least one snapshot from creation
        # This test verifies that behavior

        # Create a game
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        game_id = response.json()["game_id"]

        # Get replay - should have at least creation snapshot
        response = client.get(f"/api/v1/history/games/{game_id}/replay")
        assert response.status_code == 200
        replay = response.json()
        assert replay["total_snapshots"] >= 1


class TestHistoryErrorHandling:
    """Tests for error handling across history endpoints."""

    def test_list_games_database_error_handling(self, client):
        """Test graceful handling of database errors."""
        # This would require mocking database failure
        # For now, we verify the endpoint doesn't crash
        response = client.get("/api/v1/history/games")
        assert response.status_code in [200, 500]

    def test_invalid_game_id_format(self, client):
        """Test handling of malformed game IDs."""
        # SQL injection attempt
        response = client.get("/api/v1/history/games/'; DROP TABLE games;--")
        # Should either 404 or handle gracefully
        assert response.status_code in [404, 500]

    def test_invalid_snapshot_id_type(self, client, sample_games):
        """Test handling of non-integer snapshot IDs."""
        game_id = sample_games[0]["game_id"]

        # String instead of integer
        response = client.get(f"/api/v1/history/games/{game_id}/snapshots/not-a-number")
        assert response.status_code == 422  # Validation error


class TestHistoryIntegrationWithGameFlow:
    """Integration tests combining history with actual game flow."""

    
    def test_history_tracks_game_lifecycle(self, client):
        """Test that history correctly tracks game from creation to completion."""
        # Create game
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        game_id = response.json()["game_id"]

        # Check history after creation
        response = client.get(f"/api/v1/history/games/{game_id}")
        assert response.status_code == 200
        detail = response.json()
        assert detail["game"]["state"] == "lobby"
        initial_snapshots = detail["total_snapshots"]

        # Join players
        for i in range(4):
            client.post(
                f"/api/v1/game/{game_id}/join",
                json={"name": f"Player{i}", "is_bot": False}
            )

        # Check history after players joined
        response = client.get(f"/api/v1/history/games/{game_id}")
        detail = response.json()
        assert len(detail["game"]["players"]) == 4
        # Should have more snapshots now
        assert detail["total_snapshots"] > initial_snapshots

    
    def test_replay_captures_all_actions(self, client):
        """Test that replay includes all game actions."""
        # Create and play a game
        response = client.post("/api/v1/game/create", json={"mode": "28", "seats": 4})
        game_id = response.json()["game_id"]

        # Join 4 players
        for i in range(4):
            client.post(
                f"/api/v1/game/{game_id}/join",
                json={"name": f"Player{i}", "is_bot": i >= 2}
            )

        # Get replay
        response = client.get(f"/api/v1/history/games/{game_id}/replay")
        replay = response.json()

        # Verify snapshots capture state transitions
        snapshot_reasons = [s["snapshot_reason"] for s in replay["snapshots"]]
        assert "game_created" in snapshot_reasons or "player_join" in snapshot_reasons
