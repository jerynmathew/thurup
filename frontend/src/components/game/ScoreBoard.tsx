/**
 * ScoreBoard component - displays current scores and game info.
 */

import { GameState, GamePhase } from '../../types';
import { Badge, Card } from '../ui';

interface ScoreBoardProps {
  gameState: GameState;
}

export function ScoreBoard({ gameState }: ScoreBoardProps) {
  const { mode, state, points_by_seat, bids, bid_winner, bid_value, trump, lead_suit, last_trick, short_code } = gameState;

  return (
    <Card padding="md" className="w-full max-w-md">
      <div className="space-y-4">
        {/* Game Code */}
        {short_code && (
          <div className="flex items-center justify-between bg-primary-500/10 border border-primary-500/30 rounded px-3 py-2">
            <span className="text-primary-300 text-sm font-semibold">Game Code</span>
            <span className="text-white font-mono font-bold text-lg">{short_code}</span>
          </div>
        )}

        {/* Game Mode */}
        <div className="flex items-center justify-between">
          <span className="text-slate-400 text-sm">Mode</span>
          <Badge variant="primary">{mode}</Badge>
        </div>

        {/* Game Phase */}
        <div className="flex items-center justify-between">
          <span className="text-slate-400 text-sm">Phase</span>
          <Badge variant="info">{getPhaseLabel(state)}</Badge>
        </div>

        {/* Trump Info */}
        {state !== 'lobby' && state !== 'dealing' && state !== 'bidding' && (
          <div className="flex items-center justify-between">
            <span className="text-slate-400 text-sm">Trump</span>
            {trump ? (
              <span className="text-3xl">{trump}</span>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-slate-500 text-sm italic">Hidden</span>
                <span className="text-2xl">🎴</span>
              </div>
            )}
          </div>
        )}

        {/* Lead Suit - during play phase */}
        {state === 'play' && lead_suit && (
          <div className="flex items-center justify-between bg-primary-500/10 border border-primary-500/30 rounded px-3 py-2">
            <span className="text-primary-300 text-sm font-semibold">Follow Suit</span>
            <span className="text-3xl">{lead_suit}</span>
          </div>
        )}

        {/* Last Trick - show the previous trick winner and cards */}
        {(state === 'play' || state === 'scoring' || state === 'round_end') && last_trick && (
          <div className="border-t border-slate-700 pt-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-slate-300 font-semibold text-sm">Last Trick</h3>
              <Badge variant="success">
                {gameState.players.find((p: any) => p.seat === last_trick.winner)?.name || `Seat ${last_trick.winner + 1}`} won
              </Badge>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(last_trick.cards)
                .sort(([a], [b]) => Number(a) - Number(b))
                .map(([seat, card]: [string, any]) => (
                  <div
                    key={seat}
                    className={`flex items-center justify-between bg-slate-700/50 rounded px-3 py-2 ${
                      Number(seat) === last_trick.winner ? 'ring-1 ring-green-500/50' : ''
                    }`}
                  >
                    <span className="text-slate-300 text-xs">
                      {gameState.players.find((p: any) => p.seat === Number(seat))?.name || `Seat ${Number(seat) + 1}`}
                    </span>
                    <span className={`text-lg font-semibold ${
                      card.suit === '♥' || card.suit === '♦' ? 'text-red-500' : 'text-slate-300'
                    }`}>
                      {card.rank}{card.suit}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Bidding Winner */}
        {bid_winner !== null && bid_winner !== undefined && (
          <div className="border-t border-slate-700 pt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-400 text-sm font-semibold">Bid Winner</span>
            </div>
            <div className="bg-slate-700/50 rounded px-3 py-2">
              <div className="flex items-center justify-between">
                <span className="text-white font-semibold">
                  {gameState.players.find((p: any) => p.seat === bid_winner)?.name || `Seat ${bid_winner + 1}`}
                </span>
                {bids && bids[bid_winner] !== undefined && bids[bid_winner] !== null && (
                  <Badge variant="success">{bids[bid_winner]} points</Badge>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Team Scores */}
        {points_by_seat && Object.keys(points_by_seat).length > 0 && (
          <div className="border-t border-slate-700 pt-4">
            <h3 className="text-slate-300 font-semibold mb-3">Team Scores</h3>
            {(() => {
              // Calculate team scores: Team 0 (even seats), Team 1 (odd seats)
              const teamScores = Object.entries(points_by_seat).reduce(
                (acc, [seat, score]) => {
                  const team = Number(seat) % 2 === 0 ? 0 : 1;
                  acc[team] += score;
                  return acc;
                },
                { 0: 0, 1: 0 }
              );

              // Determine winning team if bid exists
              const winningTeam = bid_winner !== null && bid_winner !== undefined
                ? Number(bid_winner) % 2 === 0 ? 0 : 1
                : null;

              const bidSuccess = winningTeam !== null && bid_value !== null
                ? teamScores[winningTeam] >= bid_value
                : null;

              return (
                <>
                  <div className="space-y-2">
                    {/* Team 1 (Even seats) */}
                    <div className={`flex items-center justify-between bg-slate-700/50 rounded px-4 py-3 ${
                      winningTeam === 0 ? 'ring-2 ring-primary-500/50' : ''
                    }`}>
                      <div>
                        <div className="text-white font-semibold">Team 1</div>
                        <div className="text-slate-400 text-xs">
                          {Object.keys(points_by_seat)
                            .filter(s => Number(s) % 2 === 0)
                            .map(s => gameState.players.find((p: any) => p.seat === Number(s))?.name || `Seat ${Number(s) + 1}`)
                            .join(', ')}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-white font-bold text-xl">{teamScores[0]}</div>
                        {winningTeam === 0 && bid_value !== null && (
                          <div className="text-xs text-slate-400">Target: {bid_value}</div>
                        )}
                      </div>
                    </div>

                    {/* Team 2 (Odd seats) */}
                    <div className={`flex items-center justify-between bg-slate-700/50 rounded px-4 py-3 ${
                      winningTeam === 1 ? 'ring-2 ring-primary-500/50' : ''
                    }`}>
                      <div>
                        <div className="text-white font-semibold">Team 2</div>
                        <div className="text-slate-400 text-xs">
                          {Object.keys(points_by_seat)
                            .filter(s => Number(s) % 2 === 1)
                            .map(s => gameState.players.find((p: any) => p.seat === Number(s))?.name || `Seat ${Number(s) + 1}`)
                            .join(', ')}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-white font-bold text-xl">{teamScores[1]}</div>
                        {winningTeam === 1 && bid_value !== null && (
                          <div className="text-xs text-slate-400">Target: {bid_value}</div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Bid outcome indicator */}
                  {bidSuccess !== null && state === 'scoring' && (
                    <div className={`mt-3 text-center py-2 rounded ${
                      bidSuccess
                        ? 'bg-green-500/20 text-green-300 border border-green-500/50'
                        : 'bg-red-500/20 text-red-300 border border-red-500/50'
                    }`}>
                      {bidSuccess
                        ? `Team ${winningTeam + 1} made their bid!`
                        : `Team ${winningTeam + 1} failed their bid`
                      }
                    </div>
                  )}
                </>
              );
            })()}
          </div>
        )}

        {/* Bids (during bidding phase) */}
        {state === 'bidding' && bids && Object.keys(bids).length > 0 && (
          <div className="border-t border-slate-700 pt-4">
            <h3 className="text-slate-300 font-semibold mb-3">Current Bids</h3>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(bids)
                .sort(([a], [b]) => Number(a) - Number(b))
                .map(([seat, bid]) => (
                  <div
                    key={seat}
                    className="flex items-center justify-between bg-slate-700/50 rounded px-3 py-2"
                  >
                    <span className="text-slate-300 text-sm">
                      {gameState.players.find((p: any) => p.seat === Number(seat))?.name || `Seat ${Number(seat) + 1}`}
                    </span>
                    <span className="text-white font-semibold">
                      {bid === -1 ? 'PASS' : bid === null ? '—' : bid}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

function getPhaseLabel(phase: GamePhase): string {
  switch (phase) {
    case 'lobby':
      return 'Lobby';
    case 'dealing':
      return 'Dealing';
    case 'bidding':
      return 'Bidding';
    case 'choose_trump':
      return 'Trump Choice';
    case 'play':
      return 'Playing';
    case 'scoring':
      return 'Scoring';
    case 'round_end':
      return 'Round End';
    default:
      return phase;
  }
}
