/**
 * RoundHistory component - displays history of completed rounds
 */

import { useState } from 'react';
import { RoundHistory as RoundHistoryType, GameState, PlayerInfo, getSuitColor } from '../../types';
import { Card, Badge } from '../ui';

interface RoundHistoryProps {
  gameState: GameState;
}

export function RoundHistory({ gameState }: RoundHistoryProps) {
  const { rounds_history, players } = gameState;
  const [selectedRound, setSelectedRound] = useState<number | null>(null);

  if (!rounds_history || rounds_history.length === 0) {
    return null; // Don't render if no history
  }

  const selectedRoundData = selectedRound !== null
    ? rounds_history.find(r => r.round_number === selectedRound)
    : null;

  return (
    <div className="space-y-4 w-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-neon-cyan font-bold text-lg">History</h2>
        <span className="text-xs px-2 py-1 bg-white/10 rounded-full text-white">{rounds_history.length} rounds</span>
      </div>

      {/* Round selector */}
      <div className="flex flex-wrap gap-2">
        {rounds_history.map((round) => (
          <button
            key={round.round_number}
            onClick={() => setSelectedRound(
              selectedRound === round.round_number ? null : round.round_number
            )}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-colors border ${selectedRound === round.round_number
                ? 'bg-neon-cyan/20 text-neon-cyan border-neon-cyan/50'
                : 'bg-white/5 text-slate-400 border-white/10 hover:bg-white/10'
              }`}
          >
            R{round.round_number}
          </button>
        ))}
      </div>

      {/* Selected round details */}
      {selectedRoundData && (
        <div className="border-t border-white/10 pt-4 space-y-4 animate-fade-in">
          {/* Round info */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="bg-white/5 p-2 rounded border border-white/10">
              <div className="text-slate-400 text-[10px]">Bid Winner</div>
              <div className="text-white font-medium">
                {getPlayerName(players, selectedRoundData.bid_winner)}
              </div>
            </div>
            <div className="bg-white/5 p-2 rounded border border-white/10">
              <div className="text-slate-400 text-[10px]">Bid Value</div>
              <div className="text-neon-amber font-bold">
                {selectedRoundData.bid_value ?? 'N/A'}
              </div>
            </div>
            <div className="bg-white/5 p-2 rounded border border-white/10">
              <div className="text-slate-400 text-[10px]">Trump</div>
              <div className={`text-xl ${selectedRoundData.trump && getSuitColor(selectedRoundData.trump) === 'red'
                  ? 'text-red-500'
                  : 'text-white'
                }`}>
                {selectedRoundData.trump ?? 'None'}
              </div>
            </div>
            <div className="bg-white/5 p-2 rounded border border-white/10">
              <div className="text-slate-400 text-[10px]">Dealer</div>
              <div className="text-white font-medium">
                {getPlayerName(players, selectedRoundData.dealer)}
              </div>
            </div>
          </div>

          {/* Team scores */}
          <div>
            <h3 className="text-slate-300 font-semibold mb-2 text-xs">Scores</h3>
            <div className="space-y-2">
              {[0, 1].map(teamIdx => (
                <div key={teamIdx} className={`
                  flex items-center justify-between bg-white/5 rounded px-3 py-2 border border-white/10
                  ${selectedRoundData.team_scores.bid_outcome?.winning_team === teamIdx ? 'ring-1 ring-neon-cyan' : ''}
                `}>
                  <div>
                    <div className="text-white text-sm font-semibold">Team {teamIdx + 1}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-white font-bold">{selectedRoundData.team_scores.team_points[teamIdx as 0 | 1]}</div>
                    {selectedRoundData.team_scores.bid_outcome?.winning_team === teamIdx && (
                      <div className="text-[10px] text-neon-amber">
                        Target: {selectedRoundData.team_scores.bid_outcome.bid_value}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Helper function to get player name from seat
function getPlayerName(players: PlayerInfo[], seat: number | null): string {
  if (seat === null) return 'N/A';
  const player = players.find(p => p.seat === seat);
  return player?.name || `Seat ${seat + 1}`;
}
