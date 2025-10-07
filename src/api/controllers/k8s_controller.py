"""
WARPCORE K8s Controller
Business logic controller for Kubernetes operations
"""

from typing import Dict, Any
from .base_controller import BaseController


class K8sController(BaseController):
    """Controller for Kubernetes operations - PAP compliant with orchestrator delegation"""
    
    def __init__(self):
        super().__init__("k8s")
        self.orchestrator_registry = None
    
    def set_orchestrator_registry(self, orchestrator_registry):
        """Wire up orchestrator registry for PAP compliance"""
        self.orchestrator_registry = orchestrator_registry
    
    def get_k8s_orchestrator(self):
        """Get K8s orchestrator through registry"""
        if self.orchestrator_registry:
            return self.orchestrator_registry.get_orchestrator("k8s")
        return None
    
    async def get_status(self) -> Dict[str, Any]:
        """Get Kubernetes cluster status via orchestrator"""
        try:
            k8s_orchestrator = self.get_k8s_orchestrator()
            if not k8s_orchestrator:
                return {
                    "success": False,
                    "error": "K8s orchestrator not available - PAP compliance required"
                }
            
            # Delegate to orchestrator following PAP pattern
            return await k8s_orchestrator.get_status_operation()
            
        except Exception as e:
            return {
                "success": False,
                "error": f"K8s controller error: {str(e)}"
            }
    
    async def get_clusters(self) -> Dict[str, Any]:
        """Get available Kubernetes clusters via orchestrator"""
        try:
            k8s_orchestrator = self.get_k8s_orchestrator()
            if not k8s_orchestrator:
                return {
                    "success": False,
                    "error": "K8s orchestrator not available - PAP compliance required"
                }
            
            # Delegate to orchestrator following PAP pattern
            return await k8s_orchestrator.get_clusters_operation()
            
        except Exception as e:
            return {
                "success": False,
                "error": f"K8s controller error: {str(e)}"
            }
    
    async def switch_context(self, context: str) -> Dict[str, Any]:
        """Switch Kubernetes context via orchestrator"""
        try:
            k8s_orchestrator = self.get_k8s_orchestrator()
            if not k8s_orchestrator:
                return {
                    "success": False,
                    "error": "K8s orchestrator not available - PAP compliance required"
                }
            
            # Broadcast message for real-time updates
            await self.broadcast_message({
                "type": "k8s_context_switch",
                "data": {
                    "controller": self.name,
                    "context": context,
                    "message": f"Switching to context: {context}"
                }
            })
            
            # Delegate to orchestrator following PAP pattern
            return await k8s_orchestrator.switch_context_operation(context=context)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"K8s controller error: {str(e)}"
            }
    
    async def get_pods(self, namespace: str = "default") -> Dict[str, Any]:
        """Get pods in namespace via orchestrator"""
        try:
            k8s_orchestrator = self.get_k8s_orchestrator()
            if not k8s_orchestrator:
                return {
                    "success": False,
                    "error": "K8s orchestrator not available - PAP compliance required"
                }
            
            # Delegate to orchestrator following PAP pattern
            return await k8s_orchestrator.get_pods_operation(namespace=namespace)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"K8s controller error: {str(e)}"
            }
