#!/usr/bin/env python3
"""
WARPCORE License Server Routes
Basic routes for purchase, validation, and management
"""

from fastapi import HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime


# Request models
class LicenseValidateRequest(BaseModel):
    license_key: str
    hardware_signature: Optional[str] = None


class LicenseGenerateRequest(BaseModel):
    user_email: str
    user_name: str
    license_type: str = "trial"  # trial, standard, enterprise
    hardware_signature: Optional[str] = None


class LicensePurchaseRequest(BaseModel):
    user_email: str
    user_name: str
    license_type: str
    payment_method: str = "stripe"


def setup_license_server_routes(app, license_provider, payment_service, email_service):
    """Setup license server routes"""
    
    @app.post("/api/license/generate")
    async def generate_license(request: LicenseGenerateRequest):
        """Generate a new license (for testing)"""
        try:
            result = await license_provider.generate_license(
                user_email=request.user_email,
                user_name=request.user_name,
                license_type=request.license_type,
                hardware_signature=request.hardware_signature
            )
            
            if result["success"]:
                return result
            else:
                raise HTTPException(status_code=400, detail=result["error"])
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"License generation failed: {str(e)}")
    
    @app.post("/api/license/validate")
    async def validate_license(request: LicenseValidateRequest):
        """Validate a license key remotely"""
        try:
            result = await license_provider.validate_license(
                license_key=request.license_key,
                hardware_signature=request.hardware_signature
            )
            
            # Add server info
            result["server_mode"] = license_provider.config.mode
            result["validated_at"] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation failed: {str(e)}",
                "server_mode": license_provider.config.mode
            }
    
    @app.get("/api/license/types")
    async def get_license_types():
        """Get available license types and pricing"""
        return license_provider.get_license_types()
    
    @app.post("/api/license/purchase")
    async def purchase_license(request: LicensePurchaseRequest, background_tasks: BackgroundTasks):
        """Purchase a license (simplified for demo)"""
        try:
            # For demo mode, simulate immediate success
            if license_provider.config.mode == "local":
                # Generate license immediately for demo
                result = await license_provider.generate_license(
                    user_email=request.user_email,
                    user_name=request.user_name,
                    license_type=request.license_type
                )
                
                if result["success"]:
                    # Add purchase info
                    result["purchase_completed"] = True
                    result["message"] = f"{request.license_type} license purchased successfully"
                    
                    return result
                else:
                    raise HTTPException(status_code=400, detail=result["error"])
            
            # For real modes, would integrate with payment processing
            else:
                return {
                    "success": False,
                    "error": "Payment processing not implemented for remote mode",
                    "message": "Real payment processing would be implemented for production remote server"
                }
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Purchase failed: {str(e)}")
    
    @app.get("/api/license/user/{user_email}")
    async def get_user_licenses(user_email: str):
        """Get all licenses for a user"""
        try:
            result = await license_provider.list_user_licenses(user_email)
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get user licenses: {str(e)}")
    
    @app.delete("/api/license/revoke/{license_id}")
    async def revoke_license(license_id: str):
        """Revoke a license"""
        try:
            result = await license_provider.revoke_license(license_id)
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to revoke license: {str(e)}")
    
    @app.get("/api/server/status")
    async def get_server_status():
        """Get license server status"""
        return {
            "status": "running",
            "mode": license_provider.config.mode,
            "server": "WARP_LICENSE_SERVER",
            "timestamp": datetime.now().isoformat(),
            "features": {
                "payment_processing": license_provider.config.is_payment_enabled(),
                "email_delivery": license_provider.config.is_email_enabled(),
                "database": "sqlite" if "sqlite" in license_provider.config.get_database_url() else "postgresql"
            }
        }