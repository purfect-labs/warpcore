#!/usr/bin/env bash
# start-warpcore.sh - Start WARPCORE HTML UI Server
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PROJECT_ROOT="$SCRIPT_DIR"
export PYTHONPATH="$SCRIPT_DIR/src:${PYTHONPATH:-}"

echo "🌊 WARPCORE Command Center Startup"
echo "=================================="
echo ""
echo "🌐 WARPCORE Web Interface will be available at: http://localhost:8000"
echo "🔑 License UI with JavaScript fixes applied"
echo ""

# Start the WARPCORE server using the full system with UI (like APEX pattern)
cd "$SCRIPT_DIR"
PYTHONPATH="$SCRIPT_DIR/src:${PYTHONPATH:-}" python3 -c "from src.api.main import run_server; run_server()"
