"""
WARPCORE Base Middleware - PAP Layer 5
Policy enforcement, audit logging, security controls
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import asyncio
import json
from datetime import datetime

class BaseMiddleware(ABC):
    """Base class for PAP Layer 5 middleware"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
    
    @abstractmethod
    async def process(self, operation: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process operation through middleware"""
        pass
    
    async def validate(self, operation: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate operation against policies"""
        if not self.enabled:
            return {"allowed": True, "message": "Middleware disabled"}
        
        return await self.process(operation, context)
    
    async def log(self, operation: str, context: Dict[str, Any], result: Dict[str, Any] = None):
        """Log operation for audit trail"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "middleware": self.name,
            "operation": operation,
            "context": context,
            "result": result
        }
        
        # Override in subclasses for specific logging
        await self._write_audit_log(log_entry)
    
    async def _write_audit_log(self, log_entry: Dict[str, Any]):
        """Write audit log entry - override in subclasses"""
        # Default: write to temp file for development
        import tempfile
        import os
        
        log_file = os.path.join(tempfile.gettempdir(), "warpcore_audit.log")
        
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass  # Silently fail to not break operations