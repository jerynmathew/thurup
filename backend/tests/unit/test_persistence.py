"""
Tests for session persistence layer.

Tests saving, loading, and deleting game sessions from database.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.db.persistence import SessionPersistence
from app.db.repository import GameRepository
from app.game.session import GameSession, HiddenTrumpMode, SessionState
from app.models import BidCmd, PlayerInfo


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session."""
    # Use in-memory SQLite for tests
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Create session factory
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def sample_session():
    """Create a sample game session for testing."""
    session = GameSession(
        game_id="test-game-123",
        mode="28",
        seats=4,
        hidden_trump_mode=HiddenTrumpMode.ON_FIRST_NONFOLLOW,
        min_bid=14,
        two_decks_for_56=False,
    )

    # Add players
    session.players[0] = PlayerInfo(player_id="p1", name="Alice", seat=0, is_bot=False)
    session.players[1] = PlayerInfo(player_id="p2", name="Bob", seat=1, is_bot=True)
    session.players[2] = PlayerInfo(
        player_id="p3", name="Charlie", seat=2, is_bot=False
    )
    session.players[3] = PlayerInfo(player_id="p4", name="Dave", seat=3, is_bot=False)

    return session


@pytest.mark.asyncio
async def test_save_new_session(db_session: AsyncSession, sample_session: GameSession):
    """Test saving a new game session."""
    persistence = SessionPersistence(db_session)

    # Save session
    success = await persistence.save_session(sample_session, snapshot_reason="test")
    assert success

    # Verify game was created
    repo = GameRepository(db_session)
    game = await repo.get_game(sample_session.id)
    assert game is not None
    assert game.id == "test-game-123"
    assert game.mode == "28"
    assert game.seats == 4
    assert game.state == SessionState.LOBBY.value


@pytest.mark.asyncio
async def test_load_session(db_session: AsyncSession, sample_session: GameSession):
    """Test loading a saved game session."""
    persistence = SessionPersistence(db_session)

    # Save session
    await persistence.save_session(sample_session, snapshot_reason="test")

    # Load it back
    loaded_session = await persistence.load_session(sample_session.id)
    assert loaded_session is not None
    assert loaded_session.id == sample_session.id
    assert loaded_session.mode == sample_session.mode
    assert loaded_session.seats == sample_session.seats
    assert len(loaded_session.players) == 4
    assert loaded_session.players[0].name == "Alice"
    assert loaded_session.players[1].is_bot


@pytest.mark.asyncio
async def test_save_session_with_game_state(
    db_session: AsyncSession, sample_session: GameSession
):
    """Test saving session with active game state."""
    persistence = SessionPersistence(db_session)

    # Start a round
    await sample_session.start_round()
    assert sample_session.state == SessionState.BIDDING
    # With dealer=0, leader=(0-1)%4=3 (clockwise direction)
    assert sample_session.turn == 3

    # Place some bids in clockwise order: 3, 2
    await sample_session.place_bid(3, BidCmd(value=15))
    await sample_session.place_bid(2, BidCmd(value=16))

    # Save session
    success = await persistence.save_session(sample_session, snapshot_reason="mid_game")
    assert success

    # Load it back
    loaded_session = await persistence.load_session(sample_session.id)
    assert loaded_session is not None
    assert loaded_session.state == SessionState.BIDDING
    assert loaded_session.bidding_manager.bids[3] == 15
    assert loaded_session.bidding_manager.bids[2] == 16
    assert loaded_session.bidding_manager.current_highest == 16
    assert len(loaded_session.hands[0]) > 0  # Cards were dealt


@pytest.mark.asyncio
async def test_update_existing_session(
    db_session: AsyncSession, sample_session: GameSession
):
    """Test updating an existing game session."""
    persistence = SessionPersistence(db_session)

    # Save initial state
    await persistence.save_session(sample_session, snapshot_reason="initial")

    # Modify session
    await sample_session.start_round()
    # With dealer=0, leader=(0-1)%4=3 (clockwise direction)
    assert sample_session.turn == 3
    await sample_session.place_bid(3, BidCmd(value=15))

    # Save updated state
    success = await persistence.save_session(sample_session, snapshot_reason="updated")
    assert success

    # Load and verify
    loaded_session = await persistence.load_session(sample_session.id)
    assert loaded_session is not None
    assert loaded_session.state == SessionState.BIDDING
    assert loaded_session.bidding_manager.bids[3] == 15


@pytest.mark.asyncio
async def test_delete_session(db_session: AsyncSession, sample_session: GameSession):
    """Test deleting a game session."""
    persistence = SessionPersistence(db_session)

    # Save session
    await persistence.save_session(sample_session, snapshot_reason="test")

    # Verify it exists
    loaded = await persistence.load_session(sample_session.id)
    assert loaded is not None

    # Delete it
    success = await persistence.delete_session(sample_session.id)
    assert success

    # Verify it's gone
    loaded = await persistence.load_session(sample_session.id)
    assert loaded is None


@pytest.mark.asyncio
async def test_load_nonexistent_session(db_session: AsyncSession):
    """Test loading a session that doesn't exist."""
    persistence = SessionPersistence(db_session)

    # Try to load non-existent session
    loaded = await persistence.load_session("nonexistent-id")
    assert loaded is None


@pytest.mark.asyncio
async def test_card_serialization(
    db_session: AsyncSession, sample_session: GameSession
):
    """Test that cards are properly serialized and deserialized."""
    persistence = SessionPersistence(db_session)

    # Deal cards
    await sample_session.start_round()

    # Save original hand
    original_hand = sample_session.hands[0].copy()
    original_card_uids = [c.uid for c in original_hand]

    # Save session
    await persistence.save_session(sample_session, snapshot_reason="test")

    # Load it back
    loaded_session = await persistence.load_session(sample_session.id)
    assert loaded_session is not None

    # Verify cards match
    loaded_hand = loaded_session.hands[0]
    loaded_card_uids = [c.uid for c in loaded_hand]

    assert len(loaded_hand) == len(original_hand)
    assert loaded_card_uids == original_card_uids

    # Verify card details
    for original, loaded in zip(original_hand, loaded_hand):
        assert loaded.suit == original.suit
        assert loaded.rank == original.rank
        assert loaded.uid == original.uid


@pytest.mark.asyncio
async def test_multiple_snapshots(
    db_session: AsyncSession, sample_session: GameSession
):
    """Test that multiple snapshots are created."""
    persistence = SessionPersistence(db_session)

    # Save initial state
    await persistence.save_session(sample_session, snapshot_reason="initial")

    # Modify and save again
    await sample_session.start_round()
    await persistence.save_session(sample_session, snapshot_reason="after_deal")

    # Place bids and save again (seat 3 is first to bid with clockwise direction)
    await sample_session.place_bid(3, BidCmd(value=15))
    await persistence.save_session(sample_session, snapshot_reason="after_bid")

    # Get all snapshots
    snapshots = await persistence.snapshot_repo.get_snapshots_for_game(
        sample_session.id, limit=10
    )
    assert len(snapshots) >= 3

    # Most recent should be the last one
    latest = snapshots[0]
    assert latest.snapshot_reason == "after_bid"
