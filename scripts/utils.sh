#!/bin/bash
# Shared utility functions for deployment scripts

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="${PROJECT_ROOT}/.thurup"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Ensure PID directory exists
ensure_pid_dir() {
    mkdir -p "${PID_DIR}"
}

# Save PID to file
save_pid() {
    local service_name=$1
    local pid=$2
    ensure_pid_dir
    echo "$pid" > "${PID_DIR}/${service_name}.pid"
    log_info "Saved PID $pid for $service_name"
}

# Read PID from file
read_pid() {
    local service_name=$1
    local pid_file="${PID_DIR}/${service_name}.pid"

    if [ -f "$pid_file" ]; then
        cat "$pid_file"
    else
        echo ""
    fi
}

# Check if process is running
is_running() {
    local pid=$1
    if [ -z "$pid" ]; then
        return 1
    fi

    if ps -p "$pid" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Kill process gracefully
kill_process() {
    local service_name=$1
    local pid=$(read_pid "$service_name")

    if [ -z "$pid" ]; then
        log_warn "No PID found for $service_name"
        return 0
    fi

    if is_running "$pid"; then
        log_info "Stopping $service_name (PID: $pid)..."
        kill "$pid" 2>/dev/null || true

        # Wait up to 5 seconds for graceful shutdown
        for i in {1..5}; do
            if ! is_running "$pid"; then
                log_success "$service_name stopped"
                rm -f "${PID_DIR}/${service_name}.pid"
                return 0
            fi
            sleep 1
        done

        # Force kill if still running
        log_warn "Force killing $service_name..."
        kill -9 "$pid" 2>/dev/null || true
        rm -f "${PID_DIR}/${service_name}.pid"
        log_success "$service_name stopped (forced)"
    else
        log_warn "$service_name not running (stale PID)"
        rm -f "${PID_DIR}/${service_name}.pid"
    fi
}

# Kill process by port
kill_port() {
    local port=$1
    local service_name=$2

    log_info "Checking for processes on port $port..."
    local pids=$(lsof -ti:$port 2>/dev/null)

    if [ -n "$pids" ]; then
        log_info "Killing processes on port $port: $pids"
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 1
        log_success "Port $port is now free"
    else
        log_info "Port $port is already free"
    fi
}

# Wait for HTTP endpoint to be ready
wait_for_http() {
    local url=$1
    local service_name=$2
    local max_attempts=${3:-30}

    log_info "Waiting for $service_name to be ready at $url..."

    for i in $(seq 1 $max_attempts); do
        if curl -s -f "$url" > /dev/null 2>&1; then
            log_success "$service_name is ready!"
            return 0
        fi
        echo -n "."
        sleep 1
    done

    echo ""
    log_error "$service_name failed to start after $max_attempts seconds"
    return 1
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required commands
check_requirements() {
    local missing=()

    for cmd in "$@"; do
        if ! command_exists "$cmd"; then
            missing+=("$cmd")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing required commands: ${missing[*]}"
        return 1
    fi

    return 0
}

# Load environment file
load_env() {
    local env_file=$1

    if [ -f "$env_file" ]; then
        log_info "Loading environment from $env_file"
        set -a
        source "$env_file"
        set +a
        return 0
    else
        log_warn "Environment file not found: $env_file"
        return 1
    fi
}

# Export all functions
export -f log_info log_success log_warn log_error
export -f ensure_pid_dir save_pid read_pid
export -f is_running kill_process kill_port
export -f wait_for_http command_exists check_requirements load_env
