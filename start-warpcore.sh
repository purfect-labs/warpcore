#!/usr/bin/env bash
# start-warpcore.sh - Start WARPCORE with all database connections pre-established
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PROJECT_ROOT="$SCRIPT_DIR"
export WARPCORE_BINS="$PROJECT_ROOT/bin"
export WARPCORE_CONFIG_DIR="$PROJECT_ROOT/.config"
echo "🚀 WARPCORE Command Center Startup"
echo "==============================="
echo ""
echo "🌐 WARPCORE Web Interface will be available at: http://localhost:8000"
PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}" python3 -c "from web.main import run_server; run_server()"
