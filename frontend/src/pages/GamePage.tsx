/**
 * Game page - Main gameplay interface.
 * Shows the game board, player's hand, and handles real-time updates.
 */

import { useEffect, useCallback, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router';
import { useGameStore, selectMyHand, selectIsMyTurn, useUIStore } from '../stores';
import { GameBoard, PlayerHand, ScoreBoard, BiddingPanel, TrumpPanel, LobbyPanel, JoinGameModal, RoundHistory } from '../components/game';
import { Button, Loading } from '../components/ui';
import { useGame } from '../hooks/useGame';
import { gameApi } from '../api';
import { loadSession, saveSession, clearExpiredSessions } from '../utils/sessionManager';
import type { Suit, Card } from '../types';
export default function GamePage() {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const addToast = useUIStore((state) => state.addToast);

  // Read values from store - each primitive value separately to avoid object recreation
  const gameState = useGameStore((state) => state.gameState);
  const seat = useGameStore((state) => state.seat);
  const playerId = useGameStore((state) => state.playerId);
  const isConnected = useGameStore((state) => state.isConnected);
  const setGame = useGameStore((state) => state.setGame);

  // Join modal state
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [isJoining, setIsJoining] = useState(false);
  const [joinError, setJoinError] = useState<string | null>(null);
  const [sessionChecked, setSessionChecked] = useState(false);

  const myHand = useGameStore(selectMyHand);
  const isMyTurn = useGameStore(selectIsMyTurn);

  // Session management - check for existing session on mount FIRST
  useEffect(() => {
    if (!gameId) {
      navigate('/');
      return;
    }

    // Clear expired sessions on page load
    clearExpiredSessions();

    // Check if we have a session for this game
    const existingSession = loadSession(gameId);

    if (existingSession) {
      // Restore session from localStorage
      console.log('[GamePage] Restoring session from localStorage', existingSession);
      setGame(existingSession.gameId, existingSession.seat, existingSession.playerId);
      setSessionChecked(true);
    } else if (seat === null || playerId === null) {
      // No session and no player info - show join modal
      console.log('[GamePage] No session found, showing join modal');
      setShowJoinModal(true);
      setSessionChecked(true);
    } else {
      // Already have seat/playerId in store
      setSessionChecked(true);
    }
  }, [gameId, navigate, seat, playerId, setGame]);

  // Stable callback refs for useGame hook
  const handleConnect = useCallback(() => {
    console.log('Connected to game');
  }, []);

  const handleDisconnect = useCallback(() => {
    console.log('Disconnected from game');
  }, []);

  const handleError = useCallback((error: string) => {
    console.error('Game error:', error);
  }, []);

  // Initialize WebSocket connection AFTER session is checked
  const game = useGame({
    gameId: sessionChecked ? (gameId || '') : '', // Don't connect until session is checked
    seat,
    playerId,
    onConnect: handleConnect,
    onDisconnect: handleDisconnect,
    onError: handleError,
  });

  // Handle join game via modal
  const handleJoinGame = async (playerName: string) => {
    if (!gameId) return;

    setIsJoining(true);
    setJoinError(null);

    try {
      const response = await gameApi.joinGame(gameId, playerName);

      // Update store with player info
      setGame(gameId, response.seat, response.player_id);

      // Save session to localStorage
      saveSession({
        gameId,
        seat: response.seat,
        playerId: response.player_id,
        playerName,
        joinedAt: Date.now(),
      });

      addToast('Joined game successfully!', 'success');
      setShowJoinModal(false);
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to join game';
      setJoinError(errorMessage);
      addToast(errorMessage, 'error');
    } finally {
      setIsJoining(false);
    }
  };

  // Check if player can reveal trump
  const canRevealTrump =
    isMyTurn &&
    gameState?.state === 'play' &&
    gameState?.trump === null && // trump hidden
    gameState?.current_trick &&
    Object.keys(gameState.current_trick).length > 0 && // not leading
    gameState?.lead_suit &&
    !myHand.some((c) => c.suit === gameState.lead_suit); // can't follow suit

  // Calculate which cards are playable based on game rules
  const playableCards = useMemo(() => {
    if (!gameState || !isMyTurn || gameState.state !== 'play') {
      return [];
    }

    // If leading (no current trick), all cards playable
    if (!gameState.lead_suit) {
      return myHand.map((c) => c.id);
    }

    const leadSuit = gameState.lead_suit;
    const trumpSuit = gameState.trump; // Will be null if hidden

    // If can follow suit, must follow
    const followCards = myHand.filter((c) => c.suit === leadSuit);
    if (followCards.length > 0) {
      return followCards.map((c) => c.id);
    }

    // If trump revealed and have trump, must play trump
    if (trumpSuit) {
      const trumpCards = myHand.filter((c) => c.suit === trumpSuit);
      if (trumpCards.length > 0) {
        return trumpCards.map((c) => c.id);
      }
    }

    // Otherwise can play any card
    return myHand.map((c) => c.id);
  }, [myHand, isMyTurn, gameState]);

  if (!gameState) {
    return (
      <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center">
        <Loading text="Loading game..." />
      </div>
    );
  }

  const handleCardPlay = (card: Card) => {
    if (!game.isConnected) {
      console.warn('Cannot play card: Not connected');
      return;
    }
    game.playCard(card.id);
  };

  const handleBid = (value: number) => {
    if (!game.isConnected) {
      console.warn('Cannot bid: Not connected');
      return;
    }
    game.placeBid(value);
  };

  const handlePass = () => {
    if (!game.isConnected) {
      console.warn('Cannot pass: Not connected');
      return;
    }
    game.placeBid(-1); // -1 represents pass
  };

  const handleTrumpSelection = (suit: Suit) => {
    if (!game.isConnected) {
      console.warn('Cannot select trump: Not connected');
      return;
    }
    game.chooseTrump(suit);
  };

  const handleRevealTrump = () => {
    if (!game.isConnected) {
      console.warn('Cannot reveal trump: Not connected');
      return;
    }
    game.revealTrump();
  };

  const handleStartGame = async () => {
    if (!gameId) return;
    try {
      await gameApi.startGame(gameId);
      // Game state will be updated via WebSocket
    } catch (error: any) {
      console.error('Failed to start game:', error);
    }
  };

  const handleAddBot = async () => {
    if (!gameId) return;
    try {
      const botName = `Bot ${gameState?.players.length || 0 + 1}`;
      await gameApi.joinGame(gameId, botName, true);
      // Game state will be updated via WebSocket
    } catch (error: any) {
      console.error('Failed to add bot:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* Join Game Modal */}
      <JoinGameModal
        isOpen={showJoinModal}
        onClose={() => navigate('/')}
        onJoin={handleJoinGame}
        gameId={gameState?.short_code || gameId || ''}
        isLoading={isJoining}
        error={joinError}
      />

      <div className="container mx-auto px-4 py-4">
        {/* Header */}
        <div className="mb-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold">Game: {gameState?.short_code || gameId?.slice(0, 8) + '...'}</h1>
            {!isConnected && (
              <span className="px-3 py-1 bg-yellow-600/20 text-yellow-300 text-sm rounded-full border border-yellow-600/50">
                Disconnected
              </span>
            )}
            {isMyTurn && (
              <span className="px-3 py-1 bg-primary-500/20 text-primary-300 text-sm rounded-full border border-primary-500/50 animate-pulse">
                Your Turn
              </span>
            )}
          </div>
          <Button variant="secondary" onClick={() => navigate('/')}>
            Leave Game
          </Button>
        </div>

        {/* Main Game Area */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* Game Board - Main area */}
          <div className="lg:col-span-3">
            <div className="bg-slate-800/30 rounded-lg border border-slate-700 p-4">
              <GameBoard gameState={gameState} mySeat={seat} />
            </div>

            {/* Player Hand */}
            {myHand.length > 0 && (
              <div className="mt-4 bg-slate-800/30 rounded-lg border border-slate-700 p-4">
                <h3 className="text-lg font-semibold mb-4 text-center">Your Hand</h3>
                <PlayerHand
                  cards={myHand}
                  playableCards={playableCards}
                  onCardClick={handleCardPlay}
                  onRevealTrump={handleRevealTrump}
                  canRevealTrump={canRevealTrump}
                  disabled={!isMyTurn}
                />
              </div>
            )}
          </div>

          {/* Sidebar - Score and info */}
          <div className="lg:col-span-1 space-y-4">
            <ScoreBoard gameState={gameState} />

            {/* Round History */}
            <RoundHistory gameState={gameState} />

            {/* Action Panels based on game phase */}

            {/* Lobby - Waiting for players */}
            {gameState.state === 'lobby' && (
              <LobbyPanel
                gameState={gameState}
                onStartGame={handleStartGame}
                onAddBot={handleAddBot}
                isOwner={true}
              />
            )}

            {/* Bidding Phase */}
            {gameState.state === 'bidding' && (
              <BiddingPanel
                minBid={gameState.mode === '28' ? 16 : 32}
                currentHighBid={
                  Object.values(gameState.bids).reduce((max, bid) => {
                    if (bid === -1 || bid === null) return max;
                    return max === null ? bid : Math.max(max, bid);
                  }, null as number | null)
                }
                onBid={handleBid}
                onPass={handlePass}
                isMyTurn={isMyTurn}
              />
            )}

            {/* Trump Selection Phase */}
            {gameState.state === 'choose_trump' && (
              <TrumpPanel
                onSelectTrump={handleTrumpSelection}
                isMyTurn={seat === gameState.bid_winner}
              />
            )}

            {/* Scoring Phase - Start Next Round */}
            {gameState.state === 'scoring' && (
              <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-4">
                <h3 className="text-lg font-semibold mb-3 text-center">Round Complete!</h3>
                <p className="text-slate-400 text-sm mb-4 text-center">
                  Ready to start the next round?
                </p>
                <button
                  onClick={handleStartGame}
                  className="w-full py-3 bg-primary-500 hover:bg-primary-600 text-white font-semibold rounded-lg transition-colors"
                >
                  Start Next Round
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
