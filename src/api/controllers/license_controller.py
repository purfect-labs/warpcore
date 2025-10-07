#!/usr/bin/env python3
"""
WARPCORE License Controller - PAP Implementation  
Business logic controller for license management operations
Controllers → Orchestrators → Providers → Data Layer
"""

from typing import Dict, Any, Optional
from .base_controller import BaseController
from ..orchestrators.license.license_orchestrator import LicenseOrchestrator
from ...data.config.license.license_config import get_license_config


class LicenseController(BaseController):
    """Controller for license management operations - PAP compliant"""
    
    def __init__(self):
        super().__init__("license")
        self.config = get_license_config()
        self.orchestrator = LicenseOrchestrator()
        self._orchestrator_wired = False
    
    def set_provider_registry(self, provider_registry):
        """Set provider registry and wire orchestrator"""
        super().set_provider_registry(provider_registry)
        self.orchestrator.set_provider_registry(provider_registry)
        self._orchestrator_wired = True
        self.logger.info("WARP LICENSE CONTROLLER: Orchestrator wired with provider registry")
    
    def set_websocket_manager(self, websocket_manager):
        """Set WebSocket manager"""
        super().set_websocket_manager(websocket_manager)
        self.logger.info("WARP LICENSE CONTROLLER: WebSocket manager wired")
    
    def _wire_orchestrator_registries(self):
        """Wire orchestrator with middleware and executor registries if available"""
        # This would be called during startup if middleware/executor registries are available
        pass
    
    async def get_status(self) -> Dict[str, Any]:
        """Get controller status - PAP aligned with config from data layer"""
        watermark = self.config.get_watermark_config()
        
        return {
            "success": True,
            "controller": self.name,
            "orchestrator_wired": self._orchestrator_wired,
            "config_loaded": True,
            "demo_mode": self.config.is_demo_mode(),
            "broadcast_enabled": self.config.should_broadcast_events(),
            "cache_duration": self.config.get_cache_duration(),
            "watermark": watermark["controller"]
        }
    
    async def get_license_status(self) -> Dict[str, Any]:
        """Get detailed license information via orchestrator"""
        try:
            if not self._orchestrator_wired:
                return {
                    "success": True,
                    "data": {
                        "status": "no_license",
                        "license_type": None,
                        "user_name": None,
                        "user_email": None,
                        "expires": None,
                        "days_remaining": 0,
                        "features": []
                    }
                }
            
            # Use orchestrator for proper PAP flow
            result = await self.orchestrator.orchestrate_license_status_check()
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"License status check failed: {str(e)}"
            }
    
    async def validate_license_key(self, license_key: str) -> Dict[str, Any]:
        """Validate license key via orchestrator"""
        try:
            watermark = self.config.get_watermark_config()
            
            if not license_key:
                return {
                    "valid": False,
                    "error": "License key required",
                    "watermark": watermark["controller"]
                }
            
            if not self._orchestrator_wired:
                # Fallback validation when orchestrator not available
                return {
                    "valid": license_key.startswith("test-") or license_key.startswith("warp-"),
                    "license_type": "test",
                    "features": ["basic", "test"],
                    "watermark": watermark["controller"],
                    "orchestrator_available": False
                }
            
            # Use orchestrator for proper PAP validation
            result = await self.orchestrator.orchestrate_license_validation(license_key)
            
            # Add controller processing metadata
            if isinstance(result, dict):
                result["controller_processed"] = True
                result["pap_flow_completed"] = True
            
            # Broadcast validation event if configured
            if self.config.should_broadcast_events():
                await self.broadcast_message({
                    "type": "license_validated", 
                    "data": {
                        "controller": self.name,
                        "valid": result.get("valid", False),
                        "license_type": result.get("license_type"),
                        "watermark": watermark["controller"]
                    }
                })
            
            return result
            
        except Exception as e:
            watermark = self.config.get_watermark_config()
            return {
                "valid": False,
                "error": f"Controller license validation failed: {str(e)}",
                "watermark": watermark["error"]
            }
    
    async def activate_license(self, license_key: str, user_email: str = None) -> Dict[str, Any]:
        """Activate license via orchestrator"""
        try:
            watermark = self.config.get_watermark_config()
            
            if not self._orchestrator_wired:
                return {
                    "success": False,
                    "error": "License orchestrator not available",
                    "watermark": watermark["controller"]
                }
            
            # Use orchestrator for complex activation workflow
            result = await self.orchestrator.orchestrate_license_activation(license_key, user_email)
            
            # Add controller processing metadata
            if result.get("success"):
                result["controller_processed"] = True
                result["pap_flow_completed"] = True
            
            # Broadcast activation event if configured and successful
            if self.config.should_broadcast_events() and result.get("success"):
                await self.broadcast_message({
                    "type": "license_activated",
                    "data": {
                        "controller": self.name,
                        "user_email": user_email,
                        "license_type": result.get("license_type"),
                        "message": "License activated via PAP flow",
                        "watermark": watermark["controller"]
                    }
                })
            
            return result
            
        except Exception as e:
            watermark = self.config.get_watermark_config()
            return {
                "success": False,
                "error": f"Controller license activation failed: {str(e)}",
                "watermark": watermark["error"]
            }
    
    async def deactivate_license(self) -> Dict[str, Any]:
        """Deactivate license via orchestrator cleanup"""
        try:
            watermark = self.config.get_watermark_config()
            
            if not self._orchestrator_wired:
                return {
                    "success": False,
                    "error": "License orchestrator not available",
                    "watermark": watermark["controller"]
                }
            
            # Use orchestrator for cleanup workflow
            result = await self.orchestrator.orchestrate_license_cleanup()
            
            # Add controller processing metadata  
            if result.get("success"):
                result["controller_processed"] = True
                result["pap_flow_completed"] = True
            
            # Broadcast deactivation event if configured
            if self.config.should_broadcast_events() and result.get("success"):
                await self.broadcast_message({
                    "type": "license_deactivated",
                    "data": {
                        "controller": self.name,
                        "message": "License deactivated via PAP flow",
                        "watermark": watermark["controller"]
                    }
                })
            
            return result
            
        except Exception as e:
            watermark = self.config.get_watermark_config()
            return {
                "success": False,
                "error": f"Controller license deactivation failed: {str(e)}",
                "watermark": watermark["error"]
            }
    
    async def generate_trial_license(self, user_email: str, days: int = None) -> Dict[str, Any]:
        """Generate trial license via orchestrator"""
        try:
            watermark = self.config.get_watermark_config()
            
            if not self._orchestrator_wired:
                return {
                    "success": False,
                    "error": "License orchestrator not available",
                    "watermark": watermark["controller"]
                }
            
            # Use orchestrator for trial generation with business rules
            result = await self.orchestrator.orchestrate_trial_license_generation(user_email, days)
            
            # Add controller processing metadata
            if result.get("success"):
                result["controller_processed"] = True
                result["pap_flow_completed"] = True
            
            # Broadcast trial generation event if configured
            if self.config.should_broadcast_events() and result.get("success"):
                await self.broadcast_message({
                    "type": "trial_license_generated",
                    "data": {
                        "controller": self.name,
                        "user_email": user_email,
                        "days": result.get("days"),
                        "message": "Trial license generated via PAP flow",
                        "watermark": watermark["controller"]
                    }
                })
            
            return result
            
        except Exception as e:
            watermark = self.config.get_watermark_config()
            return {
                "success": False,
                "error": f"Controller trial generation failed: {str(e)}",
                "watermark": watermark["error"]
            }
    
    async def generate_full_license(self, user_email: str, user_name: str, days: int, features: list) -> Dict[str, Any]:
        """Generate full license via orchestrator"""
        try:
            watermark = self.config.get_watermark_config()
            
            if not self._orchestrator_wired:
                return {
                    "success": False,
                    "error": "License orchestrator not available", 
                    "watermark": watermark["controller"]
                }
            
            # Use orchestrator for full license generation with feature validation
            result = await self.orchestrator.orchestrate_full_license_generation(user_email, user_name, days, features)
            
            # Add controller processing metadata
            if result.get("success"):
                result["controller_processed"] = True
                result["pap_flow_completed"] = True
            
            # Broadcast full license generation event if configured
            if self.config.should_broadcast_events() and result.get("success"):
                await self.broadcast_message({
                    "type": "full_license_generated",
                    "data": {
                        "controller": self.name,
                        "user_email": user_email,
                        "user_name": user_name,
                        "days": days,
                        "features": features,
                        "message": "Full license generated via PAP flow",
                        "watermark": watermark["controller"]
                    }
                })
            
            return result
            
        except Exception as e:
            watermark = self.config.get_watermark_config()
            return {
                "success": False,
                "error": f"Controller full license generation failed: {str(e)}",
                "watermark": watermark["error"]
            }
    
    async def generate_custom_license_key(self, user_email: str, user_name: str = None, days: int = 365, features: list = None, license_type: str = "standard") -> Dict[str, Any]:
        """Generate custom license key with specified parameters via orchestrator"""
        try:
            # Set defaults from config if not provided
            if not user_name:
                user_name = user_email.split('@')[0].title()
            if not features:
                features = self.config.get_feature_list(license_type)
            
            if not self._orchestrator_wired:
                return {
                    "success": False,
                    "error": "License orchestrator not available"
                }
            
            # Use orchestrator for custom key generation
            result = await self.orchestrator.orchestrate_custom_license_generation(user_email, user_name, days, features, license_type)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_secure_license(self, user_email: str, user_name: str, days: int, features: list, hardware_binding: bool = True) -> Dict[str, Any]:
        """Generate production-grade secure license with hardware binding via orchestrator"""
        try:
            watermark = self.config.get_watermark_config()
            
            if not self._orchestrator_wired:
                return {
                    "success": False,
                    "error": "License orchestrator not available",
                    "watermark": watermark["controller"]
                }
            
            # Use orchestrator for secure license generation
            result = await self.orchestrator.orchestrate_secure_license_generation(
                user_email, user_name, days, features, hardware_binding
            )
            
            # Add controller processing metadata
            if result.get("success"):
                result["controller_processed"] = True
                result["pap_flow_completed"] = True
                result["security_level"] = "production"
            
            # Broadcast secure license generation event if configured
            if self.config.should_broadcast_events() and result.get("success"):
                await self.broadcast_message({
                    "type": "secure_license_generated",
                    "data": {
                        "controller": self.name,
                        "user_email": user_email,
                        "user_name": user_name,
                        "days": days,
                        "features_count": len(features),
                        "hardware_binding": hardware_binding,
                        "message": "Production secure license generated via PAP flow",
                        "watermark": watermark["controller"]
                    }
                })
            
            return result
            
        except Exception as e:
            watermark = self.config.get_watermark_config()
            return {
                "success": False,
                "error": f"Controller secure license generation failed: {str(e)}",
                "watermark": watermark["error"]
            }
    
    async def get_subscription_info(self) -> Dict[str, Any]:
        """Get subscription info - uses data layer config for demo data"""
        try:
            watermark = self.config.get_watermark_config()
            demo_data = self.config.get_demo_data()
            features_config = self.config.get_features_config()
            
            # For now, return demo subscription data from config
            return {
                "success": True,
                "data": {
                    "subscription_type": "WARP TEST SUBSCRIPTION",
                    "features_available": list(features_config.keys()),
                    "features_active": ["basic", "test"],
                    "billing_status": "demo",
                    "renewal_date": "2025-12-31",
                    "demo_users": len(demo_data.get("test_users", [])),
                    "watermark": watermark["controller"],
                    "controller_processed": True,
                    "config_driven": True
                }
            }
            
        except Exception as e:
            watermark = self.config.get_watermark_config()
            return {
                "success": False,
                "error": f"Controller subscription info failed: {str(e)}",
                "watermark": watermark["error"]
            }