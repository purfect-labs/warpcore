"""
WARPCORE Route Composer - Discovery-driven API endpoints
PAP Layer 1: Dynamic route generation from provider capabilities
"""

from typing import Dict, Any, List, Callable
from fastapi import FastAPI

class RouteComposer:
    """Compose routes dynamically based on discovered provider capabilities"""
    
    def __init__(self, app: FastAPI, controller_registry):
        self.app = app
        self.controller_registry = controller_registry
        self.registered_routes = set()
    
    async def compose_routes_for_provider(self, provider_name: str, provider_capabilities: List[str]):
        """Compose routes for a discovered provider"""
        
        controller = self.controller_registry.get_controller(provider_name)
        if not controller:
            return
        
        # Generate routes for each capability
        for capability in provider_capabilities:
            await self._create_route_for_capability(provider_name, capability, controller)
    
    async def _create_route_for_capability(self, provider_name: str, capability: str, controller):
        """Create a route for a specific provider capability"""
        
        route_path = f"/api/{provider_name}/{capability}"
        
        # Skip if route already registered
        if route_path in self.registered_routes:
            return
        
        # Create route handler based on capability type
        if capability == "authenticate":
            handler = self._create_auth_handler(controller)
            self.app.post(route_path)(handler)
            
        elif capability.startswith("list_"):
            handler = self._create_list_handler(controller, capability)
            self.app.get(route_path)(handler)
            
        elif capability == "get_status":
            handler = self._create_status_handler(controller)
            self.app.get(route_path)(handler)
            
        else:
            # Generic capability handler
            handler = self._create_generic_handler(controller, capability)
            self.app.post(route_path)(handler)
        
        self.registered_routes.add(route_path)
    
    def _create_auth_handler(self, controller) -> Callable:
        """Create authentication route handler"""
        async def auth_handler(project: str = None, context: str = None):
            return await controller.authenticate(project=project, context=context)
        
        auth_handler.__name__ = f"auth_{controller.name}"
        return auth_handler
    
    def _create_list_handler(self, controller, capability: str) -> Callable:
        """Create list operation route handler"""
        async def list_handler(project: str = None, **kwargs):
            # Map capability to controller method
            method_name = capability  # e.g., "list_projects", "list_instances"
            if hasattr(controller, method_name):
                method = getattr(controller, method_name)
                return await method(project=project, **kwargs)
            else:
                return {"success": False, "error": f"Method {method_name} not found"}
        
        list_handler.__name__ = f"{capability}_{controller.name}"
        return list_handler
    
    def _create_status_handler(self, controller) -> Callable:
        """Create status route handler"""
        async def status_handler():
            return await controller.get_status()
        
        status_handler.__name__ = f"status_{controller.name}"
        return status_handler
    
    def _create_generic_handler(self, controller, capability: str) -> Callable:
        """Create generic capability route handler"""
        async def generic_handler(**kwargs):
            if hasattr(controller, capability):
                method = getattr(controller, capability)
                return await method(**kwargs)
            else:
                return {"success": False, "error": f"Capability {capability} not available"}
        
        generic_handler.__name__ = f"{capability}_{controller.name}"
        return generic_handler
    
    async def auto_discover_and_compose_routes(self):
        """Auto-discover providers and compose routes"""
        
        # Get all controllers and their capabilities
        for controller_name, controller in self.controller_registry._controllers.items():
            
            # Get provider capabilities if controller has a provider
            provider_name = controller_name
            provider = self.controller_registry._provider_registry.get_provider(f"{provider_name}_provider") if hasattr(self.controller_registry, '_provider_registry') else None
            
            if provider and hasattr(provider, 'get_self_description'):
                try:
                    description = await provider.get_self_description()
                    capabilities = description.get("capabilities", [])
                    
                    if capabilities:
                        await self.compose_routes_for_provider(provider_name, capabilities)
                        
                except Exception as e:
                    print(f"Failed to get capabilities for {provider_name}: {e}")
            
            # Fallback: create basic routes for known controller methods
            else:
                await self._create_fallback_routes(provider_name, controller)
    
    async def _create_fallback_routes(self, provider_name: str, controller):
        """Create fallback routes for controllers without self-describing providers"""
        
        # Standard controller methods
        standard_methods = ["authenticate", "get_status", "list_projects"]
        
        for method_name in standard_methods:
            if hasattr(controller, method_name):
                route_path = f"/api/{provider_name}/{method_name}"
                
                if route_path not in self.registered_routes:
                    if method_name == "authenticate":
                        handler = self._create_auth_handler(controller)
                        self.app.post(route_path)(handler)
                    else:
                        handler = self._create_generic_handler(controller, method_name)
                        self.app.get(route_path)(handler)
                    
                    self.registered_routes.add(route_path)
    
    def get_registered_routes(self) -> List[str]:
        """Get list of all registered routes"""
        return list(self.registered_routes)