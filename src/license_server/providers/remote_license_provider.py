#!/usr/bin/env python3
"""
Remote License Provider for WARPCORE License Server
Handles server-side license operations: validation, generation, management
"""

import json
import base64
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import uuid
import logging


class RemoteLicenseProvider:
    """Remote License Provider - Server-side license operations"""
    
    def __init__(self, config, database):
        self.config = config
        self.database = database
        self.logger = logging.getLogger(__name__)
        
        # Initialize encryption
        self._setup_encryption()
        
        # License types and features
        self.license_types = {
            "trial": {
                "duration_days": self.config.get_trial_days(),
                "features": ["basic", "cloud_connect"],
                "max_devices": 1,
                "price": 0.0
            },
            "standard": {
                "duration_days": 365,
                "features": ["basic", "cloud_connect", "advanced_features"],
                "max_devices": 3,
                "price": self.config.get_license_prices()["standard"]
            },
            "enterprise": {
                "duration_days": 365,
                "features": ["basic", "cloud_connect", "advanced_features", "enterprise_features", "admin_panel"],
                "max_devices": 10,
                "price": self.config.get_license_prices()["enterprise"]
            }
        }
        
        self.logger.info("🔐 WARP LICENSE PROVIDER: Remote license provider initialized")
    
    def _setup_encryption(self):
        """Setup FERNET encryption for license keys"""
        try:
            # Use configured key or generate one
            key_str = self.config.get_license_encryption_key()
            if len(key_str) == 32:
                # Pad to 44 characters for base64 encoding
                key_str = key_str + "=" * (44 - len(key_str))
            
            # Ensure it's a valid FERNET key
            try:
                key_bytes = base64.urlsafe_b64decode(key_str.encode())
                if len(key_bytes) != 32:
                    raise ValueError("Key must be 32 bytes")
                self._fernet = Fernet(base64.urlsafe_b64encode(key_bytes))
            except:
                # Generate new key if invalid
                key = Fernet.generate_key()
                self._fernet = Fernet(key)
                self.logger.warning("🔑 WARP LICENSE: Generated new encryption key")
            
        except Exception as e:
            # Fallback to generated key
            key = Fernet.generate_key()
            self._fernet = Fernet(key)
            self.logger.warning(f"🔑 WARP LICENSE: Using fallback encryption key: {str(e)}")
    
    async def generate_license(self, user_email: str, user_name: str, 
                             license_type: str, hardware_signature: str = None) -> Dict[str, Any]:
        """Generate a new license key"""
        try:
            if license_type not in self.license_types:
                return {
                    "success": False,
                    "error": f"Invalid license type: {license_type}"
                }
            
            license_config = self.license_types[license_type]
            expires_date = datetime.now() + timedelta(days=license_config["duration_days"])
            
            # Create license data
            license_data = {
                "user_email": user_email,
                "user_name": user_name,
                "license_type": license_type,
                "features": license_config["features"],
                "max_devices": license_config["max_devices"],
                "expires": expires_date.isoformat(),
                "generated_at": datetime.now().isoformat(),
                "hardware_signature": hardware_signature,
                "license_id": str(uuid.uuid4()),
                "server_signature": self._generate_server_signature(user_email, expires_date)
            }
            
            # Note: Production license generation without demo watermarks
            
            # Encrypt license data
            license_json = json.dumps(license_data, sort_keys=True)
            encrypted_data = self._fernet.encrypt(license_json.encode())
            license_key = base64.urlsafe_b64encode(encrypted_data).decode()
            
            # Format license key for readability
            formatted_key = self._format_license_key(license_key)
            
            # Store in database
            await self.database.store_license(
                license_id=license_data["license_id"],
                user_email=user_email,
                user_name=user_name,
                license_key=formatted_key,
                license_type=license_type,
                expires_date=expires_date,
                hardware_signature=hardware_signature,
                features=license_config["features"]
            )
            
            self.logger.info(f"✅ WARP LICENSE: Generated {license_type} license for {user_email}")
            
            return {
                "success": True,
                "license_key": formatted_key,
                "license_id": license_data["license_id"],
                "user_email": user_email,
                "user_name": user_name,
                "license_type": license_type,
                "features": license_config["features"],
                "expires": expires_date.isoformat(),
                "max_devices": license_config["max_devices"],
                "price": license_config["price"],
                "server_mode": self.config.mode
            }
            
        except Exception as e:
            self.logger.error(f"❌ WARP LICENSE: License generation failed: {str(e)}")
            return {
                "success": False,
                "error": f"License generation failed: {str(e)}"
            }
    
    async def validate_license(self, license_key: str, hardware_signature: str = None) -> Dict[str, Any]:
        """Validate a license key"""
        try:
            # Remove formatting from license key
            clean_key = license_key.replace("-", "").replace(" ", "")
            
            # Decrypt license data
            try:
                encrypted_data = base64.urlsafe_b64decode(clean_key.encode())
                decrypted_data = self._fernet.decrypt(encrypted_data)
                license_data = json.loads(decrypted_data.decode())
            except Exception as e:
                return {
                    "valid": False,
                    "error": "Invalid license key format"
                }
            
            # Check expiration
            expires_date = datetime.fromisoformat(license_data["expires"])
            if datetime.now() > expires_date:
                return {
                    "valid": False,
                    "error": "License has expired",
                    "expires": license_data["expires"]
                }
            
            # Check hardware binding (if provided)
            if hardware_signature and license_data.get("hardware_signature"):
                if license_data["hardware_signature"] != hardware_signature:
                    return {
                        "valid": False,
                        "error": "License not valid for this device",
                        "hardware_mismatch": True
                    }
            
            # Validate server signature
            expected_signature = self._generate_server_signature(
                license_data["user_email"], 
                expires_date
            )
            if license_data.get("server_signature") != expected_signature:
                return {
                    "valid": False,
                    "error": "License signature invalid",
                    "tampered": True
                }
            
            # Check database record (if not in demo mode)
            if not license_data.get("demo_mode", False):
                db_license = await self.database.get_license_by_id(license_data["license_id"])
                if not db_license:
                    return {
                        "valid": False,
                        "error": "License not found in database",
                        "revoked": True
                    }
            
            days_remaining = (expires_date - datetime.now()).days
            
            self.logger.info(f"✅ WARP LICENSE: Validated license for {license_data['user_email']}")
            
            return {
                "valid": True,
                "user_email": license_data["user_email"],
                "user_name": license_data["user_name"],
                "license_type": license_data["license_type"],
                "features": license_data["features"],
                "expires": license_data["expires"],
                "days_remaining": days_remaining,
                "max_devices": license_data["max_devices"],
                "license_id": license_data["license_id"],
                "demo_mode": license_data.get("demo_mode", False),
                "server_mode": self.config.mode
            }
            
        except Exception as e:
            self.logger.error(f"❌ WARP LICENSE: Validation failed: {str(e)}")
            return {
                "valid": False,
                "error": f"License validation failed: {str(e)}"
            }
    
    async def revoke_license(self, license_id: str) -> Dict[str, Any]:
        """Revoke a license"""
        try:
            success = await self.database.revoke_license(license_id)
            if success:
                self.logger.info(f"🚫 WARP LICENSE: Revoked license {license_id}")
                return {
                    "success": True,
                    "message": "License revoked successfully",
                    "license_id": license_id
                }
            else:
                return {
                    "success": False,
                    "error": "License not found",
                    "license_id": license_id
                }
        except Exception as e:
            self.logger.error(f"❌ WARP LICENSE: Revoke failed: {str(e)}")
            return {
                "success": False,
                "error": f"License revocation failed: {str(e)}"
            }
    
    async def get_license_info(self, license_id: str) -> Dict[str, Any]:
        """Get license information"""
        try:
            license_info = await self.database.get_license_by_id(license_id)
            if license_info:
                return {
                    "success": True,
                    **license_info
                }
            else:
                return {
                    "success": False,
                    "error": "License not found"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get license info: {str(e)}"
            }
    
    async def list_user_licenses(self, user_email: str) -> Dict[str, Any]:
        """List all licenses for a user"""
        try:
            licenses = await self.database.get_licenses_by_user(user_email)
            return {
                "success": True,
                "licenses": licenses,
                "count": len(licenses)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list licenses: {str(e)}"
            }
    
    def _generate_server_signature(self, user_email: str, expires_date: datetime) -> str:
        """Generate server signature for tamper detection"""
        data = f"{user_email}:{expires_date.isoformat()}:{self.config.get_jwt_secret()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _format_license_key(self, license_key: str) -> str:
        """Format license key for readability (XXXX-XXXX-XXXX-XXXX)"""
        # Take first 16 characters and format
        key_part = license_key[:16].upper()
        return f"{key_part[:4]}-{key_part[4:8]}-{key_part[8:12]}-{key_part[12:16]}"
    
    def get_license_types(self) -> Dict[str, Any]:
        """Get available license types and their configurations"""
        return {
            "success": True,
            "license_types": self.license_types,
            "server_mode": self.config.mode
        }