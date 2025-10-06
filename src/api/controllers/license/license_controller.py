"""
WARPCORE License Controller - PAP Layer 2
Business logic for license management
"""

from ..base_controller import BaseController
from typing import Dict, Any

class LicenseController(BaseController):
    """License controller - handles license validation and management"""
    
    def __init__(self):
        super().__init__("license_controller")
    
    async def get_license_status(self) -> Dict[str, Any]:
        """Get current license status"""
        try:
            license_provider = self.get_provider("license")
            if not license_provider:
                return {
                    "success": True,
                    "status": "no_license_required",
                    "message": "WARPCORE running in open mode"
                }
            
            return await license_provider.get_status()
            
        except Exception as e:
            return {
                "success": False,
                "error": f"License status error: {str(e)}"
            }