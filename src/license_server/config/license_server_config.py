#!/usr/bin/env python3
"""
WARPCORE License Server Configuration
Configurable settings for local/remote/hybrid modes
"""

import os
from typing import Dict, Any, List
from pathlib import Path


class LicenseServerConfig:
    """Configuration for WARPCORE License Server with different modes"""
    
    def __init__(self, mode: str = "local"):
        self.mode = mode
        self._load_config()
    
    def _load_config(self):
        """Load configuration based on mode"""
        
        if self.mode == "local":
            # Local testing mode - runs alongside main WARPCORE
            self.host = "127.0.0.1"
            self.port = 8001  # Different from main WARPCORE (8000)
            self.database_url = "sqlite:///./warp_license_local.db"
            self.payment_enabled = True  # Enable for testing
            self.email_enabled = True   # Enable for testing  
            self.allowed_origins = ["http://localhost:8000", "http://127.0.0.1:8000"]
            self.stripe_test_mode = True
            
        elif self.mode == "remote":
            # Production remote server mode
            self.host = os.getenv("LICENSE_SERVER_HOST", "0.0.0.0")
            self.port = int(os.getenv("LICENSE_SERVER_PORT", "8001"))
            self.database_url = os.getenv("LICENSE_DATABASE_URL", "postgresql://user:pass@localhost/warp_licenses")
            self.payment_enabled = True
            self.email_enabled = True
            self.allowed_origins = self._get_production_origins()
            self.stripe_test_mode = False
            
        elif self.mode == "hybrid":
            # Hybrid mode - local server with remote capabilities
            self.host = "127.0.0.1"
            self.port = 8001
            self.database_url = "sqlite:///./warp_license_hybrid.db"
            self.payment_enabled = True
            self.email_enabled = True
            self.allowed_origins = ["*"]  # Allow all for testing
            self.stripe_test_mode = True
        
        # Common settings - production values required via environment
        self.jwt_secret_key = os.getenv("LICENSE_JWT_SECRET")
        self.stripe_api_key = os.getenv("STRIPE_API_KEY")
        self.stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        # Email configuration - production values required via environment
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        
        # License settings - production values required via environment
        self.license_encryption_key = os.getenv("LICENSE_ENCRYPTION_KEY")
        self.trial_days = int(os.getenv("TRIAL_DAYS", "7"))
        self.standard_license_price = float(os.getenv("STANDARD_LICENSE_PRICE", "99.00"))
        self.enterprise_license_price = float(os.getenv("ENTERPRISE_LICENSE_PRICE", "299.00"))
    
    def _get_production_origins(self) -> List[str]:
        """Get allowed origins for production mode"""
        origins_env = os.getenv("ALLOWED_ORIGINS", "")
        if origins_env:
            return [origin.strip() for origin in origins_env.split(",")]
        return ["https://warpcore.com", "https://app.warpcore.com"]
    
    # Getter methods
    def get_host(self) -> str:
        return self.host
    
    def get_port(self) -> int:
        return self.port
    
    def get_database_url(self) -> str:
        return self.database_url
    
    def get_allowed_origins(self) -> List[str]:
        return self.allowed_origins
    
    def is_payment_enabled(self) -> bool:
        return self.payment_enabled
    
    def is_email_enabled(self) -> bool:
        return self.email_enabled
    
    def is_stripe_test_mode(self) -> bool:
        return self.stripe_test_mode
    
    def get_jwt_secret(self) -> str:
        return self.jwt_secret_key
    
    def get_stripe_api_key(self) -> str:
        return self.stripe_api_key
    
    def get_stripe_webhook_secret(self) -> str:
        return self.stripe_webhook_secret
    
    def get_smtp_config(self) -> Dict[str, Any]:
        return {
            "host": self.smtp_host,
            "port": self.smtp_port,
            "user": self.smtp_user,
            "password": self.smtp_password
        }
    
    def get_license_encryption_key(self) -> str:
        return self.license_encryption_key
    
    def get_trial_days(self) -> int:
        return self.trial_days
    
    def get_license_prices(self) -> Dict[str, float]:
        return {
            "standard": self.standard_license_price,
            "enterprise": self.enterprise_license_price
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Export config as dictionary for debugging"""
        return {
            "mode": self.mode,
            "host": self.host,
            "port": self.port,
            "database_url": self.database_url.replace("://", "://***") if "://" in self.database_url else self.database_url,
            "payment_enabled": self.payment_enabled,
            "email_enabled": self.email_enabled,
            "allowed_origins": self.allowed_origins,
            "stripe_test_mode": self.stripe_test_mode,
            "trial_days": self.trial_days,
            "license_prices": self.get_license_prices()
        }