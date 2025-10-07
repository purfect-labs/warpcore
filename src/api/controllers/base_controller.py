"""
WARPCORE Base Controller
Base class for all business logic controllers in the Provider-Abstraction-Pattern
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging


class BaseController(ABC):
    """Base class for all controllers in the PAP architecture"""
    
    def __init__(self, name: str):
        self.name = name
        self.provider_registry = None
        self.websocket_manager = None
        self.logger = logging.getLogger(f"controller.{name}")
    
    def set_provider_registry(self, provider_registry):
        """Set the provider registry for accessing providers"""
        self.provider_registry = provider_registry
    
    def set_websocket_manager(self, websocket_manager):
        """Set the WebSocket manager for real-time communication"""
        self.websocket_manager = websocket_manager
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast a message via WebSocket if available"""
        if self.websocket_manager and hasattr(self.websocket_manager, 'broadcast_message'):
            try:
                await self.websocket_manager.broadcast_message(message)
            except Exception as e:
                self.logger.warning(f"Failed to broadcast message: {e}")
    
    def get_provider(self, name: str):
        """Get a provider by name"""
        if self.provider_registry:
            return self.provider_registry.get_provider(name)
        return None
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get controller status - must be implemented by subclasses"""
        pass
    
    async def authenticate(self, **kwargs) -> Dict[str, Any]:
        """Authentication method - can be overridden by subclasses"""
        return {
            "success": False,
            "message": f"Authentication not implemented for {self.name} controller"
        }
    
    async def initialize(self):
        """Initialize the controller - can be overridden"""
        pass
    
    async def shutdown(self):
        """Shutdown the controller - can be overridden"""
        pass