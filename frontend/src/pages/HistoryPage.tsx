/**
 * History page - Browse past games.
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { historyApi } from '../api';
import { Button, Card, Badge, Loading } from '../components/ui';
import { Clock, Users, Trophy } from 'lucide-react';
import type { GameSummary } from '../types';

export default function HistoryPage() {
  const navigate = useNavigate();
  const [games, setGames] = useState<GameSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'completed' | 'active'>('all');

  useEffect(() => {
    loadGames();
  }, [filter]);

  const loadGames = async () => {
    setIsLoading(true);
    try {
      const params: any = { limit: 50 };
      if (filter !== 'all') {
        params.state = filter;
      }
      const data = await historyApi.listGames(params);
      setGames(data);
    } catch (error) {
      console.error('Failed to load games:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStateColor = (state: string) => {
    switch (state) {
      case 'completed':
        return 'success';
      case 'active':
        return 'primary';
      case 'lobby':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 flex justify-between items-center">
          <h1 className="text-3xl font-bold">Game History</h1>
          <Button variant="secondary" onClick={() => navigate('/')}>
            Back to Home
          </Button>
        </div>

        {/* Filters */}
        <div className="mb-6 flex gap-2">
          <Button
            variant={filter === 'all' ? 'primary' : 'secondary'}
            onClick={() => setFilter('all')}
          >
            All Games
          </Button>
          <Button
            variant={filter === 'completed' ? 'primary' : 'secondary'}
            onClick={() => setFilter('completed')}
          >
            Completed
          </Button>
          <Button
            variant={filter === 'active' ? 'primary' : 'secondary'}
            onClick={() => setFilter('active')}
          >
            Active
          </Button>
        </div>

        {/* Games List */}
        {isLoading ? (
          <Loading text="Loading game history..." />
        ) : games.length === 0 ? (
          <Card padding="lg">
            <div className="text-center py-16">
              <Trophy className="w-16 h-16 mx-auto mb-4 text-slate-600" />
              <p className="text-xl text-slate-400 mb-2">No games found</p>
              <p className="text-sm text-slate-500">
                Create a new game to get started!
              </p>
              <Button
                variant="primary"
                className="mt-6"
                onClick={() => navigate('/')}
              >
                Create Game
              </Button>
            </div>
          </Card>
        ) : (
          <div className="grid gap-4">
            {games.map((game) => (
              <Card
                key={game.game_id}
                padding="md"
                className="hover:border-primary-500 transition-colors cursor-pointer"
                onClick={() => {
                  if (game.state === 'completed') {
                    navigate(`/replay/${game.game_id}`);
                  } else {
                    navigate(`/game/${game.game_id}`);
                  }
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-lg">
                        Game {game.game_id.slice(0, 8)}
                      </h3>
                      <Badge variant={getStateColor(game.state) as any}>
                        {game.state}
                      </Badge>
                      <Badge variant="default">{game.mode}</Badge>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-slate-400">
                      <div className="flex items-center gap-1">
                        <Users className="w-4 h-4" />
                        {game.player_count} / {game.seats} players
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {new Date(game.created_at).toLocaleDateString()}
                      </div>
                    </div>

                    {game.players && game.players.length > 0 && (
                      <div className="mt-2 flex gap-2">
                        {game.players.slice(0, 4).map((player, i) => (
                          <span key={i} className="text-sm text-slate-300">
                            {player}
                            {i < game.players.length - 1 && ','}
                          </span>
                        ))}
                        {game.players.length > 4 && (
                          <span className="text-sm text-slate-400">
                            +{game.players.length - 4} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  <Button
                    variant={game.state === 'completed' ? 'primary' : 'secondary'}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (game.state === 'completed') {
                        navigate(`/replay/${game.game_id}`);
                      } else {
                        navigate(`/game/${game.game_id}`);
                      }
                    }}
                  >
                    {game.state === 'completed' ? 'Replay' : 'Join'}
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
