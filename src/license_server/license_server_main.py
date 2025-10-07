#!/usr/bin/env python3
"""
WARPCORE License Server Main Application
Self-contained remote licensing system with configurable modes
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from .config.license_server_config import LicenseServerConfig
from .providers.remote_license_provider import RemoteLicenseProvider
from .routes.license_server_routes import setup_license_server_routes
from .database.license_database import LicenseDatabase
from .services.payment_service import PaymentService
from .services.email_service import EmailService


class LicenseServerApp:
    """
    WARPCORE License Server - Self-Contained Remote Licensing System
    Configurable modes: local, remote, hybrid
    """
    
    def __init__(self, mode: str = "local"):
        self.mode = mode  # local, remote, hybrid
        self.config = LicenseServerConfig(mode)
        self.app = FastAPI(
            title="WARPCORE License Server", 
            version="1.0.0",
            description=f"Remote licensing system running in {mode} mode"
        )
        
        # Initialize components
        self.database = LicenseDatabase(self.config)
        self.license_provider = RemoteLicenseProvider(self.config, self.database)
        self.payment_service = PaymentService(self.config)
        self.email_service = EmailService(self.config)
        
        # Setup CORS for cross-origin requests from main WARPCORE app
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.get_allowed_origins(),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        setup_license_server_routes(
            self.app, 
            self.license_provider, 
            self.payment_service, 
            self.email_service
        )
        
        # Setup health check
        self.setup_health_check()
        
        logging.info(f"🔐 WARP LICENSE SERVER: Initialized in {mode} mode")
        logging.info(f"📡 WARP LICENSE SERVER: Will run on {self.config.get_host()}:{self.config.get_port()}")
    
    def setup_health_check(self):
        """Setup health check endpoint"""
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "mode": self.mode,
                "server": "WARP_LICENSE_SERVER",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }
        
        @self.app.get("/")
        async def root():
            return {
                "server": "WARPCORE License Server",
                "mode": self.mode,
                "message": f"WARP LICENSE SERVER running in {self.mode} mode",
                "endpoints": {
                    "health": "/health",
                    "purchase": "/api/license/purchase",
                    "validate": "/api/license/validate",
                    "generate": "/api/license/generate",
                    "revoke": "/api/license/revoke"
                }
            }
    
    async def start_server(self):
        """Start the license server"""
        try:
            # Initialize database
            await self.database.initialize()
            
            # Start server
            config = uvicorn.Config(
                self.app,
                host=self.config.get_host(),
                port=self.config.get_port(),
                log_level="info",
                access_log=True
            )
            
            server = uvicorn.Server(config)
            
            logging.info(f"🚀 WARP LICENSE SERVER: Starting on {self.config.get_host()}:{self.config.get_port()}")
            logging.info(f"🔧 WARP LICENSE SERVER: Mode = {self.mode}")
            logging.info(f"💳 WARP LICENSE SERVER: Payment processing = {self.config.is_payment_enabled()}")
            logging.info(f"📧 WARP LICENSE SERVER: Email delivery = {self.config.is_email_enabled()}")
            
            await server.serve()
            
        except Exception as e:
            logging.error(f"❌ WARP LICENSE SERVER: Failed to start: {str(e)}")
            raise e
    
    def run_sync(self):
        """Run server synchronously"""
        asyncio.run(self.start_server())


# Factory function for different modes
def create_license_server(mode: str = None) -> LicenseServerApp:
    """Create license server with specified mode"""
    
    # Determine mode from environment or parameter
    if mode is None:
        mode = os.getenv('WARP_LICENSE_MODE', 'local')
    
    # Validate mode
    if mode not in ['local', 'remote', 'hybrid']:
        logging.warning(f"Invalid license mode '{mode}', defaulting to 'local'")
        mode = 'local'
    
    logging.info(f"🔐 WARP LICENSE SERVER: Creating server in {mode} mode")
    
    return LicenseServerApp(mode)


# Main entry point for standalone execution
if __name__ == "__main__":
    import sys
    
    # Get mode from command line argument or default to local
    mode = sys.argv[1] if len(sys.argv) > 1 else 'local'
    
    print(f"🔐 WARPCORE License Server starting in {mode} mode...")
    
    server = create_license_server(mode)
    server.run_sync()