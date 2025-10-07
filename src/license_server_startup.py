#!/usr/bin/env python3
"""
WARPCORE License Server Startup Integration
Starts license server alongside main WARPCORE application
"""

import asyncio
import logging
import os
from typing import Optional

from license_server import create_license_server


class LicenseServerManager:
    """Manages the license server lifecycle alongside WARPCORE"""
    
    def __init__(self):
        self.license_server = None
        self.license_server_task = None
        self.mode = self._determine_mode()
        self.logger = logging.getLogger(__name__)
    
    def _determine_mode(self) -> str:
        """Determine license server mode from environment"""
        mode = os.getenv('WARP_LICENSE_MODE', 'local')
        
        # Validate mode
        if mode not in ['local', 'remote', 'hybrid']:
            self.logger.warning(f"Invalid license mode '{mode}', defaulting to 'local'")
            mode = 'local'
        
        return mode
    
    async def start_license_server(self):
        """Start the license server in background"""
        try:
            self.logger.info(f"🔐 WARPCORE: Starting license server in {self.mode} mode...")
            
            # Create license server
            self.license_server = create_license_server(self.mode)
            
            # Start server in background task
            self.license_server_task = asyncio.create_task(
                self.license_server.start_server()
            )
            
            # Give it a moment to start
            await asyncio.sleep(1)
            
            self.logger.info(f"✅ WARPCORE: License server started on {self.license_server.config.get_host()}:{self.license_server.config.get_port()}")
            
        except Exception as e:
            self.logger.error(f"❌ WARPCORE: License server startup failed: {str(e)}")
            raise e
    
    async def stop_license_server(self):
        """Stop the license server"""
        try:
            if self.license_server_task:
                self.license_server_task.cancel()
                try:
                    await self.license_server_task
                except asyncio.CancelledError:
                    pass
                
                self.logger.info("🔐 WARPCORE: License server stopped")
                
        except Exception as e:
            self.logger.error(f"❌ WARPCORE: License server stop error: {str(e)}")
    
    def get_server_info(self) -> dict:
        """Get license server information"""
        if self.license_server:
            return {
                "status": "running" if self.license_server_task and not self.license_server_task.done() else "stopped",
                "mode": self.mode,
                "host": self.license_server.config.get_host(),
                "port": self.license_server.config.get_port(),
                "endpoints": {
                    "health": f"http://{self.license_server.config.get_host()}:{self.license_server.config.get_port()}/health",
                    "purchase": f"http://{self.license_server.config.get_host()}:{self.license_server.config.get_port()}/api/license/purchase",
                    "validate": f"http://{self.license_server.config.get_host()}:{self.license_server.config.get_port()}/api/license/validate",
                }
            }
        else:
            return {"status": "not_initialized", "mode": self.mode}


# Global license server manager
_license_server_manager: Optional[LicenseServerManager] = None


def get_license_server_manager() -> LicenseServerManager:
    """Get the global license server manager"""
    global _license_server_manager
    if _license_server_manager is None:
        _license_server_manager = LicenseServerManager()
    return _license_server_manager


async def start_license_server():
    """Start the license server (called during WARPCORE startup)"""
    manager = get_license_server_manager()
    await manager.start_license_server()


async def stop_license_server():
    """Stop the license server (called during WARPCORE shutdown)"""
    manager = get_license_server_manager()
    await manager.stop_license_server()


def get_license_server_info() -> dict:
    """Get license server information"""
    manager = get_license_server_manager()
    return manager.get_server_info()