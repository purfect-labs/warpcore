"""
WARPCORE Context Discovery System
Replace hardcoded environments with discovery-driven context inference
"""

import asyncio
import os
import subprocess
from typing import Dict, Any, List, Optional, Set
from .github_discovery import GitHubDiscovery
from .provider_discovery import ProviderDiscoveryRegistry


class ContextDiscoverySystem:
    """Autonomous context discovery to replace hardcoded environments"""
    
    def __init__(self):
        self.github_discovery = GitHubDiscovery()
        self.provider_discovery = ProviderDiscoveryRegistry()
        self.discovered_contexts = {}
        self.inferred_environments = []
        self.port_assignments = {}
    
    async def discover_all_contexts(self) -> Dict[str, Any]:
        """Discover all operational contexts autonomously"""
        
        # Phase 1: Git/GitHub context discovery
        github_contexts = await self.github_discovery.discover_contexts()
        
        # Phase 2: Abstract provider discovery (GCP, Kubernetes, etc.)
        provider_contexts = await self.provider_discovery.discover_all_providers()
        
        # Phase 3: Infer operational environments from discovered providers
        environments = self._infer_environments_from_providers(
            github_contexts, provider_contexts
        )
        
        # Phase 4: Dynamic port assignment
        port_assignments = self._assign_dynamic_ports(environments)
        
        self.discovered_contexts = {
            "github": github_contexts,
            "providers": provider_contexts,
            "environments": environments,
            "ports": port_assignments,
            "discovery_timestamp": asyncio.get_event_loop().time()
        }
        
        return self.discovered_contexts
    
    async def _discover_available_tools(self) -> Dict[str, Any]:
        """Discover available command-line tools"""
        tools_to_check = [
            "gcloud", "kubectl", "aws", "git", "gh", "docker", 
            "terraform", "helm", "istioctl", "kustomize"
        ]
        
        available_tools = {}
        
        for tool in tools_to_check:
            try:
                # Check if tool is available and get version
                result = await self._run_command([tool, "--version"])
                if result["exit_code"] == 0:
                    available_tools[tool] = {
                        "available": True,
                        "version": result["stdout"].strip()[:100],  # First 100 chars
                        "path": await self._get_tool_path(tool)
                    }
                else:
                    available_tools[tool] = {"available": False}
            except Exception:
                available_tools[tool] = {"available": False}
        
        self.tool_availability = available_tools
        return available_tools
    
    async def _discover_cloud_contexts(self) -> Dict[str, Any]:
        """Discover GCP authentication and project contexts (GCP prototype only)"""
        return {
            "gcp": await self._discover_gcp_context()
        }
    
    async def _discover_gcp_context(self) -> Dict[str, Any]:
        """Discover GCP authentication status and projects"""
        if not self.tool_availability.get("gcloud", {}).get("available"):
            return {"available": False, "reason": "gcloud not installed"}
        
        try:
            # Check authentication status
            auth_result = await self._run_command(["gcloud", "auth", "list", "--format=json"])
            
            # Get current project
            project_result = await self._run_command(["gcloud", "config", "get-value", "project"])
            
            # List available projects
            projects_result = await self._run_command(["gcloud", "projects", "list", "--format=json", "--limit=50"])
            
            import json
            
            auth_accounts = []
            if auth_result["exit_code"] == 0:
                try:
                    auth_data = json.loads(auth_result["stdout"])
                    auth_accounts = [acc for acc in auth_data if acc.get("status") == "ACTIVE"]
                except:
                    pass
            
            current_project = project_result["stdout"].strip() if project_result["exit_code"] == 0 else None
            
            available_projects = []
            if projects_result["exit_code"] == 0:
                try:
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
                "available": True,
                "authenticated": len(auth_accounts) > 0,
                "current_project": current_project,
                "auth_accounts": auth_accounts,
                "available_projects": available_projects,
                "project_count": len(available_projects)
            }
        
        except Exception as e:
            return {"available": True, "error": str(e), "authenticated": False}
    
    
    async def _discover_k8s_contexts(self) -> Dict[str, Any]:
        """Discover Kubernetes contexts and clusters"""
        if not self.tool_availability.get("kubectl", {}).get("available"):
            return {"available": False, "reason": "kubectl not installed"}
        
        try:
            # Get current context
            current_context_result = await self._run_command(["kubectl", "config", "current-context"])
            
            # Get all contexts
            contexts_result = await self._run_command(["kubectl", "config", "get-contexts", "-o", "name"])
            
            current_context = current_context_result["stdout"].strip() if current_context_result["exit_code"] == 0 else None
            
            available_contexts = []
            if contexts_result["exit_code"] == 0:
                available_contexts = [ctx.strip() for ctx in contexts_result["stdout"].split('\n') if ctx.strip()]
            
            # Try to get cluster info for current context
            cluster_info = None
            if current_context:
                cluster_result = await self._run_command(["kubectl", "cluster-info", "--request-timeout=5s"])
                if cluster_result["exit_code"] == 0:
                    cluster_info = cluster_result["stdout"][:200]  # First 200 chars
            
            return {
                "available": True,
                "current_context": current_context,
                "available_contexts": available_contexts,
                "context_count": len(available_contexts),
                "cluster_info": cluster_info,
                "connected": cluster_info is not None
            }
        
        except Exception as e:
            return {"available": True, "error": str(e), "connected": False}
    
    def _infer_environments_from_providers(self, github_ctx: Dict, provider_ctx: Dict) -> List[Dict[str, Any]]:
        """Use actual provider contexts as environments - no substring parsing"""
        
        environments = []
        
        # Use actual provider contexts as environments
        for provider_name, provider_data in provider_ctx.items():
            if not provider_data.get("available"):
                continue
                
            # Each provider contributes their own contexts as environments
            if provider_name == "gcp":
                # Use actual GCP projects as environments
                gcp_projects = provider_data.get("available_projects", [])
                for project in gcp_projects:
                    environments.append({
                        "name": project.get("project_id"),
                        "display_name": project.get("name", project.get("project_id")),
                        "type": "gcp_project",
                        "provider": "gcp",
                        "status": project.get("status", "UNKNOWN"),
                        "sources": ["gcp_projects"],
                        "capabilities": ["gcp"] if provider_data.get("authenticated") else []
                    })
                    
            elif provider_name == "aws":
                # Use actual AWS accounts/profiles as environments
                aws_profiles = provider_data.get("available_profiles", [])
                for profile in aws_profiles:
                    environments.append({
                        "name": profile.get("profile_name", profile),
                        "display_name": profile.get("account_name", profile),
                        "type": "aws_account",
                        "provider": "aws",
                        "sources": ["aws_profiles"],
                        "capabilities": ["aws"] if provider_data.get("authenticated") else []
                    })
                    
            elif provider_name == "kubernetes":
                # Use actual K8s contexts as environments
                k8s_contexts = provider_data.get("available_contexts", [])
                for context in k8s_contexts:
                    environments.append({
                        "name": context,
                        "display_name": context,
                        "type": "k8s_context",
                        "provider": "kubernetes", 
                        "sources": ["kubernetes_contexts"],
                        "capabilities": ["kubernetes"] if provider_data.get("connected") else []
                    })
                    
            # Other providers can add their contexts here following the same pattern
        
        # If no provider environments discovered, add a fallback
        if not environments:
            import os
            current_dir = os.path.basename(os.getcwd())
            current_user = github_ctx.get("user", {}).get("username", os.getenv("USER", "user"))
            
            environments.append({
                "name": f"{current_dir}-{current_user}",
                "display_name": f"Local {current_dir}",
                "type": "local_fallback",
                "provider": "local",
                "sources": ["fallback"],
                "capabilities": []
            })
        
        self.inferred_environments = environments
        return environments
    
    def _assign_dynamic_ports(self, environments: List[Dict]) -> Dict[str, Any]:
        """Dynamically assign ports based on discovered environments"""
        
        base_port = 20000  # Start from port 20000
        port_assignments = {}
        
        for i, env in enumerate(environments):
            env_name = env["name"]
            assigned_port = base_port + i + 1
            
            port_assignments[env_name] = {
                "kiali_port": assigned_port,
                "proxy_port": assigned_port + 100,
                "forward_port": assigned_port + 200,
                "debug_port": assigned_port + 300
            }
        
        # Add system ports
        port_assignments["system"] = {
            "api_port": 8000,  # Main API port (configurable)
            "websocket_port": 8000,  # Same as API for now
            "health_port": 8001
        }
        
        self.port_assignments = port_assignments
        return port_assignments
    
    async def _run_command(self, command: List[str]) -> Dict[str, Any]:
        """Run shell command and return result"""
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
    
    async def _get_tool_path(self, tool: str) -> Optional[str]:
        """Get the full path of a tool"""
        try:
            result = await self._run_command(["which", tool])
            if result["exit_code"] == 0:
                return result["stdout"].strip()
        except:
            pass
        return None
    
    def get_environment_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get discovered environment by name"""
        for env in self.inferred_environments:
            if env["name"] == name:
                return env
        return None
    
    def get_ports_for_environment(self, env_name: str) -> Dict[str, int]:
        """Get dynamically assigned ports for environment"""
        return self.port_assignments.get(env_name, {})
    
    def get_available_environments(self) -> List[str]:
        """Get list of all discovered environment names"""
        return [env["name"] for env in self.inferred_environments]