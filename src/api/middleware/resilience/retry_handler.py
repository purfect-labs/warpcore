#!/usr/bin/env python3
"""
WARPCORE Retry Handler Implementation
Provides configurable retry mechanisms with exponential backoff and jitter
"""

import asyncio
import random
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable, Awaitable, Type, Tuple
from enum import Enum
from datetime import datetime, timedelta


class RetryStrategy(Enum):
    """Retry strategies"""
    FIXED_INTERVAL = "fixed"
    LINEAR_BACKOFF = "linear"
    EXPONENTIAL_BACKOFF = "exponential"
    EXPONENTIAL_WITH_JITTER = "exponential_jitter"


class RetryCondition(Enum):
    """Conditions for retry decisions"""
    ALWAYS = "always"
    ON_EXCEPTION = "on_exception"
    ON_TIMEOUT = "on_timeout"
    ON_HTTP_ERROR = "on_http_error"
    CUSTOM = "custom"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay: float = 1.0                    # Base delay in seconds
    max_delay: float = 60.0                    # Maximum delay in seconds
    backoff_multiplier: float = 2.0            # Multiplier for exponential backoff
    jitter: bool = True                        # Add randomness to prevent thundering herd
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_WITH_JITTER
    
    # Exception handling
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    non_retryable_exceptions: Tuple[Type[Exception], ...] = ()
    
    # Custom retry condition
    retry_condition_func: Optional[Callable[[Exception], bool]] = None
    
    # Timeout settings
    operation_timeout: Optional[float] = None  # Overall operation timeout
    attempt_timeout: Optional[float] = None    # Per-attempt timeout
    
    # WARP watermarking
    name: str = "retry_handler"
    enable_logging: bool = True
    enable_metrics: bool = True


@dataclass
class RetryMetrics:
    """Metrics collected during retry operations"""
    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    total_delay_time: float = 0.0
    last_attempt_time: Optional[float] = None
    last_success_time: Optional[float] = None
    exception_counts: Dict[str, int] = field(default_factory=dict)
    attempt_durations: list = field(default_factory=list)


class RetryHandler:
    """
    Handles retry logic with configurable strategies and comprehensive error handling
    """
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.metrics = RetryMetrics()
        self.logger = logging.getLogger(f"retry_handler.{config.name}")
        
        if self.config.enable_logging:
            self.logger.info(
                f"Retry handler '{config.name}' initialized - "
                f"max_attempts={config.max_attempts}, strategy={config.strategy.value}"
            )
    
    async def execute_with_retry(self, 
                                func: Callable[..., Awaitable[Any]], 
                                *args, 
                                **kwargs) -> Any:
        """
        Execute function with retry logic
        
        Args:
            func: Async function to execute with retry
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            RetryExhaustedException: When all retry attempts are exhausted
            Exception: Original exception if non-retryable
        """
        operation_start = time.time()
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            attempt_start = time.time()
            
            try:
                if self.config.enable_logging and attempt > 1:
                    self.logger.info(
                        f"Retry attempt {attempt}/{self.config.max_attempts} for '{self.config.name}'"
                    )
                
                # Apply per-attempt timeout if configured
                if self.config.attempt_timeout:
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=self.config.attempt_timeout
                    )
                else:
                    result = await func(*args, **kwargs)
                
                # Success - record metrics and return
                attempt_duration = time.time() - attempt_start
                await self._record_success(attempt, attempt_duration)
                
                if self.config.enable_logging:
                    self.logger.info(
                        f"Retry handler '{self.config.name}' succeeded on attempt {attempt} "
                        f"(duration: {attempt_duration:.2f}s)"
                    )
                
                return result
                
            except Exception as e:
                attempt_duration = time.time() - attempt_start
                last_exception = e
                
                # Record metrics
                await self._record_failure(attempt, attempt_duration, e)
                
                # Check if we should retry this exception
                should_retry = self._should_retry(e, attempt)
                
                if not should_retry:
                    if self.config.enable_logging:
                        self.logger.warning(
                            f"Retry handler '{self.config.name}' - "
                            f"non-retryable exception: {type(e).__name__}"
                        )
                    raise e
                
                # Check if we've exhausted attempts
                if attempt >= self.config.max_attempts:
                    if self.config.enable_logging:
                        self.logger.error(
                            f"Retry handler '{self.config.name}' exhausted all {self.config.max_attempts} attempts"
                        )
                    break
                
                # Check overall operation timeout
                if self.config.operation_timeout:
                    elapsed_time = time.time() - operation_start
                    if elapsed_time >= self.config.operation_timeout:
                        if self.config.enable_logging:
                            self.logger.error(
                                f"Retry handler '{self.config.name}' - "
                                f"operation timeout {self.config.operation_timeout}s exceeded"
                            )
                        raise RetryTimeoutException(
                            f"Operation timeout {self.config.operation_timeout}s exceeded after {attempt} attempts"
                        )
                
                # Calculate delay for next attempt
                delay = self._calculate_delay(attempt)
                
                if self.config.enable_logging:
                    self.logger.warning(
                        f"Retry handler '{self.config.name}' attempt {attempt} failed "
                        f"({type(e).__name__}), retrying in {delay:.2f}s"
                    )
                
                # Wait before next attempt
                await asyncio.sleep(delay)
                self.metrics.total_delay_time += delay
        
        # All retries exhausted
        raise RetryExhaustedException(
            f"All {self.config.max_attempts} retry attempts failed for '{self.config.name}'",
            last_exception=last_exception,
            total_attempts=self.config.max_attempts
        )
    
    def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if an exception should trigger a retry"""
        
        # Check non-retryable exceptions first
        if isinstance(exception, self.config.non_retryable_exceptions):
            return False
        
        # Check custom retry condition if provided
        if self.config.retry_condition_func:
            return self.config.retry_condition_func(exception)
        
        # Check retryable exceptions
        return isinstance(exception, self.config.retryable_exceptions)
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for next retry attempt"""
        if self.config.strategy == RetryStrategy.FIXED_INTERVAL:
            delay = self.config.base_delay
            
        elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.config.base_delay * attempt
            
        elif self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.base_delay * (self.config.backoff_multiplier ** (attempt - 1))
            
        elif self.config.strategy == RetryStrategy.EXPONENTIAL_WITH_JITTER:
            base_delay = self.config.base_delay * (self.config.backoff_multiplier ** (attempt - 1))
            if self.config.jitter:
                # Add jitter to prevent thundering herd (±20% randomization)
                jitter_range = base_delay * 0.2
                delay = base_delay + random.uniform(-jitter_range, jitter_range)
            else:
                delay = base_delay
        else:
            delay = self.config.base_delay
        
        # Cap at maximum delay
        return min(delay, self.config.max_delay)
    
    async def _record_success(self, attempt: int, duration: float):
        """Record successful attempt metrics"""
        self.metrics.total_attempts += attempt
        self.metrics.successful_attempts += 1
        self.metrics.last_attempt_time = time.time()
        self.metrics.last_success_time = time.time()
        self.metrics.attempt_durations.append(duration)
        
        # Keep only recent durations to prevent memory growth
        if len(self.metrics.attempt_durations) > 100:
            self.metrics.attempt_durations = self.metrics.attempt_durations[-50:]
    
    async def _record_failure(self, attempt: int, duration: float, exception: Exception):
        """Record failed attempt metrics"""
        if attempt == self.config.max_attempts:  # Only count as failed if final attempt
            self.metrics.failed_attempts += 1
        
        self.metrics.last_attempt_time = time.time()
        self.metrics.attempt_durations.append(duration)
        
        # Track exception types
        exception_type = type(exception).__name__
        self.metrics.exception_counts[exception_type] = self.metrics.exception_counts.get(exception_type, 0) + 1
        
        # Keep only recent durations
        if len(self.metrics.attempt_durations) > 100:
            self.metrics.attempt_durations = self.metrics.attempt_durations[-50:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get current retry handler status and metrics"""
        avg_duration = 0.0
        if self.metrics.attempt_durations:
            avg_duration = sum(self.metrics.attempt_durations) / len(self.metrics.attempt_durations)
        
        success_rate = 0.0
        total_operations = self.metrics.successful_attempts + self.metrics.failed_attempts
        if total_operations > 0:
            success_rate = self.metrics.successful_attempts / total_operations
        
        return {
            "name": self.config.name,
            "config": {
                "max_attempts": self.config.max_attempts,
                "strategy": self.config.strategy.value,
                "base_delay": self.config.base_delay,
                "max_delay": self.config.max_delay,
                "backoff_multiplier": self.config.backoff_multiplier,
                "jitter_enabled": self.config.jitter
            },
            "metrics": {
                "total_attempts": self.metrics.total_attempts,
                "successful_operations": self.metrics.successful_attempts,
                "failed_operations": self.metrics.failed_attempts,
                "success_rate": round(success_rate * 100, 2),
                "total_delay_time": round(self.metrics.total_delay_time, 2),
                "average_attempt_duration": round(avg_duration, 2),
                "exception_counts": self.metrics.exception_counts
            },
            "timestamps": {
                "last_attempt": datetime.fromtimestamp(self.metrics.last_attempt_time).isoformat() if self.metrics.last_attempt_time else None,
                "last_success": datetime.fromtimestamp(self.metrics.last_success_time).isoformat() if self.metrics.last_success_time else None,
                "status_timestamp": datetime.now().isoformat()
            },
            "health": {
                "is_healthy": success_rate > 0.8,  # 80% success rate threshold
                "retry_enabled": True
            }
        }
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = RetryMetrics()
        if self.config.enable_logging:
            self.logger.info(f"Retry handler '{self.config.name}' metrics reset")


class RetryExhaustedException(Exception):
    """Exception raised when all retry attempts are exhausted"""
    
    def __init__(self, message: str, last_exception: Optional[Exception] = None, total_attempts: int = 0):
        super().__init__(message)
        self.last_exception = last_exception
        self.total_attempts = total_attempts


class RetryTimeoutException(Exception):
    """Exception raised when operation timeout is exceeded during retries"""
    pass


class RetryRegistry:
    """Global registry for managing retry handlers across the system"""
    
    def __init__(self):
        self._handlers: Dict[str, RetryHandler] = {}
        self._default_configs: Dict[str, RetryConfig] = {}
        self.logger = logging.getLogger("retry_registry")
    
    def register_default_config(self, name: str, config: RetryConfig):
        """Register default configuration for a retry handler"""
        self._default_configs[name] = config
        self.logger.info(f"Registered default retry config for: {name}")
    
    def get_retry_handler(self, name: str, config: Optional[RetryConfig] = None) -> RetryHandler:
        """Get or create retry handler by name"""
        if name not in self._handlers:
            # Use provided config or default config or create basic config
            if config is None:
                config = self._default_configs.get(name, RetryConfig(name=name))
            
            self._handlers[name] = RetryHandler(config)
            self.logger.info(f"Created retry handler: {name}")
        
        return self._handlers[name]
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all retry handlers"""
        return {name: handler.get_status() for name, handler in self._handlers.items()}
    
    def reset_all_metrics(self):
        """Reset metrics for all retry handlers"""
        for name, handler in self._handlers.items():
            handler.reset_metrics()
            self.logger.info(f"Reset metrics for retry handler: {name}")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary of all retry handlers"""
        if not self._handlers:
            return {
                "overall_health": "no_retry_handlers",
                "total_handlers": 0,
                "healthy_handlers": 0,
                "degraded_handlers": 0
            }
        
        statuses = self.get_all_status()
        
        healthy = sum(1 for status in statuses.values() if status["health"]["is_healthy"])
        total = len(self._handlers)
        
        overall_health = "healthy"
        if healthy < total * 0.8:  # Less than 80% healthy
            overall_health = "degraded"
        
        return {
            "overall_health": overall_health,
            "total_handlers": total,
            "healthy_handlers": healthy,
            "degraded_handlers": total - healthy,
            "timestamp": datetime.now().isoformat()
        }


# Global retry registry instance
_retry_registry = RetryRegistry()


def get_retry_registry() -> RetryRegistry:
    """Get global retry registry"""
    return _retry_registry


# Decorator for easy retry application
def retry(name: str, config: Optional[RetryConfig] = None):
    """
    Decorator to apply retry logic to async functions
    
    Usage:
        @retry("external_api", RetryConfig(max_attempts=5, strategy=RetryStrategy.EXPONENTIAL_WITH_JITTER))
        async def call_external_api():
            # Implementation that might fail
    """
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        handler = get_retry_registry().get_retry_handler(name, config)
        
        async def wrapper(*args, **kwargs):
            return await handler.execute_with_retry(func, *args, **kwargs)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator


# Predefined common retry configurations
class CommonRetryConfigs:
    """Common retry configurations for different scenarios"""
    
    @staticmethod
    def fast_api_calls() -> RetryConfig:
        """Config for fast API calls that should retry quickly"""
        return RetryConfig(
            name="fast_api",
            max_attempts=3,
            base_delay=0.5,
            max_delay=5.0,
            strategy=RetryStrategy.EXPONENTIAL_WITH_JITTER,
            attempt_timeout=10.0,
            operation_timeout=30.0
        )
    
    @staticmethod
    def slow_operations() -> RetryConfig:
        """Config for slow operations that need more patience"""
        return RetryConfig(
            name="slow_operations",
            max_attempts=5,
            base_delay=2.0,
            max_delay=60.0,
            strategy=RetryStrategy.EXPONENTIAL_WITH_JITTER,
            attempt_timeout=120.0,
            operation_timeout=600.0
        )
    
    @staticmethod
    def database_operations() -> RetryConfig:
        """Config for database operations"""
        return RetryConfig(
            name="database",
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            strategy=RetryStrategy.EXPONENTIAL_WITH_JITTER,
            attempt_timeout=30.0,
            operation_timeout=90.0
        )
    
    @staticmethod
    def file_operations() -> RetryConfig:
        """Config for file operations"""
        return RetryConfig(
            name="file_ops",
            max_attempts=3,
            base_delay=0.1,
            max_delay=2.0,
            strategy=RetryStrategy.LINEAR_BACKOFF,
            attempt_timeout=5.0,
            operation_timeout=15.0
        )
    
    @staticmethod
    def network_operations() -> RetryConfig:
        """Config for network operations"""
        return RetryConfig(
            name="network",
            max_attempts=4,
            base_delay=1.0,
            max_delay=30.0,
            strategy=RetryStrategy.EXPONENTIAL_WITH_JITTER,
            attempt_timeout=45.0,
            operation_timeout=180.0,
            retryable_exceptions=(ConnectionError, TimeoutError, OSError)
        )