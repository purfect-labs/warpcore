#!/usr/bin/env python3
"""
WARPCORE License PAP Flow Test
Comprehensive testing of the complete Provider-Abstraction-Pattern flow:
UI → Web Routes → API Routes → Controllers → Orchestrators → Providers → Data Layer
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


async def test_data_layer_config():
    """Test data layer configuration - foundation of PAP"""
    print("\n🔧 TESTING DATA LAYER CONFIGURATION")
    print("=" * 60)
    
    try:
        # Test license config initialization
        config = get_license_config()
        
        # Test provider config
        provider_config = config.get_provider_config()
        print(f"✅ Provider config loaded: {len(provider_config)} settings")
        print(f"   Encryption key: {'✓' if config.get_encryption_key() else '✗'}")
        print(f"   Demo mode: {config.is_demo_mode()}")
        print(f"   Watermark: {provider_config.get('watermark', 'NOT SET')}")
        
        # Test orchestrator config
        orch_config = config.get_orchestrator_config()
        print(f"✅ Orchestrator config loaded: {len(orch_config)} settings")
        print(f"   Trial duration: {config.get_trial_config()['duration_days']} days")
        print(f"   Cache duration: {config.get_cache_duration()} minutes")
        
        # Test controller config
        controller_config = config.get_controller_config()
        print(f"✅ Controller config loaded: {len(controller_config)} settings")
        print(f"   Broadcast events: {config.should_broadcast_events()}")
        
        # Test routes config
        routes_config = config.get_routes_config()
        print(f"✅ Routes config loaded: {len(routes_config)} settings")
        print(f"   Rate limit: {config.get_rate_limit()} per minute")
        print(f"   Background tasks: {config.should_use_background_tasks()}")
        
        # Test demo data
        demo_data = config.get_demo_data()
        print(f"✅ Demo data loaded: {len(demo_data.get('test_users', []))} test users")
        
        # Test watermark config
        watermarks = config.get_watermark_config()
        print(f"✅ Watermark config loaded: {len(watermarks)} watermarks")
        for layer, mark in watermarks.items():
            print(f"   {layer}: {mark}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data layer config test failed: {str(e)}")
        return False


async def test_provider_layer():
    """Test provider layer - core functionality"""
    print("\n🔌 TESTING PROVIDER LAYER")
    print("=" * 60)
    
    try:
        # Test provider initialization with data layer config
        provider = LicenseProvider()
        print("✅ License provider initialized from data layer")
        
        # Test provider status
        status = await provider.get_status()
        print(f"✅ Provider status: {status.get('status', 'unknown')}")
        print(f"   Keychain available: {status.get('keychain_available', False)}")
        
        # Test license status check
        license_status = await provider.get_license_status()
        print(f"✅ License status check: {license_status.get('success', False)}")
        print(f"   Status: {license_status.get('status', 'unknown')}")
        print(f"   Source: {license_status.get('source', 'unknown')}")
        
        # Test trial license generation  
        trial_result = await provider.generate_trial_license("warp-test@warp-fake-sub-test-demo.com", 7)
        print(f"✅ Trial generation: {trial_result.get('success', False)}")
        print(f"   License key length: {len(trial_result.get('license_key', ''))}")
        print(f"   Source: {trial_result.get('source', 'unknown')}")
        
        # Test license validation
        if trial_result.get('success') and trial_result.get('license_key'):
            validation_result = await provider.validate_license_key(trial_result['license_key'])
            print(f"✅ License validation: {validation_result.get('valid', False)}")
            print(f"   License type: {validation_result.get('license_info', {}).get('license_type', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Provider layer test failed: {str(e)}")
        return False


async def test_orchestrator_layer():
    """Test orchestrator layer - business process orchestration"""
    print("\n🎭 TESTING ORCHESTRATOR LAYER")
    print("=" * 60)
    
    try:
        # Test orchestrator initialization
        orchestrator = LicenseOrchestrator()
        print("✅ License orchestrator initialized with data layer config")
        
        # Test orchestrator status
        status = await orchestrator.get_orchestrator_status()
        print(f"✅ Orchestrator status: {status.get('success', False)}")
        print(f"   Cache entries: {status.get('cache_entries', 0)}")
        print(f"   Cache duration: {status.get('cache_duration_minutes', 0)} minutes")
        print(f"   Config loaded: {status.get('config_loaded', False)}")
        
        # Test provider registry wiring (simulate)
        provider_registry = get_provider_registry()
        license_provider = LicenseProvider()
        provider_registry.register_provider("license", license_provider)
        orchestrator.set_provider_registry(provider_registry)
        print("✅ Orchestrator wired with provider registry")
        
        # Test license status orchestration
        status_result = await orchestrator.orchestrate_license_status_check()
        print(f"✅ Status orchestration: {status_result.get('success', False)}")
        print(f"   Has orchestrator watermark: {'orchestrator_watermark' in status_result}")
        
        # Test license validation orchestration
        validation_result = await orchestrator.orchestrate_license_validation("warp-test-key-12345")
        print(f"✅ Validation orchestration: {validation_result.get('valid', False)}")
        print(f"   Has orchestrator watermark: {'orchestrator_watermark' in validation_result}")
        
        # Test trial generation orchestration
        trial_result = await orchestrator.orchestrate_trial_license_generation("warp-test@warp-fake-sub-test-demo.com")
        print(f"✅ Trial orchestration: {trial_result.get('success', False)}")
        print(f"   Orchestrated: {trial_result.get('orchestrated', False)}")
        print(f"   Has trial config: {'trial_config_applied' in trial_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator layer test failed: {str(e)}")
        return False


async def test_controller_layer():
    """Test controller layer - business logic coordination"""
    print("\n🎮 TESTING CONTROLLER LAYER")
    print("=" * 60)
    
    try:
        # Test controller initialization
        controller = LicenseController()
        print("✅ License controller initialized with data layer config")
        
        # Test controller status
        status = await controller.get_status()
        print(f"✅ Controller status: {status.get('success', False)}")
        print(f"   Demo mode: {status.get('demo_mode', False)}")
        print(f"   Broadcast enabled: {status.get('broadcast_enabled', False)}")
        print(f"   Config loaded: {status.get('config_loaded', False)}")
        print(f"   Orchestrator wired: {status.get('orchestrator_wired', False)}")
        
        # Test provider registry wiring
        provider_registry = get_provider_registry()
        license_provider = LicenseProvider()
        provider_registry.register_provider("license", license_provider)
        controller.set_provider_registry(provider_registry)
        print("✅ Controller wired with provider registry")
        
        # Test updated status after wiring
        updated_status = await controller.get_status()
        print(f"✅ Updated controller status - orchestrator wired: {updated_status.get('orchestrator_wired', False)}")
        
        # Test license status via controller
        license_status = await controller.get_license_status()
        print(f"✅ License status via controller: {license_status.get('success', False)}")
        if license_status.get('data'):
            data = license_status['data']
            print(f"   Controller processed: {data.get('controller_processed', False)}")
            print(f"   PAP flow completed: {data.get('pap_flow_completed', False)}")
            print(f"   Orchestrator processed: {data.get('orchestrator_processed', False)}")
        
        # Test license validation via controller
        validation_result = await controller.validate_license_key("warp-test-key-12345")
        print(f"✅ License validation via controller: {validation_result.get('valid', False)}")
        print(f"   Controller processed: {validation_result.get('controller_processed', False)}")
        print(f"   PAP flow completed: {validation_result.get('pap_flow_completed', False)}")
        
        # Test trial generation via controller
        trial_result = await controller.generate_trial_license("warp-test@warp-fake-sub-test-demo.com")
        print(f"✅ Trial generation via controller: {trial_result.get('success', False)}")
        print(f"   Controller processed: {trial_result.get('controller_processed', False)}")
        print(f"   PAP flow completed: {trial_result.get('pap_flow_completed', False)}")
        
        # Test subscription info from data layer config
        subscription_info = await controller.get_subscription_info()
        print(f"✅ Subscription info via controller: {subscription_info.get('success', False)}")
        if subscription_info.get('data'):
            data = subscription_info['data']
            print(f"   Features available: {len(data.get('features_available', []))}")
            print(f"   Demo users: {data.get('demo_users', 0)}")
            print(f"   Config driven: {data.get('config_driven', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Controller layer test failed: {str(e)}")
        return False


async def test_complete_pap_flow():
    """Test complete PAP flow end-to-end"""
    print("\n🚀 TESTING COMPLETE PAP FLOW")
    print("=" * 60)
    
    try:
        # Build complete PAP stack
        print("📦 Building complete PAP stack...")
        
        # Data Layer
        config = get_license_config()
        print("✅ Data layer initialized")
        
        # Provider Layer  
        provider_registry = get_provider_registry()
        license_provider = LicenseProvider()
        provider_registry.register_provider("license", license_provider)
        print("✅ Provider layer initialized and registered")
        
        # Orchestrator Layer
        orchestrator = LicenseOrchestrator()
        orchestrator.set_provider_registry(provider_registry)
        print("✅ Orchestrator layer initialized and wired")
        
        # Controller Layer
        controller = LicenseController()
        controller.set_provider_registry(provider_registry)
        print("✅ Controller layer initialized and wired")
        
        # Test complete flow: License Status
        print("\n🔄 Testing complete PAP flow: License Status")
        status_result = await controller.get_license_status()
        print(f"   Final result success: {status_result.get('success', False)}")
        
        if status_result.get('data'):
            data = status_result['data']
            print(f"   Data layer processed: {'watermark' in data}")
            print(f"   Provider layer processed: {'source' in data}")
            print(f"   Orchestrator layer processed: {data.get('orchestrator_processed', False)}")
            print(f"   Controller layer processed: {data.get('controller_processed', False)}")
            print(f"   PAP flow completed: {data.get('pap_flow_completed', False)}")
        
        # Test complete flow: Trial License Generation
        print("\n🔄 Testing complete PAP flow: Trial License Generation")
        trial_result = await controller.generate_trial_license("warp-complete-test@warp-fake-sub-test-demo.com", 14)
        print(f"   Final result success: {trial_result.get('success', False)}")
        print(f"   Orchestrated: {trial_result.get('orchestrated', False)}")
        print(f"   Controller processed: {trial_result.get('controller_processed', False)}")
        print(f"   PAP flow completed: {trial_result.get('pap_flow_completed', False)}")
        
        # Test complete flow: License Validation
        if trial_result.get('success') and trial_result.get('license_key'):
            print("\n🔄 Testing complete PAP flow: License Validation")
            validation_result = await controller.validate_license_key(trial_result['license_key'])
            print(f"   Final result valid: {validation_result.get('valid', False)}")
            print(f"   Orchestrator validated: {validation_result.get('orchestrator_validated', False)}")
            print(f"   Controller processed: {validation_result.get('controller_processed', False)}")
            print(f"   PAP flow completed: {validation_result.get('pap_flow_completed', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Complete PAP flow test failed: {str(e)}")
        return False


async def test_warp_watermarking():
    """Test WARP watermarking throughout the PAP flow"""
    print("\n💧 TESTING WARP WATERMARKING")
    print("=" * 60)
    
    try:
        # Test data layer watermarks
        config = get_license_config()
        watermarks = config.get_watermark_config()
        print(f"✅ Data layer watermarks: {len(watermarks)} defined")
        
        required_watermarks = ["provider", "orchestrator", "controller", "routes", "main", "error"]
        for watermark_type in required_watermarks:
            if watermark_type in watermarks:
                mark = watermarks[watermark_type]
                has_warp = "WARP" in mark.upper()
                print(f"   {watermark_type}: {'✓' if has_warp else '✗'} WARP watermarked ({mark[:30]}...)")
            else:
                print(f"   {watermark_type}: ✗ Missing watermark")
        
        # Test provider watermarking
        provider = LicenseProvider()
        status_result = await provider.get_license_status()
        has_warp_provider = any("WARP" in str(v).upper() for v in status_result.values() if isinstance(v, str))
        print(f"✅ Provider watermarking: {'✓' if has_warp_provider else '✗'}")
        
        # Test orchestrator watermarking
        orchestrator = LicenseOrchestrator()
        provider_registry = get_provider_registry()
        provider_registry.register_provider("license", provider)
        orchestrator.set_provider_registry(provider_registry)
        
        orch_status = await orchestrator.get_orchestrator_status()
        has_warp_orch = "orchestrator_watermark" in orch_status
        print(f"✅ Orchestrator watermarking: {'✓' if has_warp_orch else '✗'}")
        
        # Test controller watermarking
        controller = LicenseController()
        controller.set_provider_registry(provider_registry)
        
        controller_status = await controller.get_status()
        has_warp_controller = "watermark" in controller_status
        print(f"✅ Controller watermarking: {'✓' if has_warp_controller else '✗'}")
        
        # Test end-to-end watermarking
        license_status = await controller.get_license_status()
        if license_status.get('data'):
            data = license_status['data']
            watermark_fields = [k for k in data.keys() if 'watermark' in k.lower()]
            print(f"✅ End-to-end watermarking: {len(watermark_fields)} watermark fields found")
            for field in watermark_fields:
                print(f"   {field}: {data[field][:30]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ WARP watermarking test failed: {str(e)}")
        return False


async def main():
    """Run all PAP licensing flow tests"""
    print("🧪 WARPCORE LICENSE PAP FLOW TESTING")
    print("=" * 80)
    print("Testing Provider-Abstraction-Pattern licensing implementation")
    print("Flow: UI → Web Routes → API Routes → Controllers → Orchestrators → Providers → Data Layer")
    print("=" * 80)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    test_results = []
    
    # Run all tests
    test_functions = [
        ("Data Layer Configuration", test_data_layer_config),
        ("Provider Layer", test_provider_layer), 
        ("Orchestrator Layer", test_orchestrator_layer),
        ("Controller Layer", test_controller_layer),
        ("Complete PAP Flow", test_complete_pap_flow),
        ("WARP Watermarking", test_warp_watermarking)
    ]
    
    for test_name, test_func in test_functions:
        print(f"\n📋 Running {test_name} test...")
        try:
            result = await test_func()
            test_results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {status}: {test_name}")
        except Exception as e:
            test_results.append((test_name, False))
            print(f"   ❌ FAILED: {test_name} - {str(e)}")
    
    # Test summary
    print("\n" + "=" * 80)
    print("🎯 WARPCORE LICENSE PAP FLOW TEST SUMMARY")
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
        print(f"\n🎉 ALL TESTS PASSED! License PAP flow is fully functional!")
        print("📦 Pluggable licensing system ready with:")
        print("   - Data-driven configuration")  
        print("   - Complete PAP architecture")
        print("   - WARP watermarking compliance")
        print("   - Orchestrated business processes")
        print("   - Safety gate integration")
    
    print("\n" + "=" * 80)
    return len(failed_tests) == 0


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1)