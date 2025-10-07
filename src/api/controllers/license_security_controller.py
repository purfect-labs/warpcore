#!/usr/bin/env python3
"""
WARPCORE License Security Controller - PAP Compliant
Business logic controller for license security operations
Controller → Orchestrator → Provider → Middleware → Executor
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta

from .base_controller import BaseController
from ..orchestrators.license_security_orchestrator import LicenseSecurityOrchestrator


class LicenseSecurityController(BaseController):
    """PAP Controller: Business logic for license security operations"""
    
    def __init__(self):
        super().__init__("license_security")
        self.orchestrator = LicenseSecurityOrchestrator()
        self.logger = logging.getLogger(__name__)
    
    async def validate_security(self, 
                              license_key: Optional[str] = None,
                              license_data: Optional[Dict[str, Any]] = None,
                              validation_type: str = "comprehensive") -> Dict[str, Any]:
        """
        PAP Controller: Validate license security
        Delegates to orchestrator for workflow coordination
        """
        try:
            # Input validation and sanitization (controller responsibility)
            if not license_key and not license_data:
                return {
                    "success": False,
                    "error": "Either license_key or license_data must be provided",
                    "validation_type": validation_type
                }
            
            # Validate validation_type
            valid_types = ["comprehensive", "encryption", "hardware", "tampering", "compliance"]
            if validation_type not in valid_types:
                return {
                    "success": False,
                    "error": f"Invalid validation_type. Must be one of: {valid_types}",
                    "validation_type": validation_type
                }
            
            # Delegate to orchestrator for complex workflow coordination
            result = await self.orchestrator.orchestrate_security_validation(
                license_key=license_key,
                license_data=license_data,
                validation_type=validation_type
            )
            
            # Controller-level result processing and logging
            await self.broadcast_message({
                'type': 'license_security_validation',
                'data': {
                    'validation_type': validation_type,
                    'success': result.get('success', False),
                    'security_level': result.get('security_level', 'unknown'),
                    'timestamp': datetime.now().isoformat()
                }
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"License security validation controller error: {str(e)}")
            return {
                "success": False,
                "error": f"Security validation failed: {str(e)}",
                "validation_type": validation_type
            }
    
    async def assess_compliance(self,
                              license_data: Dict[str, Any],
                              standards: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        PAP Controller: Assess license compliance
        Business logic for compliance checking
        """
        try:
            # Input validation
            if not license_data:
                return {
                    "success": False,
                    "error": "License data is required for compliance assessment"
                }
            
            # Default standards if none provided
            if not standards:
                standards = ["encryption_strength", "hardware_binding", "tamper_detection"]
            
            # Delegate to orchestrator for compliance workflow
            result = await self.orchestrator.orchestrate_compliance_assessment(
                license_data=license_data,
                standards=standards
            )
            
            # Controller-level processing
            await self.broadcast_message({
                'type': 'license_compliance_assessment',
                'data': {
                    'standards_checked': len(standards),
                    'compliance_score': result.get('compliance_score', 0),
                    'passed': result.get('success', False),
                    'timestamp': datetime.now().isoformat()
                }
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"License compliance assessment controller error: {str(e)}")
            return {
                "success": False,
                "error": f"Compliance assessment failed: {str(e)}",
                "compliance_score": 0
            }
    
    async def assess_vulnerabilities(self, license_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        PAP Controller: Assess security vulnerabilities
        Business logic for vulnerability detection
        """
        try:
            if not license_data:
                return {
                    "success": False,
                    "error": "License data is required for vulnerability assessment"
                }
            
            # Delegate to orchestrator for vulnerability assessment workflow
            result = await self.orchestrator.orchestrate_vulnerability_assessment(license_data)
            
            # Controller-level risk assessment
            risk_level = result.get('risk_level', 'unknown')
            issues_count = len(result.get('issues', []))
            
            await self.broadcast_message({
                'type': 'license_vulnerability_assessment',
                'data': {
                    'risk_level': risk_level,
                    'issues_found': issues_count,
                    'assessment_completed': result.get('success', False),
                    'timestamp': datetime.now().isoformat()
                }
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"License vulnerability assessment controller error: {str(e)}")
            return {
                "success": False,
                "error": f"Vulnerability assessment failed: {str(e)}",
                "risk_level": "unknown"
            }
    
    async def get_security_audit(self,
                               audit_type: str = "recent",
                               time_range_hours: int = 24) -> Dict[str, Any]:
        """
        PAP Controller: Retrieve security audit data
        Business logic for audit data aggregation
        """
        try:
            # Input validation
            valid_audit_types = ["recent", "full", "compliance", "violations", "metrics"]
            if audit_type not in valid_audit_types:
                return {
                    "success": False,
                    "error": f"Invalid audit_type. Must be one of: {valid_audit_types}"
                }
            
            if time_range_hours <= 0 or time_range_hours > 8760:  # Max 1 year
                return {
                    "success": False,
                    "error": "time_range_hours must be between 1 and 8760 (1 year)"
                }
            
            # Delegate to orchestrator for audit data workflow
            result = await self.orchestrator.orchestrate_security_audit(
                audit_type=audit_type,
                time_range_hours=time_range_hours
            )
            
            # Controller-level audit summary
            await self.broadcast_message({
                'type': 'license_security_audit',
                'data': {
                    'audit_type': audit_type,
                    'time_range_hours': time_range_hours,
                    'events_found': result.get('events_count', 0),
                    'audit_completed': result.get('success', False),
                    'timestamp': datetime.now().isoformat()
                }
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"License security audit controller error: {str(e)}")
            return {
                "success": False,
                "error": f"Security audit failed: {str(e)}",
                "audit_type": audit_type
            }
    
    async def get_security_status(self) -> Dict[str, Any]:
        """
        PAP Controller: Get overall security system status
        Business logic for status aggregation
        """
        try:
            # Delegate to orchestrator for status orchestration
            result = await self.orchestrator.orchestrate_security_status()
            
            # Controller-level status processing
            status_data = {
                'system_status': result.get('system_status', 'unknown'),
                'components_healthy': result.get('components_healthy', 0),
                'last_check': datetime.now().isoformat(),
                'security_level': result.get('security_level', 'unknown')
            }
            
            await self.broadcast_message({
                'type': 'license_security_status',
                'data': status_data
            })
            
            return {
                "success": True,
                **status_data,
                **result
            }
            
        except Exception as e:
            self.logger.error(f"License security status controller error: {str(e)}")
            return {
                "success": False,
                "error": f"Security status failed: {str(e)}",
                "system_status": "error"
            }
    
    async def get_security_metrics(self) -> Dict[str, Any]:
        """
        PAP Controller: Get security metrics and performance data
        Business logic for metrics aggregation
        """
        try:
            # Delegate to orchestrator for metrics orchestration
            result = await self.orchestrator.orchestrate_security_metrics()
            
            # Controller-level metrics processing
            metrics_data = {
                'total_validations': result.get('total_validations', 0),
                'successful_validations': result.get('successful_validations', 0),
                'security_incidents': result.get('security_incidents', 0),
                'average_response_time': result.get('average_response_time', 0.0),
                'last_updated': datetime.now().isoformat()
            }
            
            await self.broadcast_message({
                'type': 'license_security_metrics',
                'data': metrics_data
            })
            
            return {
                "success": True,
                **metrics_data,
                **result
            }
            
        except Exception as e:
            self.logger.error(f"License security metrics controller error: {str(e)}")
            return {
                "success": False,
                "error": f"Security metrics failed: {str(e)}",
                "total_validations": 0
            }
    
    async def log_security_event(self, event_type: str, event_data: Dict[str, Any]):
        """
        PAP Controller: Log security events
        Business logic for security event logging
        """
        try:
            # Delegate to orchestrator for audit logging workflow
            await self.orchestrator.orchestrate_audit_logging(
                event_type=event_type,
                event_data=event_data
            )
            
        except Exception as e:
            self.logger.error(f"Security event logging error: {str(e)}")
    
    async def get_status(self) -> Dict[str, Any]:
        """
        PAP Controller: Get controller status (required by BaseController)
        """
        try:
            orchestrator_status = await self.orchestrator.get_status()
            
            return {
                "success": True,
                "controller": "license_security",
                "status": "active",
                "orchestrator_status": orchestrator_status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "controller": "license_security", 
                "status": "error",
                "error": str(e)
            }