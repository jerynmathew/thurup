/**
 * Admin page - Server management dashboard.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { useAuthStore } from '../stores';

export default function AdminPage() {
  const navigate = useNavigate();
  const { isAuthenticated, username, login, logout } = useAuthStore();
  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await login(loginUsername, loginPassword);
    } catch (err: any) {
      setError(err.message || 'Login failed');
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white flex items-center justify-center">
        <div className="max-w-md w-full mx-4">
          <div className="bg-slate-800/50 rounded-lg p-8 backdrop-blur-sm border border-slate-700">
            <h1 className="text-3xl font-bold mb-6 text-center">Admin Login</h1>

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Username
                </label>
                <input
                  type="text"
                  value={loginUsername}
                  onChange={(e) => setLoginUsername(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Password
                </label>
                <input
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-white"
                  required
                />
              </div>

              {error && (
                <div className="p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-200 text-sm">
                  {error}
                </div>
              )}

              <button
                type="submit"
                className="w-full py-3 bg-primary-500 hover:bg-primary-600 text-white font-semibold rounded-lg transition-colors"
              >
                Login
              </button>
            </form>

            <button
              onClick={() => navigate('/')}
              className="w-full mt-4 py-2 text-slate-400 hover:text-white transition-colors"
            >
              Back to Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  return <AdminDashboard username={username || ''} onLogout={logout} onNavigateHome={() => navigate('/')} />;
}

interface AdminDashboardProps {
  username: string;
  onLogout: () => void;
  onNavigateHome: () => void;
}

function AdminDashboard({ username, onLogout, onNavigateHome }: AdminDashboardProps) {
  const navigate = useNavigate();
  const { password } = useAuthStore();
  const [health, setHealth] = useState<any>(null);
  const [sessions, setSessions] = useState<any[]>([]);
  const [dbStats, setDbStats] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);

  useEffect(() => {
    loadAllData();
    const interval = setInterval(loadAllData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const loadAllData = async () => {
    try {
      const [healthData, sessionsData, dbStatsData] = await Promise.all([
        loadHealth(),
        loadSessions(),
        loadDbStats(),
      ]);
    } catch (error) {
      console.error('Failed to load admin data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadHealth = async () => {
    try {
      const { adminApi } = await import('../api');
      const data = await adminApi.getHealth(username, password || '');
      setHealth(data);
      return data;
    } catch (error) {
      console.error('Failed to load health:', error);
    }
  };

  const loadSessions = async () => {
    try {
      const { adminApi } = await import('../api');
      const data = await adminApi.listSessions(username, password || '');
      setSessions(data);
      return data;
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const loadDbStats = async () => {
    try {
      const { adminApi } = await import('../api');
      const data = await adminApi.getDatabaseStats(username, password || '');
      setDbStats(data);
      return data;
    } catch (error) {
      console.error('Failed to load database stats:', error);
    }
  };

  const handleForceSave = async (gameId: string) => {
    try {
      const { adminApi } = await import('../api');
      await adminApi.forceSave(gameId, username, password || '');
      alert('Game saved successfully');
      loadSessions();
    } catch (error: any) {
      alert(`Failed to save game: ${error.message}`);
    }
  };

  const handleDeleteSession = async (gameId: string) => {
    if (!confirm(`Are you sure you want to delete session ${gameId}?`)) return;

    try {
      const { adminApi } = await import('../api');
      await adminApi.deleteSession(gameId, username, password || '');
      alert('Session deleted successfully');
      loadSessions();
    } catch (error: any) {
      alert(`Failed to delete session: ${error.message}`);
    }
  };

  const handleTriggerCleanup = async () => {
    if (!confirm('Are you sure you want to trigger cleanup? This will delete old/stale games.')) return;

    try {
      const { adminApi } = await import('../api');
      const result = await adminApi.triggerCleanup(username, password || '');
      alert(`Cleanup completed: ${result.deleted_games} games deleted`);
      loadAllData();
    } catch (error: any) {
      alert(`Failed to trigger cleanup: ${error.message}`);
    }
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const formatBytes = (bytes: number | null) => {
    if (bytes === null) return 'N/A';
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
          <p>Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Admin Dashboard</h1>
            <p className="text-slate-400 mt-1">Logged in as: {username}</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => navigate('/admin/history')}
              className="px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
            >
              Game History
            </button>
            <button
              onClick={onNavigateHome}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
            >
              Home
            </button>
            <button
              onClick={onLogout}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
            >
              Logout
            </button>
          </div>
        </div>

        <div className="grid gap-6">
          {/* Server Health */}
          <div className="bg-slate-800/50 rounded-lg p-6 backdrop-blur-sm border border-slate-700">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Server Health</h2>
              <span
                className={`px-3 py-1 rounded-full text-sm font-medium ${
                  health?.status === 'healthy'
                    ? 'bg-green-500/20 text-green-300 border border-green-500/50'
                    : 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/50'
                }`}
              >
                {health?.status || 'Unknown'}
              </span>
            </div>
            {health && (
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="bg-slate-700/50 p-4 rounded-lg">
                  <p className="text-slate-400 text-sm">Uptime</p>
                  <p className="text-2xl font-bold mt-1">{formatUptime(health.uptime_seconds)}</p>
                </div>
                <div className="bg-slate-700/50 p-4 rounded-lg">
                  <p className="text-slate-400 text-sm">Sessions</p>
                  <p className="text-2xl font-bold mt-1">{health.in_memory_sessions}</p>
                </div>
                <div className="bg-slate-700/50 p-4 rounded-lg">
                  <p className="text-slate-400 text-sm">Connections</p>
                  <p className="text-2xl font-bold mt-1">{health.total_connections}</p>
                </div>
                <div className="bg-slate-700/50 p-4 rounded-lg">
                  <p className="text-slate-400 text-sm">Bot Tasks</p>
                  <p className="text-2xl font-bold mt-1">{health.running_bot_tasks}</p>
                </div>
                <div className="bg-slate-700/50 p-4 rounded-lg">
                  <p className="text-slate-400 text-sm">Database</p>
                  <p className="text-2xl font-bold mt-1">
                    {health.database_connected ? '✓' : '✗'}
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Database Stats */}
          <div className="bg-slate-800/50 rounded-lg p-6 backdrop-blur-sm border border-slate-700">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Database Stats</h2>
              <button
                onClick={handleTriggerCleanup}
                className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 rounded-lg transition-colors text-sm"
              >
                Trigger Cleanup
              </button>
            </div>
            {dbStats && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-slate-700/50 p-4 rounded-lg">
                  <p className="text-slate-400 text-sm">Total Games</p>
                  <p className="text-2xl font-bold mt-1">{dbStats.total_games}</p>
                </div>
                <div className="bg-slate-700/50 p-4 rounded-lg">
                  <p className="text-slate-400 text-sm">Total Players</p>
                  <p className="text-2xl font-bold mt-1">{dbStats.total_players}</p>
                </div>
                <div className="bg-slate-700/50 p-4 rounded-lg">
                  <p className="text-slate-400 text-sm">Snapshots</p>
                  <p className="text-2xl font-bold mt-1">{dbStats.total_snapshots}</p>
                </div>
                <div className="bg-slate-700/50 p-4 rounded-lg">
                  <p className="text-slate-400 text-sm">DB Size</p>
                  <p className="text-2xl font-bold mt-1">{formatBytes(dbStats.db_size_bytes)}</p>
                </div>
              </div>
            )}
          </div>

          {/* Active Sessions */}
          <div className="bg-slate-800/50 rounded-lg p-6 backdrop-blur-sm border border-slate-700">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Active Sessions ({sessions.length})</h2>
              <button
                onClick={loadSessions}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-sm"
              >
                Refresh
              </button>
            </div>
            {sessions.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-slate-400">No active sessions</p>
              </div>
            ) : (
              <div className="space-y-3">
                {sessions.map((session) => (
                  <div
                    key={session.game_id}
                    className="bg-slate-700/50 p-4 rounded-lg flex items-center justify-between"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <code className="font-mono text-sm bg-slate-600 px-2 py-1 rounded">
                          {session.short_code || session.game_id.slice(0, 8)}
                        </code>
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium ${
                            session.state === 'lobby'
                              ? 'bg-yellow-500/20 text-yellow-300'
                              : session.state === 'playing'
                              ? 'bg-green-500/20 text-green-300'
                              : 'bg-blue-500/20 text-blue-300'
                          }`}
                        >
                          {session.state}
                        </span>
                        <span className="text-slate-400 text-sm">{session.mode}</span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-slate-400">
                        <span>Players: {session.player_count} / {session.seats}</span>
                        <span>Connections: {session.connection_count}</span>
                        <span>Connected Seats: [{session.connected_seats.join(', ')}]</span>
                        {session.has_bot_task && (
                          <span className="text-primary-400">Bot Active</span>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleForceSave(session.game_id)}
                        className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm transition-colors"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => handleDeleteSession(session.game_id)}
                        className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
