"""
WARPCORE Abstract Provider Discovery System
Discover and register available providers (GCP, GitHub, CircleCI, etc.)
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set


class BaseProviderDiscovery(ABC):
    """Abstract base for provider discovery implementations"""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.capabilities = []
        self.available = False
        self.authenticated = False
    
    @abstractmethod
    async def discover(self) -> Dict[str, Any]:
        """Discover provider availability and context"""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> List[str]:
        """Get list of provider capabilities"""
        pass
    
    async def is_available(self) -> bool:
        """Check if provider is available"""
        return self.available
    
    async def is_authenticated(self) -> bool:
        """Check if provider is authenticated"""
        return self.authenticated


class GCPProviderDiscovery(BaseProviderDiscovery):
    """GCP provider discovery implementation"""
    
    def __init__(self):
        super().__init__("gcp")
    
    async def discover(self) -> Dict[str, Any]:
        """Discover GCP context and authentication"""
        # Check if gcloud is available
        gcloud_available = await self._check_tool_available("gcloud")
        if not gcloud_available:
            return {"available": False, "reason": "gcloud not installed"}
        
        self.available = True
        
        # Check authentication
        auth_result = await self._run_command(["gcloud", "auth", "list", "--format=json"])
        auth_accounts = []
        if auth_result["exit_code"] == 0:
            try:
                import json
                auth_data = json.loads(auth_result["stdout"])
                auth_accounts = [acc for acc in auth_data if acc.get("status") == "ACTIVE"]
                self.authenticated = len(auth_accounts) > 0
            except:
                pass
        
        # Get current project
        project_result = await self._run_command(["gcloud", "config", "get-value", "project"])
        current_project = project_result["stdout"].strip() if project_result["exit_code"] == 0 else None
        
        # List available projects
        projects_result = await self._run_command(["gcloud", "projects", "list", "--format=json", "--limit=50"])
        available_projects = []
        if projects_result["exit_code"] == 0:
            try:
                import json
                projects_data = json.loads(projects_result["stdout"])
                available_projects = [
                    {
                        "project_id": p["projectId"],
                        "name": p.get("name", p["projectId"]),
                        "status": p.get("lifecycleState", "UNKNOWN")
                    }
                    for p in projects_data
                ]
            except:
                pass
        
        return {
            "provider": self.provider_name,
            "available": True,
            "authenticated": self.authenticated,
            "current_project": current_project,
            "auth_accounts": auth_accounts,
            "available_projects": available_projects,
            "project_count": len(available_projects)
        }
    
    async def get_capabilities(self) -> List[str]:
        """Get GCP provider capabilities"""
        if not self.available:
            return []
        
        capabilities = ["authentication", "projects", "compute"]
        
        if self.authenticated:
            capabilities.extend(["gke", "cloud-functions", "storage", "iam"])
        
        return capabilities
    
    async def _check_tool_available(self, tool: str) -> bool:
        """Check if a tool is available"""
        try:
            result = await self._run_command([tool, "--version"])
            return result["exit_code"] == 0
        except:
            return False
    
    async def _run_command(self, command: List[str]) -> Dict[str, Any]:
        """Run command and return result"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return {
                "exit_code": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode()
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e)
            }


class KubernetesProviderDiscovery(BaseProviderDiscovery):
    """Kubernetes provider discovery implementation"""
    
    def __init__(self):
        super().__init__("kubernetes")
    
    async def discover(self) -> Dict[str, Any]:
        """Discover Kubernetes context"""
        # Check if kubectl is available
        kubectl_available = await self._check_tool_available("kubectl")
        if not kubectl_available:
            return {"available": False, "reason": "kubectl not installed"}
        
        self.available = True
        
        # Get current context
        current_context_result = await self._run_command(["kubectl", "config", "current-context"])
        current_context = current_context_result["stdout"].strip() if current_context_result["exit_code"] == 0 else None
        
        # Get all contexts
        contexts_result = await self._run_command(["kubectl", "config", "get-contexts", "-o", "name"])
        available_contexts = []
        if contexts_result["exit_code"] == 0:
            available_contexts = [ctx.strip() for ctx in contexts_result["stdout"].split('\n') if ctx.strip()]
        
        # Check connectivity
        cluster_connected = False
        if current_context:
            cluster_result = await self._run_command(["kubectl", "cluster-info", "--request-timeout=5s"])
            cluster_connected = cluster_result["exit_code"] == 0
        
        self.authenticated = cluster_connected
        
        return {
            "provider": self.provider_name,
            "available": True,
            "authenticated": self.authenticated,
            "current_context": current_context,
            "available_contexts": available_contexts,
            "context_count": len(available_contexts),
            "connected": cluster_connected
        }
    
    async def get_capabilities(self) -> List[str]:
        """Get Kubernetes provider capabilities"""
        if not self.available:
            return []
        
        capabilities = ["contexts", "cluster-info"]
        
        if self.authenticated:
            capabilities.extend(["pods", "services", "deployments", "namespaces", "port-forward"])
        
        return capabilities
    
    async def _check_tool_available(self, tool: str) -> bool:
        """Check if a tool is available"""
        try:
            result = await self._run_command([tool, "--version"])
            return result["exit_code"] == 0
        except:
            return False
    
    async def _run_command(self, command: List[str]) -> Dict[str, Any]:
        """Run command and return result"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return {
                "exit_code": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode()
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e)
            }


class ProviderDiscoveryRegistry:
    """Registry for managing provider discovery implementations"""
    
    def __init__(self):
        self.discovery_providers = {}
        self.discovered_contexts = {}
        
        # Register GCP provider only for focused POC
        self.register_discovery_provider("gcp", GCPProviderDiscovery())
        # Kubernetes removed for GCP-focused POC
        # More providers can be added later: GitHub, CircleCI, etc.
    
    def register_discovery_provider(self, name: str, discovery_provider: BaseProviderDiscovery):
        """Register a provider discovery implementation"""
        self.discovery_providers[name] = discovery_provider
    
    async def discover_all_providers(self) -> Dict[str, Any]:
        """Discover all registered providers"""
        discovered = {}
        
        for name, discovery_provider in self.discovery_providers.items():
            try:
                provider_context = await discovery_provider.discover()
                capabilities = await discovery_provider.get_capabilities()
                
                discovered[name] = {
                    **provider_context,
                    "capabilities": capabilities
                }
            except Exception as e:
                discovered[name] = {
                    "provider": name,
                    "available": False,
                    "error": str(e)
                }
        
        self.discovered_contexts = discovered
        return discovered
    
    def get_provider_context(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get discovered context for a specific provider"""
        return self.discovered_contexts.get(provider_name)
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names"""
        return [
            name for name, context in self.discovered_contexts.items()
            if context.get("available", False)
        ]
    
    def get_authenticated_providers(self) -> List[str]:
        """Get list of authenticated provider names"""
        return [
            name for name, context in self.discovered_contexts.items()
            if context.get("authenticated", False)
        ]