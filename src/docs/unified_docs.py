"""
WARPCORE Unified Documentation System
Auto-discovers all 3 layers (data, web, api) with clean Scalar UI separation
"""

from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json
import importlib
import inspect
from pathlib import Path


class WARPCOREUnifiedDocs:
    """Clean, unified documentation for all WARPCORE layers"""
    
    def __init__(self, app: FastAPI, discovery_system=None):
        self.app = app
        self.discovery = discovery_system
        self.layers = ["data", "web", "api"]
        
    async def discover_all_layers(self) -> Dict[str, Any]:
        """Auto-discover endpoints and capabilities across all 3 layers"""
        
        discovered = {
            "data": await self._discover_data_layer(),
            "web": await self._discover_web_layer(), 
            "api": await self._discover_api_layer()
        }
        
        return discovered
    
    async def _discover_data_layer(self) -> Dict[str, Any]:
        """Discover data layer components"""
        return {
            "name": "Data Layer",
            "description": "Configuration, discovery, and data management",
            "components": {
                "config_loader": {
                    "description": "Global configuration management",
                    "methods": ["get_config", "get_aws_config", "get_gcp_config"]
                },
                "context_discovery": {
                    "description": "Autonomous provider and environment discovery",
                    "methods": ["discover_all_contexts", "discover_providers"]
                },
                "feature_gates": {
                    "description": "Feature flag management",
                    "methods": ["is_enabled", "get_features"]
                }
            },
            "endpoints": {
                "/api/data/config": "Get system configuration",
                "/api/data/discovery": "Get discovery results",
                "/api/data/features": "Get feature flags"
            }
        }
    
    async def _discover_web_layer(self) -> Dict[str, Any]:
        """Discover web layer components"""
        return {
            "name": "Web Layer", 
            "description": "UI templates, static assets, and web interfaces",
            "components": {
                "template_manager": {
                    "description": "Template rendering and management",
                    "methods": ["render_template", "get_template_context"]
                },
                "static_assets": {
                    "description": "CSS, JS, and static file serving",
                    "methods": ["serve_static", "get_asset_url"]
                }
            },
            "endpoints": {
                "/": "Main web interface",
                "/static/*": "Static assets (CSS, JS, images)",
                "/templates/*": "Dynamic template rendering"
            }
        }
    
    async def _discover_api_layer(self) -> Dict[str, Any]:
        """Discover API layer components with auto-discovery integration"""
        
        # Get live discovery results if available
        discovered_components = {}
        if self.discovery:
            contexts = getattr(self.discovery, '_discovered_contexts', {})
            components = getattr(self.discovery, '_discovered_components', {})
            
            providers = contexts.get('providers', {})
            
            for provider_name, provider_data in providers.items():
                discovered_components[f"{provider_name}_provider"] = {
                    "description": f"{provider_name.upper()} cloud provider integration",
                    "status": "authenticated" if provider_data.get('authenticated') else "available",
                    "capabilities": provider_data.get('capabilities', [])
                }
        
        return {
            "name": "API Layer",
            "description": "REST APIs, auto-discovery, and provider integrations", 
            "components": {
                "auto_discovery": {
                    "description": "Component auto-discovery and registration",
                    "methods": ["auto_discover_components", "auto_register_components"]
                },
                **discovered_components
            },
            "endpoints": {
                "/api/status": "System status and health",
                "/api/discovery/status": "Auto-discovery system status",
                "/api/discovery/components": "Discovered component details",
                **{f"/api/{provider}/auth": f"{provider.upper()} authentication" 
                   for provider in (getattr(self.discovery, '_discovered_contexts', {})
                                  .get('providers', {}).keys() if self.discovery else [])}
            }
        }
    
    async def generate_unified_spec(self) -> Dict[str, Any]:
        """Generate unified OpenAPI spec with layer separation"""
        
        layers_data = await self.discover_all_layers()
        
        spec = {
            "openapi": "3.1.0",
            "info": {
                "title": "WARPCORE Unified API",
                "version": "3.0.0",
                "description": """
🌊 **WARPCORE Auto-Discovery System**

Complete documentation for all system layers with autonomous component discovery.

### Architecture Layers:
- 📊 **Data Layer**: Configuration, discovery, feature management  
- 🌐 **Web Layer**: UI templates, static assets, web interfaces
- ⚡ **API Layer**: REST APIs, auto-discovery, cloud provider integrations

### Auto-Discovery Features:
- 🔍 **Zero Configuration**: Automatic provider detection
- 🔧 **Component Discovery**: Dynamic PAP layer registration  
- 🚀 **Live Integration**: Real-time GCP/AWS/K8s discovery
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
            "tags": [
                {"name": "📊 Data Layer", "description": "Configuration and discovery services"},
                {"name": "🌐 Web Layer", "description": "UI templates and static assets"}, 
                {"name": "⚡ API Layer", "description": "REST APIs and provider integrations"},
                {"name": "🔍 Auto-Discovery", "description": "Autonomous component discovery"},
                {"name": "🎛️ System", "description": "Core system endpoints"}
            ]
        }
        
        # Add endpoints for each layer with proper tagging
        await self._add_layer_endpoints(spec, layers_data)
        
        return spec
    
    async def _add_layer_endpoints(self, spec: Dict[str, Any], layers_data: Dict[str, Any]):
        """Add endpoints organized by layer"""
        
        # Data Layer Endpoints
        data_layer = layers_data["data"]
        spec["paths"].update({
            "/api/data/config": {
                "get": {
                    "summary": "System Configuration",
                    "description": "Get global system configuration and settings",
                    "responses": {
                        "200": {
                            "description": "System configuration",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "aws_profiles": ["dev", "stage", "prod"],
                                        "gcp_projects": ["project-dev", "project-prod"],
                                        "feature_flags": {"auto_discovery": True}
                                    }
                                }
                            }
                        }
                    },
                    "tags": ["📊 Data Layer"]
                }
            },
            "/api/data/discovery": {
                "get": {
                    "summary": "Discovery Results",
                    "description": "Get complete autonomous discovery results",
                    "responses": {
                        "200": {
                            "description": "Discovery system results",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "providers": ["gcp", "kubernetes"],
                                        "environments": "Auto-discovered",
                                        "components": "Live discovery results"
                                    }
                                }
                            }
                        }
                    },
                    "tags": ["📊 Data Layer"]
                }
            }
        })
        
        # Web Layer Endpoints  
        web_layer = layers_data["web"]
        spec["paths"].update({
            "/": {
                "get": {
                    "summary": "Main Web Interface",
                    "description": "Primary web application interface",
                    "responses": {
                        "200": {
                            "description": "Web interface HTML",
                            "content": {"text/html": {"example": "<!DOCTYPE html>..."}}
                        }
                    },
                    "tags": ["🌐 Web Layer"]
                }
            },
            "/static/{path:path}": {
                "get": {
                    "summary": "Static Assets",
                    "description": "CSS, JavaScript, images and other static files",
                    "parameters": [
                        {
                            "name": "path",
                            "in": "path", 
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Static asset path"
                        }
                    ],
                    "responses": {
                        "200": {"description": "Static file content"}
                    },
                    "tags": ["🌐 Web Layer"]
                }
            }
        })
        
        # API Layer Endpoints
        api_layer = layers_data["api"] 
        spec["paths"].update({
            "/api/status": {
                "get": {
                    "summary": "System Status",
                    "description": "Get detailed system status and metrics",
                    "responses": {
                        "200": {
                            "description": "System status",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "system": "WARPCORE",
                                        "version": "3.0.0",
                                        "auto_discovery": "operational",
                                        "layers": {
                                            "data": "✅ operational",
                                            "web": "✅ operational", 
                                            "api": "✅ operational"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "tags": ["⚡ API Layer"]
                }
            },
            "/api/discovery/status": {
                "get": {
                    "summary": "Auto-Discovery Status",
                    "description": "Get autonomous discovery system status across all layers",
                    "responses": {
                        "200": {
                            "description": "Discovery system status",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "success": True,
                                        "autonomous_discovery": True,
                                        "zero_configuration": True,
                                        "layers_discovered": 3,
                                        "components_discovered": "Live count",
                                        "providers_active": "Real provider list"
                                    }
                                }
                            }
                        }
                    },
                    "tags": ["🔍 Auto-Discovery"]
                }
            }
        })
        
        # Add discovered provider endpoints
        if self.discovery:
            contexts = getattr(self.discovery, '_discovered_contexts', {})
            providers = contexts.get('providers', {})
            
            for provider_name in providers.keys():
                spec["paths"][f"/api/{provider_name}/auth"] = {
                    "post": {
                        "summary": f"{provider_name.upper()} Authentication", 
                        "description": f"Authenticate with {provider_name} provider (auto-discovered)",
                        "responses": {
                            "200": {
                                "description": f"{provider_name.upper()} authentication result",
                                "content": {
                                    "application/json": {
                                        "example": {
                                            "success": True,
                                            "provider": provider_name,
                                            "authenticated": True,
                                            "auto_discovered": True
                                        }
                                    }
                                }
                            }
                        },
                        "tags": [f"🔗 {provider_name.upper()} Provider"]
                    }
                }
    
    def get_scalar_html(self) -> str:
        """Generate working Scalar UI - simplified and reliable"""
        return """<!DOCTYPE html>
<html>
<head>
    <title>WARPCORE API Documentation</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
        body { margin: 0; padding: 0; font-family: Inter, sans-serif; }
    </style>
</head>
<body>
    <script
        id="api-reference"
        type="application/json">
        {
            "url": "/openapi.json",
            "theme": "purple",
            "darkMode": true
        }
    </script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
</body>
</html>"""

    def setup_unified_docs(self):
        """Setup unified documentation routes"""
        
        @self.app.get("/openapi.json", include_in_schema=False)
        async def get_unified_spec():
            """Generate unified OpenAPI spec for all layers"""
            return await self.generate_unified_spec()
        
        @self.app.get("/docs", response_class=HTMLResponse, include_in_schema=False)
        async def get_unified_docs():
            """Beautiful unified Scalar documentation"""
            return self.get_scalar_html()
        
        @self.app.get("/api-docs", response_class=HTMLResponse, include_in_schema=False) 
        async def get_api_docs_alt():
            """Alternative docs URL"""
            return self.get_scalar_html()


def setup_unified_warpcore_docs(app: FastAPI, discovery_system=None) -> WARPCOREUnifiedDocs:
    """Clean one-line setup for unified documentation"""
    unified_docs = WARPCOREUnifiedDocs(app, discovery_system)
    unified_docs.setup_unified_docs()
    return unified_docs