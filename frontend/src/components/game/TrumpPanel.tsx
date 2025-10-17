/**
 * TrumpPanel component - handles trump suit selection.
 */

import { Suit } from '../../types';
import { Button, Card } from '../ui';

interface TrumpPanelProps {
  onSelectTrump: (suit: Suit) => void;
  disabled?: boolean;
  isMyTurn: boolean;
}

const SUITS: { suit: Suit; name: string; color: string }[] = [
  { suit: '♠', name: 'Spades', color: 'text-gray-900' },
  { suit: '♥', name: 'Hearts', color: 'text-red-600' },
  { suit: '♦', name: 'Diamonds', color: 'text-red-600' },
  { suit: '♣', name: 'Clubs', color: 'text-gray-900' },
];

export function TrumpPanel({ onSelectTrump, disabled = false, isMyTurn }: TrumpPanelProps) {
  const canSelect = isMyTurn && !disabled;

  return (
    <Card padding="md">
      <h3 className="text-lg font-semibold mb-4">Choose Trump</h3>

      {!isMyTurn && (
        <p className="text-slate-400 text-sm mb-4">
          Waiting for bid winner to choose trump...
        </p>
      )}

      {isMyTurn && (
        <>
          <p className="text-slate-300 text-sm mb-4">
            You won the bidding! Choose your trump suit:
          </p>

          <div className="grid grid-cols-2 gap-3">
            {SUITS.map(({ suit, name, color }) => (
              <button
                key={suit}
                onClick={() => onSelectTrump(suit)}
                disabled={!canSelect}
                className="flex flex-col items-center justify-center p-4 bg-slate-700/50 hover:bg-slate-600 rounded-lg border-2 border-slate-600 hover:border-primary-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span className={`text-5xl mb-2 ${color}`}>{suit}</span>
                <span className="text-slate-300 text-sm font-medium">{name}</span>
              </button>
            ))}
          </div>
        </>
      )}
    </Card>
  );
}
