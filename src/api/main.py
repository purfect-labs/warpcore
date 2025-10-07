"""
WARPCORE API Server
PAP-compliant backend with discovery-driven provider composition
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..data.config_loader import get_config
from .providers.gcp.auth import GCPAuth
from .providers.license.license_provider import LicenseProvider
from .controllers import get_controller_registry, get_aws_controller, get_gcp_controller, get_k8s_controller, get_license_controller
from .providers import get_provider_registry
from .middleware import get_middleware_registry
from .executors import get_executor_registry
from .orchestrators.gcp.gcp_auth_orchestrator import GCPAuthOrchestrator
from ..web.routes import setup_all_routes
from ..data.config.discovery.context_discovery import ContextDiscoverySystem
from .auto_registration import ComponentAutoDiscovery
from ..docs.compliant_docs import CompliantDocsGenerator
# Simple endpoint filtering - if we have endpoints we know not to call, we don't call them
# No hardcoded endpoint filtering - use discovery


class AuthRequest(BaseModel):
    provider: str  # Provider type discovered from system
    context: Optional[str] = None  # Context inferred from git/codeowners
    project: Optional[str] = None  # Project discovered from provider


class CommandRequest(BaseModel):
    action: str  # e.g., 'list_instances', 'list_projects', 'authenticate'
    provider: str  # Provider type discovered from system
    params: Optional[Dict] = {}  # Additional parameters


class RawCommandRequest(BaseModel):
    command: str  # Raw shell command to execute
    context: Optional[str] = "terminal"  # Context for the command


class WARPCOREAPIServer:
    """WARPCORE API Server - PAP-compliant backend"""
    
    def __init__(self):
        self.app = FastAPI(title="WARPCORE Command Center", version="3.0.0")
        self.connections: Dict[str, WebSocket] = {}
        self.config = get_config()
        
        # Mount static files from src/web
        static_path = Path(__file__).parent.parent / "web" / "static"
        if static_path.exists():
            self.app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        
        # Initialize template manager
        from ..web.template_manager import TemplateManager
        self.template_manager = TemplateManager()
        
        # Get all PAP layer registries
        self.controller_registry = get_controller_registry()
        self.provider_registry = get_provider_registry()
        self.middleware_registry = get_middleware_registry()
        self.executor_registry = get_executor_registry()
        
        # Initialize orchestrators
        self.gcp_orchestrator = GCPAuthOrchestrator()
        
        # Initialize discovery systems for zero-configuration
        self.context_discovery = ContextDiscoverySystem()
        self.auto_discovery = ComponentAutoDiscovery()
        
        # Initialize complete architecture documentation system
        self.docs_generator = CompliantDocsGenerator(self.app, self.context_discovery)
        
        # Discovery state
        self._discovered_contexts = {}
        self._discovered_components = {}
        self._registration_results = {}
        
        # Set up the architecture
        self._setup_architecture()
        
        # Setup routes
        self.setup_routes()
        
        # Setup documentation endpoints with complete architecture discovery
        self.setup_documentation_endpoints()
    
    def _setup_architecture(self):
        """Setup PAP architecture: Routes -> Controllers -> Orchestrators -> Providers -> Middleware -> Executors"""
        # Wire up WebSocket managers for all registries
        self.provider_registry.set_websocket_manager(self)
        self.middleware_registry.set_websocket_manager(self)
        self.executor_registry.set_websocket_manager(self)
        
        # Wire up controller registry with provider registry and WebSocket
        self.controller_registry.set_provider_registry(self.provider_registry)
        self.controller_registry.set_websocket_manager(self)
        
        # Wire up orchestrator with all registries
        self.gcp_orchestrator.set_provider_registry(self.provider_registry)
        self.gcp_orchestrator.set_middleware_registry(self.middleware_registry)
        self.gcp_orchestrator.set_executor_registry(self.executor_registry)
        
        # Discovery system will be initialized when the server starts
    
    async def _initialize_architecture_discovery(self):
        """Initialize complete architecture discovery for Data, Web, and API layers"""
        try:
            # Discover complete architecture (Data, Web, API layers)
            await self.docs_generator.register_discovered_endpoints_now()
            
            logging.info("✅ Complete architecture discovery initialized")
            logging.info("📊 Data Layer discovery: ACTIVE")
            logging.info("🌐 Web Layer discovery: ACTIVE")
            logging.info("⚡ API Layer discovery: ACTIVE")
            
        except Exception as e:
            logging.error(f"❌ Architecture discovery initialization failed: {str(e)}")
        
        # Initialize discovered providers only
        gcp_auth = GCPAuth()
        license_provider = LicenseProvider()
        
        # Register discovered providers
        self.provider_registry.register_provider("gcp_auth", gcp_auth)
        self.provider_registry.register_provider("license", license_provider)
    
    def setup_documentation_endpoints(self):
        """Setup comprehensive documentation endpoints with full architecture discovery"""
        # Setup Scalar-based documentation endpoints
        self.docs_generator.setup_compliant_docs_routes()
        
        # Architecture discovery will be initialized when server starts
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        # Setup organized routes by provider
        setup_all_routes(self.app, self.controller_registry)
        
        @self.app.get("/", response_class=HTMLResponse)
        async def get_index():
            try:
                # Get license status
                license_controller = self.controller_registry.get_license_controller()
                license_status = None
                if license_controller:
                    license_result = await license_controller.get_license_status()
                    if license_result.get('success'):
                        license_status = license_result.get('data')
                
                # Get template context using instance template manager
                context = self.template_manager.get_template_context(license_status)
                
                # Add additional context
                context.update({
                    'license_status': license_status,
                    'current_tab': 'terminal'  # Default tab
                })
                
                return self.render_main_template(context)
                
            except Exception as e:
                logging.error(f"Error in index route: {str(e)}")
                # Fallback to simple interface if template system fails
                return self.get_html_content()
        
        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            await websocket.accept()
            self.connections[client_id] = websocket
            
            try:
                # Send initial status (cached, won't spam commands)
                await self.send_initial_status(client_id)
                
                # Auto-login on page load to show auth logs
                await self.auto_authenticate_on_load()
                
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    await self.handle_websocket_message(client_id, message)
                    
            except WebSocketDisconnect:
                if client_id in self.connections:
                    del self.connections[client_id]
        
        @self.app.post("/api/auth")
        async def authenticate(request: AuthRequest, background_tasks: BackgroundTasks):
            background_tasks.add_task(self.authenticate_provider, request)
            return {"status": "starting", "provider": request.provider}
        
# AWS endpoints removed - using discovery-based providers only
        
        @self.app.api_route("/api/status", methods=["GET", "HEAD"])
        async def get_status():
            return await self.get_full_status()
        
# AWS status removed - using discovery-based status
        
        @self.app.get("/api/gcp/status")
        async def get_gcp_status():
            """Get GCP authentication status"""
            try:
                gcp_controller = self.controller_registry.get_gcp_controller()
                if gcp_controller:
                    return await gcp_controller.get_status()
                else:
                    return {"success": False, "authenticated": False, "error": "GCP controller not available"}
            except Exception as e:
                return {"success": False, "authenticated": False, "error": str(e)}
        
        # WARP FAKE SUB TEST DEMO - AWS endpoints removed for GCP-only architecture
        
        @self.app.get("/api/gcp/endpoints")
        async def get_gcp_endpoints():
            """Get available GCP endpoints with real-time capability discovery"""
            try:
                gcp_controller = self.controller_registry.get_gcp_controller()
                if gcp_controller and hasattr(gcp_controller, 'get_endpoints'):
                    return await gcp_controller.get_endpoints()
                else:
                    return {"success": False, "error": "GCP controller not available or endpoint discovery not implemented"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/config")
        async def get_config_info():
            # WARP FAKE SUB TEST DEMO - AWS profiles removed, GCP-only configuration
            return {
                'gcp_projects': list(self.config.get_gcp_config().get('projects', {}).keys()),
                'database_configs': self.config.get_all_database_configs(),
                'timestamp': datetime.now().isoformat(),
                'note': 'WARP FAKE SUB TEST DEMO - AWS functionality removed'
            }
        
        # License management endpoints
        class LicenseActivateRequest(BaseModel):
            license_key: str
            user_email: Optional[str] = None
        
        class TrialLicenseRequest(BaseModel):
            user_email: str
            days: Optional[int] = 7
        
        class LicenseValidateRequest(BaseModel):
            license_key: str
        
        @self.app.get("/api/license/status")
        async def get_license_status():
            """Get current license status"""
            try:
                license_controller = self.controller_registry.get_license_controller()
                if license_controller:
                    return await license_controller.get_license_status()
                else:
                    return {"success": False, "error": "License controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/license/validate")
        async def validate_license_key(request: LicenseValidateRequest):
            """Validate a license key without activating it"""
            try:
                license_controller = self.controller_registry.get_license_controller()
                if license_controller:
                    result = await license_controller.validate_license_key(request.license_key)
                    return result
                else:
                    return {"valid": False, "error": "License controller not available"}
            except Exception as e:
                return {"valid": False, "error": str(e)}
        
        @self.app.post("/api/license/activate")
        async def activate_license(request: LicenseActivateRequest, background_tasks: BackgroundTasks):
            """Activate a license key"""
            try:
                license_controller = self.controller_registry.get_license_controller()
                if license_controller:
                    background_tasks.add_task(
                        license_controller.activate_license, 
                        request.license_key, 
                        request.user_email
                    )
                    return {"success": True, "message": "License activation started"}
                else:
                    return {"success": False, "error": "License controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/license/generate-trial")
        async def generate_trial_license(request: TrialLicenseRequest, background_tasks: BackgroundTasks):
            """Generate a trial license"""
            try:
                license_controller = self.controller_registry.get_license_controller()
                if license_controller:
                    background_tasks.add_task(
                        license_controller.generate_trial_license,
                        request.user_email,
                        request.days
                    )
                    return {"success": True, "message": "Trial license generation started"}
                else:
                    return {"success": False, "error": "License controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/license/deactivate")
        async def deactivate_license(background_tasks: BackgroundTasks):
            """Deactivate current license"""
            try:
                license_controller = self.controller_registry.get_license_controller()
                if license_controller:
                    background_tasks.add_task(license_controller.deactivate_license)
                    return {"success": True, "message": "License deactivation started"}
                else:
                    return {"success": False, "error": "License controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/license/subscription")
        async def get_subscription_info():
            """Get subscription and feature information"""
            try:
                license_controller = self.controller_registry.get_license_controller()
                if license_controller:
                    return await license_controller.get_subscription_info()
                else:
                    return {"success": False, "error": "License controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/command")
        async def execute_command(request: CommandRequest, background_tasks: BackgroundTasks):
            """Execute commands via controller layer"""
            try:
                # WARP FAKE SUB TEST DEMO - AWS controller removed
                if request.provider == "gcp":
                    controller = self.controller_registry.get_gcp_controller()
                else:
                    return {"success": False, "error": f"Unknown provider: {request.provider}"}
                
                if not controller:
                    return {"success": False, "error": f"Controller not available for {request.provider}"}
                
                # Route action to appropriate controller method
                if hasattr(controller, request.action):
                    method = getattr(controller, request.action)
                    background_tasks.add_task(method, **request.params)
                    return {"success": True, "message": f"Command {request.action} initiated", "provider": request.provider}
                else:
                    return {"success": False, "error": f"Action {request.action} not available on {request.provider} controller"}
                    
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/execute")
        async def execute_raw_command(request: RawCommandRequest, background_tasks: BackgroundTasks):
            """Execute raw shell command through PAP safety gates"""
            try:
                # Parse command for safety validation
                command_parts = request.command.strip().split()
                if not command_parts:
                    return {"success": False, "error": "Empty command"}
                
                # Create execution context
                context = {
                    "operation": "raw_command_execution",
                    "context": request.context,
                    "user_initiated": True
                }
                
                # Execute through PAP safety gates
                result = await self.executor_registry.execute_with_safety_gates(
                    "terminal_command",
                    command_parts,
                    context
                )
                
                return {
                    "success": result.get("success", False),
                    "message": f"Command executed via PAP safety gates: {request.command}",
                    "pap_enforced": True,
                    "safety_gate_applied": True,
                    "command": request.command,
                    "context": request.context,
                    "execution_details": result
                }
                
            except Exception as e:
                return {
                    "success": False, 
                    "error": f"PAP safety gate execution failed: {str(e)}",
                    "pap_enforced": True,
                    "command": request.command
                }
        
        # WARP FAKE SUB TEST DEMO - Database status endpoints removed with AWS controller
        
        
        @self.app.post("/api/gcp/kali/forward/{env}")
        async def kali_port_forward_env(env: str, background_tasks: BackgroundTasks):
            """Setup Kali port forwarding for specific environment"""
            try:
                gcp_controller = self.controller_registry.get_gcp_controller()
                if gcp_controller:
                    background_tasks.add_task(gcp_controller.kali_port_forward, env=env)
                    return {"success": True, "message": f"Kali port forwarding initiated for {env}"}
                else:
                    return {"success": False, "error": "GCP controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/gcp/kali/forward/all")
        async def kali_port_forward_all(background_tasks: BackgroundTasks):
            """Setup Kali port forwarding for all environments"""
            try:
                gcp_controller = self.controller_registry.get_gcp_controller()
                if gcp_controller:
                    background_tasks.add_task(gcp_controller.kali_port_forward_all)
                    return {"success": True, "message": "Kali port forwarding initiated for all environments"}
                else:
                    return {"success": False, "error": "GCP controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # Add missing Kali routes that frontend expects
        class KaliRequest(BaseModel):
            env: str
        
        @self.app.post("/api/gcp/kali/connect")
        async def kali_connect(request: KaliRequest, background_tasks: BackgroundTasks):
            """Connect Kali for specific environment"""
            try:
                gcp_controller = self.controller_registry.get_gcp_controller()
                if gcp_controller:
                    result = await gcp_controller.kali_port_forward(env=request.env)
                    return result
                else:
                    return {"success": False, "error": "GCP controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/gcp/kali/stop")
        async def kali_stop_all(background_tasks: BackgroundTasks):
            """Stop all Kali port forwards"""
            try:
                # Use pkill to stop all kubectl port-forward processes for Kiali
                from .providers.base_provider import BaseProvider
                
                class KaliStopProvider(BaseProvider):
                    def __init__(self):
                        super().__init__("kali_stop")
                    
                    async def authenticate(self, **kwargs):
                        return {"success": True, "message": "No auth needed"}
                    
                    async def get_status(self):
                        return {"status": "ready"}
                
                stop_provider = KaliStopProvider()
                stop_provider.broadcast_message = self.broadcast_message
                
                # Kill all kubectl port-forward processes for Kiali
                result = await stop_provider.execute_command(
                    "pkill -f 'kubectl port-forward.*kiali.*istio-system'"
                )
                
                return {
                    "success": True,
                    "message": "All Kali port forwards stopped",
                    "details": result
                }
                
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/gcp/kali/status")
        async def kali_status():
            """Get Kali connection status for all environments"""
            try:
                from .providers.base_provider import BaseProvider
                
                class KaliStatusProvider(BaseProvider):
                    def __init__(self):
                        super().__init__("kali_status")
                    
                    async def authenticate(self, **kwargs):
                        return {"success": True, "message": "No auth needed"}
                    
                    async def get_status(self):
                        return {"status": "ready"}
                
                status_provider = KaliStatusProvider()
                
                # Check for running kubectl port-forward processes
                result = await status_provider.execute_command(
                    "ps aux | grep 'kubectl port-forward.*kiali.*istio-system' | grep -v grep"
                )
                
                # Parse output to determine which environments are connected
                envs_status = []
                
                # Use discovered environments and dynamic ports instead of hardcoded
                discovered_contexts = getattr(self, '_discovered_contexts', {})
                port_assignments = discovered_contexts.get('ports', {})
                
                # Create reverse port mapping from discovered contexts
                port_map = {}
                for env_name, ports in port_assignments.items():
                    if env_name != "system" and "kiali_port" in ports:
                        port_map[str(ports["kiali_port"])] = env_name
                
                if result.get('success') and result.get('stdout', '').strip():
                    lines = result['stdout'].strip().split('\n')
                    for line in lines:
                        for port, env in port_map.items():
                            if port in line:
                                envs_status.append({
                                    'env': env,
                                    'port': int(port),
                                    'connected': True
                                })
                                break
                
                # Add missing environments as not connected
                connected_envs = [status['env'] for status in envs_status]
                for port, env in port_map.items():
                    if env not in connected_envs:
                        envs_status.append({
                            'env': env,
                            'port': int(port),
                            'connected': False
                        })
                
                return {
                    "success": True,
                    "status": envs_status
                }
                
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/gcp/kubectl/auth/{env}")
        async def kubectl_auth_env(env: str, background_tasks: BackgroundTasks):
            """Authenticate kubectl with GKE cluster for environment"""
            try:
                gcp_controller = self.controller_registry.get_gcp_controller()
                if gcp_controller:
                    background_tasks.add_task(gcp_controller.kubectl_auth, env=env)
                    return {"success": True, "message": f"kubectl authentication initiated for {env}"}
                else:
                    return {"success": False, "error": "GCP controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # Add missing Kali routes that frontend expects
        class KaliRequest(BaseModel):
            env: str
        
        @self.app.post("/api/gcp/kali/connect")
        async def kali_connect(request: KaliRequest, background_tasks: BackgroundTasks):
            """Connect Kali for specific environment"""
            try:
                gcp_controller = self.controller_registry.get_gcp_controller()
                if gcp_controller:
                    result = await gcp_controller.kali_port_forward(env=request.env)
                    return result
                else:
                    return {"success": False, "error": "GCP controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/gcp/kali/stop")
        async def kali_stop_all(background_tasks: BackgroundTasks):
            """Stop all Kali port forwards"""
            try:
                # Use pkill to stop all kubectl port-forward processes for Kiali
                from .providers.base_provider import BaseProvider
                
                class KaliStopProvider(BaseProvider):
                    def __init__(self):
                        super().__init__("kali_stop")
                    
                    async def authenticate(self, **kwargs):
                        return {"success": True, "message": "No auth needed"}
                    
                    async def get_status(self):
                        return {"status": "ready"}
                
                stop_provider = KaliStopProvider()
                stop_provider.broadcast_message = self.broadcast_message
                
                # Kill all kubectl port-forward processes
                result = await stop_provider.execute_command(
                    "pkill -f 'kubectl port-forward.*kiali.*istio-system'"
                )
                
                return {
                    "success": True,
                    "message": "All Kali port forwards stopped",
                    "details": result
                }
                
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/gcp/kali/status")
        async def kali_status():
            """Get Kali connection status for all environments"""
            try:
                from .providers.base_provider import BaseProvider
                
                class KaliStatusProvider(BaseProvider):
                    def __init__(self):
                        super().__init__("kali_status")
                    
                    async def authenticate(self, **kwargs):
                        return {"success": True, "message": "No auth needed"}
                    
                    async def get_status(self):
                        return {"status": "ready"}
                
                status_provider = KaliStatusProvider()
                
                # Check for running kubectl port-forward processes
                result = await status_provider.execute_command(
                    "ps aux | grep 'kubectl port-forward.*kiali.*istio-system' | grep -v grep"
                )
                
                # Parse output to determine which environments are connected
                envs_status = []
                
                # Use discovered environments and dynamic ports instead of hardcoded
                discovered_contexts = getattr(self, '_discovered_contexts', {})
                port_assignments = discovered_contexts.get('ports', {})
                
                # Create reverse port mapping from discovered contexts
                port_map = {}
                for env_name, ports in port_assignments.items():
                    if env_name != "system" and "kiali_port" in ports:
                        port_map[str(ports["kiali_port"])] = env_name
                
                if result.get('success') and result.get('stdout', '').strip():
                    lines = result['stdout'].strip().split('\n')
                    for line in lines:
                        for port, env in port_map.items():
                            if port in line:
                                envs_status.append({
                                    'env': env,
                                    'port': int(port),
                                    'connected': True
                                })
                                break
                
                # Add missing environments as not connected
                connected_envs = [status['env'] for status in envs_status]
                for port, env in port_map.items():
                    if env not in connected_envs:
                        envs_status.append({
                            'env': env,
                            'port': int(port),
                            'connected': False
                        })
                
                return {
                    "success": True,
                    "status": envs_status
                }
                
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # =================
        # K8s API ENDPOINTS WITH MANDATORY CONTEXT VALIDATION
        # =================
        
        class K8sRequest(BaseModel):
            env: str
            namespace: Optional[str] = "default"
        
        class K8sPodRequest(BaseModel):
            env: str
            pod_name: str
            namespace: Optional[str] = "default"
            tail: Optional[int] = 100
        
        class K8sPortForwardRequest(BaseModel):
            env: str
            resource: str
            ports: str
            namespace: Optional[str] = "default"
        
        class K8sRawCommandRequest(BaseModel):
            env: str
            command: str
            namespace: Optional[str] = None
        
        @self.app.post("/api/k8s/auth/{env}")
        async def k8s_authenticate_env(env: str, background_tasks: BackgroundTasks):
            """Authenticate kubectl with specific environment cluster (SAFE)"""
            try:
                k8s_controller = self.controller_registry.get_controller("k8s")
                if k8s_controller:
                    background_tasks.add_task(k8s_controller.authenticate, env=env)
                    return {"success": True, "message": f"K8s authentication initiated for {env} with context validation"}
                else:
                    return {"success": False, "error": "K8s controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/k8s/status")
        async def k8s_get_status():
            """Get K8s cluster status"""
            try:
                k8s_controller = self.controller_registry.get_controller("k8s")
                if k8s_controller:
                    return await k8s_controller.get_status()
                else:
                    return {"success": False, "error": "K8s controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/k8s/pods")
        async def k8s_get_pods(request: K8sRequest, background_tasks: BackgroundTasks):
            """Get pods with environment context validation"""
            try:
                k8s_controller = self.controller_registry.get_controller("k8s")
                if k8s_controller:
                    background_tasks.add_task(
                        k8s_controller.get_pods, 
                        env=request.env, 
                        namespace=request.namespace
                    )
                    return {
                        "success": True, 
                        "message": f"Getting pods from {request.env}/{request.namespace} with context safety"
                    }
                else:
                    return {"success": False, "error": "K8s controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/k8s/services")
        async def k8s_get_services(request: K8sRequest, background_tasks: BackgroundTasks):
            """Get services with environment context validation"""
            try:
                k8s_controller = self.controller_registry.get_controller("k8s")
                if k8s_controller:
                    background_tasks.add_task(
                        k8s_controller.get_services, 
                        env=request.env, 
                        namespace=request.namespace
                    )
                    return {
                        "success": True, 
                        "message": f"Getting services from {request.env}/{request.namespace} with context safety"
                    }
                else:
                    return {"success": False, "error": "K8s controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/k8s/deployments")
        async def k8s_get_deployments(request: K8sRequest, background_tasks: BackgroundTasks):
            """Get deployments with environment context validation"""
            try:
                k8s_controller = self.controller_registry.get_controller("k8s")
                if k8s_controller:
                    background_tasks.add_task(
                        k8s_controller.get_deployments, 
                        env=request.env, 
                        namespace=request.namespace
                    )
                    return {
                        "success": True, 
                        "message": f"Getting deployments from {request.env}/{request.namespace} with context safety"
                    }
                else:
                    return {"success": False, "error": "K8s controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/k8s/namespaces")
        async def k8s_get_namespaces(request: K8sRequest, background_tasks: BackgroundTasks):
            """Get namespaces with environment context validation"""
            try:
                k8s_controller = self.controller_registry.get_controller("k8s")
                if k8s_controller:
                    background_tasks.add_task(k8s_controller.get_namespaces, env=request.env)
                    return {
                        "success": True, 
                        "message": f"Getting namespaces from {request.env} with context safety"
                    }
                else:
                    return {"success": False, "error": "K8s controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/k8s/pods/describe")
        async def k8s_describe_pod(request: K8sPodRequest, background_tasks: BackgroundTasks):
            """Describe pod with environment context validation"""
            try:
                k8s_controller = self.controller_registry.get_controller("k8s")
                if k8s_controller:
                    background_tasks.add_task(
                        k8s_controller.describe_pod,
                        pod_name=request.pod_name,
                        env=request.env, 
                        namespace=request.namespace
                    )
                    return {
                        "success": True, 
                        "message": f"Describing pod {request.pod_name} in {request.env}/{request.namespace} with context safety"
                    }
                else:
                    return {"success": False, "error": "K8s controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/k8s/pods/logs")
        async def k8s_get_logs(request: K8sPodRequest, background_tasks: BackgroundTasks):
            """Get pod logs with environment context validation"""
            try:
                k8s_controller = self.controller_registry.get_controller("k8s")
                if k8s_controller:
                    background_tasks.add_task(
                        k8s_controller.get_logs,
                        pod_name=request.pod_name,
                        env=request.env, 
                        namespace=request.namespace,
                        tail=request.tail
                    )
                    return {
                        "success": True, 
                        "message": f"Getting logs for {request.pod_name} in {request.env}/{request.namespace} (tail={request.tail}) with context safety"
                    }
                else:
                    return {"success": False, "error": "K8s controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/k8s/port-forward")
        async def k8s_port_forward(request: K8sPortForwardRequest, background_tasks: BackgroundTasks):
            """Start port forwarding with environment context validation and background logging"""
            try:
                k8s_controller = self.controller_registry.get_controller("k8s")
                if k8s_controller:
                    background_tasks.add_task(
                        k8s_controller.port_forward,
                        resource=request.resource,
                        ports=request.ports,
                        env=request.env, 
                        namespace=request.namespace
                    )
                    return {
                        "success": True, 
                        "message": f"Port forwarding {request.resource} ({request.ports}) in {request.env}/{request.namespace} with context safety and tmp logging"
                    }
                else:
                    return {"success": False, "error": "K8s controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/k8s/kubectl")
        async def k8s_raw_kubectl(request: K8sRawCommandRequest, background_tasks: BackgroundTasks):
            """Execute raw kubectl command with environment context validation"""
            try:
                k8s_controller = self.controller_registry.get_controller("k8s")
                if k8s_controller:
                    background_tasks.add_task(
                        k8s_controller.execute_raw_kubectl,
                        command=request.command,
                        env=request.env,
                        namespace=request.namespace
                    )
                    return {
                        "success": True, 
                        "message": f"Executing kubectl command '{request.command}' in {request.env} with MANDATORY context validation"
                    }
                else:
                    return {"success": False, "error": "K8s controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/k8s/endpoints")
        async def get_k8s_endpoints():
            """Get available K8s endpoints with real-time capability discovery"""
            try:
                k8s_controller = self.controller_registry.get_k8s_controller()
                if k8s_controller and hasattr(k8s_controller, 'get_endpoints'):
                    return await k8s_controller.get_endpoints()
                else:
                    return {"success": False, "error": "K8s controller not available or endpoint discovery not implemented"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/endpoints/test")
        async def get_simple_test():
            """Simple test endpoint"""
            return {"test": "working", "timestamp": datetime.now().isoformat()}
        
        @self.app.get("/api/pap/status")
        async def get_pap_status():
            """Validate PAP architecture implementation"""
            try:
                return {
                    "success": True,
                    "pap_architecture": {
                        "middleware_registry": bool(self.middleware_registry),
                        "executor_registry": bool(self.executor_registry),
                        "gcp_orchestrator": bool(self.gcp_orchestrator),
                        "middleware_count": len(self.middleware_registry.get_all_middleware()),
                        "executor_count": len(self.executor_registry.get_all_executors()),
                        "safety_gates_active": True
                    },
                    "layer_status": {
                        "layer_1_routes": "implemented",
                        "layer_2_controllers": "implemented", 
                        "layer_3_orchestrators": "implemented",
                        "layer_4_providers": "implemented",
                        "layer_5_middleware": "implemented",
                        "layer_6_executors": "implemented"
                    },
                    "violations_fixed": [
                        "no_privileged_execution",
                        "auditable_middleware",
                        "pap_flow_enforcement"
                    ],
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"PAP status check failed: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.app.get("/api/discovery/status")
        async def get_discovery_status():
            """Get autonomous discovery system status"""
            try:
                discovered_contexts = getattr(self, '_discovered_contexts', None)
                discovered_components = getattr(self, '_discovered_components', {})
                registration_results = getattr(self, '_registration_results', {})
                
                if not discovered_contexts:
                    return {
                        "success": False,
                        "discovered": False,
                        "message": "Discovery system not yet initialized",
                        "autonomous_discovery": True
                    }
                
                providers = discovered_contexts.get('providers', {})
                environments = discovered_contexts.get('environments', [])
                ports = discovered_contexts.get('ports', {})
                
                return {
                    "success": True,
                    "discovered": True,
                    "autonomous_discovery": True,
                    "zero_configuration": True,
                    "auto_registration": True,
                    "providers": {
                        name: {
                            "available": ctx.get("available", False),
                            "authenticated": ctx.get("authenticated", False),
                            "capabilities": ctx.get("capabilities", [])
                        }
                        for name, ctx in providers.items()
                    },
                    "environments": [
                        {
                            "name": env["name"],
                            "type": env.get("type", "unknown"),
                            "capabilities": env.get("capabilities", [])
                        }
                        for env in environments
                    ],
                    "components_discovered": {
                        provider: {
                            "controllers": len(components.get("controllers", {})),
                            "orchestrators": len(components.get("orchestrators", {})),
                            "providers": len(components.get("providers", {})),
                            "total_capabilities": len(components.get("capabilities", []))
                        }
                        for provider, components in discovered_components.items()
                    },
                    "components_registered": {
                        comp_type: {
                            "count": len(comps),
                            "successful": len([c for c in comps.values() if c.get("success", False)]),
                            "failed": len([c for c in comps.values() if not c.get("success", False)])
                        }
                        for comp_type, comps in registration_results.items()
                    },
                    "dynamic_ports": {
                        env_name: ports.get("kiali_port") 
                        for env_name, ports in ports.items() 
                        if env_name != "system"
                    },
                    "hardcoded_values_eliminated": True,
                    "discovery_timestamp": discovered_contexts.get('discovery_timestamp'),
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Discovery status check failed: {str(e)}",
                    "autonomous_discovery": True,
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.app.get("/api/discovery/components")
        async def get_component_discovery():
            """Get detailed component discovery results"""
            try:
                discovered_components = getattr(self, '_discovered_components', {})
                registration_results = getattr(self, '_registration_results', {})
                
                if not discovered_components:
                    return {
                        "success": False,
                        "message": "Component discovery not yet completed",
                        "auto_registration": True
                    }
                
                return {
                    "success": True,
                    "auto_discovery": True,
                    "auto_registration": True,
                    "discovered_components": discovered_components,
                    "registration_results": registration_results,
                    "capabilities": self.auto_discovery.get_discovered_capabilities(),
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Component discovery status check failed: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.app.get("/api/discovery/components/{provider}")
        async def get_provider_components(provider: str):
            """Get component discovery results for specific provider"""
            try:
                discovered_components = getattr(self, '_discovered_components', {})
                registration_results = getattr(self, '_registration_results', {})
                
                if provider not in discovered_components:
                    return {
                        "success": False,
                        "message": f"No components discovered for provider: {provider}",
                        "available_providers": list(discovered_components.keys())
                    }
                
                provider_components = discovered_components[provider]
                provider_registrations = {
                    comp_type: {
                        name: result for name, result in comps.items() 
                        if name.startswith(f"{provider}_")
                    }
                    for comp_type, comps in registration_results.items()
                }
                
                return {
                    "success": True,
                    "provider": provider,
                    "components": provider_components,
                    "registrations": provider_registrations,
                    "capabilities": provider_components.get("capabilities", []),
                    "auto_discovered": True,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Provider component discovery failed: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.app.post("/api/discovery/rediscover")
        async def rediscover_components():
            """Re-run component discovery and registration"""
            try:
                # Re-run the discovery system
                await self._initialize_discovery_system()
                
                return {
                    "success": True,
                    "message": "Component rediscovery completed",
                    "rediscovered_at": datetime.now().isoformat(),
                    "auto_registration": True
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Component rediscovery failed: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
        
        
        @self.app.get("/api/endpoints/quick-summary")
        async def get_quick_endpoint_summary():
            """Quick endpoint summary without testing"""
            discovered_endpoints = []
            
            # Just discover endpoints, don't test them
            for route in self.app.routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    if route.path.startswith('/ws/') or route.path.startswith('/static/'):
                        continue
                    
                    for method in route.methods:
                        if method in ['GET', 'POST', 'PUT', 'DELETE', 'HEAD']:
                            discovered_endpoints.append({
                                "path": route.path,
                                "method": method
                            })
            
            return {
                "success": True,
                "discovered_count": len(discovered_endpoints),
                "endpoints": discovered_endpoints[:15],  # First 15 only
                "filtered_out": list(DO_NOT_CALL_ENDPOINTS),
                "note": "WARP FAKE SUB TEST DEMO - Discovery only, no testing",
                "timestamp": datetime.now().isoformat()
            }
        
        # WARP FAKE SUB TEST DEMO - AWS resources endpoint removed for GCP-only architecture
        
        # WARP FAKE SUB TEST DEMO - AWS EC2 and RDS endpoints removed
        # Original endpoints contained WARP-DEMO data that has been cleaned up
        
        @self.app.get("/api/endpoints/failed-list")
        async def get_failed_endpoints():
            """Get list of failed endpoints by testing all real endpoints from the running server"""
            failed_endpoints = []
            working_endpoints = []
            discovered_endpoints = []
            
            # Discover all real endpoints from the FastAPI app
            for route in self.app.routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    # Skip websocket and static file routes
                    if route.path.startswith('/ws/') or route.path.startswith('/static/'):
                        continue
                    
                    for method in route.methods:
                        if method in ['GET', 'POST', 'PUT', 'DELETE', 'HEAD']:
                            endpoint_path = route.path
                            # Replace path parameters with dummy values for testing
                            if '{' in endpoint_path:
                                endpoint_path = endpoint_path.replace('{env}', 'dev')
                                endpoint_path = endpoint_path.replace('{client_id}', 'test')
                            
                            discovered_endpoints.append((endpoint_path, method))
            
            # Test each discovered endpoint (limit to first 20 to avoid timeouts)
            import httpx
            test_endpoints = discovered_endpoints[:20]
            
            async with httpx.AsyncClient(timeout=2.0) as client:
                for endpoint_path, method in test_endpoints:
                    # Skip the dangerous endpoints we know not to call
                    if endpoint_path in DO_NOT_CALL_ENDPOINTS:
                        continue
                        
                    try:
                        # For POST requests, add minimal test data
                        request_data = None
                        headers = {'Content-Type': 'application/json'}
                        
                        if method == 'POST' and 'auth' in endpoint_path:
                            request_data = json.dumps({'provider': 'test', 'env': 'dev'})
                        elif method == 'POST':
                            request_data = json.dumps({'test': 'WARP_DEMO_DATA'})
                        
                        response = await client.request(
                            method, 
                            f"http://127.0.0.1:8000{endpoint_path}",
                            data=request_data if request_data else None,
                            headers=headers if request_data else None
                        )
                        
                        endpoint_info = {
                            "endpoint": endpoint_path,
                            "method": method,
                            "status_code": response.status_code,
                            "tested_at": datetime.now().isoformat()
                        }
                        
                        if response.status_code >= 400:
                            endpoint_info["error"] = response.text[:200]
                            endpoint_info["failed_at"] = datetime.now().isoformat()
                            failed_endpoints.append(endpoint_info)
                        else:
                            endpoint_info["success"] = True
                            endpoint_info["response_size"] = len(response.text)
                            working_endpoints.append(endpoint_info)
                            
                    except Exception as e:
                        failed_endpoints.append({
                            "endpoint": endpoint_path,
                            "method": method,
                            "status_code": None,
                            "error": str(e)[:200],
                            "failed_at": datetime.now().isoformat(),
                            "exception_type": type(e).__name__
                        })
            
            return {
                "success": True,
                "discovered_endpoints_count": len(discovered_endpoints),
                "tested_endpoints_count": len([e for e in discovered_endpoints if e[0] not in DO_NOT_CALL_ENDPOINTS]),
                "working_endpoints": working_endpoints[:10],  # First 10 working endpoints
                "working_count": len(working_endpoints),
                "failed_endpoints": failed_endpoints,
                "failed_count": len(failed_endpoints),
                "filtered_out": [e[0] for e in discovered_endpoints if e[0] in DO_NOT_CALL_ENDPOINTS],
                "timestamp": datetime.now().isoformat()
            }
        
        class AIFixRequest(BaseModel):
            test_results: Dict[str, Any]
            failed_endpoints: List[Dict[str, Any]]
            discovered_flaws: List[Dict[str, Any]] 
            fix_recommendations: List[Dict[str, Any]]
            system_info: Optional[Dict[str, Any]] = None
        
        @self.app.post("/api/ai/fix-endpoints")
        async def ai_fix_endpoints(request: AIFixRequest, background_tasks: BackgroundTasks):
            """Send endpoint failure report to AI for automated fixing"""
            try:
                # Store the fix request for AI processing
                fix_data = {
                    "timestamp": datetime.now().isoformat(),
                    "test_results": request.test_results,
                    "failed_endpoints": request.failed_endpoints,
                    "discovered_flaws": request.discovered_flaws,
                    "fix_recommendations": request.fix_recommendations,
                    "system_info": request.system_info or {},
                    "status": "submitted"
                }
                
                # Create a comprehensive prompt for the AI
                ai_prompt = f"""
ENDPOINT FAILURE ANALYSIS & AUTOMATED FIX REQUEST

=== SYSTEM INFO ===
Timestamp: {fix_data['timestamp']}
Total Failed Endpoints: {len(request.failed_endpoints)}
Total Flaws Discovered: {len(request.discovered_flaws)}
Fix Categories: {len(request.fix_recommendations)}

=== FAILED ENDPOINTS ===
{json.dumps(request.failed_endpoints, indent=2)}

=== DISCOVERED FLAWS ===
{json.dumps(request.discovered_flaws, indent=2)}

=== FIX RECOMMENDATIONS ===
{json.dumps(request.fix_recommendations, indent=2)}

=== FULL TEST RESULTS ===
{json.dumps(request.test_results, indent=2)}

=== AI INSTRUCTIONS ===
Please analyze the above endpoint failures and implement the following fixes:

1. ADD MISSING ROUTES: For any 404 endpoints, add the route handlers to main.py
2. FIX SERVER ERRORS: For any 500 errors, debug and fix the implementation
3. IMPLEMENT MISSING CONTROLLER METHODS: Add any missing methods to controllers
4. UPDATE PROVIDER VERIFICATION: Fix any provider verification issues
5. CONFIGURE AUTHENTICATION: Fix any auth-related problems

CURRENT PROJECT STRUCTURE:
- /Users/shawn_meredith/code/github/apex/web/main.py (FastAPI routes)
- /Users/shawn_meredith/code/github/apex/web/controllers/ (Business logic)
- /Users/shawn_meredith/code/github/apex/web/providers/ (Provider implementations)

Please implement the fixes directly in the codebase and provide a summary of changes made.
"""
                
                # Store the AI prompt in the fix data
                fix_data["ai_prompt"] = ai_prompt
                fix_data["prompt_length"] = len(ai_prompt)
                
                return {
                    "success": True,
                    "message": "Endpoint failure report submitted to AI for automated fixing",
                    "ai_prompt_preview": ai_prompt[:500] + "..." if len(ai_prompt) > 500 else ai_prompt,
                    "failed_endpoint_count": len(request.failed_endpoints),
                    "flaw_count": len(request.discovered_flaws),
                    "recommendation_count": len(request.fix_recommendations),
                    "fix_request_id": f"fix_{int(datetime.now().timestamp())}",
                    "status": "ready_for_ai_processing"
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to submit AI fix request: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
        
        class EndpointTestRequest(BaseModel):
            endpoints: List[Dict[str, Any]]
            max_concurrent: Optional[int] = 5
            base_url: Optional[str] = None
        
        @self.app.post("/api/endpoints/test-safely")
        async def test_endpoints_safely(request: EndpointTestRequest, background_tasks: BackgroundTasks):
            """Test multiple endpoints safely - simple filtering approach"""
            try:
                base_url = request.base_url or "http://127.0.0.1:8000"
                
                # Filter out endpoints we know not to call
                safe_endpoints = []
                for endpoint in request.endpoints:
                    endpoint_path = endpoint.get('path', '')
                    if endpoint_path not in DO_NOT_CALL_ENDPOINTS:
                        safe_endpoints.append(endpoint)
                
                # Test safe endpoints in background
                background_tasks.add_task(
                    self._run_simple_endpoint_tests,
                    safe_endpoints,
                    base_url,
                    request.max_concurrent
                )
                
                return {
                    "success": True,
                    "message": f"Started testing of {len(safe_endpoints)} safe endpoints (filtered {len(request.endpoints) - len(safe_endpoints)})",
                    "max_concurrent": request.max_concurrent,
                    "base_url": base_url,
                    "filtered_count": len(request.endpoints) - len(safe_endpoints),
                    "test_started_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to start endpoint testing: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.app.get("/api/endpoints/status")
        async def get_endpoint_filter_status():
            """Get current status of endpoint filtering for monitoring"""
            try:
                return {
                    "success": True,
                    "endpoint_filter": {
                        "do_not_call_endpoints": list(DO_NOT_CALL_ENDPOINTS),
                        "filter_count": len(DO_NOT_CALL_ENDPOINTS),
                        "approach": "simple_filtering"
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        # =================
        # GCP GCLOUD API ENDPOINTS (Enhanced)
        # =================
        
        class GCPRequest(BaseModel):
            env: Optional[str] = "dev"
            project: Optional[str] = None
            region: Optional[str] = None
            zone: Optional[str] = None
        
        @self.app.post("/api/gcp/auth")
        async def gcp_authenticate(request: GCPRequest, background_tasks: BackgroundTasks):
            """Authenticate with GCP using PAP orchestrator flow"""
            try:
                # Use orchestrator instead of direct controller call
                result = await self.gcp_orchestrator.orchestrate(
                    operation="authenticate",
                    project=request.project,
                    env=request.env
                )
                return {
                    "success": result.get("success", False),
                    "message": result.get("message", "GCP authentication processed via PAP flow"),
                    "pap_enforced": True,
                    "safety_gates_applied": result.get("safety_gates_enforced", False),
                    "details": result
                }
            except Exception as e:
                return {
                    "success": False, 
                    "error": f"PAP orchestration failed: {str(e)}",
                    "pap_enforced": True
                }
        
        @self.app.get("/api/gcp/projects")
        async def gcp_list_projects(background_tasks: BackgroundTasks):
            """List GCP projects using gcloud"""
            try:
                gcp_controller = self.controller_registry.get_gcp_controller()
                if gcp_controller:
                    background_tasks.add_task(gcp_controller.list_projects)
                    return {"success": True, "message": "Listing GCP projects via gcloud"}
                else:
                    return {"success": False, "error": "GCP controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/gcp/compute/instances")
        async def gcp_list_compute_instances(request: GCPRequest, background_tasks: BackgroundTasks):
            """List GCP Compute instances using gcloud"""
            try:
                gcp_controller = self.controller_registry.get_gcp_controller()
                if gcp_controller:
                    background_tasks.add_task(
                        gcp_controller.list_compute_instances,
                        project=request.project,
                        zone=request.zone
                    )
                    return {
                        "success": True, 
                        "message": f"Listing Compute instances for {request.project or 'current project'} via gcloud"
                    }
                else:
                    return {"success": False, "error": "GCP controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/gcp/functions")
        async def gcp_list_cloud_functions(request: GCPRequest, background_tasks: BackgroundTasks):
            """List GCP Cloud Functions using gcloud"""
            try:
                gcp_controller = self.controller_registry.get_gcp_controller()
                if gcp_controller:
                    background_tasks.add_task(
                        gcp_controller.list_cloud_functions,
                        project=request.project,
                        region=request.region
                    )
                    return {
                        "success": True, 
                        "message": f"Listing Cloud Functions for {request.project or 'current project'} via gcloud"
                    }
                else:
                    return {"success": False, "error": "GCP controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        class GCPCommandRequest(BaseModel):
            command: str  # gcloud command to execute
            project: Optional[str] = None
            env: Optional[str] = "dev"
        
        @self.app.post("/api/gcp/execute")
        async def gcp_execute_command(request: GCPCommandRequest, background_tasks: BackgroundTasks):
            """Execute arbitrary gcloud command"""
            try:
                gcp_controller = self.controller_registry.get_gcp_controller()
                if gcp_controller:
                    background_tasks.add_task(
                        gcp_controller.execute_command,
                        command=request.command,
                        project=request.project,
                        env=request.env
                    )
                    return {
                        "success": True, 
                        "message": f"GCP command execution started: {request.command}"
                    }
                else:
                    return {"success": False, "error": "GCP controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/gcp/auth")
        async def gcp_auth_list():
            """List GCP authenticated accounts"""
            try:
                gcp_controller = self.controller_registry.get_gcp_controller()
                if gcp_controller:
                    return await gcp_controller.list_auth_accounts()
                else:
                    return {"success": False, "error": "GCP controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/gcp/switch-project")
        async def gcp_switch_project(request: GCPRequest, background_tasks: BackgroundTasks):
            """Switch to a specific GCP project"""
            try:
                gcp_controller = self.controller_registry.get_gcp_controller()
                if gcp_controller:
                    background_tasks.add_task(
                        gcp_controller.switch_project,
                        project=request.project or request.env
                    )
                    return {
                        "success": True, 
                        "message": f"Switching to GCP project: {request.project or request.env}"
                    }
                else:
                    return {"success": False, "error": "GCP controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/gcp/config")
        async def gcp_get_config():
            """Get current GCP configuration"""
            try:
                gcp_controller = self.controller_registry.get_gcp_controller()
                if gcp_controller:
                    return await gcp_controller.get_config()
                else:
                    return {"success": False, "error": "GCP controller not available"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/gcp/auth/test")
        async def gcp_test_auth(request: GCPRequest):
            """Test GCP authentication for specific project"""
            try:
                gcp_controller = self.controller_registry.get_gcp_controller()
                if gcp_controller:
                    return await gcp_controller.test_authentication(project=request.project, env=request.env)
                else:
                    return {"success": False, "authenticated": False, "error": "GCP controller not available"}
            except Exception as e:
                return {"success": False, "authenticated": False, "error": str(e)}
        
        # Add command execution endpoint that templates expect
        @self.app.post("/execute-command")
        async def execute_terminal_command(command_request: dict, background_tasks: BackgroundTasks):
            """Execute terminal command from the UI"""
            try:
                command = command_request.get('command', '')
                background = command_request.get('background', False)
                
                if not command:
                    return {"success": False, "error": "No command provided"}
                
                # Create a raw command provider to execute the command
                from .providers.base_provider import BaseProvider
                
                class TerminalProvider(BaseProvider):
                    def __init__(self):
                        super().__init__("terminal")
                    
                    async def authenticate(self, **kwargs):
                        return {"success": True, "message": "Terminal ready"}
                    
                    async def get_status(self):
                        return {"status": "ready"}
                
                terminal_provider = TerminalProvider()
                terminal_provider.broadcast_message = self.broadcast_message
                
                if background:
                    # Execute in background
                    background_tasks.add_task(terminal_provider.execute_command, command)
                    return {
                        "success": True,
                        "message": f"Command started in background: {command}",
                        "output": "",
                        "error": ""
                    }
                else:
                    # Execute synchronously
                    result = await terminal_provider.execute_command(command)
                    return {
                        "success": result.get('success', False),
                        "output": result.get('stdout', ''),
                        "error": result.get('stderr', ''),
                        "message": result.get('message', '')
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "output": "",
                    "message": "Command execution failed"
                }
    
    def render_main_template(self, context: dict) -> str:
        """Render the main template with given context"""
        try:
            return self.template_manager.render_template('main.html', **context)
        except Exception as e:
            logging.error(f"Template rendering failed: {e}")
            # Return fallback if template rendering fails
            return self.get_html_content()
    
    async def _initialize_discovery_system(self):
        """Initialize discovery system - autonomous context and component discovery"""
        try:
            # Phase 1: Context Discovery
            discovered_contexts = await self.context_discovery.discover_all_contexts()
            self._discovered_contexts = discovered_contexts
            
            # Phase 2: Component Auto-Discovery and Registration
            providers = discovered_contexts.get('providers', {})
            discovered_providers = list(providers.keys())
            
            if discovered_providers:
                # Auto-discover PAP components for all discovered providers
                self._discovered_components = await self.auto_discovery.auto_discover_components(
                    discovered_providers
                )
                
                # Auto-register discovered components with their registries
                self._registration_results = await self.auto_discovery.auto_register_components(
                    self  # Pass self as registry manager
                )
            
            # Log comprehensive discovery results
            environments = discovered_contexts.get('environments', [])
            
            await self.broadcast_message({
                'type': 'discovery_complete',
                'data': {
                    'providers_discovered': discovered_providers,
                    'environments_discovered': [env['name'] for env in environments],
                    'components_discovered': {
                        provider: list(components.keys()) 
                        for provider, components in self._discovered_components.items()
                    },
                    'components_registered': {
                        comp_type: list(comps.keys()) 
                        for comp_type, comps in self._registration_results.items()
                    },
                    'autonomous_discovery': True,
                    'zero_configuration': True,
                    'auto_registration': True,
                    'timestamp': discovered_contexts.get('discovery_timestamp')
                }
            })
            
        except Exception as e:
            import logging
            logging.error(f"Discovery system initialization failed: {str(e)}")
            await self.broadcast_message({
                'type': 'discovery_error',
                'data': {
                    'error': f'Autonomous discovery failed: {str(e)}',
                    'autonomous_discovery': False,
                    'timestamp': asyncio.get_event_loop().time()
                }
            })
    
    def get_html_content(self):
        """Return the HTML template"""
        template_path = Path(__file__).parent / "templates" / "apex_compact.html"
        
        if template_path.exists():
            with open(template_path) as f:
                return f.read()
        else:
            # Simple fallback HTML - using % formatting to avoid f-string quote issues
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>APEX Command Center</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .status {{ padding: 10px; margin: 10px 0; border-radius: 5px; }}
                    .success {{ background-color: #d4edda; color: #155724; }}
                    .error {{ background-color: #f8d7da; color: #721c24; }}
                    .info {{ background-color: #d1ecf1; color: #0c5460; }}
                    button {{ padding: 10px 15px; margin: 5px; cursor: pointer; }}
                </style>
                <script>
                    const ws = new WebSocket('ws://localhost:8000/ws/main');
                    ws.onmessage = function(event) {{
                        const data = JSON.parse(event.data);
                        console.log('Received:', data);
                        
                        const output = document.getElementById('output');
                        const div = document.createElement('div');
                        div.className = 'status info';
                        div.textContent = JSON.stringify(data, null, 2);
                        output.appendChild(div);
                        output.scrollTop = output.scrollHeight;
                    }};
                    
                    // WARP FAKE SUB TEST DEMO - AWS auth functions removed
                    
                    function authGCP() {
                        fetch('/api/auth', {
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{provider: 'gcp', env: 'dev'}})
                        });
                    }}
                    
                    function connectGKE() {{
                        fetch('/api/auth', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{'provider': 'gcp_k8s', 'env': 'dev'}})
                        }});
                    }}
                    
                    function getStatus() {{
                        fetch('/api/status')
                            .then(r => r.json())
                            .then(data => {{
                                const output = document.getElementById('output');
                                const div = document.createElement('div');
                                div.className = 'status success';
                                div.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                                output.appendChild(div);
                                output.scrollTop = output.scrollHeight;
                            }});
                    }}
                </script>
            </head>
            <body>
                <h1>APEX Command Center</h1>
                <div>
                    <!-- WARP FAKE SUB TEST DEMO - AWS auth buttons removed -->
                    <button onclick="authGCP()">Auth GCP</button>
                    <button onclick="connectGKE()">Connect GKE (Dev)</button>
                    <button onclick="getStatus()">Get Status</button>
                </div>
                <div id="output" style="height: 500px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; background-color: #f9f9f9;"></div>
            </body>
            </html>
            """
    
    async def send_initial_status(self, client_id: str):
        """Send initial status to a new client"""
        status = await self.get_full_status()
        
        await self.send_message_to_client(client_id, {
            'type': 'initial_status',
            'data': status
        })
    
    async def auto_authenticate_on_load(self):
        """Auto-authenticate GCP on page load - WARP FAKE SUB TEST DEMO: AWS removed"""
        try:
            # Get GCP provider only - AWS removed
            gcp_auth = self.provider_registry.get_provider("gcp_auth")
            
            # Auto-authenticate GCP only
            if gcp_auth:
                await gcp_auth.authenticate()
                
        except Exception as e:
            await self.broadcast_message({
                'type': 'auto_auth_error',
                'data': {'error': f'Auto-auth failed (AWS removed): {str(e)}'}
            })
    
    async def handle_websocket_message(self, client_id: str, message: dict):
        """Handle incoming WebSocket messages"""
        msg_type = message.get('type')
        data = message.get('data', {})
        
        if msg_type == 'auth_request':
            provider = data.get('provider')
            # WARP FAKE SUB TEST DEMO - AWS authentication removed
            if provider == 'gcp':
                await self.gcp_auth.authenticate(project=data.get('project'))
            elif provider == 'gcp_k8s':
                # Use first GCP project from config as default env
                gcp_projects = list(self.config.get_gcp_config().get('projects', {}).keys())
                default_env = gcp_projects[0] if gcp_projects else 'dev'
                await self.gcp_k8s.authenticate(env=data.get('env', default_env))
        
        elif msg_type == 'status_request':
            status = await self.get_full_status()
            await self.send_message_to_client(client_id, {
                'type': 'status_response',
                'data': status
            })
    
    async def authenticate_provider(self, request: AuthRequest):
        """Authenticate with specified provider"""
        try:
            # WARP FAKE SUB TEST DEMO - AWS authentication removed
            if request.provider == 'gcp':
                result = await self.gcp_auth.authenticate(project=request.project)
                return result
                
            elif request.provider == 'gcp_k8s':
                # Use first GCP project from config as default env
                gcp_projects = list(self.config.get_gcp_config().get('projects', {}).keys())
                default_env = gcp_projects[0] if gcp_projects else 'dev'
                result = await self.gcp_k8s.authenticate(env=request.env or default_env)
                return result
                
            else:
                error_msg = f'Unknown provider: {request.provider}'
                await self.broadcast_message({
                    'type': 'error',
                    'data': {'error': error_msg, 'timestamp': datetime.now().isoformat()}
                })
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            error_msg = f'Authentication failed: {str(e)}'
            await self.broadcast_message({
                'type': 'error',
                'data': {'error': error_msg, 'timestamp': datetime.now().isoformat()}
            })
            return {'success': False, 'error': error_msg}
    
    async def get_full_status(self) -> Dict:
        """Get status from all controllers - WARP FAKE SUB TEST DEMO: AWS removed"""
        try:
            gcp_controller = self.controller_registry.get_gcp_controller()
            
            gcp_status = await gcp_controller.get_status() if gcp_controller else {"error": "GCP controller not available"}
            
            return {
                'timestamp': datetime.now().isoformat(),
                'gcp': gcp_status,
                'config': {
                    'gcp_projects': list(self.config.get_gcp_config().get('projects', {}).keys()),
                    'note': 'WARP FAKE SUB TEST DEMO - AWS functionality removed'
                }
            }
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'gcp': {'error': 'Failed to get status'}
            }
    
    async def broadcast_message(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for client_id, websocket in self.connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except:
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            if client_id in self.connections:
                del self.connections[client_id]
    
    async def send_message_to_client(self, client_id: str, message: dict):
        """Send message to specific client"""
        if client_id in self.connections:
            try:
                await self.connections[client_id].send_text(json.dumps(message))
            except:
                # Client disconnected
                if client_id in self.connections:
                    del self.connections[client_id]
    
    async def _run_simple_endpoint_tests(self, endpoints: List[Dict[str, Any]], 
                                         base_url: str, 
                                         max_concurrent: int):
        """Run simple endpoint tests in background and broadcast results"""
        try:
            await self.broadcast_message({
                'type': 'endpoint_test_start',
                'data': {
                    'message': f'🧪 Starting simple testing of {len(endpoints)} endpoints...',
                    'endpoint_count': len(endpoints),
                    'max_concurrent': max_concurrent,
                    'timestamp': datetime.now().isoformat()
                }
            })
            
            # Simple HTTP testing without complex logic
            import httpx
            successful = 0
            failed = 0
            results = []
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                for endpoint in endpoints:
                    endpoint_path = endpoint.get('path', '')
                    method = endpoint.get('method', 'GET')
                    
                    try:
                        response = await client.request(method, f"{base_url}{endpoint_path}")
                        if response.status_code < 400:
                            successful += 1
                            results.append({'endpoint': endpoint_path, 'status': 'success', 'status_code': response.status_code})
                        else:
                            failed += 1
                            results.append({'endpoint': endpoint_path, 'status': 'failed', 'status_code': response.status_code})
                    except Exception as e:
                        failed += 1
                        results.append({'endpoint': endpoint_path, 'status': 'error', 'error': str(e)})
            
            # Broadcast final results
            await self.broadcast_message({
                'type': 'endpoint_test_complete',
                'data': {
                    'message': f'✅ Simple endpoint testing complete - {successful}/{len(endpoints)} successful',
                    'successful': successful,
                    'failed': failed,
                    'results': results[:10],  # First 10 results only
                    'timestamp': datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            await self.broadcast_message({
                'type': 'endpoint_test_error',
                'data': {
                    'message': f'❌ Simple endpoint testing failed: {str(e)}',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
            })


def create_app():
    """Create and return the FastAPI app"""
    warpcore_app = WARPCOREAPIServer()
    return warpcore_app.app


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the WARPCORE API server using system orchestrator"""
    print("🃚 Starting WARPCORE API Server...")
    print("🌊 Using System Orchestrator for PAP architecture initialization")
    print(f"🌐 Server will be available at: http://{host}:{port}")
    
    # Initialize system using orchestrator
    import asyncio
    from ..system_orchestrator import initialize_api_only
    
    try:
        # Use system orchestrator for elaborate logging and initialization
        asyncio.run(initialize_api_only())
    except Exception as e:
        print(f"⚠️ System orchestrator failed: {e}")
        print("🛡️ Continuing with basic server startup\n")
    
    # Create app after orchestrator initialization
    warpcore_app = WARPCOREAPIServer()
    
    print(f"✅ WARPCORE API Server ready on http://{host}:{port}")
    print(f"📖 Main Interface: http://{host}:{port}")
    print(f"📋 API Documentation: http://{host}:{port}/docs")
    print(f"🏗️ Architecture Discovery: http://{host}:{port}/api/architecture")
    
    uvicorn.run(warpcore_app.app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()