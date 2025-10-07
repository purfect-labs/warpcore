#!/usr/bin/env python3
"""
WARPCORE Circuit Breaker Implementation
Prevents cascading failures and provides graceful degradation
"""

import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, Callable, Awaitable
import logging
from dataclasses import dataclass, field


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast, blocking requests
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    failure_threshold: int = 5              # Number of failures before opening
    recovery_timeout: int = 60              # Seconds to wait before testing recovery
    success_threshold: int = 3              # Successes needed to close circuit
    timeout: int = 30                       # Request timeout in seconds
    expected_exception_types: tuple = (Exception,)  # Exceptions to count as failures
    name: str = "circuit_breaker"           # Circuit breaker identifier
    
    # WARP watermarking for test scenarios
    enable_test_mode: bool = False
    test_failure_rate: float = 0.0


@dataclass
class CircuitBreakerMetrics:
    """Metrics collected by circuit breaker"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changes: list = field(default_factory=list)
    recovery_attempts: int = 0


class CircuitBreaker:
    """
    Circuit breaker implementation for fault tolerance
    
    Implements the circuit breaker pattern to prevent cascading failures
    and provide graceful degradation when services become unavailable.
    """
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self.logger = logging.getLogger(f"circuit_breaker.{config.name}")
        self._lock = asyncio.Lock()
        
        # State transition callbacks
        self._on_open_callbacks = []
        self._on_close_callbacks = []
        self._on_half_open_callbacks = []
        
        self.logger.info(f"Circuit breaker '{config.name}' initialized with threshold={config.failure_threshold}")
    
    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker protection
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: When circuit is open
            TimeoutError: When function times out
            Exception: Original function exceptions
        """
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if not self._should_attempt_reset():
                    self.metrics.total_requests += 1
                    self.logger.warning(f"Circuit breaker '{self.config.name}' is OPEN - failing fast")
                    raise CircuitBreakerOpenError(f"Circuit breaker '{self.config.name}' is open")
                else:
                    # Transition to half-open state
                    await self._transition_to_half_open()
        
        # Execute the function with timeout
        start_time = time.time()
        try:
            self.metrics.total_requests += 1
            
            # Apply timeout protection
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )
            
            # Record success
            await self._record_success(time.time() - start_time)
            return result
            
        except asyncio.TimeoutError as e:
            await self._record_failure(time.time() - start_time, e)
            self.logger.warning(f"Circuit breaker '{self.config.name}' - operation timed out after {self.config.timeout}s")
            raise TimeoutError(f"Operation timed out after {self.config.timeout} seconds")
            
        except Exception as e:
            if isinstance(e, self.config.expected_exception_types):
                await self._record_failure(time.time() - start_time, e)
            else:
                # Don't count unexpected exceptions as circuit breaker failures
                self.logger.warning(f"Circuit breaker '{self.config.name}' - unexpected exception: {type(e).__name__}")
            raise
    
    async def _record_success(self, duration: float):
        """Record successful operation"""
        self.metrics.successful_requests += 1
        self.metrics.consecutive_failures = 0
        self.metrics.consecutive_successes += 1
        self.metrics.last_success_time = time.time()
        
        self.logger.debug(f"Circuit breaker '{self.config.name}' - success recorded (duration: {duration:.2f}s)")
        
        # Check if we should close the circuit from half-open state
        if (self.state == CircuitState.HALF_OPEN and 
            self.metrics.consecutive_successes >= self.config.success_threshold):
            await self._transition_to_closed()
    
    async def _record_failure(self, duration: float, exception: Exception):
        """Record failed operation"""
        self.metrics.failed_requests += 1
        self.metrics.consecutive_successes = 0
        self.metrics.consecutive_failures += 1
        self.metrics.last_failure_time = time.time()
        
        self.logger.warning(
            f"Circuit breaker '{self.config.name}' - failure recorded "
            f"(duration: {duration:.2f}s, exception: {type(exception).__name__})"
        )
        
        # Check if we should open the circuit
        if (self.state in [CircuitState.CLOSED, CircuitState.HALF_OPEN] and
            self.metrics.consecutive_failures >= self.config.failure_threshold):
            await self._transition_to_open()
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset from open state"""
        if not self.metrics.last_failure_time:
            return True
        
        time_since_failure = time.time() - self.metrics.last_failure_time
        return time_since_failure >= self.config.recovery_timeout
    
    async def _transition_to_open(self):
        """Transition circuit breaker to open state"""
        if self.state != CircuitState.OPEN:
            old_state = self.state
            self.state = CircuitState.OPEN
            
            transition = {
                "from_state": old_state.value,
                "to_state": CircuitState.OPEN.value,
                "timestamp": datetime.now().isoformat(),
                "consecutive_failures": self.metrics.consecutive_failures,
                "reason": "failure_threshold_exceeded"
            }
            self.metrics.state_changes.append(transition)
            
            self.logger.error(
                f"Circuit breaker '{self.config.name}' OPENED - "
                f"{self.metrics.consecutive_failures} consecutive failures"
            )
            
            # Notify callbacks
            for callback in self._on_open_callbacks:
                try:
                    await callback(self)
                except Exception as e:
                    self.logger.error(f"Error in open callback: {e}")
    
    async def _transition_to_half_open(self):
        """Transition circuit breaker to half-open state"""
        if self.state != CircuitState.HALF_OPEN:
            old_state = self.state
            self.state = CircuitState.HALF_OPEN
            
            transition = {
                "from_state": old_state.value,
                "to_state": CircuitState.HALF_OPEN.value,
                "timestamp": datetime.now().isoformat(),
                "recovery_attempt": self.metrics.recovery_attempts + 1,
                "reason": "recovery_timeout_elapsed"
            }
            self.metrics.state_changes.append(transition)
            self.metrics.recovery_attempts += 1
            self.metrics.consecutive_successes = 0  # Reset success counter
            
            self.logger.info(
                f"Circuit breaker '{self.config.name}' HALF-OPEN - "
                f"testing recovery (attempt {self.metrics.recovery_attempts})"
            )
            
            # Notify callbacks
            for callback in self._on_half_open_callbacks:
                try:
                    await callback(self)
                except Exception as e:
                    self.logger.error(f"Error in half-open callback: {e}")
    
    async def _transition_to_closed(self):
        """Transition circuit breaker to closed state"""
        if self.state != CircuitState.CLOSED:
            old_state = self.state
            self.state = CircuitState.CLOSED
            
            transition = {
                "from_state": old_state.value,
                "to_state": CircuitState.CLOSED.value,
                "timestamp": datetime.now().isoformat(),
                "consecutive_successes": self.metrics.consecutive_successes,
                "reason": "success_threshold_met"
            }
            self.metrics.state_changes.append(transition)
            self.metrics.consecutive_failures = 0  # Reset failure counter
            
            self.logger.info(
                f"Circuit breaker '{self.config.name}' CLOSED - "
                f"service recovered after {self.metrics.consecutive_successes} successes"
            )
            
            # Notify callbacks
            for callback in self._on_close_callbacks:
                try:
                    await callback(self)
                except Exception as e:
                    self.logger.error(f"Error in close callback: {e}")
    
    def add_state_change_callback(self, state: CircuitState, callback: Callable[["CircuitBreaker"], Awaitable[None]]):
        """Add callback for state transitions"""
        if state == CircuitState.OPEN:
            self._on_open_callbacks.append(callback)
        elif state == CircuitState.CLOSED:
            self._on_close_callbacks.append(callback)
        elif state == CircuitState.HALF_OPEN:
            self._on_half_open_callbacks.append(callback)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        uptime_hours = (time.time() - (self.metrics.last_failure_time or time.time())) / 3600
        
        success_rate = 0.0
        if self.metrics.total_requests > 0:
            success_rate = self.metrics.successful_requests / self.metrics.total_requests
        
        return {
            "name": self.config.name,
            "state": self.state.value,
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "success_rate": round(success_rate * 100, 2),
                "consecutive_failures": self.metrics.consecutive_failures,
                "consecutive_successes": self.metrics.consecutive_successes,
                "recovery_attempts": self.metrics.recovery_attempts
            },
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout
            },
            "timestamps": {
                "last_failure": datetime.fromtimestamp(self.metrics.last_failure_time).isoformat() if self.metrics.last_failure_time else None,
                "last_success": datetime.fromtimestamp(self.metrics.last_success_time).isoformat() if self.metrics.last_success_time else None,
                "status_timestamp": datetime.now().isoformat()
            },
            "health": {
                "is_healthy": self.state == CircuitState.CLOSED,
                "uptime_hours": round(uptime_hours, 2),
                "can_accept_requests": self.state != CircuitState.OPEN
            }
        }
    
    def reset(self):
        """Manually reset circuit breaker to closed state"""
        self.state = CircuitState.CLOSED
        self.metrics.consecutive_failures = 0
        self.metrics.consecutive_successes = 0
        self.logger.info(f"Circuit breaker '{self.config.name}' manually reset to CLOSED")


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class CircuitBreakerRegistry:
    """
    Global registry for managing circuit breakers across the system
    """
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._default_configs: Dict[str, CircuitBreakerConfig] = {}
        self.logger = logging.getLogger("circuit_breaker_registry")
    
    def register_default_config(self, name: str, config: CircuitBreakerConfig):
        """Register default configuration for a circuit breaker"""
        self._default_configs[name] = config
        self.logger.info(f"Registered default config for circuit breaker: {name}")
    
    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker by name"""
        if name not in self._breakers:
            # Use provided config or default config or create basic config
            if config is None:
                config = self._default_configs.get(name, CircuitBreakerConfig(name=name))
            
            self._breakers[name] = CircuitBreaker(config)
            self.logger.info(f"Created circuit breaker: {name}")
        
        return self._breakers[name]
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers"""
        return {name: breaker.get_status() for name, breaker in self._breakers.items()}
    
    def reset_all(self):
        """Reset all circuit breakers"""
        for name, breaker in self._breakers.items():
            breaker.reset()
            self.logger.info(f"Reset circuit breaker: {name}")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary of all circuit breakers"""
        if not self._breakers:
            return {
                "overall_health": "no_circuit_breakers",
                "total_breakers": 0,
                "healthy_breakers": 0,
                "degraded_breakers": 0,
                "failed_breakers": 0
            }
        
        statuses = self.get_all_status()
        
        healthy = sum(1 for status in statuses.values() if status["health"]["is_healthy"])
        half_open = sum(1 for status in statuses.values() if status["state"] == "half_open")
        open_breakers = sum(1 for status in statuses.values() if status["state"] == "open")
        
        overall_health = "healthy"
        if open_breakers > len(self._breakers) * 0.5:  # More than 50% failed
            overall_health = "critical"
        elif open_breakers > 0 or half_open > 0:
            overall_health = "degraded"
        
        return {
            "overall_health": overall_health,
            "total_breakers": len(self._breakers),
            "healthy_breakers": healthy,
            "degraded_breakers": half_open,
            "failed_breakers": open_breakers,
            "timestamp": datetime.now().isoformat()
        }


# Global circuit breaker registry instance
_circuit_breaker_registry = CircuitBreakerRegistry()


def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """Get global circuit breaker registry"""
    return _circuit_breaker_registry


# Decorator for easy circuit breaker application
def circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """
    Decorator to apply circuit breaker to async functions
    
    Usage:
        @circuit_breaker("external_api")
        async def call_external_api():
            # Implementation
    """
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        breaker = get_circuit_breaker_registry().get_circuit_breaker(name, config)
        
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator