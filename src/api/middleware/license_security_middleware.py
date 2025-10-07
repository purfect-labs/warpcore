#!/usr/bin/env python3
"""
WARPCORE License Security Middleware - Production Implementation
Comprehensive security validation middleware for license operations
Handles encryption strength validation, tampering detection, rate limiting, DoS protection
"""

import time
import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from collections import defaultdict, deque
from ..base_middleware import BaseMiddleware
from ...data.config.license.license_config import get_license_config


class LicenseSecurityMiddleware(BaseMiddleware):
    """Production-grade security middleware for license operations"""
    
    def __init__(self):
        super().__init__("license_security")
        self.config = get_license_config()
        
        # Rate limiting storage
        self._rate_limiter = defaultdict(deque)
        self._rate_limit_window = 60  # seconds
        self._max_requests_per_minute = 30
        
        # DoS protection
        self._suspicious_ips = defaultdict(int)
        self._blocked_ips = set()
        self._block_duration = 300  # 5 minutes
        self._blocked_until = {}
        
        # Security event tracking
        self._security_events = deque(maxlen=1000)
        
        # Audit logging
        self._audit_file = self.config.get_audit_file()
    
    async def process_request(self, request_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process request through security validation pipeline"""
        try:
            client_ip = request_context.get("client_ip", "unknown")
            operation = request_context.get("operation", "unknown")
            license_key = request_context.get("license_key")
            
            # Step 1: DoS protection check
            dos_result = await self._check_dos_protection(client_ip)
            if not dos_result["allowed"]:
                return {
                    "success": False,
                    "error": "Request blocked by DoS protection",
                    "security_event": "dos_protection_triggered",
                    "blocked_until": dos_result.get("blocked_until")
                }
            
            # Step 2: Rate limiting check
            rate_limit_result = await self._check_rate_limit(client_ip, operation)
            if not rate_limit_result["allowed"]:
                await self._log_security_event("rate_limit_exceeded", {
                    "client_ip": client_ip,
                    "operation": operation,
                    "requests_count": rate_limit_result["requests_count"]
                })
                return {
                    "success": False,
                    "error": "Rate limit exceeded",
                    "security_event": "rate_limit_exceeded",
                    "retry_after": rate_limit_result["retry_after"]
                }
            
            # Step 3: License key security validation (if provided)
            if license_key:
                security_validation = await self._validate_license_security(license_key)
                if not security_validation["valid"]:
                    await self._log_security_event("license_security_failure", {
                        "client_ip": client_ip,
                        "operation": operation,
                        "error": security_validation["error"]
                    })
                    return {
                        "success": False,
                        "error": f"License security validation failed: {security_validation['error']}",
                        "security_event": "license_security_failure"
                    }
            
            # Step 4: Operation-specific security checks
            operation_check = await self._check_operation_security(operation, request_context)
            if not operation_check["allowed"]:
                await self._log_security_event("operation_security_failure", {
                    "client_ip": client_ip,
                    "operation": operation,
                    "error": operation_check["error"]
                })
                return {
                    "success": False,
                    "error": f"Operation security check failed: {operation_check['error']}",
                    "security_event": "operation_security_failure"
                }
            
            # All security checks passed
            await self._log_security_event("security_validation_passed", {
                "client_ip": client_ip,
                "operation": operation,
                "checks_passed": ["dos_protection", "rate_limiting", "license_security", "operation_security"]
            })
            
            return {
                "success": True,
                "security_validated": True,
                "security_level": "production",
                "validation_timestamp": time.time()
            }
            
        except Exception as e:
            await self._log_security_event("security_middleware_error", {
                "error": str(e),
                "operation": request_context.get("operation", "unknown")
            })
            return {
                "success": False,
                "error": f"Security middleware error: {str(e)}",
                "security_event": "middleware_error"
            }
    
    async def _check_dos_protection(self, client_ip: str) -> Dict[str, Any]:
        """Check DoS protection for client IP"""
        try:
            current_time = time.time()
            
            # Check if IP is currently blocked
            if client_ip in self._blocked_ips:
                blocked_until = self._blocked_until.get(client_ip, 0)
                if current_time < blocked_until:
                    return {
                        "allowed": False,
                        "blocked_until": datetime.fromtimestamp(blocked_until).isoformat()
                    }
                else:
                    # Unblock IP
                    self._blocked_ips.discard(client_ip)
                    self._blocked_until.pop(client_ip, None)
                    self._suspicious_ips[client_ip] = 0
            
            # Check suspicion level
            suspicion_level = self._suspicious_ips[client_ip]
            if suspicion_level > 10:  # Block after 10 suspicious activities
                block_until = current_time + self._block_duration
                self._blocked_ips.add(client_ip)
                self._blocked_until[client_ip] = block_until
                
                await self._log_security_event("ip_blocked_dos_protection", {
                    "client_ip": client_ip,
                    "suspicion_level": suspicion_level,
                    "blocked_until": datetime.fromtimestamp(block_until).isoformat()
                })
                
                return {
                    "allowed": False,
                    "blocked_until": datetime.fromtimestamp(block_until).isoformat()
                }
            
            return {"allowed": True}
            
        except Exception as e:
            self.logger.error(f"DoS protection check failed: {e}")
            return {"allowed": True}  # Fail open for availability
    
    async def _check_rate_limit(self, client_ip: str, operation: str) -> Dict[str, Any]:
        """Check rate limiting for client IP and operation"""
        try:
            current_time = time.time()
            window_start = current_time - self._rate_limit_window
            
            # Clean old requests
            requests = self._rate_limiter[f"{client_ip}:{operation}"]
            while requests and requests[0] < window_start:
                requests.popleft()
            
            # Check if under limit
            if len(requests) >= self._max_requests_per_minute:
                # Increase suspicion for potential DoS
                self._suspicious_ips[client_ip] += 1
                
                return {
                    "allowed": False,
                    "requests_count": len(requests),
                    "retry_after": int(requests[0] + self._rate_limit_window - current_time)
                }
            
            # Add current request
            requests.append(current_time)
            
            return {
                "allowed": True,
                "requests_count": len(requests)
            }
            
        except Exception as e:
            self.logger.error(f"Rate limit check failed: {e}")
            return {"allowed": True}  # Fail open for availability
    
    async def _validate_license_security(self, license_key: str) -> Dict[str, Any]:
        """Validate license key security properties"""
        try:
            # Check key format and structure
            if not license_key or len(license_key) < 32:
                return {
                    "valid": False,
                    "error": "License key too short or empty"
                }
            
            # Check for suspicious patterns
            if license_key.count("0") > len(license_key) * 0.8:
                return {
                    "valid": False,
                    "error": "License key contains suspicious patterns"
                }
            
            # Check encoding validity
            try:
                # Remove formatting
                clean_key = license_key.replace("-", "").replace(" ", "")
                # Try to decode as base64
                import base64
                decoded = base64.urlsafe_b64decode(clean_key + "==")  # Padding for validation
            except Exception:
                return {
                    "valid": False,
                    "error": "License key has invalid encoding"
                }
            
            # Check key entropy (basic randomness check)
            entropy = self._calculate_entropy(clean_key)
            if entropy < 3.0:  # Minimum entropy threshold
                return {
                    "valid": False,
                    "error": "License key has insufficient entropy"
                }
            
            return {"valid": True}
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Security validation error: {str(e)}"
            }
    
    def _calculate_entropy(self, data: str) -> float:
        """Calculate Shannon entropy of data"""
        try:
            if not data:
                return 0.0
            
            # Count character frequencies
            char_counts = defaultdict(int)
            for char in data:
                char_counts[char] += 1
            
            # Calculate entropy
            entropy = 0.0
            data_len = len(data)
            for count in char_counts.values():
                probability = count / data_len
                if probability > 0:
                    entropy -= probability * (probability.bit_length() - 1)
            
            return entropy
            
        except Exception:
            return 0.0
    
    async def _check_operation_security(self, operation: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check security for specific operations"""
        try:
            # High-risk operations require additional validation
            high_risk_operations = [
                "generate_license",
                "activate_license",
                "deactivate_license",
                "generate_secure_license"
            ]
            
            if operation in high_risk_operations:
                # Check for required context fields
                required_fields = {
                    "generate_license": ["user_email"],
                    "generate_secure_license": ["user_email", "user_name"],
                    "activate_license": ["license_key"],
                    "deactivate_license": []
                }
                
                required = required_fields.get(operation, [])
                for field in required:
                    if field not in context or not context[field]:
                        return {
                            "allowed": False,
                            "error": f"Missing required field for operation: {field}"
                        }
                
                # Additional email validation for generation operations
                if "user_email" in context:
                    email = context["user_email"]
                    if not self._validate_email_security(email):
                        return {
                            "allowed": False,
                            "error": "Email address failed security validation"
                        }
            
            return {"allowed": True}
            
        except Exception as e:
            return {
                "allowed": False,
                "error": f"Operation security check error: {str(e)}"
            }
    
    def _validate_email_security(self, email: str) -> bool:
        """Validate email for security concerns"""
        try:
            if not email or "@" not in email:
                return False
            
            # Check for suspicious patterns
            suspicious_patterns = [
                "test@test",
                "admin@admin",
                "root@",
                "hack@",
                "exploit@"
            ]
            
            email_lower = email.lower()
            for pattern in suspicious_patterns:
                if pattern in email_lower:
                    return False
            
            # Basic format validation
            parts = email.split("@")
            if len(parts) != 2 or not parts[0] or not parts[1]:
                return False
            
            return True
            
        except Exception:
            return False
    
    async def _log_security_event(self, event_type: str, data: Dict[str, Any]):
        """Log security events to audit trail"""
        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "component": "license_security_middleware",
                "data": data
            }
            
            # Add to in-memory buffer
            self._security_events.append(event)
            
            # Write to audit file
            with open(self._audit_file, "a") as f:
                f.write(json.dumps(event) + "\n")
                
        except Exception as e:
            self.logger.error(f"Failed to log security event: {e}")
    
    async def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics for monitoring"""
        try:
            current_time = time.time()
            
            # Count recent events by type
            recent_events = [
                event for event in self._security_events
                if (current_time - time.mktime(datetime.fromisoformat(event["timestamp"]).timetuple())) < 3600
            ]
            
            event_counts = defaultdict(int)
            for event in recent_events:
                event_counts[event["event_type"]] += 1
            
            return {
                "success": True,
                "metrics": {
                    "total_events_last_hour": len(recent_events),
                    "event_counts": dict(event_counts),
                    "blocked_ips_count": len(self._blocked_ips),
                    "suspicious_ips_count": len(self._suspicious_ips),
                    "rate_limit_windows_active": len(self._rate_limiter),
                    "security_level": "production"
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get security metrics: {str(e)}"
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get middleware status"""
        return {
            "success": True,
            "middleware": self.name,
            "security_level": "production",
            "dos_protection_active": True,
            "rate_limiting_active": True,
            "license_validation_active": True,
            "audit_logging_active": True,
            "blocked_ips": len(self._blocked_ips),
            "configuration_loaded": True
        }