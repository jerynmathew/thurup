/**
 * Authentication state management with Zustand.
 * Handles admin authentication for protected routes.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthStore {
  // State
  isAuthenticated: boolean;
  username: string | null;
  password: string | null; // Stored for Basic Auth (consider security implications)

  // Actions
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  getAuthHeader: () => string | null;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      isAuthenticated: false,
      username: null,
      password: null,

      // Actions
      login: async (username, password) => {
        // Verify credentials by making a test request to the health endpoint
        const { createAuthenticatedClient } = await import('../api/client');
        const client = createAuthenticatedClient(username, password);

        try {
          // Make a test request to verify credentials
          await client.get('/api/v1/admin/health');

          // If successful, save credentials
          set({
            isAuthenticated: true,
            username,
            password,
          });
        } catch (error: any) {
          // If failed, throw error to be caught by login handler
          throw new Error(error.message || 'Invalid credentials');
        }
      },

      logout: () => {
        set({
          isAuthenticated: false,
          username: null,
          password: null,
        });
      },

      getAuthHeader: () => {
        const { username, password } = get();
        if (!username || !password) return null;

        // Create Basic Auth header
        const credentials = btoa(`${username}:${password}`);
        return `Basic ${credentials}`;
      },
    }),
    {
      name: 'thurup-auth-storage',
      // Persist authentication status and credentials
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        username: state.username,
        password: state.password, // Needed for Basic Auth on page refresh
        // Note: In production, use session tokens or secure cookies instead
      }),
    }
  )
);
