#!/bin/bash

# WARPCORE Analytics Testing Framework Runner
# Efficient test execution with comprehensive reporting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
TEST_DIR="tests"
RESULTS_DIR="tests/results"
SERVER_PID=""
SERVER_LOG="/tmp/warp_test_server.log"
SERVER_PORT=8080

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Setup functions
setup_test_environment() {
    log_step "Setting up test environment..."
    
    # Create results directory
    mkdir -p "$RESULTS_DIR"/{html-report,screenshots,videos,traces}
    
    # Check if Node.js is available
    if ! command -v node &> /dev/null; then
        log_error "Node.js is required but not installed"
        exit 1
    fi
    
    # Install dependencies if needed
    if [ ! -d "$TEST_DIR/node_modules" ]; then
        log_info "Installing test dependencies..."
        cd "$TEST_DIR" && npm install && cd ..
    fi
    
    # Install Playwright browsers if needed
    if [ ! -d "$HOME/.cache/ms-playwright" ] && [ ! -d "$HOME/Library/Caches/ms-playwright" ]; then
        log_info "Installing Playwright browsers..."
        cd "$TEST_DIR" && npx playwright install && cd ..
    fi
    
    log_success "Test environment ready"
}

start_test_server() {
    log_step "Starting WARPCORE server for testing..."
    
    # Check if server is already running
    if lsof -Pi :$SERVER_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "Server already running on port $SERVER_PORT"
        return 0
    fi
    
    # Start server in background
    nohup python3 server.py > "$SERVER_LOG" 2>&1 &
    SERVER_PID=$!
    
    # Wait for server to be ready
    log_info "Waiting for server to start..."
    for i in {1..30}; do
        if curl -s "http://localhost:$SERVER_PORT" > /dev/null 2>&1; then
            log_success "Server started successfully (PID: $SERVER_PID)"
            return 0
        fi
        sleep 1
    done
    
    log_error "Server failed to start within 30 seconds"
    cat "$SERVER_LOG"
    exit 1
}

stop_test_server() {
    if [ -n "$SERVER_PID" ]; then
        log_step "Stopping test server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
        log_success "Server stopped"
    fi
    
    # Kill any remaining servers on the port
    lsof -ti:$SERVER_PORT | xargs kill -9 2>/dev/null || true
}

run_tests() {
    local test_type="$1"
    local project="$2"
    
    log_step "Running $test_type tests..."
    
    cd "$TEST_DIR"
    
    case "$test_type" in
        "ui")
            npx playwright test tests/playwright/ui --project="$project" --reporter=html,line,json
            ;;
        "api")
            npx playwright test tests/playwright/api --project=api-tests --reporter=html,line,json
            ;;
        "flows")
            npx playwright test tests/playwright/flows --project=user-flows --reporter=html,line,json
            ;;
        "all")
            npx playwright test --project=chrome-desktop --project=api-tests --project=user-flows --reporter=html,line,json
            ;;
        "cross-browser")
            npx playwright test --project=chrome-desktop --project=firefox-desktop --reporter=html,line,json
            ;;
        "mobile")
            npx playwright test --project=mobile-chrome --reporter=html,line,json
            ;;
        "performance")
            npx playwright test tests/playwright/flows/user-journey.spec.js -g "performance|load|benchmark" --reporter=html,line,json
            ;;
        "accessibility")
            npx playwright test tests/playwright/ui/dashboard-ui.spec.js -g "accessibility" --reporter=html,line,json
            ;;
        *)
            npx playwright test --reporter=html,line,json
            ;;
    esac
    
    cd ..
}

generate_report() {
    log_step "Generating comprehensive test report..."
    
    cd "$TEST_DIR"
    
    # Generate HTML report
    npx playwright show-report --host=127.0.0.1 --port=9323 &
    REPORT_PID=$!
    
    log_success "Test report available at: http://127.0.0.1:9323"
    log_info "Report PID: $REPORT_PID (kill manually when done viewing)"
    
    # Generate summary
    if [ -f "tests/results/test-results.json" ]; then
        local total_tests=$(jq '.suites | map(.specs | length) | add' tests/results/test-results.json 2>/dev/null || echo "N/A")
        local passed_tests=$(jq '[.suites[].specs[].tests[] | select(.results[].status == "passed")] | length' tests/results/test-results.json 2>/dev/null || echo "N/A")
        local failed_tests=$(jq '[.suites[].specs[].tests[] | select(.results[].status == "failed")] | length' tests/results/test-results.json 2>/dev/null || echo "N/A")
        
        log_info "Test Summary:"
        echo "  Total Tests: $total_tests"
        echo "  Passed: $passed_tests"
        echo "  Failed: $failed_tests"
        
        if [ "$failed_tests" != "0" ] && [ "$failed_tests" != "N/A" ]; then
            log_warning "Some tests failed - check the detailed report"
        else
            log_success "All tests passed!"
        fi
    fi
    
    cd ..
}

cleanup() {
    log_step "Cleaning up..."
    stop_test_server
    
    # Kill report server if running
    pkill -f "playwright show-report" 2>/dev/null || true
    
    log_success "Cleanup complete"
}

# Main execution
main() {
    local test_type="${1:-all}"
    local project="${2:-chrome-desktop}"
    
    # Set up cleanup trap
    trap cleanup EXIT INT TERM
    
    log_info "🚀 Starting WARPCORE Analytics Test Suite"
    log_info "Test Type: $test_type"
    log_info "Project: $project"
    echo ""
    
    # Setup
    setup_test_environment
    start_test_server
    
    # Run tests
    run_tests "$test_type" "$project"
    
    # Generate report
    generate_report
    
    log_success "🎉 Test execution complete!"
}

# Help function
show_help() {
    echo "WARPCORE Analytics Testing Framework"
    echo ""
    echo "Usage: $0 [TEST_TYPE] [PROJECT]"
    echo ""
    echo "Test Types:"
    echo "  ui              - Run UI tests only"
    echo "  api             - Run API tests only" 
    echo "  flows           - Run user journey flow tests"
    echo "  all             - Run all test suites (default)"
    echo "  cross-browser   - Run tests across Chrome and Firefox"
    echo "  mobile          - Run mobile device tests"
    echo "  performance     - Run performance benchmark tests"
    echo "  accessibility   - Run accessibility tests"
    echo ""
    echo "Projects:"
    echo "  chrome-desktop  - Desktop Chrome (default)"
    echo "  firefox-desktop - Desktop Firefox"
    echo "  mobile-chrome   - Mobile Chrome"
    echo "  api-tests       - API-only tests"
    echo "  user-flows      - Integration flow tests"
    echo ""
    echo "Examples:"
    echo "  $0                          # Run all tests with Chrome"
    echo "  $0 ui chrome-desktop        # Run UI tests on Chrome"
    echo "  $0 api                      # Run API tests only"
    echo "  $0 flows                    # Run user journey tests"
    echo "  $0 cross-browser            # Run cross-browser tests"
    echo "  $0 performance              # Run performance tests"
    echo ""
    echo "Environment Variables:"
    echo "  CI=true                     # Run in CI mode (more retries, etc.)"
    echo "  HEADED=true                 # Run tests in headed mode"
    echo "  DEBUG=true                  # Run tests in debug mode"
    echo ""
}

# Parse command line arguments
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

# Set environment-based options
if [ "$CI" = "true" ]; then
    export PLAYWRIGHT_CI=true
    log_info "Running in CI mode"
fi

if [ "$HEADED" = "true" ]; then
    export PLAYWRIGHT_HEADED=true
    log_info "Running in headed mode"
fi

if [ "$DEBUG" = "true" ]; then
    export PLAYWRIGHT_DEBUG=true
    log_info "Running in debug mode"
fi

# Execute main function
main "$@"