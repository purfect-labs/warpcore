#!/usr/bin/env python3
"""
WARPCORE License Security Middleware - PAP Compliant
Cross-cutting security concerns: rate limiting, DoS protection, audit logging
"""

import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict
import logging
import re

from ..base_middleware import BaseMiddleware
from ....data.config.license.license_config import get_license_config


class LicenseSecurityMiddleware(BaseMiddleware):
    """PAP Middleware: Cross-cutting security concerns for license operations"""
    
    def __init__(self):
        super().__init__("license_security")
        self.config = get_license_config()
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting state
        self._rate_limits = defaultdict(list)  # IP -> list of timestamps
        self._blocked_ips = {}  # IP -> block_until_timestamp
        
        # DoS protection settings
        self._max_requests_per_minute = 10
        self._max_requests_per_hour = 100
        self._block_duration_minutes = 15
        
        # Security monitoring
        self._security_events = []
        self._metrics = {
            'total_requests': 0,
            'blocked_requests': 0,
            'security_violations': 0,
            'audit_events': 0
        }
        
        # Vulnerability patterns for detection
        self._vulnerability_patterns = [
            r"(test|demo|fake|example)@",
            r"password.*123",
            r"admin.*admin",
            r"^(root|admin|test)$",
            r"['\";\\\\]",  # SQL injection patterns
            r"<script|javascript:",  # XSS patterns
        ]
        
        # Audit file
        self._audit_file = "/tmp/warpcore_license_security_audit.log"
    
    async def apply_security_gates(self, request_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        PAP Middleware: Apply security gates before processing
        Rate limiting, DoS protection, IP blocking
        """
        try:
            # Extract request metadata
            client_ip = request_context.get('client_ip', 'unknown')
            operation = request_context.get('operation', 'unknown')
            timestamp = time.time()
            
            self._metrics['total_requests'] += 1
            
            # Check if IP is currently blocked
            if client_ip in self._blocked_ips:
                if timestamp < self._blocked_ips[client_ip]:
                    self._metrics['blocked_requests'] += 1
                    await self.log_security_event('ip_blocked_request', {
                        'client_ip': client_ip,
                        'operation': operation,
                        'block_expires': datetime.fromtimestamp(self._blocked_ips[client_ip]).isoformat()
                    })
                    raise SecurityException(f"IP {client_ip} is blocked until {datetime.fromtimestamp(self._blocked_ips[client_ip])}")
                else:
                    # Block expired, remove it
                    del self._blocked_ips[client_ip]
            
            # Rate limiting check
            current_minute = int(timestamp // 60)
            current_hour = int(timestamp // 3600)
            
            # Clean old timestamps for this IP
            ip_requests = self._rate_limits[client_ip]
            self._rate_limits[client_ip] = [t for t in ip_requests if timestamp - t < 3600]  # Keep last hour
            
            # Count requests in current minute and hour
            minute_requests = sum(1 for t in self._rate_limits[client_ip] if int(t // 60) == current_minute)
            hour_requests = len(self._rate_limits[client_ip])
            
            # Apply rate limits
            if minute_requests >= self._max_requests_per_minute:
                await self._block_ip(client_ip, operation, "rate_limit_minute_exceeded")
                self._metrics['blocked_requests'] += 1
                raise SecurityException(f"Rate limit exceeded: {minute_requests} requests per minute")
            
            if hour_requests >= self._max_requests_per_hour:
                await self._block_ip(client_ip, operation, "rate_limit_hour_exceeded")
                self._metrics['blocked_requests'] += 1
                raise SecurityException(f"Rate limit exceeded: {hour_requests} requests per hour")
            
            # Record this request
            self._rate_limits[client_ip].append(timestamp)
            
            # DoS pattern detection
            await self._detect_dos_patterns(client_ip, operation, request_context)
            
            # Log successful gate passage
            await self.log_security_event('security_gates_passed', {
                'client_ip': client_ip,
                'operation': operation,
                'minute_requests': minute_requests,
                'hour_requests': hour_requests
            })
            
            return {
                'success': True,
                'gates_passed': True,
                'client_ip': client_ip,
                'operation': operation
            }
            
        except SecurityException:
            raise
        except Exception as e:
            self.logger.error(f"Security gates application error: {str(e)}")
            await self.log_security_event('security_gates_error', {'error': str(e)})
            raise SecurityException(f"Security gates failed: {str(e)}")
    
    async def _block_ip(self, client_ip: str, operation: str, reason: str):
        """Block an IP address for the configured duration"""
        block_until = time.time() + (self._block_duration_minutes * 60)
        self._blocked_ips[client_ip] = block_until
        
        await self.log_security_event('ip_blocked', {
            'client_ip': client_ip,
            'operation': operation,
            'reason': reason,
            'block_duration_minutes': self._block_duration_minutes,
            'block_until': datetime.fromtimestamp(block_until).isoformat()
        })
        
        self._metrics['security_violations'] += 1
    
    async def _detect_dos_patterns(self, client_ip: str, operation: str, request_context: Dict[str, Any]):
        """Detect DoS attack patterns"""
        try:
            # Pattern 1: Rapid successive identical requests
            recent_requests = [t for t in self._rate_limits[client_ip] if time.time() - t < 10]  # Last 10 seconds
            if len(recent_requests) >= 5:  # 5+ requests in 10 seconds
                await self._block_ip(client_ip, operation, "dos_rapid_requests")
                raise SecurityException("DoS pattern detected: rapid successive requests")
            
            # Pattern 2: Unusual request patterns (if we have request data)
            request_data = request_context.get('request_data', {})
            if isinstance(request_data, dict):
                # Check for suspicious patterns in license data
                license_data_str = json.dumps(request_data, default=str)
                for pattern in self._vulnerability_patterns:
                    if re.search(pattern, license_data_str, re.IGNORECASE):
                        await self.log_security_event('vulnerability_pattern_detected', {
                            'client_ip': client_ip,
                            'operation': operation,
                            'pattern': pattern,
                            'severity': 'medium'
                        })
                        self._metrics['security_violations'] += 1
            
        except SecurityException:
            raise
        except Exception as e:
            self.logger.warning(f"DoS pattern detection error: {str(e)}")
    
    async def validate_email_security(self, email: str) -> Dict[str, Any]:
        """Validate email for security issues"""
        try:
            issues = []
            
            # Check for test/demo patterns
            for pattern in self._vulnerability_patterns:
                if re.search(pattern, email, re.IGNORECASE):
                    issues.append(f"Suspicious email pattern detected: {pattern}")
            
            # Basic email validation
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                issues.append("Invalid email format")
            
            # Domain validation (could be enhanced with reputation checking)
            domain = email.split('@')[1] if '@' in email else ''
            if domain.lower() in ['test.com', 'example.com', 'fake.com', 'demo.com']:
                issues.append("Suspicious domain detected")
            
            await self.log_security_event('email_security_validation', {
                'email_domain': domain,
                'issues_found': len(issues),
                'valid': len(issues) == 0
            })
            
            return {
                'valid': len(issues) == 0,
                'issues': issues,
                'risk_level': 'high' if len(issues) > 2 else ('medium' if len(issues) > 0 else 'low')
            }
            
        except Exception as e:
            return {
                'valid': False,
                'issues': [f"Email validation error: {str(e)}"],
                'risk_level': 'high'
            }
    
    async def log_security_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log security events to audit trail"""
        try:
            timestamp = datetime.now().isoformat()
            audit_entry = {
                'timestamp': timestamp,
                'event_type': event_type,
                'component': 'license_security_middleware',
                'data': event_data
            }
            
            # Store in memory for recent access
            self._security_events.append(audit_entry)
            # Keep only last 1000 events in memory
            if len(self._security_events) > 1000:
                self._security_events = self._security_events[-1000:]
            
            # Write to audit file
            with open(self._audit_file, 'a') as f:
                f.write(json.dumps(audit_entry) + '\n')
            
            self._metrics['audit_events'] += 1
            
        except Exception as e:
            self.logger.error(f"Security event logging error: {str(e)}")
    
    async def get_security_audit(self, audit_type: str, time_range_hours: int) -> Dict[str, Any]:
        """Retrieve security audit data"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
            
            if audit_type == "recent":
                # Return recent in-memory events
                recent_events = [
                    event for event in self._security_events
                    if datetime.fromisoformat(event['timestamp']) > cutoff_time
                ]
                return {
                    'events': recent_events,
                    'events_count': len(recent_events),
                    'time_range_hours': time_range_hours
                }
            
            elif audit_type == "violations":
                # Filter security violations
                violation_events = [
                    event for event in self._security_events
                    if 'violation' in event['event_type'] or 'blocked' in event['event_type']
                    and datetime.fromisoformat(event['timestamp']) > cutoff_time
                ]
                return {
                    'events': violation_events,
                    'events_count': len(violation_events),
                    'violation_types': list(set(e['event_type'] for e in violation_events))
                }
            
            elif audit_type == "metrics":
                # Return current metrics
                return {
                    'metrics': self._metrics,
                    'active_blocks': len(self._blocked_ips),
                    'rate_limit_tracking': len(self._rate_limits)
                }
            
            else:
                # Default: all events in time range
                filtered_events = [
                    event for event in self._security_events
                    if datetime.fromisoformat(event['timestamp']) > cutoff_time
                ]
                return {
                    'events': filtered_events,
                    'events_count': len(filtered_events),
                    'time_range_hours': time_range_hours
                }
            
        except Exception as e:
            return {
                'events': [],
                'events_count': 0,
                'error': str(e)
            }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get current security metrics"""
        return {
            **self._metrics,
            'active_ip_blocks': len(self._blocked_ips),
            'tracked_ips': len(self._rate_limits),
            'avg_requests_per_ip': sum(len(reqs) for reqs in self._rate_limits.values()) / len(self._rate_limits) if self._rate_limits else 0,
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get middleware status"""
        try:
            return {
                'healthy': True,
                'component': 'license_security_middleware',
                'rate_limiting_active': True,
                'dos_protection_active': True,
                'audit_logging_active': True,
                'metrics': await self.get_metrics()
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }


class SecurityException(Exception):
    """Custom exception for security-related errors"""
    pass