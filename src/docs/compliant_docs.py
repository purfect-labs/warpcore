"""
WARPCORE PAP-Compliant Documentation System
Complete discovery of all layers: Routes -> Controllers -> Orchestrators -> Providers -> Middleware -> Executors
Slick Scalar UI with proper layer separation and real component discovery
"""

import asyncio
import importlib
import inspect
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI
from fastapi.responses import HTMLResponse


class CompliantDocsGenerator:
    """Complete Provider-Abstraction-Pattern compliant documentation system with full layer discovery"""
    
    def __init__(self, app: FastAPI, discovery_system=None):
        self.app = app
        self.discovery = discovery_system
        self.discovered_layers = {}
        
    async def discover_complete_architecture(self) -> Dict[str, Any]:
        """Discover the complete Provider-Abstraction-Pattern architecture across all layers"""
        
        discovered = {
            "data_layer": await self._discover_data_layer(),
            "web_layer": await self._discover_web_layer(),
            "api_layer": await self._discover_api_layer(),
            "architecture_components": await self._discover_architecture_components(),
            "discovery_metadata": {
                "total_components": 0,
                "total_endpoints": 0,
                "architecture_compliance": "Provider-Abstraction-Pattern",
                "layers": 3
            }
        }
        
        # Calculate totals for metadata
        total_components = 0
        total_endpoints = 0
        
        for layer_name, layer_data in discovered.items():
            if isinstance(layer_data, dict) and "components" in layer_data:
                total_components += len(layer_data["components"])
            if isinstance(layer_data, dict) and "endpoints" in layer_data:
                total_endpoints += len(layer_data["endpoints"])
        
        discovered["discovery_metadata"]["total_components"] = total_components
        discovered["discovery_metadata"]["total_endpoints"] = total_endpoints
        
        return discovered
    
    async def register_discovered_endpoints_now(self):
        """Register discovered endpoints after discovery system is ready"""
        if not hasattr(self, '_endpoints_registered') or not self._endpoints_registered:
            await self._register_discovered_endpoints()
            self._endpoints_registered = True
            
            # Get complete architecture after registration
            discovered = await self.discover_complete_architecture()
            
            # Calculate totals
            total_components = 0
            total_endpoints = 0
            
            for layer_name, layer_data in discovered.items():
                if isinstance(layer_data, dict) and "components" in layer_data:
                    total_components += len(layer_data["components"])
                if isinstance(layer_data, dict) and "endpoints" in layer_data:
                    total_endpoints += len(layer_data["endpoints"])
            
            discovered["discovery_metadata"]["total_components"] = total_components
            discovered["discovery_metadata"]["total_endpoints"] = total_endpoints
            
            self.discovered_layers = discovered
            return discovered
        
        return self.discovered_layers if hasattr(self, 'discovered_layers') else {}
    
    async def _discover_data_layer(self) -> Dict[str, Any]:
        """Discover complete data layer components using filesystem scanning"""
        
        data_components = {}
        data_endpoints = {}
        
        # Dynamically discover data layer components by scanning filesystem
        data_modules = await self._scan_for_modules_in_path("src/data")
        
        for module_path in data_modules:
            try:
                module = importlib.import_module(module_path)
                
                # Find all classes and functions that look like data components
                for name, obj in inspect.getmembers(module):
                    if not name.startswith('_') and not self._is_internal_class(name):
                        if inspect.isclass(obj):
                            # Data layer classes (config loaders, feature gates, etc.)
                            if any(keyword in name.lower() for keyword in ['config', 'loader', 'discovery', 'feature', 'gate']):
                                # Skip internal/infrastructure classes
                                if not self._is_infrastructure_class(name, obj):
                                    data_components[name] = {
                                        "type": self._infer_component_type(name),
                                        "description": f"Auto-discovered data component: {name}",
                                        "methods": self._extract_methods(obj),
                                        "capabilities": self._infer_capabilities(name),
                                        "module": module_path
                                    }
                        elif inspect.isfunction(obj):
                            # Data layer functions (get_config, etc.)
                            if any(keyword in name.lower() for keyword in ['get_', 'load_', 'fetch_', 'discover_']):
                                # Only include business-relevant functions
                                if self._is_business_function(name):
                                    data_components[name] = {
                                        "type": "data_function",
                                        "description": f"Auto-discovered data function: {name}",
                                        "methods": [name],
                                        "capabilities": self._infer_capabilities(name),
                                        "module": module_path
                                    }
                                
            except (ImportError, AttributeError, ModuleNotFoundError):
                pass
        
        # Add live discovery system if available
        if self.discovery:
            data_components["live_context_discovery"] = {
                "type": "discovery_provider", 
                "description": "Live autonomous provider and environment discovery",
                "methods": self._extract_methods(self.discovery),
                "capabilities": ["provider_discovery", "environment_inference", "zero_config"]
            }
        
        # Generate data layer endpoints dynamically
        data_endpoints = await self._generate_data_endpoints(data_components)
        
        return {
            "name": "Data Layer",
            "description": "Configuration, discovery, and data management services",
            "pap_role": "Data abstraction and configuration management",
            "components": data_components,
            "endpoints": data_endpoints,
            "component_count": len(data_components)
        }
    
    async def _discover_web_layer(self) -> Dict[str, Any]:
        """Discover complete web layer components using filesystem scanning"""
        
        web_components = {}
        web_endpoints = {}
        
        # Dynamically discover web layer components by scanning filesystem
        web_modules = await self._scan_for_modules_in_path("src/web")
        
        for module_path in web_modules:
            try:
                module = importlib.import_module(module_path)
                
                # Find all classes and functions that look like web components
                for name, obj in inspect.getmembers(module):
                    if not name.startswith('_'):
                        if inspect.isclass(obj):
                            # Web layer classes (template managers, renderers, etc.)
                            if any(keyword in name.lower() for keyword in ['template', 'manager', 'render', 'view', 'handler']):
                                web_components[name] = {
                                    "type": self._infer_component_type(name),
                                    "description": f"Auto-discovered web component: {name}",
                                    "methods": self._extract_methods(obj),
                                    "capabilities": self._infer_capabilities(name),
                                    "module": module_path
                                }
                        elif inspect.isfunction(obj):
                            # Web layer functions (render_, serve_, handle_)
                            if any(keyword in name.lower() for keyword in ['render_', 'serve_', 'handle_', 'process_']):
                                web_components[name] = {
                                    "type": "web_function",
                                    "description": f"Auto-discovered web function: {name}",
                                    "methods": [name],
                                    "capabilities": self._infer_capabilities(name),
                                    "module": module_path
                                }
                                
            except (ImportError, AttributeError, ModuleNotFoundError):
                pass
        
        # Generate web layer endpoints dynamically
        web_endpoints = await self._generate_web_endpoints(web_components)
        
        return {
            "name": "Web Layer",
            "description": "UI templates, static assets, and web interface management", 
            "pap_role": "Presentation layer abstraction",
            "components": web_components,
            "endpoints": web_endpoints,
            "component_count": len(web_components)
        }
    
    async def _discover_api_layer(self) -> Dict[str, Any]:
        """Discover complete API layer with full PAP architecture"""
        
        api_components = {}
        api_endpoints = {}
        
        # Dynamically discover API layer components by scanning filesystem
        api_modules = await self._scan_for_modules_in_path("src/api")
        
        for module_path in api_modules:
            try:
                module = importlib.import_module(module_path)
                
                # Find all classes that look like API components
                for name, obj in inspect.getmembers(module):
                    if not name.startswith('_') and inspect.isclass(obj):
                        # API layer classes (controllers, providers, orchestrators)
                        if any(keyword in name.lower() for keyword in ['controller', 'provider', 'orchestrator', 'auth', 'api']):
                            api_components[name] = {
                                "type": self._infer_component_type(name),
                                "description": f"Auto-discovered API component: {name}",
                                "methods": self._extract_methods(obj),
                                "capabilities": self._infer_capabilities(name),
                                "module": module_path,
                                "layer": self._infer_layer_from_name(name)
                            }
                            
            except (ImportError, AttributeError, ModuleNotFoundError):
                pass
        
        # Add live discovery system data if available
        if self.discovery:
            contexts = getattr(self.discovery, '_discovered_contexts', {})
            components = getattr(self.discovery, '_discovered_components', {})
            
            # Add discovered provider contexts
            providers = contexts.get('providers', {})
            for provider_name, provider_data in providers.items():
                api_components[f"{provider_name}_live_provider"] = {
                    "type": "cloud_provider",
                    "description": f"{provider_name.upper()} cloud integration provider (live discovery)",
                    "status": "authenticated" if provider_data.get('authenticated') else "available", 
                    "capabilities": provider_data.get('capabilities', []),
                    "layer": "provider",
                    "live_discovery": True
                }
            
            # Add auto-discovery system itself
            api_components["auto_discovery_system"] = {
                "type": "discovery_orchestrator",
                "description": "Live component auto-discovery and registration system",
                "methods": self._extract_methods(self.discovery),
                "capabilities": ["component_discovery", "auto_registration", "architecture_compliance"],
                "layer": "orchestrator"
            }
        
        # Generate API layer endpoints dynamically
        api_endpoints = await self._generate_api_endpoints(api_components)
        
        # Add discovered provider endpoints (exclude orchestrators)
        if self.discovery:
            contexts = getattr(self.discovery, '_discovered_contexts', {})
            providers = contexts.get('providers', {})
            
            for provider_name in providers.keys():
                # Skip if this is actually an orchestrator disguised as a provider
                if 'orchestrator' not in provider_name.lower():
                    api_endpoints[f"/api/{provider_name}/auth"] = {
                        "method": "POST",
                        "summary": f"{provider_name.upper()} Authentication",
                        "description": f"Authenticate with {provider_name} provider (auto-discovered)",
                        "layer": "api", 
                        "component": f"{provider_name}_controller",
                        "auto_discovered": True
                    }
        
        return {
            "name": "API Layer",
            "description": "REST APIs, auto-discovery, and cloud provider integrations",
            "pap_role": "API abstraction with autonomous component discovery",
            "components": api_components,
            "endpoints": api_endpoints,
            "component_count": len(api_components)
        }
    
    async def _discover_architecture_components(self) -> Dict[str, Any]:
        """Discover complete Provider-Abstraction-Pattern architecture components"""
        
        architecture_layers = {
            "routes": {},
            "controllers": {},
            "orchestrators": {}, 
            "providers": {},
            "middleware": {},
            "executors": {}
        }
        
        # Routes discovery from FastAPI app
        for route in self.app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                route_info = {
                    "path": route.path,
                    "methods": list(route.methods) if hasattr(route.methods, '__iter__') else ['GET'],
                    "name": getattr(route, 'name', 'unnamed'),
                    "layer": "route"
                }
                architecture_layers["routes"][route.path] = route_info
        
        # Also discover route files in the codebase
        await self._discover_route_files(architecture_layers)
        
        # Controllers discovery - direct filesystem scan
        await self._discover_pap_components("controllers", architecture_layers)
        
        # Providers discovery - direct filesystem scan
        await self._discover_pap_components("providers", architecture_layers)
        
        # Middleware discovery - direct filesystem scan
        await self._discover_pap_components("middleware", architecture_layers)
        
        # Executors discovery - direct filesystem scan
        await self._discover_pap_components("executors", architecture_layers)
        
        # Orchestrators discovery
        try:
            # Look for orchestrators in the orchestrators directory
            orchestrator_path = Path("src/api/orchestrators")
            if orchestrator_path.exists():
                for orch_file in orchestrator_path.rglob("*.py"):
                    if orch_file.name != "__init__.py":
                        module_path = str(orch_file).replace("/", ".").replace(".py", "")
                        try:
                            module = importlib.import_module(module_path)
                            for name, obj in inspect.getmembers(module, inspect.isclass):
                                if "orchestrator" in name.lower():
                                    architecture_layers["orchestrators"][name] = {
                                        "class_name": name,
                                        "module": module_path,
                                        "methods": self._extract_methods(obj),
                                        "layer": "orchestrator"
                                    }
                        except ImportError:
                            pass
        except Exception:
            pass
        
        return architecture_layers
    
    async def _discover_pap_components(self, component_type: str, architecture_layers: Dict[str, Any]):
        """Discover Provider-Abstraction-Pattern components by type"""
        component_path = Path(f"src/api/{component_type}")
        
        if not component_path.exists():
            return
            
        # Keywords to identify each component type
        type_keywords = {
            "controllers": ["controller"],
            "providers": ["provider", "auth"],
            "orchestrators": ["orchestrator"],
            "middleware": ["middleware"],
            "executors": ["executor"]
        }
        
        keywords = type_keywords.get(component_type, [component_type.rstrip('s')])
        
        # Scan all Python files in the component directory
        for py_file in component_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            # Convert file path to module path
            try:
                relative_path = py_file.relative_to(Path("src"))
                module_path = f"src.{str(relative_path.with_suffix('')).replace('/', '.')}"
                
                module = importlib.import_module(module_path)
                
                # Find all classes matching the component type
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if not name.startswith('_') and any(keyword in name.lower() for keyword in keywords):
                        # Extract methods and capabilities
                        methods = self._extract_methods(obj)
                        
                        architecture_layers[component_type][name] = {
                            "class_name": name,
                            "module": module_path,
                            "methods": methods,
                            "method_count": len(methods),
                            "layer": component_type.rstrip('s'),  # Remove plural
                            "file_path": str(py_file),
                            "capabilities": self._infer_capabilities(name)
                        }
                        
            except (ImportError, AttributeError, ModuleNotFoundError, ValueError) as e:
                # Skip files that can't be imported
                continue
    
    async def _discover_route_files(self, architecture_layers: Dict[str, Any]):
        """Discover route files by scanning the routes directory"""
        try:
            routes_path = Path("src/api/routes")
            if routes_path.exists():
                # Scan for Python files in routes directory
                for route_file in routes_path.rglob("*.py"):
                    if route_file.name != "__init__.py":
                        # Convert to module path and try to import
                        relative_path = route_file.relative_to(Path("src/api"))
                        module_path = f"src.api.{str(relative_path.with_suffix('')).replace('/', '.')}"
                        
                        try:
                            module = importlib.import_module(module_path)
                            route_info = {
                                "file_path": str(route_file),
                                "module_path": module_path,
                                "functions": [],
                                "layer": "route_file"
                            }
                            
                            # Find all functions that might be route handlers
                            for name, func in inspect.getmembers(module, inspect.isfunction):
                                if not name.startswith('_'):
                                    route_info["functions"].append(name)
                            
                            if route_info["functions"]:
                                architecture_layers["routes"][f"route_file_{route_file.stem}"] = route_info
                        
                        except (ImportError, AttributeError, ModuleNotFoundError):
                            pass
        except Exception:
            pass
    
    def _extract_methods(self, obj) -> List[str]:
        """Extract business-relevant public methods from an object or class (filter out infrastructure)"""
        if obj is None:
            return []
        
        try:
            if inspect.isclass(obj):
                methods = [name for name, _ in inspect.getmembers(obj, predicate=inspect.isfunction)
                          if not name.startswith('_')]
            else:
                methods = [name for name, _ in inspect.getmembers(obj, predicate=inspect.ismethod) 
                          if not name.startswith('_')]
            
            # Filter to business-relevant methods only
            return self._filter_business_methods(methods, obj.__name__ if hasattr(obj, '__name__') else 'unknown')
        except Exception:
            return []
    
    async def _scan_for_modules_in_path(self, path: str) -> List[str]:
        """Scan filesystem for Python modules in any directory path, excluding problematic directories"""
        modules = []
        
        # Directories to exclude from scanning (avoid problematic imports)
        exclude_patterns = [
            'node_modules', 'venv', '__pycache__', '.git', '.pytest_cache',
            'build', 'dist', 'native/build', 'native/desktop', 'electron',
            'deps', 'vendor', 'site-packages'
        ]
        
        try:
            base_path = Path(path)
            if base_path.exists():
                # Scan all Python files recursively, excluding problematic directories
                for py_file in base_path.rglob("*.py"):
                    # Skip __init__.py files
                    if py_file.name == "__init__.py":
                        continue
                        
                    # Check if the file is in any excluded directory
                    path_parts = py_file.parts
                    if any(exclude_pattern in str(py_file) for exclude_pattern in exclude_patterns):
                        continue
                    
                    # Convert file path to module path
                    try:
                        relative_path = py_file.relative_to(Path("."))
                        module_path = str(relative_path.with_suffix("")).replace("/", ".")
                        modules.append(module_path)
                    except ValueError:
                        # Skip files outside current directory
                        continue
        except Exception:
            pass
        return modules
    
    def _infer_component_type(self, name: str) -> str:
        """Infer component type from class/function name"""
        name_lower = name.lower()
        
        if "controller" in name_lower:
            return "controller"
        elif "orchestrator" in name_lower:
            return "orchestrator"
        elif "provider" in name_lower or "auth" in name_lower:
            return "provider"
        elif "middleware" in name_lower:
            return "middleware"
        elif "executor" in name_lower:
            return "executor"
        elif "config" in name_lower or "loader" in name_lower:
            return "configuration_provider"
        elif "template" in name_lower or "render" in name_lower:
            return "template_provider"
        elif "discovery" in name_lower:
            return "discovery_provider"
        elif "feature" in name_lower or "gate" in name_lower:
            return "feature_provider"
        else:
            return "component"
    
    def _infer_capabilities(self, name: str) -> List[str]:
        """Infer capabilities from class/function name"""
        name_lower = name.lower()
        capabilities = []
        
        # Capability inference based on name patterns
        capability_mapping = {
            "auth": ["authentication", "authorization"],
            "gcp": ["gcp_integration", "cloud_provider"],
            "aws": ["aws_integration", "cloud_provider"],
            "k8s": ["kubernetes_integration", "container_orchestration"],
            "config": ["configuration_management", "settings"],
            "discovery": ["component_discovery", "auto_detection"],
            "template": ["template_rendering", "ui_generation"],
            "feature": ["feature_flags", "capability_gates"],
            "controller": ["business_logic", "request_handling"],
            "orchestrator": ["workflow_coordination", "process_orchestration"],
            "provider": ["service_integration", "external_api"],
            "middleware": ["cross_cutting_concerns", "request_processing"],
            "executor": ["command_execution", "operation_execution"]
        }
        
        for keyword, caps in capability_mapping.items():
            if keyword in name_lower:
                capabilities.extend(caps)
        
        return capabilities if capabilities else ["general_capability"]
    
    def _is_internal_class(self, name: str) -> bool:
        """Check if a class name represents an internal/infrastructure class"""
        internal_patterns = [
            'apex',  # APEXConfigLoader and similar
            'base',  # Base classes (unless they're actual business components)
            'helper', 'util', 'manager', 'loader'
        ]
        
        name_lower = name.lower()
        
        # Skip APEX-prefixed classes (internal infrastructure)
        if name_lower.startswith('apex'):
            return True
            
        # Skip other internal patterns for config/infrastructure classes
        for pattern in internal_patterns:
            if pattern in name_lower and 'config' in name_lower:
                return True
                
        return False
    
    def _is_infrastructure_class(self, name: str, obj) -> bool:
        """Check if a class is pure infrastructure vs business component"""
        name_lower = name.lower()
        
        # Infrastructure class patterns
        infrastructure_indicators = [
            ('loader' in name_lower and 'config' in name_lower),  # Config loaders
            ('manager' in name_lower and not any(biz in name_lower for biz in ['license', 'auth', 'provider'])),
            name_lower.startswith('apex'),  # APEX infrastructure
            name_lower.endswith('helper'),
            name_lower.endswith('util'),
        ]
        
        return any(infrastructure_indicators)
    
    def _is_business_function(self, name: str) -> bool:
        """Check if a function represents a business capability vs internal utility"""
        name_lower = name.lower()
        
        # Business function indicators
        business_indicators = [
            'get_config',  # Main config access
            'get_feature_status',  # Feature gates
            'get_database_config_for_env',  # Environment-specific DB config
        ]
        
        # Skip internal utility functions
        internal_functions = [
            'get_logger', 'get_instance', 'get_class', 'get_module',
            'load_config', 'load_file', 'load_module',  # Low-level loaders
        ]
        
        if name in business_indicators:
            return True
            
        if name in internal_functions:
            return False
            
        # General business function patterns
        return any(pattern in name_lower for pattern in ['config', 'feature', 'database']) and \
               not any(util in name_lower for util in ['helper', 'util', 'internal'])
    
    def _generate_hierarchical_tags(self, path: str, component: str, layer: str) -> List[str]:
        """Generate hierarchical tags using hardcoded PAP structure with discovered sub-categories"""
        
        # HARDCODED TOP-LEVEL LAYERS
        if layer == "data":
            # Data layer sub-organization
            if "config" in path.lower():
                return ["📊 Data / Configuration"]
            elif "discovery" in path.lower():
                return ["📊 Data / Discovery"]
            elif "feature" in path.lower():
                return ["📊 Data / Feature Gates"]
            else:
                return ["📊 Data Layer"]
                
        elif layer == "web":
            # Web layer sub-organization
            if "static" in path.lower():
                return ["🌐 Web / Assets"]
            else:
                return ["🌐 Web / Interface"]
                
        elif layer == "api":
            # API layer with dynamic sub-categories but keeping structure
            path_parts = path.strip('/').split('/')
            if len(path_parts) >= 2 and path_parts[0] == 'api':
                provider_or_component = path_parts[1]
                readable_name = provider_or_component.replace('_', ' ').title()
                return [f"⚡ API / {readable_name}"]
            else:
                return ["⚡ API Layer"]
                
        # HARDCODED PAP ARCHITECTURAL LAYERS
        elif layer == "route":
            return ["🎯 Routes"]
        elif layer == "controller":
            return ["🏛️ Controllers"]
        elif layer == "orchestrator":
            return ["🔧 Orchestrators"]
        elif layer == "provider":
            # Auto-discover provider sub-categories
            if "gcp" in component.lower():
                return ["🔗 Providers / GCP"]
            elif "aws" in component.lower():
                return ["🔗 Providers / AWS"]
            elif "auth" in component.lower():
                return ["🔗 Providers / Auth"]
            else:
                return ["🔗 Providers"]
        elif layer == "middleware":
            return ["🛡️ Middleware"]
        elif layer == "executor":
            return ["⚙️ Executors"]
        else:
            # Fallback
            layer_name = layer.title().replace('_', ' ')
            return [f"{layer_name}"]
    
    def _infer_layer_from_name(self, name: str) -> str:
        """Infer Provider-Abstraction-Pattern layer from component name"""
        name_lower = name.lower()
        
        if "route" in name_lower:
            return "route"
        elif "controller" in name_lower:
            return "controller"
        elif "orchestrator" in name_lower:
            return "orchestrator"
        elif "provider" in name_lower or "auth" in name_lower:
            return "provider"
        elif "middleware" in name_lower:
            return "middleware"
        elif "executor" in name_lower:
            return "executor"
        else:
            return "component"
    
    
    def _infer_capabilities(self, name: str) -> List[str]:
        """Infer capabilities from class/function name"""
        name_lower = name.lower()
        capabilities = []
        
        # Capability inference based on name patterns
        capability_mapping = {
            "auth": ["authentication", "authorization"],
            "gcp": ["gcp_integration", "cloud_provider"],
            "aws": ["aws_integration", "cloud_provider"],
            "k8s": ["kubernetes_integration", "container_orchestration"],
            "config": ["configuration_management", "settings"],
            "discovery": ["component_discovery", "auto_detection"],
            "template": ["template_rendering", "ui_generation"],
            "feature": ["feature_flags", "capability_gates"],
            "controller": ["business_logic", "request_handling"],
            "orchestrator": ["workflow_coordination", "process_orchestration"],
            "provider": ["service_integration", "external_api"],
            "middleware": ["cross_cutting_concerns", "request_processing"],
            "executor": ["command_execution", "operation_execution"]
        }
        
        for keyword, caps in capability_mapping.items():
            if keyword in name_lower:
                capabilities.extend(caps)
        
        return capabilities if capabilities else ["general_capability"]
    
    def _infer_layer_from_name(self, name: str) -> str:
        """Infer Provider-Abstraction-Pattern layer from component name"""
        name_lower = name.lower()
        
        if "route" in name_lower:
            return "route"
        elif "controller" in name_lower:
            return "controller"
        elif "orchestrator" in name_lower:
            return "orchestrator"
        elif "provider" in name_lower or "auth" in name_lower:
            return "provider"
        elif "middleware" in name_lower:
            return "middleware"
        elif "executor" in name_lower:
            return "executor"
        else:
            return "component"
    
    def _filter_business_methods(self, methods: List[str], component_name: str) -> List[str]:
        """Filter methods to show all relevant capabilities including infrastructure"""
        
        # Important infrastructure methods that SHOULD be shown in documentation
        infrastructure_methods = {
            # Base class registry/wiring infrastructure
            'set_provider_registry', 'set_middleware_registry', 'set_executor_registry', 
            'set_websocket_manager', 'set_controller_registry',
            
            # Logging/monitoring infrastructure
            'broadcast_message', 'log_action', 'log_result', 'log_step', 'log_detail',
            
            # Generic workflow/orchestration infrastructure
            'apply_middleware', 'compose_workflow', 'compose_workflow_with_safety', 
            'execute_with_safety', 'get_executor', 'get_middleware', 'get_provider', 'orchestrate',
            
            # Generic filesystem/storage infrastructure  
            'normalize_path', 'create_directory', 'delete_file', 'move_file', 'copy_file',
            'stream_file', 'get_filename', 'get_file_size', 'filter_files', 'list_files',
            'read_file', 'write_file', 'exists', 'get_metadata',
            
            # Generic validation/safety infrastructure
            'validate_command', 'sanitize_input', 'check_permissions', 'validate_input',
            'validate_response', 'handle_error', 'parse_response',
            
            # Generic command execution infrastructure
            'execute_command', 'run_command', 'parse_output', 'handle_timeout',
            
            # Generic configuration/setup infrastructure
            'load_config', 'save_config', 'get_config', 'set_config', 'initialize',
        }
        
        # Only exclude truly internal/private methods
        excluded_methods = {
            '__init__', '__del__', '__str__', '__repr__', '__dict__', '__class__',
            '__module__', '__doc__', '__annotations__'
        }
        
        filtered_methods = []
        
        for method in methods:
            # Include ALL methods except truly private/internal ones
            if method not in excluded_methods and not method.startswith('__'):
                # Show both infrastructure methods AND business methods
                if (method in infrastructure_methods or 
                    self._is_business_method(method, component_name) or
                    self._is_infrastructure_method(method)):
                    filtered_methods.append(method)
        
        return filtered_methods
    
    def _is_business_method(self, method: str, component_name: str) -> bool:
        """Determine if a method represents actual business functionality vs infrastructure"""
        
        method_lower = method.lower()
        component_lower = component_name.lower()
        
        # Abstract business capability patterns (not provider-specific)
        business_patterns = [
            # Authentication & Authorization patterns
            'authenticate', 'login', 'logout', 'auth', 'sso', 'token',
            
            # Resource Management patterns (abstract CRUD)
            'create', 'delete', 'update', 'get', 'list', 'describe', 'show',
            'deploy', 'start', 'stop', 'restart', 'scale', 'resize',
            
            # Connection & Context Management patterns
            'connect', 'disconnect', 'switch', 'activate', 'deactivate',
            
            # Capability Management patterns (abstract)
            'generate_', 'validate_', 'get_status', 'deactivate_',
            
            # Orchestration patterns (abstract)
            'orchestrate_',
            
            # Context/Environment patterns (abstract)
            'get_cluster', 'switch_', 'get_projects', 'get_contexts'
        ]
        
        # Check if method matches abstract business patterns
        for pattern in business_patterns:
            if pattern in method_lower or (pattern.endswith('_') and method_lower.startswith(pattern)):
                return True
        
        # Abstract component capability patterns (not provider-specific)
        if 'auth' in component_lower:
            return any(word in method_lower for word in ['login', 'profile', 'account', 'credential', 'session'])
        elif 'controller' in component_lower:
            return any(word in method_lower for word in ['handle', 'process', 'manage', 'control', 'execute'])
        elif 'orchestrator' in component_lower:
            return method_lower.startswith('orchestrate_') or 'workflow' in method_lower
        elif 'provider' in component_lower:
            return any(word in method_lower for word in ['connect', 'resource', 'service', 'operation', 'request'])
        elif 'executor' in component_lower:
            return any(word in method_lower for word in ['execute', 'run', 'command', 'operation'])
        
        return False
    
    def _is_infrastructure_method(self, method: str) -> bool:
        """Identify infrastructure methods by abstract patterns"""
        method_lower = method.lower()
        
        # Abstract infrastructure method patterns
        infrastructure_patterns = [
            # Registry/wiring patterns
            'set_', 'register_', 'wire_', 'bind_',
            
            # Logging/monitoring patterns
            'broadcast_', 'log_', 'emit_', 'track_',
            
            # Workflow/orchestration patterns
            'apply_', 'compose_', 'execute_with_', 'orchestrate',
            
            # Filesystem/storage patterns
            'normalize_', 'filter_', 'stream_', 'get_filename', 'get_file_size', 'exists', 'get_metadata',
            
            # Validation/safety patterns
            'validate_', 'sanitize_', 'check_', 'handle_', 'parse_',
            
            # Command execution patterns
            'run_', 'execute_', 'timeout',
            
            # Configuration patterns
            'load_', 'save_', 'initialize'
        ]
        
        # Check if method matches any infrastructure pattern
        for pattern in infrastructure_patterns:
            if pattern in method_lower or (pattern.endswith('_') and method_lower.startswith(pattern)):
                return True
        
        return False
    
    async def _generate_data_endpoints(self, data_components: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data layer endpoints from discovered components"""
        endpoints = {}
        
        # Always include core data endpoints
        endpoints["/api/data/config"] = {
            "method": "GET",
            "summary": "System Configuration",
            "description": "Get complete system configuration across all providers",
            "layer": "data",
            "component": "config_system"
        }
        
        endpoints["/api/data/discovery"] = {
            "method": "GET",
            "summary": "Discovery Results", 
            "description": "Get autonomous discovery results and inferred contexts",
            "layer": "data",
            "component": "context_discovery"
        }
        
        # Generate endpoints from discovered components
        for component_name, component_info in data_components.items():
            component_type = component_info.get('type', 'unknown')
            
            if 'config' in component_name.lower():
                endpoints[f"/api/data/{component_name.lower()}"] = {
                    "method": "GET",
                    "summary": f"{component_name} Access",
                    "description": f"Access {component_name} data and configuration",
                    "layer": "data",
                    "component": component_name
                }
                
            elif 'feature' in component_name.lower():
                endpoints[f"/api/data/{component_name.lower()}"] = {
                    "method": "GET", 
                    "summary": f"{component_name} Status",
                    "description": f"Get {component_name} status and configuration",
                    "layer": "data",
                    "component": component_name
                }
                
        return endpoints
    
    async def _generate_web_endpoints(self, web_components: Dict[str, Any]) -> Dict[str, Any]:
        """Generate web layer endpoints from discovered components"""
        endpoints = {}
        
        # Always include core web endpoints
        endpoints["/"] = {
            "method": "GET",
            "summary": "Main Web Interface",
            "description": "Primary web application with dynamic template rendering",
            "layer": "web",
            "component": "web_interface"
        }
        
        endpoints["/static/{path:path}"] = {
            "method": "GET",
            "summary": "Static Assets",
            "description": "CSS, JavaScript, images and static resources",
            "layer": "web",
            "component": "static_handler"
        }
        
        # Generate endpoints from discovered web components
        for component_name, component_info in web_components.items():
            if 'template' in component_name.lower():
                endpoints[f"/templates/{component_name.lower()}"] = {
                    "method": "GET",
                    "summary": f"{component_name} Templates",
                    "description": f"Access {component_name} template rendering",
                    "layer": "web",
                    "component": component_name
                }
                
            elif 'render' in component_name.lower():
                endpoints[f"/render/{component_name.lower()}"] = {
                    "method": "POST",
                    "summary": f"{component_name} Rendering",
                    "description": f"Render content using {component_name}",
                    "layer": "web",
                    "component": component_name
                }
                
        return endpoints
    
    async def _generate_api_endpoints(self, api_components: Dict[str, Any]) -> Dict[str, Any]:
        """Generate API layer endpoints from discovered components"""
        endpoints = {}
        
        # Always include core API endpoints
        endpoints["/api/status"] = {
            "method": "GET",
            "summary": "System Status",
            "description": "Complete system health and architecture status",
            "layer": "api",
            "component": "system_status"
        }
        
        endpoints["/api/architecture"] = {
            "method": "GET",
            "summary": "Architecture Discovery",
            "description": "Complete Provider-Abstraction-Pattern architecture discovery",
            "layer": "api",
            "component": "architecture_discovery"
        }
        
        # Generate endpoints from discovered API components
        for component_name, component_info in api_components.items():
            component_type = component_info.get('type', 'unknown')
            
            if 'controller' in component_name.lower():
                # Controller endpoints
                base_name = component_name.lower().replace('controller', '')
                if base_name:
                    endpoints[f"/api/{base_name}/status"] = {
                        "method": "GET",
                        "summary": f"{component_name} Status",
                        "description": f"Get status from {component_name}",
                        "layer": "controller",  # FIXED: Use controller layer
                        "component": component_name
                    }
                    
                    endpoints[f"/api/{base_name}/execute"] = {
                        "method": "POST",
                        "summary": f"{component_name} Execute",
                        "description": f"Execute operations via {component_name}",
                        "layer": "controller",  # FIXED: Use controller layer
                        "component": component_name
                    }
                    
            elif 'auth' in component_name.lower():
                # Authentication provider endpoints
                base_name = component_name.lower().replace('auth', '').replace('provider', '')
                if base_name:
                    endpoints[f"/api/{base_name}/auth"] = {
                        "method": "POST",
                        "summary": f"{component_name} Authentication",
                        "description": f"Authenticate using {component_name}",
                        "layer": "provider",  # FIXED: Use provider layer
                        "component": component_name
                    }
                    
            elif 'orchestrator' in component_name.lower():
                # Orchestrator endpoints - properly separate provider and orchestrator
                component_lower = component_name.lower()
                
                # Extract provider name and add underscore
                if component_lower.endswith('orchestrator'):
                    provider_name = component_lower[:-len('orchestrator')]
                elif component_lower.endswith('authorchestragor'):
                    # Handle edge case where 'auth' might be mixed in
                    provider_name = component_lower.replace('auth', '').replace('orchestrator', '')
                else:
                    provider_name = component_lower.replace('orchestrator', '')
                
                # Clean up any remaining 'auth' parts
                provider_name = provider_name.replace('auth', '').strip('_')
                
                if provider_name:
                    # Use underscore to separate provider and orchestrator
                    endpoint_path = f"/api/{provider_name}_orchestrator/orchestrate"
                    endpoints[endpoint_path] = {
                        "method": "POST",
                        "summary": f"{component_name} Orchestration",
                        "description": f"Orchestrate workflows via {component_name}",
                        "layer": "orchestrator",  # FIXED: Use orchestrator layer
                        "component": component_name
                    }
                    
        return endpoints
    
    async def _register_discovered_endpoints(self):
        """Register all discovered endpoints as actual FastAPI routes"""
        try:
            # Discover architecture to get all endpoints
            architecture = await self.discover_complete_architecture()
            
            # Register data layer endpoints
            data_endpoints = architecture.get("data_layer", {}).get("endpoints", {})
            for path, endpoint_info in data_endpoints.items():
                self._register_endpoint(path, endpoint_info)
            
            # Register web layer endpoints  
            web_endpoints = architecture.get("web_layer", {}).get("endpoints", {})
            for path, endpoint_info in web_endpoints.items():
                self._register_endpoint(path, endpoint_info)
                
            # Register API layer endpoints
            api_endpoints = architecture.get("api_layer", {}).get("endpoints", {})
            for path, endpoint_info in api_endpoints.items():
                if not path.startswith("/api/architecture"):  # Skip already registered
                    self._register_endpoint(path, endpoint_info)
                    
        except Exception as e:
            print(f"Warning: Could not register discovered endpoints: {e}")
    
    def _register_endpoint(self, path: str, endpoint_info: Dict[str, Any]):
        """Register a single endpoint with FastAPI"""
        try:
            method = endpoint_info.get("method", "GET").lower()
            summary = endpoint_info.get("summary", "Auto-discovered endpoint")
            description = endpoint_info.get("description", "Dynamically discovered endpoint")
            component = endpoint_info.get("component", "unknown")
            layer = endpoint_info.get("layer", "unknown")
            
            # Create functional handler based on endpoint type
            async def endpoint_handler():
                return await self._handle_discovered_endpoint(path, method, component, layer)
            
            # Register with FastAPI based on method - include in schema with hierarchical tags
            tags = self._generate_hierarchical_tags(path, component, layer)
            
            if method == "get":
                self.app.get(path, summary=summary, description=description, tags=tags)(endpoint_handler)
            elif method == "post":
                self.app.post(path, summary=summary, description=description, tags=tags)(endpoint_handler)
            elif method == "put":
                self.app.put(path, summary=summary, description=description, tags=tags)(endpoint_handler)
            elif method == "delete":
                self.app.delete(path, summary=summary, description=description, tags=tags)(endpoint_handler)
                
        except Exception as e:
            # Skip endpoints that can't be registered (conflicts, etc.)
            pass
    
    async def _handle_discovered_endpoint(self, path: str, method: str, component: str, layer: str) -> Dict[str, Any]:
        """Handle discovered endpoints with functional implementations"""
        
        # Data layer endpoints
        if layer == "data":
            return await self._handle_data_endpoint(path, method, component)
            
        # Web layer endpoints  
        elif layer == "web":
            return await self._handle_web_endpoint(path, method, component)
            
        # API layer endpoints
        elif layer == "api":
            return await self._handle_api_endpoint(path, method, component)
            
        # Default handler
        return {
            "endpoint": path,
            "method": method.upper(),
            "component": component,
            "layer": layer,
            "status": "functional",
            "message": f"Auto-discovered and functional endpoint from {component}"
        }
    
    async def _handle_data_endpoint(self, path: str, method: str, component: str) -> Dict[str, Any]:
        """Handle data layer endpoints with real functionality"""
        
        if "/api/data/config" in path:
            # Return actual system configuration
            try:
                from src.data.config_loader import get_config
                config = get_config()
                return {
                    "endpoint": path,
                    "layer": "data",
                    "component": "config_system",
                    "data": {
                        "config_loaded": config is not None,
                        "config_type": str(type(config).__name__) if config else None,
                        "timestamp": self._get_timestamp()
                    },
                    "status": "success"
                }
            except Exception as e:
                return self._error_response(path, "data", str(e))
                
        elif "/api/data/discovery" in path:
            # Return live discovery data
            if self.discovery:
                contexts = getattr(self.discovery, '_discovered_contexts', {})
                return {
                    "endpoint": path,
                    "layer": "data", 
                    "component": "context_discovery",
                    "data": {
                        "providers": list(contexts.get('providers', {}).keys()),
                        "environments_count": len(contexts.get('environments', [])),
                        "environments": [env.get('name') for env in contexts.get('environments', [])[:10]],  # First 10
                        "discovery_timestamp": contexts.get('discovery_timestamp')
                    },
                    "status": "success"
                }
            else:
                return self._error_response(path, "data", "Discovery system not available")
                
        elif "feature" in component.lower():
            # Return feature gates status
            return {
                "endpoint": path,
                "layer": "data",
                "component": component,
                "data": {
                    "feature_gates": ["auto_discovery", "filesystem_scanning", "provider_abstraction"],
                    "all_enabled": True,
                    "timestamp": self._get_timestamp()
                },
                "status": "success"
            }
            
        return self._default_data_response(path, component)
    
    async def _handle_web_endpoint(self, path: str, method: str, component: str) -> Dict[str, Any]:
        """Handle web layer endpoints with real functionality"""
        
        if path == "/":
            return {
                "endpoint": path,
                "layer": "web",
                "component": "web_interface", 
                "content_type": "text/html",
                "html": "<h1>🌊 WARPCORE Web Interface</h1><p>Auto-discovered web layer</p>",
                "status": "success"
            }
            
        elif "/static/" in path:
            return {
                "endpoint": path,
                "layer": "web",
                "component": "static_handler",
                "message": "Static asset handler - would serve files from static directory",
                "status": "success"
            }
            
        elif "/templates/" in path:
            return {
                "endpoint": path,
                "layer": "web",
                "component": component,
                "data": {
                    "template_engine": "auto_discovered",
                    "available_templates": ["base.html", "dashboard.html", "components.html"],
                    "rendering_capability": True
                },
                "status": "success"
            }
            
        return self._default_web_response(path, component)
    
    async def _handle_api_endpoint(self, path: str, method: str, component: str) -> Dict[str, Any]:
        """Handle API layer endpoints with real functionality"""
        
        if "/api/status" in path:
            # Return comprehensive system status
            architecture = await self.discover_complete_architecture()
            return {
                "endpoint": path,
                "layer": "api",
                "component": "system_status",
                "data": {
                    "system": "WARPCORE",
                    "version": "3.0.0",
                    "architecture_compliant": True,
                    "discovery_active": self.discovery is not None,
                    "total_components": architecture.get('discovery_metadata', {}).get('total_components', 0),
                    "total_endpoints": architecture.get('discovery_metadata', {}).get('total_endpoints', 0),
                    "layers_active": 3,
                    "timestamp": self._get_timestamp()
                },
                "status": "operational"
            }
            
        elif "/auth" in path:
            # Handle authentication endpoints
            provider = self._extract_provider_from_path(path)
            return {
                "endpoint": path,
                "layer": "api",
                "component": component,
                "data": {
                    "provider": provider,
                    "auth_available": True,
                    "method": "auto_discovered",
                    "message": f"Authentication handler for {provider} provider"
                },
                "status": "ready"
            }
            
        elif "/execute" in path:
            # Handle execution endpoints
            provider = self._extract_provider_from_path(path)
            return {
                "endpoint": path,
                "layer": "api", 
                "component": component,
                "data": {
                    "provider": provider,
                    "execution_capability": True,
                    "supported_operations": ["status", "list", "create", "delete"],
                    "message": f"Execution handler for {provider} provider"
                },
                "status": "ready"
            }
            
        elif "/orchestrate" in path:
            # Handle orchestration endpoints
            provider = self._extract_provider_from_path(path)
            return {
                "endpoint": path,
                "layer": "api",
                "component": component,
                "data": {
                    "provider": provider,
                    "orchestration_capability": True,
                    "workflow_types": ["authentication", "deployment", "monitoring"],
                    "message": f"Workflow orchestration for {provider} provider"
                },
                "status": "ready"
            }
            
        return self._default_api_response(path, component)
    
    def _extract_provider_from_path(self, path: str) -> str:
        """Extract provider name from API path"""
        parts = path.split('/')
        for part in parts:
            if part in ['gcp', 'aws', 'kubernetes', 'k8s']:
                return part
        return "unknown"
    
    def _get_timestamp(self) -> float:
        """Get current timestamp"""
        import time
        return time.time()
    
    def _error_response(self, path: str, layer: str, error: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "endpoint": path,
            "layer": layer,
            "status": "error",
            "error": error,
            "timestamp": self._get_timestamp()
        }
    
    def _default_data_response(self, path: str, component: str) -> Dict[str, Any]:
        """Default data layer response"""
        return {
            "endpoint": path,
            "layer": "data",
            "component": component,
            "data": {
                "auto_discovered": True,
                "functional": True,
                "message": f"Data component {component} is operational"
            },
            "status": "success"
        }
    
    def _default_web_response(self, path: str, component: str) -> Dict[str, Any]:
        """Default web layer response"""
        return {
            "endpoint": path,
            "layer": "web",
            "component": component,
            "content": {
                "auto_discovered": True,
                "functional": True,
                "message": f"Web component {component} is operational"
            },
            "status": "success"
        }
    
    def _default_api_response(self, path: str, component: str) -> Dict[str, Any]:
        """Default API layer response"""
        return {
            "endpoint": path,
            "layer": "api",
            "component": component,
            "api": {
                "auto_discovered": True,
                "functional": True,
                "message": f"API component {component} is operational"
            },
            "status": "success"
        }
    
    def _serve_html_file(self, file_path: str) -> str:
        """Serve HTML file from docs directory"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return "<html><body><h1>Documentation not found</h1></body></html>"
    
    async def generate_compliant_spec(self) -> Dict[str, Any]:
        """Generate complete Provider-Abstraction-Pattern compliant OpenAPI spec"""
        
        architecture = await self.discover_complete_architecture()
        
        spec = {
            "openapi": "3.1.0",
            "info": {
                "title": "WARPCORE Compliant API",
                "version": "3.0.0", 
                "description": """
🌊 **WARPCORE Provider-Abstraction-Pattern Architecture**

Complete documentation of the full Provider-Abstraction-Pattern system with autonomous discovery.

## 📋 Architecture Overview:
- **🎯 Architecture Compliant**: Routes → Controllers → Orchestrators → Providers → Middleware → Executors
- **🔍 Auto-Discovery**: Zero-configuration component discovery and registration
- **⚡ Three Layers**: Data, Web, and API with complete separation of concerns

## 📊 Data Layer:
Configuration management, autonomous discovery, and feature gates

## 🌐 Web Layer: 
Template rendering, static assets, and presentation logic

## ⚡ API Layer:
REST APIs, cloud provider integrations, and business logic

## 🔧 PAP Components:
- **Routes**: HTTP endpoint definitions and request routing
- **Controllers**: Business logic orchestration and validation  
- **Orchestrators**: Complex workflow coordination
- **Providers**: Direct service integrations (GCP, AWS, K8s)
- **Middleware**: Cross-cutting concerns and safety gates
- **Executors**: Command execution with safety validation
                """,
                "contact": {
                    "name": "WARPCORE System",
                    "url": "https://github.com/warpcore"
                }
            },
            "servers": [
                {"url": "http://localhost:8000", "description": "Development server"}
            ],
            "paths": {},
            "components": {"schemas": {}},
            "tags": []
        }
        
        # Add comprehensive tags for organization - 3 high-level primitives first, then auto-discovered structure
        tags = [
            # High-level architectural layers (top-level) - MUST BE FIRST
            {"name": "📊 Data Layer", "description": "Configuration, discovery, and data management services"},
            {"name": "🌐 Web Layer", "description": "Templates, static assets, and presentation interfaces"},
            {"name": "⚡ API Layer", "description": "REST APIs, business logic, and system operations"}
        ]
        
        # Auto-discover additional tags from the discovered architecture
        discovered_tags = self._generate_discovered_tags(architecture)
        tags.extend(discovered_tags)
        spec["tags"] = tags
        
        # Generate endpoints for each layer
        await self._add_compliant_endpoints(spec, architecture)
        
        return spec
    
    def _generate_discovered_tags(self, architecture: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate hardcoded PAP layer structure with discovered content within each layer"""
        discovered_tags = []
        
        # Get discovered architecture components
        architecture_components = architecture.get("architecture_components", {})
        
        # HARDCODED PAP ARCHITECTURAL LAYERS UNDER API LAYER
        # All PAP components belong under API layer with context-based sub-directories
        
        # Controllers (organized by context: core, gcp, license, filesystem)
        controllers_count = len(architecture_components.get("controllers", {}))
        discovered_tags.append({
            "name": "🏛️ Controllers", 
            "description": f"Business logic coordination ({controllers_count} discovered) - Core, GCP, License, Filesystem"
        })
        
        # Orchestrators (organized by context: core, gcp, license, filesystem) 
        orchestrators_count = len(architecture_components.get("orchestrators", {}))
        discovered_tags.append({
            "name": "🔧 Orchestrators",
            "description": f"Workflow orchestration ({orchestrators_count} discovered) - Core, GCP, License, Filesystem"
        })
        
        # Providers (organized by context: core, gcp, license, filesystem)
        providers_count = len(architecture_components.get("providers", {}))
        discovered_tags.append({
            "name": "🔗 Providers",
            "description": f"Service integrations ({providers_count} discovered) - Core, GCP, License, Filesystem"
        })
        
        # Middleware (organized by context: core, security, validation)
        middleware_count = len(architecture_components.get("middleware", {}))
        discovered_tags.append({
            "name": "🛡️ Middleware",
            "description": f"Cross-cutting concerns ({middleware_count} discovered) - Core, Security, Validation"
        })
        
        # Executors (organized by context: core, command, operation)
        executors_count = len(architecture_components.get("executors", {}))
        discovered_tags.append({
            "name": "⚙️ Executors",
            "description": f"Command execution ({executors_count} discovered) - Core, Command, Operation"
        })
        
        # Data layer auto-discovery (more comprehensive)
        data_layer = architecture.get("data_layer", {})
        data_components = data_layer.get("components", {})
        data_subcategories = set()
        
        for component_name in data_components.keys():
            if "config" in component_name.lower():
                data_subcategories.add("Configuration")
            elif "discovery" in component_name.lower():
                data_subcategories.add("Discovery")
            elif "feature" in component_name.lower():
                data_subcategories.add("Feature Gates")
            elif "environment" in component_name.lower() or "env" in component_name.lower():
                data_subcategories.add("Environment")
                
        for subcategory in sorted(data_subcategories):
            discovered_tags.append({
                "name": f"📊 Data / {subcategory}",
                "description": f"Data layer {subcategory.lower()} management"
            })
        
        # Web layer auto-discovery with Routes
        web_layer = architecture.get("web_layer", {})
        web_components = web_layer.get("components", {})
        web_subcategories = set(["Routes"])  # Always include Routes in Web layer
        
        for component_name in web_components.keys():
            if "template" in component_name.lower():
                web_subcategories.add("Templates")
            elif "static" in component_name.lower() or "asset" in component_name.lower():
                web_subcategories.add("Assets")
            elif "render" in component_name.lower():
                web_subcategories.add("Rendering")
            else:
                web_subcategories.add("Interface")
                
        for subcategory in sorted(web_subcategories):
            if subcategory == "Routes":
                discovered_tags.append({
                    "name": f"🌐 Web / Routes",
                    "description": f"HTTP routing logic mapping to API controllers - Core, GCP, License, Filesystem"
                })
            else:
                discovered_tags.append({
                    "name": f"🌐 Web / {subcategory}",
                    "description": f"Web layer {subcategory.lower()} services"
                })
        
        # API layer auto-discovery (by actual discovered providers)
        api_layer = architecture.get("api_layer", {})
        api_components = api_layer.get("components", {})
        api_subcategories = set()
        
        for component_name in api_components.keys():
            if "_live_provider" in component_name:
                # Extract provider name dynamically
                provider_name = component_name.replace("_live_provider", "").replace("_", " ").title()
                api_subcategories.add(provider_name)
            elif "controller" in component_name.lower():
                api_subcategories.add("System")
            elif "discovery" in component_name.lower():
                api_subcategories.add("Discovery")
                
        for subcategory in sorted(api_subcategories):
            discovered_tags.append({
                "name": f"⚡ API / {subcategory}",
                "description": f"API layer {subcategory.lower()} operations"
            })
        
        return discovered_tags
    
    async def _add_compliant_endpoints(self, spec: Dict[str, Any], architecture: Dict[str, Any]):
        """Add Provider-Abstraction-Pattern compliant endpoints organized by layer and component"""
        
        # Data Layer endpoints
        data_layer = architecture.get("data_layer", {})
        for endpoint, details in data_layer.get("endpoints", {}).items():
            spec["paths"][endpoint] = {
                details["method"].lower(): {
                    "summary": details["summary"],
                    "description": f"{details['description']} (Layer: {details['layer']})",
                    "responses": {
                        "200": {
                            "description": f"Success response from {details['component']}",
                            "content": {
                                "application/json": {
                                    "example": {"success": True, "layer": details['layer']}
                                }
                            }
                        }
                    },
                    "tags": ["📊 Data Layer"]
                }
            }
        
        # Web Layer endpoints  
        web_layer = architecture.get("web_layer", {})
        for endpoint, details in web_layer.get("endpoints", {}).items():
            spec["paths"][endpoint] = {
                details["method"].lower(): {
                    "summary": details["summary"],
                    "description": f"{details['description']} (Layer: {details['layer']})",
                    "responses": {
                        "200": {"description": f"Success response from {details['component']}"}
                    },
                    "tags": ["🌐 Web Layer"]
                }
            }
        
        # API Layer endpoints
        api_layer = architecture.get("api_layer", {}) 
        for endpoint, details in api_layer.get("endpoints", {}).items():
            method = details["method"].lower()
            spec["paths"][endpoint] = {
                method: {
                    "summary": details["summary"],
                    "description": f"{details['description']} (Layer: {details['layer']})",
                    "responses": {
                        "200": {
                            "description": f"Success response from {details['component']}",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "success": True, 
                                        "layer": details['layer'],
                                        "auto_discovered": details.get('auto_discovered', False)
                                    }
                                }
                            }
                        }
                    },
                    "tags": [
                        "⚡ API Layer" if not details.get('auto_discovered') 
                        else "🔍 Auto-Discovery"
                    ]
                }
            }
        
        # Add architecture component endpoints
        architecture_components = architecture.get("architecture_components", {})
        
        # Routes overview
        if architecture_components.get("routes"):
            spec["paths"]["/api/routes"] = {
                "get": {
                    "summary": "Routes Discovery",
                    "description": "Complete discovery of all HTTP routes in the architecture",
                    "responses": {
                        "200": {
                            "description": "All discovered routes",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "total_routes": len(architecture_components["routes"]),
                                        "routes": "Live route discovery results"
                                    }
                                }
                            }
                        }
                    },
                    "tags": ["🎯 Routes"]
                }
            }
        
        # Controllers overview
        if architecture_components.get("controllers"):
            spec["paths"]["/api/controllers"] = {
                "get": {
                    "summary": "Controllers Discovery", 
                    "description": "Complete discovery of all business logic controllers",
                    "responses": {
                        "200": {
                            "description": "All discovered controllers",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "total_controllers": len(architecture_components["controllers"]),
                                        "controllers": "Live controller discovery results"
                                    }
                                }
                            }
                        }
                    },
                    "tags": ["🏛️ Controllers"]
                }
            }
            
        # Orchestrators overview
        if architecture_components.get("orchestrators"):
            spec["paths"]["/api/orchestrators"] = {
                "get": {
                    "summary": "Orchestrators Discovery", 
                    "description": "Complete discovery of all workflow orchestrators",
                    "responses": {
                        "200": {
                            "description": "All discovered orchestrators",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "total_orchestrators": len(architecture_components["orchestrators"]),
                                        "orchestrators": "Live orchestrator discovery results"
                                    }
                                }
                            }
                        }
                    },
                    "tags": ["🔧 Orchestrators"]
                }
            }
            
        # Middleware overview
        if architecture_components.get("middleware"):
            spec["paths"]["/api/middleware"] = {
                "get": {
                    "summary": "Middleware Discovery", 
                    "description": "Complete discovery of all middleware components",
                    "responses": {
                        "200": {
                            "description": "All discovered middleware",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "total_middleware": len(architecture_components["middleware"]),
                                        "middleware": "Live middleware discovery results"
                                    }
                                }
                            }
                        }
                    },
                    "tags": ["🛡️ Middleware"]
                }
            }
            
        # Executors overview
        if architecture_components.get("executors"):
            spec["paths"]["/api/executors"] = {
                "get": {
                    "summary": "Executors Discovery", 
                    "description": "Complete discovery of all command executors",
                    "responses": {
                        "200": {
                            "description": "All discovered executors",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "total_executors": len(architecture_components["executors"]),
                                        "executors": "Live executor discovery results"
                                    }
                                }
                            }
                        }
                    },
                    "tags": ["⚙️ Executors"]
                }
            }
        
        # Providers overview
        if architecture_components.get("providers"):
            spec["paths"]["/api/providers"] = {
                "get": {
                    "summary": "Providers Discovery",
                    "description": "Complete discovery of all providers in the architecture",
                    "responses": {
                        "200": {
                            "description": "All discovered providers",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "total_providers": len(architecture_components["providers"]),
                                        "providers": "Live provider discovery results"
                                    }
                                }
                            }
                        }
                    },
                    "tags": ["🔗 Providers"]
                }
            }
    
    def get_working_scalar_html(self) -> str:
        """Generate Purfect Labs styled Scalar UI - dark theme with purple accents"""
        return """<!DOCTYPE html>
<html lang="en" class="scroll-smooth" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌊 WarpCop API Documentation - Provider-Abstraction-Pattern by PurfectLabs</title>
    <meta name="description" content="WarpCop by PurfectLabs - Enhanced Provider-Abstraction-Pattern API documentation with auto-discovery and hierarchical organization.">
    <meta name="theme-color" content="#8b5cf6">
    
    <!-- Fonts -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    
    <style>
        :root {
            /* Purfect Labs Dark Theme */
            --bg: #1e1f22;
            --bg-soft: #2b2d31;
            --text: #f2f3f5;
            --text-muted: #b5bac1;
            --surface: #313338;
            --surface-2: #383a40;
            --border: #3f4147;
            --accent: #8b5cf6;
            --accent-hover: #7c3aed;
            --success: #22c55e;
            --warning: #fbbf24;
            --danger: #ef4444;
            --info: #38bdf8;
            
            /* Typography */
            --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-display: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
            
            /* Glow effects */
            --glow-primary: 0 0 30px rgba(139, 92, 246, 0.5);
            --glow-soft: 0 0 15px rgba(139, 92, 246, 0.25);
        }
        
        body {
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, var(--bg) 0%, var(--bg-soft) 100%);
            font-family: var(--font-primary);
            color: var(--text);
            min-height: 100vh;
        }
        
        /* Header styling */
        .warpcore-header {
            background: rgba(49, 51, 56, 0.95);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }
        
        .warpcore-title {
            font-family: var(--font-display);
            font-size: 1.5rem;
            font-weight: 600;
            background: linear-gradient(135deg, var(--accent) 0%, #a78bfa 50%, #c084fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .warpcore-badge {
            font-size: 0.75rem;
            padding: 0.25rem 0.75rem;
            background: rgba(139, 92, 246, 0.1);
            color: var(--accent);
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-radius: 12px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .stats-bar {
            display: flex;
            gap: 2rem;
            margin-top: 1rem;
            font-size: 0.875rem;
            color: var(--text-muted);
        }
        
        .nav-links {
            display: flex;
            gap: 1.5rem;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
            font-size: 0.875rem;
        }
        
        .nav-link {
            color: var(--text-muted);
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            border: 1px solid transparent;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .nav-link:hover {
            color: var(--accent);
            border-color: rgba(139, 92, 246, 0.3);
            background: rgba(139, 92, 246, 0.05);
        }
        
        .nav-link.active {
            color: var(--accent);
            border-color: rgba(139, 92, 246, 0.5);
            background: rgba(139, 92, 246, 0.1);
        }
        
        .purfect-gradient-btn {
            background: linear-gradient(
                45deg,
                #00C8C8,  /* Purfect Labs teal */
                #FFD700,  /* Yellow addition */
                #FFB84D,  /* Purfect Labs amber */
                #A25AFF   /* Purfect Labs purple */
            ) !important;
            background-size: 200% 200%;
            animation: purfect-shift 3s ease infinite;
            color: white !important;
            border: none !important;
            font-weight: 600;
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        }
        
        .purfect-gradient-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(0, 200, 200, 0.4);
            animation-duration: 1.5s;
        }
        
        @keyframes purfect-shift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        /* Fix Scalar sidebar scrolling */
        [data-testid="sidebar"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100vh !important;
            overflow-y: auto !important;
            z-index: 1000 !important;
        }
        
        [data-testid="main-content"] {
            margin-left: 300px !important;
            height: 100vh !important;
            overflow-y: auto !important;
        }
        
        /* Alternative selectors for Scalar UI structure */
        .scalar-sidebar {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100vh !important;
            overflow-y: auto !important;
            z-index: 1000 !important;
        }
        
        .scalar-content {
            margin-left: 300px !important;
            height: 100vh !important;
            overflow-y: auto !important;
        }
        
        .stat-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .stat-number {
            color: var(--accent);
            font-weight: 600;
        }
        
        /* Scalar customization */
        #api-reference {
            --scalar-font: var(--font-primary);
            --scalar-font-code: var(--font-mono);
            
            /* Dark theme colors */
            --scalar-background-1: var(--bg);
            --scalar-background-2: var(--surface);
            --scalar-background-3: var(--surface-2);
            --scalar-background-accent: var(--accent);
            
            --scalar-color-1: var(--text);
            --scalar-color-2: var(--text-muted);
            --scalar-color-3: #6b7280;
            --scalar-color-accent: var(--accent);
            
            --scalar-border-color: var(--border);
            
            /* Buttons */
            --scalar-button-1: var(--accent);
            --scalar-button-1-hover: var(--accent-hover);
            
            /* Success/Error colors */
            --scalar-error-1: var(--danger);
            --scalar-success-1: var(--success);
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--surface);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--accent);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--accent-hover);
        }
        
        /* Glow effects for PAP layers */
        [data-testid*="tag-Data Layer"] {
            background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%) !important;
            box-shadow: var(--glow-soft) !important;
            border: none !important;
        }
        
        [data-testid*="tag-Api Layer"] {
            background: linear-gradient(135deg, var(--accent) 0%, #a78bfa 100%) !important;
            box-shadow: var(--glow-soft) !important;
            border: none !important;
        }
        
        [data-testid*="tag-Web Layer"] {
            background: linear-gradient(135deg, #10b981 0%, #34d399 100%) !important;
            box-shadow: var(--glow-soft) !important;
            border: none !important;
        }
        
        /* Loading animation */
        .loading-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 60vh;
            text-align: center;
        }
        
        .loading-spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(139, 92, 246, 0.1);
            border-top: 3px solid var(--accent);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 1rem;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .loading-text {
            font-family: var(--font-display);
            font-size: 1.25rem;
            color: var(--text-muted);
        }
    </style>
    
</head>
<body>
    <!-- Purfect Labs styled header -->
    <div class="warpcore-header">
        <div class="warpcore-title">
            🌊 WarpCop API Documentation
            <span class="warpcore-badge">PAP Compliant</span>
            <span class="warpcore-badge" style="background: rgba(56, 189, 248, 0.1); color: #38bdf8; border-color: rgba(56, 189, 248, 0.3);">by PurfectLabs</span>
        </div>
        <div class="stats-bar">
            <div class="stat-item">
                <i class="fas fa-cube" style="color: var(--accent);"></i>
                <span>Components: <span class="stat-number" id="component-count">19</span></span>
            </div>
            <div class="stat-item">
                <i class="fas fa-network-wired" style="color: var(--info);"></i>
                <span>Endpoints: <span class="stat-number" id="endpoint-count">13</span></span>
            </div>
            <div class="stat-item">
                <i class="fas fa-layer-group" style="color: var(--success);"></i>
                <span>Layers: <span class="stat-number">3</span></span>
            </div>
            <div class="stat-item">
                <i class="fas fa-check-circle" style="color: var(--success);"></i>
                <span>Auto-Discovery: <span class="stat-number" style="color: var(--success);">Active</span></span>
            </div>
        </div>
        
        <div class="nav-links">
            <a href="/docs/api/what-is-pap" class="nav-link purfect-gradient-btn" target="_blank">
                <i class="fas fa-layer-group"></i>
                What is PAP?
            </a>
            <a href="/docs/api/purfectlabs-philosophy" class="nav-link" target="_blank" style="color: #38bdf8; border-color: rgba(56, 189, 248, 0.3);">
                <i class="fas fa-heart"></i>
                UR Philosophy
            </a>
        </div>
    </div>
    
    <!-- Loading state -->
    <div id="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <div class="loading-text">🌊 Initializing WarpCop PAP Documentation by PurfectLabs...</div>
    </div>
    
    <!-- Scalar API Reference - using the data attribute method -->
    <script id="api-reference" data-url="/openapi.json" data-theme="purple"></script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference@1.24.11"></script>
    
    <script>
        console.log('🌊 WarpCop by PurfectLabs: Loading enhanced PAP API documentation...');
        
        // Load live stats
        fetch('/api/architecture')
            .then(response => response.json())
            .then(data => {
                document.getElementById('component-count').textContent = data.discovery_metadata?.total_components || '19';
                document.getElementById('endpoint-count').textContent = data.discovery_metadata?.total_endpoints || '13';
            })
            .catch(() => console.log('Using default stats'));
        
        // Hide loading after Scalar loads
        setTimeout(() => {
            const loading = document.getElementById('loading');
            if (loading) {
                loading.style.display = 'none';
            }
            console.log('✨ WarpCop by PurfectLabs: PAP Documentation loaded successfully!');
        }, 3000);
    </script>
</body>
</html>"""

    def setup_compliant_docs_routes(self):
        """Setup Provider-Abstraction-Pattern compliant documentation routes"""
        
        @self.app.get("/openapi.json", include_in_schema=False)
        async def get_compliant_spec():
            """Generate Provider-Abstraction-Pattern compliant OpenAPI specification"""
            return await self.generate_compliant_spec()
        
        @self.app.get("/docs", response_class=HTMLResponse, include_in_schema=False)
        async def get_compliant_docs():
            """Provider-Abstraction-Pattern Compliant Scalar API Documentation"""
            return self.get_working_scalar_html()
        
        @self.app.get("/api-docs", response_class=HTMLResponse, include_in_schema=False)
        async def get_api_docs():
            """Alternative compliant docs URL"""
            return self.get_working_scalar_html()
        
        # Add architecture component discovery endpoints
        @self.app.get("/api/architecture", include_in_schema=False)
        async def get_architecture():
            """Complete Provider-Abstraction-Pattern architecture discovery"""
            return await self.discover_complete_architecture()
        
        # Documentation routes
        @self.app.get("/docs/api/what-is-pap", response_class=HTMLResponse, include_in_schema=False)
        async def what_is_pap():
            """What is Provider-Abstraction-Pattern?"""
            return self._serve_html_file("docs/api/docs/Purfect-Labs_Architecture_and_Design_Philosophy.html")
        
        @self.app.get("/docs/api/purfectlabs-philosophy", response_class=HTMLResponse, include_in_schema=False)
        async def purfectlabs_philosophy():
            """PurfectLabs UR Philosophy"""
            return self._serve_html_file("docs/api/docs/Stuck_in_the_Middle_Again_State_of_the_Union_2025.html")
        
        # Store app reference for dynamic endpoint registration during startup
        self._endpoints_registered = False
        async def get_pap_docs():
            """Enhanced PAP Architecture Documentation"""
            return await self._serve_markdown_as_html("docs/dev/enhanced-pap-architecture.md", "Enhanced PAP Architecture")
        
        @self.app.get("/docs/dev/documentation-coherence-generation.md", response_class=HTMLResponse, include_in_schema=False)
        async def get_methodology_docs():
            """WarpCop Development Methodology Documentation"""
            return await self._serve_markdown_as_html("docs/dev/documentation-coherence-generation.md", "WarpCop Methodology")
        
        # Store app reference for dynamic endpoint registration during startup
        self._endpoints_registered = False


def setup_compliant_docs(app: FastAPI, discovery_system=None) -> CompliantDocsGenerator:
    """Setup complete Provider-Abstraction-Pattern compliant documentation system - one line integration"""
    compliant_docs = CompliantDocsGenerator(app, discovery_system)
    compliant_docs.setup_compliant_docs_routes()
    return compliant_docs
