/**
 * UI state management with Zustand.
 * Handles toasts, modals, theme, and other UI-related state.
 */

import { create } from 'zustand';

export interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
}

export interface Modal {
  type: string;
  props?: Record<string, any>;
}

interface UIStore {
  // State
  toasts: Toast[];
  modal: Modal | null;
  theme: 'light' | 'dark';
  soundEnabled: boolean;
  sidebarOpen: boolean;

  // Actions
  addToast: (message: string, type?: Toast['type'], duration?: number) => void;
  removeToast: (id: string) => void;
  clearToasts: () => void;
  openModal: (type: string, props?: Record<string, any>) => void;
  closeModal: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  toggleTheme: () => void;
  setSoundEnabled: (enabled: boolean) => void;
  toggleSound: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
}

export const useUIStore = create<UIStore>((set, get) => ({
  // Initial state
  toasts: [],
  modal: null,
  theme: 'light',
  soundEnabled: true,
  sidebarOpen: false,

  // Toast actions
  addToast: (message, type = 'info', duration = 4000) => {
    const id = Math.random().toString(36).slice(2, 11);
    const toast: Toast = { id, message, type, duration };

    set((state) => ({
      toasts: [...state.toasts, toast],
    }));

    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        get().removeToast(id);
      }, duration);
    }
  },

  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((toast) => toast.id !== id),
    }));
  },

  clearToasts: () => {
    set({ toasts: [] });
  },

  // Modal actions
  openModal: (type, props = {}) => {
    set({ modal: { type, props } });
  },

  closeModal: () => {
    set({ modal: null });
  },

  // Theme actions
  setTheme: (theme) => {
    set({ theme });
    // Optionally persist to localStorage
    localStorage.setItem('theme', theme);
  },

  toggleTheme: () => {
    const newTheme = get().theme === 'light' ? 'dark' : 'light';
    get().setTheme(newTheme);
  },

  // Sound actions
  setSoundEnabled: (enabled) => {
    set({ soundEnabled: enabled });
    localStorage.setItem('soundEnabled', String(enabled));
  },

  toggleSound: () => {
    const newEnabled = !get().soundEnabled;
    get().setSoundEnabled(newEnabled);
  },

  // Sidebar actions
  setSidebarOpen: (open) => {
    set({ sidebarOpen: open });
  },

  toggleSidebar: () => {
    set((state) => ({ sidebarOpen: !state.sidebarOpen }));
  },
}));

// Helper function to show toast from outside components
export const toast = {
  success: (message: string) => useUIStore.getState().addToast(message, 'success'),
  error: (message: string) => useUIStore.getState().addToast(message, 'error'),
  warning: (message: string) => useUIStore.getState().addToast(message, 'warning'),
  info: (message: string) => useUIStore.getState().addToast(message, 'info'),
};
