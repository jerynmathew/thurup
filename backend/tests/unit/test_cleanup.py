"""
Tests for game cleanup background task.

Tests initialization, lifecycle, cleanup logic, and error handling.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.db.cleanup import GameCleanupTask, start_cleanup_task, stop_cleanup_task


class TestGameCleanupTaskInit:
    """Tests for GameCleanupTask initialization."""

    def test_default_initialization(self):
        """Test initialization with default values."""
        task = GameCleanupTask()
        assert task.interval_minutes == 30
        assert task.lobby_hours == 1
        assert task.active_hours == 2
        assert task.completed_hours == 24
        assert task._task is None
        assert task._running is False

    def test_custom_initialization(self):
        """Test initialization with custom values."""
        task = GameCleanupTask(
            interval_minutes=15, lobby_hours=2, active_hours=4, completed_hours=48
        )
        assert task.interval_minutes == 15
        assert task.lobby_hours == 2
        assert task.active_hours == 4
        assert task.completed_hours == 48


class TestGameCleanupTaskLifecycle:
    """Tests for start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_task(self):
        """Test starting the cleanup task."""
        task = GameCleanupTask(interval_minutes=999)  # Very long interval to prevent actual cleanup

        await task.start()
        assert task._running is True
        assert task._task is not None
        assert not task._task.done()

        # Cleanup
        await task.stop()

    @pytest.mark.asyncio
    async def test_stop_task(self):
        """Test stopping the cleanup task."""
        task = GameCleanupTask(interval_minutes=999)

        await task.start()
        assert task._running is True

        await task.stop()
        assert task._running is False

        # Wait a moment for task cancellation to complete
        await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_start_already_running(self):
        """Test that starting an already-running task is a no-op."""
        task = GameCleanupTask(interval_minutes=999)

        await task.start()
        first_task = task._task

        # Try to start again
        await task.start()
        second_task = task._task

        # Should be the same task
        assert first_task is second_task

        await task.stop()

    @pytest.mark.asyncio
    async def test_stop_not_running(self):
        """Test that stopping a non-running task is safe."""
        task = GameCleanupTask()
        await task.stop()  # Should not raise

    @pytest.mark.asyncio
    async def test_task_cleanup_on_completion(self):
        """Test that task reference is cleaned up when task completes."""
        task = GameCleanupTask(interval_minutes=999)

        await task.start()
        assert task._task is not None

        await task.stop()
        await asyncio.sleep(0.1)  # Give time for cleanup

        # Task should be cancelled
        assert task._task.cancelled() or task._task.done()


class TestGameCleanupLogic:
    """Tests for cleanup logic."""

    @pytest.mark.asyncio
    async def test_run_cleanup_success(self):
        """Test successful cleanup run."""
        task = GameCleanupTask()

        # Mock the repository
        with patch("app.db.cleanup.AsyncSessionLocal") as mock_session_factory:
            mock_session = AsyncMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session

            mock_repo = MagicMock()
            mock_repo.cleanup_old_games = AsyncMock(return_value=5)  # 5 games deleted

            with patch("app.db.cleanup.GameRepository", return_value=mock_repo):
                await task._run_cleanup()

            # Verify cleanup was called with correct timeouts
            mock_repo.cleanup_old_games.assert_called_once_with(
                lobby_hours=task.lobby_hours,
                active_hours=task.active_hours,
                completed_hours=task.completed_hours,
            )

            # Verify commit was called
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_cleanup_no_deletions(self):
        """Test cleanup run with no games to delete."""
        task = GameCleanupTask()

        with patch("app.db.cleanup.AsyncSessionLocal") as mock_session_factory:
            mock_session = AsyncMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session

            mock_repo = MagicMock()
            mock_repo.cleanup_old_games = AsyncMock(return_value=0)  # No games deleted

            with patch("app.db.cleanup.GameRepository", return_value=mock_repo):
                await task._run_cleanup()

            mock_repo.cleanup_old_games.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_cleanup_database_error(self):
        """Test cleanup handles database errors gracefully."""
        task = GameCleanupTask()

        with patch("app.db.cleanup.AsyncSessionLocal") as mock_session_factory:
            mock_session = AsyncMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session

            mock_repo = MagicMock()
            mock_repo.cleanup_old_games = AsyncMock(side_effect=Exception("DB error"))

            with patch("app.db.cleanup.GameRepository", return_value=mock_repo):
                # Should raise the exception
                with pytest.raises(Exception, match="DB error"):
                    await task._run_cleanup()

            # Rollback should be called
            mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_loop_continues_after_error(self):
        """Test that cleanup loop continues after error."""
        task = GameCleanupTask(interval_minutes=0.001)  # Very short interval

        call_count = [0]

        async def mock_run_cleanup():
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("First call fails")
            # Second call succeeds

        task._run_cleanup = mock_run_cleanup

        await task.start()
        await asyncio.sleep(0.1)  # Let it run a couple times
        await task.stop()

        # Should have been called at least twice (once failed, once succeeded)
        assert call_count[0] >= 2

    @pytest.mark.asyncio
    async def test_cleanup_respects_interval(self):
        """Test that cleanup waits for interval between runs."""
        task = GameCleanupTask(interval_minutes=0.01)  # 0.6 seconds

        call_times = []

        async def mock_run_cleanup():
            call_times.append(asyncio.get_event_loop().time())

        task._run_cleanup = mock_run_cleanup

        await task.start()
        await asyncio.sleep(1.5)  # Wait for at least 2 cleanup cycles
        await task.stop()

        # Should have at least 2 cleanup calls
        assert len(call_times) >= 2

        if len(call_times) >= 2:
            # Check that interval is respected (allow some tolerance)
            interval = call_times[1] - call_times[0]
            expected_interval = 0.01 * 60  # 0.6 seconds
            assert 0.4 <= interval <= 1.0  # Allow some variance


class TestGameCleanupTaskIntegration:
    """Integration tests with real database (in-memory SQLite)."""

    @pytest.mark.asyncio
    async def test_cleanup_with_real_database(self):
        """Test cleanup with real database operations."""
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
        from sqlmodel import SQLModel

        from app.db.models import GameModel
        from app.db.repository import GameRepository

        # Create in-memory test database
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        # Add some test games
        async with async_session() as session:
            repo = GameRepository(session)

            # Use timezone-aware datetime
            from datetime import UTC
            now = datetime.now(UTC)

            # Create old lobby game (should be deleted)
            old_lobby = GameModel(
                id="old-lobby",
                short_code="old-lobby-11",
                mode="28",
                seats=4,
                min_bid=14,
                hidden_trump_mode="on_first_nonfollow",
                two_decks_for_56=False,
                state="lobby",
                created_at=now - timedelta(hours=2),
                updated_at=now - timedelta(hours=2),
                last_activity_at=now - timedelta(hours=2),
            )
            session.add(old_lobby)

            # Create recent lobby game (should be kept)
            recent_lobby = GameModel(
                id="recent-lobby",
                short_code="recent-lobby-22",
                mode="28",
                seats=4,
                min_bid=14,
                hidden_trump_mode="on_first_nonfollow",
                two_decks_for_56=False,
                state="lobby",
                created_at=now,
                updated_at=now,
                last_activity_at=now,
            )
            session.add(recent_lobby)

            # Create old completed game (should be deleted)
            old_completed = GameModel(
                id="old-completed",
                short_code="old-completed-33",
                mode="28",
                seats=4,
                min_bid=14,
                hidden_trump_mode="on_first_nonfollow",
                two_decks_for_56=False,
                state="completed",
                created_at=now - timedelta(days=2),
                updated_at=now - timedelta(days=2),
                last_activity_at=now - timedelta(days=2),
            )
            session.add(old_completed)

            await session.commit()

        # Run cleanup
        async with async_session() as session:
            repo = GameRepository(session)
            deleted = await repo.cleanup_old_games(
                lobby_hours=1, active_hours=2, completed_hours=24
            )
            await session.commit()

            # Should delete 2 games (old lobby and old completed)
            assert deleted == 2

            # Verify recent lobby still exists
            recent = await repo.get_game("recent-lobby")
            assert recent is not None

            # Verify old games are gone
            old_l = await repo.get_game("old-lobby")
            old_c = await repo.get_game("old-completed")
            assert old_l is None
            assert old_c is None

        await engine.dispose()


class TestGlobalCleanupFunctions:
    """Tests for global start/stop functions."""

    @pytest.mark.asyncio
    async def test_start_cleanup_task_global(self):
        """Test starting global cleanup task."""
        import app.db.cleanup as cleanup_module

        # Reset global state
        cleanup_module._cleanup_task = None

        await start_cleanup_task()
        assert cleanup_module._cleanup_task is not None
        assert cleanup_module._cleanup_task._running is True

        # Cleanup
        await stop_cleanup_task()

    @pytest.mark.asyncio
    async def test_stop_cleanup_task_global(self):
        """Test stopping global cleanup task."""
        import app.db.cleanup as cleanup_module

        cleanup_module._cleanup_task = None

        await start_cleanup_task()
        await stop_cleanup_task()

        assert cleanup_module._cleanup_task._running is False

    @pytest.mark.asyncio
    async def test_start_cleanup_task_idempotent(self):
        """Test that starting global task multiple times is safe."""
        import app.db.cleanup as cleanup_module

        cleanup_module._cleanup_task = None

        await start_cleanup_task()
        first_task = cleanup_module._cleanup_task

        await start_cleanup_task()  # Call again
        second_task = cleanup_module._cleanup_task

        # Should reuse existing task
        assert first_task is second_task

        await stop_cleanup_task()

    @pytest.mark.asyncio
    async def test_stop_cleanup_task_when_none(self):
        """Test stopping when no task exists."""
        import app.db.cleanup as cleanup_module

        cleanup_module._cleanup_task = None

        # Should not raise
        await stop_cleanup_task()
