#!/usr/bin/env python3
"""
WARPCORE Distributed Tracing and Error Correlation System
Tracks requests across PAP layers with correlation IDs and detailed context preservation
"""

import asyncio
import logging
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Awaitable, Set
import json
import traceback
from functools import wraps


class TraceLevel(Enum):
    """Trace detail levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SpanType(Enum):
    """Types of trace spans"""
    REQUEST = "request"           # HTTP request handling
    DATABASE = "database"         # Database operations
    EXTERNAL_API = "external_api" # External service calls
    COMPUTATION = "computation"   # CPU-intensive operations
    IO_OPERATION = "io_operation" # File/network I/O
    CACHE_OPERATION = "cache"     # Cache read/write
    AUTHENTICATION = "auth"       # Authentication/authorization
    MIDDLEWARE = "middleware"     # Middleware processing
    PROVIDER = "provider"         # Provider operations
    CONTROLLER = "controller"     # Controller business logic
    ORCHESTRATOR = "orchestrator" # Workflow orchestration
    EXECUTOR = "executor"         # Command execution


# Context variables for request tracing
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
span_stack_var: ContextVar[List[str]] = ContextVar('span_stack', default=[])


@dataclass
class SpanContext:
    """Context for a trace span"""
    span_id: str
    parent_span_id: Optional[str]
    trace_id: str
    correlation_id: str
    operation_name: str
    span_type: SpanType
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    status: str = "in_progress"  # in_progress, success, error
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    baggage: Dict[str, Any] = field(default_factory=dict)
    error_info: Optional[Dict[str, Any]] = None


@dataclass 
class TraceMetrics:
    """Metrics for a trace"""
    total_spans: int = 0
    successful_spans: int = 0
    failed_spans: int = 0
    total_duration: float = 0.0
    span_types_count: Dict[str, int] = field(default_factory=dict)
    error_count_by_type: Dict[str, int] = field(default_factory=dict)


class RequestTrace:
    """Complete trace for a request"""
    
    def __init__(self, trace_id: str, correlation_id: str):
        self.trace_id = trace_id
        self.correlation_id = correlation_id
        self.spans: Dict[str, SpanContext] = {}
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.root_span_id: Optional[str] = None
        self.status = "in_progress"
        self.error_count = 0
        self.metadata: Dict[str, Any] = {}
    
    def add_span(self, span: SpanContext):
        """Add a span to this trace"""
        self.spans[span.span_id] = span
        if not self.root_span_id:
            self.root_span_id = span.span_id
    
    def finish_trace(self):
        """Mark trace as completed"""
        self.end_time = time.time()
        self.status = "completed" if self.error_count == 0 else "error"
    
    def get_metrics(self) -> TraceMetrics:
        """Calculate trace metrics"""
        metrics = TraceMetrics()
        
        for span in self.spans.values():
            metrics.total_spans += 1
            
            if span.status == "success":
                metrics.successful_spans += 1
            elif span.status == "error":
                metrics.failed_spans += 1
                
            if span.duration:
                metrics.total_duration += span.duration
            
            # Count by span type
            span_type_name = span.span_type.value
            metrics.span_types_count[span_type_name] = metrics.span_types_count.get(span_type_name, 0) + 1
            
            # Count errors by type
            if span.error_info:
                error_type = span.error_info.get('exception_type', 'unknown')
                metrics.error_count_by_type[error_type] = metrics.error_count_by_type.get(error_type, 0) + 1
        
        return metrics
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary for serialization"""
        return {
            "trace_id": self.trace_id,
            "correlation_id": self.correlation_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": (self.end_time - self.start_time) if self.end_time else None,
            "status": self.status,
            "error_count": self.error_count,
            "root_span_id": self.root_span_id,
            "spans": {
                span_id: {
                    "span_id": span.span_id,
                    "parent_span_id": span.parent_span_id,
                    "operation_name": span.operation_name,
                    "span_type": span.span_type.value,
                    "start_time": span.start_time,
                    "end_time": span.end_time,
                    "duration": span.duration,
                    "status": span.status,
                    "tags": span.tags,
                    "logs": span.logs,
                    "baggage": span.baggage,
                    "error_info": span.error_info
                }
                for span_id, span in self.spans.items()
            },
            "metadata": self.metadata,
            "metrics": self.get_metrics().__dict__
        }


class TraceSpan:
    """Context manager for trace spans"""
    
    def __init__(self, operation_name: str, span_type: SpanType, tags: Dict[str, str] = None, tracer: 'RequestTracer' = None):
        self.operation_name = operation_name
        self.span_type = span_type
        self.tags = tags or {}
        self.span_context: Optional[SpanContext] = None
        self.tracer = tracer or get_request_tracer()
        
    async def __aenter__(self):
        """Enter async context manager"""
        self.span_context = await self.tracer.start_span(
            self.operation_name, 
            self.span_type, 
            self.tags
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager"""
        if self.span_context:
            if exc_type is not None:
                # Record exception information
                error_info = {
                    'exception_type': exc_type.__name__,
                    'exception_message': str(exc_val),
                    'traceback': traceback.format_exception(exc_type, exc_val, exc_tb)
                }
                await self.tracer.finish_span(self.span_context.span_id, "error", error_info)
            else:
                await self.tracer.finish_span(self.span_context.span_id, "success")
        return False  # Don't suppress exceptions
    
    def __enter__(self):
        """Enter sync context manager"""
        raise RuntimeError("Use 'async with' for TraceSpan")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit sync context manager"""
        raise RuntimeError("Use 'async with' for TraceSpan")
    
    def log(self, level: TraceLevel, message: str, data: Dict[str, Any] = None):
        """Add a log entry to the span"""
        if self.span_context:
            self.span_context.logs.append({
                'timestamp': datetime.now().isoformat(),
                'level': level.value,
                'message': message,
                'data': data or {}
            })
    
    def add_tag(self, key: str, value: str):
        """Add a tag to the span"""
        if self.span_context:
            self.span_context.tags[key] = value
    
    def add_baggage(self, key: str, value: Any):
        """Add baggage (context data) to the span"""
        if self.span_context:
            self.span_context.baggage[key] = value


class RequestTracer:
    """Distributed request tracer for WARPCORE"""
    
    def __init__(self):
        self.active_traces: Dict[str, RequestTrace] = {}
        self.completed_traces: List[RequestTrace] = []
        self.max_completed_traces = 1000  # Keep last 1000 traces
        self.logger = logging.getLogger("request_tracer")
        
        # Tracing configuration
        self.enabled = True
        self.sample_rate = 1.0  # Sample 100% of requests (adjust for production)
        self.max_trace_duration = 300  # 5 minutes max trace duration
        
        # Statistics
        self.total_traces = 0
        self.total_spans = 0
        self.error_traces = 0
    
    def generate_id(self) -> str:
        """Generate a unique ID"""
        return str(uuid.uuid4())
    
    def should_sample(self) -> bool:
        """Determine if this request should be sampled"""
        import random
        return random.random() < self.sample_rate
    
    async def start_trace(self, correlation_id: str = None) -> str:
        """Start a new trace"""
        if not self.enabled or not self.should_sample():
            return None
        
        trace_id = self.generate_id()
        if not correlation_id:
            correlation_id = self.generate_id()
        
        trace = RequestTrace(trace_id, correlation_id)
        self.active_traces[trace_id] = trace
        self.total_traces += 1
        
        # Set context variables
        correlation_id_var.set(correlation_id)
        trace_id_var.set(trace_id)
        span_stack_var.set([])
        
        self.logger.debug(f"Started trace: {trace_id} (correlation: {correlation_id})")
        return trace_id
    
    async def start_span(self, operation_name: str, span_type: SpanType, 
                        tags: Dict[str, str] = None) -> Optional[SpanContext]:
        """Start a new span within the current trace"""
        trace_id = trace_id_var.get()
        if not trace_id or trace_id not in self.active_traces:
            return None
        
        correlation_id = correlation_id_var.get()
        span_stack = span_stack_var.get() or []
        
        span_id = self.generate_id()
        parent_span_id = span_stack[-1] if span_stack else None
        
        span_context = SpanContext(
            span_id=span_id,
            parent_span_id=parent_span_id,
            trace_id=trace_id,
            correlation_id=correlation_id,
            operation_name=operation_name,
            span_type=span_type,
            start_time=time.time(),
            tags=tags or {}
        )
        
        # Add span to trace
        trace = self.active_traces[trace_id]
        trace.add_span(span_context)
        
        # Update span stack
        span_stack.append(span_id)
        span_stack_var.set(span_stack)
        
        self.total_spans += 1
        self.logger.debug(f"Started span: {operation_name} ({span_id}) in trace {trace_id}")
        
        return span_context
    
    async def finish_span(self, span_id: str, status: str = "success", 
                         error_info: Dict[str, Any] = None):
        """Finish a span"""
        trace_id = trace_id_var.get()
        if not trace_id or trace_id not in self.active_traces:
            return
        
        trace = self.active_traces[trace_id]
        if span_id not in trace.spans:
            return
        
        span = trace.spans[span_id]
        span.end_time = time.time()
        span.duration = span.end_time - span.start_time
        span.status = status
        
        if error_info:
            span.error_info = error_info
            trace.error_count += 1
        
        # Update span stack
        span_stack = span_stack_var.get() or []
        if span_stack and span_stack[-1] == span_id:
            span_stack.pop()
            span_stack_var.set(span_stack)
        
        self.logger.debug(f"Finished span: {span.operation_name} ({span_id}) - {status}")
    
    async def finish_trace(self, trace_id: str = None):
        """Finish a trace"""
        if not trace_id:
            trace_id = trace_id_var.get()
        
        if not trace_id or trace_id not in self.active_traces:
            return
        
        trace = self.active_traces[trace_id]
        trace.finish_trace()
        
        # Move to completed traces
        self.completed_traces.append(trace)
        del self.active_traces[trace_id]
        
        # Keep only recent completed traces
        if len(self.completed_traces) > self.max_completed_traces:
            self.completed_traces = self.completed_traces[-self.max_completed_traces:]
        
        if trace.error_count > 0:
            self.error_traces += 1
        
        self.logger.info(
            f"Finished trace {trace_id}: {len(trace.spans)} spans, "
            f"{trace.error_count} errors, "
            f"{trace.end_time - trace.start_time:.3f}s duration"
        )
        
        # Clear context variables
        correlation_id_var.set(None)
        trace_id_var.set(None)
        span_stack_var.set([])
    
    def get_current_trace_id(self) -> Optional[str]:
        """Get current trace ID from context"""
        return trace_id_var.get()
    
    def get_current_correlation_id(self) -> Optional[str]:
        """Get current correlation ID from context"""
        return correlation_id_var.get()
    
    def get_trace(self, trace_id: str) -> Optional[RequestTrace]:
        """Get a trace by ID (active or completed)"""
        if trace_id in self.active_traces:
            return self.active_traces[trace_id]
        
        for trace in self.completed_traces:
            if trace.trace_id == trace_id:
                return trace
        
        return None
    
    def get_trace_by_correlation_id(self, correlation_id: str) -> Optional[RequestTrace]:
        """Get a trace by correlation ID"""
        # Check active traces first
        for trace in self.active_traces.values():
            if trace.correlation_id == correlation_id:
                return trace
        
        # Check completed traces
        for trace in self.completed_traces:
            if trace.correlation_id == correlation_id:
                return trace
        
        return None
    
    def get_recent_traces(self, limit: int = 10) -> List[RequestTrace]:
        """Get recent traces"""
        all_traces = list(self.active_traces.values()) + self.completed_traces
        all_traces.sort(key=lambda t: t.start_time, reverse=True)
        return all_traces[:limit]
    
    def get_error_traces(self, limit: int = 10) -> List[RequestTrace]:
        """Get recent traces with errors"""
        error_traces = [t for t in self.completed_traces if t.error_count > 0]
        error_traces.sort(key=lambda t: t.start_time, reverse=True)
        return error_traces[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tracing statistics"""
        active_count = len(self.active_traces)
        completed_count = len(self.completed_traces)
        
        # Calculate average durations for completed traces
        avg_duration = 0.0
        if self.completed_traces:
            total_duration = sum(
                (t.end_time - t.start_time) for t in self.completed_traces 
                if t.end_time
            )
            avg_duration = total_duration / len(self.completed_traces)
        
        return {
            "enabled": self.enabled,
            "sample_rate": self.sample_rate,
            "total_traces": self.total_traces,
            "total_spans": self.total_spans,
            "error_traces": self.error_traces,
            "active_traces": active_count,
            "completed_traces": completed_count,
            "average_trace_duration": round(avg_duration, 3),
            "error_rate": (self.error_traces / max(1, self.total_traces)) * 100
        }
    
    async def cleanup_old_traces(self):
        """Clean up old active traces that may have been abandoned"""
        current_time = time.time()
        abandoned_traces = []
        
        for trace_id, trace in self.active_traces.items():
            if current_time - trace.start_time > self.max_trace_duration:
                abandoned_traces.append(trace_id)
        
        for trace_id in abandoned_traces:
            trace = self.active_traces[trace_id]
            trace.status = "abandoned"
            trace.end_time = current_time
            
            self.completed_traces.append(trace)
            del self.active_traces[trace_id]
            
            self.logger.warning(f"Cleaned up abandoned trace: {trace_id}")


# Global tracer instance
_request_tracer = RequestTracer()


def get_request_tracer() -> RequestTracer:
    """Get the global request tracer"""
    return _request_tracer


# Decorator for automatic span creation
def trace_operation(operation_name: str = None, span_type: SpanType = SpanType.COMPUTATION, 
                   tags: Dict[str, str] = None):
    """
    Decorator to automatically trace function execution
    
    Usage:
        @trace_operation("database_query", SpanType.DATABASE)
        async def query_database():
            # Implementation
    """
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        op_name = operation_name or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with TraceSpan(op_name, span_type, tags) as span:
                # Add function metadata as tags
                if span.span_context:
                    span.add_tag("function.name", func.__name__)
                    span.add_tag("function.module", func.__module__)
                    
                    # Add arguments as baggage (be careful with sensitive data)
                    if args:
                        span.add_baggage("args_count", len(args))
                    if kwargs:
                        span.add_baggage("kwargs_keys", list(kwargs.keys()))
                
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Context management functions
def get_current_correlation_id() -> Optional[str]:
    """Get current correlation ID"""
    return correlation_id_var.get()


def get_current_trace_id() -> Optional[str]:
    """Get current trace ID"""
    return trace_id_var.get()


def set_trace_metadata(key: str, value: Any):
    """Set metadata on the current trace"""
    trace_id = trace_id_var.get()
    if trace_id:
        tracer = get_request_tracer()
        trace = tracer.get_trace(trace_id)
        if trace:
            trace.metadata[key] = value


# Error correlation helpers
def correlate_error_with_trace(exception: Exception, additional_context: Dict[str, Any] = None):
    """Correlate an error with the current trace"""
    trace_id = trace_id_var.get()
    correlation_id = correlation_id_var.get()
    
    if not trace_id and not correlation_id:
        return None
    
    error_context = {
        "trace_id": trace_id,
        "correlation_id": correlation_id,
        "exception_type": type(exception).__name__,
        "exception_message": str(exception),
        "timestamp": datetime.now().isoformat(),
        "traceback": traceback.format_exc()
    }
    
    if additional_context:
        error_context.update(additional_context)
    
    return error_context


# Middleware for FastAPI integration
async def tracing_middleware(request, call_next):
    """FastAPI middleware for request tracing"""
    tracer = get_request_tracer()
    
    # Extract correlation ID from headers or generate new one
    correlation_id = request.headers.get('x-correlation-id') or tracer.generate_id()
    
    # Start trace
    trace_id = await tracer.start_trace(correlation_id)
    
    if trace_id:
        async with TraceSpan("http_request", SpanType.REQUEST, {
            "http.method": request.method,
            "http.url": str(request.url),
            "http.route": getattr(request, "route", {}).get("path", "unknown")
        }) as span:
            try:
                # Add request metadata
                span.add_baggage("request.method", request.method)
                span.add_baggage("request.path", request.url.path)
                span.add_baggage("request.query_params", dict(request.query_params))
                
                response = await call_next(request)
                
                # Add response metadata
                span.add_tag("http.status_code", str(response.status_code))
                
                # Add correlation ID to response headers
                response.headers["x-correlation-id"] = correlation_id
                response.headers["x-trace-id"] = trace_id
                
                return response
                
            finally:
                await tracer.finish_trace(trace_id)
    else:
        # Tracing disabled, process normally
        response = await call_next(request)
        response.headers["x-correlation-id"] = correlation_id
        return response