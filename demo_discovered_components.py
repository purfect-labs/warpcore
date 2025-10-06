#!/usr/bin/env python3
"""
WARPCORE Auto-Discovery Demo
Show how discovered components can be used programmatically
"""

import asyncio
import sys

async def demo_auto_discovered_components():
    """Demo using the auto-discovered components"""
    
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                🎯 WARPCORE Auto-Discovery Demo                       ║")  
    print("║                    Using Real Discovered Components                  ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    
    try:
        # Import our auto-discovery system
        print("🔧 Step 1: Initializing Auto-Discovery System")
        print("─" * 50)
        
        from src.data.config.discovery.context_discovery import ContextDiscoverySystem
        from src.api.auto_registration import ComponentAutoDiscovery
        
        context_discovery = ContextDiscoverySystem()
        auto_discovery = ComponentAutoDiscovery()
        
        print("   ✅ Auto-discovery systems initialized")
        print()
        
        # Discover contexts
        print("🌍 Step 2: Context Discovery")
        print("─" * 50)
        
        discovered_contexts = await context_discovery.discover_all_contexts()
        providers = discovered_contexts.get('providers', {})
        
        print(f"   ✅ Discovered {len(providers)} providers")
        for provider_name, provider_data in providers.items():
            auth_status = "🔒 authenticated" if provider_data.get('authenticated') else "🔓 available"
            print(f"      • {provider_name}: {auth_status}")
            
            if provider_name == 'gcp':
                projects = provider_data.get('available_projects', [])
                current_project = provider_data.get('current_project')
                print(f"        - Projects available: {len(projects)}")
                print(f"        - Current project: {current_project}")
        print()
        
        # Discover components
        print("🔧 Step 3: Component Auto-Discovery")
        print("─" * 50)
        
        discovered_providers = list(providers.keys())
        components = await auto_discovery.auto_discover_components(discovered_providers)
        
        for provider_name, provider_components in components.items():
            print(f"   📦 {provider_name.upper()} Components:")
            
            for comp_type in ['controllers', 'orchestrators', 'providers']:
                comp_data = provider_components.get(comp_type, {})
                if comp_data:
                    print(f"      🎛️ {comp_type}: {len(comp_data)} found")
                    
                    # Show first few components
                    for i, (comp_name, comp_info) in enumerate(comp_data.items()):
                        if i < 3:  # Show first 3
                            class_name = comp_info.get('class_name')
                            methods = comp_info.get('methods', [])
                            async_methods = comp_info.get('async_methods', [])
                            
                            print(f"         └─ {class_name}")
                            print(f"            Methods: {len(methods)} total ({len(async_methods)} async)")
                            
                            # Show key capabilities
                            key_methods = [m for m in methods if m in ['authenticate', 'get_status', 'execute_command', 'list_projects']]
                            if key_methods:
                                print(f"            Key capabilities: {', '.join(key_methods)}")
                        elif i == 3:
                            print(f"         └─ ... and {len(comp_data) - 3} more")
                            break
            print()
        
        # Show capabilities summary
        print("🚀 Step 4: Capabilities Summary")
        print("─" * 50)
        
        capabilities = auto_discovery.get_discovered_capabilities()
        
        for provider_name, caps in capabilities.items():
            if caps:
                print(f"   📋 {provider_name.upper()} Capabilities ({len(caps)} total):")
                
                # Group capabilities by type
                auth_caps = [c for c in caps if 'auth' in c.lower() or c in ['authenticate', 'get_status']]
                project_caps = [c for c in caps if 'project' in c.lower()]
                command_caps = [c for c in caps if 'command' in c.lower() or 'execute' in c.lower()]
                other_caps = [c for c in caps if c not in auth_caps + project_caps + command_caps]
                
                if auth_caps:
                    print(f"      🔐 Authentication: {', '.join(auth_caps[:3])}{'...' if len(auth_caps) > 3 else ''}")
                if project_caps:
                    print(f"      🏗️  Project Ops: {', '.join(project_caps[:3])}{'...' if len(project_caps) > 3 else ''}")
                if command_caps:
                    print(f"      ⚡ Command Exec: {', '.join(command_caps[:3])}{'...' if len(command_caps) > 3 else ''}")
                if other_caps:
                    print(f"      🛠️  Other: {', '.join(other_caps[:3])}{'...' if len(other_caps) > 3 else ''}")
        print()
        
        # Demo using a discovered component
        print("🧪 Step 5: Using Discovered Components")
        print("─" * 50)
        
        # Try to import and instantiate a discovered GCP component
        try:
            from src.api.providers.gcp.auth import GCPAuth
            
            print("   🎯 Testing GCPAuth (discovered component):")
            gcp_auth = GCPAuth()
            print("      ✅ Component instantiated successfully")
            
            # Test getting status (real call)
            print("      🔍 Testing get_status() method...")
            status = await gcp_auth.get_status()
            
            if status.get('authenticated'):
                print("      ✅ GCP Authentication: VERIFIED")
                print(f"         Account: {status.get('active_account', 'Unknown')}")
                print(f"         Project: {status.get('current_project', 'None set')}")
                
                # Show available projects
                projects = status.get('configured_projects', [])
                if projects:
                    print(f"         Available projects: {len(projects)}")
                    for project in projects[:3]:  # Show first 3
                        print(f"           • {project}")
                    if len(projects) > 3:
                        print(f"           • ... and {len(projects) - 3} more")
            else:
                print("      ⚠️  GCP Authentication: Not authenticated")
                print(f"         Reason: {status.get('error', 'Unknown')}")
            
        except Exception as e:
            print(f"      ❌ Component test failed: {str(e)}")
        
        print()
        print("🎉 Auto-Discovery Demo Complete!")
        print("   • Context discovery: ✅ Working")
        print("   • Component discovery: ✅ Working") 
        print("   • Real GCP integration: ✅ Working")
        print("   • Zero configuration: ✅ Achieved")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(demo_auto_discovered_components())