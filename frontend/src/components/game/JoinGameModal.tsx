/**
 * JoinGameModal - Modal for player name input when joining a game.
 * Used on both HomePage and GamePage for consistent UX.
 */

import { useState } from 'react';
import { Modal } from '../ui/Modal';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';

interface JoinGameModalProps {
  isOpen: boolean;
  onClose: () => void;
  onJoin: (playerName: string) => void;
  gameId: string;
  isLoading?: boolean;
  error?: string | null;
}

export function JoinGameModal({
  isOpen,
  onClose,
  onJoin,
  gameId,
  isLoading = false,
  error = null,
}: JoinGameModalProps) {
  const [playerName, setPlayerName] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = () => {
    // Validate player name
    const trimmedName = playerName.trim();
    if (!trimmedName) {
      setLocalError('Please enter your name');
      return;
    }

    if (trimmedName.length < 2) {
      setLocalError('Name must be at least 2 characters');
      return;
    }

    if (trimmedName.length > 20) {
      setLocalError('Name must be less than 20 characters');
      return;
    }

    // Clear local error and submit
    setLocalError(null);
    onJoin(trimmedName);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading) {
      handleSubmit();
    }
  };

  const displayError = error || localError;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Join Game"
      size="sm"
      showCloseButton={!isLoading}
    >
      <div className="space-y-4">
        <p className="text-slate-300 text-sm">
          Enter your name to join the game
        </p>

        {gameId && (
          <div className="bg-slate-700/50 rounded px-3 py-2">
            <span className="text-slate-400 text-xs">Game Code:</span>
            <span className="text-white font-mono font-bold text-sm ml-2">
              {gameId}
            </span>
          </div>
        )}

        <Input
          label="Your Name"
          value={playerName}
          onChange={(e) => {
            setPlayerName(e.target.value);
            setLocalError(null); // Clear error on input change
          }}
          onKeyDown={handleKeyPress}
          placeholder="Enter your name"
          fullWidth
          disabled={isLoading}
          autoFocus
        />

        {displayError && (
          <div className="bg-red-500/10 border border-red-500/30 rounded px-3 py-2">
            <p className="text-red-300 text-sm">{displayError}</p>
          </div>
        )}

        <div className="flex gap-3">
          <Button
            onClick={onClose}
            variant="secondary"
            fullWidth
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            variant="primary"
            fullWidth
            isLoading={isLoading}
            disabled={isLoading}
          >
            Join Game
          </Button>
        </div>
      </div>
    </Modal>
  );
}
