/**
 * React Router configuration.
 * Defines all application routes and lazy-loaded page components.
 */

import { createBrowserRouter } from 'react-router';

// Lazy load pages for better performance
import HomePage from './pages/HomePage';
import GamePage from './pages/GamePage';
import HistoryPage from './pages/HistoryPage';
import ReplayPage from './pages/ReplayPage';
import AdminPage from './pages/AdminPage';
import AdminGameHistoryPage from './pages/AdminGameHistoryPage';
import NotFoundPage from './pages/NotFoundPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <HomePage />,
  },
  {
    path: '/game/:gameId',
    element: <GamePage />,
  },
  {
    path: '/history',
    element: <HistoryPage />,
  },
  {
    path: '/replay/:gameId',
    element: <ReplayPage />,
  },
  {
    path: '/admin',
    element: <AdminPage />,
  },
  {
    path: '/admin/history',
    element: <AdminGameHistoryPage />,
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
]);
