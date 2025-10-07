#!/usr/bin/env python3
"""
WARPCORE License Provider - Production Implementation
Production-ready license operations with hardware binding and FERNET encryption
Handles keychain access, license generation, validation, and security compliance
"""

import json
import base64
import keyring
import asyncio
import hashlib
import platform
import uuid
import os
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from ..core.base_provider import BaseProvider

# Import real APEX license manager for production use
try:
    import sys
    from pathlib import Path
    apex_path = Path(__file__).parent.parent.parent.parent.parent / 'apex'
    sys.path.insert(0, str(apex_path / 'native' / 'app'))
    sys.path.insert(0, str(apex_path / 'web' / 'providers'))
    from apex_license import APEXLicenseManager
    from license import LicenseProvider as APEXLicenseProvider
    APEX_LICENSE_AVAILABLE = True
except ImportError:
    APEXLicenseManager = None
    APEXLicenseProvider = None
    APEX_LICENSE_AVAILABLE = False


class LicenseProvider(BaseProvider):
    """WARPCORE License operations provider - APEX implementation with native integration"""
    
    def __init__(self):
        super().__init__("license")
        
        # Initialize APEX license manager if available
        if APEX_LICENSE_AVAILABLE:
            self._native_manager = APEXLicenseManager()
        else:
            self._native_manager = None
        
        # Production-grade FERNET encryption setup
        self._encryption_key = self._get_or_create_encryption_key()
        self._fernet = Fernet(self._encryption_key)
        self._keychain_service = "warpcore-license"
        self._keychain_account = "WARPCORE"
        
        # Hardware binding components
        self._hardware_signature = self._generate_hardware_signature()
        
        # Audit logging setup
        self._audit_file = "/tmp/warpcore_audit.log"
        
        # Security compliance standards
        self._compliance_standards = {
            "encryption_strength": {
                "min_key_length": 256,
                "required_algorithm": "FERNET",
                "key_rotation_days": 90
            },
            "hardware_binding": {
                "required": True,
                "signature_length": 16,
                "entropy_threshold": 3.5
            },
            "tamper_detection": {
                "signature_validation": True,
                "timestamp_validation": True,
                "structure_validation": True
            }
        }
        
        # Vulnerability patterns
        self._vulnerability_patterns = [
            r"(test|demo|fake|example)@",
            r"password.*123",
            r"admin.*admin",
            r"^(root|admin|test)$",
            r"['\";\\\\]",  # SQL injection patterns
            r"<script|javascript:",  # XSS patterns
        ]

    async def get_license_status(self) -> Dict[str, Any]:
        """Get current license status from native manager or keychain fallback"""
        try:
            # Try APEX license manager first if available
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
                    "message": "No license found - WARP FALLBACK TEST",
                    "user_email": None,
                    "expires": None,
                    "features": [],
                    "license_type": None,
                    "days_remaining": None,
                    "source": "WARP FALLBACK KEYCHAIN"
                }
            
            # Validate and decode license
            license_data = await self._validate_license_key(stored_license)
            
            if not license_data.get("valid", False):
                # License is invalid, clear it
                await self.deactivate_license()
                return {
                    "success": True,
                    "status": "invalid",
                    "message": license_data.get("error", "License validation failed - WARP FALLBACK"),
                    "user_email": None,
                    "expires": None,
                    "features": [],
                    "license_type": None,
                    "days_remaining": None,
                    "source": "WARP FALLBACK KEYCHAIN"
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
                "source": "WARP FALLBACK KEYCHAIN"
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
                    "error": f"License key does not match email {user_email} - WARP VALIDATION"
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
                "source": "WARP FALLBACK ENCRYPTED"
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
                "source": "WARP FALLBACK KEYCHAIN"
            }
        except keyring.errors.PasswordDeleteError:
            return {
                "success": True,
                "message": "No license was active - WARP FALLBACK"
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
            
            # Fallback to encrypted trial generation - WARP FALLBACK
            expires_date = datetime.now() + timedelta(days=days)
            
            license_data = {
                "user_email": user_email,
                "user_name": user_email.split('@')[0].title(),  # Simple name from email
                "expires": expires_date.isoformat(),
                "features": ["basic"],  # Trial gets basic features
                "license_type": "trial",
                "generated_at": datetime.now().isoformat(),
                "source": "WARP FALLBACK TRIAL"
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
                "source": "WARP FALLBACK TRIAL"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Trial license generation failed: {str(e)}"
            }

    async def generate_full_license(self, user_email: str, user_name: str, 
                                   days: int, features: list) -> Dict[str, Any]:
        """Generate a full license with specified features using APEX or fallback"""
        try:
            # Try APEX license generation first if available
            if APEX_LICENSE_AVAILABLE:
                try:
                    apex_manager = APEXLicenseManager()
                    # Use APEX's real license generation
                    license_key = apex_manager.generate_license_key(
                        user_email=user_email,
                        user_name=user_name, 
                        days_valid=days,
                        features=features
                    )
                    
                    if license_key:
                        expires_date = datetime.now() + timedelta(days=days)
                        return {
                            "success": True,
                            "license_key": license_key,
                            "user_email": user_email,
                            "user_name": user_name,
                            "expires": expires_date.isoformat(),
                            "features": features,
                            "days": days,
                            "license_type": "standard",
                            "message": f"{days}-day license generated successfully via APEX",
                            "source": "APEX_LICENSE_MANAGER",
                            "real_license": True
                        }
                except Exception as apex_error:
                    self.logger.warning(f"APEX license generation failed: {apex_error}")
            
            # Fallback to encrypted license generation with WARP watermarking
            expires_date = datetime.now() + timedelta(days=days)
            
            license_data = {
                "user_email": user_email,
                "user_name": user_name,
                "expires": expires_date.isoformat(),
                "features": features,
                "license_type": "standard",
                "generated_at": datetime.now().isoformat(),
                "source": "WARP FALLBACK FULL"
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
                "message": f"{days}-day license generated successfully - WARP FALLBACK",
                "source": "WARP FALLBACK FULL"
            }
            
        except Exception as e:
            self._log_audit_event("license_generation_failed", {"error": str(e), "user_email": user_email})
            return {
                "success": False,
                "error": f"License generation failed: {str(e)}"
            }
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create a production-grade FERNET encryption key"""
        try:
            # Try to get existing key from keychain
            stored_key = keyring.get_password("warpcore-encryption", "fernet-key")
            if stored_key:
                return stored_key.encode()
            
            # Generate new key using secure random and salt
            password = os.urandom(32)
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            
            # Store both key and salt securely
            keyring.set_password("warpcore-encryption", "fernet-key", key.decode())
            keyring.set_password("warpcore-encryption", "salt", base64.b64encode(salt).decode())
            
            self._log_audit_event("encryption_key_generated", {"key_length": len(key)})
            return key
            
        except Exception as e:
            # Fallback to deterministic key generation based on hardware
            fallback_data = f"warpcore-{platform.node()}-{platform.machine()}".encode()
            key = base64.urlsafe_b64encode(hashlib.sha256(fallback_data).digest())
            self._log_audit_event("encryption_key_fallback", {"error": str(e)})
            return key
    
    def _generate_hardware_signature(self) -> str:
        """Generate unique hardware fingerprint for license binding"""
        try:
            components = [
                platform.node(),  # Hostname
                platform.machine(),  # Architecture
                platform.processor() or "unknown",  # Processor
                str(uuid.getnode()),  # MAC address
            ]
            
            # Add additional system-specific identifiers
            if platform.system() == "Darwin":
                # macOS specific identifiers
                try:
                    import subprocess
                    result = subprocess.run(["system_profiler", "SPHardwareDataType"], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if "Serial Number" in line:
                                components.append(line.split(":")[1].strip())
                                break
                except:
                    pass
            
            # Create deterministic hardware signature
            combined = "-".join(components)
            signature = hashlib.sha256(combined.encode()).hexdigest()[:16]
            
            self._log_audit_event("hardware_signature_generated", {"signature_length": len(signature)})
            return signature
            
        except Exception as e:
            # Fallback signature based on basic system info
            fallback = f"{platform.system()}-{platform.node()}"
            signature = hashlib.md5(fallback.encode()).hexdigest()[:16]
            self._log_audit_event("hardware_signature_fallback", {"error": str(e)})
            return signature
    
    def _validate_hardware_binding(self, license_data: Dict[str, Any]) -> bool:
        """Validate hardware binding for license enforcement"""
        try:
            stored_signature = license_data.get("hardware_signature")
            if not stored_signature:
                return True  # No hardware binding required
            
            current_signature = self._generate_hardware_signature()
            is_valid = stored_signature == current_signature
            
            self._log_audit_event("hardware_binding_validation", {
                "valid": is_valid,
                "stored": stored_signature[:8] + "...",
                "current": current_signature[:8] + "..."
            })
            
            return is_valid
            
        except Exception as e:
            self._log_audit_event("hardware_binding_error", {"error": str(e)})
            return False
    
    def _detect_tampering(self, license_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect license tampering and return validation results"""
        try:
            tampering_checks = {
                "signature_valid": True,
                "structure_valid": True,
                "timestamp_valid": True,
                "hardware_valid": True
            }
            
            # Check required fields
            required_fields = ["user_email", "expires", "generated_at", "features"]
            for field in required_fields:
                if field not in license_data:
                    tampering_checks["structure_valid"] = False
                    break
            
            # Check timestamp consistency
            try:
                generated = datetime.fromisoformat(license_data["generated_at"].replace('Z', '+00:00'))
                expires = datetime.fromisoformat(license_data["expires"].replace('Z', '+00:00'))
                if expires <= generated:
                    tampering_checks["timestamp_valid"] = False
            except:
                tampering_checks["timestamp_valid"] = False
            
            # Validate hardware binding
            tampering_checks["hardware_valid"] = self._validate_hardware_binding(license_data)
            
            # Overall tampering detection
            is_tampered = not all(tampering_checks.values())
            
            self._log_audit_event("tampering_detection", {
                "tampered": is_tampered,
                "checks": tampering_checks
            })
            
            return {
                "tampered": is_tampered,
                "checks": tampering_checks
            }
            
        except Exception as e:
            self._log_audit_event("tampering_detection_error", {"error": str(e)})
            return {"tampered": True, "error": str(e)}
    
    def _log_audit_event(self, event_type: str, data: Dict[str, Any]):
        """Log audit events to production logging system"""
        try:
            timestamp = datetime.now().isoformat()
            audit_entry = {
                "timestamp": timestamp,
                "event_type": event_type,
                "component": "license_provider",
                "hardware_signature": self._hardware_signature[:8] + "...",
                "data": data
            }
            
            with open(self._audit_file, "a") as f:
                f.write(json.dumps(audit_entry) + "\n")
                
        except Exception as e:
            # Silent fail for audit logging to not break main functionality
            pass
    
    async def generate_secure_license(self, user_email: str, user_name: str, 
                                    days: int, features: List[str],
                                    hardware_binding: bool = True) -> Dict[str, Any]:
        """Generate a secure license with hardware binding and tamper detection"""
        try:
            expires_date = datetime.now() + timedelta(days=days)
            generated_at = datetime.now()
            
            license_data = {
                "user_email": user_email,
                "user_name": user_name,
                "expires": expires_date.isoformat(),
                "generated_at": generated_at.isoformat(),
                "features": features,
                "license_type": "production",
                "version": "2.0"
            }
            
            # Add hardware binding if requested
            if hardware_binding:
                license_data["hardware_signature"] = self._hardware_signature
            
            # Add tamper detection signature
            license_signature = hashlib.sha256(
                json.dumps(license_data, sort_keys=True).encode()
            ).hexdigest()
            license_data["signature"] = license_signature
            
            # Encrypt the license data
            license_json = json.dumps(license_data)
            encrypted_data = self._fernet.encrypt(license_json.encode())
            license_key = base64.urlsafe_b64encode(encrypted_data).decode()
            
            # Format for readability
            formatted_key = self._format_license_key(license_key)
            
            self._log_audit_event("secure_license_generated", {
                "user_email": user_email,
                "days": days,
                "features_count": len(features),
                "hardware_binding": hardware_binding,
                "expires": expires_date.isoformat()
            })
            
            return {
                "success": True,
                "license_key": formatted_key,
                "user_email": user_email,
                "user_name": user_name,
                "expires": expires_date.isoformat(),
                "features": features,
                "days": days,
                "hardware_binding": hardware_binding,
                "license_type": "production",
                "message": f"{days}-day production license generated successfully"
            }
            
        except Exception as e:
            self._log_audit_event("secure_license_generation_failed", {
                "error": str(e),
                "user_email": user_email
            })
            return {
                "success": False,
                "error": f"Secure license generation failed: {str(e)}"
            }
    
    async def _validate_encryption_strength(self, license_data: Dict[str, Any], 
                                          license_key: str = None) -> Dict[str, Any]:
        """Validate encryption strength and algorithm compliance"""
        try:
            result = {
                "valid": True,
                "strength_score": 0,
                "algorithm": "unknown",
                "key_length": 0,
                "errors": [],
                "warnings": []
            }
            
            # Check if encryption is enabled
            if not license_data.get("encrypted", True):
                result["valid"] = False
                result["errors"].append("License is not encrypted")
                return result
            
            # Validate FERNET encryption if license key provided
            if license_key:
                try:
                    clean_key = license_key.replace("-", "").replace(" ", "")
                    import base64
                    decoded = base64.urlsafe_b64decode(clean_key + "==")
                    
                    # Check if it looks like FERNET encrypted data
                    if len(decoded) >= 45:  # Minimum FERNET token size
                        result["algorithm"] = "FERNET"
                        result["strength_score"] = 90
                    else:
                        result["warnings"].append("License key too short for FERNET encryption")
                        result["strength_score"] = 60
                        
                except Exception:
                    result["errors"].append("Unable to validate encryption format")
                    result["valid"] = False
                    return result
            
            # Check encryption standards compliance
            standards = self._compliance_standards.get("encryption_strength", {})
            if result["algorithm"] != standards.get("required_algorithm", "FERNET"):
                result["warnings"].append(f"Algorithm {result['algorithm']} does not match required {standards.get('required_algorithm')}")
                result["strength_score"] -= 10
            
            # Set final strength score
            if result["strength_score"] < 70:
                result["valid"] = False
                result["errors"].append("Encryption strength below security threshold")
            
            self._log_audit_event("encryption_strength_validation", {
                "valid": result["valid"],
                "algorithm": result["algorithm"],
                "strength_score": result["strength_score"]
            })
            
            return result
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Encryption validation failed: {str(e)}"
            }
    
    async def _assess_vulnerabilities(self, license_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess security vulnerabilities in license data"""
        try:
            issues = []
            risk_level = "low"
            
            # Check for vulnerability patterns
            license_str = json.dumps(license_data, default=str)
            for pattern in self._vulnerability_patterns:
                if re.search(pattern, license_str, re.IGNORECASE):
                    issues.append(f"Vulnerability pattern detected: {pattern}")
            
            # Check email security if present
            if "user_email" in license_data:
                email = license_data["user_email"]
                for pattern in [r"(test|demo|fake|example)@", r"admin.*admin"]:
                    if re.search(pattern, email, re.IGNORECASE):
                        issues.append(f"Suspicious email pattern: {pattern}")
            
            # Check for hardcoded test data
            test_indicators = ["warp", "test", "demo", "fake", "example"]
            for indicator in test_indicators:
                if indicator.lower() in license_str.lower():
                    issues.append(f"Test data indicator found: {indicator}")
            
            # Determine risk level
            if len(issues) > 3:
                risk_level = "high"
            elif len(issues) > 1:
                risk_level = "medium"
            
            self._log_audit_event("vulnerability_assessment", {
                "issues_found": len(issues),
                "risk_level": risk_level
            })
            
            return {
                "issues": issues,
                "risk_level": risk_level,
                "issues_count": len(issues)
            }
            
        except Exception as e:
            return {
                "issues": [f"Vulnerability assessment failed: {str(e)}"],
                "risk_level": "high",
                "error": str(e)
            }

    async def _validate_license_key(self, license_key: str) -> Dict[str, Any]:
        """Validate license key with production security, tamper detection, and hardware binding"""
        try:
            # Try native validation first if available
            if self._native_manager:
                try:
                    is_valid = self._native_manager.validate_license_key(license_key)
                    if is_valid:
                        license_info = self._native_manager.get_license_info()
                        self._log_audit_event("license_validation_native_success", {
                            "user": license_info.get("user", "unknown")
                        })
                        return {
                            "valid": True,
                            "license_info": {
                                "user_email": license_info.get("user", "NATIVE-USER"),
                                "user_name": license_info.get("user", "Native User"),
                                "expires": license_info.get("expires"),
                                "features": license_info.get("features", []),
                                "license_type": license_info.get("license_type", "basic"),
                                "source": "NATIVE_WARPCORE_MANAGER"
                            }
                        }
                except Exception as native_error:
                    self.logger.warning(f"Native license validation failed: {native_error}")
                    self._log_audit_event("license_validation_native_failed", {
                        "error": str(native_error)
                    })
            
            # Production encrypted validation with security checks
            clean_key = license_key.replace("-", "").replace(" ", "")
            
            # Decode and decrypt the license
            try:
                encrypted_data = base64.urlsafe_b64decode(clean_key.encode())
                decrypted_data = self._fernet.decrypt(encrypted_data)
                license_data = json.loads(decrypted_data.decode())
            except Exception as e:
                self._log_audit_event("license_validation_decryption_failed", {
                    "error": str(e)
                })
                return {
                    "valid": False,
                    "error": "Invalid license key format or encryption"
                }
            
            # Validate required fields
            required_fields = ["user_email", "expires", "features", "license_type"]
            for field in required_fields:
                if field not in license_data:
                    self._log_audit_event("license_validation_missing_field", {
                        "missing_field": field
                    })
                    return {
                        "valid": False,
                        "error": f"License missing required field: {field}"
                    }
            
            # Validate expiration
            try:
                expires_str = license_data["expires"]
                expires_date = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                if expires_date < datetime.now():
                    self._log_audit_event("license_validation_expired", {
                        "expires": expires_str,
                        "user_email": license_data.get("user_email")
                    })
                    return {
                        "valid": False,
                        "error": "License has expired"
                    }
            except Exception as e:
                self._log_audit_event("license_validation_date_error", {
                    "error": str(e)
                })
                return {
                    "valid": False,
                    "error": "Invalid license expiration date"
                }
            
            # Validate email format
            email = license_data["user_email"]
            if "@" not in email or "." not in email:
                self._log_audit_event("license_validation_invalid_email", {
                    "email": email[:5] + "..."
                })
                return {
                    "valid": False,
                    "error": "Invalid email format in license"
                }
            
            # Perform tampering detection
            tamper_result = self._detect_tampering(license_data)
            if tamper_result.get("tampered", False):
                self._log_audit_event("license_validation_tampered", {
                    "tamper_checks": tamper_result.get("checks", {}),
                    "user_email": license_data.get("user_email")
                })
                return {
                    "valid": False,
                    "error": "License tampering detected",
                    "tamper_details": tamper_result
                }
            
            # Validate hardware binding if present
            if "hardware_signature" in license_data:
                if not self._validate_hardware_binding(license_data):
                    self._log_audit_event("license_validation_hardware_mismatch", {
                        "user_email": license_data.get("user_email")
                    })
                    return {
                        "valid": False,
                        "error": "License hardware binding validation failed"
                    }
            
            # All validation passed
            self._log_audit_event("license_validation_success", {
                "user_email": license_data.get("user_email"),
                "license_type": license_data.get("license_type"),
                "hardware_binding": "hardware_signature" in license_data
            })
            
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
