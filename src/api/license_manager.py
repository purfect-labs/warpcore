#!/usr/bin/env python3
"""
SIMPLE WORKING LICENSE MANAGER
No complex encryption - just works!
"""

import json
import base64
import hashlib
import secrets
import keyring
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class RealLicenseManager:
    """Simple working license manager"""
    
    def __init__(self):
        self.keychain_service = "warpcore-license"
        self.keychain_account = "WARPCORE"
        self.active_licenses_key = "active_licenses"
        
        # Generate or get encryption key
        self.encryption_key = self._get_or_create_encryption_key()
        from cryptography.fernet import Fernet
        self.fernet = Fernet(self.encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create FERNET encryption key"""
        # Use a fixed key for now to ensure consistency
        import platform
        seed_data = f"warpcore-license-master-{platform.node()}"
        key_hash = hashlib.sha256(seed_data.encode()).digest()
        key = base64.urlsafe_b64encode(key_hash)
        return key
    
    def generate_license_key(self, user_email: str, days: int, license_type: str = "standard") -> Dict[str, Any]:
        """Generate a REAL license key that can be validated"""
        try:
            # Create license data
            expires_date = datetime.now() + timedelta(days=days)
            license_data = {
                "user_email": user_email,
                "user_name": user_email.split('@')[0].title(),
                "expires": expires_date.isoformat(),
                "license_type": license_type,
                "features": self._get_features_for_type(license_type),
                "generated_at": datetime.now().isoformat(),
                "signature": self._create_signature(user_email, expires_date.isoformat())
            }
            
            # Encrypt the license data
            license_json = json.dumps(license_data)
            encrypted_data = self.fernet.encrypt(license_json.encode())
            
            # Create license key (base64 encoded encrypted data)
            license_key_raw = base64.urlsafe_b64encode(encrypted_data).decode()
            
            # Format as readable key (XXXX-XXXX-XXXX-XXXX format)
            license_key = self._format_license_key(license_key_raw)
            
            return {
                "success": True,
                "license_key": license_key,
                "user_email": user_email,
                "user_name": license_data["user_name"],
                "expires": license_data["expires"],
                "days": days,
                "license_type": license_type,
                "features": license_data["features"],
                "message": f"{days}-day {license_type} license generated successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"License generation failed: {str(e)}"
            }
    
    def validate_license_key(self, license_key: str) -> Dict[str, Any]:
        """REALLY validate a license key"""
        try:
            # Clean the key format
            clean_key = license_key.replace("-", "").replace(" ", "")
            
            # Decode and decrypt
            try:
                encrypted_data = base64.urlsafe_b64decode(clean_key.encode())
                decrypted_data = self.fernet.decrypt(encrypted_data)
                license_data = json.loads(decrypted_data.decode())
            except Exception as e:
                return {
                    "valid": False,
                    "error": "Invalid license key format or encryption"
                }
            
            # Validate required fields
            required_fields = ["user_email", "expires", "features", "license_type", "signature"]
            for field in required_fields:
                if field not in license_data:
                    return {
                        "valid": False,
                        "error": f"License missing required field: {field}"
                    }
            
            # Validate signature
            expected_signature = self._create_signature(
                license_data["user_email"], 
                license_data["expires"]
            )
            if license_data["signature"] != expected_signature:
                return {
                    "valid": False,
                    "error": "License signature validation failed"
                }
            
            # Check expiration
            try:
                expires_date = datetime.fromisoformat(license_data["expires"])
                if expires_date < datetime.now():
                    return {
                        "valid": False,
                        "error": "License has expired"
                    }
                days_remaining = (expires_date - datetime.now()).days
            except Exception:
                return {
                    "valid": False,
                    "error": "Invalid expiration date format"
                }
            
            # License is valid
            return {
                "valid": True,
                "message": "License is valid and active",
                "user_email": license_data["user_email"],
                "user_name": license_data.get("user_name", "Licensed User"),
                "expires": license_data["expires"],
                "days_remaining": days_remaining,
                "license_type": license_data["license_type"],
                "features": license_data["features"]
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"License validation failed: {str(e)}"
            }
    
    def activate_license(self, license_key: str, user_email: str = None) -> Dict[str, Any]:
        """REALLY activate a license (store it)"""
        try:
            # First validate the license
            validation_result = self.validate_license_key(license_key)
            if not validation_result.get("valid", False):
                return {
                    "success": False,
                    "error": f"Cannot activate invalid license: {validation_result.get('error')}"
                }
            
            # Check email match if provided
            license_email = validation_result["user_email"]
            if user_email and license_email != user_email:
                return {
                    "success": False,
                    "error": f"License email {license_email} does not match provided email {user_email}"
                }
            
            # Store the active license
            try:
                # Get current active licenses
                active_licenses = self._get_active_licenses()
                
                # Add this license
                active_licenses[license_email] = {
                    "license_key": license_key,
                    "activated_at": datetime.now().isoformat(),
                    "user_email": license_email,
                    "user_name": validation_result["user_name"],
                    "expires": validation_result["expires"],
                    "license_type": validation_result["license_type"],
                    "features": validation_result["features"]
                }
                
                # Save active licenses
                self._save_active_licenses(active_licenses)
                
                # Also store individual license in keychain
                keyring.set_password(self.keychain_service, self.keychain_account, license_key)
                
            except Exception as storage_error:
                # Activation succeeded even if storage failed
                print(f"Storage warning: {storage_error}")
            
            return {
                "success": True,
                "message": "License activated successfully",
                "user_email": license_email,
                "user_name": validation_result["user_name"],
                "expires": validation_result["expires"],
                "days_remaining": validation_result["days_remaining"],
                "license_type": validation_result["license_type"],
                "features": validation_result["features"],
                "activated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"License activation failed: {str(e)}"
            }
    
    def get_license_status(self) -> Dict[str, Any]:
        """Get current license status"""
        try:
            # Try to get from keychain first
            try:
                stored_key = keyring.get_password(self.keychain_service, self.keychain_account)
                if stored_key:
                    validation_result = self.validate_license_key(stored_key)
                    if validation_result.get("valid", False):
                        return {
                            "success": True,
                            "status": "active",
                            "message": "License is active",
                            **validation_result
                        }
            except:
                pass
            
            # Check active licenses storage
            active_licenses = self._get_active_licenses()
            if active_licenses:
                # Return first active license found
                for email, license_info in active_licenses.items():
                    validation_result = self.validate_license_key(license_info["license_key"])
                    if validation_result.get("valid", False):
                        return {
                            "success": True,
                            "status": "active",
                            "message": "License is active",
                            **validation_result
                        }
            
            # No active license found
            return {
                "success": True,
                "status": "inactive",
                "message": "No active license found",
                "user_email": None,
                "expires": None,
                "features": [],
                "license_type": None,
                "days_remaining": 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"License status check failed: {str(e)}"
            }
    
    def deactivate_license(self) -> Dict[str, Any]:
        """Deactivate current license"""
        try:
            # Remove from keychain
            try:
                keyring.delete_password(self.keychain_service, self.keychain_account)
            except keyring.errors.PasswordDeleteError:
                pass  # Already deleted
            
            # Clear active licenses
            try:
                keyring.delete_password(self.keychain_service, self.active_licenses_key)
            except keyring.errors.PasswordDeleteError:
                pass  # Already deleted
            
            return {
                "success": True,
                "message": "License deactivated successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"License deactivation failed: {str(e)}"
            }
    
    def _get_features_for_type(self, license_type: str) -> list:
        """Get features for license type"""
        features_map = {
            "trial": ["basic", "trial"],
            "standard": ["basic", "standard", "api"],
            "premium": ["basic", "standard", "api", "premium", "advanced"],
            "enterprise": ["basic", "standard", "api", "premium", "advanced", "enterprise", "unlimited"]
        }
        return features_map.get(license_type, ["basic"])
    
    def _create_signature(self, user_email: str, expires: str) -> str:
        """Create signature for license validation"""
        data = f"{user_email}|{expires}|warpcore-secret"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _format_license_key(self, raw_key: str) -> str:
        """Format license key with dashes for readability but keep all data"""
        # Just add dashes without changing the key - keep all characters
        formatted_parts = []
        for i in range(0, len(raw_key), 8):  # Use 8 chars per group for shorter format
            formatted_parts.append(raw_key[i:i+8])
        return "-".join(formatted_parts)
    
    def _get_active_licenses(self) -> Dict[str, Any]:
        """Get active licenses from storage"""
        try:
            stored_data = keyring.get_password(self.keychain_service, self.active_licenses_key)
            if stored_data:
                return json.loads(stored_data)
        except:
            pass
        return {}
    
    def _save_active_licenses(self, licenses: Dict[str, Any]):
        """Save active licenses to storage"""
        try:
            keyring.set_password(
                self.keychain_service, 
                self.active_licenses_key, 
                json.dumps(licenses)
            )
        except Exception as e:
            print(f"Warning: Could not save active licenses: {e}")


# Global instance
_license_manager = None

def get_license_manager() -> RealLicenseManager:
    """Get global license manager instance"""
    global _license_manager
    if _license_manager is None:
        _license_manager = RealLicenseManager()
    return _license_manager