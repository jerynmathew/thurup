/**
 * Tests for API client configuration and helpers.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createAuthenticatedClient, getWebSocketUrl } from './client';

describe('API Client', () => {
  describe('createAuthenticatedClient', () => {
    it('creates client with Basic Auth credentials', () => {
      const client = createAuthenticatedClient('admin', 'password');

      expect(client.defaults.auth).toEqual({
        username: 'admin',
        password: 'password',
      });
    });

    it('creates separate client instances', () => {
      const client1 = createAuthenticatedClient('user1', 'pass1');
      const client2 = createAuthenticatedClient('user2', 'pass2');

      expect(client1).not.toBe(client2);
      expect(client1.defaults.auth?.username).toBe('user1');
      expect(client2.defaults.auth?.username).toBe('user2');
    });

    it('inherits base client configuration', () => {
      const client = createAuthenticatedClient('admin', 'password');

      expect(client.defaults.timeout).toBeDefined();
      expect(client.defaults.headers).toBeDefined();
    });
  });

  describe('getWebSocketUrl', () => {
    it('generates ws:// URL from http:// location', () => {
      Object.defineProperty(window, 'location', {
        value: {
          protocol: 'http:',
          host: 'localhost:3000',
        },
        writable: true,
      });

      const url = getWebSocketUrl();
      expect(url).toBe('ws://localhost:3000');
    });

    it('generates wss:// URL from https:// location', () => {
      Object.defineProperty(window, 'location', {
        value: {
          protocol: 'https:',
          host: 'example.com',
        },
        writable: true,
      });

      const url = getWebSocketUrl();
      expect(url).toBe('wss://example.com');
    });

    it('includes port in WebSocket URL', () => {
      Object.defineProperty(window, 'location', {
        value: {
          protocol: 'http:',
          host: 'localhost:8080',
        },
        writable: true,
      });

      const url = getWebSocketUrl();
      expect(url).toBe('ws://localhost:8080');
    });
  });
});
