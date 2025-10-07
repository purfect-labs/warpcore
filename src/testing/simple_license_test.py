#!/usr/bin/env python3
"""
Simple WARPCORE License Provider Test - WARP FAKE SUB TEST DEMO
Direct test of license provider without complex imports
"""

import asyncio
import sys
import json
from pathlib import Path

# Add the src directory to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

# Add api path
api_path = src_path / 'api'
sys.path.insert(0, str(api_path))

async def test_license_provider():
    """Test the license provider directly"""
    try:
        # Direct imports to avoid package issues
        sys.path.insert(0, str(src_path / 'api' / 'providers' / 'core'))
        from base_provider import BaseProvider
        
        sys.path.insert(0, str(src_path / 'api' / 'providers' / 'license'))
        from license_provider import LicenseProvider
        
        print("✓ Imports successful")
        
        # Create provider instance
        provider = LicenseProvider()
        print(f"✓ License provider created")
        print(f"  Native manager available: {provider._native_manager is not None}")
        
        # Test trial license generation
        print("\n🧪 Testing trial license generation...")
        trial_result = await provider.generate_trial_license("warp-test@example.com", 7)
        print(f"Trial generation result: {json.dumps(trial_result, indent=2)}")
        
        if trial_result.get("success"):
            trial_key = trial_result.get("license_key")
            print(f"Generated trial key length: {len(trial_key) if trial_key else 0}")
            
            # Test license validation
            print("\n🧪 Testing license validation...")
            validation_result = await provider.validate_license_key(trial_key)
            print(f"Validation result: {json.dumps(validation_result, indent=2)}")
            
            # Test license activation (without keychain to avoid permissions)
            print(f"\n🧪 Testing native manager availability...")
            if provider._native_manager:
                print("✓ Native manager is available")
                try:
                    # Test native manager methods if available
                    # This should fail gracefully if native manager isn't working
                    native_info = provider._native_manager.get_license_info()
                    print(f"Native manager info: {native_info}")
                except Exception as e:
                    print(f"Native manager test failed (expected): {e}")
            else:
                print("ℹ️ Native manager not available, using fallback mode")
        
        print("\n🎉 Basic license provider integration test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Simple WARPCORE License Provider Test")
    print("=" * 50)
    asyncio.run(test_license_provider())