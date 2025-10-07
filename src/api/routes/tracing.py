#!/usr/bin/env python3
"""
WARPCORE Distributed Tracing and Error Correlation API Endpoints
Exposes tracing data, correlation analysis, and error insights
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..middleware.tracing.request_tracer import (
    get_request_tracer, 
    get_current_correlation_id, 
    get_current_trace_id,
    TraceSpan,
    SpanType
)
from ..middleware.tracing.error_correlator import (
    get_error_correlator,
    ErrorSeverity,
    ErrorCategory,
    correlate_error
)


# Pydantic models for API responses
class TraceInfo(BaseModel):
    trace_id: str
    correlation_id: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    status: str
    error_count: int
    span_count: int
    root_span_id: Optional[str] = None


class SpanInfo(BaseModel):
    span_id: str
    parent_span_id: Optional[str] = None
    operation_name: str
    span_type: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    status: str
    tags: Dict[str, str] = Field(default_factory=dict)
    error_info: Optional[Dict[str, Any]] = None


class DetailedTrace(BaseModel):
    trace_id: str
    correlation_id: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    status: str
    error_count: int
    root_span_id: Optional[str] = None
    spans: Dict[str, SpanInfo] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ErrorInfo(BaseModel):
    error_id: str
    timestamp: float
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None
    exception_type: str
    exception_message: str
    function_name: str
    module_name: str
    file_name: str
    line_number: int
    category: str
    severity: str
    fingerprint: str
    correlation_score: float = 0.0
    related_error_count: int = 0


class ErrorClusterInfo(BaseModel):
    cluster_id: str
    fingerprint: str
    first_seen: float
    last_seen: float
    count: int
    error_rate: float
    trend: str
    affected_traces_count: int
    affected_users_count: int
    suspected_root_causes: List[str] = Field(default_factory=list)
    pattern_analysis: Dict[str, Any] = Field(default_factory=dict)


class TracingStatistics(BaseModel):
    enabled: bool
    sample_rate: float
    total_traces: int
    total_spans: int
    error_traces: int
    active_traces: int
    completed_traces: int
    average_trace_duration: float
    error_rate: float


class CorrelationStatistics(BaseModel):
    total_errors: int
    total_clusters: int
    active_clusters: int
    correlation_hits: int
    correlation_rate: float
    recent_errors: int
    category_distribution: Dict[str, int] = Field(default_factory=dict)
    severity_distribution: Dict[str, int] = Field(default_factory=dict)
    high_priority_clusters: int


# Create router
router = APIRouter(prefix="/api/tracing", tags=["tracing"])
logger = logging.getLogger("tracing_api")


@router.get("/health", summary="Check tracing system health")
async def get_tracing_health():
    """Check if tracing systems are operational"""
    tracer = get_request_tracer()
    correlator = get_error_correlator()
    
    return JSONResponse({
        "status": "healthy",
        "tracing_enabled": tracer.enabled,
        "error_correlation_enabled": True,
        "current_trace_id": get_current_trace_id(),
        "current_correlation_id": get_current_correlation_id(),
        "timestamp": datetime.now().isoformat()
    })


@router.get("/statistics", response_model=Dict[str, Any], summary="Get comprehensive tracing statistics")
async def get_tracing_statistics():
    """Get detailed statistics about tracing and error correlation"""
    async with TraceSpan("get_tracing_statistics", SpanType.REQUEST):
        tracer = get_request_tracer()
        correlator = get_error_correlator()
        
        tracing_stats = tracer.get_statistics()
        correlation_stats = correlator.get_correlation_statistics()
        
        return JSONResponse({
            "tracing": TracingStatistics(**tracing_stats).dict(),
            "error_correlation": CorrelationStatistics(**correlation_stats).dict(),
            "system_health": {
                "active_traces": tracing_stats["active_traces"],
                "error_rate": correlation_stats["correlation_rate"],
                "high_priority_issues": correlation_stats["high_priority_clusters"]
            },
            "timestamp": datetime.now().isoformat()
        })


@router.get("/traces", response_model=List[TraceInfo], summary="Get recent traces")
async def get_recent_traces(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of traces to return"),
    include_errors_only: bool = Query(False, description="Only return traces with errors")
):
    """Get list of recent traces with basic information"""
    async with TraceSpan("get_recent_traces", SpanType.REQUEST, {"limit": str(limit)}):
        tracer = get_request_tracer()
        
        if include_errors_only:
            traces = tracer.get_error_traces(limit)
        else:
            traces = tracer.get_recent_traces(limit)
        
        trace_infos = []
        for trace in traces:
            trace_info = TraceInfo(
                trace_id=trace.trace_id,
                correlation_id=trace.correlation_id,
                start_time=trace.start_time,
                end_time=trace.end_time,
                duration=(trace.end_time - trace.start_time) if trace.end_time else None,
                status=trace.status,
                error_count=trace.error_count,
                span_count=len(trace.spans),
                root_span_id=trace.root_span_id
            )
            trace_infos.append(trace_info)
        
        return JSONResponse([info.dict() for info in trace_infos])


@router.get("/traces/{trace_id}", response_model=DetailedTrace, summary="Get detailed trace information")
async def get_trace_details(trace_id: str):
    """Get detailed information about a specific trace"""
    async with TraceSpan("get_trace_details", SpanType.REQUEST, {"trace_id": trace_id}):
        tracer = get_request_tracer()
        trace = tracer.get_trace(trace_id)
        
        if not trace:
            raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
        
        # Convert spans to SpanInfo models
        span_infos = {}
        for span_id, span in trace.spans.items():
            span_info = SpanInfo(
                span_id=span.span_id,
                parent_span_id=span.parent_span_id,
                operation_name=span.operation_name,
                span_type=span.span_type.value,
                start_time=span.start_time,
                end_time=span.end_time,
                duration=span.duration,
                status=span.status,
                tags=span.tags,
                error_info=span.error_info
            )
            span_infos[span_id] = span_info
        
        detailed_trace = DetailedTrace(
            trace_id=trace.trace_id,
            correlation_id=trace.correlation_id,
            start_time=trace.start_time,
            end_time=trace.end_time,
            duration=(trace.end_time - trace.start_time) if trace.end_time else None,
            status=trace.status,
            error_count=trace.error_count,
            root_span_id=trace.root_span_id,
            spans={sid: sinfo.dict() for sid, sinfo in span_infos.items()},
            metadata=trace.metadata,
            metrics=trace.get_metrics().__dict__
        )
        
        return JSONResponse(detailed_trace.dict())


@router.get("/traces/correlation/{correlation_id}", response_model=DetailedTrace, summary="Get trace by correlation ID")
async def get_trace_by_correlation_id(correlation_id: str):
    """Get trace information using correlation ID"""
    async with TraceSpan("get_trace_by_correlation_id", SpanType.REQUEST, {"correlation_id": correlation_id}):
        tracer = get_request_tracer()
        trace = tracer.get_trace_by_correlation_id(correlation_id)
        
        if not trace:
            raise HTTPException(status_code=404, detail=f"No trace found for correlation ID {correlation_id}")
        
        # Reuse the logic from get_trace_details
        return await get_trace_details(trace.trace_id)


@router.get("/errors", response_model=List[ErrorInfo], summary="Get recent errors")
async def get_recent_errors(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of errors to return"),
    severity: Optional[str] = Query(None, description="Filter by severity (low, medium, high, critical)"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """Get list of recent errors with correlation information"""
    async with TraceSpan("get_recent_errors", SpanType.REQUEST, {
        "limit": str(limit),
        "severity": severity or "all",
        "category": category or "all"
    }):
        correlator = get_error_correlator()
        errors = correlator.get_recent_errors(limit)
        
        # Apply filters
        if severity:
            severity_filter = ErrorSeverity(severity.lower())
            errors = [e for e in errors if e.severity == severity_filter]
        
        if category:
            category_filter = ErrorCategory(category.lower())
            errors = [e for e in errors if e.category == category_filter]
        
        error_infos = []
        for error in errors:
            error_info = ErrorInfo(
                error_id=error.error_id,
                timestamp=error.timestamp,
                trace_id=error.trace_id,
                correlation_id=error.correlation_id,
                exception_type=error.exception_type,
                exception_message=error.exception_message,
                function_name=error.function_name,
                module_name=error.module_name,
                file_name=error.file_name,
                line_number=error.line_number,
                category=error.category.value,
                severity=error.severity.value,
                fingerprint=str(error.fingerprint),
                correlation_score=error.correlation_score,
                related_error_count=len(error.related_error_ids)
            )
            error_infos.append(error_info)
        
        return JSONResponse([info.dict() for info in error_infos])


@router.get("/errors/{error_id}", response_model=Dict[str, Any], summary="Get detailed error information")
async def get_error_details(error_id: str):
    """Get detailed information about a specific error"""
    async with TraceSpan("get_error_details", SpanType.REQUEST, {"error_id": error_id}):
        correlator = get_error_correlator()
        error = correlator.get_error(error_id)
        
        if not error:
            raise HTTPException(status_code=404, detail=f"Error {error_id} not found")
        
        # Get related errors
        related_errors = []
        for related_id in error.related_error_ids:
            related_error = correlator.get_error(related_id)
            if related_error:
                related_errors.append({
                    "error_id": related_error.error_id,
                    "exception_type": related_error.exception_type,
                    "timestamp": related_error.timestamp,
                    "correlation_score": related_error.correlation_score
                })
        
        return JSONResponse({
            "error": ErrorInfo(
                error_id=error.error_id,
                timestamp=error.timestamp,
                trace_id=error.trace_id,
                correlation_id=error.correlation_id,
                exception_type=error.exception_type,
                exception_message=error.exception_message,
                function_name=error.function_name,
                module_name=error.module_name,
                file_name=error.file_name,
                line_number=error.line_number,
                category=error.category.value,
                severity=error.severity.value,
                fingerprint=str(error.fingerprint),
                correlation_score=error.correlation_score,
                related_error_count=len(error.related_error_ids)
            ).dict(),
            "stack_trace": error.stack_trace,
            "metadata": error.metadata,
            "related_errors": related_errors,
            "fingerprint_details": {
                "error_type": error.fingerprint.error_type,
                "error_message_hash": error.fingerprint.error_message_hash,
                "function_signature": error.fingerprint.function_signature,
                "stack_trace_hash": error.fingerprint.stack_trace_hash
            }
        })


@router.get("/clusters", response_model=List[ErrorClusterInfo], summary="Get error clusters")
async def get_error_clusters(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of clusters to return"),
    priority_only: bool = Query(False, description="Only return high priority clusters")
):
    """Get error clusters with pattern analysis"""
    async with TraceSpan("get_error_clusters", SpanType.REQUEST, {
        "limit": str(limit),
        "priority_only": str(priority_only)
    }):
        correlator = get_error_correlator()
        
        if priority_only:
            clusters = correlator.get_high_priority_clusters()[:limit]
        else:
            clusters = correlator.get_error_clusters(limit)
        
        cluster_infos = []
        for cluster in clusters:
            cluster_info = ErrorClusterInfo(
                cluster_id=cluster.cluster_id,
                fingerprint=str(cluster.fingerprint),
                first_seen=cluster.first_seen,
                last_seen=cluster.last_seen,
                count=cluster.count,
                error_rate=cluster.error_rate,
                trend=cluster.trend,
                affected_traces_count=len(cluster.affected_traces),
                affected_users_count=len(cluster.affected_users),
                suspected_root_causes=cluster.suspected_root_causes,
                pattern_analysis=cluster.correlation_patterns
            )
            cluster_infos.append(cluster_info)
        
        return JSONResponse([info.dict() for info in cluster_infos])


@router.get("/clusters/{cluster_id}", response_model=Dict[str, Any], summary="Get detailed cluster information")
async def get_cluster_details(cluster_id: str):
    """Get detailed information about an error cluster"""
    async with TraceSpan("get_cluster_details", SpanType.REQUEST, {"cluster_id": cluster_id}):
        correlator = get_error_correlator()
        cluster = correlator.get_cluster(cluster_id)
        
        if not cluster:
            raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
        
        # Get sample errors from cluster
        sample_errors = []
        for error in cluster.errors[:10]:  # First 10 errors as samples
            sample_errors.append({
                "error_id": error.error_id,
                "timestamp": error.timestamp,
                "exception_type": error.exception_type,
                "exception_message": error.exception_message[:200],  # Truncate long messages
                "trace_id": error.trace_id,
                "correlation_id": error.correlation_id
            })
        
        return JSONResponse({
            "cluster": ErrorClusterInfo(
                cluster_id=cluster.cluster_id,
                fingerprint=str(cluster.fingerprint),
                first_seen=cluster.first_seen,
                last_seen=cluster.last_seen,
                count=cluster.count,
                error_rate=cluster.error_rate,
                trend=cluster.trend,
                affected_traces_count=len(cluster.affected_traces),
                affected_users_count=len(cluster.affected_users),
                suspected_root_causes=cluster.suspected_root_causes,
                pattern_analysis=cluster.correlation_patterns
            ).dict(),
            "fingerprint_details": {
                "error_type": cluster.fingerprint.error_type,
                "error_message_hash": cluster.fingerprint.error_message_hash,
                "function_signature": cluster.fingerprint.function_signature,
                "stack_trace_hash": cluster.fingerprint.stack_trace_hash
            },
            "sample_errors": sample_errors,
            "affected_traces": list(cluster.affected_traces),
            "affected_users": list(cluster.affected_users)
        })


@router.post("/test-error", summary="Test error correlation (WARP TEST endpoint)")
async def test_error_correlation(
    error_type: str = Query("ValueError", description="Type of error to generate"),
    message: str = Query("WARP TEST error for correlation testing", description="Error message")
):
    """Test endpoint to generate errors for correlation testing"""
    async with TraceSpan("test_error_correlation", SpanType.REQUEST, {
        "error_type": error_type,
        "test_mode": "true"
    }):
        try:
            # Generate a test exception
            if error_type == "ValueError":
                raise ValueError(message)
            elif error_type == "RuntimeError":
                raise RuntimeError(message)
            elif error_type == "ConnectionError":
                raise ConnectionError(message)
            else:
                raise Exception(f"{error_type}: {message}")
                
        except Exception as e:
            # Record the error for correlation
            error_id = await correlate_error(e, {
                "test_mode": True,
                "user_id": "WARP_TEST_USER",
                "request_source": "api_test"
            })
            
            return JSONResponse({
                "message": "WARP TEST error generated and recorded for correlation",
                "error_id": error_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "trace_id": get_current_trace_id(),
                "correlation_id": get_current_correlation_id()
            })


@router.get("/analysis/timeline", summary="Get error timeline analysis")
async def get_error_timeline(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to analyze"),
    granularity: str = Query("hour", description="Time granularity (hour, minute)")
):
    """Get timeline analysis of errors and traces"""
    async with TraceSpan("get_error_timeline", SpanType.REQUEST, {
        "hours": str(hours),
        "granularity": granularity
    }):
        correlator = get_error_correlator()
        tracer = get_request_tracer()
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Get recent errors and traces
        recent_errors = correlator.get_recent_errors(1000)  # Large sample
        recent_traces = tracer.get_recent_traces(1000)
        
        # Filter by time range
        start_timestamp = start_time.timestamp()
        end_timestamp = end_time.timestamp()
        
        filtered_errors = [e for e in recent_errors if start_timestamp <= e.timestamp <= end_timestamp]
        filtered_traces = [t for t in recent_traces if start_timestamp <= t.start_time <= end_timestamp]
        
        # Group by time buckets
        bucket_size = 3600 if granularity == "hour" else 60  # seconds
        timeline = {}
        
        current = start_timestamp
        while current < end_timestamp:
            bucket_key = datetime.fromtimestamp(current).isoformat()
            bucket_end = current + bucket_size
            
            bucket_errors = [e for e in filtered_errors if current <= e.timestamp < bucket_end]
            bucket_traces = [t for t in filtered_traces if current <= t.start_time < bucket_end]
            
            timeline[bucket_key] = {
                "timestamp": current,
                "error_count": len(bucket_errors),
                "trace_count": len(bucket_traces),
                "error_rate": len(bucket_errors) / (bucket_size / 60),  # per minute
                "categories": {},
                "severities": {}
            }
            
            # Count by category and severity
            for error in bucket_errors:
                cat = error.category.value
                sev = error.severity.value
                timeline[bucket_key]["categories"][cat] = timeline[bucket_key]["categories"].get(cat, 0) + 1
                timeline[bucket_key]["severities"][sev] = timeline[bucket_key]["severities"].get(sev, 0) + 1
            
            current += bucket_size
        
        return JSONResponse({
            "analysis_period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "hours": hours,
                "granularity": granularity
            },
            "timeline": timeline,
            "summary": {
                "total_errors": len(filtered_errors),
                "total_traces": len(filtered_traces),
                "avg_error_rate": len(filtered_errors) / (hours * 60) if hours > 0 else 0,
                "peak_error_rate": max((bucket["error_rate"] for bucket in timeline.values()), default=0)
            }
        })


@router.get("/analysis/correlations", summary="Get correlation analysis")
async def get_correlation_analysis():
    """Get detailed correlation analysis and insights"""
    async with TraceSpan("get_correlation_analysis", SpanType.REQUEST):
        correlator = get_error_correlator()
        
        # Get high priority clusters for analysis
        priority_clusters = correlator.get_high_priority_clusters()
        
        insights = []
        for cluster in priority_clusters[:10]:  # Top 10 priority clusters
            cluster_insight = {
                "cluster_id": cluster.cluster_id,
                "priority_score": (cluster.error_rate * 10) + (cluster.count * 2),
                "error_count": cluster.count,
                "error_rate": cluster.error_rate,
                "trend": cluster.trend,
                "affected_systems": {
                    "traces": len(cluster.affected_traces),
                    "users": len(cluster.affected_users)
                },
                "root_causes": cluster.suspected_root_causes,
                "patterns": cluster.correlation_patterns,
                "recommendations": []
            }
            
            # Generate recommendations
            if cluster.error_rate > 2.0:
                cluster_insight["recommendations"].append("URGENT: High error rate detected - investigate immediately")
            
            if cluster.trend == "increasing":
                cluster_insight["recommendations"].append("Error trend is increasing - monitor closely")
            
            if "cascade" in cluster.correlation_patterns and cluster.correlation_patterns["cascade"].get("is_cascade"):
                cluster_insight["recommendations"].append("Error cascade detected - focus on root cause errors")
            
            if len(cluster.affected_users) > 10:
                cluster_insight["recommendations"].append("Multiple users affected - consider user notification")
            
            insights.append(cluster_insight)
        
        return JSONResponse({
            "correlation_analysis": {
                "high_priority_clusters": len(priority_clusters),
                "total_insights": len(insights),
                "analysis_timestamp": datetime.now().isoformat()
            },
            "insights": insights,
            "system_health": {
                "overall_error_rate": sum(c.error_rate for c in priority_clusters[:5]) / max(len(priority_clusters[:5]), 1),
                "trending_issues": len([c for c in priority_clusters if c.trend in ["increasing", "spike"]]),
                "cascade_issues": len([c for c in priority_clusters if c.correlation_patterns.get("cascade", {}).get("is_cascade")])
            }
        })


# Add router to main application
def setup_tracing_routes(app):
    """Setup tracing routes on FastAPI app"""
    app.include_router(router)
    logger.info("WARPCORE distributed tracing API routes configured")