/**
 * Game page - Main gameplay interface.
 * Shows the game board, player's hand, and handles real-time updates.
 */

import { useEffect, useCallback, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router';
import { useGameStore, selectMyHand, selectIsMyTurn, useUIStore } from '../stores';
import { GameBoard, PlayerHand, ScoreBoard, BiddingPanel, TrumpPanel, LobbyPanel, JoinGameModal, RoundHistory } from '../components/game';
import { Button, Loading, GlassPanel, NeonButton } from '../components/ui';
import { useGame } from '../hooks/useGame';
import { gameApi } from '../api';
import { loadSession, saveSession, clearExpiredSessions } from '../utils/sessionManager';
import type { Suit, Card } from '../types';

export default function GamePage() {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const addToast = useUIStore((state) => state.addToast);

  // Read values from store
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

  // Session management
  useEffect(() => {
    if (!gameId) {
      navigate('/');
      return;
    }
    clearExpiredSessions();
    const existingSession = loadSession(gameId);

    if (existingSession) {
      setGame(existingSession.gameId, existingSession.seat, existingSession.playerId);
      setSessionChecked(true);
    } else if (seat === null || playerId === null) {
      setShowJoinModal(true);
      setSessionChecked(true);
    } else {
      setSessionChecked(true);
    }
  }, [gameId, navigate, seat, playerId, setGame]);

  // WebSocket connection
  const handleConnect = useCallback(() => console.log('Connected'), []);
  const handleDisconnect = useCallback(() => console.log('Disconnected'), []);
  const handleError = useCallback((error: string) => console.error('Game error:', error), []);

  const game = useGame({
    gameId: sessionChecked ? (gameId || '') : '',
    seat,
    playerId,
    onConnect: handleConnect,
    onDisconnect: handleDisconnect,
    onError: handleError,
  });

  // Handlers
  const handleJoinGame = async (playerName: string) => {
    if (!gameId) return;
    setIsJoining(true);
    setJoinError(null);
    try {
      const response = await gameApi.joinGame(gameId, playerName);
      setGame(gameId, response.seat, response.player_id);
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
      setJoinError(error.message || 'Failed to join game');
      addToast(error.message || 'Failed to join game', 'error');
    } finally {
      setIsJoining(false);
    }
  };

  const handleCardPlay = (card: Card) => {
    if (!game.isConnected) return;
    game.playCard(card.id);
  };

  const handleBid = (value: number) => {
    if (!game.isConnected) return;
    game.placeBid(value);
  };

  const handlePass = () => {
    if (!game.isConnected) return;
    game.placeBid(-1);
  };

  const handleTrumpSelection = (suit: Suit) => {
    if (!game.isConnected) return;
    game.chooseTrump(suit);
  };

  const handleRevealTrump = () => {
    if (!game.isConnected) return;
    game.revealTrump();
  };

  const handleStartGame = async () => {
    if (!gameId) return;
    try {
      await gameApi.startGame(gameId);
    } catch (error) {
      console.error('Failed to start game:', error);
    }
  };

  const handleAddBot = async () => {
    if (!gameId) return;
    try {
      const botName = `Bot ${gameState?.players.length || 0 + 1}`;
      await gameApi.joinGame(gameId, botName, true);
    } catch (error) {
      console.error('Failed to add bot:', error);
    }
  };

  // Logic for playable cards and trump reveal
  const canRevealTrump =
    isMyTurn &&
    gameState?.state === 'play' &&
    gameState?.trump === null &&
    gameState?.current_trick &&
    Object.keys(gameState.current_trick).length > 0 &&
    gameState?.lead_suit &&
    !myHand.some((c) => c.suit === gameState.lead_suit);

  const playableCards = useMemo(() => {
    if (!gameState || !isMyTurn || gameState.state !== 'play') return [];
    if (!gameState.lead_suit) return myHand.map((c) => c.id);

    const leadSuit = gameState.lead_suit;
    const trumpSuit = gameState.trump;
    const followCards = myHand.filter((c) => c.suit === leadSuit);

    if (followCards.length > 0) return followCards.map((c) => c.id);
    if (trumpSuit) {
      const trumpCards = myHand.filter((c) => c.suit === trumpSuit);
      if (trumpCards.length > 0) return trumpCards.map((c) => c.id);
    }
    return myHand.map((c) => c.id);
  }, [myHand, isMyTurn, gameState]);

  if (!gameState) {
    return (
      <div className="min-h-screen bg-dark-950 text-white flex items-center justify-center">
        <Loading text="Loading game..." />
      </div>
    );
  }

  return (
    <div className="h-screen w-full text-white overflow-hidden flex flex-col relative">

      {/* Join Game Modal */}
      <JoinGameModal
        isOpen={showJoinModal}
        onClose={() => navigate('/')}
        onJoin={handleJoinGame}
        gameId={gameState?.short_code || gameId || ''}
        isLoading={isJoining}
        error={joinError}
      />

      {/* Top Bar */}
      <div className="h-16 glass flex items-center justify-between px-6 z-20 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-neon-cyan to-neon-magenta flex items-center justify-center font-bold text-white">T</div>
          <span className="font-bold text-xl tracking-wide hidden sm:block">THURUP</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-white/10 border border-white/10 text-slate-300">
            #{gameState.short_code || gameId?.slice(0, 8)}
          </span>
        </div>

        <div className="flex items-center gap-4">
          {!isConnected && (
            <span className="px-3 py-1 bg-yellow-600/20 text-yellow-300 text-xs rounded-full border border-yellow-600/50">
              Disconnected
            </span>
          )}
          {isMyTurn && (
            <span className="px-3 py-1 bg-neon-cyan/20 text-neon-cyan text-xs rounded-full border border-neon-cyan/50 animate-pulse">
              Your Turn
            </span>
          )}
          <Button variant="secondary" onClick={() => navigate('/')} className="text-xs px-3 py-1">
            Leave
          </Button>
        </div>
      </div>

      {/* Main Game Area */}
      <div className="flex-1 relative flex items-center justify-center w-full overflow-hidden">

        {/* Floating Info Panel (Desktop) */}
        <div className="absolute top-4 left-4 z-20 hidden lg:block w-64 space-y-4">
          <GlassPanel className="p-4">
            <ScoreBoard gameState={gameState} />
          </GlassPanel>
          <GlassPanel className="p-4 max-h-48 overflow-y-auto">
            <RoundHistory gameState={gameState} />
          </GlassPanel>
        </div>

        {/* Floating Action Panels (Right Side) */}
        <div className="absolute top-4 right-4 z-20 w-64 space-y-4">
          {/* Lobby - Waiting for players */}
          {gameState.state === 'lobby' && (
            <GlassPanel className="p-4">
              <LobbyPanel
                gameState={gameState}
                onStartGame={handleStartGame}
                onAddBot={handleAddBot}
                isOwner={true}
              />
            </GlassPanel>
          )}

          {/* Bidding Phase */}
          {gameState.state === 'bidding' && (
            <GlassPanel className="p-4">
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
            </GlassPanel>
          )}

          {/* Trump Selection Phase */}
          {gameState.state === 'choose_trump' && (
            <GlassPanel className="p-4">
              <TrumpPanel
                onSelectTrump={handleTrumpSelection}
                isMyTurn={seat === gameState.bid_winner}
              />
            </GlassPanel>
          )}

          {/* Scoring Phase - Start Next Round */}
          {gameState.state === 'scoring' && (
            <GlassPanel className="p-4 text-center">
              <h3 className="text-lg font-semibold mb-3 text-white">Round Complete!</h3>
              <NeonButton
                variant="primary"
                onClick={handleStartGame}
                className="w-full"
              >
                Start Next Round
              </NeonButton>
            </GlassPanel>
          )}
        </div>

        {/* Game Board */}
        <div className="w-full h-full flex items-center justify-center">
          <GameBoard gameState={gameState} mySeat={seat} />
        </div>
      </div>

      {/* Player Hand (Fixed Bottom) */}
      <div className="shrink-0 z-30">
        {myHand.length > 0 && (
          <PlayerHand
            cards={myHand}
            playableCards={playableCards}
            onCardClick={handleCardPlay}
            onRevealTrump={handleRevealTrump}
            canRevealTrump={!!canRevealTrump}
            disabled={!isMyTurn}
          />
        )}
      </div>
    </div>
  );
}
