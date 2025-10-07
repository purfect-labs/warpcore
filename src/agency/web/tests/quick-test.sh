#!/bin/bash

# Quick WARPCORE Test Runner - No Blocking, Fail Fast
set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 WARPCORE Quick Test Runner${NC}"

# Check if server is running
if ! curl -s http://localhost:8080 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Server not running - starting in background...${NC}"
    cd .. && nohup python3 server.py > /tmp/quick_test_server.log 2>&1 &
    SERVER_PID=$!
    
    # Wait max 10 seconds for server
    for i in {1..10}; do
        if curl -s http://localhost:8080 > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Server started${NC}"
            break
        fi
        sleep 1
    done
    cd tests
else
    echo -e "${GREEN}✅ Server already running${NC}"
fi

# Run tests with fail-fast and no blocking
TEST_TYPE=${1:-api}

case "$TEST_TYPE" in
    "api")
        echo -e "${GREEN}🧪 Running API tests...${NC}"
        timeout 60s npx playwright test api/api-endpoints.spec.js --project=api-tests --max-failures=1 --reporter=line || true
        ;;
    "ui")
        echo -e "${GREEN}🧪 Running UI tests...${NC}"
        timeout 120s npx playwright test ui/dashboard-ui.spec.js --project=chrome-desktop --max-failures=3 --reporter=line || true
        ;;
    "flows")
        echo -e "${GREEN}🧪 Running flow tests...${NC}"
        timeout 180s npx playwright test flows/user-journey.spec.js --project=user-flows --max-failures=2 --reporter=line || true
        ;;
    *)
        echo -e "${GREEN}🧪 Running all tests...${NC}"
        timeout 300s npx playwright test --max-failures=5 --reporter=line || true
        ;;
esac

# Cleanup
if [ ! -z "$SERVER_PID" ]; then
    echo -e "${YELLOW}🧹 Stopping test server...${NC}"
    kill $SERVER_PID 2>/dev/null || true
fi

echo -e "${GREEN}✅ Test run complete${NC}"