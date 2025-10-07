#!/usr/bin/env python3
"""
WARPCORE License Configuration - Data Layer
Provides all licensing configuration for the PAP stack
All licensing components get config from here - no hardcoded values
"""

import os
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List
from ...config_loader import get_config


class LicenseConfig:
    """License configuration management - Data layer for PAP"""
    
    def __init__(self):
        self.base_config = get_config()
        self._license_config = None
        self._load_license_config()
    
    def _load_license_config(self):
        """Load license-specific configuration from WARPCORE config"""
        # Load from main WARPCORE config sections
        self._license_config = {
            "licensing": self.base_config.get_section('licensing', {}),
            "license_security": self.base_config.get_section('license_security', {}),
            "license_features": self.base_config.get_section('license_features', {}),
            "license_validation": self.base_config.get_section('license_validation', {}),
            "logging": self.base_config.get_section('logging', {}),
            "security": self.base_config.get_section('security', {}),
            "compliance": self.base_config.get_section('compliance', {})
        }
    
    def _get_warp_demo_defaults(self) -> Dict[str, Any]:
        """WARP demo defaults with proper watermarking"""
        return {
            "license": {
                "provider": {
                    "encryption_key": base64.urlsafe_b64encode(b"warpcore_license_key_32_chars_!!").decode(),
                    "keychain_service": "warpcore-license",
                    "keychain_account": "WARPCORE",
                    "demo_mode": True,
                    "watermark": "WARP FAKE SUB TEST DEMO"
                },
                "orchestrator": {
                    "trial_duration_days": 7,
                    "default_features": ["basic", "test"],
                    "max_trial_per_email": 3,
                    "auto_cleanup_expired": True,
                    "watermark": "WARP DEMO ORCHESTRATOR"
                },
                "controller": {
                    "broadcast_events": True,
                    "cache_duration_minutes": 15,
                    "validate_on_startup": True,
                    "watermark": "WARP DEMO CONTROLLER"
                },
                "routes": {
                    "rate_limit_per_minute": 60,
                    "require_auth": False,
                    "background_tasks": True,
                    "watermark": "WARP DEMO ROUTES"
                },
                "features": {
                    "basic": ["license_status", "validate"],
                    "standard": ["license_status", "validate", "activate", "deactivate"],
                    "premium": ["license_status", "validate", "activate", "deactivate", "generate_trial", "generate_full"],
                    "test": ["all_features", "watermark_testing"]
                },
                "demo_data": {
                    "test_users": [
                        {
                            "email": "warp-demo-user@warp-fake-sub-test-demo.com",
                            "name": "WARP Demo User",
                            "license_type": "test",
                            "features": ["basic", "test"]
                        },
                        {
                            "email": "warp-trial@warp-fake-sub-test-demo.com", 
                            "name": "WARP Trial User",
                            "license_type": "trial",
                            "features": ["basic"]
                        }
                    ],
                    "watermark": "WARP FAKE SUB TEST DEMO WATER"
                }
            }
        }
    
    def get_provider_config(self) -> Dict[str, Any]:
        """Get provider configuration from licensing section"""
        licensing = self._license_config.get("licensing", {})
        security = self._license_config.get("license_security", {})
        return {
            "encryption_enabled": licensing.get("encryption_enabled", True),
            "hardware_binding": licensing.get("hardware_binding", True),
            "production_mode": licensing.get("production_mode", True),
            "audit_all_operations": licensing.get("audit_all_operations", True),
            "fernet_encryption": security.get("fernet_encryption", True),
            "hardware_fingerprinting": security.get("hardware_fingerprinting", True),
            "tamper_detection": security.get("tamper_detection", True),
            "security_level": security.get("security_level", "production")
        }
    
    def get_orchestrator_config(self) -> Dict[str, Any]:
        """Get orchestrator configuration"""
        return self._license_config.get("license", {}).get("orchestrator", {})
    
    def get_controller_config(self) -> Dict[str, Any]:
        """Get controller configuration"""
        return self._license_config.get("license", {}).get("controller", {})
    
    def get_routes_config(self) -> Dict[str, Any]:
        """Get routes configuration"""
        return self._license_config.get("license", {}).get("routes", {})
    
    def get_features_config(self) -> Dict[str, Any]:
        """Get features configuration"""
        return self._license_config.get("license", {}).get("features", {})
    
    def get_demo_data(self) -> Dict[str, Any]:
        """Get demo data for testing"""
        return self._license_config.get("license", {}).get("demo_data", {})
    
    def get_encryption_key(self) -> str:
        """Get encryption key for license operations"""
        return self.get_provider_config().get("encryption_key", "")
    
    def get_keychain_config(self) -> Dict[str, str]:
        """Get keychain configuration"""
        provider_config = self.get_provider_config()
        return {
            "service": provider_config.get("keychain_service", "warpcore-license"),
            "account": provider_config.get("keychain_account", "WARPCORE")
        }
    
    def is_demo_mode(self) -> bool:
        """Check if running in demo mode"""
        return self.get_provider_config().get("demo_mode", True)
    
    def get_trial_config(self) -> Dict[str, Any]:
        """Get trial license configuration from WARPCORE config"""
        licensing = self._license_config.get("licensing", {})
        return {
            "duration_days": licensing.get("trial_duration_days", 7),
            "max_duration_days": licensing.get("max_trial_duration_days", 30),
            "default_features": ["basic"]
        }
    
    def get_feature_list(self, license_type: str) -> List[str]:
        """Get features for a license type from WARPCORE config"""
        features_config = self._license_config.get("license_features", {})
        return features_config.get(license_type, ["core", "api"])
    
    def get_watermark_config(self) -> Dict[str, str]:
        """Get watermarking configuration (disabled for production)"""
        return {
            "provider": "",
            "orchestrator": "", 
            "controller": "",
            "routes": "",
            "main": "",
            "error": ""
        }
    
    def get_security_features(self) -> List[str]:
        """Get approved security features"""
        security = self._license_config.get("license_security", {})
        return security.get("production_features", ["production", "security", "audit", "enterprise"])
    
    def get_required_security_features(self) -> List[str]:
        """Get required security features for production licenses"""
        security = self._license_config.get("license_security", {})
        return security.get("required_security_features", ["production", "security"])
    
    def get_validation_config(self) -> Dict[str, Any]:
        """Get license validation configuration"""
        return self._license_config.get("license_validation", {})
    
    def get_max_license_duration(self) -> int:
        """Get maximum license duration in days"""
        licensing = self._license_config.get("licensing", {})
        return licensing.get("max_license_duration_days", 365)
    
    def get_key_rotation_days(self) -> int:
        """Get key rotation period in days"""
        licensing = self._license_config.get("licensing", {})
        return licensing.get("key_rotation_days", 90)
    
    def get_audit_file(self) -> str:
        """Get audit log file path"""
        logging = self._license_config.get("logging", {})
        return logging.get("audit_file", "/tmp/warpcore_audit.log")
    
    def is_production_mode(self) -> bool:
        """Check if running in production mode"""
        licensing = self._license_config.get("licensing", {})
        return licensing.get("production_mode", True)
    
    def get_trial_duration(self) -> int:
        """Get default trial duration in days"""
        licensing = self._license_config.get("licensing", {})
        return licensing.get("trial_duration_days", 7)
    
    def get_max_trial_duration(self) -> int:
        """Get maximum trial duration in days"""
        licensing = self._license_config.get("licensing", {})
        return licensing.get("max_trial_duration_days", 30)
    
    def get_available_features(self) -> List[str]:
        """Get all available features"""
        features = self._license_config.get("license_features", {})
        all_features = set()
        for feature_list in features.values():
            if isinstance(feature_list, list):
                all_features.update(feature_list)
        return list(all_features)
    
    def get_license_type_config(self, license_type: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific license type"""
        features = self._license_config.get("license_features", {})
        if license_type not in features:
            return None
        
        max_days = self.get_max_license_duration()
        allowed_features = features.get(license_type, [])
        
        return {
            "max_days": max_days,
            "allowed_features": allowed_features
        }
    
    def should_broadcast_events(self) -> bool:
        """Check if events should be broadcasted"""
        return self.get_controller_config().get("broadcast_events", True)
    
    def get_cache_duration(self) -> int:
        """Get cache duration in minutes"""
        return self.get_controller_config().get("cache_duration_minutes", 15)
    
    def get_rate_limit(self) -> int:
        """Get rate limit per minute"""
        return self.get_routes_config().get("rate_limit_per_minute", 60)
    
    def should_use_background_tasks(self) -> bool:
        """Check if background tasks should be used"""
        return self.get_routes_config().get("background_tasks", True)
    
    def reload_config(self):
        """Reload configuration from data layer"""
        self.base_config.reload()
        self._load_license_config()


# Global license config instance
_license_config = None


def get_license_config() -> LicenseConfig:
    """Get global license configuration instance"""
    global _license_config
    if _license_config is None:
        _license_config = LicenseConfig()
    return _license_config


def reload_license_config():
    """Reload license configuration"""
    global _license_config
    _license_config = None
    return get_license_config()