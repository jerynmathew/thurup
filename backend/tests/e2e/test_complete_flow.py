"""
End-to-End tests for complete game flows.

Tests the entire system with real HTTP requests, simulating actual user workflows.
Requires the server to be running.
"""

import time

import pytest
import requests

BASE_URL = "http://localhost:8000/api/v1"


@pytest.fixture(scope="module")
def check_server():
    """Verify server is running before tests."""
    try:
        resp = requests.get("http://localhost:8000/", timeout=2)
        assert resp.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.skip("Server not running. Start with: uv run uvicorn app.main:app")


class TestCompleteGameFlow:
    """End-to-end test of complete game flow."""

    def test_full_game_lifecycle(self, check_server):
        """Test complete game from creation to history."""
        print("\n" + "=" * 60)
        print("E2E TEST: Complete Game Lifecycle")
        print("=" * 60)

        # Step 1: Create Game
        print("\n[1/15] Creating game...")
        resp = requests.post(f"{BASE_URL}/game/create", json={"mode": "28", "seats": 4})
        assert resp.status_code == 200
        game_id = resp.json()["game_id"]
        print(f"✅ Game created: {game_id}")

        # Step 2: Get Initial State
        print("\n[2/15] Getting initial game state...")
        resp = requests.get(f"{BASE_URL}/game/{game_id}")
        assert resp.status_code == 200
        state = resp.json()
        assert state["state"] == "lobby"
        assert state["mode"] == "28"
        assert state["seats"] == 4
        print(f"✅ State: {state['state']}, Mode: {state['mode']}")

        # Step 3: Join Players
        print("\n[3/15] Joining 4 players (2 humans, 2 bots)...")
        players = []
        for i in range(4):
            is_bot = i >= 2
            player_type = "BOT" if is_bot else "HUMAN"
            resp = requests.post(
                f"{BASE_URL}/game/{game_id}/join",
                json={"name": f"Player{i}", "is_bot": is_bot},
            )
            assert resp.status_code == 200
            player_data = resp.json()
            players.append(player_data)
            print(f"  Player {i} ({player_type}) - Seat: {player_data['seat']}")
        print(f"✅ All 4 players joined")

        # Step 4: Check Auto-Start
        print("\n[4/15] Checking if game auto-started...")
        time.sleep(1)  # Give bots time to act
        resp = requests.get(f"{BASE_URL}/game/{game_id}")
        assert resp.status_code == 200
        state = resp.json()
        assert state["state"] in ["bidding", "choose_trump", "play"]
        print(f"✅ Game auto-started - State: {state['state']}")

        # Step 5: List Games in History
        print("\n[5/15] Listing games in history...")
        resp = requests.get(f"{BASE_URL}/history/games?limit=5")
        assert resp.status_code == 200
        games = resp.json()
        assert len(games) > 0
        found = any(g["game_id"] == game_id for g in games)
        assert found
        print(f"✅ Found {len(games)} games, our game is listed")

        # Step 6: Filter by State
        print("\n[6/15] Filtering games by state...")
        resp = requests.get(f"{BASE_URL}/history/games?state=active&limit=10")
        assert resp.status_code == 200
        active_games = resp.json()
        print(f"✅ Found {len(active_games)} active games")

        # Step 7: Get Game Detail
        print("\n[7/15] Getting game detail with snapshots...")
        resp = requests.get(f"{BASE_URL}/history/games/{game_id}")
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["game"]["game_id"] == game_id
        assert detail["total_snapshots"] > 0
        print(f"✅ Game detail retrieved - {detail['total_snapshots']} snapshots")

        # Step 8: Get Specific Snapshot
        print("\n[8/15] Getting specific snapshot data...")
        if detail["total_snapshots"] > 0:
            snapshot_id = detail["snapshots"][0]["snapshot_id"]
            resp = requests.get(
                f"{BASE_URL}/history/games/{game_id}/snapshots/{snapshot_id}"
            )
            assert resp.status_code == 200
            snapshot = resp.json()
            assert "data" in snapshot
            print(
                f"✅ Snapshot {snapshot_id}: {snapshot['state_phase']} ({snapshot['snapshot_reason']})"
            )

        # Step 9: Get Full Replay
        print("\n[9/15] Getting full game replay...")
        resp = requests.get(f"{BASE_URL}/history/games/{game_id}/replay")
        assert resp.status_code == 200
        replay = resp.json()
        assert replay["game_id"] == game_id
        assert replay["total_snapshots"] > 0
        print(f"✅ Replay retrieved - {replay['total_snapshots']} snapshots")
        for i, snap in enumerate(replay["snapshots"][:5]):
            print(f"  {i+1}. {snap['snapshot_reason']} -> {snap['state_phase']}")

        # Step 10: History Stats
        print("\n[10/15] Getting history statistics...")
        resp = requests.get(f"{BASE_URL}/history/stats")
        assert resp.status_code == 200
        stats = resp.json()
        assert stats["total_games"] > 0
        print(f"✅ Stats: {stats['total_games']} games, {stats['total_players']} players")

        # Step 11: Admin Health Check
        print("\n[11/15] Admin health check...")
        resp = requests.get(f"{BASE_URL}/admin/health", auth=("admin", "changeme"))
        assert resp.status_code == 200
        health = resp.json()
        assert health["status"] in ["healthy", "degraded"]
        print(
            f"✅ Health: {health['status']} - {health['in_memory_sessions']} sessions"
        )

        # Step 12: Admin List Sessions
        print("\n[12/15] Admin listing sessions...")
        resp = requests.get(f"{BASE_URL}/admin/sessions", auth=("admin", "changeme"))
        assert resp.status_code == 200
        sessions = resp.json()
        assert len(sessions) > 0
        found = any(s["game_id"] == game_id for s in sessions)
        assert found
        print(f"✅ Found {len(sessions)} sessions in memory")

        # Step 13: Admin Session Detail
        print("\n[13/15] Admin getting session detail (all hands visible)...")
        resp = requests.get(
            f"{BASE_URL}/admin/sessions/{game_id}/detail", auth=("admin", "changeme")
        )
        assert resp.status_code == 200
        detail = resp.json()
        assert "all_hands" in detail
        print(f"✅ Admin can see all {len(detail['all_hands'])} player hands")

        # Step 14: Admin Database Stats
        print("\n[14/15] Admin getting database stats...")
        resp = requests.get(
            f"{BASE_URL}/admin/database/stats", auth=("admin", "changeme")
        )
        assert resp.status_code == 200
        db_stats = resp.json()
        print(
            f"✅ DB: {db_stats['total_games']} games, {db_stats['total_snapshots']} snapshots"
        )

        # Step 15: Admin Force Save
        print("\n[15/15] Admin forcing save...")
        resp = requests.post(
            f"{BASE_URL}/admin/sessions/{game_id}/save", auth=("admin", "changeme")
        )
        assert resp.status_code == 200
        print(f"✅ Save successful")

        print("\n" + "=" * 60)
        print("✅ E2E TEST COMPLETE - ALL STEPS PASSED!")
        print("=" * 60)
        print(f"\nTest Game ID: {game_id}")


class TestMultipleGames:
    """Test managing multiple games simultaneously."""

    def test_concurrent_games(self, check_server):
        """Create and manage multiple games at once."""
        print("\n" + "=" * 60)
        print("E2E TEST: Multiple Concurrent Games")
        print("=" * 60)

        game_ids = []

        # Create 3 games
        print("\n[1/3] Creating 3 games...")
        for i in range(3):
            resp = requests.post(
                f"{BASE_URL}/game/create", json={"mode": "28", "seats": 4}
            )
            assert resp.status_code == 200
            game_id = resp.json()["game_id"]
            game_ids.append(game_id)
            print(f"  Game {i+1}: {game_id[:8]}...")

        # Join players in each game
        print("\n[2/3] Joining players in all games...")
        for game_id in game_ids:
            for j in range(4):
                resp = requests.post(
                    f"{BASE_URL}/game/{game_id}/join",
                    json={"name": f"Player{j}", "is_bot": True},
                )
                assert resp.status_code == 200

        # Verify all games are active
        print("\n[3/3] Verifying all games are active...")
        time.sleep(1)
        for game_id in game_ids:
            resp = requests.get(f"{BASE_URL}/game/{game_id}")
            assert resp.status_code == 200
            state = resp.json()
            assert state["state"] != "lobby"
            print(f"  {game_id[:8]}... - State: {state['state']}")

        print(f"\n✅ Successfully managed {len(game_ids)} concurrent games")


class TestAuthenticationSecurity:
    """Test admin authentication and security."""

    def test_admin_requires_auth(self, check_server):
        """Verify admin endpoints require authentication."""
        print("\n" + "=" * 60)
        print("E2E TEST: Admin Authentication")
        print("=" * 60)

        # Test without auth
        print("\n[1/3] Testing without authentication...")
        resp = requests.get(f"{BASE_URL}/admin/health")
        assert resp.status_code == 401
        print("✅ Correctly rejected unauthenticated request")

        # Test with wrong credentials
        print("\n[2/3] Testing with wrong credentials...")
        resp = requests.get(f"{BASE_URL}/admin/health", auth=("wrong", "wrong"))
        assert resp.status_code == 401
        print("✅ Correctly rejected wrong credentials")

        # Test with correct credentials
        print("\n[3/3] Testing with correct credentials...")
        resp = requests.get(f"{BASE_URL}/admin/health", auth=("admin", "changeme"))
        assert resp.status_code == 200
        print("✅ Accepted correct credentials")


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_game_not_found(self, check_server):
        """Test 404 for non-existent game."""
        print("\n" + "=" * 60)
        print("E2E TEST: Error Handling")
        print("=" * 60)

        print("\n[1/3] Testing non-existent game...")
        resp = requests.get(f"{BASE_URL}/game/nonexistent-id")
        assert resp.status_code == 404
        print("✅ Correctly returned 404 for missing game")

        print("\n[2/3] Testing non-existent snapshot...")
        resp = requests.get(f"{BASE_URL}/history/games/fake-id/snapshots/99999")
        assert resp.status_code == 404
        print("✅ Correctly returned 404 for missing snapshot")

        print("\n[3/3] Testing invalid game creation...")
        resp = requests.post(
            f"{BASE_URL}/game/create", json={"mode": "invalid", "seats": 99}
        )
        assert resp.status_code in [400, 422]  # Validation error
        print("✅ Correctly rejected invalid game config")
