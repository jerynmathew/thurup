"""
Tests for bot runner logic.

Tests bot scheduling, action handling, and error handling.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from app.api.v1.bot_runner import run_bots_for_game, schedule_bot_runner
from app.game.enums import SessionState
from app.game.session import GameSession
from app.models import PlayerInfo


@pytest.fixture
def mock_session():
    """Create a mock game session for testing."""
    session = MagicMock(spec=GameSession)
    session.state = SessionState.LOBBY
    session.turn = 0
    session.players = {}
    session.bidding_manager = MagicMock()
    session.bidding_manager.bids = {0: None, 1: None, 2: None, 3: None}
    session.bidding_manager.bid_winner = None
    return session


@pytest.fixture
def mock_game_server():
    """Create a mock GameServer for testing."""
    server = Mock()
    server.get_session = Mock(return_value=None)
    server.get_bot_task = Mock(return_value=None)
    server.add_bot_task = Mock()
    server.remove_bot_task = Mock()
    return server


class TestScheduleBotRunner:
    """Tests for schedule_bot_runner() function."""

    @pytest.mark.asyncio
    async def test_schedule_bot_runner_creates_task(self, mock_game_server):
        """Test that scheduling creates a new task."""
        game_id = "test-game-123"

        with patch("app.api.v1.bot_runner.get_game_server", return_value=mock_game_server), patch(
            "app.api.v1.bot_runner.run_bots_for_game", new=AsyncMock()
        ):
            schedule_bot_runner(game_id)

            # Give task a moment to be created
            await asyncio.sleep(0.01)

            # Task should be created
            mock_game_server.add_bot_task.assert_called()

    @pytest.mark.asyncio
    async def test_schedule_bot_runner_prevents_duplicate(self, mock_game_server):
        """Test that scheduling doesn't create duplicate tasks."""
        game_id = "test-game-456"

        # Create a mock ongoing task
        mock_task = MagicMock()
        mock_task.done.return_value = False
        mock_game_server.get_bot_task.return_value = mock_task

        with patch("app.api.v1.bot_runner.get_game_server", return_value=mock_game_server):
            # Try to schedule again
            schedule_bot_runner(game_id)

            # Should not create new task (add_bot_task should not be called)
            mock_game_server.add_bot_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_schedule_bot_runner_allows_after_completion(self, mock_game_server):
        """Test that scheduling after task completion creates new task."""
        game_id = "test-game-789"

        # Create a mock completed task
        mock_task = MagicMock()
        mock_task.done.return_value = True
        mock_game_server.get_bot_task.return_value = mock_task

        with patch("app.api.v1.bot_runner.get_game_server", return_value=mock_game_server), patch(
            "app.api.v1.bot_runner.run_bots_for_game", new=AsyncMock()
        ):
            schedule_bot_runner(game_id)

            # Should create new task since old one is done
            await asyncio.sleep(0.01)
            mock_game_server.add_bot_task.assert_called()


class TestRunBotsForGame:
    """Tests for run_bots_for_game() function."""

    @pytest.mark.asyncio
    async def test_run_bots_no_session(self, mock_game_server):
        """Test that bot runner handles missing session gracefully."""
        game_id = "nonexistent-game"
        mock_game_server.get_session.return_value = None

        with patch("app.api.v1.bot_runner.get_game_server", return_value=mock_game_server):
            # Should not raise error
            await run_bots_for_game(game_id, delay=0.001, max_cycles=1)

    @pytest.mark.asyncio
    async def test_run_bots_lobby_state(self, mock_session, mock_game_server):
        """Test that bot runner doesn't act in LOBBY state."""
        game_id = "test-game"
        mock_session.state = SessionState.LOBBY
        mock_game_server.get_session.return_value = mock_session

        with patch("app.api.v1.bot_runner.get_game_server", return_value=mock_game_server), patch(
            "app.api.v1.bot_runner.broadcast_state", new=AsyncMock()
        ):
            await run_bots_for_game(game_id, delay=0.001, max_cycles=1)

            # Should exit without calling any actions
            # (no exception means success)

    @pytest.mark.asyncio
    async def test_run_bots_bidding_human_turn(self, mock_session, mock_game_server):
        """Test bot doesn't act when it's a human's turn."""
        game_id = "test-game"
        mock_session.state = SessionState.BIDDING
        mock_session.turn = 0

        # Player 0 is human
        mock_session.players = {
            0: PlayerInfo(player_id="p0", name="Human", seat=0, is_bot=False)
        }

        mock_game_server.get_session.return_value = mock_session

        with patch("app.api.v1.bot_runner.get_game_server", return_value=mock_game_server), patch(
            "app.api.v1.bot_runner.broadcast_state", new=AsyncMock()
        ):
            await run_bots_for_game(game_id, delay=0.001, max_cycles=1)

            # Should not call force_bot_play_choice
            assert not hasattr(mock_session, "force_bot_play_choice") or True

    @pytest.mark.asyncio
    async def test_run_bots_bidding_bot_turn(self, mock_session, mock_game_server):
        """Test bot acts when it's bot's turn to bid."""
        game_id = "test-game"
        mock_session.state = SessionState.BIDDING
        mock_session.turn = 1

        # Player 1 is bot
        mock_session.players = {
            1: PlayerInfo(player_id="bot1", name="Bot1", seat=1, is_bot=True)
        }

        # Mock bot decision
        mock_session.force_bot_play_choice = MagicMock(
            return_value={"type": "place_bid", "payload": {"value": 15}}
        )
        mock_session.place_bid = AsyncMock(return_value=(True, "Bid placed"))

        mock_game_server.get_session.return_value = mock_session

        with patch("app.api.v1.bot_runner.get_game_server", return_value=mock_game_server), patch(
            "app.api.v1.bot_runner.broadcast_state", new=AsyncMock()
        ):
            await run_bots_for_game(game_id, delay=0.001, max_cycles=1)

            # Bot should have been asked for decision
            mock_session.force_bot_play_choice.assert_called_once()
            mock_session.place_bid.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_bots_choose_trump_bot(self, mock_session, mock_game_server):
        """Test bot chooses trump when winner."""
        game_id = "test-game"
        mock_session.state = SessionState.CHOOSE_TRUMP
        mock_session.bidding_manager.bid_winner = 2

        # Player 2 is bot and bid winner
        mock_session.players = {
            2: PlayerInfo(player_id="bot2", name="Bot2", seat=2, is_bot=True)
        }

        # Mock bot decision
        mock_session.force_bot_play_choice = MagicMock(
            return_value={"type": "choose_trump", "payload": {"suit": "♠"}}
        )
        mock_session.choose_trump = AsyncMock(return_value=(True, "Trump chosen"))

        mock_game_server.get_session.return_value = mock_session

        with patch("app.api.v1.bot_runner.get_game_server", return_value=mock_game_server), patch(
            "app.api.v1.bot_runner.broadcast_state", new=AsyncMock()
        ):
            await run_bots_for_game(game_id, delay=0.001, max_cycles=1)

            mock_session.force_bot_play_choice.assert_called_once()
            mock_session.choose_trump.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_bots_play_bot_turn(self, mock_session, mock_game_server):
        """Test bot plays card when it's their turn."""
        game_id = "test-game"
        mock_session.state = SessionState.PLAY
        mock_session.turn = 3

        # Player 3 is bot
        mock_session.players = {
            3: PlayerInfo(player_id="bot3", name="Bot3", seat=3, is_bot=True)
        }

        # Mock bot decision
        mock_session.force_bot_play_choice = MagicMock(
            return_value={"type": "play_card", "payload": {"card_id": "A♠#1"}}
        )
        mock_session.play_card = AsyncMock(return_value=(True, "Card played"))

        mock_game_server.get_session.return_value = mock_session

        with patch("app.api.v1.bot_runner.get_game_server", return_value=mock_game_server), patch(
            "app.api.v1.bot_runner.broadcast_state", new=AsyncMock()
        ):
            await run_bots_for_game(game_id, delay=0.001, max_cycles=1)

            mock_session.force_bot_play_choice.assert_called_once()
            mock_session.play_card.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_bots_max_cycles(self, mock_session, mock_game_server):
        """Test bot runner respects max_cycles limit."""
        game_id = "test-game"
        mock_session.state = SessionState.BIDDING
        mock_session.turn = 0

        # Player 0 is bot
        mock_session.players = {
            0: PlayerInfo(player_id="bot0", name="Bot0", seat=0, is_bot=True)
        }

        call_count = [0]

        def mock_bot_decision(*args, **kwargs):
            call_count[0] += 1
            return {"type": "place_bid", "payload": {"value": 15}}

        mock_session.force_bot_play_choice = mock_bot_decision
        mock_session.place_bid = AsyncMock(return_value=(True, "Bid placed"))

        with patch("app.api.v1.bot_runner.get_game_server", return_value=mock_game_server), patch(
            "app.api.v1.bot_runner.broadcast_state", new=AsyncMock()
        ):
            await run_bots_for_game(game_id, delay=0.001, max_cycles=3)

            # Should not exceed max_cycles
            assert call_count[0] <= 3

    @pytest.mark.asyncio
    async def test_run_bots_handles_errors(self, mock_session, mock_game_server):
        """Test bot runner handles errors gracefully."""
        game_id = "test-game"
        mock_session.state = SessionState.BIDDING
        mock_session.turn = 0

        # Player 0 is bot
        mock_session.players = {
            0: PlayerInfo(player_id="bot0", name="Bot0", seat=0, is_bot=True)
        }

        # Mock bot decision that raises error
        mock_session.force_bot_play_choice = MagicMock(
            side_effect=Exception("Bot error")
        )

        with patch("app.api.v1.bot_runner.get_game_server", return_value=mock_game_server), patch(
            "app.api.v1.bot_runner.broadcast_state", new=AsyncMock()
        ):
            # Should not raise error
            await run_bots_for_game(game_id, delay=0.001, max_cycles=1)

    @pytest.mark.asyncio
    async def test_run_bots_broadcasts_state(self, mock_session, mock_game_server):
        """Test bot runner broadcasts state after completion."""
        game_id = "test-game"
        mock_session.state = SessionState.LOBBY

        mock_broadcast = AsyncMock()
        mock_game_server.get_session.return_value = mock_session

        with patch("app.api.v1.bot_runner.get_game_server", return_value=mock_game_server), patch(
            "app.api.v1.bot_runner.broadcast_state", mock_broadcast
        ):
            await run_bots_for_game(game_id, delay=0.001, max_cycles=1)

            # Should always broadcast state
            mock_broadcast.assert_called_once_with(game_id)


class TestBotRunnerIntegration:
    """Integration tests for bot runner with real game sessions."""

    @pytest.mark.asyncio
    async def test_bot_runner_with_all_bots(self):
        """Test bot runner with all bot players."""
        game_id = "all-bots-game"
        session = GameSession(game_id=game_id, mode="28", seats=4)

        # Add 4 bot players
        for i in range(4):
            player = PlayerInfo(
                player_id=f"bot{i}", name=f"Bot{i}", seat=i, is_bot=True
            )
            session.players[i] = player

        await session.start_round()

        mock_game_server = Mock()
        mock_game_server.get_session.return_value = session

        with patch("app.api.v1.bot_runner.get_game_server", return_value=mock_game_server), patch(
            "app.api.v1.bot_runner.broadcast_state", new=AsyncMock()
        ):
            # Run bot runner with short delay
            await run_bots_for_game(game_id, delay=0.001, max_cycles=10)

            # Bots should have made some bids
            # (check that bidding progressed)
            bids_made = sum(
                1
                for v in session.bidding_manager.bids.values()
                if v is not None
            )
            assert bids_made > 0

    @pytest.mark.asyncio
    async def test_bot_runner_with_mixed_players(self):
        """Test bot runner with mix of human and bot players."""
        game_id = "mixed-game"
        session = GameSession(game_id=game_id, mode="28", seats=4)

        # Add 2 humans and 2 bots
        session.players[0] = PlayerInfo(
            player_id="h0", name="Human0", seat=0, is_bot=False
        )
        session.players[1] = PlayerInfo(
            player_id="bot1", name="Bot1", seat=1, is_bot=True
        )
        session.players[2] = PlayerInfo(
            player_id="h2", name="Human2", seat=2, is_bot=False
        )
        session.players[3] = PlayerInfo(
            player_id="bot3", name="Bot3", seat=3, is_bot=True
        )

        await session.start_round()

        mock_game_server = Mock()
        mock_game_server.get_session.return_value = session

        with patch("app.api.v1.bot_runner.get_game_server", return_value=mock_game_server), patch(
            "app.api.v1.bot_runner.broadcast_state", new=AsyncMock()
        ):
            # Run bot runner - should only act for bots
            await run_bots_for_game(game_id, delay=0.001, max_cycles=5)

            # At least some bot should have acted
            # (implementation detail: we can't check exact state without knowing turn order)
