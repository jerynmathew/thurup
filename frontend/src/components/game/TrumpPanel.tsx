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
    <div className="space-y-4">
      <h3 className="text-lg font-bold text-neon-magenta">Choose Trump</h3>

      {!isMyTurn && (
        <div className="p-3 bg-white/5 rounded border border-white/10 text-center">
          <p className="text-slate-400 text-sm animate-pulse">Waiting for bid winner...</p>
        </div>
      )}

      {isMyTurn && (
        <>
          <p className="text-slate-300 text-sm">
            You won the bidding! Choose your trump suit:
          </p>

          <div className="grid grid-cols-2 gap-3">
            {SUITS.map(({ suit, name, color }) => (
              <button
                key={suit}
                onClick={() => onSelectTrump(suit)}
                disabled={!canSelect}
                className="
                  flex flex-col items-center justify-center p-4 
                  bg-white/5 hover:bg-white/10 rounded-lg border border-white/10 
                  hover:border-neon-magenta hover:shadow-[0_0_15px_rgba(217,70,239,0.3)]
                  transition-all disabled:opacity-50 disabled:cursor-not-allowed
                "
              >
                <span className={`text-5xl mb-2 ${color}`}>{suit}</span>
                <span className="text-slate-300 text-sm font-medium">{name}</span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
