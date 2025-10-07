#!/usr/bin/env python3
"""
WARPCORE Native License Integration Test - WARP TEST FRAMEWORK
Test script to validate native license manager integration in license provider
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def test_license_provider_integration():
    """Test the license provider with native manager integration"""
    try:
        # Import the license provider
        from api.providers.license.license_provider import LicenseProvider
        
        # Create provider instance
        provider = LicenseProvider()
        print(f"✓ License provider created successfully")
        print(f"  Native manager available: {provider._native_manager is not None}")
        
        # Test provider status
        status_result = await provider.get_status()
        print(f"✓ Provider status: {status_result}")
        
        # Test license status (should be inactive initially)
        license_status = await provider.get_license_status()
        print(f"✓ License status: {license_status}")
        
        # Test trial license generation
        trial_result = await provider.generate_trial_license("warp-test@example.com", 7)
        print(f"✓ Trial license generation: {trial_result}")
        
        if trial_result.get("success"):
            trial_key = trial_result.get("license_key")
            print(f"  Generated trial key (first 50 chars): {trial_key[:50]}...")
            
            # Test license validation
            validation_result = await provider.validate_license_key(trial_key)
            print(f"✓ Trial license validation: {validation_result}")
            
            # Test license activation
            activation_result = await provider.activate_license(trial_key, "warp-test@example.com")
            print(f"✓ License activation: {activation_result}")
            
            # Test license status after activation
            active_status = await provider.get_license_status()
            print(f"✓ License status after activation: {active_status}")
            
            # Test license deactivation
            deactivation_result = await provider.deactivate_license()
            print(f"✓ License deactivation: {deactivation_result}")
            
            # Test license status after deactivation
            inactive_status = await provider.get_license_status()
            print(f"✓ License status after deactivation: {inactive_status}")
        
        print("\n🎉 All license provider integration tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing WARPCORE Native License Manager Integration")
    print("=" * 60)
    asyncio.run(test_license_provider_integration())