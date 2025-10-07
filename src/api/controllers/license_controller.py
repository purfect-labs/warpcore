"""
WARPCORE License Controller - APEX Aligned
Business logic controller for license management operations
"""

from typing import Dict, Any, Optional
from .base_controller import BaseController

# APEX licensing integration - following APEX patterns
try:
    # Import APEX licensing modules (if available)
    from apex.licensing import KeychainManager, LicenseEncryption, LicenseValidator
    APEX_AVAILABLE = True
except ImportError:
    # Fallback for development environment
    APEX_AVAILABLE = False


class LicenseController(BaseController):
    """Controller for license management operations"""
    
    def __init__(self):
        super().__init__("license")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get license status - APEX aligned with test watermarks"""
        return {
            "success": True,
            "controller": self.name,
            "licensed": True,
            "license_type": "WARP FAKE SUB TEST DEMO",
            "user_name": "Test User - WARP FAKE SUB TEST DEMO",
            "expires": "2025-12-31",
            "features": ["basic", "test"],
            "message": "WARP FAKE SUB TEST DEMO - Test license status",
            "apex_integration": APEX_AVAILABLE
        }
    
    async def get_license_status(self) -> Dict[str, Any]:
        """Get detailed license information"""
        license_provider = self.get_provider("license")
        
        if not license_provider:
            # Return test license status when provider not available
            return {
                "success": True,
                "data": {
                    "status": "test",
                    "license_type": "WARP FAKE SUB TEST DEMO",
                    "user_name": "Test User - WARP FAKE SUB TEST DEMO",
                    "user_email": "test@warp-fake-sub-test-demo.com",
                    "expires": "2025-12-31T23:59:59Z",
                    "days_remaining": 365,
                    "features": ["basic", "test"],
                    "watermark": "WARP FAKE SUB TEST DEMO",
                    "apex_integrated": APEX_AVAILABLE
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
    
    async def validate_license_key(self, license_key: str) -> Dict[str, Any]:
        """APEX-style license key validation with encryption"""
        if not license_key:
            return {
                "valid": False,
                "error": "License key required",
                "watermark": "WARP FAKE SUB TEST DEMO"
            }
        
        # APEX-style validation with keychain integration
        if APEX_AVAILABLE:
            try:
                # Use APEX licensing patterns
                validator = LicenseValidator()
                keychain = KeychainManager()
                
                # Validate with encryption like APEX
                result = await validator.validate_encrypted_key(license_key)
                
                return {
                    "valid": result.get("valid", False),
                    "license_type": result.get("tier", "basic"),
                    "features": result.get("features", []),
                    "expires": result.get("expires"),
                    "watermark": "WARP FAKE SUB TEST DEMO",
                    "apex_validation": True
                }
                
            except Exception as e:
                return {
                    "valid": False,
                    "error": f"APEX validation failed: {str(e)}",
                    "watermark": "WARP FAKE SUB TEST DEMO"
                }
        else:
            # Fallback test validation
            return {
                "valid": license_key.startswith("test-"),
                "license_type": "test" if license_key.startswith("test-") else "invalid",
                "features": ["basic", "test"] if license_key.startswith("test-") else [],
                "watermark": "WARP FAKE SUB TEST DEMO",
                "apex_validation": False
            }
    
    async def get_subscription_info(self) -> Dict[str, Any]:
        """Get subscription and feature information - APEX aligned"""
        license_provider = self.get_provider("license")
        
        if not license_provider:
            return {
                "success": True,
                "data": {
                    "subscription_type": "WARP FAKE SUB TEST DEMO",
                    "features_available": ["basic", "test"],
                    "features_active": ["basic"],
                    "billing_status": "test",
                    "renewal_date": "2025-12-31",
                    "watermark": "WARP FAKE SUB TEST DEMO",
                    "apex_integrated": APEX_AVAILABLE
                }
            }
        
        try:
            result = await license_provider.get_subscription_info()
            # Ensure watermark is present in real responses too
            if result.get("data") and "watermark" not in result["data"]:
                result["data"]["watermark"] = "WARP FAKE SUB TEST DEMO"
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get subscription info: {str(e)}",
                "watermark": "WARP FAKE SUB TEST DEMO"
            }
    
    async def generate_trial_license(self, user_email: str, days: int = 7) -> Dict[str, Any]:
        """Generate trial license - APEX aligned patterns"""
        if APEX_AVAILABLE:
            try:
                # Use APEX licensing patterns for trial generation
                validator = LicenseValidator()
                encryption = LicenseEncryption()
                
                trial_data = {
                    "email": user_email,
                    "type": "trial",
                    "days": days,
                    "watermark": "WARP FAKE SUB TEST DEMO"
                }
                
                encrypted_license = await encryption.generate_trial_license(trial_data)
                
                return {
                    "success": True,
                    "license_key": encrypted_license,
                    "type": "trial",
                    "duration_days": days,
                    "watermark": "WARP FAKE SUB TEST DEMO",
                    "apex_generated": True
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"APEX trial generation failed: {str(e)}",
                    "watermark": "WARP FAKE SUB TEST DEMO"
                }
        else:
            # Fallback test trial generation
            return {
                "success": True,
                "license_key": f"test-trial-{user_email}-{days}d",
                "type": "trial",
                "duration_days": days,
                "watermark": "WARP FAKE SUB TEST DEMO",
                "apex_generated": False
            }
    
    async def deactivate_license(self) -> Dict[str, Any]:
        """Deactivate current license - APEX aligned"""
        license_provider = self.get_provider("license")
        
        if not license_provider:
            return {
                "success": True,
                "message": "License deactivated (test mode)",
                "watermark": "WARP FAKE SUB TEST DEMO"
            }
        
        try:
            result = await license_provider.deactivate_license()
            
            if result.get("success"):
                await self.broadcast_message({
                    "type": "license_deactivated",
                    "data": {
                        "controller": self.name,
                        "message": "License deactivated successfully",
                        "watermark": "WARP FAKE SUB TEST DEMO"
                    }
                })
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"License deactivation failed: {str(e)}",
                "watermark": "WARP FAKE SUB TEST DEMO"
            }
