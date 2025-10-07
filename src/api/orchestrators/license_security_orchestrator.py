#!/usr/bin/env python3
"""
WARPCORE License Security Orchestrator - PAP Compliant
Coordinates workflows across providers, middleware, and executors
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .base_orchestrator import BaseOrchestrator
from ..providers.license.license_provider import LicenseProvider
from ..middleware.license.license_security_middleware import LicenseSecurityMiddleware


class LicenseSecurityOrchestrator(BaseOrchestrator):
    """PAP Orchestrator: Coordinates license security workflows"""

    def __init__(self):
        super().__init__("license_security")
        self.provider = LicenseProvider()
        self.middleware = LicenseSecurityMiddleware()
        self.logger = logging.getLogger(__name__)

    async def orchestrate_security_validation(self, 
                                            license_key: Optional[str],
                                            license_data: Optional[Dict[str, Any]],
                                            validation_type: str) -> Dict[str, Any]:
        """Coordinate comprehensive security validation workflow"""
        try:
            # Apply middleware security gates first (rate limiting, DoS, etc.)
            await self.middleware.apply_security_gates({
                'operation': 'validate_security',
                'validation_type': validation_type,
                'timestamp': datetime.now().isoformat()
            })

            # Determine validation path based on inputs
            if license_key and not license_data:
                decoded = await self.provider._validate_license_key(license_key)
                if not decoded.get('valid'):
                    return {
                        'success': False,
                        'error': decoded.get('error', 'Invalid license key'),
                        'security_level': 'development'
                    }
                license_data = decoded.get('license_info', {})

            # Perform requested validation type(s)
            results = {}
            overall_valid = True

            if validation_type in ('comprehensive', 'encryption'):
                results['encryption'] = await self.provider._validate_encryption_strength(license_data, license_key)
                overall_valid = overall_valid and results['encryption'].get('valid', False)

            if validation_type in ('comprehensive', 'hardware'):
                results['hardware_binding'] = {
                    'valid': self.provider._validate_hardware_binding(license_data)
                }
                overall_valid = overall_valid and results['hardware_binding'].get('valid', False)

            if validation_type in ('comprehensive', 'tampering'):
                results['tampering'] = self.provider._detect_tampering(license_data)
                if results['tampering'].get('tampered'):
                    overall_valid = False

            if validation_type in ('comprehensive', 'compliance'):
                # Derive compliance score from above checks
                score = 0
                if 'encryption' in results and results['encryption'].get('valid'):
                    score += 40
                if 'hardware_binding' in results and results['hardware_binding'].get('valid'):
                    score += 30
                if 'tampering' in results and not results['tampering'].get('tampered'):
                    score += 30
                results['compliance'] = {'score': score}

            # Determine security level
            security_level = 'production' if overall_valid and results.get('compliance', {}).get('score', 0) >= 90 else (
                'staging' if overall_valid else 'development'
            )

            # Log event via middleware
            await self.middleware.log_security_event('security_validation_complete', {
                'validation_type': validation_type,
                'overall_valid': overall_valid,
                'security_level': security_level
            })

            return {
                'success': overall_valid,
                'security_level': security_level,
                'validations': results,
                'compliance_score': results.get('compliance', {}).get('score', 0)
            }

        except Exception as e:
            await self.middleware.log_security_event('security_validation_error', {'error': str(e)})
            return {
                'success': False,
                'error': str(e),
                'security_level': 'development'
            }

    async def orchestrate_compliance_assessment(self, license_data: Dict[str, Any], standards: List[str]) -> Dict[str, Any]:
        """Coordinate compliance assessment workflow"""
        try:
            await self.middleware.apply_security_gates({'operation': 'compliance_assessment'})

            # Use provider methods for component validations
            results = {}
            score = 0

            if 'encryption_strength' in standards:
                results['encryption'] = await self.provider._validate_encryption_strength(license_data)
                if results['encryption'].get('valid'):
                    score += 40
            if 'hardware_binding' in standards:
                hb_valid = self.provider._validate_hardware_binding(license_data)
                results['hardware_binding'] = {'valid': hb_valid}
                if hb_valid:
                    score += 30
            if 'tamper_detection' in standards:
                tamper = self.provider._detect_tampering(license_data)
                results['tampering'] = tamper
                if not tamper.get('tampered'):
                    score += 30

            await self.middleware.log_security_event('compliance_assessment_complete', {'score': score})

            return {
                'success': score >= 70,
                'compliance_score': score,
                'validations': results
            }

        except Exception as e:
            await self.middleware.log_security_event('compliance_assessment_error', {'error': str(e)})
            return {'success': False, 'compliance_score': 0, 'error': str(e)}

    async def orchestrate_vulnerability_assessment(self, license_data: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate vulnerability assessment workflow"""
        try:
            await self.middleware.apply_security_gates({'operation': 'vulnerability_assessment'})
            result = await self.provider._assess_vulnerabilities(license_data)
            await self.middleware.log_security_event('vulnerability_assessment_complete', {'risk': result.get('risk_level')})
            return {'success': True, **result}
        except Exception as e:
            await self.middleware.log_security_event('vulnerability_assessment_error', {'error': str(e)})
            return {'success': False, 'error': str(e)}

    async def orchestrate_security_audit(self, audit_type: str, time_range_hours: int) -> Dict[str, Any]:
        """Coordinate security audit retrieval workflow"""
        try:
            await self.middleware.apply_security_gates({'operation': 'security_audit'})
            result = await self.middleware.get_security_audit(audit_type, time_range_hours)
            return {'success': True, **result}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def orchestrate_security_status(self) -> Dict[str, Any]:
        """Coordinate overall security status gathering"""
        try:
            await self.middleware.apply_security_gates({'operation': 'security_status'})
            middleware_status = await self.middleware.get_status()
            provider_status = await self.provider.get_license_status()

            components_healthy = int(middleware_status.get('healthy', False)) + int(provider_status.get('success', False))
            security_level = 'production' if components_healthy == 2 else ('staging' if components_healthy == 1 else 'development')

            return {
                'system_status': 'healthy' if components_healthy == 2 else ('degraded' if components_healthy == 1 else 'unhealthy'),
                'components_healthy': components_healthy,
                'security_level': security_level
            }
        except Exception as e:
            return {
                'system_status': 'error',
                'components_healthy': 0,
                'security_level': 'development',
                'error': str(e)
            }

    async def orchestrate_security_metrics(self) -> Dict[str, Any]:
        """Coordinate security metrics aggregation"""
        try:
            await self.middleware.apply_security_gates({'operation': 'security_metrics'})
            return await self.middleware.get_metrics()
        except Exception as e:
            return {
                'total_validations': 0,
                'successful_validations': 0,
                'security_incidents': 0,
                'average_response_time': 0.0,
                'error': str(e)
            }

    async def orchestrate_audit_logging(self, event_type: str, event_data: Dict[str, Any]):
        """Coordinate audit logging workflow"""
        try:
            await self.middleware.log_security_event(event_type, event_data)
        except Exception:
            pass

    async def get_status(self) -> Dict[str, Any]:
        """Orchestrator status for controller status endpoint"""
        try:
            middleware_status = await self.middleware.get_status()
            provider_status = await self.provider.get_license_status()
            return {
                'middleware': middleware_status,
                'provider': provider_status,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}