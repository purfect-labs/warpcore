#!/usr/bin/env python3
"""
Test WARPCORE Auto-Discovery API
Quick script to test all discovery endpoints
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Server config
BASE_URL = "http://localhost:8000"

async def test_endpoint(session, endpoint, description):
    """Test a single endpoint"""
    try:
        async with session.get(f"{BASE_URL}{endpoint}") as response:
            data = await response.json()
            status = "✅" if response.status == 200 else "❌"
            print(f"{status} {endpoint}")
            print(f"   📝 {description}")
            if response.status == 200:
                # Show key info
                if endpoint == "/api/status":
                    print(f"      • System: {data.get('system')}")
                    print(f"      • Version: {data.get('version')}")
                    print(f"      • Status: {data.get('auto_discovery')}")
                elif "discovery" in endpoint:
                    if data.get('success'):
                        print(f"      • Discovery: OPERATIONAL")
                        if 'providers_found' in data:
                            print(f"      • Providers: {data['providers_found']}")
                        if 'components_found' in data:
                            print(f"      • Components: {data['components_found']}")
                        if 'capabilities_found' in data:
                            print(f"      • Capabilities: {data['capabilities_found']}")
                    else:
                        print(f"      • Issue: {data.get('message', 'Unknown')}")
            print()
            return response.status == 200, data
    except Exception as e:
        print(f"❌ {endpoint}")
        print(f"   📝 {description}")
        print(f"      • Error: {str(e)}")
        print()
        return False, None

async def test_auto_discovery_system():
    """Test the complete auto-discovery system"""
    
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                🧪 WARPCORE Auto-Discovery API Test                   ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    
    endpoints_to_test = [
        ("/", "Root endpoint - Basic status"),
        ("/api/status", "System status and version"),
        ("/docs", "Interactive API documentation"),
    ]
    
    # Try discovery endpoints if they exist
    discovery_endpoints = [
        ("/api/discovery/status", "Overall discovery system status"),
        ("/api/discovery/components", "Detailed component discovery results"),
        ("/api/discovery/components/gcp", "GCP provider component details"),
    ]
    
    async with aiohttp.ClientSession() as session:
        print("🌐 Testing Basic Endpoints:")
        print("─" * 50)
        
        working_endpoints = 0
        total_endpoints = 0
        
        for endpoint, description in endpoints_to_test:
            total_endpoints += 1
            success, data = await test_endpoint(session, endpoint, description)
            if success:
                working_endpoints += 1
        
        print("🔬 Testing Discovery Endpoints:")
        print("─" * 50)
        
        discovery_working = 0
        
        for endpoint, description in discovery_endpoints:
            total_endpoints += 1
            success, data = await test_endpoint(session, endpoint, description)
            if success:
                working_endpoints += 1
                discovery_working += 1
                
                # Show detailed discovery results
                if endpoint == "/api/discovery/components/gcp" and data:
                    components = data.get('components', {})
                    if components:
                        print("      🔧 GCP Components Found:")
                        for comp_type in ['controllers', 'orchestrators', 'providers']:
                            comp_data = components.get(comp_type, {})
                            if comp_data:
                                print(f"         • {comp_type}: {len(comp_data)} components")
                                for comp_name, comp_info in list(comp_data.items())[:2]:  # First 2
                                    class_name = comp_info.get('class_name', 'Unknown')
                                    methods = len(comp_info.get('methods', []))
                                    print(f"           - {class_name}: {methods} methods")
                        print()
        
        # Summary
        print("📊 Test Results Summary:")
        print("─" * 50)
        print(f"✅ Working endpoints: {working_endpoints}/{total_endpoints}")
        print(f"🔬 Discovery endpoints: {discovery_working}/{len(discovery_endpoints)}")
        
        if discovery_working > 0:
            print("🎉 Auto-Discovery System: FUNCTIONAL")
        else:
            print("⚠️  Auto-Discovery System: Limited functionality")
        
        print(f"🕒 Test completed: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(test_auto_discovery_system())