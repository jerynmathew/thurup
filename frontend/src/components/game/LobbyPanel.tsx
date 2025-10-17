/**
 * LobbyPanel - Shows players in the lobby and allows game start.
 */

import { GameState } from '../../types';
import { Button, Card, Badge } from '../ui';
import { Users, Bot, CheckCircle } from 'lucide-react';

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
    <div className="space-y-6">
      {/* Game Info Card */}
      <Card padding="md">
        <h2 className="text-2xl font-bold mb-4">Game Lobby</h2>

        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-slate-400">Game ID:</span>
            <code className="bg-slate-700 px-2 py-1 rounded text-sm">{game_id.slice(0, 8)}</code>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-slate-400">Mode:</span>
            <Badge variant="primary">{mode}</Badge>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-slate-400">Players:</span>
            <span className="text-white font-semibold">
              {players.length} / {seats}
            </span>
          </div>
        </div>
      </Card>

      {/* Players List */}
      <Card padding="md">
        <div className="flex items-center gap-2 mb-4">
          <Users className="w-5 h-5 text-primary-400" />
          <h3 className="text-lg font-semibold">Players</h3>
        </div>

        <div className="space-y-2">
          {players.map((player) => (
            <div
              key={player.player_id}
              className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center font-bold">
                  {player.seat}
                </div>
                <div>
                  <div className="font-medium text-white">{player.name}</div>
                  {player.is_bot && (
                    <div className="text-xs text-slate-400 flex items-center gap-1">
                      <Bot className="w-3 h-3" />
                      Bot Player
                    </div>
                  )}
                </div>
              </div>
              <CheckCircle className="w-5 h-5 text-green-400" />
            </div>
          ))}

          {/* Empty Seats */}
          {Array.from({ length: emptySeats }).map((_, i) => (
            <div
              key={`empty-${i}`}
              className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border-2 border-dashed border-slate-700"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center text-slate-500">
                  {players.length + i}
                </div>
                <span className="text-slate-500">Waiting for player...</span>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Actions */}
      {isOwner && (
        <Card padding="md">
          <h3 className="text-lg font-semibold mb-4">Actions</h3>

          <div className="space-y-3">
            <Button
              fullWidth
              variant="primary"
              size="lg"
              onClick={onStartGame}
              disabled={!canStart}
            >
              {canStart ? 'Start Game' : `Need ${2 - players.length} more player(s)`}
            </Button>

            {emptySeats > 0 && (
              <Button
                fullWidth
                variant="secondary"
                onClick={onAddBot}
              >
                Add Bot Player
              </Button>
            )}
          </div>

          {!canStart && (
            <p className="mt-4 text-sm text-slate-400 text-center">
              Share the game ID with friends to invite them
            </p>
          )}
        </Card>
      )}

      {/* Share Info */}
      <Card padding="md" className="bg-primary-500/10 border-primary-500/30">
        <h3 className="text-sm font-semibold mb-2 text-primary-300">Share this game</h3>
        <p className="text-xs text-slate-300 mb-3">
          Share the game ID or URL with your friends to invite them
        </p>
        <div className="flex gap-2">
          <input
            type="text"
            value={`${window.location.origin}/game/${game_id}`}
            readOnly
            className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white"
          />
          <Button
            variant="primary"
            size="sm"
            onClick={() => {
              navigator.clipboard.writeText(`${window.location.origin}/game/${game_id}`);
            }}
          >
            Copy
          </Button>
        </div>
      </Card>
    </div>
  );
}
