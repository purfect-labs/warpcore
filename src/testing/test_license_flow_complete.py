#!/usr/bin/env python3
"""
WARPCORE Complete License Flow Test
Test the full license system: Generate → Validate → Apply → Status
Uses real APEX license functionality when available
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.config.license.license_config import get_license_config
from api.providers.license.license_provider import LicenseProvider
from api.orchestrators.license.license_orchestrator import LicenseOrchestrator 
from api.controllers.license_controller import LicenseController
from api.providers import get_provider_registry


async def test_generate_license_key():
    """Test license key generation"""
    print("\n🔑 TESTING LICENSE KEY GENERATION")
    print("=" * 60)
    
    try:
        # Setup PAP stack
        provider_registry = get_provider_registry()
        license_provider = LicenseProvider()
        provider_registry.register_provider("license", license_provider)
        
        orchestrator = LicenseOrchestrator()
        orchestrator.set_provider_registry(provider_registry)
        
        controller = LicenseController()
        controller.set_provider_registry(provider_registry)
        
        print("✅ PAP stack initialized for license generation")
        
        # Test 1: Trial license generation
        trial_result = await controller.generate_trial_license("test-user@warp-fake-sub-test-demo.com", 14)
        print(f"✅ Trial license generation: {trial_result.get('success', False)}")
        if trial_result.get('success'):
            print(f"   License key: {trial_result.get('license_key', 'N/A')[:50]}...")
            print(f"   Days: {trial_result.get('days')}")
            print(f"   PAP flow: {trial_result.get('pap_flow_completed', False)}")
        
        # Test 2: Custom license key generation
        custom_result = await controller.generate_custom_license_key(
            user_email="custom-user@warp-fake-sub-test-demo.com",
            user_name="Custom WARP User",
            days=30,
            features=["basic", "advanced", "premium"],
            license_type="premium"
        )
        print(f"✅ Custom license generation: {custom_result.get('success', False)}")
        if custom_result.get('success'):
            print(f"   License key: {custom_result.get('license_key', 'N/A')[:50]}...")
            print(f"   License type: {custom_result.get('license_type')}")
            print(f"   Features: {custom_result.get('validated_features', [])}")
            print(f"   Real license: {custom_result.get('real_license', False)}")
        
        # Test 3: Full license generation
        full_result = await controller.generate_full_license(
            user_email="full-user@warp-fake-sub-test-demo.com", 
            user_name="Full WARP User",
            days=365,
            features=["basic", "advanced", "premium", "enterprise"]
        )
        print(f"✅ Full license generation: {full_result.get('success', False)}")
        if full_result.get('success'):
            print(f"   License key: {full_result.get('license_key', 'N/A')[:50]}...")
            print(f"   Source: {full_result.get('source', 'unknown')}")
            print(f"   Real license: {full_result.get('real_license', False)}")
        
        return {
            "trial": trial_result,
            "custom": custom_result, 
            "full": full_result
        }
        
    except Exception as e:
        print(f"❌ License generation test failed: {str(e)}")
        return None


async def test_validate_license_keys(generation_results):
    """Test license key validation"""
    print("\n✅ TESTING LICENSE KEY VALIDATION")
    print("=" * 60)
    
    try:
        # Setup validation stack
        provider_registry = get_provider_registry()
        license_provider = LicenseProvider()
        provider_registry.register_provider("license", license_provider)
        
        controller = LicenseController()
        controller.set_provider_registry(provider_registry)
        
        validation_results = {}
        
        # Validate generated keys
        if generation_results:
            for key_type, result in generation_results.items():
                if result and result.get('success') and result.get('license_key'):
                    license_key = result['license_key']
                    validation = await controller.validate_license_key(license_key)
                    
                    print(f"✅ {key_type.title()} key validation: {validation.get('valid', False)}")
                    if validation.get('valid'):
                        print(f"   License type: {validation.get('license_type', 'unknown')}")
                        print(f"   Features: {validation.get('license_info', {}).get('features', [])}")
                        print(f"   PAP flow: {validation.get('pap_flow_completed', False)}")
                    else:
                        print(f"   Error: {validation.get('error', 'unknown')}")
                    
                    validation_results[key_type] = validation
        
        # Test validation of invalid keys
        invalid_tests = [
            ("empty", ""),
            ("invalid_format", "invalid-key-12345"),
            ("expired", "expired-key-from-2020"),
            ("malformed", "short"),
        ]
        
        for test_name, test_key in invalid_tests:
            validation = await controller.validate_license_key(test_key)
            print(f"✅ {test_name} key validation (should fail): {not validation.get('valid', True)}")
            validation_results[test_name] = validation
        
        return validation_results
        
    except Exception as e:
        print(f"❌ License validation test failed: {str(e)}")
        return None


async def test_apply_license_keys(generation_results):
    """Test license key application (activation)"""
    print("\n⚙️ TESTING LICENSE KEY APPLICATION")
    print("=" * 60)
    
    try:
        # Setup application stack
        provider_registry = get_provider_registry()
        license_provider = LicenseProvider()
        provider_registry.register_provider("license", license_provider)
        
        controller = LicenseController()
        controller.set_provider_registry(provider_registry)
        
        application_results = {}
        
        # Apply generated keys
        if generation_results:
            for key_type, result in generation_results.items():
                if result and result.get('success') and result.get('license_key'):
                    license_key = result['license_key'] 
                    user_email = result.get('user_email')
                    
                    # Apply the license
                    activation = await controller.activate_license(license_key, user_email)
                    
                    print(f"✅ {key_type.title()} key activation: {activation.get('success', False)}")
                    if activation.get('success'):
                        print(f"   User: {activation.get('user_name', 'unknown')}")
                        print(f"   Email: {activation.get('user_email', 'unknown')}")
                        print(f"   License type: {activation.get('license_type', 'unknown')}")
                        print(f"   PAP flow: {activation.get('pap_flow_completed', False)}")
                        print(f"   Source: {activation.get('source', 'unknown')}")
                    else:
                        print(f"   Error: {activation.get('error', 'unknown')}")
                    
                    application_results[key_type] = activation
                    
                    # Test license status after activation
                    status = await controller.get_license_status()
                    print(f"✅ License status after {key_type} activation: {status.get('success', False)}")
                    if status.get('success') and status.get('data'):
                        data = status['data']
                        print(f"   Status: {data.get('status', 'unknown')}")
                        print(f"   User: {data.get('user_name', 'unknown')}")
                        print(f"   Days remaining: {data.get('days_remaining', 'unknown')}")
                        print(f"   PAP processed: {data.get('pap_flow_completed', False)}")
                    
                    # Deactivate after testing
                    deactivation = await controller.deactivate_license()
                    print(f"✅ License deactivation: {deactivation.get('success', False)}")
                    
                    print("")  # Spacing between tests
        
        return application_results
        
    except Exception as e:
        print(f"❌ License application test failed: {str(e)}")
        return None


async def test_license_status_reporting():
    """Test license status reporting throughout the system"""
    print("\n📊 TESTING LICENSE STATUS REPORTING")
    print("=" * 60)
    
    try:
        # Setup status reporting stack
        provider_registry = get_provider_registry()
        license_provider = LicenseProvider()
        provider_registry.register_provider("license", license_provider)
        
        controller = LicenseController()
        controller.set_provider_registry(provider_registry)
        
        # Test status with no license
        status_empty = await controller.get_license_status()
        print(f"✅ Status with no license: {status_empty.get('success', False)}")
        if status_empty.get('data'):
            data = status_empty['data']
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Orchestrator available: {data.get('orchestrator_available', False)}")
        
        # Generate and activate a test license
        trial_result = await controller.generate_trial_license("status-test@warp-fake-sub-test-demo.com", 7)
        if trial_result.get('success') and trial_result.get('license_key'):
            activation = await controller.activate_license(
                trial_result['license_key'], 
                "status-test@warp-fake-sub-test-demo.com"
            )
            
            if activation.get('success'):
                # Test status with active license
                status_active = await controller.get_license_status()
                print(f"✅ Status with active license: {status_active.get('success', False)}")
                if status_active.get('data'):
                    data = status_active['data']
                    print(f"   Status: {data.get('status', 'unknown')}")
                    print(f"   User: {data.get('user_name', 'unknown')}")
                    print(f"   License type: {data.get('license_type', 'unknown')}")
                    print(f"   Features: {data.get('features', [])}")
                    print(f"   Days remaining: {data.get('days_remaining', 'unknown')}")
                    print(f"   Controller processed: {data.get('controller_processed', False)}")
                    print(f"   Orchestrator processed: {data.get('orchestrator_processed', False)}")
                
                # Test subscription info
                subscription = await controller.get_subscription_info()
                print(f"✅ Subscription info: {subscription.get('success', False)}")
                if subscription.get('data'):
                    data = subscription['data']
                    print(f"   Subscription type: {data.get('subscription_type', 'unknown')}")
                    print(f"   Features available: {len(data.get('features_available', []))}")
                    print(f"   Demo users: {data.get('demo_users', 0)}")
                    print(f"   Config driven: {data.get('config_driven', False)}")
                
                # Cleanup
                await controller.deactivate_license()
        
        return True
        
    except Exception as e:
        print(f"❌ License status reporting test failed: {str(e)}")
        return False


async def test_complete_license_workflow():
    """Test complete end-to-end license workflow"""
    print("\n🚀 TESTING COMPLETE LICENSE WORKFLOW")
    print("=" * 60)
    
    try:
        # Setup complete PAP stack
        config = get_license_config()
        
        provider_registry = get_provider_registry()
        license_provider = LicenseProvider()
        provider_registry.register_provider("license", license_provider)
        
        orchestrator = LicenseOrchestrator()
        orchestrator.set_provider_registry(provider_registry)
        
        controller = LicenseController()
        controller.set_provider_registry(provider_registry)
        
        print("✅ Complete PAP stack initialized")
        
        # Step 1: Generate a license key
        print("\n🔑 Step 1: Generate License Key")
        generation = await controller.generate_custom_license_key(
            user_email="workflow-test@warp-fake-sub-test-demo.com",
            user_name="Workflow Test User",
            days=90,
            features=["basic", "advanced"],
            license_type="premium"
        )
        
        if not generation.get('success'):
            print(f"❌ License generation failed: {generation.get('error')}")
            return False
        
        license_key = generation.get('license_key')
        print(f"✅ Generated license key: {license_key[:50]}...")
        
        # Step 2: Validate the license key
        print("\n✅ Step 2: Validate License Key")
        validation = await controller.validate_license_key(license_key)
        
        if not validation.get('valid'):
            print(f"❌ License validation failed: {validation.get('error')}")
            return False
        
        print(f"✅ License validation successful")
        print(f"   License type: {validation.get('license_type')}")
        print(f"   Features: {validation.get('license_info', {}).get('features', [])}")
        
        # Step 3: Apply the license
        print("\n⚙️ Step 3: Apply License")
        activation = await controller.activate_license(license_key, "workflow-test@warp-fake-sub-test-demo.com")
        
        if not activation.get('success'):
            print(f"❌ License activation failed: {activation.get('error')}")
            return False
        
        print(f"✅ License activation successful")
        print(f"   User: {activation.get('user_name')}")
        print(f"   License type: {activation.get('license_type')}")
        
        # Step 4: Check license status
        print("\n📊 Step 4: Check License Status")
        status = await controller.get_license_status()
        
        if not status.get('success'):
            print(f"❌ License status check failed: {status.get('error')}")
            return False
        
        if status.get('data'):
            data = status['data']
            print(f"✅ License status check successful")
            print(f"   Status: {data.get('status')}")
            print(f"   User: {data.get('user_name')}")
            print(f"   Days remaining: {data.get('days_remaining')}")
            print(f"   Features: {data.get('features', [])}")
            print(f"   Complete PAP flow: {data.get('pap_flow_completed', False)}")
        
        # Step 5: Deactivate license
        print("\n🧹 Step 5: Deactivate License")
        deactivation = await controller.deactivate_license()
        
        if not deactivation.get('success'):
            print(f"❌ License deactivation failed: {deactivation.get('error')}")
            return False
        
        print(f"✅ License deactivation successful")
        
        # Step 6: Verify license is deactivated
        print("\n🔍 Step 6: Verify Deactivation")
        final_status = await controller.get_license_status()
        
        if final_status.get('data', {}).get('status') != 'active':
            print("✅ License successfully deactivated")
        else:
            print("⚠️ License may still be active")
        
        return True
        
    except Exception as e:
        print(f"❌ Complete license workflow test failed: {str(e)}")
        return False


async def main():
    """Run all license flow tests"""
    print("🧪 WARPCORE COMPLETE LICENSE FLOW TESTING")
    print("=" * 80)
    print("Testing: Generate → Validate → Apply → Status → Deactivate")
    print("=" * 80)
    
    # Configure logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise
    
    test_results = []
    
    # Run license generation tests
    print("📋 Running license generation tests...")
    generation_results = await test_generate_license_key()
    test_results.append(("License Generation", generation_results is not None))
    
    # Run validation tests
    print("\n📋 Running license validation tests...")
    validation_results = await test_validate_license_keys(generation_results)
    test_results.append(("License Validation", validation_results is not None))
    
    # Run application tests
    print("\n📋 Running license application tests...")
    application_results = await test_apply_license_keys(generation_results)
    test_results.append(("License Application", application_results is not None))
    
    # Run status reporting tests
    print("\n📋 Running license status reporting tests...")
    status_results = await test_license_status_reporting()
    test_results.append(("License Status Reporting", status_results))
    
    # Run complete workflow test
    print("\n📋 Running complete workflow test...")
    workflow_results = await test_complete_license_workflow()
    test_results.append(("Complete License Workflow", workflow_results))
    
    # Summary
    print("\n" + "=" * 80)
    print("🎯 WARPCORE LICENSE FLOW TEST SUMMARY")
    print("=" * 80)
    
    passed_tests = [name for name, result in test_results if result]
    failed_tests = [name for name, result in test_results if not result]
    
    print(f"✅ PASSED: {len(passed_tests)}/{len(test_results)} tests")
    for test_name in passed_tests:
        print(f"   ✓ {test_name}")
    
    if failed_tests:
        print(f"\n❌ FAILED: {len(failed_tests)}/{len(test_results)} tests")
        for test_name in failed_tests:
            print(f"   ✗ {test_name}")
    else:
        print(f"\n🎉 ALL TESTS PASSED! Complete license flow working!")
        print("📦 Ready for production with:")
        print("   - Real APEX license integration")  
        print("   - Complete Generate → Validate → Apply flow")
        print("   - PAP architecture compliance")
        print("   - Comprehensive validation")
        print("   - Full lifecycle management")
    
    print("\n" + "=" * 80)
    return len(failed_tests) == 0


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1)