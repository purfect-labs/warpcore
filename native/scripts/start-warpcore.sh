#!/usr/bin/env bash
# start-warpcore.sh - Start WARPCORE with all database connections pre-established

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PROJECT_ROOT="$SCRIPT_DIR"

export WARPCORE_BINS="$PROJECT_ROOT/bin"
export WARPCORE_CONFIG_DIR="$PROJECT_ROOT/config"
export WARPCORE_STATIC_CONFIG_DIR="$WARPCORE_CONFIG_DIR/static"
export WARPCORE_STATIC_CONFIG_TEMPLATE="$WARPCORE_CONFIG_DIR/templates"

export AWS_DB_CONFIG_FILE_TEMPLATE="$WARPCORE_STATIC_CONFIG_TEMPLATE/aws.db.config.template"
export AWS_SSO_CONFIG_FILE_TEMPLATE="$WARPCORE_STATIC_CONFIG_TEMPLATE/aws.sso.config.template"

export AWS_SSO_CONFIG_FILE="$WARPCORE_CONFIG_DIR/aws.sso.config"
export AWS_DB_CONFIG_FILE="$WARPCORE_CONFIG_DIR/aws.db.config"

export AWS_CONFIG_DIR="$HOME/.aws"
export AWS_CONFIG_FILE="$AWS_CONFIG_DIR/config"
export BACKUP_FILE="$AWS_CONFIG_DIR/config.backup"

echo "🚀 WARPCORE Command Center Startup"
echo "==============================="
echo ""

"$SCRIPT_DIR/bin/config-setup.sh"
"$WARPCORE_BINS/start-all-db-connections.sh" &
DB_PID=$!

echo "🔄 Database connections starting in background (PID: $DB_PID)"
echo "🌐 WARPCORE Web Interface will be available at: http://localhost:8000"
PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}" python3 -c "from web.main import run_server; run_server()"
