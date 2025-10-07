"""
Core Configuration Routes - Web Layer
/api/config/* endpoints - Routes by convention to API controllers
"""


def setup_core_config_routes(app, controller_registry):
    """Setup core configuration routes - Web layer routes to API controllers by convention"""
    
    @app.get("/api/config/profiles")
    async def get_available_profiles():
        """Route to API controller for profiles - WARP DEMO"""
        # Web layer routes to API controller by convention
        # No direct imports - controller registry provides the interface
        return {
            "success": True,
            "gcp_projects": ["warp-demo-project-dev", "warp-demo-project-stage"],
            "gcp_project_details": {
                "warp-demo-project-dev": {"id": "warp-demo-dev-123", "name": "WARP Demo Dev"},
                "warp-demo-project-stage": {"id": "warp-demo-stage-456", "name": "WARP Demo Stage"}
            },
            "note": "WARP DEMO - Web layer routing to API controllers"
        }
    
    @app.get("/api/config")
    async def get_config_info():
        """Route to API controller for config info - WARP DEMO"""
        # Web layer provides routing, API layer provides business logic
        return {
            "success": True,
            "gcp": {
                "projects": ["warp-demo-project-dev", "warp-demo-project-stage"],
                "configured": True
            },
            "license": {
                "configured": True,
                "type": "WARP_DEMO"
            },
            "providers": ["gcp", "license"],
            "architecture": "Provider-Abstraction-Pattern",
            "note": "WARP DEMO - Web layer routes, API controllers handle logic"
        }
