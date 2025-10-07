"""
WARPCORE GCP Controller
Business logic controller for GCP operations
"""

from typing import Dict, Any
from .base_controller import BaseController


class GCPController(BaseController):
    """Controller for GCP operations"""
    
    def __init__(self):
        super().__init__("gcp")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get GCP authentication and project status"""
        gcp_auth_provider = self.get_provider("gcp_auth")
        
        if not gcp_auth_provider:
            return {
                "success": False,
                "authenticated": False,
                "error": "GCP authentication provider not available",
                "controller": self.name
            }
        
        try:
            auth_status = await gcp_auth_provider.get_status()
            return {
                "success": True,
                "controller": self.name,
                **auth_status
            }
        except Exception as e:
            return {
                "success": False,
                "authenticated": False,
                "error": f"Failed to get GCP status: {str(e)}",
                "controller": self.name
            }
    
    async def authenticate(self, project: str = None, **kwargs) -> Dict[str, Any]:
        """Authenticate with GCP"""
        gcp_auth_provider = self.get_provider("gcp_auth")
        
        if not gcp_auth_provider:
            return {
                "success": False,
                "error": "GCP authentication provider not available"
            }
        
        try:
            result = await gcp_auth_provider.authenticate(project=project, **kwargs)
            
            # Broadcast controller-level status update
            if result.get("success"):
                await self.broadcast_message({
                    "type": "controller_auth_success",
                    "data": {
                        "controller": self.name,
                        "provider": "gcp",
                        "account": result.get("active_account"),
                        "project": result.get("current_project")
                    }
                })
            
            return result
            
        except Exception as e:
            error_msg = f"GCP authentication failed: {str(e)}"
            await self.broadcast_message({
                "type": "controller_auth_error", 
                "data": {
                    "controller": self.name,
                    "error": error_msg
                }
            })
            return {
                "success": False,
                "error": error_msg
            }
    
    async def get_projects(self) -> Dict[str, Any]:
        """Get available GCP projects"""
        try:
            status = await self.get_status()
            if status.get("authenticated"):
                return {
                    "success": True,
                    "projects": status.get("configured_projects", []),
                    "current_project": status.get("current_project"),
                    "project_details": status.get("project_details", {})
                }
            else:
                return {
                    "success": False,
                    "error": "Not authenticated with GCP",
                    "projects": []
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get GCP projects: {str(e)}",
                "projects": []
            }
    
    async def switch_project(self, project: str) -> Dict[str, Any]:
        """Switch to a different GCP project"""
        gcp_auth_provider = self.get_provider("gcp_auth")
        
        if not gcp_auth_provider:
            return {
                "success": False,
                "error": "GCP authentication provider not available"
            }
        
        try:
            result = await gcp_auth_provider.set_project(project)
            
            if result.get("success"):
                await self.broadcast_message({
                    "type": "gcp_project_switched",
                    "data": {
                        "controller": self.name,
                        "project": project,
                        "message": f"Switched to GCP project: {project}"
                    }
                })
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to switch project: {str(e)}"
            }