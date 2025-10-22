# Thurup Deployment Guide

This guide covers how to deploy and run Thurup in different environments.

## Quick Start

### Development Mode (Local Only)

Start both backend and frontend for local development:

```bash
./deploy.sh dev
```

This will:
- Start the backend API on `http://localhost:18081`
- Start the frontend dev server on `http://localhost:5173`
- Enable hot-reload for code changes
- Initialize the database if needed

Access points:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:18081 (proxied through frontend)
- **API Docs**: http://localhost:18081/docs

### Test Mode (Share with Family/Friends)

Start services with a public Cloudflare Tunnel URL:

```bash
./deploy.sh test
```

This will:
- Start the backend and frontend (same as dev mode)
- Start a reverse proxy that serves both backend and frontend
- Create a temporary public URL via Cloudflare Tunnel
- Display the public URL to share

Example output:
```
✓ Test environment ready!

Local Access:
  Full App: http://localhost:8080 (via reverse proxy)
  Backend:  http://localhost:18081 (direct)
  Frontend: http://localhost:5173 (direct)

Public Access (share this URL):
  https://random-name-1234.trycloudflare.com

The tunnel serves both frontend AND backend through a reverse proxy.
Remote users can access the full app, including API calls.
```

**Note**: The tunnel URL is temporary and changes on each restart.

**How it works**: Test mode uses a reverse proxy (Node.js http-proxy) on port 8080 that routes:
- `/api/*` → Backend (port 18081)
- `/ws` → Backend WebSocket (port 18081)
- `/*` → Frontend (port 5173)

This ensures remote users can access both the frontend UI and backend API through a single Cloudflare Tunnel URL.

### Stop All Services

```bash
./deploy.sh stop
```

This gracefully stops all running services (backend, frontend, tunnel).

---

## Prerequisites

### Required Software

1. **Python 3.11+** with `uv` package manager
   ```bash
   # Install uv (if not already installed)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Node.js 18+** and npm
   ```bash
   # Verify installation
   node --version
   npm --version
   ```

3. **For Test Mode**: Cloudflare Tunnel (`cloudflared`)
   - **macOS** (with Homebrew):
     ```bash
     brew install cloudflare/cloudflare/cloudflared
     ```
   - **Linux**:
     ```bash
     wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
     sudo dpkg -i cloudflared-linux-amd64.deb
     ```
   - **Windows**: Download from [Cloudflare Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/)

### First-Time Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd thurup
   ```

2. **Install backend dependencies**:
   ```bash
   cd backend
   uv sync
   ```

3. **Install frontend dependencies**:
   ```bash
   cd ../frontend
   npm install
   ```

4. **Verify environment files exist**:
   ```bash
   # Backend should have these files:
   ls backend/.env.*
   # Expected: .env.development, .env.production, .env.test, .env.template
   ```

---

## Configuration

### Deployment Configuration

Copy `.env.template` to `.env.local` and customize if needed:

```bash
cp .env.template .env.local
```

Available options in `.env.local`:

```bash
# Port Configuration
BACKEND_PORT=18081         # Backend API port
FRONTEND_PORT=5173         # Frontend dev server port
PROXY_PORT=8080            # Reverse proxy port (test mode only)

# Backend Environment File
BACKEND_ENV=./backend/.env.development  # Path to backend .env

# Cloudflare Tunnel Binary
CLOUDFLARED_PATH=/usr/local/bin/cloudflared
```

**Note**: For most users, the defaults work fine. Only create `.env.local` if you need custom ports or paths.

### Backend Configuration

Backend settings are in `backend/.env.*` files:

- `backend/.env.development` - Development settings (local only)
- `backend/.env.test` - Test settings (when using tunnel)
- `backend/.env.production` - Production settings (future use)

Key backend settings:
- `LOG_LEVEL` - Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `DATABASE_URL` - Database connection string
- `CORS_ORIGINS` - Allowed frontend origins (comma-separated)
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` - Admin API credentials

See `backend/.env.template` for full documentation.

---

## Directory Structure

```
thurup/
├── deploy.sh              # Main deployment script
├── package.json           # Proxy dependencies
├── node_modules/          # Proxy dependencies (gitignored)
├── .env.template          # Deployment config template
├── .env.local             # Your custom config (gitignored)
├── scripts/               # Helper scripts
│   ├── utils.sh          # Shared utilities
│   ├── proxy.js          # Reverse proxy for test mode
│   ├── dev.sh            # Development mode
│   ├── test.sh           # Test mode with tunnel
│   └── stop.sh           # Stop all services
├── .thurup/              # Runtime artifacts (gitignored)
│   ├── *.pid             # Process IDs
│   ├── *.log             # Service logs (backend, frontend, proxy, tunnel)
│   └── tunnel.log        # Cloudflare tunnel logs
├── backend/              # Backend service
│   ├── app/              # FastAPI application
│   ├── .env.*            # Backend environment files
│   └── thurup.db         # SQLite database (gitignored)
└── frontend/             # Frontend service
    ├── src/              # React application
    └── dist/             # Built assets (production)
```

---

## Usage

### Development Workflow

1. **Start development**:
   ```bash
   ./deploy.sh dev
   ```

2. **Make code changes** - Changes will hot-reload automatically

3. **View logs** (if needed):
   ```bash
   tail -f .thurup/backend.log
   tail -f .thurup/frontend.log
   ```

4. **Stop when done**:
   ```bash
   ./deploy.sh stop
   ```

### Testing with Family/Friends

1. **Start test mode**:
   ```bash
   ./deploy.sh test
   ```

2. **Share the public URL** displayed in the output

3. **Monitor activity**:
   ```bash
   # Watch backend logs
   tail -f .thurup/backend.log

   # Watch tunnel logs
   tail -f .thurup/tunnel.log
   ```

4. **Stop when done**:
   ```bash
   ./deploy.sh stop
   ```

---

## Troubleshooting

### Port Already in Use

If you see "port already in use" errors:

```bash
# Stop all services
./deploy.sh stop

# If that doesn't work, manually kill processes
lsof -ti:8000 | xargs kill -9  # Backend port
lsof -ti:5173 | xargs kill -9  # Frontend port
```

### Services Won't Start

**Check logs**:
```bash
cat .thurup/backend.log
cat .thurup/frontend.log
```

**Common issues**:
- Missing dependencies: Run `uv sync` in backend/, `npm install` in frontend/
- Database not initialized: Delete `backend/thurup.db` and restart
- Wrong Python/Node version: Verify `python --version` and `node --version`

### Cloudflare Tunnel Issues

**Tunnel not starting**:
```bash
# Verify cloudflared is installed
which cloudflared

# Check tunnel logs
cat .thurup/tunnel.log
```

**Tunnel URL not showing**:
- Wait 10-15 seconds for tunnel to initialize
- Check `.thurup/tunnel.log` for errors
- Ensure ports 8000 and 5173 are not blocked by firewall

### Frontend Can't Reach Backend

**Check CORS settings** in `backend/.env.development`:
```bash
# Should include your frontend URL
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

**For test mode**, also add the tunnel domain:
```bash
CORS_ORIGINS=http://localhost:5173,https://your-tunnel-url.trycloudflare.com
```

### Database Issues

**Reset database**:
```bash
./deploy.sh stop
rm backend/thurup.db
./deploy.sh dev  # Will recreate database
```

**Run migrations manually**:
```bash
cd backend
uv run alembic upgrade head
```

---

## Advanced Usage

### Custom Ports

Create `.env.local`:
```bash
BACKEND_PORT=8080
FRONTEND_PORT=3000
```

Then start normally:
```bash
./deploy.sh dev
```

### View Process IDs

```bash
cat .thurup/backend.pid
cat .thurup/frontend.pid
cat .thurup/tunnel.pid
```

### Manual Service Control

**Start individual services**:
```bash
./scripts/dev.sh      # Start dev mode
./scripts/test.sh     # Start test mode with tunnel
./scripts/stop.sh     # Stop all
```

### Persistent Logs

Logs are stored in `.thurup/` and are not automatically cleaned. To view history:

```bash
# View all logs
ls -lh .thurup/*.log

# Clean old logs
rm .thurup/*.log
```

---

## Security Notes

### Development & Test Mode

- **NEVER expose development/test deployments to the public internet long-term**
- Cloudflare Tunnel URLs are temporary but public - anyone with the URL can access your game
- Default admin credentials should be changed in `backend/.env.development`
- SQLite database has no authentication - suitable for local/testing only

### For Production Deployment

**Future work** (not yet implemented):
- Use Docker containers for isolation
- PostgreSQL database with authentication
- HTTPS with proper SSL certificates
- Secure admin credentials
- Rate limiting and DDoS protection
- Log aggregation and monitoring

---

## Next Steps

After getting comfortable with local deployment:

1. **Customize game settings** in `backend/.env.*`
2. **Invite friends to test** using test mode
3. **Report bugs** on GitHub Issues
4. **Contribute improvements** via Pull Requests

For production deployment with Docker, see the root README.md (coming soon).

---

## Support

**Documentation**:
- Backend: `backend/CLAUDE.md`
- Frontend: `frontend/CLAUDE.md`

**Issues**:
- Report bugs or request features on GitHub

**Logs**:
- Always check `.thurup/*.log` files first when debugging

---

**Last Updated**: 2025-10-15
