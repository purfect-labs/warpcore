"""
WARPCORE Dynamic API Documentation Generator
Clean, modern Scalar-based docs with auto-discovery integration
"""

from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json


class WARPCOREDocsGenerator:
    """Clean, lean API docs generator using Scalar"""
    
    def __init__(self, app: FastAPI, discovery_system=None):
        self.app = app
        self.discovery = discovery_system
        self.base_spec = {
            "openapi": "3.1.0",
            "info": {
                "title": "WARPCORE Auto-Discovery API",
                "version": "3.0.0",
                "description": "Autonomous cloud provider discovery and management system",
                "contact": {
                    "name": "WARPCORE System",
                    "url": "https://github.com/warpcore"
                }
            },
            "servers": [
                {"url": "http://localhost:8000", "description": "Development server"}
            ],
            "paths": {},
            "components": {"schemas": {}}
        }
    
    async def generate_dynamic_spec(self) -> Dict[str, Any]:
        """Generate OpenAPI spec from discovered components"""
        spec = self.base_spec.copy()
        
        # Add static endpoints
        spec["paths"].update({
            "/": {
                "get": {
                    "summary": "System Status",
                    "description": "Get basic WARPCORE system status",
                    "responses": {
                        "200": {
                            "description": "System status",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "message": "WARPCORE Auto-Discovery System",
                                        "status": "running"
                                    }
                                }
                            }
                        }
                    },
                    "tags": ["System"]
                }
            },
            "/api/status": {
                "get": {
                    "summary": "Detailed System Status",
                    "description": "Get detailed system status and metrics",
                    "responses": {
                        "200": {
                            "description": "Detailed system information",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "system": "WARPCORE",
                                        "version": "3.0.0",
                                        "auto_discovery": "ready"
                                    }
                                }
                            }
                        }
                    },
                    "tags": ["System"]
                }
            }
        })
        
        # Add discovery endpoints if available
        if self.discovery:
            await self._add_discovery_endpoints(spec)
        
        return spec
    
    async def _add_discovery_endpoints(self, spec: Dict[str, Any]):
        """Add dynamic endpoints from auto-discovery"""
        try:
            # Get discovered contexts
            contexts = getattr(self.discovery, '_discovered_contexts', {})
            components = getattr(self.discovery, '_discovered_components', {})
            
            providers = contexts.get('providers', {})
            
            # Discovery status endpoint
            spec["paths"]["/api/discovery/status"] = {
                "get": {
                    "summary": "Auto-Discovery Status",
                    "description": "Get autonomous discovery system status and metrics",
                    "responses": {
                        "200": {
                            "description": "Discovery system status",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "success": True,
                                        "providers_discovered": len(providers),
                                        "components_discovered": sum(
                                            len(comp.get('providers', {})) + 
                                            len(comp.get('controllers', {})) + 
                                            len(comp.get('orchestrators', {}))
                                            for comp in components.values()
                                        ),
                                        "autonomous_discovery": True,
                                        "zero_configuration": True
                                    }
                                }
                            }
                        }
                    },
                    "tags": ["Auto-Discovery"]
                }
            }
            
            # Component discovery endpoint
            spec["paths"]["/api/discovery/components"] = {
                "get": {
                    "summary": "Component Discovery Results",
                    "description": "Get detailed auto-discovered component information",
                    "responses": {
                        "200": {
                            "description": "Discovered components and capabilities",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "success": True,
                                        "auto_discovery": True,
                                        "discovered_components": {
                                            provider: {
                                                "controllers": len(comp.get('controllers', {})),
                                                "orchestrators": len(comp.get('orchestrators', {})),
                                                "providers": len(comp.get('providers', {})),
                                                "total_capabilities": len(comp.get('capabilities', []))
                                            }
                                            for provider, comp in components.items()
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "tags": ["Auto-Discovery"]
                }
            }
            
            # Provider-specific endpoints
            for provider_name in providers.keys():
                spec["paths"][f"/api/discovery/components/{provider_name}"] = {
                    "get": {
                        "summary": f"{provider_name.upper()} Components",
                        "description": f"Get component discovery results for {provider_name} provider",
                        "parameters": [
                            {
                                "name": "provider",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string", "enum": [provider_name]},
                                "description": f"Provider name: {provider_name}"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": f"{provider_name.upper()} provider components",
                                "content": {
                                    "application/json": {
                                        "example": {
                                            "success": True,
                                            "provider": provider_name,
                                            "auto_discovered": True,
                                            "components": "Dynamic based on discovery",
                                            "capabilities": "Live from discovered components"
                                        }
                                    }
                                }
                            }
                        },
                        "tags": [f"{provider_name.upper()} Provider"]
                    }
                }
        
        except Exception:
            # Silent fail - docs still work without discovery integration
            pass
    
    def get_scalar_html(self, spec_url: str = "/openapi.json") -> str:
        """Generate beautiful Scalar documentation HTML"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>WARPCORE API Documentation</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
        body {{ margin: 0; padding: 0; }}
        .scalar-container {{ height: 100vh; }}
    </style>
</head>
<body>
    <div class="scalar-container">
        <script
            id="api-reference"
            data-url="{spec_url}"
            data-configuration='{json.dumps({
                "theme": "purple",
                "layout": "modern",
                "hideDownloadButton": False,
                "searchHotKey": "/",
                "darkMode": True,
                "customCss": """
                    .scalar-api-reference {{ --scalar-color-1: #1a1a2e; }}
                    .scalar-api-reference {{ --scalar-color-2: #16213e; }}
                    .scalar-api-reference {{ --scalar-color-3: #0f172a; }}
                    .scalar-api-reference {{ --scalar-font: 'Inter', -apple-system, BlinkMacSystemFont; }}
                """,
                "metadata": {
                    "title": "WARPCORE Auto-Discovery API",
                    "description": "Modern API documentation with autonomous component discovery",
                    "logo": "🌊"
                }
            })}'>
        </script>
        <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
    </div>
</body>
</html>"""

    def setup_docs_routes(self):
        """Setup clean, lean documentation routes"""
        
        @self.app.get("/openapi.json", include_in_schema=False)
        async def get_openapi_spec():
            """Dynamic OpenAPI spec generation"""
            return await self.generate_dynamic_spec()
        
        @self.app.get("/docs", response_class=HTMLResponse, include_in_schema=False)
        async def get_docs():
            """Beautiful Scalar API documentation"""
            return self.get_scalar_html()
        
        @self.app.get("/api-docs", response_class=HTMLResponse, include_in_schema=False)
        async def get_api_docs():
            """Alternative docs URL"""
            return self.get_scalar_html()


def setup_warpcore_docs(app: FastAPI, discovery_system=None) -> WARPCOREDocsGenerator:
    """Clean setup function - one line integration"""
    docs_generator = WARPCOREDocsGenerator(app, discovery_system)
    docs_generator.setup_docs_routes()
    return docs_generator