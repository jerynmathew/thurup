#!/bin/bash
# Stop all running services and cleanup

set -e

# Load utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils.sh"

# Change to project root
cd "${PROJECT_ROOT}"

log_info "Stopping Thurup services..."

# Services to stop (in reverse order of startup)
SERVICES=("tunnel" "proxy" "frontend" "backend")

# Stop each service
for service in "${SERVICES[@]}"; do
    kill_process "$service"
done

# Clean up old PID files
for pid_file in "${PID_DIR}"/*.pid; do
    if [ -f "$pid_file" ]; then
        service_name=$(basename "$pid_file" .pid)
        log_warn "Cleaning up stale PID file for: $service_name"
        rm -f "$pid_file"
    fi
done

# Clean up log files (optional, comment out if you want to keep logs)
# log_info "Cleaning up log files..."
# rm -f "${PID_DIR}"/*.log

log_success "✓ All services stopped"
