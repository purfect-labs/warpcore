#!/usr/bin/env python3
"""
WARPCORE License Security Routes - PAP Compliant
Routes for license security operations following Provider-Abstraction-Pattern
Route → Controller → Orchestrator → Provider → Middleware → Executor
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

# Import PAP components
from ..controllers.license_security_controller import LicenseSecurityController

logger = logging.getLogger(__name__)

# Initialize PAP-compliant router
router = APIRouter(prefix="/api/license/security", tags=["License Security"])


class SecurityValidationRequest(BaseModel):
    """Request model for security validation"""
    license_key: Optional[str] = None
    license_data: Optional[Dict[str, Any]] = None
    validation_type: str = "comprehensive"  # comprehensive, encryption, hardware, tampering


class ComplianceAssessmentRequest(BaseModel):
    """Request model for compliance assessment"""
    license_data: Dict[str, Any]
    compliance_standards: Optional[List[str]] = None


class SecurityAuditRequest(BaseModel):
    """Request model for security audit"""
    audit_type: str = "full"  # full, recent, compliance, violations
    time_range_hours: Optional[int] = 24


# PAP Route Layer - Entry points with minimal logic
@router.post("/validate")
async def validate_license_security(
    request: SecurityValidationRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    PAP Route: License security validation
    Delegates to LicenseSecurityController for business logic
    """
    try:
        # Get controller instance (dependency injection)
        controller = LicenseSecurityController()
        
        # Delegate to controller layer
        result = await controller.validate_security(
            license_key=request.license_key,
            license_data=request.license_data,
            validation_type=request.validation_type
        )
        
        # Background audit logging
        background_tasks.add_task(
            controller.log_security_event,
            "security_validation_request",
            {"validation_type": request.validation_type, "success": result.get("success", False)}
        )
        
        return result
        
    except Exception as e:
        logger.error(f"License security validation route error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Security validation failed: {str(e)}")


@router.post("/compliance")
async def assess_compliance(
    request: ComplianceAssessmentRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    PAP Route: License compliance assessment
    Delegates to LicenseSecurityController for compliance checking
    """
    try:
        controller = LicenseSecurityController()
        
        result = await controller.assess_compliance(
            license_data=request.license_data,
            standards=request.compliance_standards
        )
        
        background_tasks.add_task(
            controller.log_security_event,
            "compliance_assessment_request",
            {"standards_count": len(request.compliance_standards or []), "score": result.get("compliance_score", 0)}
        )
        
        return result
        
    except Exception as e:
        logger.error(f"License compliance route error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Compliance assessment failed: {str(e)}")


@router.post("/vulnerabilities")
async def assess_vulnerabilities(
    license_data: Dict[str, Any],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    PAP Route: License vulnerability assessment
    Delegates to controller for security vulnerability detection
    """
    try:
        controller = LicenseSecurityController()
        
        result = await controller.assess_vulnerabilities(license_data)
        
        background_tasks.add_task(
            controller.log_security_event,
            "vulnerability_assessment_request",
            {"risk_level": result.get("risk_level", "unknown"), "issues_found": len(result.get("issues", []))}
        )
        
        return result
        
    except Exception as e:
        logger.error(f"License vulnerability assessment route error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Vulnerability assessment failed: {str(e)}")


@router.get("/audit")
async def get_security_audit(
    background_tasks: BackgroundTasks,
    audit_type: str = "recent",
    time_range_hours: int = 24
) -> Dict[str, Any]:
    """
    PAP Route: Security audit data retrieval
    Delegates to controller for audit log analysis
    """
    try:
        controller = LicenseSecurityController()
        
        result = await controller.get_security_audit(
            audit_type=audit_type,
            time_range_hours=time_range_hours
        )
        
        background_tasks.add_task(
            controller.log_security_event,
            "security_audit_request",
            {"audit_type": audit_type, "time_range": time_range_hours}
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Security audit route error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Security audit failed: {str(e)}")


@router.get("/status")
async def get_security_status() -> Dict[str, Any]:
    """
    PAP Route: Get overall license security system status
    Minimal route logic - delegates to controller
    """
    try:
        controller = LicenseSecurityController()
        return await controller.get_security_status()
        
    except Exception as e:
        logger.error(f"Security status route error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Security status failed: {str(e)}")


@router.get("/metrics")
async def get_security_metrics() -> Dict[str, Any]:
    """
    PAP Route: Get security metrics and performance data
    Delegates to controller for metrics aggregation
    """
    try:
        controller = LicenseSecurityController()
        return await controller.get_security_metrics()
        
    except Exception as e:
        logger.error(f"Security metrics route error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Security metrics failed: {str(e)}")


# Register routes for auto-discovery
def get_license_security_routes():
    """Get license security router for registration"""
    return router