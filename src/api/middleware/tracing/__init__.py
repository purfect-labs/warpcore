#!/usr/bin/env python3
"""
WARPCORE Distributed Tracing and Error Correlation Module
Provides comprehensive request tracing and error analysis capabilities
"""

from .request_tracer import (
    get_request_tracer,
    get_current_correlation_id,
    get_current_trace_id,
    TraceSpan,
    SpanType,
    trace_operation,
    tracing_middleware,
    correlate_error_with_trace,
    set_trace_metadata
)

from .error_correlator import (
    get_error_correlator,
    correlate_error,
    get_error_context,
    ErrorSeverity,
    ErrorCategory,
    CorrelatedError,
    ErrorCluster,
    ErrorFingerprint
)

__all__ = [
    # Request Tracer
    "get_request_tracer",
    "get_current_correlation_id", 
    "get_current_trace_id",
    "TraceSpan",
    "SpanType",
    "trace_operation",
    "tracing_middleware",
    "correlate_error_with_trace",
    "set_trace_metadata",
    
    # Error Correlator
    "get_error_correlator",
    "correlate_error",
    "get_error_context", 
    "ErrorSeverity",
    "ErrorCategory",
    "CorrelatedError",
    "ErrorCluster",
    "ErrorFingerprint"
]