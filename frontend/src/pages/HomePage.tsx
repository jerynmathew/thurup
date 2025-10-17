/**
 * Home page - Game lobby and creation.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router';
import { gameApi } from '../api';
import { useUIStore, useGameStore } from '../stores';
import { Button, Card, Input } from '../components/ui';
import { JoinGameModal } from '../components/game';
import { saveSession } from '../utils/sessionManager';
import type { GameMode } from '../types';

export default function HomePage() {
  const navigate = useNavigate();
  const addToast = useUIStore((state) => state.addToast);
  const setGame = useGameStore((state) => state.setGame);

  const [mode, setMode] = useState<GameMode>('28');
  const [seats, setSeats] = useState<4 | 6>(4);
  const [playerName, setPlayerName] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  // Join game modal state
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [gameCodeToJoin, setGameCodeToJoin] = useState('');
  const [gameCode, setGameCode] = useState('');
  const [isJoining, setIsJoining] = useState(false);
  const [joinError, setJoinError] = useState<string | null>(null);

  const handleCreateGame = async () => {
    if (!playerName.trim()) {
      addToast('Please enter a player name', 'warning');
      return;
    }

    setIsCreating(true);
    try {
      // Create game
      const createResponse = await gameApi.createGame(mode, seats);
      addToast(`Game created!`, 'success');

      // Auto-join the game
      const joinResponse = await gameApi.joinGame(createResponse.game_id, playerName.trim());

      // Store game information
      setGame(createResponse.game_id, joinResponse.seat, joinResponse.player_id);

      // Save session to localStorage
      saveSession({
        gameId: createResponse.game_id,
        seat: joinResponse.seat,
        playerId: joinResponse.player_id,
        playerName: playerName.trim(),
        joinedAt: Date.now(),
      });

      // Navigate to game page
      navigate(`/game/${createResponse.game_id}`);
    } catch (error: any) {
      addToast(error.message || 'Failed to create game', 'error');
    } finally {
      setIsCreating(false);
    }
  };

  // Show join modal with game code
  const handleShowJoinModal = () => {
    if (!gameCode.trim()) {
      addToast('Please enter a game code', 'warning');
      return;
    }
    setGameCodeToJoin(gameCode.trim());
    setJoinError(null);
    setShowJoinModal(true);
  };

  // Handle join via modal
  const handleJoinGame = async (playerName: string) => {
    setIsJoining(true);
    setJoinError(null);

    try {
      // Join the game using the short code or UUID
      const joinResponse = await gameApi.joinGame(gameCodeToJoin, playerName);

      // Store game information
      setGame(gameCodeToJoin, joinResponse.seat, joinResponse.player_id);

      // Save session to localStorage
      saveSession({
        gameId: gameCodeToJoin,
        seat: joinResponse.seat,
        playerId: joinResponse.player_id,
        playerName,
        joinedAt: Date.now(),
      });

      addToast(`Joined game successfully!`, 'success');
      setShowJoinModal(false);

      // Navigate to game page (using the code they entered, backend will resolve it)
      navigate(`/game/${gameCodeToJoin}`);
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to join game';
      setJoinError(errorMessage);
      addToast(errorMessage, 'error');
    } finally {
      setIsJoining(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* Join Game Modal */}
      <JoinGameModal
        isOpen={showJoinModal}
        onClose={() => setShowJoinModal(false)}
        onJoin={handleJoinGame}
        gameId={gameCodeToJoin}
        isLoading={isJoining}
        error={joinError}
      />

      <div className="container mx-auto px-4 py-16">
        <div className="max-w-2xl mx-auto text-center">
          <h1 className="text-6xl font-bold mb-4">Thurup</h1>
          <p className="text-xl text-slate-300 mb-12">
            The classic 28/56 card game
          </p>

          <Card padding="lg">
            <h2 className="text-2xl font-semibold mb-6">Create New Game</h2>

            <div className="space-y-6">
              {/* Player Name */}
              <Input
                label="Your Name"
                value={playerName}
                onChange={(e) => setPlayerName(e.target.value)}
                placeholder="Enter your name"
                fullWidth
              />

              {/* Game Mode Selection */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Game Mode
                </label>
                <div className="flex gap-4 justify-center">
                  <Button
                    variant={mode === '28' ? 'primary' : 'secondary'}
                    size="lg"
                    onClick={() => setMode('28')}
                  >
                    28 (4 Players)
                  </Button>
                  <Button
                    variant={mode === '56' ? 'primary' : 'secondary'}
                    size="lg"
                    onClick={() => setMode('56')}
                  >
                    56 (6 Players)
                  </Button>
                </div>
              </div>

              {/* Seats Selection (for 56 mode) */}
              {mode === '56' && (
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Number of Seats
                  </label>
                  <div className="flex gap-4 justify-center">
                    <Button
                      variant={seats === 4 ? 'primary' : 'secondary'}
                      size="lg"
                      onClick={() => setSeats(4)}
                    >
                      4 Seats
                    </Button>
                    <Button
                      variant={seats === 6 ? 'primary' : 'secondary'}
                      size="lg"
                      onClick={() => setSeats(6)}
                    >
                      6 Seats
                    </Button>
                  </div>
                </div>
              )}

              {/* Create Button */}
              <Button
                onClick={handleCreateGame}
                isLoading={isCreating}
                fullWidth
                size="lg"
              >
                Create Game
              </Button>
            </div>
          </Card>

          {/* Join Existing Game */}
          <Card padding="lg" className="mt-8">
            <h2 className="text-2xl font-semibold mb-6">Join Existing Game</h2>

            <div className="space-y-6">
              {/* Game Code Input */}
              <Input
                label="Game Code"
                value={gameCode}
                onChange={(e) => setGameCode(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && gameCode.trim()) {
                    handleShowJoinModal();
                  }
                }}
                placeholder="e.g., royal-turtle-65"
                fullWidth
              />

              <p className="text-sm text-slate-400 text-center -mt-4">
                Enter the game code shared by the host
              </p>

              {/* Join Button */}
              <Button
                onClick={handleShowJoinModal}
                fullWidth
                size="lg"
                variant="secondary"
              >
                Join Game
              </Button>
            </div>
          </Card>

          {/* Quick Links */}
          <div className="mt-12 flex gap-4 justify-center">
            <Button variant="secondary" size="lg" onClick={() => navigate('/history')}>
              Game History
            </Button>
            <Button variant="secondary" size="lg" onClick={() => navigate('/admin')}>
              Admin Panel
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
