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

# Check if .data directory exists
if [ ! -d ".data" ]; then
    echo "📁 Creating .data directory..."
    mkdir -p .data
    echo "ℹ️  No existing workflow data found. Demo data will be created."
else
    JSON_COUNT=$(find .data -name "*.json" | wc -l)
    echo "📊 Found $JSON_COUNT JSON data files in .data/"
fi

# Start the API server in background
echo "🔧 Starting WARPCORE Real Data API server..."
python3 api-server.py &
API_PID=$!

# Give the server a moment to start
sleep 2

# Check if server started successfully
if curl -s http://localhost:8080/health > /dev/null; then
    echo "✅ API server running at http://localhost:8080"
    
    # Open the dashboard in default browser
    if command -v open &> /dev/null; then
        # macOS
        echo "🌐 Opening dashboard in browser..."
        open http://localhost:8080
    elif command -v xdg-open &> /dev/null; then
        # Linux
        echo "🌐 Opening dashboard in browser..."
        xdg-open http://localhost:8080
    else
        echo "🌐 Dashboard available at: http://localhost:8080"
        echo "   Real Data Dashboard: http://localhost:8080/real-data-dashboard.html"
        echo "   Live Dashboard: http://localhost:8080/index.html"
    fi
    
    echo ""
    echo "✨ WARPCORE Real Data Dashboard is now running!"
    echo "📊 Real Data Dashboard: http://localhost:8080/real-data-dashboard.html"
    echo "⚡ Live Dashboard: http://localhost:8080/index.html"
    echo "🔍 API Endpoints:"
    echo "   • Execution Logs: http://localhost:8080/api/execution-logs"
    echo "   • Statistics: http://localhost:8080/api/stats"
    echo "   • Health Check: http://localhost:8080/health"
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