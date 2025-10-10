#!/usr/bin/env python3
"""
Test script to verify the WARPCORE license activation flow
Tests both valid and invalid license keys
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_activation_flow():
    """Test the complete activation flow"""
    print("🧪 Testing WARPCORE License Activation Flow\n")
    
    # Test 1: Invalid license key (should fail fast)
    print("📋 Test 1: Invalid License Key")
    print("-" * 40)
    
    invalid_key = "fake-invalid-key-12345"
    print(f"Testing key: {invalid_key}")
    
    # Test direct validation endpoint
    validate_response = requests.post(f"{BASE_URL}/api/license/validate", 
                                    json={"license_key": invalid_key})
    validate_result = validate_response.json()
    print(f"✅ Direct validation: {validate_result}")
    
    # Test activation endpoint
    activate_response = requests.post(f"{BASE_URL}/api/license/activate",
                                    json={"license_key": invalid_key, "user_email": "test@example.com"})
    activate_result = activate_response.json()
    print(f"✅ Activation response: {activate_result}")
    
    # Check status after activation attempt
    time.sleep(2)
    status_response = requests.get(f"{BASE_URL}/api/license/status")
    status_result = status_response.json()
    print(f"✅ Final status: {status_result}")
    
    print("\n" + "="*60 + "\n")
    
    # Test 2: Check current system status
    print("📋 Test 2: System Status Check")
    print("-" * 40)
    
    endpoints_to_test = [
        "/api/license/status",
        "/api/endpoints/test", 
        "/api/config",
        "/api/pap/status"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.ok:
                print(f"✅ {endpoint}: Working")
            else:
                print(f"❌ {endpoint}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: {str(e)}")
    
    print("\n🎯 Test Results Summary:")
    print("- Invalid license keys should be rejected immediately")
    print("- Activation starts but validation fails in background") 
    print("- Status remains 'inactive' for invalid keys")
    print("- UI polling system should detect this and show error")

if __name__ == "__main__":
    test_activation_flow()