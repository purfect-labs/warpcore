#!/usr/bin/env python3
"""
WARPCORE Distributed Tracing System Tests
Tests for request tracing, error correlation, and system integration
"""

import asyncio
import pytest
import time
from datetime import datetime
from unittest.mock import Mock, patch

from src.api.middleware.tracing.request_tracer import (
    RequestTracer,
    TraceSpan,
    SpanType,
    get_request_tracer,
    trace_operation,
    get_current_trace_id,
    get_current_correlation_id,
    correlate_error_with_trace
)
from src.api.middleware.tracing.error_correlator import (
    ErrorCorrelator,
    ErrorSeverity,
    ErrorCategory,
    get_error_correlator,
    correlate_error
)


class TestDistributedTracing:
    """WARP TEST: Test distributed tracing functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        # Create fresh instances for each test
        self.tracer = RequestTracer()
        self.correlator = ErrorCorrelator()
    
    @pytest.mark.asyncio
    async def test_trace_creation_and_management(self):
        """Test basic trace creation and lifecycle"""
        # Start a new trace
        trace_id = await self.tracer.start_trace()
        
        assert trace_id is not None
        assert trace_id in self.tracer.active_traces
        
        trace = self.tracer.get_trace(trace_id)
        assert trace is not None
        assert trace.trace_id == trace_id
        assert trace.status == "in_progress"
        
        # Finish the trace
        await self.tracer.finish_trace(trace_id)
        
        assert trace_id not in self.tracer.active_traces
        assert trace in self.tracer.completed_traces
        assert trace.status in ["completed", "error"]
    
    @pytest.mark.asyncio
    async def test_span_creation_and_nesting(self):
        """Test span creation and parent-child relationships"""
        # Start trace
        trace_id = await self.tracer.start_trace("WARP_TEST_CORRELATION_001")
        
        # Create root span
        async with TraceSpan("root_operation", SpanType.REQUEST) as root_span:
            assert root_span.span_context is not None
            root_span_id = root_span.span_context.span_id
            
            # Create nested span
            async with TraceSpan("nested_operation", SpanType.DATABASE) as nested_span:
                assert nested_span.span_context is not None
                assert nested_span.span_context.parent_span_id == root_span_id
                
                # Add metadata to spans
                root_span.add_tag("service", "WARP_TEST_SERVICE")
                nested_span.add_tag("query", "SELECT * FROM warp_test_table")
                nested_span.add_baggage("test_mode", True)
        
        # Verify trace structure
        trace = self.tracer.get_trace(trace_id)
        assert len(trace.spans) == 2
        
        # Check span relationships
        spans = list(trace.spans.values())
        root_spans = [s for s in spans if s.parent_span_id is None]
        child_spans = [s for s in spans if s.parent_span_id is not None]
        
        assert len(root_spans) == 1
        assert len(child_spans) == 1
        assert child_spans[0].parent_span_id == root_spans[0].span_id
        
        await self.tracer.finish_trace(trace_id)
    
    @pytest.mark.asyncio
    async def test_trace_decorator(self):
        """Test automatic tracing with decorator"""
        # Start trace context
        trace_id = await self.tracer.start_trace()
        
        @trace_operation("test_operation", SpanType.COMPUTATION)
        async def test_function(value: int):
            """WARP TEST function for tracing"""
            await asyncio.sleep(0.01)  # Simulate work
            return value * 2
        
        # Execute traced function
        result = await test_function(21)
        assert result == 42
        
        # Verify span was created
        trace = self.tracer.get_trace(trace_id)
        assert len(trace.spans) > 0
        
        operation_spans = [s for s in trace.spans.values() if s.operation_name == "test_operation"]
        assert len(operation_spans) == 1
        
        span = operation_spans[0]
        assert span.span_type == SpanType.COMPUTATION
        assert span.status == "success"
        assert span.duration is not None
        assert span.duration > 0
        
        await self.tracer.finish_trace(trace_id)
    
    @pytest.mark.asyncio
    async def test_error_correlation_basic(self):
        """Test basic error correlation functionality"""
        # Record some test errors
        try:
            raise ValueError("WARP TEST validation error")
        except Exception as e:
            error_id_1 = await self.correlator.record_error(e, {"test_mode": True})
        
        try:
            raise ValueError("WARP TEST validation error")  # Same message
        except Exception as e:
            error_id_2 = await self.correlator.record_error(e, {"test_mode": True})
        
        # Verify errors were recorded
        error_1 = self.correlator.get_error(error_id_1)
        error_2 = self.correlator.get_error(error_id_2)
        
        assert error_1 is not None
        assert error_2 is not None
        assert error_1.category == ErrorCategory.VALIDATION
        assert error_2.category == ErrorCategory.VALIDATION
        
        # Verify correlation
        assert len(error_1.related_error_ids) > 0 or len(error_2.related_error_ids) > 0
        
        # Check clustering
        clusters = self.correlator.get_error_clusters()
        assert len(clusters) > 0
        
        # Find cluster containing our errors
        test_cluster = None
        for cluster in clusters:
            cluster_error_ids = [e.error_id for e in cluster.errors]
            if error_id_1 in cluster_error_ids or error_id_2 in cluster_error_ids:
                test_cluster = cluster
                break
        
        assert test_cluster is not None
        assert test_cluster.count >= 2
    
    @pytest.mark.asyncio
    async def test_error_correlation_with_tracing(self):
        """Test error correlation integrated with request tracing"""
        # Start trace
        trace_id = await self.tracer.start_trace("WARP_TEST_ERROR_CORRELATION")
        
        async with TraceSpan("error_test_operation", SpanType.REQUEST) as span:
            try:
                # Simulate an error in traced context
                raise RuntimeError("WARP TEST runtime error in traced context")
            except Exception as e:
                # Record error with correlation
                error_id = await self.correlator.record_error(e, {
                    "test_mode": True,
                    "operation": "error_test_operation"
                })
                
                # Check error has trace context
                error = self.correlator.get_error(error_id)
                assert error.trace_id == trace_id
                assert error.correlation_id == get_current_correlation_id()
        
        await self.tracer.finish_trace(trace_id)
        
        # Verify trace has error information
        trace = self.tracer.get_trace(trace_id)
        assert trace.error_count > 0
        
        # Find error span
        error_spans = [s for s in trace.spans.values() if s.status == "error"]
        assert len(error_spans) > 0
        
        error_span = error_spans[0]
        assert error_span.error_info is not None
        assert "RuntimeError" in error_span.error_info.get("exception_type", "")
    
    @pytest.mark.asyncio
    async def test_error_pattern_detection(self):
        """Test error pattern detection and analysis"""
        # Create a burst pattern of errors
        errors = []
        for i in range(5):
            try:
                raise ConnectionError(f"WARP TEST network error {i}")
            except Exception as e:
                error_id = await self.correlator.record_error(e, {
                    "test_mode": True,
                    "burst_test": True
                })
                errors.append(error_id)
            
            # Small delay to create temporal pattern
            await asyncio.sleep(0.001)
        
        # Wait for pattern analysis
        await asyncio.sleep(0.1)
        
        # Check if cluster was created with pattern analysis
        clusters = self.correlator.get_error_clusters()
        network_clusters = [c for c in clusters if any(
            e.category == ErrorCategory.NETWORK for e in c.errors
        )]
        
        assert len(network_clusters) > 0
        
        test_cluster = network_clusters[0]
        if len(test_cluster.errors) >= 3:  # Pattern analysis triggers with 3+ errors
            assert "temporal" in test_cluster.correlation_patterns
            temporal_pattern = test_cluster.correlation_patterns["temporal"]
            
            # Should detect burst or spike pattern
            assert temporal_pattern.get("pattern") in ["burst", "spike", "scattered"]
    
    @pytest.mark.asyncio  
    async def test_high_priority_cluster_detection(self):
        """Test high priority error cluster detection"""
        # Create critical errors
        for i in range(3):
            try:
                raise Exception("WARP TEST critical system failure")
            except Exception as e:
                await self.correlator.record_error(e, {
                    "test_mode": True,
                    "severity_test": "critical"
                })
        
        # Get high priority clusters
        high_priority = self.correlator.get_high_priority_clusters()
        
        # Should have at least one high priority cluster
        assert len(high_priority) > 0
        
        # Check if our critical errors cluster is in high priority
        critical_cluster = None
        for cluster in high_priority:
            if any("critical system failure" in e.exception_message for e in cluster.errors):
                critical_cluster = cluster
                break
        
        assert critical_cluster is not None
        assert critical_cluster.count >= 3
    
    @pytest.mark.asyncio
    async def test_correlation_statistics(self):
        """Test correlation statistics calculation"""
        # Generate some test data
        trace_id = await self.tracer.start_trace()
        
        # Create various types of errors
        error_types = [
            (ValueError, "WARP TEST validation", ErrorCategory.VALIDATION),
            (ConnectionError, "WARP TEST network", ErrorCategory.NETWORK),
            (RuntimeError, "WARP TEST runtime", ErrorCategory.UNKNOWN)
        ]
        
        for error_class, message, expected_category in error_types:
            try:
                raise error_class(f"{message} error")
            except Exception as e:
                await self.correlator.record_error(e, {"test_mode": True})
        
        await self.tracer.finish_trace(trace_id)
        
        # Get statistics
        tracer_stats = self.tracer.get_statistics()
        correlator_stats = self.correlator.get_correlation_statistics()
        
        # Verify tracer statistics
        assert tracer_stats["total_traces"] >= 1
        assert tracer_stats["total_spans"] >= 0
        assert tracer_stats["completed_traces"] >= 1
        
        # Verify correlator statistics
        assert correlator_stats["total_errors"] >= 3
        assert correlator_stats["total_clusters"] >= 1
        assert len(correlator_stats["category_distribution"]) > 0
        assert len(correlator_stats["severity_distribution"]) > 0
    
    @pytest.mark.asyncio
    async def test_trace_sampling(self):
        """Test trace sampling functionality"""
        # Set sampling rate to 50%
        self.tracer.sample_rate = 0.5
        
        # Start multiple traces
        trace_ids = []
        for i in range(20):
            trace_id = await self.tracer.start_trace()
            if trace_id:  # Only non-None if sampled
                trace_ids.append(trace_id)
                await self.tracer.finish_trace(trace_id)
        
        # Should have sampled roughly half (allow for variance)
        assert 5 <= len(trace_ids) <= 15  # Rough sampling check
        
        # Reset sampling
        self.tracer.sample_rate = 1.0
    
    @pytest.mark.asyncio
    async def test_trace_cleanup(self):
        """Test automatic cleanup of old traces"""
        # Create a trace and artificially age it
        trace_id = await self.tracer.start_trace()
        trace = self.tracer.active_traces[trace_id]
        
        # Make trace appear old
        trace.start_time = time.time() - 400  # Older than max_trace_duration
        
        # Trigger cleanup
        await self.tracer.cleanup_old_traces()
        
        # Trace should be moved to completed
        assert trace_id not in self.tracer.active_traces
        assert trace in self.tracer.completed_traces
        assert trace.status == "abandoned"
    
    @pytest.mark.asyncio
    async def test_error_fingerprinting(self):
        """Test error fingerprinting for correlation"""
        # Create similar errors that should have same fingerprint
        errors = []
        for i in range(3):
            try:
                # Same error type and similar message (with dynamic content)
                raise ValueError(f"WARP TEST invalid value: {i} at timestamp {time.time()}")
            except Exception as e:
                error_id = await self.correlator.record_error(e, {"test_mode": True})
                errors.append(self.correlator.get_error(error_id))
        
        # Check fingerprints are similar/same (normalized message should match)
        fingerprints = [str(e.fingerprint) for e in errors]
        
        # At least some should have same fingerprint due to normalization
        fingerprint_counts = {}
        for fp in fingerprints:
            fingerprint_counts[fp] = fingerprint_counts.get(fp, 0) + 1
        
        # Should have correlation due to similar error patterns
        max_count = max(fingerprint_counts.values())
        assert max_count >= 2  # At least 2 errors should correlate
    
    def test_context_variables(self):
        """Test context variable functionality"""
        # Test that context variables work correctly
        from src.api.middleware.tracing.request_tracer import (
            correlation_id_var,
            trace_id_var,
            span_stack_var
        )
        
        # Initially should be None/empty
        assert correlation_id_var.get() is None
        assert trace_id_var.get() is None
        assert span_stack_var.get() == []
        
        # Set values
        correlation_id_var.set("WARP_TEST_CORRELATION")
        trace_id_var.set("WARP_TEST_TRACE")
        span_stack_var.set(["span1", "span2"])
        
        # Verify values
        assert correlation_id_var.get() == "WARP_TEST_CORRELATION"
        assert trace_id_var.get() == "WARP_TEST_TRACE"
        assert span_stack_var.get() == ["span1", "span2"]
        
        # Test helper functions
        assert get_current_correlation_id() == "WARP_TEST_CORRELATION"
        assert get_current_trace_id() == "WARP_TEST_TRACE"
    
    @pytest.mark.asyncio
    async def test_middleware_integration(self):
        """Test middleware integration (mock FastAPI request)"""
        from fastapi import Request
        from starlette.responses import JSONResponse
        from src.api.middleware.tracing.request_tracer import tracing_middleware
        
        # Mock request and response
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.url = Mock()
        mock_request.url.__str__ = lambda: "http://localhost/api/test"
        mock_request.url.path = "/api/test"
        mock_request.query_params = {}
        mock_request.headers = {"x-correlation-id": "WARP_TEST_MIDDLEWARE"}
        mock_request.route = {"path": "/api/test"}
        
        async def mock_call_next(request):
            response = JSONResponse({"message": "WARP TEST response"})
            response.status_code = 200
            return response
        
        # Process through middleware
        response = await tracing_middleware(mock_request, mock_call_next)
        
        # Verify correlation headers in response
        assert "x-correlation-id" in response.headers
        assert response.headers["x-correlation-id"] == "WARP_TEST_MIDDLEWARE"
        
        # Verify trace was created
        tracer = get_request_tracer()
        recent_traces = tracer.get_recent_traces(1)
        
        if recent_traces:
            trace = recent_traces[0]
            assert trace.correlation_id == "WARP_TEST_MIDDLEWARE"
            assert len(trace.spans) >= 1
            
            # Should have HTTP request span
            request_spans = [s for s in trace.spans.values() if s.span_type == SpanType.REQUEST]
            assert len(request_spans) >= 1


@pytest.mark.integration
class TestDistributedTracingIntegration:
    """Integration tests for distributed tracing system"""
    
    @pytest.mark.asyncio
    async def test_full_system_integration(self):
        """Test complete system integration"""
        tracer = get_request_tracer()
        correlator = get_error_correlator()
        
        # Start trace
        trace_id = await tracer.start_trace("WARP_INTEGRATION_TEST")
        
        # Simulate complex operation with multiple spans and errors
        async with TraceSpan("main_operation", SpanType.REQUEST) as main_span:
            main_span.add_tag("integration_test", "true")
            
            # Database operation
            async with TraceSpan("database_query", SpanType.DATABASE) as db_span:
                db_span.add_tag("query", "SELECT * FROM warp_integration_test")
                await asyncio.sleep(0.01)  # Simulate DB time
            
            # External API call with error
            async with TraceSpan("external_api_call", SpanType.EXTERNAL_API) as api_span:
                try:
                    raise ConnectionError("WARP TEST external service unavailable")
                except Exception as e:
                    await correlate_error(e, {
                        "integration_test": True,
                        "service": "external_test_api"
                    })
                    api_span.add_tag("error", "true")
            
            # Business logic processing
            async with TraceSpan("business_logic", SpanType.COMPUTATION) as logic_span:
                logic_span.add_baggage("processed_records", 42)
                await asyncio.sleep(0.005)  # Simulate processing
        
        await tracer.finish_trace(trace_id)
        
        # Verify complete trace
        trace = tracer.get_trace(trace_id)
        assert trace is not None
        assert len(trace.spans) == 4  # main + db + api + logic
        assert trace.error_count > 0
        
        # Verify error correlation
        recent_errors = correlator.get_recent_errors(10)
        integration_errors = [e for e in recent_errors if e.metadata.get("integration_test")]
        assert len(integration_errors) > 0
        
        integration_error = integration_errors[0]
        assert integration_error.trace_id == trace_id
        assert integration_error.category == ErrorCategory.NETWORK
        
        # Verify statistics
        stats = tracer.get_statistics()
        assert stats["total_traces"] >= 1
        assert stats["total_spans"] >= 4