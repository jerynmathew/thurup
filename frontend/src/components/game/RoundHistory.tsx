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
    <Card padding="md" className="w-full max-w-md">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h2 className="text-white font-bold text-lg">Round History</h2>
          <Badge variant="info">{rounds_history.length} rounds</Badge>
        </div>

        {/* Round selector */}
        <div className="flex flex-wrap gap-2">
          {rounds_history.map((round) => (
            <button
              key={round.round_number}
              onClick={() => setSelectedRound(
                selectedRound === round.round_number ? null : round.round_number
              )}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                selectedRound === round.round_number
                  ? 'bg-primary-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              Round {round.round_number}
            </button>
          ))}
        </div>

        {/* Selected round details */}
        {selectedRoundData && (
          <div className="border-t border-slate-700 pt-4 space-y-4">
            {/* Round info */}
            <div className="grid grid-cols-2 gap-3">
              {/* Bid winner */}
              <div>
                <div className="text-slate-400 text-xs mb-1">Bid Winner</div>
                <div className="text-white font-medium">
                  {getPlayerName(players, selectedRoundData.bid_winner)}
                </div>
              </div>

              {/* Bid value */}
              <div>
                <div className="text-slate-400 text-xs mb-1">Bid Value</div>
                <div className="text-white font-medium">
                  {selectedRoundData.bid_value ?? 'N/A'}
                </div>
              </div>

              {/* Trump */}
              <div>
                <div className="text-slate-400 text-xs mb-1">Trump</div>
                <div className={`text-2xl ${
                  selectedRoundData.trump && getSuitColor(selectedRoundData.trump) === 'red'
                    ? 'text-red-500'
                    : 'text-white'
                }`}>
                  {selectedRoundData.trump ?? 'None'}
                </div>
              </div>

              {/* Dealer */}
              <div>
                <div className="text-slate-400 text-xs mb-1">Dealer</div>
                <div className="text-white font-medium">
                  {getPlayerName(players, selectedRoundData.dealer)}
                </div>
              </div>
            </div>

            {/* Team scores */}
            <div>
              <h3 className="text-slate-300 font-semibold mb-2 text-sm">Team Scores</h3>
              <div className="space-y-2">
                {/* Team 1 */}
                <div className={`flex items-center justify-between bg-slate-700/50 rounded px-4 py-3 ${
                  selectedRoundData.team_scores.bid_outcome?.winning_team === 0
                    ? 'ring-2 ring-primary-500/50'
                    : ''
                }`}>
                  <div>
                    <div className="text-white font-semibold">Team 1</div>
                    <div className="text-slate-400 text-xs">
                      Seats: {Object.keys(selectedRoundData.points_by_seat)
                        .filter(s => Number(s) % 2 === 0)
                        .map(s => Number(s) + 1)
                        .join(', ')}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-white font-bold text-xl">
                      {selectedRoundData.team_scores.team_points[0]}
                    </div>
                    {selectedRoundData.team_scores.bid_outcome?.winning_team === 0 && (
                      <div className="text-xs text-slate-400">
                        Target: {selectedRoundData.team_scores.bid_outcome.bid_value}
                      </div>
                    )}
                  </div>
                </div>

                {/* Team 2 */}
                <div className={`flex items-center justify-between bg-slate-700/50 rounded px-4 py-3 ${
                  selectedRoundData.team_scores.bid_outcome?.winning_team === 1
                    ? 'ring-2 ring-primary-500/50'
                    : ''
                }`}>
                  <div>
                    <div className="text-white font-semibold">Team 2</div>
                    <div className="text-slate-400 text-xs">
                      Seats: {Object.keys(selectedRoundData.points_by_seat)
                        .filter(s => Number(s) % 2 === 1)
                        .map(s => Number(s) + 1)
                        .join(', ')}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-white font-bold text-xl">
                      {selectedRoundData.team_scores.team_points[1]}
                    </div>
                    {selectedRoundData.team_scores.bid_outcome?.winning_team === 1 && (
                      <div className="text-xs text-slate-400">
                        Target: {selectedRoundData.team_scores.bid_outcome.bid_value}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Bid outcome */}
              {selectedRoundData.team_scores.bid_outcome && (
                <div className={`mt-3 text-center py-2 rounded text-sm font-medium ${
                  selectedRoundData.team_scores.bid_outcome.success
                    ? 'bg-green-500/20 text-green-300 border border-green-500/50'
                    : 'bg-red-500/20 text-red-300 border border-red-500/50'
                }`}>
                  {selectedRoundData.team_scores.bid_outcome.success
                    ? `Team ${selectedRoundData.team_scores.bid_outcome.winning_team + 1} made their bid!`
                    : `Team ${selectedRoundData.team_scores.bid_outcome.winning_team + 1} failed their bid`
                  }
                </div>
              )}
            </div>

            {/* Tricks won */}
            <div>
              <h3 className="text-slate-300 font-semibold mb-2 text-sm">
                Tricks Won: {selectedRoundData.captured_tricks.length}
              </h3>
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {selectedRoundData.captured_tricks.map((trick, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between bg-slate-700/30 rounded px-3 py-2 text-sm"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-slate-500 font-mono">#{idx + 1}</span>
                      <span className="text-white font-medium">
                        {getPlayerName(players, trick.winner)}
                      </span>
                    </div>
                    <Badge variant={trick.points > 0 ? 'success' : 'secondary'}>
                      {trick.points} pts
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

// Helper function to get player name from seat
function getPlayerName(players: PlayerInfo[], seat: number | null): string {
  if (seat === null) return 'N/A';
  const player = players.find(p => p.seat === seat);
  return player?.name || `Seat ${seat + 1}`;
}
