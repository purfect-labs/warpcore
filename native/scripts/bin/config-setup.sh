#!/usr/bin/env bash
set -euo pipefail
echo "🚀 WARPCORE Configuration Setup"
echo "=========================="
echo ""
$WARPCORE_BINS/setup-aws-sso-auth.sh
$WARPCORE_BINS/setup-aws-db-config.sh

