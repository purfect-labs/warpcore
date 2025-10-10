#!/usr/bin/env python3
"""
Debug script to understand license generation flow
"""

import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def test_license_generation():
    """Test the license generation directly"""
    print("🔍 Testing License Generation Flow\n")
    
    try:
        # Import the license provider directly
        from api.providers.license.license_provider import LicenseProvider
        
        # Create provider instance
        provider = LicenseProvider()
        
        print("1. Testing trial license generation...")
        result = await provider.generate_trial_license("test@warpcore.dev", 7)
        print(f"Generation result: {result}")
        
        if result.get("success") and result.get("license_key"):
            license_key = result["license_key"]
            print(f"\n2. Generated license key: {license_key[:50]}...")
            
            print("\n3. Testing license validation...")
            validation = await provider.validate_license_key(license_key)
            print(f"Validation result: {validation}")
            
            print("\n4. Testing license activation...")
            activation = await provider.activate_license(license_key, "test@warpcore.dev")
            print(f"Activation result: {activation}")
            
            print("\n5. Testing license status check...")
            status = await provider.get_license_status()
            print(f"Status result: {status}")
            
        else:
            print("❌ License generation failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_license_generation())