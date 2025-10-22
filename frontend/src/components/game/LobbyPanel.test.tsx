/**
 * Tests for LobbyPanel component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { LobbyPanel } from './LobbyPanel';
import type { GameState } from '../../types';

describe('LobbyPanel', () => {
  const mockGameState: GameState = {
    game_id: 'test-game-123',
    short_code: 'TEST-CODE',
    mode: '28',
    seats: 4,
    state: 'lobby',
    players: [
      { seat: 0, player_id: 'p1', name: 'Alice', is_bot: false },
      { seat: 1, player_id: 'p2', name: 'Bot 1', is_bot: true },
    ],
    dealer: 0,
    leader: 0,
  };

  const mockCallbacks = {
    onStartGame: vi.fn(),
    onAddBot: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // Mock window.location
    Object.defineProperty(window, 'location', {
      value: { origin: 'http://localhost:3000' },
      writable: true,
    });
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn(),
      },
    });
  });

  it('renders game info', () => {
    render(<LobbyPanel gameState={mockGameState} {...mockCallbacks} />);

    expect(screen.getByText('Game Lobby')).toBeInTheDocument();
    // Game ID is truncated to first 8 characters
    expect(screen.getByText('test-gam')).toBeInTheDocument();
    expect(screen.getByText('28')).toBeInTheDocument();
    expect(screen.getByText(/2 \/ 4/)).toBeInTheDocument();
  });

  it('displays all players', () => {
    render(<LobbyPanel gameState={mockGameState} {...mockCallbacks} />);

    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('Bot 1')).toBeInTheDocument();
  });

  it('shows bot indicator for bot players', () => {
    render(<LobbyPanel gameState={mockGameState} {...mockCallbacks} />);

    expect(screen.getByText('Bot Player')).toBeInTheDocument();
  });

  it('shows empty seats', () => {
    render(<LobbyPanel gameState={mockGameState} {...mockCallbacks} />);

    const emptySeats = screen.getAllByText('Waiting for player...');
    expect(emptySeats).toHaveLength(2); // 4 seats - 2 players = 2 empty
  });

  it('enables start button when enough players', () => {
    render(<LobbyPanel gameState={mockGameState} {...mockCallbacks} />);

    const startButton = screen.getByText('Start Game');
    expect(startButton).not.toBeDisabled();
  });

  it('disables start button when not enough players', () => {
    const singlePlayerState = {
      ...mockGameState,
      players: [mockGameState.players[0]],
    };

    render(<LobbyPanel gameState={singlePlayerState} {...mockCallbacks} />);

    const startButton = screen.getByText(/Need 1 more player/);
    expect(startButton).toBeDisabled();
  });

  it('calls onStartGame when start button clicked', () => {
    render(<LobbyPanel gameState={mockGameState} {...mockCallbacks} />);

    const startButton = screen.getByText('Start Game');
    fireEvent.click(startButton);

    expect(mockCallbacks.onStartGame).toHaveBeenCalledOnce();
  });

  it('shows add bot button when seats available', () => {
    render(<LobbyPanel gameState={mockGameState} {...mockCallbacks} />);

    expect(screen.getByText('Add Bot Player')).toBeInTheDocument();
  });

  it('hides add bot button when lobby full', () => {
    const fullLobbyState = {
      ...mockGameState,
      players: [
        { seat: 0, player_id: 'p1', name: 'Alice', is_bot: false },
        { seat: 1, player_id: 'p2', name: 'Bob', is_bot: false },
        { seat: 2, player_id: 'p3', name: 'Charlie', is_bot: false },
        { seat: 3, player_id: 'p4', name: 'David', is_bot: false },
      ],
    };

    render(<LobbyPanel gameState={fullLobbyState} {...mockCallbacks} />);

    expect(screen.queryByText('Add Bot Player')).not.toBeInTheDocument();
  });

  it('calls onAddBot when add bot button clicked', () => {
    render(<LobbyPanel gameState={mockGameState} {...mockCallbacks} />);

    const addBotButton = screen.getByText('Add Bot Player');
    fireEvent.click(addBotButton);

    expect(mockCallbacks.onAddBot).toHaveBeenCalledOnce();
  });

  it('shows share URL with game ID', () => {
    render(<LobbyPanel gameState={mockGameState} {...mockCallbacks} />);

    const urlInput = screen.getByDisplayValue('http://localhost:3000/game/test-game-123');
    expect(urlInput).toBeInTheDocument();
  });

  it('copies URL to clipboard when copy button clicked', () => {
    render(<LobbyPanel gameState={mockGameState} {...mockCallbacks} />);

    const copyButton = screen.getByText('Copy');
    fireEvent.click(copyButton);

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      'http://localhost:3000/game/test-game-123'
    );
  });

  it('hides actions when not owner', () => {
    render(<LobbyPanel gameState={mockGameState} {...mockCallbacks} isOwner={false} />);

    expect(screen.queryByText('Start Game')).not.toBeInTheDocument();
    expect(screen.queryByText('Add Bot Player')).not.toBeInTheDocument();
  });

  it('shows actions when is owner', () => {
    render(<LobbyPanel gameState={mockGameState} {...mockCallbacks} isOwner={true} />);

    expect(screen.getByText('Start Game')).toBeInTheDocument();
  });

  it('shows share message when not enough players', () => {
    const singlePlayerState = {
      ...mockGameState,
      players: [mockGameState.players[0]],
    };

    render(<LobbyPanel gameState={singlePlayerState} {...mockCallbacks} />);

    expect(screen.getByText(/Share the game ID with friends/)).toBeInTheDocument();
  });

  it('displays player seat numbers correctly', () => {
    render(<LobbyPanel gameState={mockGameState} {...mockCallbacks} />);

    expect(screen.getByText('0')).toBeInTheDocument(); // Alice's seat
    expect(screen.getByText('1')).toBeInTheDocument(); // Bot 1's seat
  });

  it('displays empty seat numbers correctly', () => {
    render(<LobbyPanel gameState={mockGameState} {...mockCallbacks} />);

    expect(screen.getByText('2')).toBeInTheDocument(); // First empty seat
    expect(screen.getByText('3')).toBeInTheDocument(); // Second empty seat
  });
});
