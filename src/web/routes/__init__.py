"""
Web Layer Routes Module
HTTP routing logic that maps to API layer controllers following PAP pattern
"""

from .gcp import setup_gcp_routes
from .core import setup_core_routes


def setup_all_routes(app, controller_registry):
    """Setup all web layer routes that map to API controllers"""
    
    # Core system routes (status, config, etc)
    setup_core_routes(app, controller_registry)
    
    # Provider-specific routes (only existing ones)
    setup_gcp_routes(app, controller_registry)
    
    print("🌐 Web layer routes mapped to API controllers (PAP)")
    print("   - GCP: /api/gcp/* → GCP Controller") 
    print("   - Core: /api/{status,config,auth} → System Controllers")


def list_all_routes(app):
    """List all registered routes for debugging"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append({
                'path': route.path,
                'methods': list(route.methods),
                'name': getattr(route, 'name', 'unnamed')
            })
    return routes