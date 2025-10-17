#!/bin/bash
# Start test mode with Cloudflare Tunnel for sharing with family/friends

set -e

# Load utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils.sh"

# Configuration (can be overridden by .env.local)
BACKEND_PORT=${BACKEND_PORT:-18081}
FRONTEND_PORT=${FRONTEND_PORT:-5173}
PROXY_PORT=${PROXY_PORT:-8080}
BACKEND_ENV=${BACKEND_ENV:-"${PROJECT_ROOT}/backend/.env.development"}
CLOUDFLARED_PATH=${CLOUDFLARED_PATH:-"/usr/local/bin/cloudflared"}

# Change to project root
cd "${PROJECT_ROOT}"

log_info "Starting Thurup in TEST mode with Cloudflare Tunnel..."

# Check basic requirements
if ! check_requirements "uv" "node" "npm"; then
    log_error "Please install missing dependencies"
    exit 1
fi

# Check if cloudflared is installed
if ! command_exists "cloudflared"; then
    log_warn "cloudflared not found, attempting to install..."

    # Detect OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command_exists "brew"; then
            log_info "Installing cloudflared via Homebrew..."
            brew install cloudflare/cloudflare/cloudflared
        else
            log_error "Homebrew not found. Please install Homebrew or download cloudflared manually from:"
            log_error "https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        log_info "Installing cloudflared for Linux..."
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
        sudo dpkg -i cloudflared-linux-amd64.deb
        rm cloudflared-linux-amd64.deb
    else
        log_error "Unsupported OS. Please install cloudflared manually from:"
        log_error "https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
        exit 1
    fi
fi

# Load backend environment
if [ -f "${BACKEND_ENV}" ]; then
    load_env "${BACKEND_ENV}"
else
    log_warn "Backend .env not found at ${BACKEND_ENV}, using defaults"
fi

# Clean up ports
kill_port "${BACKEND_PORT}" "backend"
kill_port "${FRONTEND_PORT}" "frontend"
kill_port "${PROXY_PORT}" "proxy"

# Start backend
log_info "Starting backend on port ${BACKEND_PORT}..."
cd "${PROJECT_ROOT}/backend"

# Ensure database is initialized
if [ ! -f "thurup.db" ]; then
    log_info "Initializing database..."
    uv run alembic upgrade head
fi

# Start uvicorn in background
uv run uvicorn app.main:app --host 0.0.0.0 --port "${BACKEND_PORT}" --reload > "${PID_DIR}/backend.log" 2>&1 &
BACKEND_PID=$!
save_pid "backend" "${BACKEND_PID}"

log_info "Backend starting (PID: ${BACKEND_PID})..."

# Wait for backend to be ready
sleep 2
if ! wait_for_http "http://localhost:${BACKEND_PORT}/" "backend" 30; then
    log_error "Backend failed to start. Check logs at ${PID_DIR}/backend.log"
    kill_process "backend"
    exit 1
fi

# Start frontend (must use --host 0.0.0.0 for tunnel to work)
log_info "Starting frontend on port ${FRONTEND_PORT}..."
cd "${PROJECT_ROOT}/frontend"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    log_info "Installing frontend dependencies..."
    npm install
fi

# Start vite in background with host binding (--host 0.0.0.0 for tunnel access)
npm run dev -- --host 0.0.0.0 > "${PID_DIR}/frontend.log" 2>&1 &
FRONTEND_PID=$!
save_pid "frontend" "${FRONTEND_PID}"

log_info "Frontend starting (PID: ${FRONTEND_PID})..."

# Wait for frontend to be ready
sleep 3
if ! wait_for_http "http://localhost:${FRONTEND_PORT}" "frontend" 30; then
    log_error "Frontend failed to start. Check logs at ${PID_DIR}/frontend.log"
    kill_process "backend"
    kill_process "frontend"
    exit 1
fi

# Install proxy dependencies if needed
log_info "Setting up reverse proxy..."
cd "${PROJECT_ROOT}"
if [ ! -d "node_modules" ]; then
    log_info "Installing proxy dependencies..."
    npm install
fi

# Start reverse proxy
log_info "Starting reverse proxy on port ${PROXY_PORT}..."
BACKEND_PORT="${BACKEND_PORT}" FRONTEND_PORT="${FRONTEND_PORT}" PROXY_PORT="${PROXY_PORT}" node scripts/proxy.js > "${PID_DIR}/proxy.log" 2>&1 &
PROXY_PID=$!
save_pid "proxy" "${PROXY_PID}"

log_info "Reverse proxy starting (PID: ${PROXY_PID})..."

# Wait for proxy to be ready
sleep 2
if ! wait_for_http "http://localhost:${PROXY_PORT}" "proxy" 30; then
    log_error "Reverse proxy failed to start. Check logs at ${PID_DIR}/proxy.log"
    kill_process "backend"
    kill_process "frontend"
    kill_process "proxy"
    exit 1
fi

# Start Cloudflare Tunnel for the reverse proxy (serves both frontend and backend)
log_info "Starting Cloudflare Tunnel..."
# Use 127.0.0.1 instead of localhost to avoid IPv6 issues
cloudflared tunnel --url http://127.0.0.1:${PROXY_PORT} > "${PID_DIR}/tunnel.log" 2>&1 &
TUNNEL_PID=$!
save_pid "tunnel" "${TUNNEL_PID}"

log_info "Cloudflare Tunnel starting (PID: ${TUNNEL_PID})..."

# Wait for tunnel URL to appear in logs
sleep 3
for i in {1..10}; do
    if [ -f "${PID_DIR}/tunnel.log" ]; then
        TUNNEL_URL=$(grep -o 'https://[^[:space:]]*\.trycloudflare.com' "${PID_DIR}/tunnel.log" | head -1)
        if [ -n "$TUNNEL_URL" ]; then
            break
        fi
    fi
    sleep 1
done

log_success "✓ Test environment ready!"
echo ""
log_info "Local Access:"
log_info "  Full App: http://localhost:${PROXY_PORT} (via reverse proxy)"
log_info "  Backend:  http://localhost:${BACKEND_PORT} (direct)"
log_info "  Frontend: http://localhost:${FRONTEND_PORT} (direct)"
log_info "  API Docs: http://localhost:${PROXY_PORT}/docs"
echo ""
log_success "Public Access (share this URL):"
if [ -n "$TUNNEL_URL" ]; then
    log_success "  ${TUNNEL_URL}"
    echo ""
    log_info "The tunnel serves both frontend AND backend through a reverse proxy."
    log_info "Remote users can access the full app, including API calls."
    echo ""
    log_warn "NOTE: This URL is temporary and will change on restart"
    log_warn "Anyone with this URL can access your game"
else
    log_warn "  Tunnel URL not found yet. Check ${PID_DIR}/tunnel.log"
fi
echo ""
log_info "Logs:"
log_info "  Backend:  ${PID_DIR}/backend.log"
log_info "  Frontend: ${PID_DIR}/frontend.log"
log_info "  Proxy:    ${PID_DIR}/proxy.log"
log_info "  Tunnel:   ${PID_DIR}/tunnel.log"
echo ""
log_warn "To stop services, run: ./deploy.sh stop"
