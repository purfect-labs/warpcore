#!/usr/bin/env python3
"""
WARPCORE Dashboard Server
Simple HTTP server to serve the comprehensive agent dashboard.
"""

import os
import sys
import socket
from pathlib import Path
import http.server
import socketserver
import webbrowser
from urllib.parse import urlparse

class DashboardHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler for the dashboard."""
    
    def end_headers(self):
        # Add CORS headers for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def log_message(self, format, *args):
        # Custom log format
        print(f"[DASHBOARD] {self.address_string()} - {format % args}")

def find_free_port(start_port=8080, max_port=9000):
    """Find a free port to use for the server."""
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise OSError("No free ports found")

def start_dashboard_server(port=None, open_browser=True):
    """Start the dashboard server."""
    # Change to the docs directory
    docs_dir = Path(__file__).parent
    os.chdir(docs_dir)
    
    # Find a free port
    if port is None:
        port = find_free_port()
    
    # Create server
    with socketserver.TCPServer(("localhost", port), DashboardHTTPRequestHandler) as httpd:
        print(f"\n🚀 WARPCORE Agent Dashboard Server")
        print(f"━" * 50)
        print(f"📍 Serving from: {docs_dir}")
        print(f"🌐 URL: http://localhost:{port}")
        print(f"📊 Dashboard: http://localhost:{port}/comprehensive_dashboard.html")
        print(f"🔄 Press Ctrl+C to stop the server")
        print(f"━" * 50)
        
        # Open browser if requested
        if open_browser:
            dashboard_url = f"http://localhost:{port}/comprehensive_dashboard.html"
            print(f"🔓 Opening dashboard in browser...")
            try:
                webbrowser.open(dashboard_url)
            except Exception as e:
                print(f"Could not open browser automatically: {e}")
                print(f"Please manually open: {dashboard_url}")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n\n🛑 Dashboard server stopped.")
            httpd.shutdown()

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='WARPCORE Agent Dashboard Server')
    parser.add_argument('--port', '-p', type=int, default=None,
                        help='Port to serve on (default: find free port starting from 8080)')
    parser.add_argument('--no-browser', '-n', action='store_true',
                        help='Don\'t automatically open browser')
    parser.add_argument('--regenerate-data', '-r', action='store_true',
                        help='Regenerate dashboard data before starting server')
    
    args = parser.parse_args()
    
    # Regenerate data if requested
    if args.regenerate_data:
        print("🔄 Regenerating dashboard data...")
        try:
            from dashboard_data_loader import DashboardDataLoader
            loader = DashboardDataLoader()
            loader.save_dashboard_data()
            print("✅ Dashboard data regenerated")
        except Exception as e:
            print(f"❌ Error regenerating data: {e}")
            return 1
    
    # Check if dashboard data exists
    data_file = Path(__file__).parent / "dashboard_data.json"
    if not data_file.exists():
        print("⚠️  Dashboard data not found. Generating...")
        try:
            from dashboard_data_loader import DashboardDataLoader
            loader = DashboardDataLoader()
            loader.save_dashboard_data()
            print("✅ Dashboard data generated")
        except Exception as e:
            print(f"❌ Error generating data: {e}")
            print("💡 Try running: python dashboard_data_loader.py")
            return 1
    
    # Start server
    try:
        start_dashboard_server(port=args.port, open_browser=not args.no_browser)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())