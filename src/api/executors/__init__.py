"""
WARPCORE Executor Registry - PAP Layer 6  
Command execution safety gates and validation
"""

from typing import Dict, Any, Optional, List
from .core.base_executor import BaseExecutor
from .command.command_executor import CommandExecutor


class ExecutorRegistry:
    """Registry for PAP Layer 6 executor components"""
    
    def __init__(self):
        self._executors = {}
        self._websocket_manager = None
        self._initialize_core_executors()
    
    def _initialize_core_executors(self):
        """Initialize core executor components"""
        # Command executor - main safety gate for system commands
        command_executor = CommandExecutor()
        self.register_executor("command_executor", command_executor)
        
        # Cloud-specific executors can be registered here
        # GCP executor, AWS executor, K8s executor, etc.
    
    def register_executor(self, name: str, executor: BaseExecutor):
        """Register an executor component"""
        if self._websocket_manager:
            executor.set_websocket_manager(self._websocket_manager)
        self._executors[name] = executor
        return executor
    
    def get_executor(self, name: str) -> Optional[BaseExecutor]:
        """Get executor by name"""
        return self._executors.get(name)
    
    def get_command_executor(self) -> Optional[CommandExecutor]:
        """Get command executor specifically"""
        return self.get_executor("command_executor")
    
    def set_websocket_manager(self, websocket_manager):
        """Wire up WebSocket manager for all executors"""
        self._websocket_manager = websocket_manager
        
        # Update existing executors
        for executor in self._executors.values():
            executor.set_websocket_manager(websocket_manager)
    
    def get_all_executors(self) -> Dict[str, BaseExecutor]:
        """Get all registered executors"""
        return self._executors.copy()
    
    async def execute_with_safety_gates(self, operation: str, command: List[str], 
                                       context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command through safety gate validation"""
        
        # Get appropriate executor
        executor = self.get_command_executor()
        if not executor:
            return {
                "success": False,
                "error": "No command executor available",
                "safety_gate": False
            }
        
        # Execute through safety gate
        return await executor.execute(operation, command, context)
    
    async def validate_command_safety(self, command: List[str], 
                                    context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate command safety without execution"""
        executor = self.get_command_executor()
        if not executor:
            return {"safe": False, "reason": "No executor available"}
        
        return await executor.validate_command(command, context)
    
    def get_executor_capabilities(self) -> Dict[str, List[str]]:
        """Get capabilities of all registered executors"""
        capabilities = {}
        
        for name, executor in self._executors.items():
            if hasattr(executor, 'get_capabilities'):
                capabilities[name] = executor.get_capabilities()
            else:
                capabilities[name] = ["execute"]  # Default capability
        
        return capabilities


# Global registry instance
_executor_registry = None

def get_executor_registry() -> ExecutorRegistry:
    """Get global executor registry instance"""
    global _executor_registry
    if _executor_registry is None:
        _executor_registry = ExecutorRegistry()
    return _executor_registry