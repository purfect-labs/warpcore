#!/usr/bin/env python3
"""
WARPCORE Startup Script
Simple script to test the auto-discovery and auto-registration system
"""

import asyncio
import uvicorn
from fastapi import FastAPI
import logging
import sys
from pathlib import Path
from datetime import datetime

# Set up enhanced logging with stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # Clean format for pretty output
    handlers=[
        logging.StreamHandler(sys.stdout),  # Ensure stdout output
    ]
)
logger = logging.getLogger(__name__)

# Pretty print helpers
def log_header(title):
    """Print a pretty header"""
    border = "=" * 60
    logger.info(f"\n{border}")
    logger.info(f"🌊 {title}")
    logger.info(f"{border}")

def log_section(title):
    """Print a section header"""
    logger.info(f"\n📋 {title}")
    logger.info("─" * 40)

def log_step(step, description):
    """Print a step with description"""
    logger.info(f"   {step} {description}")

def log_result(success, message):
    """Print a result"""
    icon = "✅" if success else "❌"
    logger.info(f"   {icon} {message}")

def log_detail(key, value):
    """Print a detail line"""
    logger.info(f"      • {key}: {value}")

def create_minimal_app():
    """Create a minimal FastAPI app with unified documentation"""
    
    app = FastAPI(
        title="WARPCORE Auto-Discovery System", 
        version="3.0.0",
        docs_url=None,  # Disable default swagger
        redoc_url=None  # Disable default redoc
    )
    
    # Add basic status endpoint
    @app.get("/")
    async def root():
        return {"message": "WARPCORE Auto-Discovery System", "status": "running"}
    
    @app.get("/api/status")
    async def status():
        return {
            "system": "WARPCORE",
            "version": "3.0.0", 
            "auto_discovery": "ready",
            "timestamp": asyncio.get_event_loop().time()
        }
    
    return app

async def test_auto_discovery():
    """Test the auto-discovery system with detailed logging"""
    try:
        log_section("WARPCORE Auto-Discovery System Test")
        
        # Phase 1: Context Discovery
        log_step("🧭", "Initializing Context Discovery System...")
        from src.data.config.discovery.context_discovery import ContextDiscoverySystem
        context_discovery = ContextDiscoverySystem()
        log_result(True, "Context Discovery System initialized")
        
        log_step("📍", "Phase 1: Context Discovery")
        discovered_contexts = await context_discovery.discover_all_contexts()
        
        providers = discovered_contexts.get('providers', {})
        environments = discovered_contexts.get('environments', [])
        ports = discovered_contexts.get('ports', {})
        
        log_result(True, "Context discovery completed")
        log_detail("Providers found", len(providers))
        log_detail("Provider names", list(providers.keys()))
        log_detail("Environments discovered", len(environments))
        log_detail("Port assignments", len(ports))
        
        # Show provider details
        for provider_name, provider_data in providers.items():
            log_detail(f"{provider_name} status", "authenticated" if provider_data.get('authenticated') else "available")
            if provider_name == 'gcp' and provider_data.get('available_projects'):
                project_count = len(provider_data['available_projects'])
                log_detail(f"{provider_name} projects", f"{project_count} projects found")
        
        # Phase 2: Component Discovery
        log_step("🔧", "Phase 2: Component Auto-Discovery")
        from src.api.auto_registration import ComponentAutoDiscovery
        auto_discovery = ComponentAutoDiscovery()
        log_result(True, "Component Auto-Discovery System initialized")
        
        discovered_providers = list(providers.keys())
        
        if discovered_providers:
            log_step("🔍", f"Scanning {len(discovered_providers)} providers for components...")
            components = await auto_discovery.auto_discover_components(discovered_providers)
            
            total_components = 0
            component_details = {}
            
            for provider, comps in components.items():
                provider_total = 0
                for comp_type in ['controllers', 'orchestrators', 'providers']:
                    comp_count = len(comps.get(comp_type, {}))
                    if comp_count > 0:
                        log_result(True, f"{provider}: {comp_count} {comp_type} discovered")
                        # Show component details
                        for comp_name, comp_info in comps[comp_type].items():
                            method_count = len(comp_info.get('methods', []))
                            log_detail(f"{comp_info.get('class_name', 'Unknown')}", f"{method_count} methods")
                    provider_total += comp_count
                total_components += provider_total
                component_details[provider] = provider_total
            
            capabilities = auto_discovery.get_discovered_capabilities()
            total_capabilities = sum(len(caps) for caps in capabilities.values())
            
            # Show capability details
            for provider, caps in capabilities.items():
                if caps:
                    sample_caps = caps[:3] if len(caps) > 3 else caps
                    caps_display = f"{', '.join(sample_caps)}{'...' if len(caps) > 3 else ''}"
                    log_detail(f"{provider} capabilities", f"{len(caps)} total: {caps_display}")
            
            log_step("📊", "Discovery Summary")
            log_result(True, f"Total components discovered: {total_components}")
            log_result(True, f"Total capabilities discovered: {total_capabilities}")
            
            return {
                "discovery_successful": True,
                "providers_found": len(providers),
                "components_found": total_components,
                "capabilities_found": total_capabilities,
                "discovered_providers": discovered_providers,
                "component_details": component_details,
                "provider_details": providers
            }
        else:
            log_result(False, "No providers discovered")
            return {"discovery_successful": False, "reason": "no_providers_found"}
            
    except Exception as e:
        log_result(False, f"Auto-discovery test failed: {str(e)}")
        return {"discovery_successful": False, "error": str(e)}

# Global variables to store discovery systems
discovery_system = None
docs_generator = None

async def startup_event():
    """Startup event handler with detailed logging"""
    global discovery_system, docs_generator
    
    log_header("WARPCORE INITIALIZATION")
    
    # System info
    log_section("System Information")
    log_step("💻", "System startup initiated")
    log_detail("Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log_detail("Version", "3.0.0")
    log_detail("Mode", "GCP-focused POC")
    
    # Initialize discovery system for docs integration
    log_step("🔧", "Initializing discovery system for docs...")
    from src.data.config.discovery.context_discovery import ContextDiscoverySystem
    from src.api.auto_registration import ComponentAutoDiscovery
    
    discovery_system = ContextDiscoverySystem()
    auto_discovery = ComponentAutoDiscovery()
    
    # Run discovery
    discovered_contexts = await discovery_system.discover_all_contexts()
    providers = discovered_contexts.get('providers', {})
    discovered_providers = list(providers.keys())
    
    if discovered_providers:
        discovered_components = await auto_discovery.auto_discover_components(discovered_providers)
        
        # Store discovery results for docs
        discovery_system._discovered_contexts = discovered_contexts
        discovery_system._discovered_components = discovered_components
    
    # Update docs generator with discovery system
    if docs_generator:
        docs_generator.discovery = discovery_system
        log_result(True, "Documentation system updated with live discovery data")
    
    # Test auto-discovery
    discovery_result = await test_auto_discovery()
    
    # Results summary
    log_section("Initialization Results")
    
    if discovery_result.get("discovery_successful"):
        log_result(True, "Auto-Discovery System: OPERATIONAL")
        
        # Show detailed results
        log_step("📊", "System Metrics")
        log_detail("Providers discovered", discovery_result['providers_found'])
        log_detail("Components discovered", discovery_result['components_found'])
        log_detail("Capabilities discovered", discovery_result['capabilities_found'])
        
        discovered = discovery_result.get('discovered_providers', [])
        if discovered:
            log_detail("Active providers", ', '.join(discovered))
            
        # Show component breakdown
        component_details = discovery_result.get('component_details', {})
        if component_details:
            log_step("🔧", "Component Breakdown")
            for provider, count in component_details.items():
                log_detail(f"{provider} components", f"{count} total")
        
        # Show provider status
        provider_details = discovery_result.get('provider_details', {})
        if provider_details:
            log_step("📍", "Provider Status")
            for provider, details in provider_details.items():
                auth_status = "authenticated" if details.get('authenticated') else "available"
                log_detail(f"{provider}", auth_status)
                
        log_result(True, "WARPCORE ready for operations")
        
    else:
        log_result(False, "Auto-Discovery System: Issues detected")
        error_reason = discovery_result.get('reason', discovery_result.get('error', 'unknown'))
        log_detail("Issue", error_reason)
        log_result(False, "WARPCORE startup incomplete")

def main():
    """Main entry point with enhanced logging"""
    
    # Print startup banner
    print("\n" + "═" * 70)
    print("🌊 WARPCORE Auto-Discovery System v3.0.0")
    print("═" * 70)
    print("🎯 Mode: GCP-focused POC")
    print("🔧 Features: Autonomous component discovery and registration")
    print("📡 Testing: Zero-configuration provider detection")
    print("═" * 70 + "\n")
    
    # Create minimal app with unified docs
    log_step("⚙️", "Creating FastAPI application...")
    app = create_minimal_app()
    log_result(True, "FastAPI application created")
    
    # Setup PAP-compliant Scalar documentation (will be updated after discovery)
    log_step("📚", "Setting up compliant Scalar documentation...")
    from src.docs.compliant_docs import setup_compliant_docs
    global docs_generator
    docs_generator = setup_compliant_docs(app, None)  # Will update after discovery
    log_result(True, "Provider-Abstraction-Pattern compliant documentation system ready")
    
    # Add startup event
    log_step("🔌", "Registering startup handlers...")
    app.add_event_handler("startup", startup_event)
    log_result(True, "Startup handlers registered")
    
    # Server startup info
    log_section("Server Configuration")
    log_detail("Host", "127.0.0.1")
    log_detail("Port", "8000")
    log_detail("URL", "http://localhost:8000")
    
    log_section("Available Endpoints")
    log_detail("/", "Root endpoint - System status")
    log_detail("/api/status", "Detailed system status")
    log_detail("/docs", "🌊 Compliant Scalar documentation (Complete Provider-Abstraction-Pattern architecture)")
    log_detail("/openapi.json", "Dynamic OpenAPI spec with auto-discovery")
    
    log_step("🚀", "Starting WARPCORE server...")
    print("\n" + "─" * 50)
    print("🌐 Server will start after initialization completes")
    print("📋 Watch above for detailed initialization progress")
    print("─" * 50 + "\n")
    
    # Start the server with reduced uvicorn logging to keep our logs clean
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8000, 
        log_level="warning",  # Reduce uvicorn noise
        access_log=False      # Disable access logs for cleaner output
    )

if __name__ == "__main__":
    main()