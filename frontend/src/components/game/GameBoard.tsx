/**
 * Main GameBoard component - circular arrangement of players.
 * Displays all players around a central table with the current trick.
 */

import { useMemo } from 'react';
import { Card as CardType, PlayerInfo, GameState } from '../../types';
import { Badge } from '../ui';
import { PlayingCard } from './PlayingCard';

interface GameBoardProps {
  gameState: GameState;
  mySeat: number | null;
}

export function GameBoard({ gameState, mySeat }: GameBoardProps) {
  const { seats, players, dealer, turn, leader, trump, current_trick, bid_winner } = gameState;

  // Calculate player positions in circular layout
  const playerPositions = useMemo(() => {
    if (mySeat === null) return [];

    const positions = [];
    const totalSeats = seats;

    // Position mapping for circular layout
    // Bottom: my seat, clockwise around the circle
    for (let i = 0; i < totalSeats; i++) {
      const seatNumber = (mySeat + i) % totalSeats;
      const player = players.find((p) => p.seat === seatNumber);

      // Calculate position based on index
      let position: 'bottom' | 'top' | 'left' | 'right';
      if (totalSeats === 4) {
        // 4 players: bottom, left, top, right
        position = ['bottom', 'left', 'top', 'right'][i] as typeof position;
      } else if (totalSeats === 6) {
        // 6 players: bottom, bottom-left, top-left, top, top-right, bottom-right
        position = i === 0 ? 'bottom' : i === 3 ? 'top' : i < 3 ? 'left' : 'right';
      } else {
        position = 'bottom';
      }

      positions.push({
        seat: seatNumber,
        player,
        position,
        isDealer: seatNumber === dealer,
        isTurn: seatNumber === turn,
        trickCard: current_trick?.[seatNumber],
      });
    }

    return positions;
  }, [gameState, mySeat, seats, players, dealer, turn, current_trick]);

  return (
    <div className="relative w-full h-full flex items-center justify-center p-4">
      {/* Container with aspect ratio */}
      <div className="relative w-full max-w-4xl aspect-square">
        {/* Central Table Area */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="relative w-2/5 aspect-square">
            {/* Center circle - game info */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="bg-slate-800/80 backdrop-blur-sm rounded-full w-full h-full flex flex-col items-center justify-center border-2 border-slate-600 p-4">
                {trump ? (
                  <div className="text-center">
                    <p className="text-slate-400 text-xs sm:text-sm mb-2">Trump</p>
                    <p className="text-4xl sm:text-6xl">{trump}</p>
                  </div>
                ) : gameState.state === 'play' ? (
                  <div className="text-center flex flex-col items-center gap-1">
                    <p className="text-slate-400 text-xs sm:text-sm">Trump</p>
                    <p className="text-3xl sm:text-5xl">🎴</p>
                    <p className="text-slate-500 text-[10px] sm:text-xs px-2">
                      {mySeat === bid_winner
                        ? "Play trump to reveal"
                        : "Hidden until revealed"}
                    </p>
                  </div>
                ) : (
                  <p className="text-slate-400 text-xs sm:text-sm text-center">Waiting for trump...</p>
                )}
              </div>
            </div>

            {/* Trick Cards - positioned around center */}
            {playerPositions.map((pos) => {
              if (!pos.trickCard) return null;

              const cardPosition = getCardPositionStyle(pos.position, seats);

              return (
                <div
                  key={pos.seat}
                  className="absolute"
                  style={cardPosition}
                >
                  <PlayingCard
                    card={pos.trickCard}
                    size="sm"
                  />
                </div>
              );
            })}
          </div>
        </div>

        {/* Player Seats - positioned around the board */}
        {playerPositions.map((pos) => (
          <div
            key={pos.seat}
            className="absolute"
            style={getSeatPositionStyle(pos.position, seats)}
          >
            <PlayerSeat
              seat={pos.seat}
              player={pos.player}
              isDealer={pos.isDealer}
              isTurn={pos.isTurn}
              isMe={pos.seat === mySeat}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

interface PlayerSeatProps {
  seat: number;
  player?: PlayerInfo;
  isDealer: boolean;
  isTurn: boolean;
  isMe: boolean;
}

function PlayerSeat({ seat, player, isDealer, isTurn, isMe }: PlayerSeatProps) {
  return (
    <div
      className={`
        relative px-3 sm:px-6 py-2 sm:py-3 rounded-lg backdrop-blur-sm border-2 transition-all
        ${isTurn ? 'bg-primary-500/20 border-primary-500 ring-2 ring-primary-300' : 'bg-slate-800/60 border-slate-600'}
        ${isMe ? 'border-yellow-500 ring-2 ring-yellow-300/50' : ''}
      `}
    >
      <div className="flex flex-col items-center gap-1 sm:gap-2 min-w-[80px] sm:min-w-[120px]">
        <div className="flex items-center gap-1 sm:gap-2">
          <span className="text-white font-semibold text-xs sm:text-base truncate max-w-[80px] sm:max-w-none">
            {player?.name || `Seat ${seat + 1}`}
          </span>
          {isMe && <Badge variant="warning" size="sm">You</Badge>}
        </div>

        <div className="flex gap-1 sm:gap-2 flex-wrap justify-center">
          {isDealer && <Badge variant="info" size="sm">Dealer</Badge>}
          {player?.is_bot && <Badge variant="default" size="sm">Bot</Badge>}
          {!player && <Badge variant="default" size="sm">Empty</Badge>}
        </div>

        {isTurn && (
          <div className="absolute -top-1 sm:-top-2 -right-1 sm:-right-2 w-2 h-2 sm:w-3 sm:h-3 bg-primary-500 rounded-full animate-pulse" />
        )}
      </div>
    </div>
  );
}

// Helper functions for positioning

function getSeatPositionStyle(
  position: 'bottom' | 'top' | 'left' | 'right',
  seats: number
): React.CSSProperties {
  const baseStyles: React.CSSProperties = {
    transform: 'translate(-50%, -50%)',
  };

  if (seats === 4) {
    switch (position) {
      case 'bottom':
        return { ...baseStyles, bottom: '5%', left: '50%' };
      case 'top':
        return { ...baseStyles, top: '5%', left: '50%' };
      case 'left':
        return { ...baseStyles, left: '5%', top: '50%' };
      case 'right':
        return { ...baseStyles, right: '5%', left: 'auto', top: '50%', transform: 'translate(50%, -50%)' };
    }
  } else if (seats === 6) {
    switch (position) {
      case 'bottom':
        return { ...baseStyles, bottom: '3%', left: '50%' };
      case 'top':
        return { ...baseStyles, top: '3%', left: '50%' };
      case 'left':
        return { ...baseStyles, left: '8%', top: position === 'left' ? '25%' : '75%' };
      case 'right':
        return { ...baseStyles, right: '8%', left: 'auto', top: position === 'right' ? '25%' : '75%', transform: 'translate(50%, -50%)' };
    }
  }

  return baseStyles;
}

function getCardPositionStyle(
  position: 'bottom' | 'top' | 'left' | 'right',
  seats: number
): React.CSSProperties {
  // Position cards inside the circle, near the edge but not overlapping center
  // Positive offset keeps them inside the circle boundary
  const offset = '15%';

  switch (position) {
    case 'bottom':
      return { bottom: offset, left: '50%', transform: 'translateX(-50%)' };
    case 'top':
      return { top: offset, left: '50%', transform: 'translateX(-50%)' };
    case 'left':
      return { left: offset, top: '50%', transform: 'translateY(-50%)' };
    case 'right':
      return { right: offset, top: '50%', transform: 'translateY(-50%)' };
  }
}

function getSuitColor(suit: string): string {
  switch (suit) {
    case '♥':
    case '♦':
      return 'text-red-600';
    case '♠':
    case '♣':
      return 'text-gray-900';
    default:
      return 'text-gray-900';
  }
}
