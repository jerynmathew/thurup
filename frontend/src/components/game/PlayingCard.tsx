/**
 * PlayingCard component - renders a single playing card with actual card images.
 */

import { Card } from '../../types';
import clsx from 'clsx';

interface PlayingCardProps {
  card: Card;
  isPlayable?: boolean;
  onClick?: () => void;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

/**
 * Convert card suit and rank to Deck of Cards API format.
 * Examples: A♠ → AS, 10♥ → 0H, K♦ → KD, J♣ → JC
 */
function getCardImageCode(card: Card): string {
  // Map suits to single letters
  const suitMap: Record<string, string> = {
    '♠': 'S',
    '♥': 'H',
    '♦': 'D',
    '♣': 'C',
  };

  // Map rank to API format (10 becomes 0)
  const rankCode = card.rank === '10' ? '0' : card.rank;
  const suitCode = suitMap[card.suit] || 'S';

  return `${rankCode}${suitCode}`;
}

export function PlayingCard({
  card,
  isPlayable = false,
  onClick,
  disabled = false,
  size = 'md',
}: PlayingCardProps) {
  const cardCode = getCardImageCode(card);
  const imageUrl = `https://deckofcardsapi.com/static/img/${cardCode}.png`;

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={clsx(
        'playing-card relative flex items-center justify-center',
        'rounded-lg shadow-lg border-2 transition-all duration-200',
        'overflow-hidden', // Ensure image doesn't overflow rounded corners
        {
          // Sizes (maintaining 2:3 aspect ratio for playing cards)
          'w-16 h-24': size === 'sm',
          'w-20 h-28': size === 'md',
          'w-24 h-32': size === 'lg',

          // States
          'border-gray-300': !isPlayable && !disabled,
          'border-primary-500 ring-2 ring-primary-300 cursor-pointer hover:scale-105 hover:shadow-xl':
            isPlayable && !disabled,
          'opacity-50 cursor-not-allowed': disabled,

          // Hover effects
          'hover:shadow-xl': !disabled,
        }
      )}
    >
      {/* Card Image */}
      <img
        src={imageUrl}
        alt={`${card.rank}${card.suit}`}
        className="w-full h-full object-cover"
        loading="lazy"
      />

      {/* Playable indicator */}
      {isPlayable && !disabled && (
        <div className="absolute -top-1 -right-1 w-3 h-3 bg-primary-500 rounded-full ring-2 ring-white" />
      )}

      {/* Card ID (for debugging - can be removed) */}
      {size === 'lg' && (
        <div className="absolute bottom-1 right-1 text-[8px] text-white bg-black/50 px-1 rounded">
          {card.id.split('#')[1] || ''}
        </div>
      )}
    </button>
  );
}
