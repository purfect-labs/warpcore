#!/usr/bin/env python3
"""
Simple WARPCORE server for Electron app
Just runs your regular WARPCORE web server
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import and run your normal WARPCORE server
from web.main import run_server

if __name__ == "__main__":
    print("🚀 Starting WARPCORE server for Electron...")
    
    # Set environment variables to prevent terminal auth and loops
    os.environ['WARPCORE_NATIVE_MODE'] = '1'
    os.environ['WARPCORE_NO_TERMINAL_AUTH'] = '1'
    os.environ['WARPCORE_DISABLE_AUTO_AUTH'] = '1'
    os.environ['WARPCORE_NO_CLOUD_INIT'] = '1'
    os.environ['AWS_PROFILE'] = 'none'
    os.environ['DISABLE_AWS_AUTH'] = '1'
    os.environ['DISABLE_GCP_AUTH'] = '1'
    
    run_server()
