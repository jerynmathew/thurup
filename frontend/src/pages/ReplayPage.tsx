/**
 * Replay page - Watch game replay.
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router';
import { historyApi } from '../api';
import { Button, Card, Badge, Loading } from '../components/ui';
import { GameBoard, ScoreBoard } from '../components/game';
import { Play, Pause, SkipBack, SkipForward, ChevronsLeft, ChevronsRight } from 'lucide-react';
import type { GameReplay, GameState } from '../types';

export default function ReplayPage() {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();

  const [replay, setReplay] = useState<GameReplay | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);

  useEffect(() => {
    if (!gameId) {
      navigate('/history');
      return;
    }
    loadReplay();
  }, [gameId, navigate]);

  // Auto-play effect
  useEffect(() => {
    if (!isPlaying || !replay) return;

    const interval = setInterval(() => {
      setCurrentIndex((prev) => {
        if (prev >= replay.snapshots.length - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 2000 / playbackSpeed); // 2 seconds per snapshot, adjustable by speed

    return () => clearInterval(interval);
  }, [isPlaying, replay, playbackSpeed]);

  const loadReplay = async () => {
    if (!gameId) return;
    setIsLoading(true);
    try {
      const data = await historyApi.getGameReplay(gameId);
      setReplay(data);
    } catch (error) {
      console.error('Failed to load replay:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handlePrevious = () => {
    setCurrentIndex((prev) => Math.max(0, prev - 1));
    setIsPlaying(false);
  };

  const handleNext = () => {
    if (!replay) return;
    setCurrentIndex((prev) => Math.min(replay.snapshots.length - 1, prev + 1));
    setIsPlaying(false);
  };

  const handleFirst = () => {
    setCurrentIndex(0);
    setIsPlaying(false);
  };

  const handleLast = () => {
    if (!replay) return;
    setCurrentIndex(replay.snapshots.length - 1);
    setIsPlaying(false);
  };

  const handleSpeedChange = () => {
    setPlaybackSpeed((prev) => {
      if (prev === 1) return 2;
      if (prev === 2) return 0.5;
      return 1;
    });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center">
        <Loading text="Loading replay..." />
      </div>
    );
  }

  if (!replay || replay.snapshots.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
        <div className="container mx-auto px-4 py-8">
          <Card padding="lg">
            <div className="text-center py-16">
              <p className="text-xl text-slate-400 mb-2">No replay data available</p>
              <p className="text-sm text-slate-500 mb-6">
                This game may not have any snapshots yet.
              </p>
              <Button variant="primary" onClick={() => navigate('/history')}>
                Back to History
              </Button>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  const currentSnapshot = replay.snapshots[currentIndex];
  const currentGameState: GameState = currentSnapshot.data;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <div className="container mx-auto px-4 py-4">
        {/* Header */}
        <div className="mb-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold">Replay: {gameId?.slice(0, 8)}...</h1>
            <Badge variant="primary">{replay.mode}</Badge>
            <Badge variant="default">
              Snapshot {currentIndex + 1} / {replay.snapshots.length}
            </Badge>
          </div>
          <Button variant="secondary" onClick={() => navigate('/history')}>
            Back to History
          </Button>
        </div>

        {/* Main Replay Area */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* Game Board */}
          <div className="lg:col-span-3">
            <div className="bg-slate-800/30 rounded-lg border border-slate-700 p-4">
              <GameBoard gameState={currentGameState} mySeat={null} />
            </div>

            {/* Timeline Controls */}
            <Card padding="md" className="mt-4">
              <div className="space-y-4">
                {/* Progress Bar */}
                <div className="space-y-2">
                  <input
                    type="range"
                    min={0}
                    max={replay.snapshots.length - 1}
                    value={currentIndex}
                    onChange={(e) => {
                      setCurrentIndex(parseInt(e.target.value));
                      setIsPlaying(false);
                    }}
                    className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-primary-500"
                  />
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>{currentSnapshot.state_phase}</span>
                    <span>{currentSnapshot.snapshot_reason}</span>
                    <span>{new Date(currentSnapshot.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>

                {/* Playback Controls */}
                <div className="flex items-center justify-center gap-2">
                  <Button variant="secondary" size="sm" onClick={handleFirst} disabled={currentIndex === 0}>
                    <ChevronsLeft className="w-4 h-4" />
                  </Button>
                  <Button variant="secondary" size="sm" onClick={handlePrevious} disabled={currentIndex === 0}>
                    <SkipBack className="w-4 h-4" />
                  </Button>
                  <Button variant="primary" size="lg" onClick={handlePlayPause}>
                    {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={handleNext}
                    disabled={currentIndex === replay.snapshots.length - 1}
                  >
                    <SkipForward className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={handleLast}
                    disabled={currentIndex === replay.snapshots.length - 1}
                  >
                    <ChevronsRight className="w-4 h-4" />
                  </Button>
                </div>

                {/* Speed Control */}
                <div className="flex items-center justify-center gap-2">
                  <span className="text-sm text-slate-400">Speed:</span>
                  <Button variant="secondary" size="sm" onClick={handleSpeedChange}>
                    {playbackSpeed}x
                  </Button>
                </div>
              </div>
            </Card>
          </div>

          {/* Sidebar - Score and info */}
          <div className="lg:col-span-1 space-y-4">
            <ScoreBoard gameState={currentGameState} />

            {/* Snapshot Info */}
            <Card padding="md">
              <h3 className="text-lg font-semibold mb-4">Snapshot Info</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Phase:</span>
                  <span className="text-white font-medium">{currentSnapshot.state_phase}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Reason:</span>
                  <span className="text-white font-medium">{currentSnapshot.snapshot_reason}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Time:</span>
                  <span className="text-white font-medium">
                    {new Date(currentSnapshot.created_at).toLocaleString()}
                  </span>
                </div>
              </div>
            </Card>

            {/* Game Info */}
            <Card padding="md">
              <h3 className="text-lg font-semibold mb-4">Game Info</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Mode:</span>
                  <Badge variant="primary">{replay.mode}</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Seats:</span>
                  <span className="text-white font-medium">{replay.seats}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">State:</span>
                  <Badge variant="default">{replay.state}</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Created:</span>
                  <span className="text-white font-medium">
                    {new Date(replay.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
