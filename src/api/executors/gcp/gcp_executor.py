"""
WARPCORE GCP Executor - PAP Layer 6
Safety gates for GCP command execution
"""

from ..core.base_executor import BaseExecutor
from typing import Dict, Any, List

class GCPExecutor(BaseExecutor):
    """GCP-specific executor with safety gates"""
    
    def __init__(self):
        super().__init__("gcp_executor")
    
    async def execute(self, operation: str, command: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute GCP operation through safety gates"""
        
        # Pre-execution validation
        validation_result = await self.validate_command(command, context)
        if not validation_result.get("valid", True):
            return {
                "success": False,
                "error": validation_result.get("error"),
                "requires_confirmation": validation_result.get("requires_confirmation", False)
            }
        
        # GCP-specific validations
        gcp_validation = await self._validate_gcp_command(command, context)
        if not gcp_validation.get("valid", True):
            return {
                "success": False,
                "error": gcp_validation.get("error")
            }
        
        # Check rollback capability
        rollback_info = await self.check_rollback_capability(operation, command)
        
        # Execute with appropriate timeout based on operation
        timeout = self._get_operation_timeout(operation)
        result = await self.execute_with_timeout(command, timeout)
        
        # Audit execution
        await self.audit_execution(operation, command, result, context)
        
        # Add rollback info if available
        if rollback_info.get("can_rollback"):
            result["rollback_available"] = True
            result["rollback_command"] = rollback_info.get("rollback_command")
        
        return result
    
    async def _validate_gcp_command(self, command: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """GCP-specific command validation"""
        if not command or command[0] != "gcloud":
            return {"valid": False, "error": "Only gcloud commands allowed"}
        
        # Check for production context dangers
        if len(command) > 2:
            # Dangerous production operations
            dangerous_in_prod = [
                "projects delete",
                "compute instances delete", 
                "sql instances delete",
                "storage buckets delete"
            ]
            
            command_str = " ".join(command[1:])  # Skip 'gcloud'
            project_context = context.get("project", "")
            
            # If project contains 'prod' and doing dangerous operations
            if "prod" in project_context.lower():
                for danger in dangerous_in_prod:
                    if danger in command_str:
                        return {
                            "valid": False,
                            "error": f"Dangerous production operation blocked: {danger} on {project_context}"
                        }
        
        return {"valid": True}
    
    def _get_operation_timeout(self, operation: str) -> int:
        """Get appropriate timeout for operation"""
        operation_timeouts = {
            "authenticate": 60,  # Auth can take time
            "list_projects": 30,
            "list_instances": 45,
            "create_instance": 300,  # 5 minutes
            "delete_instance": 180,  # 3 minutes
            "default": 30
        }
        
        return operation_timeouts.get(operation, operation_timeouts["default"])