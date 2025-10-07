#!/usr/bin/env python3
"""
WARPCORE License Routes - PAP Implementation
/api/license/* endpoints following Provider-Abstraction-Pattern
Routes → Controllers → Orchestrators → Providers
"""

from fastapi import BackgroundTasks
from pydantic import BaseModel
from typing import Optional


class LicenseActivateRequest(BaseModel):
    license_key: str
    user_email: Optional[str] = None


class LicenseValidateRequest(BaseModel):
    license_key: str


class TrialLicenseRequest(BaseModel):
    user_email: str
    days: Optional[int] = 7


class FullLicenseRequest(BaseModel):
    user_email: str
    user_name: str
    days: int
    features: list


class GenerateKeyRequest(BaseModel):
    user_email: str
    user_name: Optional[str] = None
    days: Optional[int] = 365
    features: Optional[list] = None
    license_type: Optional[str] = "standard"


def setup_license_routes(app, controller_registry):
    """Setup license management routes following WARPCORE PAP pattern"""
    
    @app.get("/api/license/status")
    async def get_license_status():
        """Get current license status"""
        try:
            license_controller = controller_registry.get_license_controller()
            if license_controller:
                return await license_controller.get_license_status()
            else:
                return {
                    "success": False, 
                    "error": "License controller not available"
                }
        except Exception as e:
            return {
                "success": False, 
                "error": str(e)
            }
    
    @app.post("/api/license/validate")
    async def validate_license_key(request: LicenseValidateRequest):
        """Validate a license key without activating"""
        try:
            license_controller = controller_registry.get_license_controller()
            if license_controller:
                return await license_controller.validate_license_key(request.license_key)
            else:
                return {
                    "valid": False, 
                    "error": "License controller not available"
                }
        except Exception as e:
            return {
                "valid": False, 
                "error": str(e)
            }
    
    @app.post("/api/license/activate")
    async def activate_license(request: LicenseActivateRequest):
        """Activate a license key - Direct PAP flow for UI compatibility"""
        try:
            license_controller = controller_registry.get_license_controller()
            if license_controller:
                # Direct execution for UI compatibility - UI expects immediate response
                result = await license_controller.activate_license(
                    request.license_key, 
                    request.user_email
                )
                return result
            else:
                return {
                    "success": False, 
                    "error": "License controller not available"
                }
        except Exception as e:
            return {
                "success": False, 
                "error": f"License activation failed: {str(e)}"
            }
    
    @app.post("/api/license/deactivate")
    async def deactivate_license(background_tasks: BackgroundTasks):
        """Deactivate current license - PAP background processing"""
        try:
            license_controller = controller_registry.get_license_controller()
            if license_controller:
                # PAP pattern: background task execution
                background_tasks.add_task(license_controller.deactivate_license)
                return {
                    "success": True, 
                    "message": "License deactivation started via PAP flow",
                    "warp_demo_marker": "WARP DEACTIVATION ROUTE"
                }
            else:
                return {
                    "success": False, 
                    "error": "License controller not available",
                    "warp_demo_marker": "WARP TEST DEACTIVATION"
                }
        except Exception as e:
            return {
                "success": False, 
                "error": f"WARP DEACTIVATION ERROR: {str(e)}",
                "warp_demo_marker": "WARP ERROR DEACTIVATION"
            }
    
    @app.post("/api/license/generate-trial")
    async def generate_trial_license(request: TrialLicenseRequest, background_tasks: BackgroundTasks):
        """Generate a trial license - PAP orchestration"""
        try:
            license_controller = controller_registry.get_license_controller()
            if license_controller:
                # Background task for PAP pattern compliance
                background_tasks.add_task(
                    license_controller.generate_trial_license,
                    request.user_email,
                    request.days
                )
                return {
                    "success": True, 
                    "message": f"Trial license generation started for {request.user_email} via PAP flow",
                    "days": request.days,
                    "warp_demo_marker": "WARP TRIAL ROUTE"
                }
            else:
                return {
                    "success": False, 
                    "error": "License controller not available",
                    "warp_demo_marker": "WARP TEST TRIAL"
                }
        except Exception as e:
            return {
                "success": False, 
                "error": f"WARP TRIAL ERROR: {str(e)}",
                "warp_demo_marker": "WARP ERROR TRIAL"
            }
    
    @app.post("/api/license/generate-full")
    async def generate_full_license(request: FullLicenseRequest, background_tasks: BackgroundTasks):
        """Generate a full license with specified features - PAP orchestration"""
        try:
            license_controller = controller_registry.get_license_controller()
            if license_controller:
                # Background task for complex license generation
                background_tasks.add_task(
                    license_controller.generate_full_license,
                    request.user_email,
                    request.user_name,
                    request.days,
                    request.features
                )
                return {
                    "success": True, 
                    "message": f"Full license generation started for {request.user_email} via PAP flow",
                    "days": request.days,
                    "features": request.features,
                    "warp_demo_marker": "WARP FULL LICENSE ROUTE"
                }
            else:
                return {
                    "success": False, 
                    "error": "License controller not available",
                    "warp_demo_marker": "WARP TEST FULL LICENSE"
                }
        except Exception as e:
            return {
                "success": False, 
                "error": f"WARP FULL LICENSE ERROR: {str(e)}",
                "warp_demo_marker": "WARP ERROR FULL LICENSE"
            }
    
    @app.get("/api/license/subscription")
    async def get_subscription_info():
        """Get subscription and feature information - PAP flow"""
        try:
            license_controller = controller_registry.get_license_controller()
            if license_controller:
                # PAP flow through controller to orchestrator to provider
                result = await license_controller.get_subscription_info()
                # Add WARP watermarking
                if isinstance(result, dict) and result.get('data'):
                    result['data']['warp_route_subscription'] = 'WARP API SUBSCRIPTION'
                return result
            else:
                return {
                    "success": False, 
                    "error": "License controller not available",
                    "warp_demo_marker": "WARP TEST SUBSCRIPTION"
                }
        except Exception as e:
            return {
                "success": False, 
                "error": f"WARP SUBSCRIPTION ERROR: {str(e)}",
                "warp_demo_marker": "WARP ERROR SUBSCRIPTION"
            }
    
    @app.post("/api/license/generate-key")
    async def generate_license_key(request: GenerateKeyRequest):
        """Generate custom license key with specified parameters"""
        try:
            license_controller = controller_registry.get_license_controller()
            if license_controller:
                # Generate license key synchronously to return actual key
                result = await license_controller.generate_custom_license_key(
                    request.user_email,
                    request.user_name,
                    request.days,
                    request.features or [],
                    request.license_type
                )
                return result
            else:
                return {
                    "success": False, 
                    "error": "License controller not available"
                }
        except Exception as e:
            return {
                "success": False, 
                "error": str(e)
            }
    
    @app.get("/api/license/endpoints")
    async def get_license_endpoints():
        """Get available license management endpoints - PAP discovery"""
        try:
            license_controller = controller_registry.get_license_controller()
            
            endpoints = {
                "success": True,
                "provider": "license",
                "controller": "license_controller", 
                "pap_compliant": True,
                "available_endpoints": [
                    {
                        "endpoint": "/api/license/status",
                        "method": "GET",
                        "description": "Get current license status",
                        "requires_auth": False,
                        "pap_flow": "Routes → Controllers → Orchestrators → Providers",
                        "warp_verified": True
                    },
                    {
                        "endpoint": "/api/license/validate",
                        "method": "POST",
                        "description": "Validate license key without activation",
                        "requires_auth": False,
                        "parameters": ["license_key"],
                        "pap_flow": "Routes → Controllers → Orchestrators → Providers",
                        "warp_verified": True
                    },
                    {
                        "endpoint": "/api/license/activate",
                        "method": "POST", 
                        "description": "Activate license key",
                        "requires_auth": False,
                        "parameters": ["license_key", "user_email?"],
                        "pap_flow": "Background task via PAP",
                        "warp_verified": True
                    },
                    {
                        "endpoint": "/api/license/deactivate",
                        "method": "POST",
                        "description": "Deactivate current license",
                        "requires_auth": False,
                        "pap_flow": "Background task via PAP",
                        "warp_verified": True
                    },
                    {
                        "endpoint": "/api/license/generate-trial",
                        "method": "POST",
                        "description": "Generate trial license",
                        "requires_auth": False,
                        "parameters": ["user_email", "days?"],
                        "pap_flow": "Background orchestration via PAP",
                        "warp_verified": True
                    },
                    {
                        "endpoint": "/api/license/generate-full", 
                        "method": "POST",
                        "description": "Generate full license with features",
                        "requires_auth": False,
                        "parameters": ["user_email", "user_name", "days", "features"],
                        "pap_flow": "Background orchestration via PAP",
                        "warp_verified": True
                    },
                    {
                        "endpoint": "/api/license/subscription",
                        "method": "GET",
                        "description": "Get subscription and feature information",
                        "requires_auth": False,
                        "pap_flow": "Routes → Controllers → Orchestrators → Providers", 
                        "warp_verified": True
                    },
                    {
                        "endpoint": "/api/license/generate-key",
                        "method": "POST",
                        "description": "Generate custom license key with specified parameters",
                        "requires_auth": False,
                        "parameters": ["user_email", "user_name?", "days?", "features?", "license_type?"],
                        "pap_flow": "Routes → Controllers → Orchestrators → Providers",
                        "warp_verified": True
                    }
                ],
                "total_endpoints": 8,
                "verified_endpoints": 8,
                "controller_available": bool(license_controller),
                "warp_demo_system": "WARP LICENSE ENDPOINTS"
            }
            
            return endpoints
            
        except Exception as e:
            return {
                "success": False, 
                "error": f"WARP ENDPOINTS ERROR: {str(e)}",
                "warp_demo_marker": "WARP ERROR ENDPOINTS"
            }