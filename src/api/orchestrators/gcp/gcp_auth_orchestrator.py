"""
WARPCORE GCP Authentication Orchestrator
PAP Layer 3: Compose authentication workflows across providers
"""

from ..base_orchestrator import BaseOrchestrator
from typing import Dict, Any

class GCPAuthOrchestrator(BaseOrchestrator):
    """Orchestrate GCP authentication workflows"""
    
    def __init__(self):
        super().__init__("gcp_auth_orchestrator")
    
    async def orchestrate(self, **kwargs) -> Dict[str, Any]:
        """Main orchestration entry point"""
        operation = kwargs.get("operation", "authenticate")
        
        if operation == "authenticate":
            return await self.orchestrate_authentication(**kwargs)
        elif operation == "discover_projects":
            return await self.orchestrate_project_discovery(**kwargs)
        elif operation == "status_check":
            return await self.orchestrate_status_check(**kwargs)
        else:
            return {"success": False, "error": f"Unknown operation: {operation}"}
    
    async def orchestrate_authentication(self, project: str = None, **kwargs) -> Dict[str, Any]:
        """Orchestrate complete GCP authentication workflow"""
        
        # Define authentication workflow
        auth_workflow = [
            {
                "name": "check_gcloud_available",
                "provider": "gcp",
                "operation": "_check_gcloud_available",
                "params": {}
            },
            {
                "name": "check_current_auth",
                "provider": "gcp", 
                "operation": "_check_auth_status",
                "params": {}
            }
        ]
        
        # Execute pre-auth checks
        workflow_result = await self.compose_workflow(auth_workflow)
        if not workflow_result.get("success"):
            return workflow_result
        
        # Check if already authenticated
        auth_check_result = workflow_result["results"][1]["result"]
        if auth_check_result.get("authenticated", False):
            return {
                "success": True,
                "message": "Already authenticated with GCP",
                "already_authenticated": True,
                "auth_status": auth_check_result
            }
        
        # Perform authentication
        gcp_provider = self.get_provider("gcp")
        if not gcp_provider:
            return {"success": False, "error": "GCP provider not available"}
        
        # Execute authentication through PAP workflow with safety gates
        auth_workflow = [{
            "name": "gcp_authenticate",
            "provider": "gcp",
            "operation": "authenticate", 
            "params": {"project": project},
            "requires_safety_gate": True,
            "command": ["gcloud", "auth", "login", "--no-launch-browser"]
        }]
        
        context = {
            "provider": "gcp", 
            "operation": "authenticate",
            "project": project,
            "orchestrator": self.name
        }
        
        auth_workflow_result = await self.compose_workflow_with_safety(auth_workflow, context)
        if not auth_workflow_result.get("success"):
            return auth_workflow_result
        
        auth_result = auth_workflow_result["results"][0]["result"]
        
        if auth_result.get("success"):
            # Post-authentication validation workflow
            validation_workflow = [
                {
                    "name": "validate_auth",
                    "provider": "gcp",
                    "operation": "_check_auth_status", 
                    "params": {}
                },
                {
                    "name": "get_current_project",
                    "provider": "gcp",
                    "operation": "_discover_current_project",
                    "params": {}
                }
            ]
            
            validation_result = await self.compose_workflow(validation_workflow)
            
            return {
                "success": True,
                "message": "GCP authentication workflow completed",
                "auth_result": auth_result,
                "validation": validation_result
            }
        else:
            return auth_result
    
    async def orchestrate_project_discovery(self, **kwargs) -> Dict[str, Any]:
        """Orchestrate GCP project discovery workflow"""
        
        discovery_workflow = [
            {
                "name": "check_auth",
                "provider": "gcp",
                "operation": "_check_auth_status",
                "params": {}
            },
            {
                "name": "list_projects",
                "provider": "gcp", 
                "operation": "_discover_available_projects",
                "params": {}
            },
            {
                "name": "get_current_project",
                "provider": "gcp",
                "operation": "_discover_current_project", 
                "params": {}
            }
        ]
        
        result = await self.compose_workflow(discovery_workflow)
        
        if result.get("success"):
            # Extract meaningful data from workflow results
            auth_status = result["results"][0]["result"]
            available_projects = result["results"][1]["result"] 
            current_project = result["results"][2]["result"]
            
            return {
                "success": True,
                "authenticated": auth_status.get("authenticated", False),
                "current_project": current_project,
                "available_projects": available_projects,
                "project_count": len(available_projects) if available_projects else 0
            }
        
        return result
    
    async def orchestrate_status_check(self, **kwargs) -> Dict[str, Any]:
        """Orchestrate comprehensive GCP status check"""
        
        gcp_provider = self.get_provider("gcp")
        if not gcp_provider:
            return {"success": False, "error": "GCP provider not available"}
        
        # Get self-description which includes comprehensive status
        return await gcp_provider.get_self_description()