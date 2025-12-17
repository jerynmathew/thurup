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
    <div className="space-y-4 w-full">
      <h3 className="text-lg font-bold text-neon-cyan mb-2">Game Info</h3>

      <div className="space-y-2 text-sm">
        {/* Game Code */}
        {short_code && (
          <div className="flex items-center justify-between bg-white/5 px-3 py-2 rounded border border-white/10">
            <span className="text-slate-400">Code</span>
            <span className="text-neon-magenta font-mono font-bold">{short_code}</span>
          </div>
        )}

        {/* Game Mode & Phase */}
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-white/5 px-3 py-2 rounded border border-white/10">
            <div className="text-slate-400 text-xs">Mode</div>
            <div className="text-white font-semibold">{mode}</div>
          </div>
          <div className="bg-white/5 px-3 py-2 rounded border border-white/10">
            <div className="text-slate-400 text-xs">Phase</div>
            <div className="text-neon-amber font-semibold">{getPhaseLabel(state)}</div>
          </div>
        </div>

        {/* Trump Info */}
        {state !== 'lobby' && state !== 'dealing' && state !== 'bidding' && (
          <div className="flex items-center justify-between bg-white/5 px-3 py-2 rounded border border-white/10">
            <span className="text-slate-400">Trump</span>
            {trump ? (
              <span className={`text-2xl ${trump === '♥' || trump === '♦' ? 'text-red-500' : 'text-white'}`}>{trump}</span>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-slate-500 text-xs italic">Hidden</span>
                <span className="text-xl">🎴</span>
              </div>
            )}
          </div>
        )}

        {/* Lead Suit */}
        {state === 'play' && lead_suit && (
          <div className="flex items-center justify-between bg-neon-cyan/10 px-3 py-2 rounded border border-neon-cyan/30">
            <span className="text-neon-cyan text-xs font-semibold">Lead Suit</span>
            <span className={`text-2xl ${lead_suit === '♥' || lead_suit === '♦' ? 'text-red-500' : 'text-white'}`}>{lead_suit}</span>
          </div>
        )}

        {/* Last Trick */}
        {(state === 'play' || state === 'scoring' || state === 'round_end') && last_trick && (
          <div className="pt-2 border-t border-white/10">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-400 text-xs">Last Trick Winner</span>
              <span className="text-neon-cyan font-semibold text-xs">
                {gameState.players.find((p: any) => p.seat === last_trick.winner)?.name || `Seat ${last_trick.winner}`}
              </span>
            </div>
            <div className="flex justify-center gap-1">
              {Object.entries(last_trick.cards)
                .sort(([a], [b]) => Number(a) - Number(b))
                .map(([seat, card]: [string, any]) => (
                  <div key={seat} className={`
                    flex flex-col items-center p-1 rounded bg-white/5 border border-white/10
                    ${Number(seat) === last_trick.winner ? 'ring-1 ring-neon-cyan' : ''}
                  `}>
                    <span className={`text-lg leading-none ${card.suit === '♥' || card.suit === '♦' ? 'text-red-500' : 'text-white'
                      }`}>
                      {card.rank}{card.suit}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Bid Winner */}
        {bid_winner !== null && bid_winner !== undefined && (
          <div className="pt-2 border-t border-white/10">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 text-xs">Bid Winner</span>
              <div className="text-right">
                <div className="text-neon-amber font-bold text-sm">
                  {gameState.players.find((p: any) => p.seat === bid_winner)?.name}
                </div>
                {bids && bids[bid_winner] && (
                  <div className="text-xs text-white">{bids[bid_winner]} points</div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Team Scores */}
        {points_by_seat && Object.keys(points_by_seat).length > 0 && (
          <div className="pt-2 border-t border-white/10 space-y-2">
            <h4 className="text-slate-300 text-xs font-semibold">Team Scores</h4>
            {(() => {
              const teamScores = Object.entries(points_by_seat).reduce(
                (acc, [seat, score]) => {
                  const team = Number(seat) % 2 === 0 ? 0 : 1;
                  acc[team] += score;
                  return acc;
                },
                { 0: 0, 1: 0 }
              );

              const winningTeam = bid_winner !== null && bid_winner !== undefined
                ? Number(bid_winner) % 2 === 0 ? 0 : 1
                : null;

              return (
                <div className="grid grid-cols-2 gap-2">
                  {[0, 1].map(teamIdx => (
                    <div key={teamIdx} className={`
                      p-2 rounded bg-white/5 border border-white/10 flex flex-col justify-between
                      ${winningTeam === teamIdx ? 'ring-1 ring-neon-amber' : ''}
                    `}>
                      <span className="text-slate-400 text-[10px]">Team {teamIdx + 1}</span>
                      <div className="flex items-end justify-between">
                        <span className="text-xl font-bold text-white">{teamScores[teamIdx as 0 | 1]}</span>
                        {winningTeam === teamIdx && bid_value !== null && (
                          <span className="text-[10px] text-neon-amber">Target: {bid_value}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              );
            })()}
          </div>
        )}
      </div>
    </div>
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
