"""
WARPCORE K8s Orchestrator - PAP Layer 3
Kubernetes workflow orchestration following PAP compliance patterns
"""

from typing import Dict, Any, List, Optional
from .core.base_orchestrator import BaseOrchestrator


class K8sOrchestrator(BaseOrchestrator):
    """Orchestrator for Kubernetes operations following PAP patterns"""
    
    def __init__(self):
        super().__init__("k8s")
        self.k8s_provider = None
    
    def set_k8s_provider(self, provider):
        """Wire up K8s provider"""
        self.k8s_provider = provider
    
    async def orchestrate(self, **kwargs) -> Dict[str, Any]:
        """Main orchestration entry point for K8s operations"""
        operation = kwargs.get("operation")
        
        if operation == "get_pods":
            return await self.get_pods_operation(**kwargs)
        elif operation == "switch_context":
            return await self.switch_context_operation(**kwargs)
        elif operation == "get_clusters":
            return await self.get_clusters_operation(**kwargs)
        elif operation == "get_status":
            return await self.get_status_operation(**kwargs)
        else:
            return {
                "success": False,
                "error": f"Unknown K8s operation: {operation}"
            }
    
    async def get_pods_operation(self, namespace: str = "default", **kwargs) -> Dict[str, Any]:
        """Orchestrate pod retrieval with proper PAP flow"""
        try:
            # Apply middleware policies for K8s access
            middleware_context = {
                "operation": "k8s_get_pods",
                "namespace": namespace,
                "resource_type": "pods"
            }
            
            middleware_result = await self.apply_middleware("k8s_get_pods", middleware_context)
            if not middleware_result.get("success", True):
                return middleware_result
            
            # Get K8s provider through registry
            k8s_provider = self.get_provider("k8s") or self.k8s_provider
            if not k8s_provider:
                return {
                    "success": False,
                    "error": "K8s provider not available in orchestrator"
                }
            
            # Execute provider operation
            result = await k8s_provider.get_pods(namespace=namespace)
            
            return {
                "success": True,
                "orchestrated_by": "k8s_orchestrator", 
                "operation": "get_pods",
                "namespace": namespace,
                "pap_compliant": True,
                **result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"K8s orchestrator error in get_pods: {str(e)}"
            }
    
    async def switch_context_operation(self, context: str, **kwargs) -> Dict[str, Any]:
        """Orchestrate context switching with proper PAP flow"""
        try:
            # Apply middleware policies for context switching
            middleware_context = {
                "operation": "k8s_switch_context",
                "target_context": context,
                "resource_type": "context"
            }
            
            middleware_result = await self.apply_middleware("k8s_switch_context", middleware_context)
            if not middleware_result.get("success", True):
                return middleware_result
            
            # Get K8s provider through registry
            k8s_provider = self.get_provider("k8s") or self.k8s_provider
            if not k8s_provider:
                return {
                    "success": False,
                    "error": "K8s provider not available in orchestrator"
                }
            
            # Execute provider operation
            result = await k8s_provider.switch_context(context)
            
            return {
                "success": True,
                "orchestrated_by": "k8s_orchestrator",
                "operation": "switch_context", 
                "context": context,
                "pap_compliant": True,
                **result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"K8s orchestrator error in switch_context: {str(e)}"
            }
    
    async def get_clusters_operation(self, **kwargs) -> Dict[str, Any]:
        """Orchestrate cluster listing with proper PAP flow"""
        try:
            # Apply middleware policies for cluster access
            middleware_context = {
                "operation": "k8s_get_clusters",
                "resource_type": "clusters"
            }
            
            middleware_result = await self.apply_middleware("k8s_get_clusters", middleware_context)
            if not middleware_result.get("success", True):
                return middleware_result
            
            # Get K8s provider through registry
            k8s_provider = self.get_provider("k8s") or self.k8s_provider
            if not k8s_provider:
                return {
                    "success": False,
                    "error": "K8s provider not available in orchestrator"
                }
            
            # Execute provider operation
            result = await k8s_provider.get_clusters()
            
            return {
                "success": True,
                "orchestrated_by": "k8s_orchestrator",
                "operation": "get_clusters",
                "pap_compliant": True,
                **result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"K8s orchestrator error in get_clusters: {str(e)}"
            }
    
    async def get_status_operation(self, **kwargs) -> Dict[str, Any]:
        """Orchestrate status check with proper PAP flow"""
        try:
            # Apply middleware policies for status check
            middleware_context = {
                "operation": "k8s_get_status",
                "resource_type": "status"
            }
            
            middleware_result = await self.apply_middleware("k8s_get_status", middleware_context)
            if not middleware_result.get("success", True):
                return middleware_result
            
            # Get K8s provider through registry
            k8s_provider = self.get_provider("k8s") or self.k8s_provider
            if not k8s_provider:
                return {
                    "success": False,
                    "error": "K8s provider not available in orchestrator"
                }
            
            # Execute provider operation
            result = await k8s_provider.get_status()
            
            return {
                "success": True,
                "orchestrated_by": "k8s_orchestrator",
                "operation": "get_status",
                "pap_compliant": True,
                **result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"K8s orchestrator error in get_status: {str(e)}"
            }
    
    async def compose_k8s_workflow(self, workflow_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compose multi-step K8s workflows with PAP compliance"""
        return await self.compose_workflow_with_safety(
            workflow_steps, 
            {"orchestrator": "k8s", "pap_layer": 3}
        )