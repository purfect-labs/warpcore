#!/usr/bin/env bash
# WARPCORE Full UI System Test Runner
# Runs comprehensive end-to-end tests for the complete WARPCORE system

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WARPCORE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🧪 WARPCORE Full UI System Test Runner"
echo "======================================"
echo ""
echo "Testing complete WARPCORE system with:"
echo "  - System Orchestrator (Data → Web → API layers)"  
echo "  - Provider-Abstraction-Pattern UI flow"
echo "  - License management UI components"
echo "  - Dashboard and agent cards"
echo "  - Real user workflows with native events"
echo ""

# Ensure we're in the testing directory
cd "$SCRIPT_DIR"

# Check if WARPCORE server is running
echo "🔍 Checking WARPCORE server status..."
if curl -s "http://127.0.0.1:8000/api/status" > /dev/null 2>&1; then
    echo "✅ WARPCORE server is running on http://127.0.0.1:8000"
    
    # Get server info
    SERVER_RESPONSE=$(curl -s "http://127.0.0.1:8000/api/status" || echo '{"status":"unknown"}')
    echo "   Server status: $(echo "$SERVER_RESPONSE" | jq -r '.status // "unknown"' 2>/dev/null || echo 'unknown')"
    
    # Check if system orchestrator initialized properly
    LICENSE_RESPONSE=$(curl -s "http://127.0.0.1:8000/api/license/status" || echo '{"success":false}')
    LICENSE_STATUS=$(echo "$LICENSE_RESPONSE" | jq -r '.success // false' 2>/dev/null || echo 'false')
    echo "   License API: $LICENSE_STATUS"
    
    # Check architecture discovery
    ARCH_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "http://127.0.0.1:8000/api/architecture" || echo '000')
    if [ "$ARCH_RESPONSE" = "200" ]; then
        echo "   Architecture discovery: ✅ Active"
    else
        echo "   Architecture discovery: ⚠️ Not available (status: $ARCH_RESPONSE)"
    fi
    
    echo ""
    
else
    echo "❌ WARPCORE server is not running!"
    echo ""
    echo "To start the server, run:"
    echo "  cd $WARPCORE_ROOT"
    echo "  python3 warpcore.py --web"
    echo ""
    echo "Or use the start script:"
    echo "  cd $WARPCORE_ROOT" 
    echo "  bash start-warpcore.sh"
    echo ""
    echo "The system orchestrator will initialize all layers:"
    echo "  📊 Data Layer → 🌐 Web Layer → ⚡ API Layer"
    echo ""
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Playwright dependencies..."
    npm install
    echo ""
fi

# Run Playwright tests
echo "🎭 Starting Playwright tests..."
echo "Using configuration: playwright.config.js"
echo "Base URL: http://127.0.0.1:8000"
echo ""

# Default test command
TEST_COMMAND="npx playwright test e2e/warpcore_full_ui_system.spec.js"

# Parse command line arguments
case "${1:-default}" in
    "headed")
        echo "🖥️  Running in headed mode (browser visible)"
        TEST_COMMAND="$TEST_COMMAND --headed"
        ;;
    "debug") 
        echo "🐛 Running in debug mode (interactive)"
        TEST_COMMAND="$TEST_COMMAND --debug"
        ;;
    "ui")
        echo "🎨 Running with Playwright UI"
        TEST_COMMAND="$TEST_COMMAND --ui"
        ;;
    "performance")
        echo "⚡ Running performance tests only"
        TEST_COMMAND="npx playwright test e2e/warpcore_full_ui_system.spec.js -g 'Performance'"
        ;;
    "system")
        echo "🏗️  Running system orchestrator tests only"
        TEST_COMMAND="npx playwright test e2e/warpcore_full_ui_system.spec.js -g 'System Orchestrator'"
        ;;
    "license")
        echo "🔑 Running license flow tests only"
        TEST_COMMAND="npx playwright test e2e/warpcore_full_ui_system.spec.js -g 'License'"
        ;;
    "pap")
        echo "🔄 Running PAP architecture tests only"
        TEST_COMMAND="npx playwright test e2e/warpcore_full_ui_system.spec.js -g 'PAP'"
        ;;
    "help")
        echo "Usage: $0 [mode]"
        echo ""
        echo "Modes:"
        echo "  default    - Run all tests in headless mode"
        echo "  headed     - Run with browser visible"
        echo "  debug      - Run in interactive debug mode"
        echo "  ui         - Run with Playwright UI"
        echo "  performance - Run performance tests only"
        echo "  system     - Run system orchestrator tests only"
        echo "  license    - Run license flow tests only" 
        echo "  pap        - Run PAP architecture tests only"
        echo "  help       - Show this help"
        echo ""
        echo "Examples:"
        echo "  $0                    # Run all tests"
        echo "  $0 headed            # Run with browser visible"
        echo "  $0 debug             # Interactive debugging"
        echo "  $0 system            # Test system orchestrator only"
        echo ""
        exit 0
        ;;
    "default")
        echo "🤖 Running in headless mode (default)"
        ;;
    *)
        echo "❌ Unknown mode: $1"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac

echo "Command: $TEST_COMMAND"
echo ""

# Run the tests
echo "🚀 Executing tests..."
eval $TEST_COMMAND

# Get test results
TEST_EXIT_CODE=$?

echo ""
echo "======================================"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "🎉 All WARPCORE UI tests passed!"
    echo ""
    echo "✅ System Orchestrator: Data → Web → API layers tested"
    echo "✅ Provider-Abstraction-Pattern: UI flow validated"
    echo "✅ License Management: UI components tested"
    echo "✅ User Workflows: End-to-end flows verified"
    echo "✅ Performance: System responsiveness validated"
    echo ""
    echo "🌊 WARPCORE Full UI System: Ready for production! 🚀"
else
    echo "❌ Some WARPCORE UI tests failed (exit code: $TEST_EXIT_CODE)"
    echo ""
    echo "Check the test output above for details."
    echo "Common issues:"
    echo "  - Server not fully initialized (wait for system orchestrator)"
    echo "  - UI components loaded differently than expected"
    echo "  - Network timeouts (system orchestrator can take time)"
    echo ""
    echo "To debug:"
    echo "  $0 debug     # Interactive debugging mode"
    echo "  $0 headed    # Run with browser visible"
fi

exit $TEST_EXIT_CODE