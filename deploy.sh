#!/bin/bash
# Thurup Deployment Script - Main Orchestrator
# Usage: ./deploy.sh [dev|test|stop]

set -e

# Load utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/scripts/utils.sh"

# Load local environment if exists
if [ -f "${SCRIPT_DIR}/.env.local" ]; then
    load_env "${SCRIPT_DIR}/.env.local"
fi

# Show usage
show_usage() {
    cat << EOF
Thurup Deployment Script

Usage: ./deploy.sh [COMMAND]

Commands:
  dev     Start development mode (local only)
  test    Start test mode with Cloudflare Tunnel (share with family/friends)
  stop    Stop all running services

Examples:
  ./deploy.sh dev     # Start local development
  ./deploy.sh test    # Start with public tunnel
  ./deploy.sh stop    # Stop everything

Environment:
  Configuration can be customized in .env.local file.
  See .env.template for available options.

For more information, see DEPLOYMENT.md
EOF
}

# Main logic
case "${1:-}" in
    dev)
        log_info "Starting in DEVELOPMENT mode..."
        "${SCRIPT_DIR}/scripts/dev.sh"
        ;;
    test)
        log_info "Starting in TEST mode with Cloudflare Tunnel..."
        "${SCRIPT_DIR}/scripts/test.sh"
        ;;
    stop)
        "${SCRIPT_DIR}/scripts/stop.sh"
        ;;
    help|--help|-h)
        show_usage
        exit 0
        ;;
    "")
        log_error "No command specified"
        echo ""
        show_usage
        exit 1
        ;;
    *)
        log_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
