#!/usr/bin/env python3
"""
WARPCORE Error Classification and Recovery System
Provides intelligent error categorization and automated recovery strategies
"""

import asyncio
import inspect
import logging
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, Callable, Awaitable, Type, List, Union, Tuple
from datetime import datetime, timedelta
from abc import ABC, abstractmethod


class ErrorCategory(Enum):
    """High-level error categories"""
    TRANSIENT = "transient"          # Temporary failures, likely to recover
    PERMANENT = "permanent"          # Persistent failures, unlikely to recover
    CONFIGURATION = "configuration" # Configuration or setup issues
    AUTHENTICATION = "authentication" # Auth/permission issues
    NETWORK = "network"             # Network connectivity issues
    RESOURCE = "resource"           # Resource exhaustion (memory, disk, etc.)
    BUSINESS_LOGIC = "business"     # Application business logic errors
    SYSTEM = "system"               # System-level failures
    EXTERNAL = "external"           # External service failures
    UNKNOWN = "unknown"             # Unclassified errors


class ErrorSeverity(Enum):
    """Error severity levels"""
    CRITICAL = "critical"           # System is unusable
    HIGH = "high"                  # Major functionality affected
    MEDIUM = "medium"              # Some functionality affected
    LOW = "low"                    # Minor issues
    INFO = "info"                  # Informational


class RecoveryAction(Enum):
    """Types of recovery actions"""
    RETRY = "retry"                # Retry the operation
    FALLBACK = "fallback"          # Use alternative approach
    DEGRADE = "degrade"            # Reduce functionality
    NOTIFY = "notify"              # Alert operators
    RESTART = "restart"            # Restart component
    IGNORE = "ignore"              # Safe to ignore
    FAIL_FAST = "fail_fast"        # Don't attempt recovery


@dataclass
class ErrorClassification:
    """Classification of an error"""
    category: ErrorCategory
    severity: ErrorSeverity
    is_recoverable: bool
    recovery_actions: List[RecoveryAction]
    confidence: float = 1.0  # Confidence in classification (0-1)
    context: Dict[str, Any] = field(default_factory=dict)
    classification_reason: str = ""
    recommended_retry_count: int = 0
    recommended_backoff: float = 1.0


@dataclass
class RecoveryResult:
    """Result of a recovery attempt"""
    success: bool
    action_taken: RecoveryAction
    message: str
    duration: float
    context: Dict[str, Any] = field(default_factory=dict)
    should_retry: bool = False
    fallback_available: bool = False


class ErrorClassifier:
    """
    Intelligent error classifier that categorizes exceptions
    and recommends recovery strategies
    """
    
    def __init__(self):
        self.logger = logging.getLogger("error_classifier")
        self._classification_rules = []
        self._pattern_cache = {}
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default classification rules"""
        
        # Network errors - typically transient and recoverable
        self.add_classification_rule(
            exception_types=(ConnectionError, ConnectionResetError, ConnectionRefusedError),
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            is_recoverable=True,
            recovery_actions=[RecoveryAction.RETRY, RecoveryAction.FALLBACK],
            recommended_retry_count=3,
            recommended_backoff=2.0
        )
        
        # Timeout errors - often transient
        self.add_classification_rule(
            exception_types=(asyncio.TimeoutError, TimeoutError),
            category=ErrorCategory.TRANSIENT,
            severity=ErrorSeverity.MEDIUM,
            is_recoverable=True,
            recovery_actions=[RecoveryAction.RETRY, RecoveryAction.DEGRADE],
            recommended_retry_count=2,
            recommended_backoff=5.0
        )
        
        # Permission/authentication errors - usually permanent
        self.add_classification_rule(
            exception_types=(PermissionError,),
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            is_recoverable=False,
            recovery_actions=[RecoveryAction.NOTIFY, RecoveryAction.FAIL_FAST],
            recommended_retry_count=0,
            recommended_backoff=0.0
        )
        
        # Resource errors - may be transient
        self.add_classification_rule(
            exception_types=(MemoryError, OSError),
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.HIGH,
            is_recoverable=True,
            recovery_actions=[RecoveryAction.RETRY, RecoveryAction.DEGRADE, RecoveryAction.RESTART],
            recommended_retry_count=1,
            recommended_backoff=10.0
        )
        
        # File system errors
        self.add_classification_rule(
            exception_types=(FileNotFoundError, IsADirectoryError, FileExistsError),
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.MEDIUM,
            is_recoverable=True,
            recovery_actions=[RecoveryAction.FALLBACK, RecoveryAction.NOTIFY],
            recommended_retry_count=1,
            recommended_backoff=1.0
        )
        
        # Value errors - usually business logic issues
        self.add_classification_rule(
            exception_types=(ValueError, TypeError),
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.MEDIUM,
            is_recoverable=False,
            recovery_actions=[RecoveryAction.NOTIFY, RecoveryAction.FAIL_FAST],
            recommended_retry_count=0,
            recommended_backoff=0.0
        )
        
        # KeyError, AttributeError - usually configuration or code issues
        self.add_classification_rule(
            exception_types=(KeyError, AttributeError),
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            is_recoverable=False,
            recovery_actions=[RecoveryAction.FALLBACK, RecoveryAction.NOTIFY],
            recommended_retry_count=0,
            recommended_backoff=0.0
        )
    
    def add_classification_rule(self,
                              exception_types: Tuple[Type[Exception], ...],
                              category: ErrorCategory,
                              severity: ErrorSeverity,
                              is_recoverable: bool,
                              recovery_actions: List[RecoveryAction],
                              recommended_retry_count: int = 0,
                              recommended_backoff: float = 1.0,
                              pattern_matcher: Optional[Callable[[Exception], bool]] = None):
        """Add a custom classification rule"""
        rule = {
            'exception_types': exception_types,
            'category': category,
            'severity': severity,
            'is_recoverable': is_recoverable,
            'recovery_actions': recovery_actions,
            'recommended_retry_count': recommended_retry_count,
            'recommended_backoff': recommended_backoff,
            'pattern_matcher': pattern_matcher
        }
        self._classification_rules.append(rule)
        self.logger.debug(f"Added classification rule for {exception_types}")
    
    def classify_error(self, exception: Exception, context: Dict[str, Any] = None) -> ErrorClassification:
        """
        Classify an error and recommend recovery strategies
        
        Args:
            exception: The exception to classify
            context: Additional context about the error
            
        Returns:
            ErrorClassification with recommended recovery strategy
        """
        context = context or {}
        exception_type = type(exception)
        
        # Check cache first
        cache_key = (exception_type.__name__, str(exception)[:100])
        if cache_key in self._pattern_cache:
            cached_result = self._pattern_cache[cache_key]
            cached_result.context.update(context)
            return cached_result
        
        # Apply classification rules
        for rule in self._classification_rules:
            if isinstance(exception, rule['exception_types']):
                # Check pattern matcher if provided
                if rule['pattern_matcher'] and not rule['pattern_matcher'](exception):
                    continue
                
                classification = ErrorClassification(
                    category=rule['category'],
                    severity=rule['severity'],
                    is_recoverable=rule['is_recoverable'],
                    recovery_actions=rule['recovery_actions'].copy(),
                    context=context,
                    classification_reason=f"Matched rule for {rule['exception_types']}",
                    recommended_retry_count=rule['recommended_retry_count'],
                    recommended_backoff=rule['recommended_backoff'],
                    confidence=0.9
                )
                
                # Cache the result
                self._pattern_cache[cache_key] = classification
                return classification
        
        # No specific rule matched - use heuristics
        classification = self._heuristic_classification(exception, context)
        self._pattern_cache[cache_key] = classification
        
        # Clean cache if it gets too large
        if len(self._pattern_cache) > 1000:
            # Keep only recent entries
            recent_keys = list(self._pattern_cache.keys())[-500:]
            self._pattern_cache = {k: self._pattern_cache[k] for k in recent_keys}
        
        return classification
    
    def _heuristic_classification(self, exception: Exception, context: Dict[str, Any]) -> ErrorClassification:
        """Use heuristics to classify unknown errors"""
        exception_name = type(exception).__name__.lower()
        message = str(exception).lower()
        
        # Heuristic analysis based on exception name and message
        if any(keyword in exception_name or keyword in message for keyword in 
               ['timeout', 'connection', 'network', 'unreachable', 'refused']):
            return ErrorClassification(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                is_recoverable=True,
                recovery_actions=[RecoveryAction.RETRY, RecoveryAction.FALLBACK],
                context=context,
                classification_reason="Heuristic: Network-related keywords detected",
                recommended_retry_count=3,
                recommended_backoff=2.0,
                confidence=0.7
            )
        
        if any(keyword in exception_name or keyword in message for keyword in 
               ['memory', 'resource', 'limit', 'quota', 'space']):
            return ErrorClassification(
                category=ErrorCategory.RESOURCE,
                severity=ErrorSeverity.HIGH,
                is_recoverable=True,
                recovery_actions=[RecoveryAction.DEGRADE, RecoveryAction.RETRY],
                context=context,
                classification_reason="Heuristic: Resource-related keywords detected",
                recommended_retry_count=1,
                recommended_backoff=10.0,
                confidence=0.7
            )
        
        if any(keyword in exception_name or keyword in message for keyword in 
               ['auth', 'permission', 'forbidden', 'unauthorized', 'credential']):
            return ErrorClassification(
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.HIGH,
                is_recoverable=False,
                recovery_actions=[RecoveryAction.NOTIFY, RecoveryAction.FAIL_FAST],
                context=context,
                classification_reason="Heuristic: Authentication-related keywords detected",
                recommended_retry_count=0,
                recommended_backoff=0.0,
                confidence=0.8
            )
        
        # Default classification for unknown errors
        return ErrorClassification(
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.MEDIUM,
            is_recoverable=True,
            recovery_actions=[RecoveryAction.RETRY, RecoveryAction.NOTIFY],
            context=context,
            classification_reason="Heuristic: Default classification for unknown error",
            recommended_retry_count=1,
            recommended_backoff=5.0,
            confidence=0.5
        )


class RecoveryStrategy(ABC):
    """Base class for recovery strategies"""
    
    @abstractmethod
    async def execute(self, exception: Exception, classification: ErrorClassification, 
                     context: Dict[str, Any]) -> RecoveryResult:
        """Execute recovery strategy"""
        pass
    
    @abstractmethod
    def can_handle(self, action: RecoveryAction) -> bool:
        """Check if this strategy can handle the given action"""
        pass


class RetryStrategy(RecoveryStrategy):
    """Recovery strategy that retries operations"""
    
    def can_handle(self, action: RecoveryAction) -> bool:
        return action == RecoveryAction.RETRY
    
    async def execute(self, exception: Exception, classification: ErrorClassification,
                     context: Dict[str, Any]) -> RecoveryResult:
        """Execute retry recovery"""
        start_time = time.time()
        
        # Implement retry with exponential backoff
        retry_count = classification.recommended_retry_count
        backoff = classification.recommended_backoff
        
        # For now, just return a result indicating retry should be attempted
        return RecoveryResult(
            success=False,  # Indicates retry should be attempted
            action_taken=RecoveryAction.RETRY,
            message=f"Retry recommended: {retry_count} attempts with {backoff}s backoff",
            duration=time.time() - start_time,
            context={"retry_count": retry_count, "backoff": backoff},
            should_retry=True
        )


class FallbackStrategy(RecoveryStrategy):
    """Recovery strategy that uses fallback mechanisms"""
    
    def can_handle(self, action: RecoveryAction) -> bool:
        return action == RecoveryAction.FALLBACK
    
    async def execute(self, exception: Exception, classification: ErrorClassification,
                     context: Dict[str, Any]) -> RecoveryResult:
        """Execute fallback recovery"""
        start_time = time.time()
        
        # Look for fallback functions in context
        fallback_func = context.get('fallback_function')
        fallback_result = context.get('fallback_result')
        
        if fallback_func and callable(fallback_func):
            try:
                if inspect.iscoroutinefunction(fallback_func):
                    result = await fallback_func()
                else:
                    result = fallback_func()
                
                return RecoveryResult(
                    success=True,
                    action_taken=RecoveryAction.FALLBACK,
                    message="Successfully executed fallback function",
                    duration=time.time() - start_time,
                    context={"fallback_result": result},
                    fallback_available=True
                )
            except Exception as fallback_error:
                return RecoveryResult(
                    success=False,
                    action_taken=RecoveryAction.FALLBACK,
                    message=f"Fallback function failed: {fallback_error}",
                    duration=time.time() - start_time,
                    context={"fallback_error": str(fallback_error)}
                )
        
        elif fallback_result is not None:
            return RecoveryResult(
                success=True,
                action_taken=RecoveryAction.FALLBACK,
                message="Using provided fallback result",
                duration=time.time() - start_time,
                context={"fallback_result": fallback_result},
                fallback_available=True
            )
        
        return RecoveryResult(
            success=False,
            action_taken=RecoveryAction.FALLBACK,
            message="No fallback mechanism available",
            duration=time.time() - start_time,
            fallback_available=False
        )


class DegradeStrategy(RecoveryStrategy):
    """Recovery strategy that degrades functionality gracefully"""
    
    def can_handle(self, action: RecoveryAction) -> bool:
        return action == RecoveryAction.DEGRADE
    
    async def execute(self, exception: Exception, classification: ErrorClassification,
                     context: Dict[str, Any]) -> RecoveryResult:
        """Execute graceful degradation"""
        start_time = time.time()
        
        degradation_modes = context.get('degradation_modes', [])
        
        if degradation_modes:
            # Try degradation modes in order
            for mode in degradation_modes:
                try:
                    if callable(mode):
                        if inspect.iscoroutinefunction(mode):
                            result = await mode()
                        else:
                            result = mode()
                        
                        return RecoveryResult(
                            success=True,
                            action_taken=RecoveryAction.DEGRADE,
                            message=f"Successfully activated degraded mode",
                            duration=time.time() - start_time,
                            context={"degraded_mode": str(mode), "result": result}
                        )
                except Exception as deg_error:
                    continue  # Try next degradation mode
        
        return RecoveryResult(
            success=False,
            action_taken=RecoveryAction.DEGRADE,
            message="No working degradation mode available",
            duration=time.time() - start_time
        )


class NotifyStrategy(RecoveryStrategy):
    """Recovery strategy that notifies operators"""
    
    def can_handle(self, action: RecoveryAction) -> bool:
        return action == RecoveryAction.NOTIFY
    
    async def execute(self, exception: Exception, classification: ErrorClassification,
                     context: Dict[str, Any]) -> RecoveryResult:
        """Execute notification strategy"""
        start_time = time.time()
        
        notification_handler = context.get('notification_handler')
        
        notification_data = {
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'category': classification.category.value,
            'severity': classification.severity.value,
            'traceback': traceback.format_exc(),
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        
        if notification_handler and callable(notification_handler):
            try:
                if inspect.iscoroutinefunction(notification_handler):
                    await notification_handler(notification_data)
                else:
                    notification_handler(notification_data)
                
                return RecoveryResult(
                    success=True,
                    action_taken=RecoveryAction.NOTIFY,
                    message="Successfully sent notification",
                    duration=time.time() - start_time,
                    context={"notification_sent": True}
                )
            except Exception as notify_error:
                return RecoveryResult(
                    success=False,
                    action_taken=RecoveryAction.NOTIFY,
                    message=f"Notification failed: {notify_error}",
                    duration=time.time() - start_time,
                    context={"notification_error": str(notify_error)}
                )
        
        # Default: log the notification
        logging.getLogger("error_recovery").error(
            f"Error notification: {notification_data['exception_type']} - {notification_data['exception_message']}"
        )
        
        return RecoveryResult(
            success=True,
            action_taken=RecoveryAction.NOTIFY,
            message="Logged error notification",
            duration=time.time() - start_time,
            context={"logged": True}
        )


class ErrorRecoverySystem:
    """
    Central error recovery system that coordinates classification and recovery
    """
    
    def __init__(self):
        self.classifier = ErrorClassifier()
        self.strategies: Dict[RecoveryAction, RecoveryStrategy] = {}
        self.logger = logging.getLogger("error_recovery_system")
        
        # Register default recovery strategies
        self._register_default_strategies()
        
        # Metrics
        self.recovery_attempts = 0
        self.successful_recoveries = 0
        self.failed_recoveries = 0
        self.recovery_history = []
    
    def _register_default_strategies(self):
        """Register default recovery strategies"""
        self.register_strategy(RetryStrategy())
        self.register_strategy(FallbackStrategy())
        self.register_strategy(DegradeStrategy())
        self.register_strategy(NotifyStrategy())
    
    def register_strategy(self, strategy: RecoveryStrategy):
        """Register a recovery strategy"""
        for action in RecoveryAction:
            if strategy.can_handle(action):
                self.strategies[action] = strategy
        self.logger.info(f"Registered recovery strategy: {type(strategy).__name__}")
    
    async def handle_error(self, exception: Exception, context: Dict[str, Any] = None) -> RecoveryResult:
        """
        Handle an error with classification and recovery
        
        Args:
            exception: The exception to handle
            context: Additional context for recovery
            
        Returns:
            RecoveryResult indicating success/failure and actions taken
        """
        start_time = time.time()
        context = context or {}
        
        try:
            # Classify the error
            classification = self.classifier.classify_error(exception, context)
            
            self.logger.info(
                f"Error classified - Category: {classification.category.value}, "
                f"Severity: {classification.severity.value}, "
                f"Recoverable: {classification.is_recoverable}"
            )
            
            # Track metrics
            self.recovery_attempts += 1
            
            # If not recoverable, fail fast
            if not classification.is_recoverable:
                result = RecoveryResult(
                    success=False,
                    action_taken=RecoveryAction.FAIL_FAST,
                    message=f"Error classified as non-recoverable: {classification.classification_reason}",
                    duration=time.time() - start_time,
                    context={"classification": classification}
                )
                self._record_recovery_attempt(classification, result)
                return result
            
            # Try recovery actions in order of preference
            for action in classification.recovery_actions:
                if action in self.strategies:
                    try:
                        strategy = self.strategies[action]
                        result = await strategy.execute(exception, classification, context)
                        
                        if result.success:
                            self.successful_recoveries += 1
                            self.logger.info(
                                f"Recovery successful using {action.value}: {result.message}"
                            )
                        else:
                            self.logger.warning(
                                f"Recovery attempt failed using {action.value}: {result.message}"
                            )
                        
                        self._record_recovery_attempt(classification, result)
                        return result
                        
                    except Exception as recovery_error:
                        self.logger.error(f"Recovery strategy {action.value} failed: {recovery_error}")
                        continue
            
            # No recovery strategy worked
            self.failed_recoveries += 1
            result = RecoveryResult(
                success=False,
                action_taken=RecoveryAction.FAIL_FAST,
                message="All recovery strategies failed",
                duration=time.time() - start_time,
                context={"classification": classification}
            )
            self._record_recovery_attempt(classification, result)
            return result
            
        except Exception as system_error:
            self.failed_recoveries += 1
            self.logger.error(f"Error recovery system failed: {system_error}")
            
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.FAIL_FAST,
                message=f"Recovery system error: {system_error}",
                duration=time.time() - start_time,
                context={"system_error": str(system_error)}
            )
    
    def _record_recovery_attempt(self, classification: ErrorClassification, result: RecoveryResult):
        """Record recovery attempt for analysis"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'category': classification.category.value,
            'severity': classification.severity.value,
            'action_taken': result.action_taken.value,
            'success': result.success,
            'duration': result.duration,
            'confidence': classification.confidence
        }
        
        self.recovery_history.append(record)
        
        # Keep only recent history to prevent memory growth
        if len(self.recovery_history) > 1000:
            self.recovery_history = self.recovery_history[-500:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the error recovery system"""
        success_rate = 0.0
        if self.recovery_attempts > 0:
            success_rate = self.successful_recoveries / self.recovery_attempts
        
        recent_history = self.recovery_history[-10:] if self.recovery_history else []
        
        return {
            "recovery_metrics": {
                "total_attempts": self.recovery_attempts,
                "successful_recoveries": self.successful_recoveries,
                "failed_recoveries": self.failed_recoveries,
                "success_rate": round(success_rate * 100, 2)
            },
            "registered_strategies": list(self.strategies.keys()),
            "recent_history": recent_history,
            "classifier_cache_size": len(self.classifier._pattern_cache),
            "classification_rules": len(self.classifier._classification_rules),
            "timestamp": datetime.now().isoformat(),
            "is_healthy": success_rate > 0.7  # 70% success rate threshold
        }
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.recovery_attempts = 0
        self.successful_recoveries = 0
        self.failed_recoveries = 0
        self.recovery_history = []
        self.logger.info("Error recovery system metrics reset")


# Global error recovery system instance
_error_recovery_system = ErrorRecoverySystem()


def get_error_recovery_system() -> ErrorRecoverySystem:
    """Get global error recovery system"""
    return _error_recovery_system


# Decorator for automatic error recovery
def with_error_recovery(context: Dict[str, Any] = None):
    """
    Decorator to apply automatic error recovery to functions
    
    Usage:
        @with_error_recovery({'fallback_result': 'default_value'})
        async def potentially_failing_function():
            # Implementation that might fail
    """
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                recovery_system = get_error_recovery_system()
                recovery_result = await recovery_system.handle_error(e, context or {})
                
                if recovery_result.success and 'fallback_result' in recovery_result.context:
                    return recovery_result.context['fallback_result']
                elif recovery_result.should_retry:
                    # Let retry mechanism handle this
                    raise e
                else:
                    # Re-raise the original exception if recovery failed
                    raise e
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator