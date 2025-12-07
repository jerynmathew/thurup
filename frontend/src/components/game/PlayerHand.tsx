import React from 'react';
import { Card as CardType } from '../../types';
import { PlayingCard } from './PlayingCard';
import { NeonButton } from '../ui';

interface PlayerHandProps {
  cards: CardType[];
  playableCards?: string[]; // Card IDs that can be played
  onCardClick?: (card: CardType) => void;
  onRevealTrump?: () => void;
  canRevealTrump?: boolean;
  disabled?: boolean;
}

export const PlayerHand: React.FC<PlayerHandProps> = ({
  cards,
  playableCards = [],
  onCardClick,
  onRevealTrump,
  canRevealTrump = false,
  disabled = false,
}) => {
  if (cards.length === 0) {
    return (
      <div className="flex items-center justify-center py-8">
        <p className="text-slate-400">No cards in hand</p>
      </div>
    );
  }

  // Calculate rotation for fan effect
  const getRotation = (index: number, total: number) => {
    const spread = 40; // Total spread angle in degrees
    const start = -spread / 2;
    const step = spread / (total - 1 || 1);
    return start + step * index;
  };

  // Calculate vertical offset for fan arc
  const getTranslateY = (index: number, total: number) => {
    const mid = (total - 1) / 2;
    const dist = Math.abs(index - mid);
    return dist * 4; // 4px down per step from center
  };

  return (
    <div className="relative w-full h-48 flex justify-center items-end pb-6 overflow-visible">

      {/* Action Bar (Reveal Trump) */}
      {canRevealTrump && onRevealTrump && (
        <div className="absolute bottom-48 z-30 animate-bounce">
          <NeonButton
            variant="amber"
            glow
            onClick={onRevealTrump}
            className="flex items-center gap-2"
          >
            <span className="text-xl">🎴</span>
            <span>Reveal Trump</span>
          </NeonButton>
        </div>
      )}

      {/* Cards Container */}
      <div className="flex -space-x-12 hover:-space-x-8 transition-all duration-300 items-end mb-[-20px] hover:mb-0 px-12">
        {cards.map((card, index) => {
          const isPlayable = playableCards.includes(card.id);
          const canInteract = !disabled && isPlayable;
          const rotation = getRotation(index, cards.length);
          const translateY = getTranslateY(index, cards.length);

          return (
            <div
              key={card.id}
              className={`
                transform transition-all duration-200 origin-bottom
                ${canInteract ? 'cursor-pointer hover:-translate-y-12 hover:scale-110 hover:z-20' : 'opacity-70 grayscale cursor-not-allowed'}
              `}
              style={{
                zIndex: index,
                transform: `rotate(${rotation}deg) translateY(${translateY}px)`,
              }}
              onClick={() => canInteract && onCardClick?.(card)}
            >
              <PlayingCard
                card={card}
                isPlayable={canInteract}
                disabled={disabled || !isPlayable}
                className={isPlayable ? 'shadow-[0_0_15px_rgba(6,182,212,0.3)]' : ''}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
};
