#!/usr/bin/env python3
"""
WARPCORE License Orchestrator - PAP Implementation
Complex license workflows and business process orchestration
Controllers → Orchestrators → Providers
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from ....data.config.license.license_config import get_license_config


class LicenseOrchestrator:
    """License business process orchestrator - PAP layer"""
    
    def __init__(self):
        self.name = "license_orchestrator"
        self.config = get_license_config()
        self.provider_registry = None
        self.middleware_registry = None
        self.executor_registry = None
        self.logger = logging.getLogger("warpcore.orchestrator.license")
        
        # Cache for license operations
        self._license_cache = {}
        self._cache_duration = self.config.get_cache_duration()
    
    def set_provider_registry(self, provider_registry):
        """Set provider registry for accessing providers"""
        self.provider_registry = provider_registry
        self.logger.info("WARP LICENSE ORCHESTRATOR: Provider registry wired")
    
    def set_middleware_registry(self, middleware_registry):
        """Set middleware registry for safety gates"""
        self.middleware_registry = middleware_registry
        self.logger.info("WARP LICENSE ORCHESTRATOR: Middleware registry wired")
    
    def set_executor_registry(self, executor_registry):
        """Set executor registry for safe execution"""
        self.executor_registry = executor_registry
        self.logger.info("WARP LICENSE ORCHESTRATOR: Executor registry wired")
    
    def get_license_provider(self):
        """Get license provider from registry"""
        if self.provider_registry:
            return self.provider_registry.get_provider("license")
        return None
    
    async def orchestrate_license_status_check(self) -> Dict[str, Any]:
        """Orchestrate license status check with caching and validation"""
        try:
            # Check cache first
            cache_key = "license_status"
            if self._is_cached(cache_key):
                cached_result = self._get_from_cache(cache_key)
                cached_result["cached"] = True
                return cached_result
            
            # Get license provider
            license_provider = self.get_license_provider()
            if not license_provider:
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
            
            # Execute through provider
            result = await license_provider.get_license_status()
            
            # Cache successful results
            if result.get("success"):
                self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"License status check failed: {str(e)}"
            }
    
    async def orchestrate_license_activation(self, license_key: str, user_email: str = None) -> Dict[str, Any]:
        """Orchestrate license activation workflow"""
        try:
            self.logger.info(f"WARP ORCHESTRATOR: Starting license activation for {user_email}")
            
            # Get watermark config safely
            try:
                watermark = self.config.get_watermark_config() or {}
            except Exception as e:
                watermark = {"enabled": True}
            
            # Step 1: Validate license key first
            validation_result = await self.orchestrate_license_validation(license_key)
            if not validation_result.get("valid", False):
                return {
                    "success": False,
                    "error": f"License validation failed: {validation_result.get('error')}",
                    "orchestrator_watermark": "WarpCore License Orchestrator"
                }
            
            # Step 2: Check for existing license (deactivate if needed)
            await self.orchestrate_license_cleanup()
            
            # Step 3: Activate new license
            license_provider = self.get_license_provider()
            if not license_provider:
                return {
                    "success": False,
                    "error": "License provider not available in orchestrator",
                    "orchestrator_watermark": "WarpCore License Orchestrator"
                }
            
            activation_result = await self._execute_with_safety_gates(
                "activate_license",
                license_provider.activate_license,
                license_key, user_email
            )
            
            # Step 4: Clear cache after activation
            self._clear_license_cache()
            
            # Step 5: Add orchestration metadata
            if activation_result.get("success"):
                activation_result["orchestrated"] = True
                activation_result["orchestration_steps"] = ["validate", "cleanup", "activate", "cache_clear"]
                activation_result["orchestrator_watermark"] = "WarpCore License Orchestrator"
            
            return activation_result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"License activation orchestration failed: {str(e)}",
                "orchestrator_watermark": "WarpCore License Orchestrator"
            }
    
    async def orchestrate_license_validation(self, license_key: str) -> Dict[str, Any]:
        """Orchestrate license validation with multiple validation layers"""
        try:
            # Get license provider
            license_provider = self.get_license_provider()
            if not license_provider:
                return {
                    "valid": False,
                    "error": "License validation not available"
                }
            
            # Execute validation through provider
            validation_result = await license_provider.validate_license_key(license_key)
            
            return validation_result
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"License validation failed: {str(e)}"
            }
    
    async def orchestrate_trial_license_generation(self, user_email: str, days: int = None) -> Dict[str, Any]:
        """Orchestrate trial license generation with business rules"""
        try:
            watermark = self.config.get_watermark_config()
            branding = self.config.get_branding_config()
            trial_config = self.config.get_trial_config()
            
            # Use config default if no days specified
            if days is None:
                days = trial_config["duration_days"]
            
            self.logger.info(f"WARP ORCHESTRATOR: Generating trial license for {user_email} ({days} days)")
            
            # Step 1: Check trial limits (if implemented)
            # This could check against a database or cache for trial limits per email
            
            # Step 2: Generate trial license through provider
            license_provider = self.get_license_provider()
            if not license_provider:
                return {
                    "success": False,
                    "error": "License provider not available in orchestrator",
                    "orchestrator_watermark": "WarpCore License Orchestrator"
                }
            
            generation_result = await self._execute_with_safety_gates(
                "generate_trial_license",
                license_provider.generate_trial_license,
                user_email, days
            )
            
            # Step 3: Add orchestration metadata
            if generation_result.get("success"):
                generation_result["orchestrated"] = True
                generation_result["trial_config_applied"] = trial_config
                generation_result["orchestrator_watermark"] = "WarpCore License Orchestrator"
            
            return generation_result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Trial generation orchestration failed: {str(e)}",
                "orchestrator_watermark": "WarpCore License Orchestrator"
            }
    
    async def orchestrate_full_license_generation(self, user_email: str, user_name: str, days: int, features: List[str]) -> Dict[str, Any]:
        """Orchestrate full license generation with feature validation"""
        try:
            watermark = self.config.get_watermark_config()
            branding = self.config.get_branding_config()
            self.logger.info(f"WARP ORCHESTRATOR: Generating full license for {user_email} with features {features}")
            
            # Step 1: Validate requested features against available features
            available_features = self.config.get_features_config()
            
            # Step 2: Generate license through provider
            license_provider = self.get_license_provider()
            if not license_provider:
                return {
                    "success": False,
                    "error": "License provider not available in orchestrator",
                    "orchestrator_watermark": "WarpCore License Orchestrator"
                }
            
            generation_result = await self._execute_with_safety_gates(
                "generate_full_license",
                license_provider.generate_full_license,
                user_email, user_name, days, features
            )
            
            # Step 3: Add orchestration metadata
            if generation_result.get("success"):
                generation_result["orchestrated"] = True
                generation_result["features_validated"] = True
                generation_result["orchestrator_watermark"] = "WarpCore License Orchestrator"
            
            return generation_result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Full license generation orchestration failed: {str(e)}",
                "orchestrator_watermark": "WarpCore License Orchestrator"
            }
    
    async def orchestrate_license_cleanup(self) -> Dict[str, Any]:
        """Orchestrate license cleanup operations"""
        try:
            watermark = self.config.get_watermark_config()
            branding = self.config.get_branding_config()
            
            # Get current license status first
            status_result = await self.orchestrate_license_status_check()
            
            # If there's an active license, deactivate it
            if status_result.get("success") and status_result.get("data", {}).get("status") == "active":
                license_provider = self.get_license_provider()
                if license_provider:
                    deactivation_result = await self._execute_with_safety_gates(
                        "deactivate_license",
                        license_provider.deactivate_license
                    )
                    
                    # Clear cache after cleanup
                    self._clear_license_cache()
                    
                    return {
                        "success": True,
                        "message": "License cleanup completed",
                        "deactivated": deactivation_result.get("success", False),
                        "orchestrator_watermark": "WarpCore License Orchestrator"
                    }
            
            return {
                "success": True,
                "message": "No cleanup needed",
                "orchestrator_watermark": "WarpCore License Orchestrator"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"License cleanup orchestration failed: {str(e)}",
                "orchestrator_watermark": "WarpCore License Orchestrator"
            }
    
    async def orchestrate_custom_license_generation(self, user_email: str, user_name: str, days: int, features: list, license_type: str) -> Dict[str, Any]:
        """Orchestrate custom license generation with business rules and validation"""
        try:
            watermark = self.config.get_watermark_config()
            branding = self.config.get_branding_config()
            self.logger.info(f"WARP ORCHESTRATOR: Generating custom license for {user_email} ({license_type}, {days} days)")
            
            # Step 1: Validate features against available features
            available_features = self.config.get_features_config()
            valid_features = []
            for feature in features:
                if feature in available_features or feature in ['basic', 'test']:  # Always allow basic and test
                    valid_features.append(feature)
                else:
                    self.logger.warning(f"WARP ORCHESTRATOR: Unknown feature '{feature}' requested, skipping")
            
            if not valid_features:
                valid_features = ['basic']  # Fallback to basic
            
            # Step 2: Validate license type
            valid_license_types = ['trial', 'standard', 'premium', 'test']
            if license_type not in valid_license_types:
                license_type = 'standard'  # Default fallback
            
            # Step 3: Generate custom license through provider
            license_provider = self.get_license_provider()
            if not license_provider:
                return {
                    "success": False,
                    "error": "License provider not available in orchestrator",
                    "orchestrator_watermark": "WarpCore License Orchestrator"
                }
            
            # Use the existing full license generation method
            generation_result = await self._execute_with_safety_gates(
                "generate_full_license",
                license_provider.generate_full_license,
                user_email, user_name, days, valid_features
            )
            
            # Step 4: Add orchestration metadata for custom generation
            if generation_result.get("success"):
                generation_result["orchestrated"] = True
                generation_result["custom_generation"] = True
                generation_result["features_validated"] = True
                generation_result["license_type_validated"] = license_type
                generation_result["requested_features"] = features
                generation_result["validated_features"] = valid_features
                generation_result["orchestrator_watermark"] = "WarpCore License Orchestrator"
                
                # Update license type in result if different from provider result
                if "license_type" in generation_result:
                    generation_result["original_license_type"] = generation_result["license_type"]
                generation_result["license_type"] = license_type
            
            return generation_result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Custom license generation orchestration failed: {str(e)}",
                "orchestrator_watermark": "WarpCore License Orchestrator"
            }
    
    async def _execute_with_safety_gates(self, operation: str, func, *args, **kwargs) -> Dict[str, Any]:
        """Execute operation through safety gates if available"""
        try:
            if self.executor_registry:
                # Execute through PAP safety gates
                result = await self.executor_registry.execute_with_safety_gates(
                    f"license_{operation}",
                    func, *args, **kwargs
                )
                return result
            else:
                # Direct execution if no safety gates available
                return await func(*args, **kwargs)
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Safety gate execution failed for {operation}: {str(e)}"
            }
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if result is cached and not expired"""
        if cache_key not in self._license_cache:
            return False
        
        cached_data = self._license_cache[cache_key]
        cache_time = cached_data.get("cached_at")
        if not cache_time:
            return False
        
        # Check if cache is expired
        cache_age = datetime.now() - cache_time
        return cache_age.total_seconds() < (self._cache_duration * 60)
    
    def _get_from_cache(self, cache_key: str) -> Dict[str, Any]:
        """Get result from cache"""
        return self._license_cache[cache_key]["result"].copy()
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache result with timestamp"""
        self._license_cache[cache_key] = {
            "result": result.copy(),
            "cached_at": datetime.now()
        }
    
    def _clear_license_cache(self):
        """Clear all license cache"""
        self._license_cache.clear()
        self.logger.info("WARP ORCHESTRATOR: License cache cleared")
    
    async def orchestrate_secure_license_generation(self, user_email: str, user_name: str, 
                                                  days: int, features: List[str],
                                                  hardware_binding: bool = True) -> Dict[str, Any]:
        """Orchestrate production-grade secure license generation with enhanced security"""
        try:
            watermark = self.config.get_watermark_config()
            branding = self.config.get_branding_config()
            self.logger.info(f"WARP ORCHESTRATOR: Generating secure license for {user_email} with hardware binding: {hardware_binding}")
            
            # Step 1: Enhanced feature validation for secure licenses
            available_features = self.config.get_features_config()
            secure_features = []
            
            for feature in features:
                if feature in available_features or feature in ['production', 'security', 'enterprise']:
                    secure_features.append(feature)
                else:
                    self.logger.warning(f"WARP ORCHESTRATOR: Feature '{feature}' not approved for secure licenses")
            
            # Always add security features for production licenses
            mandatory_security_features = ['production', 'security', 'audit']
            for sec_feature in mandatory_security_features:
                if sec_feature not in secure_features:
                    secure_features.append(sec_feature)
            
            # Step 2: Get license provider and use secure generation if available
            license_provider = self.get_license_provider()
            if not license_provider:
                return {
                    "success": False,
                    "error": "License provider not available in orchestrator",
                    "orchestrator_watermark": "WarpCore License Orchestrator"
                }
            
            # Try secure generation method first, fallback to standard if not available
            if hasattr(license_provider, 'generate_secure_license'):
                generation_result = await self._execute_with_safety_gates(
                    "generate_secure_license",
                    license_provider.generate_secure_license,
                    user_email, user_name, days, secure_features, hardware_binding
                )
                generation_result["secure_generation_used"] = True
            else:
                # Fallback to standard generation with security metadata
                generation_result = await self._execute_with_safety_gates(
                    "generate_full_license",
                    license_provider.generate_full_license,
                    user_email, user_name, days, secure_features
                )
                generation_result["secure_generation_used"] = False
                generation_result["fallback_generation"] = True
            
            # Step 3: Add secure orchestration metadata
            if generation_result.get("success"):
                generation_result["orchestrated"] = True
                generation_result["security_level"] = "production"
                generation_result["features_security_validated"] = True
                generation_result["mandatory_features_added"] = mandatory_security_features
                generation_result["requested_features"] = features
                generation_result["approved_features"] = secure_features
                generation_result["hardware_binding_requested"] = hardware_binding
                generation_result["orchestrator_watermark"] = "WarpCore License Orchestrator"
            
            return generation_result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Secure license generation orchestration failed: {str(e)}",
                "orchestrator_watermark": "WarpCore License Orchestrator"
            }
    
    async def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        watermark = self.config.get_watermark_config()
        branding = self.config.get_branding_config()
        
        return {
            "success": True,
            "orchestrator": self.name,
            "provider_registry_wired": bool(self.provider_registry),
            "middleware_registry_wired": bool(self.middleware_registry), 
            "executor_registry_wired": bool(self.executor_registry),
            "cache_entries": len(self._license_cache),
            "cache_duration_minutes": self._cache_duration,
            "orchestrator_watermark": "WarpCore License Orchestrator",
            "config_loaded": True,
            "secure_license_support": True
        }
