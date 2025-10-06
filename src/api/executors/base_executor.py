"""
WARPCORE Base Executor - PAP Layer 6
Final safety gates and command execution isolation
"""

import asyncio
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseExecutor(ABC):
    """Base class for PAP Layer 6 executors - final safety layer"""
    
    def __init__(self, name: str):
        self.name = name
        self.audit_logger = None
    
    def set_audit_logger(self, audit_logger):
        """Wire up audit logger"""
        self.audit_logger = audit_logger
    
    @abstractmethod
    async def execute(self, operation: str, command: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute operation through safety gates"""
        pass
    
    async def validate_command(self, command: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate command before execution"""
        # Check for dangerous operations
        dangerous_patterns = [
            "rm -rf",
            "delete",
            "destroy", 
            "drop",
            "format",
            "shutdown",
            "reboot"
        ]
        
        command_str = " ".join(command)
        for pattern in dangerous_patterns:
            if pattern in command_str.lower():
                return {
                    "valid": False,
                    "error": f"Potentially dangerous operation detected: {pattern}",
                    "requires_confirmation": True
                }
        
        return {"valid": True}
    
    async def execute_with_timeout(self, command: List[str], timeout: int = 30) -> Dict[str, Any]:
        """Execute command with timeout safety"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
                
                return {
                    "success": process.returncode == 0,
                    "exit_code": process.returncode,
                    "stdout": stdout.decode(),
                    "stderr": stderr.decode(),
                    "timed_out": False
                }
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "error": f"Command timed out after {timeout} seconds",
                    "timed_out": True
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "timed_out": False
            }
    
    async def audit_execution(self, operation: str, command: List[str], result: Dict[str, Any], context: Dict[str, Any]):
        """Audit command execution"""
        if self.audit_logger:
            await self.audit_logger.log_execution({
                "operation": operation,
                "command": command,
                "result": result,
                "context": context,
                "executor": self.name
            })
    
    async def check_rollback_capability(self, operation: str, command: List[str]) -> Dict[str, Any]:
        """Check if operation can be rolled back"""
        # Define operations that have rollback capability
        rollback_operations = {
            "gcloud config set": "gcloud config unset",
            "kubectl apply": "kubectl delete",
            "gcloud projects create": "gcloud projects delete"
        }
        
        command_str = " ".join(command)
        for pattern, rollback_cmd in rollback_operations.items():
            if pattern in command_str:
                return {
                    "can_rollback": True,
                    "rollback_command": rollback_cmd
                }
        
        return {"can_rollback": False}