#!/usr/bin/env python3
"""
Quick launcher for the WARPCORE Agent Dashboard.
Run this to immediately start the dashboard.
"""

import os
import sys
from pathlib import Path

def main():
    """Launch the dashboard with sensible defaults."""
    # Change to the docs directory
    docs_dir = Path(__file__).parent
    os.chdir(docs_dir)
    
    print("🚀 Launching WARPCORE Agent Dashboard...")
    
    # Import and run the server
    try:
        from serve_dashboard import start_dashboard_server
        start_dashboard_server(port=None, open_browser=True)
    except ImportError:
        print("❌ Error: Could not import dashboard server")
        print("💡 Make sure you're in the correct directory:")
        print(f"   {docs_dir}")
        return 1
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())