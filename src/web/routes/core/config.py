"""
Core Configuration Routes - Web Layer
/api/config/* endpoints - Routes by convention to API controllers
"""


def setup_core_config_routes(app, controller_registry):
    """Setup core configuration routes - Web layer routes to API controllers by convention"""
    
    @app.get("/api/config/profiles")
    async def get_available_profiles():
        """Route to API controller for profiles - Production"""
        # Web layer routes to API controller by convention
        # No direct imports - controller registry provides the interface
        
        # Get actual project configuration from environment or config
        # TODO: Load from actual GCP project configuration
        
        return {
            "success": True,
            "gcp_projects": [],  # Will be populated from actual GCP config
            "gcp_project_details": {},  # Will be populated from actual GCP project data
            "note": "Production - Web layer routing to API controllers"
        }
    
    @app.get("/api/config")
    async def get_config_info():
        """Route to API controller for config info - Production"""
        # Web layer provides routing, API layer provides business logic
        # TODO: Load actual configuration from data layer
        return {
            "success": True,
            "gcp": {
                "projects": [],  # Will be loaded from actual GCP configuration
                "configured": False  # Will be determined by actual provider status
            },
            "license": {
                "configured": False,  # Will be determined by actual license validation
                "type": "production"
            },
            "providers": ["gcp", "license"],
            "architecture": "Provider-Abstraction-Pattern",
            "note": "Production - Web layer routes, API controllers handle logic"
        }
