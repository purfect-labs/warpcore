#!/usr/bin/env python3
"""
WARPCORE License Provider - APEX Implementation
Real working license operations from APEX system
Handles keychain access, license generation, and validation
"""

import json
import base64
import keyring
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from ..core.base_provider import BaseProvider

# Import native WARPCORE license manager (APEX-aligned)
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'native'))
    from warpcore_license import WARPCORELicenseManager
    NATIVE_LICENSE_AVAILABLE = True
except ImportError:
    WARPCORELicenseManager = None
    NATIVE_LICENSE_AVAILABLE = False


class LicenseProvider(BaseProvider):
    """WARPCORE License operations provider - APEX implementation with native integration"""
    
    def __init__(self):
        super().__init__("license")
        
        # Initialize native license manager if available
        if NATIVE_LICENSE_AVAILABLE:
            self._native_manager = WARPCORELicenseManager()
        else:
            self._native_manager = None
        
        # APEX-compatible encryption setup with WARP watermarking
        self._demo_key = base64.urlsafe_b64encode(b"warpcore_license_key_32_chars_!!").decode()
        self._fernet = Fernet(self._demo_key.encode())
        self._keychain_service = "warpcore-license"
        self._keychain_account = "WARPCORE"

    async def get_license_status(self) -> Dict[str, Any]:
        """Get current license status from native manager or keychain fallback"""
        try:
            # Try native status check first if available
            if self._native_manager:
                try:
                    license_info = self._native_manager.get_license_info()
                    if license_info and license_info.get("valid", False):
                        expires_str = license_info.get("expires")
                        days_remaining = None
                        
                        if expires_str:
                            try:
                                expires_date = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                                days_remaining = max(0, (expires_date - datetime.now()).days)
                            except:
                                pass
                        
                        return {
                            "success": True,
                            "status": "active",
                            "message": "License is active via native manager",
                            "user_email": license_info.get("user", "WARP-NATIVE-USER"),
                            "user_name": license_info.get("user", "WARP User"),
                            "expires": expires_str,
                            "features": license_info.get("features", []),
                            "license_type": license_info.get("license_type", "basic"),
                            "days_remaining": days_remaining,
                            "source": "NATIVE_WARPCORE_MANAGER"
                        }
                except Exception as native_error:
                    self.logger.warning(f"Native license status check failed: {native_error}")
            
            # Fallback to keychain stored license - Get stored license from keychain
            stored_license = keyring.get_password(self._keychain_service, self._keychain_account)
            
            if not stored_license:
                return {
                    "success": True,
                    "status": "inactive",
                    "message": "No license found - WARP FAKE SUB TEST DEMO",
                    "user_email": None,
                    "expires": None,
                    "features": [],
                    "license_type": None,
                    "days_remaining": None,
                    "source": "WARP FAKE SUB TEST DEMO KEYCHAIN"
                }
            
            # Validate and decode license
            license_data = await self._validate_license_key(stored_license)
            
            if not license_data.get("valid", False):
                # License is invalid, clear it
                await self.deactivate_license()
                return {
                    "success": True,
                    "status": "invalid",
                    "message": license_data.get("error", "License validation failed - WARP FAKE SUB TEST"),
                    "user_email": None,
                    "expires": None,
                    "features": [],
                    "license_type": None,
                    "days_remaining": None,
                    "source": "WARP FAKE SUB TEST DEMO KEYCHAIN"
                }
            
            # Return active license status
            license_info = license_data["license_info"]
            expires_str = license_info.get("expires")
            days_remaining = None
            
            if expires_str:
                try:
                    expires_date = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                    days_remaining = max(0, (expires_date - datetime.now()).days)
                except:
                    pass
            
            return {
                "success": True,
                "status": "active",
                "message": "License is active via keychain fallback",
                "user_email": license_info.get("user_email"),
                "user_name": license_info.get("user_name"),
                "expires": expires_str,
                "features": license_info.get("features", []),
                "license_type": license_info.get("license_type", "standard"),
                "days_remaining": days_remaining,
                "source": "WARP FAKE SUB TEST DEMO KEYCHAIN"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get license status: {str(e)}",
                "status": "error"
            }

    async def activate_license(self, license_key: str, user_email: str = None) -> Dict[str, Any]:
        """Activate a license key with native manager or keychain fallback"""
        try:
            # Try native activation first if available
            if self._native_manager:
                try:
                    success = self._native_manager.activate_license(license_key, user_email or "WARP-USER")
                    if success:
                        license_info = self._native_manager.get_license_info()
                        return {
                            "success": True,
                            "message": "License activated successfully via native manager",
                            "user_email": license_info.get("user", user_email),
                            "user_name": license_info.get("user", "WARP User"),
                            "expires": license_info.get("expires"),
                            "features": license_info.get("features", []),
                            "license_type": license_info.get("license_type", "standard"),
                            "source": "NATIVE_WARPCORE_MANAGER"
                        }
                except Exception as native_error:
                    self.logger.warning(f"Native license activation failed: {native_error}")
            
            # Fallback to encrypted validation and keychain storage
            validation_result = await self._validate_license_key(license_key)
            
            if not validation_result.get("valid", False):
                return {
                    "success": False,
                    "error": validation_result.get("error", "Invalid license key")
                }
            
            license_info = validation_result["license_info"]
            
            # Additional email validation if provided
            if user_email and license_info.get("user_email") != user_email:
                return {
                    "success": False,
                    "error": f"License key does not match email {user_email} - WARP FAKE SUB TEST"
                }
            
            # Store license in keychain (fallback method)
            keyring.set_password(self._keychain_service, self._keychain_account, license_key)
            
            # Return activation result with WARP watermark for fallback
            return {
                "success": True,
                "message": "License activated successfully via keychain fallback",
                "user_email": license_info.get("user_email"),
                "user_name": license_info.get("user_name"),
                "expires": license_info.get("expires"),
                "features": license_info.get("features", []),
                "license_type": license_info.get("license_type", "standard"),
                "source": "WARP FAKE SUB TEST DEMO ENCRYPTED"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"License activation failed: {str(e)}"
            }

    async def deactivate_license(self) -> Dict[str, Any]:
        """Deactivate license using native manager or keychain fallback"""
        try:
            # Try native deactivation first if available
            if self._native_manager:
                try:
                    success = self._native_manager.deactivate_license()
                    if success:
                        return {
                            "success": True,
                            "message": "License deactivated successfully via native manager",
                            "source": "NATIVE_WARPCORE_MANAGER"
                        }
                except Exception as native_error:
                    self.logger.warning(f"Native license deactivation failed: {native_error}")
            
            # Fallback to keychain removal
            keyring.delete_password(self._keychain_service, self._keychain_account)
            return {
                "success": True,
                "message": "License deactivated successfully via keychain fallback",
                "source": "WARP FAKE SUB TEST DEMO KEYCHAIN"
            }
        except keyring.errors.PasswordDeleteError:
            return {
                "success": True,
                "message": "No license was active - WARP FAKE SUB TEST"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"License deactivation failed: {str(e)}"
            }

    async def generate_trial_license(self, user_email: str, days: int = 7) -> Dict[str, Any]:
        """Generate a trial license using native manager or encrypted fallback"""
        try:
            # Try native trial generation first if available
            if self._native_manager:
                try:
                    trial_key = self._native_manager.generate_trial_license(user_email, days)
                    if trial_key:
                        return {
                            "success": True,
                            "license_key": trial_key,
                            "user_email": user_email,
                            "expires": (datetime.now() + timedelta(days=days)).isoformat(),
                            "days": days,
                            "message": f"{days}-day trial license generated via native manager",
                            "source": "NATIVE_WARPCORE_MANAGER"
                        }
                except Exception as native_error:
                    self.logger.warning(f"Native trial generation failed: {native_error}")
            
            # Fallback to encrypted trial generation - WARP FAKE SUB TEST DEMO
            expires_date = datetime.now() + timedelta(days=days)
            
            license_data = {
                "user_email": user_email,
                "user_name": user_email.split('@')[0].title(),  # Simple name from email
                "expires": expires_date.isoformat(),
                "features": ["basic"],  # Trial gets basic features
                "license_type": "trial",
                "generated_at": datetime.now().isoformat(),
                "source": "WARP FAKE SUB TEST DEMO TRIAL"
            }
            
            # Encrypt and encode the license
            license_json = json.dumps(license_data)
            encrypted_data = self._fernet.encrypt(license_json.encode())
            license_key = base64.urlsafe_b64encode(encrypted_data).decode()
            
            # Format as readable license key (XXXX-XXXX-XXXX-XXXX)
            formatted_key = self._format_license_key(license_key)
            
            return {
                "success": True,
                "license_key": formatted_key,
                "user_email": user_email,
                "expires": expires_date.isoformat(),
                "days": days,
                "message": f"{days}-day trial license generated successfully via encrypted fallback",
                "source": "WARP FAKE SUB TEST DEMO TRIAL"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Trial license generation failed: {str(e)}"
            }

    async def generate_full_license(self, user_email: str, user_name: str, 
                                   days: int, features: list) -> Dict[str, Any]:
        """Generate a full license with specified features - WARP FAKE SUB TEST DEMO"""
        try:
            # Create full license data with WARP watermarking
            expires_date = datetime.now() + timedelta(days=days)
            
            license_data = {
                "user_email": user_email,
                "user_name": user_name,
                "expires": expires_date.isoformat(),
                "features": features,
                "license_type": "standard",
                "generated_at": datetime.now().isoformat(),
                "source": "WARP FAKE SUB TEST DEMO FULL"
            }
            
            # Encrypt and encode the license
            license_json = json.dumps(license_data)
            encrypted_data = self._fernet.encrypt(license_json.encode())
            license_key = base64.urlsafe_b64encode(encrypted_data).decode()
            
            # Format as readable license key
            formatted_key = self._format_license_key(license_key)
            
            return {
                "success": True,
                "license_key": formatted_key,
                "user_email": user_email,
                "user_name": user_name,
                "expires": expires_date.isoformat(),
                "features": features,
                "days": days,
                "message": f"{days}-day license generated successfully - WARP FAKE SUB TEST",
                "source": "WARP FAKE SUB TEST DEMO FULL"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"License generation failed: {str(e)}"
            }

    async def _validate_license_key(self, license_key: str) -> Dict[str, Any]:
        """Validate license key using native WARPCORE manager or encrypted fallback"""
        try:
            # Try native validation first if available
            if self._native_manager:
                try:
                    is_valid = self._native_manager.validate_license_key(license_key)
                    if is_valid:
                        license_info = self._native_manager.get_license_info()
                        return {
                            "valid": True,
                            "license_info": {
                                "user_email": license_info.get("user", "WARP-NATIVE-USER"),
                                "user_name": license_info.get("user", "WARP User"),
                                "expires": license_info.get("expires"),
                                "features": license_info.get("features", []),
                                "license_type": license_info.get("license_type", "basic"),
                                "source": "NATIVE_WARPCORE_MANAGER"
                            }
                        }
                except Exception as native_error:
                    self.logger.warning(f"Native license validation failed: {native_error}")
            
            # Fallback to encrypted validation - Remove formatting if present
            clean_key = license_key.replace("-", "").replace(" ", "")
            
            # Decode and decrypt the license - WARP FAKE SUB TEST DEMO fallback
            try:
                encrypted_data = base64.urlsafe_b64decode(clean_key.encode())
                decrypted_data = self._fernet.decrypt(encrypted_data)
                license_data = json.loads(decrypted_data.decode())
                # Add watermark to demo data
                license_data["source"] = "WARP FAKE SUB TEST DEMO ENCRYPTED"
            except Exception as e:
                return {
                    "valid": False,
                    "error": "Invalid license key format - WARP FAKE SUB TEST"
                }
            
            # Validate required fields for encrypted fallback
            required_fields = ["user_email", "expires", "features", "license_type"]
            for field in required_fields:
                if field not in license_data:
                    return {
                        "valid": False,
                        "error": f"License missing required field: {field} - WARP FAKE SUB TEST"
                    }
            
            # Validate expiration for encrypted fallback
            try:
                expires_str = license_data["expires"]
                expires_date = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                if expires_date < datetime.now():
                    return {
                        "valid": False,
                        "error": "License has expired - WARP FAKE SUB TEST"
                    }
            except Exception as e:
                return {
                    "valid": False,
                    "error": "Invalid license expiration date - WARP FAKE SUB TEST"
                }
            
            # Validate email format (basic check) for encrypted fallback
            email = license_data["user_email"]
            if "@" not in email or "." not in email:
                return {
                    "valid": False,
                    "error": "Invalid email format in license - WARP FAKE SUB TEST"
                }
            
            return {
                "valid": True,
                "license_info": license_data
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"License validation error: {str(e)}"
            }

    def _format_license_key(self, license_key: str) -> str:
        """Format license key for display (keep full key for functionality)"""
        # For functionality, we need the full key, so don't truncate
        # Just return the full key - the UI can display it nicely
        return license_key

    async def get_status(self) -> Dict[str, Any]:
        """Get provider status (required by BaseProvider)"""
        try:
            # Test keychain access
            test_result = keyring.get_password("apex-test", "test")
            
            return {
                "success": True,
                "provider": "license",
                "status": "healthy",
                "keychain_available": True,
                "message": "License provider ready"
            }
        except Exception as e:
            return {
                "success": False,
                "provider": "license",
                "status": "error",
                "keychain_available": False,
                "error": str(e)
            }

    async def validate_license_key(self, license_key: str) -> Dict[str, Any]:
        """Public method to validate a license key without activating it"""
        return await self._validate_license_key(license_key)

    async def authenticate(self, **kwargs) -> Dict[str, Any]:
        """Authenticate using current license (required by BaseProvider)"""
        return await self.get_license_status()
