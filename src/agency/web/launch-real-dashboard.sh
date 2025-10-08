#!/bin/bash

# WARPCORE Real Data Dashboard Launcher
# This script starts the API server and opens the real data dashboard

echo "🚀 WARPCORE Real Data Dashboard Launcher"
echo "========================================"

# Check for required dependencies
echo "📋 Checking dependencies..."

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check for pip packages
if ! python3 -c "import flask" &> /dev/null; then
    echo "⚙️  Installing Flask..."
    pip3 install flask flask-cors
fi

# Change to the warpcore root directory to find .data
cd /Users/shawn_meredith/code/pets/warpcore

# Check if .data directory exists
if [ ! -d ".data" ]; then
    echo "📁 Creating .data directory..."
    mkdir -p .data
    echo "ℹ️  No existing workflow data found. Demo data will be created."
else
    JSON_COUNT=$(find .data -name "*.json" | wc -l)
    echo "📊 Found $JSON_COUNT JSON data files in .data/"
fi

# Go back to web directory for server
cd src/agency/web

# Start the API server in background
echo "🔧 Starting WARPCORE Real Data API server..."
python3 api-server.py &
API_PID=$!

# Give the server a moment to start
sleep 2

# Check if server started successfully
if curl -s http://localhost:8081/health > /dev/null; then
    echo "✅ API server running at http://localhost:8081"
    
    # Open the dashboard in default browser
    if command -v open &> /dev/null; then
        # macOS
        echo "🌐 Opening dashboard in browser..."
        open http://localhost:8081
    elif command -v xdg-open &> /dev/null; then
        # Linux
        echo "🌐 Opening dashboard in browser..."
        xdg-open http://localhost:8081
    else
        echo "🌐 Dashboard available at: http://localhost:8081"
        echo "   WARPCORE Dashboard: http://localhost:8081/index.html"
    fi
    
    echo ""
    echo "✨ WARPCORE Dashboard is now running!"
    echo "📊 WARPCORE Dashboard: http://localhost:8081/index.html"
    echo "🔍 API Endpoints:"
    echo "   • Execution Logs: http://localhost:8081/api/execution-logs"
    echo "   • Workflow Files: http://localhost:8081/api/workflow-files"
    echo "   • Statistics: http://localhost:8081/api/stats"
    echo "   • Health Check: http://localhost:8081/health"
    echo ""
    echo "💡 Features:"
    echo "   • Interactive tabbed interface (Overview, Workflows, Agents, Analytics, Timeline)"
    echo "   • Real-time data from .data/ directory"
    echo "   • Collapsible workflow details"
    echo "   • Agent performance analysis"
    echo "   • Live charts and visualizations"
    echo "   • Timeline filtering and search"
    echo ""
    echo "Press Ctrl+C to stop the server"
    
    # Wait for user interrupt
    trap "echo '🛑 Shutting down...'; kill $API_PID; exit 0" INT
    wait $API_PID

else
    echo "❌ Failed to start API server"
    kill $API_PID 2>/dev/null
    exit 1
fi