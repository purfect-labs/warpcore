#!/usr/bin/env python3
"""
WARPCORE Main Entry Point
Thin launcher that starts API server and opens UI
"""

import sys
import webbrowser
import threading
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def start_api_server():
    """Start the WARPCORE API server"""
    from src.api.main import WARPCOREAPIServer
    import uvicorn
    
    # Create and configure server
    server = WARPCOREAPIServer()
    
    # Start FastAPI server
    uvicorn.run(
        server.app, 
        host="127.0.0.1", 
        port=8000,
        log_level="info"
    )

def open_ui():
    """Open the WARPCORE UI in browser"""
    # Wait for server to start
    time.sleep(2)
    
    # Open browser
    webbrowser.open("http://127.0.0.1:8000")

def main():
    """Main entry point"""
    print("🚀 Starting WARPCORE Command Center...")
    
    # Start UI in background
    ui_thread = threading.Thread(target=open_ui, daemon=True)
    ui_thread.start()
    
    # Start API server (blocking)
    start_api_server()

if __name__ == "__main__":
    main()