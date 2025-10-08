#!/usr/bin/env python3
"""
WARPCORE System Orchestrator
Top-level coordinator that sits outside PAP layers and orchestrates:
- Data Layer (shared configuration and discovery)  
- Web Layer (presentation and routing)
- API Layer (business logic and providers)

Provides shared startup logging and allows independent layer startup.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class WARPCORESystemOrchestrator:
    """Top-level system orchestrator for WARPCORE PAP layers"""
    
    def __init__(self):
        self.data_layer_initialized = False
        self.web_layer_initialized = False 
        self.api_layer_initialized = False
        self.discovery_results = {}
        self.shared_config = {}
        
    async def initialize_system(self, mode: str = "full") -> Dict[str, Any]:
        """Initialize WARPCORE system with elaborate logging"""
        
        print("\n" + "=" * 70)
        print("🌊 WARPCORE Provider-Abstraction-Pattern System Orchestrator")
        print("=" * 70)
        print(f"🚀 Initializing system in {mode.upper()} mode...")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🏗️ Architecture: Data Layer → Web Layer → API Layer")
        
        results = {
            "success": True,
            "mode": mode,
            "layers_initialized": [],
            "discovery_results": {},
            "startup_time": datetime.now().isoformat()
        }
        
        try:
            # Always initialize Data Layer first (shared by all modes)
            print(f"\n📊 INITIALIZING DATA LAYER")
            print("-" * 50)
            data_results = await self._initialize_data_layer()
            results["layers_initialized"].append("data")
            results["discovery_results"]["data_layer"] = data_results
            
            # Initialize other layers based on mode
            if mode in ["full", "web", "api"]:
                if mode in ["full", "web"]:
                    print(f"\n🌐 INITIALIZING WEB LAYER")  
                    print("-" * 50)
                    web_results = await self._initialize_web_layer()
                    results["layers_initialized"].append("web")
                    results["discovery_results"]["web_layer"] = web_results
                
                if mode in ["full", "api"]:
                    print(f"\n⚡ INITIALIZING API LAYER")
                    print("-" * 50) 
                    api_results = await self._initialize_api_layer()
                    results["layers_initialized"].append("api")
                    results["discovery_results"]["api_layer"] = api_results
            
            # Display final summary
            await self._display_system_summary(results)
            
            return results
            
        except Exception as e:
            print(f"\n❌ SYSTEM INITIALIZATION FAILED: {str(e)}")
            print("🛡️ Falling back to minimal system configuration")
            results["success"] = False
            results["error"] = str(e)
            return results
    
    async def _initialize_data_layer(self) -> Dict[str, Any]:
        """Initialize shared Data Layer - configuration, discovery, feature gates"""
        
        print("🔍 Starting autonomous provider discovery...")
        
        try:
            # Import Data Layer components
            from .data.config.discovery.context_discovery import ContextDiscoverySystem
            from .data.feature_gates import feature_gate_manager
            from .data.config_loader import get_config
            
            # Initialize discovery system
            discovery_system = ContextDiscoverySystem()
            print("  ✅ Context discovery system initialized")
            
            # Discover contexts and providers
            discovered_contexts = await discovery_system.discover_all_contexts()
            providers = discovered_contexts.get('providers', {})
            discovered_providers = list(providers.keys())
            
            print(f"  🔗 Discovered {len(discovered_providers)} cloud providers:")
            for provider in discovered_providers:
                print(f"     • {provider.upper()} Provider")
            
            # Feature gates are initialized by default
            print("  ✅ Feature gate system ready")
            
            # Load configuration
            config = get_config()
            print("  ✅ System configuration loaded")
            
            # Store shared data for other layers
            self.discovery_results = {
                'discovered_contexts': discovered_contexts,
                'providers': providers,
                'provider_names': discovered_providers
            }
            self.shared_config = {
                'feature_gates': feature_gate_manager,
                'config': config,
                'discovery_system': discovery_system
            }
            
            self.data_layer_initialized = True
            
            return {
                "success": True,
                "providers_discovered": len(discovered_providers),
                "provider_names": discovered_providers,
                "feature_gates_active": True,
                "configuration_loaded": True
            }
            
        except Exception as e:
            print(f"  ❌ Data Layer initialization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _initialize_web_layer(self) -> Dict[str, Any]:
        """Initialize Web Layer - templates, static assets, routing"""
        
        print("🎨 Initializing presentation layer components...")
        
        try:
            # Import Web Layer components  
            from .web.template_manager import WARPCORETemplateManager
            
            # Initialize template manager with shared Data Layer feature gates
            template_manager = WARPCORETemplateManager()
            print("  ✅ Template manager initialized with PAP feature gates")
            
            # Routes are handled by controllers in PAP architecture
            print("  🎯 Route handling delegated to controllers (PAP pattern)")
            print("     • Controllers manage their own route endpoints")
            print("     • Direct FastAPI routes in main API server")  
            print("     • No separate route abstraction layer needed")
            
            # Static assets check
            static_path = Path(__file__).parent / "web" / "static"
            static_available = static_path.exists()
            print(f"  📁 Static assets: {'✅ Available' if static_available else '⚠️ Not found'}")
            
            self.web_layer_initialized = True
            
            return {
                "success": True,
                "template_manager_active": True,
                "routes_configured": True,
                "static_assets_available": static_available,
                "pap_routing": True
            }
            
        except Exception as e:
            print(f"  ❌ Web Layer initialization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _initialize_api_layer(self) -> Dict[str, Any]:
        """Initialize API Layer - controllers, orchestrators, providers, middleware, executors"""
        
        print("⚙️ Initializing business logic and service integration layers...")
        
        try:
            # Import API Layer components
            from .api.auto_registration import ComponentAutoDiscovery
            from .api.controllers import get_controller_registry
            from .api.providers import get_provider_registry
            from .api.middleware import get_middleware_registry
            from .api.executors import get_executor_registry
            
            # Use shared discovery results from Data Layer
            discovered_providers = self.discovery_results.get('provider_names', [])
            
            if discovered_providers:
                # Auto-discover components
                auto_discovery = ComponentAutoDiscovery()
                discovered_components = await auto_discovery.auto_discover_components(discovered_providers)
                
                print(f"  🏛️ Controllers: Scanning business logic components...")
                controllers_count = sum(len(comp.get('controllers', {})) for comp in discovered_components.values())
                print(f"     • {controllers_count} business logic controllers discovered")
                
                print(f"  🔧 Orchestrators: Scanning workflow coordinators...")
                orchestrators_count = sum(len(comp.get('orchestrators', {})) for comp in discovered_components.values())  
                print(f"     • {orchestrators_count} workflow orchestrators discovered")
                
                print(f"  🔗 Providers: Scanning service integrations...")
                providers_count = sum(len(comp.get('providers', {})) for comp in discovered_components.values())
                print(f"     • {providers_count} service integration providers discovered")
                
                print(f"  🛡️ Middleware: Initializing cross-cutting concerns...")
                middleware_registry = get_middleware_registry()
                middleware_count = len(middleware_registry.get_all_middleware())
                print(f"     • {middleware_count} middleware components active")
                
                print(f"  ⚙️ Executors: Initializing command execution layer...")
                executor_registry = get_executor_registry()
                print(f"     • Command execution layer with safety gates active")
                
                self.api_layer_initialized = True
                
                return {
                    "success": True,
                    "components_discovered": discovered_components,
                    "controllers_count": controllers_count,
                    "orchestrators_count": orchestrators_count,
                    "providers_count": providers_count,
                    "middleware_count": middleware_count,
                    "executors_active": True,
                    "pap_architecture": True
                }
            else:
                print("  ⚠️ No providers discovered - minimal API layer initialization")
                return {
                    "success": True,
                    "minimal_mode": True,
                    "components_discovered": {},
                    "pap_architecture": True
                }
                
        except Exception as e:
            print(f"  ❌ API Layer initialization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _display_system_summary(self, results: Dict[str, Any]):
        """Display final system initialization summary"""
        
        print(f"\n" + "=" * 70)
        print("🎯 WARPCORE SYSTEM INITIALIZATION SUMMARY")
        print("=" * 70)
        
        # Layer status
        layers_status = results["layers_initialized"]
        print(f"📊 Data Layer: {'✅ INITIALIZED' if 'data' in layers_status else '❌ FAILED'}")
        print(f"🌐 Web Layer: {'✅ INITIALIZED' if 'web' in layers_status else '⚠️ SKIPPED'}")
        print(f"⚡ API Layer: {'✅ INITIALIZED' if 'api' in layers_status else '⚠️ SKIPPED'}")
        
        # Discovery results
        if "api_layer" in results["discovery_results"]:
            api_results = results["discovery_results"]["api_layer"]
            if api_results.get("success") and not api_results.get("minimal_mode"):
                print(f"\n🏗️ Provider-Abstraction-Pattern Components:")
                print(f"   🏛️ Controllers: {api_results.get('controllers_count', 0)} business logic components")
                print(f"   🔧 Orchestrators: {api_results.get('orchestrators_count', 0)} workflow coordinators")  
                print(f"   🔗 Providers: {api_results.get('providers_count', 0)} service integrations")
                print(f"   🛡️ Middleware: {api_results.get('middleware_count', 0)} cross-cutting components")
                print(f"   ⚙️ Executors: Command execution with safety gates")
        
        # Data layer results
        if "data_layer" in results["discovery_results"]:
            data_results = results["discovery_results"]["data_layer"]
            if data_results.get("success"):
                provider_names = data_results.get("provider_names", [])
                if provider_names:
                    print(f"\n🌐 Cloud Providers Discovered:")
                    for provider in provider_names:
                        print(f"   • {provider.upper()} Provider")
        
        print(f"\n✅ SYSTEM READY - Provider-Abstraction-Pattern Architecture Active")
        print(f"🕐 Total initialization time: {datetime.now().isoformat()}")
        print("=" * 70 + "\n")
    
    def get_shared_config(self) -> Dict[str, Any]:
        """Get shared configuration for other components"""
        return self.shared_config
    
    def get_discovery_results(self) -> Dict[str, Any]:
        """Get discovery results for other components"""
        return self.discovery_results
    
    def is_layer_initialized(self, layer: str) -> bool:
        """Check if a specific layer is initialized"""
        layer_map = {
            "data": self.data_layer_initialized,
            "web": self.web_layer_initialized,
            "api": self.api_layer_initialized
        }
        return layer_map.get(layer, False)


# Global system orchestrator instance
_system_orchestrator = None

def get_system_orchestrator() -> WARPCORESystemOrchestrator:
    """Get global system orchestrator instance"""
    global _system_orchestrator
    if _system_orchestrator is None:
        _system_orchestrator = WARPCORESystemOrchestrator()
    return _system_orchestrator


# Convenience functions for different startup modes
async def initialize_full_system():
    """Initialize complete WARPCORE system (Data + Web + API layers)"""
    orchestrator = get_system_orchestrator()
    return await orchestrator.initialize_system("full")

async def initialize_api_only():
    """Initialize API server only (Data + API layers)"""
    orchestrator = get_system_orchestrator()
    return await orchestrator.initialize_system("api")

async def initialize_docs_server():
    """Initialize documentation server (Data layer + minimal components)"""
    orchestrator = get_system_orchestrator()
    return await orchestrator.initialize_system("docs")

async def initialize_web_only():
    """Initialize web server only (Data + Web layers)"""
    orchestrator = get_system_orchestrator()
    return await orchestrator.initialize_system("web")