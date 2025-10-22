/**
 * Auth Store tests.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAuthStore } from './authStore';

// Mock the API client
vi.mock('../api/client', () => ({
  createAuthenticatedClient: () => ({
    get: vi.fn().mockResolvedValue({ data: { status: 'healthy' } }),
  }),
}));

describe('authStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useAuthStore.setState({
      username: null,
      password: null,
      isAuthenticated: false,
    });

    // Clear localStorage
    localStorage.clear();
  });

  describe('Login', () => {
    it('logs in with credentials', async () => {
      const { login } = useAuthStore.getState();
      await login('admin', 'password');

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.username).toBe('admin');
      expect(state.password).toBe('password');
    });

    it('updates state immediately', async () => {
      const { login } = useAuthStore.getState();
      await login('testuser', 'testpass');

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.username).toBe('testuser');
      expect(state.password).toBe('testpass');
    });
  });

  describe('Logout', () => {
    it('clears authentication state', async () => {
      const { login, logout } = useAuthStore.getState();
      await login('admin', 'password');

      logout();

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);
      expect(state.username).toBe(null);
      expect(state.password).toBe(null);
    });

    it('can logout when not logged in', () => {
      const { logout } = useAuthStore.getState();
      logout();

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('Auth Header', () => {
    it('generates Basic Auth header', async () => {
      const { login, getAuthHeader } = useAuthStore.getState();
      await login('admin', 'password');

      const header = getAuthHeader();
      expect(header).toBeTruthy();
      expect(header).toContain('Basic ');

      // Decode to verify
      const base64Part = header?.replace('Basic ', '');
      const decoded = atob(base64Part!);
      expect(decoded).toBe('admin:password');
    });

    it('returns null when not authenticated', () => {
      const { getAuthHeader } = useAuthStore.getState();
      const header = getAuthHeader();
      expect(header).toBeNull();
    });

    it('returns null after logout', async () => {
      const { login, logout, getAuthHeader } = useAuthStore.getState();
      await login('admin', 'password');
      logout();

      const header = getAuthHeader();
      expect(header).toBeNull();
    });
  });
});
