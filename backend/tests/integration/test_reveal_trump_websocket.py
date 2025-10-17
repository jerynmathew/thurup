"""
Integration tests for reveal_trump WebSocket message handling.

Tests the full WebSocket flow for manual trump reveal.
"""

import pytest
from fastapi.testclient import TestClient

from app.api.v1.router import SESSIONS
from app.constants import Suit
from app.game.enums import SessionState
from app.game.session import GameSession
from app.main import app
from app.models import PlayerInfo


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def setup_game():
    """Set up a game session in play phase with hidden trump."""
    game_id = "test-game-reveal-trump"
    sess = GameSession(game_id=game_id, mode="28", seats=4)

    # Add players synchronously for fixture
    for i in range(4):
        player = PlayerInfo(
            player_id=f"player-{i}",
            name=f"Player {i}",
            seat=i,
            is_bot=False
        )
        sess.players[i] = player

    # Manually set up game state
    sess.state = SessionState.PLAY
    sess.leader = 0
    sess.turn = 0
    sess.trump = Suit.HEARTS.value
    sess.trump_hidden = True
    sess.bid_winner = 2
    sess.bid_value = 20

    # Give players some cards
    from app.game.rules import Card
    sess.hands = [
        [
            Card(suit=Suit.CLUBS.value, rank="7", uid="7♣#1"),
            Card(suit=Suit.CLUBS.value, rank="8", uid="8♣#1"),
            Card(suit=Suit.SPADES.value, rank="9", uid="9♠#1"),
        ],
        [
            Card(suit=Suit.DIAMONDS.value, rank="7", uid="7♦#1"),
            Card(suit=Suit.HEARTS.value, rank="8", uid="8♥#1"),
            Card(suit=Suit.SPADES.value, rank="10", uid="10♠#1"),
        ],
        [
            Card(suit=Suit.CLUBS.value, rank="J", uid="J♣#1"),
            Card(suit=Suit.HEARTS.value, rank="Q", uid="Q♥#1"),
        ],
        [
            Card(suit=Suit.CLUBS.value, rank="K", uid="K♣#1"),
            Card(suit=Suit.SPADES.value, rank="A", uid="A♠#1"),
        ],
    ]

    SESSIONS[game_id] = sess
    return game_id, sess


def collect_ws_messages_until(websocket, expected_types, max_messages=10, stop_condition=None):
    """
    Collect WebSocket messages until all expected types are received.

    Args:
        websocket: The WebSocket test session
        expected_types: Set of message types to look for
        max_messages: Maximum messages to read before stopping
        stop_condition: Optional function that returns True when we should stop

    Returns:
        List of received messages
    """
    messages = []
    for _ in range(max_messages):
        try:
            msg = websocket.receive_json()
            messages.append(msg)
            # Stop once we have all expected types
            received_types = {m["type"] for m in messages}
            if expected_types.issubset(received_types):
                # If we have a stop condition, check it
                if stop_condition is None or stop_condition(messages):
                    break
        except Exception:
            break
    return messages


class TestRevealTrumpWebSocket:
    """Integration tests for reveal_trump WebSocket messages."""

    def test_reveal_trump_websocket_success(self, client, setup_game):
        """Test successful trump reveal via WebSocket."""
        game_id, sess = setup_game

        # Player 0 leads with a club
        lead_card = sess.hands[0][0]  # 7♣
        sess.hands[0].remove(lead_card)
        sess.trick_manager.current_trick.append((0, lead_card))
        sess.turn = 1

        # Connect via WebSocket
        with client.websocket_connect(f"/api/v1/ws/game/{game_id}") as websocket:
            # Receive initial state
            data = websocket.receive_json()
            assert data["type"] == "state_snapshot"

            # Identify as player 1
            websocket.send_json({
                "type": "identify",
                "payload": {"seat": 1, "player_id": "player-1"}
            })

            # Receive identified state
            data = websocket.receive_json()
            assert data["type"] == "state_snapshot"

            # Send reveal_trump message
            websocket.send_json({
                "type": "reveal_trump",
                "payload": {"seat": 1}
            })

            # Collect messages until we get action_ok and a state_snapshot with trump revealed
            def has_revealed_trump(msgs):
                """Check if we have a state_snapshot with trump revealed."""
                for msg in msgs:
                    if msg["type"] == "state_snapshot" and msg["payload"].get("trump") is not None:
                        return True
                return False

            messages = collect_ws_messages_until(
                websocket,
                {"action_ok", "state_snapshot"},
                stop_condition=has_revealed_trump
            )

            # Verify we got the expected message types
            types = {msg["type"] for msg in messages}
            assert "action_ok" in types, f"Expected action_ok but got types: {types}"
            assert "state_snapshot" in types, f"Expected state_snapshot but got types: {types}"

            # Verify action_ok message content
            action_msg = next(msg for msg in messages if msg["type"] == "action_ok")
            assert "revealed" in action_msg["payload"]["message"].lower()

            # Verify state_snapshot shows trump is visible (find the one with trump revealed)
            state_msg = next(
                (msg for msg in messages if msg["type"] == "state_snapshot" and msg["payload"].get("trump") is not None),
                None
            )
            assert state_msg is not None, "No state_snapshot with revealed trump found"
            assert state_msg["payload"]["trump"] == Suit.HEARTS.value

        # Verify trump is revealed in session
        assert sess.trump_hidden is False

    def test_reveal_trump_websocket_not_your_turn(self, client, setup_game):
        """Test reveal_trump fails when not player's turn."""
        game_id, sess = setup_game

        # It's player 0's turn
        assert sess.turn == 0

        with client.websocket_connect(f"/api/v1/ws/game/{game_id}") as websocket:
            # Receive initial state
            websocket.receive_json()

            # Identify as player 1
            websocket.send_json({
                "type": "identify",
                "payload": {"seat": 1, "player_id": "player-1"}
            })

            # Receive identified state
            websocket.receive_json()

            # Try to reveal trump when it's not player 1's turn
            websocket.send_json({
                "type": "reveal_trump",
                "payload": {"seat": 1}
            })

            # Collect messages until we get action_failed
            messages = collect_ws_messages_until(websocket, {"action_failed"})

            # Verify we got action_failed
            types = {msg["type"] for msg in messages}
            assert "action_failed" in types, f"Expected action_failed but got types: {types}"

            # Verify action_failed message content
            action_msg = next(msg for msg in messages if msg["type"] == "action_failed")
            assert "not your turn" in action_msg["payload"]["message"].lower()

        # Trump should still be hidden
        assert sess.trump_hidden is True

    def test_reveal_trump_websocket_can_follow_suit(self, client, setup_game):
        """Test reveal_trump fails when player can follow suit."""
        game_id, sess = setup_game

        # Player 0 leads with a club
        lead_card = sess.hands[0][0]  # 7♣
        sess.hands[0].remove(lead_card)
        sess.trick_manager.current_trick.append((0, lead_card))
        sess.turn = 2

        # Player 2 has clubs (can follow suit)
        assert any(c.suit == Suit.CLUBS.value for c in sess.hands[2])

        with client.websocket_connect(f"/api/v1/ws/game/{game_id}") as websocket:
            websocket.receive_json()

            websocket.send_json({
                "type": "identify",
                "payload": {"seat": 2, "player_id": "player-2"}
            })

            websocket.receive_json()

            # Try to reveal trump
            websocket.send_json({
                "type": "reveal_trump",
                "payload": {"seat": 2}
            })

            # Collect messages until we get action_failed
            messages = collect_ws_messages_until(websocket, {"action_failed"})

            # Verify we got action_failed
            types = {msg["type"] for msg in messages}
            assert "action_failed" in types, f"Expected action_failed but got types: {types}"

            # Verify action_failed message content
            action_msg = next(msg for msg in messages if msg["type"] == "action_failed")
            assert "can follow suit" in action_msg["payload"]["message"].lower()

        assert sess.trump_hidden is True

    def test_reveal_trump_websocket_when_leading(self, client, setup_game):
        """Test reveal_trump fails when player is leading."""
        game_id, sess = setup_game

        # Player 0 is leading, no trick yet
        assert len(sess.trick_manager.current_trick) == 0
        assert sess.turn == 0

        with client.websocket_connect(f"/api/v1/ws/game/{game_id}") as websocket:
            websocket.receive_json()

            websocket.send_json({
                "type": "identify",
                "payload": {"seat": 0, "player_id": "player-0"}
            })

            websocket.receive_json()

            # Try to reveal trump when leading
            websocket.send_json({
                "type": "reveal_trump",
                "payload": {"seat": 0}
            })

            # Collect messages until we get action_failed
            messages = collect_ws_messages_until(websocket, {"action_failed"})

            # Verify we got action_failed
            types = {msg["type"] for msg in messages}
            assert "action_failed" in types, f"Expected action_failed but got types: {types}"

            # Verify action_failed message content
            action_msg = next(msg for msg in messages if msg["type"] == "action_failed")
            assert "cannot reveal" in action_msg["payload"]["message"].lower() or "leading" in action_msg["payload"]["message"].lower()

        assert sess.trump_hidden is True

    def test_reveal_trump_websocket_already_revealed(self, client, setup_game):
        """Test reveal_trump fails when trump already revealed."""
        game_id, sess = setup_game

        # Manually reveal trump
        sess.trump_hidden = False

        # Player 0 leads
        lead_card = sess.hands[0][0]
        sess.hands[0].remove(lead_card)
        sess.trick_manager.current_trick.append((0, lead_card))
        sess.turn = 1

        with client.websocket_connect(f"/api/v1/ws/game/{game_id}") as websocket:
            websocket.receive_json()

            websocket.send_json({
                "type": "identify",
                "payload": {"seat": 1, "player_id": "player-1"}
            })

            websocket.receive_json()

            # Try to reveal trump again
            websocket.send_json({
                "type": "reveal_trump",
                "payload": {"seat": 1}
            })

            # Collect messages until we get action_failed
            messages = collect_ws_messages_until(websocket, {"action_failed"})

            # Verify we got action_failed
            types = {msg["type"] for msg in messages}
            assert "action_failed" in types, f"Expected action_failed but got types: {types}"

            # Verify action_failed message content
            action_msg = next(msg for msg in messages if msg["type"] == "action_failed")
            assert "already revealed" in action_msg["payload"]["message"].lower()

    def test_reveal_trump_websocket_broadcasts_to_all(self, client, setup_game):
        """Test that trump reveal broadcasts updated state to all connected clients."""
        game_id, sess = setup_game

        # Player 0 leads with a club
        lead_card = sess.hands[0][0]
        sess.hands[0].remove(lead_card)
        sess.trick_manager.current_trick.append((0, lead_card))
        sess.turn = 1

        # Connect two clients
        with client.websocket_connect(f"/api/v1/ws/game/{game_id}") as ws1, \
             client.websocket_connect(f"/api/v1/ws/game/{game_id}") as ws2:

            # Both receive initial state
            ws1.receive_json()
            ws2.receive_json()

            # Identify clients
            ws1.send_json({
                "type": "identify",
                "payload": {"seat": 1, "player_id": "player-1"}
            })
            ws2.send_json({
                "type": "identify",
                "payload": {"seat": 2, "player_id": "player-2"}
            })

            ws1.receive_json()
            ws2.receive_json()

            # Player 1 reveals trump
            ws1.send_json({
                "type": "reveal_trump",
                "payload": {"seat": 1}
            })

            # WS1 receives messages (action_ok and state_snapshot with trump revealed)
            def has_revealed_trump(msgs):
                """Check if we have a state_snapshot with trump revealed."""
                for msg in msgs:
                    if msg["type"] == "state_snapshot" and msg["payload"].get("trump") is not None:
                        return True
                return False

            messages1 = collect_ws_messages_until(
                ws1,
                {"action_ok", "state_snapshot"},
                stop_condition=has_revealed_trump
            )
            types1 = {msg["type"] for msg in messages1}
            assert "action_ok" in types1, f"WS1 expected action_ok but got types: {types1}"
            assert "state_snapshot" in types1, f"WS1 expected state_snapshot but got types: {types1}"

            # WS2 receives state_snapshot from broadcast with trump revealed
            messages2 = collect_ws_messages_until(
                ws2,
                {"state_snapshot"},
                stop_condition=has_revealed_trump
            )
            types2 = {msg["type"] for msg in messages2}
            assert "state_snapshot" in types2, f"WS2 expected state_snapshot but got types: {types2}"

            # Verify state shows trump is visible (find ones with trump revealed)
            state_msg1 = next(
                (msg for msg in messages1 if msg["type"] == "state_snapshot" and msg["payload"].get("trump") is not None),
                None
            )
            state_msg2 = next(
                (msg for msg in messages2 if msg["type"] == "state_snapshot" and msg["payload"].get("trump") is not None),
                None
            )
            assert state_msg1 is not None, "WS1: No state_snapshot with revealed trump found"
            assert state_msg2 is not None, "WS2: No state_snapshot with revealed trump found"
            assert state_msg1["payload"]["trump"] == Suit.HEARTS.value
            assert state_msg2["payload"]["trump"] == Suit.HEARTS.value

    def test_reveal_trump_websocket_error_handling(self, client, setup_game):
        """Test error handling in reveal_trump WebSocket handler."""
        game_id, sess = setup_game

        with client.websocket_connect(f"/api/v1/ws/game/{game_id}") as websocket:
            websocket.receive_json()

            # Send malformed message (missing seat)
            websocket.send_json({
                "type": "reveal_trump",
                "payload": {}
            })

            # Should receive error or action_failed
            data = websocket.receive_json()
            assert data["type"] in ["error", "action_failed"]

    def test_reveal_trump_unknown_message_type(self, client, setup_game):
        """Test that unknown message types are handled gracefully."""
        game_id, _ = setup_game

        with client.websocket_connect(f"/api/v1/ws/game/{game_id}") as websocket:
            websocket.receive_json()

            # Send unknown message type
            websocket.send_json({
                "type": "unknown_action",
                "payload": {"seat": 0}
            })

            # Should receive error
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "unknown type" in data["payload"]["message"].lower()
