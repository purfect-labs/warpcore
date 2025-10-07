"""
Base Provider Class for APEX API Callers
"""

import asyncio
import json
import os
import subprocess
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Awaitable

# Import resilience components
try:
    from ...middleware.resilience.circuit_breaker import (
        CircuitBreaker, CircuitBreakerConfig, get_circuit_breaker_registry,
        CircuitBreakerOpenError
    )
    from ...middleware.resilience.retry_handler import (
        RetryHandler, RetryConfig, CommonRetryConfigs
    )
    from ...middleware.resilience.error_recovery import (
        get_error_recovery_system
    )
    RESILIENCE_AVAILABLE = True
except ImportError:
    # Fallback when resilience components are not available
    RESILIENCE_AVAILABLE = False
    CircuitBreakerOpenError = Exception


class BaseProvider(ABC):
    """Base class for all service providers"""
    
    def __init__(self, name: str):
        self.name = name
        self.config = {}
        self.connections = {}
        
        # Health and resilience tracking
        self._health_status = "healthy"
        self._last_health_check = None
        self._degraded_mode = False
        self._error_count = 0
        self._last_error = None
        self._performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0
        }
        
        # Initialize resilience components if available
        if RESILIENCE_AVAILABLE:
            self.circuit_breaker = get_circuit_breaker_registry().get_circuit_breaker(
                f"{name}_provider",
                CircuitBreakerConfig(
                    name=f"{name}_provider",
                    failure_threshold=5,
                    recovery_timeout=60,
                    timeout=30
                )
            )
            self.retry_handler = RetryHandler(CommonRetryConfigs.network_operations())
            self.error_recovery = get_error_recovery_system()
        else:
            self.circuit_breaker = None
            self.retry_handler = None
            self.error_recovery = None
    
    @abstractmethod
    async def authenticate(self, **kwargs) -> Dict[str, Any]:
        """Authenticate with the service"""
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get current authentication/connection status"""
        pass
    
    async def execute_command(self, command: str, env: Optional[Dict[str, str]] = None, stream_output: bool = True) -> Dict[str, Any]:
        """Execute a command and return structured result with real-time streaming"""
        try:
            # Set up environment
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)
            
            # Show command being executed
            if stream_output:
                await self.broadcast_message({
                    'type': 'command_output',
                    'data': {
                        'output': f'⚡ {command}',
                        'context': self.name
                    }
                })
            
            # Use async subprocess for real-time streaming
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=exec_env,
                cwd=os.getcwd()
            )
            
            stdout_data = []
            stderr_data = []
            
            # Stream stdout in real-time
            async def stream_stdout():
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    line_str = line.decode().rstrip()
                    stdout_data.append(line_str)
                    if stream_output and line_str:
                        await self.broadcast_message({
                            'type': 'command_output',
                            'data': {
                                'output': line_str,
                                'context': self.name
                            }
                        })
            
            # Stream stderr in real-time
            async def stream_stderr():
                while True:
                    line = await process.stderr.readline()
                    if not line:
                        break
                    line_str = line.decode().rstrip()
                    stderr_data.append(line_str)
                    if stream_output and line_str:
                        await self.broadcast_message({
                            'type': 'command_output',
                            'data': {
                                'output': line_str,
                                'context': self.name
                            }
                        })
            
            # Run both streams concurrently
            await asyncio.gather(stream_stdout(), stream_stderr())
            
            # Wait for process to complete
            return_code = await process.wait()
            
            return {
                'success': return_code == 0,
                'exit_code': return_code,
                'stdout': '\n'.join(stdout_data),
                'stderr': '\n'.join(stderr_data),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """Send message to all connected clients (to be implemented by main app)"""
        # This will be overridden by the main application
        pass
    
    def get_env_vars(self) -> Dict[str, str]:
        """Get provider-specific environment variables"""
        return {}
    
    async def execute_with_resilience(self, 
                                    operation_func: Callable[..., Awaitable[Any]],
                                    *args, 
                                    fallback_result: Any = None,
                                    **kwargs) -> Dict[str, Any]:
        """
        Execute an operation with full resilience features:
        - Circuit breaker protection
        - Retry with exponential backoff  
        - Error classification and recovery
        - Performance metrics tracking
        """
        start_time = time.time()
        operation_name = operation_func.__name__ if hasattr(operation_func, '__name__') else 'unknown_operation'
        
        try:
            self._performance_metrics['total_requests'] += 1
            
            # If resilience components are not available, execute directly
            if not RESILIENCE_AVAILABLE:
                result = await operation_func(*args, **kwargs)
                self._record_success(time.time() - start_time)
                return result
            
            # Execute with circuit breaker protection
            try:
                if self.circuit_breaker:
                    result = await self.circuit_breaker.call(operation_func, *args, **kwargs)
                else:
                    result = await operation_func(*args, **kwargs)
                
                self._record_success(time.time() - start_time)
                return result
                
            except CircuitBreakerOpenError as e:
                # Circuit breaker is open - handle graceful degradation
                await self._handle_circuit_breaker_open(operation_name, fallback_result)
                raise e
                
            except Exception as e:
                # Handle error with classification and recovery
                duration = time.time() - start_time
                self._record_failure(duration, e)
                
                if self.error_recovery:
                    recovery_context = {
                        'operation_name': operation_name,
                        'provider_name': self.name,
                        'fallback_result': fallback_result,
                        'args': args,
                        'kwargs': kwargs
                    }
                    
                    recovery_result = await self.error_recovery.handle_error(e, recovery_context)
                    
                    if recovery_result.success and 'fallback_result' in recovery_result.context:
                        return recovery_result.context['fallback_result']
                    elif recovery_result.should_retry and self.retry_handler:
                        # Let retry handler take over
                        return await self.retry_handler.execute_with_retry(
                            operation_func, *args, **kwargs
                        )
                
                # If all recovery attempts failed, raise the original exception
                raise e
                
        except Exception as e:
            self._record_failure(time.time() - start_time, e)
            raise e
    
    async def _handle_circuit_breaker_open(self, operation_name: str, fallback_result: Any):
        """Handle circuit breaker open state with graceful degradation"""
        self._degraded_mode = True
        
        await self.broadcast_message({
            'type': 'provider_degraded',
            'data': {
                'provider': self.name,
                'operation': operation_name,
                'reason': 'circuit_breaker_open',
                'degraded_mode': True,
                'fallback_available': fallback_result is not None
            }
        })
        
        if fallback_result is not None:
            return fallback_result
    
    def _record_success(self, duration: float):
        """Record successful operation metrics"""
        self._performance_metrics['successful_requests'] += 1
        self._update_avg_response_time(duration)
        self._error_count = max(0, self._error_count - 1)  # Reduce error count on success
        
        if self._degraded_mode:
            self._degraded_mode = False  # Exit degraded mode on success
    
    def _record_failure(self, duration: float, exception: Exception):
        """Record failed operation metrics"""
        self._performance_metrics['failed_requests'] += 1
        self._update_avg_response_time(duration)
        self._error_count += 1
        self._last_error = {
            'exception_type': type(exception).__name__,
            'message': str(exception),
            'timestamp': datetime.now().isoformat()
        }
        
        # Update health status based on error patterns
        if self._error_count > 10:
            self._health_status = "unhealthy"
        elif self._error_count > 5:
            self._health_status = "degraded"
    
    def _update_avg_response_time(self, duration: float):
        """Update average response time using exponential moving average"""
        alpha = 0.1  # Smoothing factor
        current_avg = self._performance_metrics['avg_response_time']
        self._performance_metrics['avg_response_time'] = (alpha * duration) + ((1 - alpha) * current_avg)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of the provider"""
        self._last_health_check = time.time()
        
        # Calculate success rate
        total_requests = self._performance_metrics['total_requests']
        success_rate = 0.0
        if total_requests > 0:
            success_rate = self._performance_metrics['successful_requests'] / total_requests
        
        health_data = {
            'provider_name': self.name,
            'health_status': self._health_status,
            'degraded_mode': self._degraded_mode,
            'error_count': self._error_count,
            'last_error': self._last_error,
            'performance_metrics': {
                **self._performance_metrics,
                'success_rate': round(success_rate * 100, 2),
                'avg_response_time': round(self._performance_metrics['avg_response_time'], 3)
            },
            'resilience_status': {
                'circuit_breaker_available': self.circuit_breaker is not None,
                'retry_handler_available': self.retry_handler is not None,
                'error_recovery_available': self.error_recovery is not None
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Add circuit breaker status if available
        if self.circuit_breaker:
            cb_status = self.circuit_breaker.get_status()
            health_data['circuit_breaker'] = {
                'state': cb_status['state'],
                'is_healthy': cb_status['health']['is_healthy'],
                'success_rate': cb_status['metrics']['success_rate'],
                'total_requests': cb_status['metrics']['total_requests']
            }
        
        # Add retry handler status if available
        if self.retry_handler:
            retry_status = self.retry_handler.get_status()
            health_data['retry_handler'] = {
                'success_rate': retry_status['metrics']['success_rate'],
                'total_operations': retry_status['metrics']['successful_operations'] + retry_status['metrics']['failed_operations'],
                'is_healthy': retry_status['health']['is_healthy']
            }
        
        return health_data
    
    async def reset_health_metrics(self):
        """Reset all health and performance metrics"""
        self._performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0
        }
        self._error_count = 0
        self._last_error = None
        self._health_status = "healthy"
        self._degraded_mode = False
        
        # Reset resilience component metrics if available
        if self.circuit_breaker:
            self.circuit_breaker.reset()
        if self.retry_handler:
            self.retry_handler.reset_metrics()
