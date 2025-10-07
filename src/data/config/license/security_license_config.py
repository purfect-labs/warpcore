#!/usr/bin/env python3
"""
WARPCORE Security License Configuration - Enhanced Security Layer
Extends base license configuration with advanced security features
WARP-DEMO-SECURITY watermarking enabled for test configurations
"""

import os
import json
import base64
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from cryptography.fernet import Fernet
from ...config_loader import get_config
from .license_config import LicenseConfig


class SecurityLicenseConfig(LicenseConfig):
    """Enhanced security configuration for licensing system - PAP compliant"""
    
    def __init__(self):
        super().__init__()
        self._security_config = None
        self._fernet_key = None
        self._hardware_binding_enabled = True
        self._monitoring_enabled = True
        self._load_security_config()
    
    def _load_security_config(self):
        """Load security-specific configuration from WARPCORE config"""
        # Load enhanced security sections
        self._security_config = {
            "security_licensing": self.base_config.get_section('security_licensing', {}),
            "fernet_encryption": self.base_config.get_section('fernet_encryption', {}),
            "hardware_binding": self.base_config.get_section('hardware_binding', {}),
            "security_monitoring": self.base_config.get_section('security_monitoring', {}),
            "security_analytics": self.base_config.get_section('security_analytics', {}),
            "key_rotation": self.base_config.get_section('key_rotation', {}),
            "environment_policies": self.base_config.get_section('environment_policies', {})
        }
    
    def _get_warp_demo_security_defaults(self) -> Dict[str, Any]:
        """WARP-DEMO-SECURITY defaults with proper watermarking for test mode"""
        return {
            "security_licensing": {
                "production_mode": False,
                "demo_mode": True,
                "watermark": "WARP-DEMO-SECURITY",
                "test_encryption_key": self._generate_test_fernet_key(),
                "test_hardware_id": "WARP-DEMO-HARDWARE-12345",
                "audit_level": "test",
                "security_level": "demo"
            },
            "fernet_encryption": {
                "enabled": True,
                "key_rotation_enabled": True,
                "key_rotation_days": 1,  # Fast rotation for testing
                "test_mode_key": self._generate_test_fernet_key(),
                "watermark": "WARP-DEMO-FERNET"
            },
            "hardware_binding": {
                "enabled": True,
                "strict_mode": False,  # Relaxed for testing
                "test_fingerprint": "WARP-DEMO-FINGERPRINT-ABCD",
                "allow_vm": True,
                "watermark": "WARP-DEMO-HARDWARE"
            },
            "security_monitoring": {
                "enabled": True,
                "analytics_enabled": True,
                "real_time_alerts": False,  # Disabled for testing
                "test_data_prefix": "WARP-DEMO-MONITOR",
                "watermark": "WARP-DEMO-MONITORING"
            }
        }
    
    def _generate_test_fernet_key(self) -> str:
        """Generate test Fernet key for WARP-DEMO-SECURITY mode"""
        # Use deterministic key for testing consistency
        test_seed = "warpcore_demo_security_test_key_32_chars_exactly"
        key_bytes = hashlib.sha256(test_seed.encode()).digest()[:32]
        return base64.urlsafe_b64encode(key_bytes).decode()
    
    def get_fernet_encryption_config(self) -> Dict[str, Any]:
        """Get Fernet encryption configuration with key rotation support"""
        fernet_config = self._security_config.get("fernet_encryption", {})
        defaults = self._get_warp_demo_security_defaults()["fernet_encryption"]
        
        return {
            "enabled": fernet_config.get("enabled", defaults["enabled"]),
            "key_rotation_enabled": fernet_config.get("key_rotation_enabled", defaults["key_rotation_enabled"]),
            "key_rotation_days": fernet_config.get("key_rotation_days", defaults["key_rotation_days"]),
            "current_key": fernet_config.get("current_key", defaults["test_mode_key"]),
            "previous_keys": fernet_config.get("previous_keys", []),
            "max_key_history": fernet_config.get("max_key_history", 5),
            "watermark": defaults["watermark"] if self.is_test_mode() else ""
        }
    
    def get_hardware_binding_config(self) -> Dict[str, Any]:
        """Get hardware binding configuration settings"""
        hardware_config = self._security_config.get("hardware_binding", {})
        defaults = self._get_warp_demo_security_defaults()["hardware_binding"]
        
        return {
            "enabled": hardware_config.get("enabled", defaults["enabled"]),
            "strict_mode": hardware_config.get("strict_mode", defaults["strict_mode"]),
            "fingerprint_methods": hardware_config.get("fingerprint_methods", ["cpu", "mac", "disk"]),
            "allow_vm": hardware_config.get("allow_vm", defaults["allow_vm"]),
            "tolerance_threshold": hardware_config.get("tolerance_threshold", 0.8),
            "test_fingerprint": defaults["test_fingerprint"] if self.is_test_mode() else None,
            "watermark": defaults["watermark"] if self.is_test_mode() else ""
        }
    
    def get_monitoring_analytics_config(self) -> Dict[str, Any]:
        """Get monitoring and analytics configuration"""
        monitoring_config = self._security_config.get("security_monitoring", {})
        defaults = self._get_warp_demo_security_defaults()["security_monitoring"]
        
        return {
            "enabled": monitoring_config.get("enabled", defaults["enabled"]),
            "analytics_enabled": monitoring_config.get("analytics_enabled", defaults["analytics_enabled"]),
            "real_time_alerts": monitoring_config.get("real_time_alerts", defaults["real_time_alerts"]),
            "metrics_collection": monitoring_config.get("metrics_collection", True),
            "anomaly_detection": monitoring_config.get("anomaly_detection", True),
            "usage_tracking": monitoring_config.get("usage_tracking", True),
            "audit_trail": monitoring_config.get("audit_trail", True),
            "test_data_prefix": defaults["test_data_prefix"] if self.is_test_mode() else None,
            "watermark": defaults["watermark"] if self.is_test_mode() else ""
        }
    
    def is_test_mode(self) -> bool:
        """Check if running in test/demo mode for WARP-DEMO-SECURITY watermarking"""
        security_config = self._security_config.get("security_licensing", {})
        return security_config.get("demo_mode", not self.is_production_mode())
    
    def validate_security_configuration(self) -> Dict[str, Any]:
        """Validate current security configuration"""
        validation_results = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Check Fernet encryption
        try:
            fernet_config = self.get_fernet_encryption_config()
            if not fernet_config["enabled"]:
                validation_results["warnings"].append("Fernet encryption is disabled")
                
        except Exception as e:
            validation_results["issues"].append(f"Fernet configuration error: {str(e)}")
            validation_results["valid"] = False
        
        if self.is_test_mode():
            validation_results["warnings"].append("Running in WARP-DEMO-SECURITY test mode")
        
        return validation_results


# Global security license config instance
_security_license_config = None


def get_security_license_config() -> SecurityLicenseConfig:
    """Get global security license configuration instance"""
    global _security_license_config
    if _security_license_config is None:
        _security_license_config = SecurityLicenseConfig()
    return _security_license_config
