/**
 * Axios HTTP client configuration.
 * Centralized API client with error handling and interceptors.
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type { ApiError } from '../types';

// Use relative URLs for API requests (works with Vite proxy and reverse proxy)
// This allows the frontend to work both locally and through Cloudflare Tunnel
const API_BASE_URL = import.meta.env.VITE_API_BASE || '';

// Create axios instance
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth headers if available
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add any global request modifications here
    // e.g., auth tokens, request ID, etc.
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle errors globally
apiClient.interceptors.response.use(
  (response) => {
    // Any status code within the range of 2xx causes this function to trigger
    return response;
  },
  (error: AxiosError<ApiError>) => {
    // Any status codes outside the range of 2xx cause this function to trigger

    // Handle network errors
    if (!error.response) {
      console.error('Network error:', error.message);
      return Promise.reject({
        message: 'Network error. Please check your connection.',
        originalError: error,
      });
    }

    // Handle HTTP errors
    const status = error.response.status;
    const data = error.response.data;

    let message = 'An error occurred';
    if (typeof data?.detail === 'string') {
      message = data.detail;
    } else if (data?.detail) {
      message = JSON.stringify(data.detail);
    } else if (error.message) {
      message = error.message;
    }

    console.error(`API Error [${status}]:`, message);

    return Promise.reject({
      status,
      message,
      data,
      originalError: error,
    });
  }
);

// Helper to create authenticated client (for admin endpoints)
export function createAuthenticatedClient(username: string, password: string) {
  const authClient = axios.create({
    ...apiClient.defaults,
    auth: {
      username,
      password,
    },
  });

  // Apply same interceptors
  authClient.interceptors.request = apiClient.interceptors.request;
  authClient.interceptors.response = apiClient.interceptors.response;

  return authClient;
}

// Export base URL for WebSocket connections
export const getWebSocketUrl = () => {
  // If API_BASE_URL is set, use it
  if (API_BASE_URL) {
    const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss' : 'ws';
    const url = API_BASE_URL.replace(/^https?:\/\//, '');
    return `${wsProtocol}://${url}`;
  }

  // Otherwise use the current window location (works with both dev and tunnel)
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host; // includes port if present
  return `${wsProtocol}//${host}`;
};
