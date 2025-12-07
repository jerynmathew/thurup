/**
 * LobbyPanel - Shows players in the lobby and allows game start.
 */

import { GameState } from '../../types';
import { NeonButton, GlassPanel } from '../ui';
import { Users, Bot, CheckCircle, Copy } from 'lucide-react';

interface LobbyPanelProps {
  gameState: GameState;
  onStartGame: () => void;
  onAddBot: () => void;
  isOwner?: boolean;
}

export function LobbyPanel({ gameState, onStartGame, onAddBot, isOwner = true }: LobbyPanelProps) {
  const { players, seats, mode, game_id } = gameState;
  const emptySeats = seats - players.length;
  const canStart = players.length >= 2;

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-neon-cyan flex items-center gap-2">
        <Users className="w-5 h-5" />
        Lobby
      </h2>

      {/* Game Info */}
      <div className="space-y-2 text-sm">
        <div className="flex justify-between items-center bg-white/5 p-2 rounded">
          <span className="text-slate-400">Game ID</span>
          <code className="text-neon-magenta font-mono">{game_id.slice(0, 8)}</code>
        </div>
        <div className="flex justify-between items-center bg-white/5 p-2 rounded">
          <span className="text-slate-400">Mode</span>
          <span className="text-neon-amber font-bold">{mode}</span>
        </div>
        <div className="flex justify-between items-center bg-white/5 p-2 rounded">
          <span className="text-slate-400">Players</span>
          <span className="text-white font-bold">{players.length} / {seats}</span>
        </div>
      </div>

      {/* Players List */}
      <div className="space-y-2 max-h-48 overflow-y-auto pr-1 custom-scrollbar">
        {players.map((player) => (
          <div
            key={player.player_id}
            className="flex items-center justify-between p-2 bg-white/5 rounded border border-white/10"
          >
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-neon-cyan/20 text-neon-cyan rounded-full flex items-center justify-center text-xs font-bold border border-neon-cyan/50">
                {player.seat}
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-medium text-white">{player.name}</span>
                {player.is_bot && (
                  <span className="text-[10px] text-slate-400 flex items-center gap-1">
                    <Bot className="w-3 h-3" /> Bot
                  </span>
                )}
              </div>
            </div>
            <CheckCircle className="w-4 h-4 text-neon-cyan" />
          </div>
        ))}

        {/* Empty Seats */}
        {Array.from({ length: emptySeats }).map((_, i) => (
          <div
            key={`empty-${i}`}
            className="flex items-center justify-between p-2 bg-white/5 rounded border border-dashed border-white/10 opacity-50"
          >
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-slate-700 rounded-full flex items-center justify-center text-xs text-slate-500">
                {players.length + i}
              </div>
              <span className="text-sm text-slate-500">Waiting...</span>
            </div>
          </div>
        ))}
      </div>

      {/* Actions */}
      {isOwner && (
        <div className="space-y-2 pt-2">
          <NeonButton
            variant="cyan"
            glow
            className="w-full py-1.5 text-sm"
            onClick={onStartGame}
            disabled={!canStart}
          >
            {canStart ? 'Start Game' : `Need ${2 - players.length} more`}
          </NeonButton>

          {emptySeats > 0 && (
            <NeonButton
              variant="secondary"
              className="w-full py-1.5 text-sm bg-white/10 hover:bg-white/20 border border-white/10"
              onClick={onAddBot}
            >
              Add Bot
            </NeonButton>
          )}
        </div>
      )}

      {/* Share */}
      <div className="pt-2 border-t border-white/10">
        <p className="text-xs text-slate-400 mb-2">Invite friends:</p>
        <div className="flex gap-2">
          <input
            type="text"
            value={`${window.location.origin}/game/${game_id}`}
            readOnly
            className="flex-1 px-2 py-1 bg-black/30 border border-white/10 rounded text-xs text-slate-300 truncate"
          />
          <button
            onClick={() => navigator.clipboard.writeText(`${window.location.origin}/game/${game_id}`)}
            className="p-1.5 bg-neon-magenta/20 text-neon-magenta rounded hover:bg-neon-magenta/30 transition-colors"
          >
            <Copy className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
