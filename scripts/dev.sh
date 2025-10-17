#!/bin/bash
# Start development mode with hot-reload for both backend and frontend

set -e

# Load utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils.sh"

# Configuration (can be overridden by .env.local)
BACKEND_PORT=${BACKEND_PORT:-18081}
FRONTEND_PORT=${FRONTEND_PORT:-5173}
BACKEND_ENV=${BACKEND_ENV:-"${PROJECT_ROOT}/backend/.env.development"}

# Change to project root
cd "${PROJECT_ROOT}"

log_info "Starting Thurup in DEVELOPMENT mode..."

# Check requirements
if ! check_requirements "uv" "node" "npm"; then
    log_error "Please install missing dependencies"
    exit 1
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

# Start frontend
log_info "Starting frontend on port ${FRONTEND_PORT}..."
cd "${PROJECT_ROOT}/frontend"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    log_info "Installing frontend dependencies..."
    npm install
fi

# Start vite in background
npm run dev > "${PID_DIR}/frontend.log" 2>&1 &
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

log_success "✓ Development environment ready!"
echo ""
log_info "Backend:  http://localhost:${BACKEND_PORT}"
log_info "Frontend: http://localhost:${FRONTEND_PORT}"
log_info "API Docs: http://localhost:${BACKEND_PORT}/docs"
echo ""
log_info "Logs:"
log_info "  Backend:  ${PID_DIR}/backend.log"
log_info "  Frontend: ${PID_DIR}/frontend.log"
echo ""
log_warn "To stop services, run: ./deploy.sh stop"
