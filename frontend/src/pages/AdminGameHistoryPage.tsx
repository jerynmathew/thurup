/**
 * Admin Game History page - Browse all games with round history.
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { adminApi } from '../api';
import { useAuthStore } from '../stores';
import { Button, Card, Badge, Loading } from '../components/ui';

export default function AdminGameHistoryPage() {
  const navigate = useNavigate();
  const { username, password, isAuthenticated } = useAuthStore();
  const [games, setGames] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedGame, setSelectedGame] = useState<any | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/admin');
      return;
    }
    loadGames();
  }, [isAuthenticated]);

  const loadGames = async () => {
    setIsLoading(true);
    try {
      const data = await adminApi.listGameHistory(username || '', password || '');
      setGames(data);
    } catch (error) {
      console.error('Failed to load game history:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadGameDetail = async (gameId: string) => {
    setLoadingDetail(true);
    try {
      const data = await adminApi.getGameRounds(gameId, username || '', password || '');
      setSelectedGame(data);
    } catch (error) {
      console.error('Failed to load game detail:', error);
      alert('Failed to load game details');
    } finally {
      setLoadingDetail(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getSuitColor = (suit: string) => {
    return suit === '♥' || suit === '♦' ? 'text-red-500' : 'text-slate-300';
  };

  const getPlayerName = (game: any, seat: number) => {
    const player = game?.players?.find((p: any) => p.seat === seat);
    return player?.name || `Seat ${seat + 1}`;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center">
        <Loading text="Loading game history..." />
      </div>
    );
  }

  if (selectedGame) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
        <div className="container mx-auto px-4 py-8">
          {/* Header */}
          <div className="mb-8 flex justify-between items-center">
            <div>
              <button
                onClick={() => setSelectedGame(null)}
                className="text-primary-400 hover:text-primary-300 mb-2"
              >
                ← Back to List
              </button>
              <h1 className="text-3xl font-bold">
                Game Detail: {selectedGame.short_code || selectedGame.game_id.slice(0, 8)}
              </h1>
            </div>
            <Button variant="secondary" onClick={() => navigate('/admin')}>
              Back to Admin
            </Button>
          </div>

          {/* Game Info */}
          <Card padding="md" className="mb-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-slate-400 text-sm">Mode</p>
                <p className="text-lg font-semibold">{selectedGame.mode}</p>
              </div>
              <div>
                <p className="text-slate-400 text-sm">State</p>
                <Badge variant="info">{selectedGame.state}</Badge>
              </div>
              <div>
                <p className="text-slate-400 text-sm">Total Rounds</p>
                <p className="text-lg font-semibold">{selectedGame.total_rounds}</p>
              </div>
              <div>
                <p className="text-slate-400 text-sm">Created</p>
                <p className="text-sm">{formatDate(selectedGame.created_at)}</p>
              </div>
            </div>

            {/* Players */}
            <div className="mt-4 pt-4 border-t border-slate-700">
              <h3 className="text-sm font-semibold text-slate-400 mb-2">Players</h3>
              <div className="flex gap-3">
                {selectedGame.players.map((player: any) => (
                  <div key={player.seat} className="bg-slate-700/50 px-3 py-2 rounded">
                    <span className="text-white font-medium">{player.name}</span>
                    <span className="text-slate-400 text-sm ml-2">
                      (Seat {player.seat + 1})
                      {player.is_bot && ' 🤖'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </Card>

          {/* Rounds */}
          {loadingDetail ? (
            <Loading text="Loading rounds..." />
          ) : selectedGame.rounds.length === 0 ? (
            <Card padding="lg">
              <p className="text-center text-slate-400">No rounds played yet</p>
            </Card>
          ) : (
            <div className="space-y-4">
              {selectedGame.rounds.map((round: any) => (
                <Card key={round.round_number} padding="md">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-xl font-bold">Round {round.round_number}</h3>
                      <p className="text-sm text-slate-400">
                        Dealer: {getPlayerName(selectedGame, round.dealer)}
                      </p>
                    </div>
                    <div className="text-right">
                      {round.trump && (
                        <div className="mb-2">
                          <span className="text-slate-400 text-sm">Trump: </span>
                          <span className={`text-3xl ${getSuitColor(round.trump)}`}>
                            {round.trump}
                          </span>
                        </div>
                      )}
                      {round.bid_winner !== null && (
                        <div>
                          <span className="text-slate-400 text-sm">Bid: </span>
                          <Badge variant="success">
                            {getPlayerName(selectedGame, round.bid_winner)} - {round.bid_value} pts
                          </Badge>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Team Scores */}
                  {round.round_data.team_scores && (
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div className="bg-slate-700/50 p-4 rounded-lg">
                        <p className="text-slate-400 text-sm">Team 1 (Even seats)</p>
                        <p className="text-2xl font-bold">
                          {round.round_data.team_scores.team_points[0]} points
                        </p>
                      </div>
                      <div className="bg-slate-700/50 p-4 rounded-lg">
                        <p className="text-slate-400 text-sm">Team 2 (Odd seats)</p>
                        <p className="text-2xl font-bold">
                          {round.round_data.team_scores.team_points[1]} points
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Tricks */}
                  {round.round_data.captured_tricks && round.round_data.captured_tricks.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-slate-300 mb-2">
                        Tricks ({round.round_data.captured_tricks.length})
                      </h4>
                      <div className="space-y-2">
                        {round.round_data.captured_tricks.map((trick: any, trickIdx: number) => (
                          <div
                            key={trickIdx}
                            className="bg-slate-700/30 p-3 rounded flex justify-between items-center"
                          >
                            <div className="flex gap-3">
                              {trick.cards.map((cardPlay: any, cardIdx: number) => (
                                <div
                                  key={cardIdx}
                                  className={`px-2 py-1 rounded text-sm ${
                                    cardPlay.seat === trick.winner
                                      ? 'bg-green-500/20 ring-1 ring-green-500'
                                      : 'bg-slate-600/50'
                                  }`}
                                >
                                  <span className="text-slate-400 mr-1 text-xs">
                                    {getPlayerName(selectedGame, cardPlay.seat)}:
                                  </span>
                                  <span className={getSuitColor(cardPlay.card.suit)}>
                                    {cardPlay.card.rank}
                                    {cardPlay.card.suit}
                                  </span>
                                </div>
                              ))}
                            </div>
                            <div className="text-sm">
                              <Badge variant="success">
                                Winner: {getPlayerName(selectedGame, trick.winner)} ({trick.points} pts)
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 flex justify-between items-center">
          <h1 className="text-3xl font-bold">Game History</h1>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => navigate('/admin')}>
              Back to Admin
            </Button>
          </div>
        </div>

        {/* Games List */}
        {games.length === 0 ? (
          <Card padding="lg">
            <div className="text-center py-16">
              <p className="text-xl text-slate-400 mb-2">No games found</p>
              <p className="text-sm text-slate-500">Start playing to create game history!</p>
            </div>
          </Card>
        ) : (
          <div className="grid gap-4">
            {games.map((game) => (
              <Card
                key={game.game_id}
                padding="md"
                className="hover:border-primary-500 transition-colors cursor-pointer"
                onClick={() => loadGameDetail(game.game_id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-lg">
                        {game.short_code || game.game_id.slice(0, 8)}
                      </h3>
                      <Badge variant="info">{game.state}</Badge>
                      <Badge variant="default">{game.mode}</Badge>
                      <span className="text-slate-400 text-sm">
                        {game.rounds_played} rounds
                      </span>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-slate-400">
                      <span>{game.seats} seats</span>
                      <span>Created: {formatDate(game.created_at)}</span>
                      <span>Last activity: {formatDate(game.last_activity_at)}</span>
                    </div>

                    {game.player_names && game.player_names.length > 0 && (
                      <div className="mt-2 flex gap-2">
                        {game.player_names.map((nameOrPlayer: any, i: number) => {
                          // Handle both string names and player objects
                          const playerName = typeof nameOrPlayer === 'string' ? nameOrPlayer : nameOrPlayer.name;
                          return (
                            <span key={i} className="text-sm text-slate-300">
                              {playerName}
                              {i < game.player_names.length - 1 && ','}
                            </span>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  <Button
                    variant="primary"
                    onClick={(e) => {
                      e.stopPropagation();
                      loadGameDetail(game.game_id);
                    }}
                  >
                    View Rounds
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
