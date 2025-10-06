"""
WARPCORE Middleware Registry - PAP Layer 5
Policy enforcement, audit logging, and security validation
"""

from typing import Dict, Any, Optional
from .base_middleware import BaseMiddleware
from .security.security_middleware import SecurityMiddleware


class MiddlewareRegistry:
    """Registry for PAP Layer 5 middleware components"""
    
    def __init__(self):
        self._middleware = {}
        self._websocket_manager = None
        self._initialize_core_middleware()
    
    def _initialize_core_middleware(self):
        """Initialize core middleware components"""
        # Security middleware - policy enforcement
        security_middleware = SecurityMiddleware()
        self.register_middleware("security", security_middleware)
        
        # Audit middleware will be registered here when created
        # Rate limiting middleware will be registered here when created
    
    def register_middleware(self, name: str, middleware: BaseMiddleware):
        """Register a middleware component"""
        if self._websocket_manager:
            middleware.set_websocket_manager(self._websocket_manager)
        self._middleware[name] = middleware
        return middleware
    
    def get_middleware(self, name: str) -> Optional[BaseMiddleware]:
        """Get middleware by name"""
        return self._middleware.get(name)
    
    def get_security_middleware(self) -> Optional[SecurityMiddleware]:
        """Get security middleware specifically"""
        return self.get_middleware("security")
    
    def set_websocket_manager(self, websocket_manager):
        """Wire up WebSocket manager for all middleware"""
        self._websocket_manager = websocket_manager
        
        # Update existing middleware
        for middleware in self._middleware.values():
            middleware.set_websocket_manager(websocket_manager)
    
    def get_all_middleware(self) -> Dict[str, BaseMiddleware]:
        """Get all registered middleware"""
        return self._middleware.copy()
    
    async def apply_middleware_chain(self, operation: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply complete middleware chain to operation"""
        
        # Security validation first
        security_middleware = self.get_security_middleware()
        if security_middleware:
            security_result = await security_middleware.validate(operation, context)
            if not security_result.get("allowed", True):
                return {
                    "success": False, 
                    "blocked": True,
                    "reason": security_result.get("reason", "Blocked by security policy"),
                    "middleware": "security"
                }
        
        # Audit logging (when implemented)
        audit_middleware = self.get_middleware("audit")
        if audit_middleware:
            await audit_middleware.log(operation, context)
        
        # Rate limiting (when implemented)
        rate_middleware = self.get_middleware("rate_limiter")
        if rate_middleware:
            rate_result = await rate_middleware.check_rate_limit(context)
            if not rate_result.get("allowed", True):
                return {
                    "success": False,
                    "blocked": True, 
                    "reason": "Rate limit exceeded",
                    "middleware": "rate_limiter"
                }
        
        return {"success": True, "middleware_applied": True}


# Global registry instance
_middleware_registry = None

def get_middleware_registry() -> MiddlewareRegistry:
    """Get global middleware registry instance"""
    global _middleware_registry
    if _middleware_registry is None:
        _middleware_registry = MiddlewareRegistry()
    return _middleware_registry