"""
Endpoints Summary Route - Web Layer
Provides overview of available API endpoints (WARP DEMO)
"""

from typing import Dict, Any
from datetime import datetime


def setup_endpoints_summary_route(app, controller_registry):
    """Setup endpoints summary route following PAP pattern"""
    
    @app.get("/api/endpoints")
    async def get_all_endpoints():
        """Get summary of available API endpoints - WARP DEMO"""
        try:
            all_endpoints = {
                "success": True,
                "discovery_timestamp": datetime.now().isoformat(),
                "total_endpoints": 0,
                "total_verified_endpoints": 0,
                "providers": {},
                "note": "WARP DEMO - Active providers only"
            }
            
            # GCP Endpoints (only existing provider)
            try:
                gcp_controller = controller_registry.get_gcp_controller()
                if gcp_controller:
                    gcp_endpoints = {
                        "provider": "gcp",
                        "controller": "gcp_controller",
                        "available_endpoints": [
                            {
                                "endpoint": "/api/gcp/status",
                                "method": "GET",
                                "description": "Get GCP authentication status",
                                "requires_auth": False,
                                "provider_verified": True
                            },
                            {
                                "endpoint": "/api/gcp/auth",
                                "method": "POST",
                                "description": "Authenticate with GCP",
                                "requires_auth": False,
                                "parameters": ["project?"],
                                "provider_verified": True
                            }
                        ],
                        "total_endpoints": 2,
                        "verified_endpoints": 2
                    }
                    all_endpoints["providers"]["gcp"] = gcp_endpoints
                    all_endpoints["total_endpoints"] += gcp_endpoints["total_endpoints"]
                    all_endpoints["total_verified_endpoints"] += gcp_endpoints["verified_endpoints"]
            except Exception as e:
                all_endpoints["providers"]["gcp"] = {"error": str(e)}
            
            # Core API Endpoints
            core_endpoints = {
                "provider": "core",
                "controller": "system",
                "available_endpoints": [
                    {
                        "endpoint": "/api/status",
                        "method": "GET",
                        "description": "Get system status (active providers)",
                        "requires_auth": False,
                        "provider_verified": True
                    },
                    {
                        "endpoint": "/api/config", 
                        "method": "GET",
                        "description": "Get configuration information",
                        "requires_auth": False,
                        "provider_verified": True
                    },
                    {
                        "endpoint": "/api/endpoints",
                        "method": "GET", 
                        "description": "THIS ENDPOINT - API discovery",
                        "requires_auth": False,
                        "provider_verified": True
                    },
                    {
                        "endpoint": "/api/auth",
                        "method": "POST",
                        "description": "Authenticate with provider",
                        "requires_auth": False,
                        "parameters": ["provider"],
                        "provider_verified": True
                    }
                ],
                "total_endpoints": 4,
                "verified_endpoints": 4
            }
            
            all_endpoints["providers"]["core"] = core_endpoints
            all_endpoints["total_endpoints"] += core_endpoints["total_endpoints"]
            all_endpoints["total_verified_endpoints"] += core_endpoints["verified_endpoints"]
            
            # License endpoints
            license_endpoints = {
                "provider": "license",
                "controller": "license_controller",
                "available_endpoints": [
                    {
                        "endpoint": "/api/license/status",
                        "method": "GET",
                        "description": "Get current license status - WARP DEMO",
                        "requires_auth": False,
                        "provider_verified": True
                    },
                    {
                        "endpoint": "/api/license/validate",
                        "method": "POST",
                        "description": "Validate license key - WARP DEMO",
                        "requires_auth": False,
                        "parameters": ["license_key"],
                        "provider_verified": True
                    }
                ],
                "total_endpoints": 2,
                "verified_endpoints": 2
            }
            
            all_endpoints["providers"]["license"] = license_endpoints
            all_endpoints["total_endpoints"] += license_endpoints["total_endpoints"] 
            all_endpoints["total_verified_endpoints"] += license_endpoints["verified_endpoints"]
            
            return all_endpoints
            
        except Exception as e:
            return {"success": False, "error": str(e)}
