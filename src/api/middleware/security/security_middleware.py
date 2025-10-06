"""
WARPCORE Security Middleware
Access control, policy enforcement, dangerous operation blocking
"""

from ..base_middleware import BaseMiddleware
from typing import Dict, Any
import os

class SecurityMiddleware(BaseMiddleware):
    """Security policy enforcement middleware"""
    
    def __init__(self):
        super().__init__("security_middleware")
        self.blocked_operations = self._load_blocked_operations()
        self.production_restrictions = True
    
    async def process(self, operation: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply security policies to operation"""
        
        # Check if operation is globally blocked
        if operation in self.blocked_operations:
            await self.log(operation, context, {"action": "blocked", "reason": "globally_blocked"})
            return {
                "allowed": False,
                "error": f"Operation {operation} is globally blocked by security policy"
            }
        
        # Check production context restrictions
        if self.production_restrictions:
            prod_check = await self._check_production_restrictions(operation, context)
            if not prod_check.get("allowed", True):
                await self.log(operation, context, {"action": "blocked", "reason": "production_restriction"})
                return prod_check
        
        # Check user permissions (placeholder for future implementation)
        user_check = await self._check_user_permissions(operation, context)
        if not user_check.get("allowed", True):
            await self.log(operation, context, {"action": "blocked", "reason": "insufficient_permissions"})
            return user_check
        
        # Log allowed operation
        await self.log(operation, context, {"action": "allowed"})
        
        return {"allowed": True, "message": "Security validation passed"}
    
    async def _check_production_restrictions(self, operation: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check production environment restrictions"""
        project = context.get("project", "")
        provider = context.get("provider", "")
        
        # Block destructive operations in production contexts
        destructive_operations = [
            "delete_instance",
            "delete_project", 
            "delete_bucket",
            "drop_database",
            "terminate_instance"
        ]
        
        if "prod" in project.lower() and operation in destructive_operations:
            return {
                "allowed": False,
                "error": f"Destructive operation '{operation}' blocked in production project '{project}'"
            }
        
        return {"allowed": True}
    
    async def _check_user_permissions(self, operation: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check user permissions - placeholder for RBAC"""
        # For now, all operations allowed
        # In future: implement role-based access control
        
        current_user = os.getenv("USER", "unknown")
        
        # Example: block certain operations for specific users
        if current_user == "guest" and operation in ["delete_instance", "create_project"]:
            return {
                "allowed": False,
                "error": f"User '{current_user}' does not have permission for operation '{operation}'"
            }
        
        return {"allowed": True}
    
    def _load_blocked_operations(self) -> set:
        """Load globally blocked operations"""
        # For now, hardcoded list - in future, load from config
        return {
            "format_disk",
            "shutdown_system",
            "delete_all_data",
            "reset_credentials"
        }