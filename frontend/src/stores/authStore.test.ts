/**
 * Auth Store tests.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from './authStore';

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
    it('logs in with credentials', () => {
      const { login } = useAuthStore.getState();
      login('admin', 'password');

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.username).toBe('admin');
      expect(state.password).toBe('password');
    });

    it('updates state immediately', () => {
      const { login } = useAuthStore.getState();
      login('testuser', 'testpass');

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.username).toBe('testuser');
      expect(state.password).toBe('testpass');
    });
  });

  describe('Logout', () => {
    it('clears authentication state', () => {
      const { login, logout } = useAuthStore.getState();
      login('admin', 'password');

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
    it('generates Basic Auth header', () => {
      const { login, getAuthHeader } = useAuthStore.getState();
      login('admin', 'password');

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

    it('returns null after logout', () => {
      const { login, logout, getAuthHeader } = useAuthStore.getState();
      login('admin', 'password');
      logout();

      const header = getAuthHeader();
      expect(header).toBeNull();
    });
  });
});
