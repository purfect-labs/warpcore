"""
WARPCORE GCP Provider - Self-describing with real system discovery
PAP Layer 4: External integrations with introspection capabilities
"""

import asyncio
import subprocess
import json
from typing import Dict, Any, List
from ..base_provider import BaseProvider

class GCPProvider(BaseProvider):
    """Self-describing GCP provider with system discovery"""
    
    def __init__(self):
        super().__init__("gcp")
    
    async def get_self_description(self) -> Dict[str, Any]:
        """Describe current GCP state and capabilities"""
        try:
            current_project = await self._discover_current_project()
            available_projects = await self._discover_available_projects()
            auth_status = await self._check_auth_status()
            
            return {
                "provider": "gcp",
                "authenticated": auth_status.get("authenticated", False),
                "current_project": current_project,
                "available_projects": available_projects,
                "capabilities": [
                    "authenticate",
                    "list_projects", 
                    "list_compute_instances",
                    "list_storage_buckets",
                    "list_functions"
                ],
                "cli_tool": "gcloud",
                "cli_available": await self._check_gcloud_available()
            }
        except Exception as e:
            return {
                "provider": "gcp",
                "error": f"Self-description failed: {str(e)}",
                "authenticated": False
            }
    
    async def authenticate(self, project: str = None) -> Dict[str, Any]:
        """Authenticate with GCP using real gcloud CLI"""
        try:
            if project:
                # Set project first
                cmd = ["gcloud", "config", "set", "project", project]
                result = await self._run_command(cmd)
                if result["exit_code"] != 0:
                    return {
                        "success": False,
                        "error": f"Failed to set project {project}: {result['stderr']}"
                    }
            
            # Authenticate 
            cmd = ["gcloud", "auth", "login", "--no-launch-browser"]
            result = await self._run_command(cmd)
            
            if result["exit_code"] == 0:
                # Get current user info
                user_info = await self._get_current_user()
                return {
                    "success": True,
                    "message": "GCP authentication successful",
                    "user": user_info.get("email"),
                    "project": project or await self._discover_current_project()
                }
            else:
                return {
                    "success": False,
                    "error": f"Authentication failed: {result['stderr']}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Authentication error: {str(e)}"
            }
    
    async def list_projects(self) -> Dict[str, Any]:
        """List available GCP projects"""
        try:
            projects = await self._discover_available_projects()
            return {
                "success": True,
                "projects": projects,
                "count": len(projects)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list projects: {str(e)}"
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current GCP status"""
        return await self.get_self_description()
    
    # Private discovery methods
    async def _discover_current_project(self) -> str:
        """Discover current GCP project from gcloud config"""
        try:
            cmd = ["gcloud", "config", "get-value", "project"]
            result = await self._run_command(cmd)
            if result["exit_code"] == 0:
                return result["stdout"].strip()
            return None
        except:
            return None
    
    async def _discover_available_projects(self) -> List[Dict[str, str]]:
        """Discover available GCP projects"""
        try:
            cmd = ["gcloud", "projects", "list", "--format=json"]
            result = await self._run_command(cmd)
            if result["exit_code"] == 0:
                projects_data = json.loads(result["stdout"])
                return [
                    {
                        "name": p.get("name"),
                        "id": p.get("projectId"),
                        "status": p.get("lifecycleState")
                    }
                    for p in projects_data
                ]
            return []
        except Exception as e:
            return []
    
    async def _check_auth_status(self) -> Dict[str, Any]:
        """Check if authenticated with GCP"""
        try:
            cmd = ["gcloud", "auth", "list", "--format=json"]
            result = await self._run_command(cmd)
            if result["exit_code"] == 0:
                auth_data = json.loads(result["stdout"])
                active_accounts = [acc for acc in auth_data if acc.get("status") == "ACTIVE"]
                return {
                    "authenticated": len(active_accounts) > 0,
                    "accounts": active_accounts
                }
            return {"authenticated": False}
        except:
            return {"authenticated": False}
    
    async def _get_current_user(self) -> Dict[str, str]:
        """Get current authenticated user info"""
        try:
            cmd = ["gcloud", "config", "get-value", "account"]
            result = await self._run_command(cmd)
            if result["exit_code"] == 0:
                return {"email": result["stdout"].strip()}
            return {}
        except:
            return {}
    
    async def _check_gcloud_available(self) -> bool:
        """Check if gcloud CLI is available"""
        try:
            cmd = ["gcloud", "--version"]
            result = await self._run_command(cmd)
            return result["exit_code"] == 0
        except:
            return False
    
    async def _run_command(self, cmd: List[str]) -> Dict[str, Any]:
        """Run command and return result"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
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