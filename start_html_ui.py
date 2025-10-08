#!/usr/bin/env python3
"""
WARPCORE HTML UI Server Startup
Properly starts the full HTML interface with license UI
"""

import sys
import os
from pathlib import Path

# Add src to Python path to fix relative imports
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Change to src directory to fix relative imports
os.chdir(str(src_path))

print("🌊 WARPCORE HTML UI Server Starting...")
print("=====================================")
print(f"📁 Project root: {project_root}")
print(f"📁 Source path: {src_path}")
print("🔑 License UI with JavaScript fixes applied")
print("🌐 Will be available at: http://localhost:8000")
print()

try:
    # Now import and start the full HTML UI server
    from api.main import WARPCOREAPIServer
    import uvicorn
    
    print("🚀 Starting WARPCORE HTML UI Server...")
    server = WARPCOREAPIServer()
    
    # Start the server
    uvicorn.run(
        server.app, 
        host='0.0.0.0', 
        port=8000,
        log_level='info'
    )
    
except KeyboardInterrupt:
    print("\n👋 WARPCORE HTML UI Server stopped")
    sys.exit(0)
except Exception as e:
    print(f"❌ Failed to start HTML UI server: {e}")
    print("🔧 Make sure all dependencies are installed")
    sys.exit(1)