/**
 * Main GameBoard component - circular arrangement of players.
 * Displays all players around a central table with the current trick.
 */

import React, { useEffect, useState } from 'react';
import { GameState, Card } from '../../types';
import { PlayingCard } from './PlayingCard';

interface GameBoardProps {
  gameState: GameState;
  mySeat: number | null;
}

export const GameBoard: React.FC<GameBoardProps> = ({ gameState, mySeat }) => {
  const { players, current_trick, last_trick, dealer, turn, trump, trump_hidden } = gameState;
  const [displayTrick, setDisplayTrick] = useState<{ [seat: number]: Card } | null>(null);
  const [showingLastTrick, setShowingLastTrick] = useState(false);

  // Handle trick display logic (including the bug fix)
  useEffect(() => {
    const currentTrickEmpty = !current_trick || Object.keys(current_trick).length === 0;
    const hasLastTrick = last_trick && last_trick.cards && Object.keys(last_trick.cards).length > 0;

    if (currentTrickEmpty && hasLastTrick && !showingLastTrick) {
      // Show last_trick cards
      setDisplayTrick(last_trick.cards);
      setShowingLastTrick(true);

      // Clear after 2.5 seconds
      const timer = setTimeout(() => {
        setDisplayTrick(null);
        setShowingLastTrick(false);
      }, 2500);

      return () => clearTimeout(timer);
    } else if (!currentTrickEmpty && current_trick) {
      // Current trick is being played - show it
      setDisplayTrick(current_trick);
      setShowingLastTrick(false);
    } else if (!hasLastTrick && showingLastTrick) {
      // New round started (last_trick cleared) - clear display immediately
      setDisplayTrick(null);
      setShowingLastTrick(false);
    }
  }, [current_trick, last_trick, showingLastTrick]);

  // Helper to get relative position (bottom, left, top, right) based on my seat
  const getRelativePosition = (targetSeat: number) => {
    if (mySeat === null) return targetSeat; // Spectator view (absolute seats)
    const diff = (targetSeat - mySeat + 4) % 4;
    return diff; // 0=bottom, 1=left, 2=top, 3=right
  };

  // Helper to get tailwind classes for positioning
  const getPositionClasses = (position: number) => {
    switch (position) {
      case 0: return 'bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2'; // Bottom (Me)
      case 1: return 'top-1/2 left-0 -translate-x-1/2 -translate-y-1/2';   // Left
      case 2: return 'top-0 left-1/2 -translate-x-1/2 -translate-y-1/2';   // Top
      case 3: return 'top-1/2 right-0 translate-x-1/2 -translate-y-1/2';  // Right
      default: return '';
    }
  };

  // Helper for card positioning in the center trick
  const getCardPositionClasses = (position: number) => {
    switch (position) {
      case 0: return 'bottom-[35%] left-1/2 -translate-x-1/2 translate-y-1/2 z-10'; // Bottom card
      case 1: return 'top-1/2 left-[35%] -translate-x-1/2 -translate-y-1/2 -rotate-90'; // Left card
      case 2: return 'top-[35%] left-1/2 -translate-x-1/2 -translate-y-1/2'; // Top card
      case 3: return 'top-1/2 right-[35%] translate-x-1/2 -translate-y-1/2 rotate-90'; // Right card
      default: return '';
    }
  };

  return (
    <div className="relative w-full h-full flex items-center justify-center py-8">
      {/* Main Circular Table */}
      <div className="relative w-[90vw] max-w-[600px] aspect-square rounded-full border border-white/5 bg-white/[0.02] backdrop-blur-sm flex items-center justify-center transition-all duration-500">

        {/* Decorative Rings */}
        <div className="absolute inset-0 rounded-full border border-white/5 scale-75 pointer-events-none"></div>
        <div className="absolute inset-0 rounded-full border border-white/5 scale-50 pointer-events-none"></div>

        {/* Center Trick Area */}
        <div className="relative w-full h-full pointer-events-none">
          {displayTrick && Object.entries(displayTrick).map(([seatStr, card]) => {
            const seat = parseInt(seatStr);
            const relPos = getRelativePosition(seat);
            return (
              <div
                key={`card-${seat}`}
                className={`absolute transition-all duration-500 ${getCardPositionClasses(relPos)}`}
              >
                <PlayingCard
                  card={card}
                  size="md"
                  // className prop is now supported
                  className={showingLastTrick ? 'opacity-80 grayscale' : 'shadow-[0_0_20px_rgba(6,182,212,0.3)]'}
                />
              </div>
            );
          })}
        </div>

        {/* Players */}
        {players.map((player) => {
          const relPos = getRelativePosition(player.seat);
          const isDealer = player.seat === dealer;
          const isTurn = player.seat === turn;
          const isMe = player.seat === mySeat;

          return (
            <div
              key={player.seat}
              className={`absolute flex flex-col items-center gap-2 transition-all duration-500 ${getPositionClasses(relPos)}`}
            >
              {/* Avatar Ring */}
              <div className={`
                relative flex items-center justify-center rounded-full bg-slate-800 border-2 transition-all duration-300
                ${isMe ? 'w-14 h-14 md:w-16 md:h-16' : 'w-12 h-12 md:w-16 md:h-16'}
                ${isTurn ? 'border-neon-cyan shadow-neon-cyan scale-110' : 'border-white/10'}
                ${isDealer ? 'border-neon-amber shadow-neon-amber' : ''}
              `}>
                <span className="font-bold text-sm md:text-base text-white">
                  {player.name.charAt(0).toUpperCase()}
                </span>

                {/* Dealer Badge */}
                {isDealer && (
                  <div className="absolute -top-2 -right-2 bg-neon-amber text-black text-[10px] font-bold px-1.5 rounded-full">
                    D
                  </div>
                )}
              </div>

              {/* Name Tag */}
              <div className={`
                px-2 py-0.5 rounded-full backdrop-blur-md text-xs md:text-sm font-medium whitespace-nowrap
                ${isMe ? 'bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/30' : 'bg-black/50 text-slate-200'}
              `}>
                {player.name} {isMe && '(You)'}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

