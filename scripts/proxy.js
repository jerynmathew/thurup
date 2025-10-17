#!/usr/bin/env node
/**
 * Simple reverse proxy for Thurup test mode
 * Routes requests to backend and frontend services
 *
 * Routes:
 * - /api/* -> Backend (port 18081)
 * - /ws   -> Backend WebSocket (port 18081)
 * - /*    -> Frontend (port 5173)
 */

const http = require('http');
const httpProxy = require('http-proxy');

// Configuration
const PROXY_PORT = process.env.PROXY_PORT || 8080;
const BACKEND_PORT = process.env.BACKEND_PORT || 18081;
const FRONTEND_PORT = process.env.FRONTEND_PORT || 5173;

// Create proxy server
const proxy = httpProxy.createProxyServer({});

// Error handling
proxy.on('error', (err, req, res) => {
  console.error(`[PROXY ERROR] ${req.url}:`, err.message);
  if (!res.headersSent) {
    res.writeHead(502, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      error: 'Bad Gateway',
      message: 'Unable to reach upstream service',
      path: req.url
    }));
  }
});

// Create HTTP server
const server = http.createServer((req, res) => {
  const url = req.url;

  // Route to backend for API and WebSocket
  if (url.startsWith('/api/') || url.startsWith('/ws') || url.startsWith('/docs') || url.startsWith('/openapi.json')) {
    console.log(`[BACKEND] ${req.method} ${url}`);
    proxy.web(req, res, {
      target: `http://127.0.0.1:${BACKEND_PORT}`,
      changeOrigin: true
    });
  }
  // Route everything else to frontend
  else {
    console.log(`[FRONTEND] ${req.method} ${url}`);
    proxy.web(req, res, {
      target: `http://127.0.0.1:${FRONTEND_PORT}`,
      changeOrigin: true
    });
  }
});

// Handle WebSocket upgrades
server.on('upgrade', (req, socket, head) => {
  const url = req.url;

  // Route WebSocket to backend
  if (url.startsWith('/ws') || url.startsWith('/api/')) {
    console.log(`[WS BACKEND] ${url}`);
    proxy.ws(req, socket, head, {
      target: `ws://127.0.0.1:${BACKEND_PORT}`,
      changeOrigin: true
    });
  }
  // Route other WebSocket to frontend (Vite HMR)
  else {
    console.log(`[WS FRONTEND] ${url}`);
    proxy.ws(req, socket, head, {
      target: `ws://127.0.0.1:${FRONTEND_PORT}`,
      changeOrigin: true
    });
  }
});

// Start server
server.listen(PROXY_PORT, '0.0.0.0', () => {
  console.log('='.repeat(60));
  console.log('Thurup Reverse Proxy Server');
  console.log('='.repeat(60));
  console.log(`Listening on: http://0.0.0.0:${PROXY_PORT}`);
  console.log(`Backend:      http://127.0.0.1:${BACKEND_PORT}`);
  console.log(`Frontend:     http://127.0.0.1:${FRONTEND_PORT}`);
  console.log('='.repeat(60));
  console.log('Routing:');
  console.log('  /api/*        -> Backend');
  console.log('  /ws           -> Backend (WebSocket)');
  console.log('  /docs         -> Backend (API docs)');
  console.log('  /*            -> Frontend');
  console.log('='.repeat(60));
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('\nShutting down proxy server...');
  server.close(() => {
    console.log('Proxy server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('\nShutting down proxy server...');
  server.close(() => {
    console.log('Proxy server closed');
    process.exit(0);
  });
});
