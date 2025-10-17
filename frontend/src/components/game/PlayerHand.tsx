/**
 * PlayerHand component - displays the player's cards.
 * Shows cards in a fan layout with hover effects.
 */

import { Card as CardType } from '../../types';
import { PlayingCard } from './PlayingCard';
import { Button } from '../ui';

interface PlayerHandProps {
  cards: CardType[];
  playableCards?: string[]; // Card IDs that can be played
  onCardClick?: (card: CardType) => void;
  onRevealTrump?: () => void;
  canRevealTrump?: boolean;
  disabled?: boolean;
}

export function PlayerHand({
  cards,
  playableCards = [],
  onCardClick,
  onRevealTrump,
  canRevealTrump = false,
  disabled = false,
}: PlayerHandProps) {
  if (cards.length === 0) {
    return (
      <div className="flex items-center justify-center py-8">
        <p className="text-slate-400">No cards in hand</p>
      </div>
    );
  }

  return (
    <div className="relative w-full py-4">
      {/* Reveal Trump Button */}
      {canRevealTrump && onRevealTrump && (
        <div className="mb-4 flex justify-center">
          <Button
            variant="primary"
            onClick={onRevealTrump}
            className="bg-yellow-600 hover:bg-yellow-700 border-2 border-yellow-500"
          >
            <span className="flex items-center gap-2">
              <span className="text-2xl">🎴</span>
              <span className="font-semibold">Reveal Trump</span>
            </span>
          </Button>
        </div>
      )}

      {/* Card container with fan layout */}
      <div className="flex items-end justify-center gap-2">
        {cards.map((card, index) => {
          const isPlayable = playableCards.includes(card.id);
          const canInteract = !disabled && isPlayable;

          return (
            <div
              key={card.id}
              className="transition-transform duration-200 hover:-translate-y-4"
              style={{
                zIndex: index,
              }}
            >
              <PlayingCard
                card={card}
                isPlayable={canInteract}
                onClick={() => canInteract && onCardClick?.(card)}
                disabled={disabled || !isPlayable}
              />
            </div>
          );
        })}
      </div>

      {/* Card count */}
      <div className="text-center mt-4">
        <p className="text-slate-400 text-sm">
          {cards.length} card{cards.length !== 1 ? 's' : ''}
          {playableCards.length > 0 && playableCards.length < cards.length && (
            <span className="ml-2 text-primary-400">
              ({playableCards.length} playable)
            </span>
          )}
        </p>
      </div>
    </div>
  );
}
