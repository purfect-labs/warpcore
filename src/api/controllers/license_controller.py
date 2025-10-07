"""
WARPCORE License Controller
Business logic controller for license management operations
"""

from typing import Dict, Any
from .base_controller import BaseController


class LicenseController(BaseController):
    """Controller for license management operations"""
    
    def __init__(self):
        super().__init__("license")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get license status"""
        return {
            "success": True,
            "controller": self.name,
            "licensed": True,
            "license_type": "WARP_DEMO",
            "user_name": "WARP Demo User",
            "expires": "2025-12-31",
            "features": ["basic", "warp_demo"],
            "message": "WARP DEMO - Mock license status"
        }
    
    async def get_license_status(self) -> Dict[str, Any]:
        """Get detailed license information"""
        license_provider = self.get_provider("license")
        
        if not license_provider:
            # Return demo license status when provider not available
            return {
                "success": True,
                "data": {
                    "status": "active",
                    "license_type": "WARP_DEMO",
                    "user_name": "WARP Demo User",
                    "user_email": "warp-demo@warp-test.com",
                    "expires": "2025-12-31T23:59:59Z",
                    "days_remaining": 365,
                    "features": ["basic", "warp_demo", "enterprise"],
                    "watermark": "WARP_FAKE_DEMO_LICENSE"
                }
            }
        
        try:
            result = await license_provider.get_license_status()
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get license status: {str(e)}",
                "data": None
            }
    
    async def validate_license(self, license_key: str) -> Dict[str, Any]:
        """Validate a license key"""
        license_provider = self.get_provider("license")
        
        if not license_provider:
            return {
                "success": False,
                "error": "License provider not available"
            }
        
        try:
            result = await license_provider.validate_license(license_key)
            
            if result.get("success"):
                await self.broadcast_message({
                    "type": "license_validated",
                    "data": {
                        "controller": self.name,
                        "valid": result.get("valid", False),
                        "license_type": result.get("license_type"),
                        "user": result.get("user_name")
                    }
                })
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"License validation failed: {str(e)}"
            }
    
    async def activate_license(self, license_key: str, user_email: str) -> Dict[str, Any]:
        """Activate a license"""
        license_provider = self.get_provider("license")
        
        if not license_provider:
            return {
                "success": False,
                "error": "License provider not available"
            }
        
        try:
            result = await license_provider.activate_license(license_key, user_email)
            
            if result.get("success"):
                await self.broadcast_message({
                    "type": "license_activated",
                    "data": {
                        "controller": self.name,
                        "user_email": user_email,
                        "license_type": result.get("license_type"),
                        "message": "License activated successfully"
                    }
                })
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"License activation failed: {str(e)}"
            }