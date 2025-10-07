#!/usr/bin/env python3
"""
Simple test for WARPCORE License Server
Tests basic functionality without external dependencies
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, 'src')

from license_server_startup import start_license_server, stop_license_server, get_license_server_info


async def test_license_server_basic():
    """Test basic license server functionality"""
    
    print("🔐 WARPCORE License Server Basic Test")
    print("=" * 50)
    
    try:
        # Set mode for testing
        os.environ['WARP_LICENSE_MODE'] = 'local'
        
        # Start license server
        print("1. Starting license server...")
        await start_license_server()
        
        # Get server info
        server_info = get_license_server_info()
        print(f"✅ Server running: {server_info}")
        
        # Basic validation that server is configured correctly
        expected_fields = ['status', 'mode', 'host', 'port', 'endpoints']
        for field in expected_fields:
            if field in server_info:
                print(f"✅ {field}: {server_info[field]}")
            else:
                print(f"❌ Missing field: {field}")
        
        print("\n2. License server configuration test completed!")
        
        # Stop server
        print("\n3. Stopping license server...")
        await stop_license_server()
        print("✅ License server stopped")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Main test function"""
    print("🚀 WARPCORE License Server Basic Test Suite")
    asyncio.run(test_license_server_basic())


if __name__ == "__main__":
    main()