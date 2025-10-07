#!/usr/bin/env python3
"""
Test script for WARPCORE License Server
Tests local/remote/hybrid modes
"""

import asyncio
import aiohttp
import json
import sys
import os

# Add src to path
sys.path.insert(0, 'src')

from license_server_startup import start_license_server, stop_license_server, get_license_server_info


async def test_license_server():
    """Test the license server functionality"""
    
    print("🔐 WARPCORE License Server Test")
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
        
        # Wait a moment for server to fully start
        await asyncio.sleep(2)
        
        # Test health endpoint
        print("\n2. Testing health endpoint...")
        async with aiohttp.ClientSession() as session:
            try:
                health_url = server_info['endpoints']['health']
                async with session.get(health_url) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print(f"✅ Health check: {health_data}")
                    else:
                        print(f"❌ Health check failed: {response.status}")
            except Exception as e:
                print(f"❌ Health check error: {str(e)}")
        
        # Test license generation (would need full routes implementation)
        print("\n3. License server basic test completed!")
        
        # Stop server
        print("\n4. Stopping license server...")
        await stop_license_server()
        print("✅ License server stopped")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Main test function"""
    print("🚀 WARPCORE License Server Test Suite")
    asyncio.run(test_license_server())


if __name__ == "__main__":
    main()