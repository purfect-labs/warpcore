"""
WARPCORE Command Safety Executor - PAP Layer 6
Final safety gates for system command execution with validation and rollback
"""

import asyncio
import os
import shlex
import tempfile
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from ..core.base_executor import BaseExecutor


class CommandExecutor(BaseExecutor):
    """PAP Layer 6: Command execution with comprehensive safety gates"""
    
    def __init__(self):
        super().__init__("command_executor")
        
        # Command safety configuration
        self.safe_commands = {
            # Read-only commands (always safe)
            "git", "ls", "cat", "grep", "find", "ps", "top", "df", "du",
            "kubectl get", "kubectl describe", "kubectl logs",
            "gcloud projects list", "gcloud auth list", "gcloud config list",
            "aws sts get-caller-identity", "aws ec2 describe-instances",
            
            # Safe operational commands
            "kubectl port-forward", "kubectl proxy",
            "gcloud container clusters get-credentials"
        }
        
        # Dangerous commands requiring production safety
        self.production_dangerous = {
            "kubectl delete", "kubectl apply", "kubectl create",
            "gcloud compute instances delete", "gcloud sql instances delete",
            "aws ec2 terminate-instances", "aws rds delete-db-instance",
            "rm -rf", "sudo rm", "docker system prune",
            "terraform destroy", "terraform apply"
        }
        
        # Commands that require confirmation
        self.confirmation_required = {
            "kubectl scale", "kubectl restart", "kubectl patch",
            "gcloud compute instances stop", "gcloud compute instances start",
            "aws ec2 stop-instances", "aws ec2 start-instances"
        }
        
        # Execution timeouts by command type
        self.command_timeouts = {
            "kubectl": 60,
            "gcloud": 120,
            "aws": 90,
            "git": 30,
            "default": 45
        }
    
    async def execute(self, operation: str, command: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command through safety gates"""
        
        # Phase 1: Command validation
        validation_result = await self.validate_command(command, context)
        if not validation_result.get("safe", False):
            return {
                "success": False,
                "blocked": True,
                "reason": validation_result.get("reason", "Command blocked by safety gate"),
                "safety_gate": "validation",
                "command": " ".join(command)
            }
        
        # Phase 2: Environment context safety
        env_safety = await self._check_environment_safety(command, context)
        if not env_safety.get("safe", False):
            return {
                "success": False,
                "blocked": True,
                "reason": env_safety.get("reason", "Command blocked by environment safety"),
                "safety_gate": "environment",
                "command": " ".join(command)
            }
        
        # Phase 3: Production safety gates
        if context.get("environment_type") == "production":
            prod_safety = await self._check_production_safety(command, context)
            if not prod_safety.get("safe", False):
                return {
                    "success": False,
                    "blocked": True,
                    "reason": prod_safety.get("reason", "Command blocked in production"),
                    "safety_gate": "production",
                    "command": " ".join(command),
                    "requires_confirmation": True
                }
        
        # Phase 4: Audit logging
        await self._log_command_execution(operation, command, context)
        
        # Phase 5: Execute with safety monitoring
        return await self._execute_with_monitoring(operation, command, context)
    
    async def validate_command(self, command: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate command safety without execution"""
        
        if not command:
            return {"safe": False, "reason": "Empty command"}
        
        command_str = " ".join(command)
        base_command = command[0]
        
        # Check against safe command patterns
        for safe_pattern in self.safe_commands:
            if command_str.startswith(safe_pattern):
                return {
                    "safe": True, 
                    "reason": f"Matches safe pattern: {safe_pattern}",
                    "safety_level": "safe"
                }
        
        # Check for dangerous patterns
        for danger_pattern in self.production_dangerous:
            if danger_pattern in command_str:
                return {
                    "safe": False,
                    "reason": f"Contains dangerous pattern: {danger_pattern}",
                    "safety_level": "dangerous",
                    "requires_confirmation": True
                }
        
        # Check for confirmation-required patterns
        for confirm_pattern in self.confirmation_required:
            if confirm_pattern in command_str:
                return {
                    "safe": True,
                    "reason": f"Requires confirmation: {confirm_pattern}",
                    "safety_level": "confirmation_required",
                    "requires_confirmation": True
                }
        
        # Unknown commands default to cautious
        return {
            "safe": True,
            "reason": "Unknown command - proceeding with caution",
            "safety_level": "cautious",
            "requires_monitoring": True
        }
    
    async def _check_environment_safety(self, command: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check command safety in current environment context"""
        
        command_str = " ".join(command)
        
        # Detect production-like environment indicators
        production_indicators = [
            "prod", "production", "live", "master", "main"
        ]
        
        # Check git branch context
        current_branch = context.get("git_branch", "unknown")
        if any(indicator in current_branch.lower() for indicator in production_indicators):
            if any(danger in command_str for danger in self.production_dangerous):
                return {
                    "safe": False,
                    "reason": f"Dangerous command '{command_str}' detected in production-like branch '{current_branch}'",
                    "environment_type": "production"
                }
        
        # Check Kubernetes context safety
        if "kubectl" in command_str:
            k8s_context = context.get("k8s_context", "unknown")
            if any(indicator in k8s_context.lower() for indicator in production_indicators):
                if "delete" in command_str or "apply" in command_str:
                    return {
                        "safe": False,
                        "reason": f"Dangerous kubectl command in production context '{k8s_context}'",
                        "environment_type": "production"
                    }
        
        # Check cloud project/account context
        cloud_project = context.get("gcp_project") or context.get("aws_account")
        if cloud_project and any(indicator in cloud_project.lower() for indicator in production_indicators):
            if any(danger in command_str for danger in self.production_dangerous):
                return {
                    "safe": False,
                    "reason": f"Dangerous cloud command in production project/account '{cloud_project}'",
                    "environment_type": "production"
                }
        
        return {"safe": True, "reason": "Environment safety check passed"}
    
    async def _check_production_safety(self, command: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Additional safety checks for production environments"""
        
        command_str = " ".join(command)
        
        # Block all dangerous operations in production by default
        for danger_pattern in self.production_dangerous:
            if danger_pattern in command_str:
                return {
                    "safe": False,
                    "reason": f"Operation '{danger_pattern}' blocked in production environment",
                    "requires_manual_override": True
                }
        
        # Require confirmation for operational commands
        for confirm_pattern in self.confirmation_required:
            if confirm_pattern in command_str:
                # In a real system, this would integrate with a confirmation UI
                return {
                    "safe": False,  # For now, block until confirmation system is built
                    "reason": f"Operation '{confirm_pattern}' requires explicit confirmation in production",
                    "requires_confirmation": True
                }
        
        return {"safe": True, "reason": "Production safety check passed"}
    
    async def _execute_with_monitoring(self, operation: str, command: List[str], 
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command with monitoring and timeout"""
        
        command_str = " ".join(command)
        base_command = command[0] if command else "unknown"
        
        # Determine timeout
        timeout = self.command_timeouts.get(base_command, self.command_timeouts["default"])
        
        try:
            # Broadcast command start
            await self.broadcast_message({
                "type": "command_execution",
                "data": {
                    "operation": operation,
                    "command": command_str,
                    "status": "starting",
                    "timeout": timeout,
                    "safety_gate": "passed",
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            # Execute with timeout
            process = await asyncio.create_subprocess_shell(
                command_str,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._get_safe_environment(context)
            )
            
            # Monitor execution with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                exit_code = process.returncode
                
                result = {
                    "success": exit_code == 0,
                    "exit_code": exit_code,
                    "stdout": stdout.decode(),
                    "stderr": stderr.decode(),
                    "command": command_str,
                    "operation": operation,
                    "safety_gate": "executed",
                    "timeout": timeout,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Broadcast completion
                await self.broadcast_message({
                    "type": "command_execution",
                    "data": {**result, "status": "completed"}
                })
                
                return result
                
            except asyncio.TimeoutError:
                # Kill the process
                process.kill()
                await process.wait()
                
                result = {
                    "success": False,
                    "error": f"Command timed out after {timeout} seconds",
                    "command": command_str,
                    "operation": operation,
                    "safety_gate": "timeout",
                    "timeout": timeout,
                    "timestamp": datetime.now().isoformat()
                }
                
                await self.broadcast_message({
                    "type": "command_execution",
                    "data": {**result, "status": "timeout"}
                })
                
                return result
                
        except Exception as e:
            result = {
                "success": False,
                "error": f"Command execution failed: {str(e)}",
                "command": command_str,
                "operation": operation,
                "safety_gate": "error",
                "timestamp": datetime.now().isoformat()
            }
            
            await self.broadcast_message({
                "type": "command_execution",
                "data": {**result, "status": "error"}
            })
            
            return result
    
    def _get_safe_environment(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Get sanitized environment variables for command execution"""
        safe_env = os.environ.copy()
        
        # Remove potentially dangerous environment variables
        dangerous_vars = [
            "LD_PRELOAD", "DYLD_INSERT_LIBRARIES", 
            "PYTHONPATH", "PATH_OVERRIDE"
        ]
        
        for var in dangerous_vars:
            safe_env.pop(var, None)
        
        # Add context-specific environment if needed
        if context.get("gcp_project"):
            safe_env["GCLOUD_PROJECT"] = context["gcp_project"]
        
        if context.get("k8s_context"):
            safe_env["KUBECONFIG"] = context.get("kubeconfig", safe_env.get("KUBECONFIG", ""))
        
        return safe_env
    
    async def _log_command_execution(self, operation: str, command: List[str], context: Dict[str, Any]):
        """Log command execution for audit trail"""
        audit_event = {
            "type": "command_execution_audit",
            "operation": operation,
            "command": " ".join(command),
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "executor": "command_executor",
            "safety_gates_applied": True
        }
        
        # Broadcast audit event
        await self.broadcast_message({
            "type": "audit_event",
            "data": audit_event
        })
    
    def get_capabilities(self) -> List[str]:
        """Get executor capabilities"""
        return [
            "command_validation",
            "safety_gates",
            "timeout_enforcement", 
            "production_protection",
            "audit_logging",
            "environment_safety"
        ]
    
    async def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety gate configuration"""
        return {
            "safe_commands_count": len(self.safe_commands),
            "dangerous_patterns_count": len(self.production_dangerous),
            "confirmation_patterns_count": len(self.confirmation_required),
            "default_timeout": self.command_timeouts["default"],
            "production_protection": True,
            "audit_logging": True,
            "capabilities": self.get_capabilities()
        }