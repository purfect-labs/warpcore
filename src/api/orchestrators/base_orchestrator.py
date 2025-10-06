"""
WARPCORE Base Orchestrator - PAP Layer 3
Workflow composition across providers and middleware
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseOrchestrator(ABC):
    """Base class for PAP Layer 3 orchestrators"""
    
    def __init__(self, name: str):
        self.name = name
        self.provider_registry = None
        self.middleware_registry = None
        self.executor_registry = None
    
    def set_provider_registry(self, provider_registry):
        """Wire up provider registry"""
        self.provider_registry = provider_registry
    
    def set_middleware_registry(self, middleware_registry):
        """Wire up middleware registry"""
        self.middleware_registry = middleware_registry
    
    def set_executor_registry(self, executor_registry):
        """Wire up executor registry"""
        self.executor_registry = executor_registry
    
    def get_provider(self, name: str):
        """Get provider by name"""
        if self.provider_registry:
            return self.provider_registry.get_provider(name)
        return None
    
    def get_middleware(self, name: str):
        """Get middleware by name"""
        if self.middleware_registry:
            return self.middleware_registry.get_middleware(name)
        return None
    
    def get_executor(self, name: str):
        """Get executor by name"""
        if self.executor_registry:
            return self.executor_registry.get_executor(name)
        return None
    
    @abstractmethod
    async def orchestrate(self, **kwargs) -> Dict[str, Any]:
        """Orchestrate workflow across layers"""
        pass
    
    async def apply_middleware(self, operation: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply middleware policies to operation"""
        if not self.middleware_registry:
            return {"success": True, "message": "No middleware registry available"}
        
        # Use registry's middleware chain
        return await self.middleware_registry.apply_middleware_chain(operation, context)
    
    async def execute_with_safety(self, operation: str, command: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute operation through safety gate"""
        if not self.executor_registry:
            return {"success": False, "error": "No executor registry available - safety gates required"}
        
        # Use registry's safety gate execution
        return await self.executor_registry.execute_with_safety_gates(operation, command, context)
    
    async def compose_workflow(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compose multi-step workflow"""
        results = []
        
        for step in steps:
            step_name = step.get("name", "unknown")
            step_provider = step.get("provider")
            step_operation = step.get("operation")
            step_params = step.get("params", {})
            
            try:
                # Apply middleware
                middleware_result = await self.apply_middleware(step_operation, {
                    "provider": step_provider,
                    "operation": step_operation,
                    **step_params
                })
                
                if not middleware_result.get("success"):
                    return middleware_result
                
                # Execute step via provider
                provider = self.get_provider(step_provider)
                if not provider:
                    return {"success": False, "error": f"Provider {step_provider} not available"}
                
                operation_method = getattr(provider, step_operation, None)
                if not operation_method:
                    return {"success": False, "error": f"Operation {step_operation} not available on {step_provider}"}
                
                result = await operation_method(**step_params)
                results.append({
                    "step": step_name,
                    "success": result.get("success", True),
                    "result": result
                })
                
                # If step failed, stop workflow
                if not result.get("success", True):
                    return {
                        "success": False,
                        "error": f"Workflow failed at step: {step_name}",
                        "results": results
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Workflow error at step {step_name}: {str(e)}",
                    "results": results
                }
        
        return {
            "success": True,
            "message": "Workflow completed successfully",
            "results": results
        }
    
    async def compose_workflow_with_safety(self, steps: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Compose workflow with safety gate integration for command execution"""
        results = []
        
        for step in steps:
            step_name = step.get("name", "unknown")
            step_provider = step.get("provider")
            step_operation = step.get("operation")
            step_params = step.get("params", {})
            requires_safety_gate = step.get("requires_safety_gate", False)
            command = step.get("command", [])
            
            try:
                # Apply middleware for each step
                step_context = {
                    **context,
                    "step_name": step_name,
                    "provider": step_provider,
                    "operation": step_operation,
                    **step_params
                }
                
                middleware_result = await self.apply_middleware(step_operation, step_context)
                if not middleware_result.get("success"):
                    return middleware_result
                
                # Execute step with or without safety gates
                if requires_safety_gate and command:
                    # Route through executor safety gates
                    result = await self.execute_with_safety(step_operation, command, step_context)
                else:
                    # Direct provider execution (for non-command operations)
                    provider = self.get_provider(step_provider)
                    if not provider:
                        return {"success": False, "error": f"Provider {step_provider} not available"}
                    
                    operation_method = getattr(provider, step_operation, None)
                    if not operation_method:
                        return {"success": False, "error": f"Operation {step_operation} not available on {step_provider}"}
                    
                    result = await operation_method(**step_params)
                
                results.append({
                    "step": step_name,
                    "success": result.get("success", True),
                    "result": result,
                    "safety_gate_applied": requires_safety_gate
                })
                
                # If step failed, stop workflow
                if not result.get("success", True):
                    return {
                        "success": False,
                        "error": f"Workflow failed at step: {step_name}",
                        "results": results,
                        "safety_gates_enforced": True
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Workflow error at step {step_name}: {str(e)}",
                    "results": results,
                    "safety_gates_enforced": True
                }
        
        return {
            "success": True,
            "message": "Workflow completed successfully with PAP enforcement",
            "results": results,
            "safety_gates_enforced": True
        }
