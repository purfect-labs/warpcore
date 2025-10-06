"""
WARPCORE Auto-Registration System
Auto-discover and register controllers, orchestrators, and providers for discovered services
"""

import asyncio
import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Type
from abc import ABC


class ComponentAutoDiscovery:
    """Auto-discover and register PAP components based on discovered providers"""
    
    def __init__(self, base_path: str = "src.api"):
        self.base_path = base_path
        self.discovered_components = {
            "controllers": {},
            "orchestrators": {},
            "providers": {},
            "capabilities": {}
        }
        self.component_methods = {}
    
    async def auto_discover_components(self, discovered_providers: List[str]) -> Dict[str, Any]:
        """Auto-discover all PAP components for discovered providers"""
        
        components = {}
        
        for provider_name in discovered_providers:
            provider_components = await self._discover_provider_components(provider_name)
            if provider_components:
                components[provider_name] = provider_components
        
        self.discovered_components = components
        return components
    
    async def _discover_provider_components(self, provider_name: str) -> Dict[str, Any]:
        """Discover all components for a specific provider"""
        
        component_info = {
            "controllers": await self._discover_controllers(provider_name),
            "orchestrators": await self._discover_orchestrators(provider_name),
            "providers": await self._discover_providers(provider_name),
            "capabilities": []
        }
        
        # Aggregate capabilities from all components
        all_capabilities = set()
        for comp_type, components in component_info.items():
            if comp_type != "capabilities" and components:
                for comp_name, comp_data in components.items():
                    all_capabilities.update(comp_data.get("methods", []))
        
        component_info["capabilities"] = list(all_capabilities)
        return component_info
    
    async def _discover_controllers(self, provider_name: str) -> Dict[str, Any]:
        """Auto-discover controllers by scanning filesystem"""
        controllers = {}
        
        # Dynamically discover controller modules by scanning filesystem
        controller_modules = await self._scan_for_modules("controllers")
        
        for module_path in controller_modules:
            # Try to import each module and find controller classes
            controller_info = await self._scan_module_for_controllers(module_path)
            if controller_info:
                for class_name, info in controller_info.items():
                    controllers[class_name] = info
        
        return controllers
    
    async def _discover_orchestrators(self, provider_name: str) -> Dict[str, Any]:
        """Auto-discover orchestrators by scanning filesystem"""
        orchestrators = {}
        
        # Dynamically discover orchestrator modules by scanning filesystem
        orchestrator_modules = await self._scan_for_modules("orchestrators")
        
        for module_path in orchestrator_modules:
            # Try to import each module and find orchestrator classes
            orchestrator_info = await self._scan_module_for_orchestrators(module_path)
            if orchestrator_info:
                for class_name, info in orchestrator_info.items():
                    orchestrators[class_name] = info
        
        return orchestrators
    
    async def _discover_providers(self, provider_name: str) -> Dict[str, Any]:
        """Auto-discover providers by scanning filesystem"""
        providers = {}
        
        # Dynamically discover provider modules by scanning filesystem
        provider_modules = await self._scan_for_modules("providers")
        
        for module_path in provider_modules:
            # Try to import each module and find provider classes
            provider_info = await self._scan_module_for_providers(module_path)
            if provider_info:
                for class_name, info in provider_info.items():
                    providers[class_name] = info
        
        return providers
    
    async def _try_import_component(self, module_path: str, class_name: str, component_type: str) -> Optional[Dict[str, Any]]:
        """Try to import and analyze a component"""
        try:
            # Convert path to proper import format
            full_module_path = f"{self.base_path}.{module_path}"
            
            # Try to import the module
            module = importlib.import_module(full_module_path)
            
            # Look for the class
            if hasattr(module, class_name):
                cls = getattr(module, class_name)
                return await self._analyze_component_class(cls, component_type)
            
            # Also try case variations
            for attr_name in dir(module):
                if attr_name.lower() == class_name.lower() and inspect.isclass(getattr(module, attr_name)):
                    cls = getattr(module, attr_name)
                    return await self._analyze_component_class(cls, component_type)
        
        except (ImportError, AttributeError, ModuleNotFoundError):
            pass
        
        return None
    
    async def _analyze_component_class(self, cls: Type, component_type: str) -> Dict[str, Any]:
        """Analyze a component class to extract methods and capabilities"""
        
        methods = []
        async_methods = []
        
        # Get all methods from the class
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if not name.startswith('_'):  # Skip private methods
                methods.append(name)
                
                # Check if it's an async method
                if inspect.iscoroutinefunction(method):
                    async_methods.append(name)
        
        # Get all methods including inherited ones from instance
        try:
            # Try to create an instance to get runtime methods
            instance = cls() if component_type == "provider" else cls("auto_discovered")
            instance_methods = [
                name for name, method in inspect.getmembers(instance, predicate=inspect.ismethod)
                if not name.startswith('_')
            ]
            # Merge with class methods
            methods = list(set(methods + instance_methods))
        except Exception:
            # If instantiation fails, just use class methods
            pass
        
        return {
            "class_name": cls.__name__,
            "module": cls.__module__,
            "methods": methods,
            "async_methods": async_methods,
            "component_type": component_type,
            "instantiable": self._is_instantiable(cls),
            "has_base_interface": self._has_required_interface(cls, component_type)
        }
    
    def _is_instantiable(self, cls: Type) -> bool:
        """Check if a class can be instantiated"""
        try:
            # Check if it's abstract
            if inspect.isabstract(cls):
                return False
            
            # Check if constructor has required parameters
            sig = inspect.signature(cls.__init__)
            required_params = [
                p for name, p in sig.parameters.items() 
                if name != 'self' and p.default == p.empty
            ]
            
            # If no required parameters or only simple ones, it's instantiable
            return len(required_params) <= 1
            
        except Exception:
            return False
    
    def _has_required_interface(self, cls: Type, component_type: str) -> bool:
        """Check if class has required interface methods"""
        
        required_methods = {
            "controller": ["authenticate", "get_status"],
            "orchestrator": ["orchestrate"],
            "provider": ["authenticate", "get_status", "execute_command"]
        }
        
        if component_type not in required_methods:
            return True
        
        class_methods = [name for name, _ in inspect.getmembers(cls, predicate=inspect.isfunction)]
        required = required_methods[component_type]
        
        return all(method in class_methods for method in required)
    
    async def auto_register_components(self, registry_manager) -> Dict[str, Any]:
        """Auto-register discovered components with their respective registries"""
        
        registration_results = {
            "controllers": {},
            "orchestrators": {}, 
            "providers": {}
        }
        
        for provider_name, components in self.discovered_components.items():
            
            # Auto-register controllers
            for controller_name, controller_info in components.get("controllers", {}).items():
                if controller_info.get("instantiable") and controller_info.get("has_base_interface"):
                    try:
                        result = await self._register_controller(
                            provider_name, controller_name, controller_info, registry_manager
                        )
                        registration_results["controllers"][f"{provider_name}_{controller_name}"] = result
                    except Exception as e:
                        registration_results["controllers"][f"{provider_name}_{controller_name}"] = {
                            "success": False, "error": str(e)
                        }
            
            # Auto-register orchestrators  
            for orchestrator_name, orchestrator_info in components.get("orchestrators", {}).items():
                if orchestrator_info.get("instantiable") and orchestrator_info.get("has_base_interface"):
                    try:
                        result = await self._register_orchestrator(
                            provider_name, orchestrator_name, orchestrator_info, registry_manager
                        )
                        registration_results["orchestrators"][f"{provider_name}_{orchestrator_name}"] = result
                    except Exception as e:
                        registration_results["orchestrators"][f"{provider_name}_{orchestrator_name}"] = {
                            "success": False, "error": str(e)
                        }
            
            # Auto-register providers
            for provider_comp_name, provider_info in components.get("providers", {}).items():
                if provider_info.get("instantiable") and provider_info.get("has_base_interface"):
                    try:
                        result = await self._register_provider(
                            provider_name, provider_comp_name, provider_info, registry_manager
                        )
                        registration_results["providers"][f"{provider_name}_{provider_comp_name}"] = result
                    except Exception as e:
                        registration_results["providers"][f"{provider_name}_{provider_comp_name}"] = {
                            "success": False, "error": str(e)
                        }
        
        return registration_results
    
    async def _register_controller(self, provider_name: str, controller_name: str, 
                                 controller_info: Dict, registry_manager) -> Dict[str, Any]:
        """Register a discovered controller"""
        
        module = importlib.import_module(controller_info["module"])
        controller_class = getattr(module, controller_info["class_name"])
        
        # Instantiate controller
        controller_instance = controller_class()
        
        # Register with controller registry
        if hasattr(registry_manager, 'controller_registry'):
            registry_manager.controller_registry.register_controller(
                f"{provider_name}_controller", controller_instance
            )
        
        return {
            "success": True,
            "component": controller_info["class_name"],
            "methods": controller_info["methods"],
            "registered_as": f"{provider_name}_controller"
        }
    
    async def _register_orchestrator(self, provider_name: str, orchestrator_name: str,
                                   orchestrator_info: Dict, registry_manager) -> Dict[str, Any]:
        """Register a discovered orchestrator"""
        
        module = importlib.import_module(orchestrator_info["module"])
        orchestrator_class = getattr(module, orchestrator_info["class_name"])
        
        # Instantiate orchestrator
        orchestrator_instance = orchestrator_class()
        
        # Wire up with registries if available
        if hasattr(registry_manager, 'provider_registry'):
            orchestrator_instance.set_provider_registry(registry_manager.provider_registry)
        if hasattr(registry_manager, 'middleware_registry'):
            orchestrator_instance.set_middleware_registry(registry_manager.middleware_registry)
        if hasattr(registry_manager, 'executor_registry'):
            orchestrator_instance.set_executor_registry(registry_manager.executor_registry)
        
        # Store for future use
        setattr(registry_manager, f"{provider_name}_orchestrator", orchestrator_instance)
        
        return {
            "success": True,
            "component": orchestrator_info["class_name"],
            "methods": orchestrator_info["methods"],
            "registered_as": f"{provider_name}_orchestrator"
        }
    
    async def _register_provider(self, provider_name: str, provider_comp_name: str,
                                provider_info: Dict, registry_manager) -> Dict[str, Any]:
        """Register a discovered provider"""
        
        module = importlib.import_module(provider_info["module"])
        provider_class = getattr(module, provider_info["class_name"])
        
        # Instantiate provider
        provider_instance = provider_class()
        
        # Wire up with WebSocket manager if available
        if hasattr(registry_manager, 'provider_registry'):
            registry_manager.provider_registry.register_provider(
                f"{provider_name}_{provider_comp_name}", provider_instance
            )
        
        return {
            "success": True,
            "component": provider_info["class_name"],
            "methods": provider_info["methods"],
            "registered_as": f"{provider_name}_{provider_comp_name}"
        }
    
    def get_discovered_capabilities(self) -> Dict[str, List[str]]:
        """Get business-relevant discovered capabilities by provider (filter out infrastructure)"""
        capabilities = {}
        
        # Infrastructure methods that shouldn't be shown as capabilities
        infrastructure_methods = {
            # Base class infrastructure
            'set_provider_registry', 'set_middleware_registry', 'set_executor_registry',
            'set_websocket_manager', 'broadcast_message', 'log_action', 'apply_middleware',
            
            # Generic filesystem/storage methods
            'normalize_path', 'create_directory', 'delete_file', 'move_file', 'copy_file',
            'stream_file', 'get_filename', 'get_file_size', 'filter_files', 'list_files',
            
            # Generic orchestration infrastructure  
            'compose_workflow', 'compose_workflow_with_safety', 'execute_with_safety',
            'get_executor', 'get_middleware', 'get_provider', 'orchestrate',
            
            # Generic validation/safety
            'validate_command', 'sanitize_input', 'check_permissions', 'log_result',
        }
        
        for provider_name, components in self.discovered_components.items():
            provider_capabilities = set()
            
            for comp_type, comp_data in components.items():
                if comp_type != "capabilities" and isinstance(comp_data, dict):
                    for comp_name, comp_info in comp_data.items():
                        if isinstance(comp_info, dict) and "methods" in comp_info:
                            # Only include business-relevant methods
                            for method in comp_info["methods"]:
                                if (method not in infrastructure_methods and 
                                    not method.startswith('_') and
                                    self._is_business_capability(method, comp_name)):
                                    provider_capabilities.add(method)
            
            capabilities[provider_name] = list(provider_capabilities)
        
        return capabilities
    
    def _is_business_capability(self, method: str, component_name: str) -> bool:
        """Determine if a method represents a business capability vs infrastructure"""
        
        # Business capability patterns
        business_patterns = [
            'authenticate', 'login', 'auth', 'sso',
            'deploy', 'create', 'delete', 'update', 'get', 'list',
            'start', 'stop', 'restart', 'scale',
            'connect', 'disconnect', 'switch',
            'generate', 'validate', 'verify',
            'orchestrate_authentication', 'orchestrate_project_discovery', 'orchestrate_status_check',
            'get_license_status', 'generate_full_license', 'deactivate_license'
        ]
        
        # Check if method matches business patterns
        method_lower = method.lower()
        for pattern in business_patterns:
            if pattern in method_lower:
                return True
                
        # Component-specific business capabilities
        component_lower = component_name.lower()
        if 'auth' in component_lower and any(word in method_lower for word in ['login', 'token', 'profile', 'account']):
            return True
        if 'k8s' in component_lower and any(word in method_lower for word in ['cluster', 'pod', 'service', 'context']):
            return True
        if 'gcp' in component_lower and any(word in method_lower for word in ['project', 'resource', 'instance']):
            return True
            
        return False
    
    async def _scan_for_modules(self, directory: str) -> List[str]:
        """Scan filesystem for Python modules in a directory"""
        modules = []
        try:
            base_path = Path(f"src/api/{directory}")
            if base_path.exists():
                # Scan all Python files recursively
                for py_file in base_path.rglob("*.py"):
                    if py_file.name != "__init__.py":
                        # Convert file path to module path
                        relative_path = py_file.relative_to(Path("src/api"))
                        module_path = str(relative_path.with_suffix("")).replace("/", ".")
                        modules.append(module_path)
        except Exception:
            pass
        return modules
    
    async def _scan_module_for_controllers(self, module_path: str) -> Dict[str, Any]:
        """Scan a module for controller classes"""
        controllers = {}
        try:
            full_module_path = f"{self.base_path}.{module_path}"
            module = importlib.import_module(full_module_path)
            
            # Find all classes that look like controllers
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if ("controller" in name.lower() or 
                    (hasattr(obj, '__module__') and obj.__module__ == full_module_path)):
                    controller_info = await self._analyze_component_class(obj, "controller")
                    if controller_info:
                        controllers[name] = controller_info
                        
        except (ImportError, AttributeError, ModuleNotFoundError):
            pass
        return controllers
    
    async def _scan_module_for_orchestrators(self, module_path: str) -> Dict[str, Any]:
        """Scan a module for orchestrator classes"""
        orchestrators = {}
        try:
            full_module_path = f"{self.base_path}.{module_path}"
            module = importlib.import_module(full_module_path)
            
            # Find all classes that look like orchestrators
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if ("orchestrator" in name.lower() or 
                    (hasattr(obj, '__module__') and obj.__module__ == full_module_path)):
                    orchestrator_info = await self._analyze_component_class(obj, "orchestrator")
                    if orchestrator_info:
                        orchestrators[name] = orchestrator_info
                        
        except (ImportError, AttributeError, ModuleNotFoundError):
            pass
        return orchestrators
    
    async def _scan_module_for_providers(self, module_path: str) -> Dict[str, Any]:
        """Scan a module for provider classes"""
        providers = {}
        try:
            full_module_path = f"{self.base_path}.{module_path}"
            module = importlib.import_module(full_module_path)
            
            # Find all classes that look like providers
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if ("provider" in name.lower() or "auth" in name.lower() or 
                    "k8s" in name.lower() or "gcp" in name.lower() or
                    (hasattr(obj, '__module__') and obj.__module__ == full_module_path)):
                    provider_info = await self._analyze_component_class(obj, "provider")
                    if provider_info:
                        providers[name] = provider_info
                        
        except (ImportError, AttributeError, ModuleNotFoundError):
            pass
        return providers
