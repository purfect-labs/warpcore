#!/usr/bin/env python3
"""
WARPCORE Error Correlation System
Analyzes error patterns, correlates related errors, and provides root cause analysis
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Set, Tuple
import hashlib
import re

from .request_tracer import get_current_correlation_id, get_current_trace_id, get_request_tracer


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for correlation"""
    NETWORK = "network"
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_API = "external_api"
    RESOURCE = "resource"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class ErrorFingerprint:
    """Unique fingerprint for error correlation"""
    error_type: str
    error_message_hash: str  # Hash of normalized error message
    function_signature: str  # Where the error occurred
    stack_trace_hash: str   # Hash of key stack trace elements
    
    def __post_init__(self):
        """Generate composite fingerprint"""
        components = [
            self.error_type,
            self.error_message_hash,
            self.function_signature,
            self.stack_trace_hash
        ]
        self.fingerprint = hashlib.sha256("|".join(components).encode()).hexdigest()[:16]
    
    def __str__(self):
        return self.fingerprint


@dataclass
class CorrelatedError:
    """A correlated error with context"""
    error_id: str
    timestamp: float
    trace_id: Optional[str]
    correlation_id: Optional[str]
    
    # Error details
    exception_type: str
    exception_message: str
    stack_trace: List[str]
    function_name: str
    module_name: str
    file_name: str
    line_number: int
    
    # Classification
    category: ErrorCategory
    severity: ErrorSeverity
    fingerprint: ErrorFingerprint
    
    # Context
    request_path: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Correlation info
    related_error_ids: Set[str] = field(default_factory=set)
    correlation_score: float = 0.0
    is_root_cause: bool = False
    chain_position: int = 0  # Position in error chain (0 = root, higher = downstream)


@dataclass
class ErrorCluster:
    """Cluster of related errors"""
    cluster_id: str
    fingerprint: ErrorFingerprint
    first_seen: float
    last_seen: float
    count: int = 0
    errors: List[CorrelatedError] = field(default_factory=list)
    
    # Analysis
    affected_traces: Set[str] = field(default_factory=set)
    affected_users: Set[str] = field(default_factory=set)
    error_rate: float = 0.0  # Errors per minute
    trend: str = "stable"  # increasing, decreasing, stable, spike
    
    # Root cause analysis
    suspected_root_causes: List[str] = field(default_factory=list)
    correlation_patterns: Dict[str, int] = field(default_factory=dict)


class ErrorPatternDetector:
    """Detects patterns in error occurrences"""
    
    def __init__(self):
        self.temporal_patterns = {
            'burst': [],      # Multiple errors in short time
            'periodic': [],   # Recurring at intervals  
            'cascade': [],    # Error chains/cascades
            'spike': []       # Sudden increase
        }
    
    def analyze_temporal_pattern(self, errors: List[CorrelatedError], 
                               window_minutes: int = 5) -> Dict[str, Any]:
        """Analyze temporal patterns in errors"""
        if len(errors) < 2:
            return {"pattern": "isolated", "confidence": 1.0}
        
        # Sort by timestamp
        sorted_errors = sorted(errors, key=lambda e: e.timestamp)
        timestamps = [e.timestamp for e in sorted_errors]
        
        # Calculate intervals between errors
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
        
        # Detect burst pattern (multiple errors in short time)
        burst_threshold = 30  # 30 seconds
        burst_count = sum(1 for interval in intervals if interval < burst_threshold)
        burst_ratio = burst_count / len(intervals) if intervals else 0
        
        # Detect periodic pattern
        if len(intervals) >= 3:
            interval_variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
            interval_std = interval_variance ** 0.5
            periodic_score = 1.0 - (interval_std / max(avg_interval, 1)) if avg_interval > 0 else 0
        else:
            periodic_score = 0
        
        # Determine dominant pattern
        if burst_ratio > 0.6:
            return {
                "pattern": "burst",
                "confidence": burst_ratio,
                "avg_interval": avg_interval,
                "details": f"{burst_count}/{len(intervals)} intervals < {burst_threshold}s"
            }
        elif periodic_score > 0.7:
            return {
                "pattern": "periodic", 
                "confidence": periodic_score,
                "avg_interval": avg_interval,
                "details": f"Regular intervals ~{avg_interval:.1f}s"
            }
        elif len(errors) > 1 and (timestamps[-1] - timestamps[0]) < window_minutes * 60:
            return {
                "pattern": "spike",
                "confidence": 0.8,
                "duration": timestamps[-1] - timestamps[0],
                "details": f"{len(errors)} errors in {(timestamps[-1] - timestamps[0]):.1f}s"
            }
        else:
            return {
                "pattern": "scattered",
                "confidence": 0.6,
                "avg_interval": avg_interval,
                "details": "Irregular timing pattern"
            }
    
    def detect_cascade_pattern(self, errors: List[CorrelatedError]) -> Dict[str, Any]:
        """Detect error cascade patterns (one error causing others)"""
        if len(errors) < 2:
            return {"is_cascade": False}
        
        # Group errors by trace/correlation ID
        trace_groups = defaultdict(list)
        for error in errors:
            if error.correlation_id:
                trace_groups[error.correlation_id].append(error)
        
        cascade_evidence = []
        
        for correlation_id, group_errors in trace_groups.items():
            if len(group_errors) < 2:
                continue
            
            # Sort by timestamp within trace
            group_errors.sort(key=lambda e: e.timestamp)
            
            # Look for error chains (sequential errors in same trace)
            for i in range(len(group_errors) - 1):
                current = group_errors[i]
                next_error = group_errors[i + 1]
                
                time_diff = next_error.timestamp - current.timestamp
                
                # If errors are close in time and in same trace, likely cascaded
                if 0 < time_diff < 10:  # Within 10 seconds
                    cascade_evidence.append({
                        'correlation_id': correlation_id,
                        'root_error': current.error_id,
                        'caused_error': next_error.error_id,
                        'time_diff': time_diff,
                        'root_type': current.exception_type,
                        'caused_type': next_error.exception_type
                    })
        
        is_cascade = len(cascade_evidence) > 0
        confidence = min(len(cascade_evidence) / len(errors), 1.0) if is_cascade else 0.0
        
        return {
            "is_cascade": is_cascade,
            "confidence": confidence,
            "cascade_chains": cascade_evidence,
            "affected_traces": len(trace_groups),
            "details": f"{len(cascade_evidence)} cascade relationships detected"
        }


class ErrorCorrelator:
    """Main error correlation engine"""
    
    def __init__(self):
        self.logger = logging.getLogger("error_correlator")
        
        # Storage
        self.errors: Dict[str, CorrelatedError] = {}
        self.clusters: Dict[str, ErrorCluster] = {}
        self.recent_errors = deque(maxlen=1000)  # Keep recent errors for pattern analysis
        
        # Pattern detection
        self.pattern_detector = ErrorPatternDetector()
        
        # Configuration
        self.correlation_threshold = 0.7
        self.max_cluster_size = 100
        self.cleanup_interval = 3600  # 1 hour
        self.retention_hours = 24
        
        # Statistics
        self.total_errors = 0
        self.total_clusters = 0
        self.correlation_hits = 0
        
        # Cleanup task (will be started when first needed)
        self._cleanup_task_started = False
    
    def _normalize_error_message(self, message: str) -> str:
        """Normalize error message for fingerprinting"""
        # Remove dynamic content like IDs, timestamps, numbers
        normalized = re.sub(r'\d+', 'N', message)
        normalized = re.sub(r'[a-f0-9-]{8,}', 'UUID', normalized)  # UUIDs/hashes
        normalized = re.sub(r'\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', 'TIMESTAMP', normalized)
        normalized = re.sub(r'0x[0-9a-f]+', 'ADDR', normalized)  # Memory addresses
        normalized = normalized.strip().lower()
        return normalized
    
    def _extract_stack_trace_signature(self, stack_trace: List[str]) -> str:
        """Extract signature from stack trace for fingerprinting"""
        if not stack_trace:
            return ""
        
        # Take key frames (filter out common/framework code)
        key_frames = []
        for frame in stack_trace:
            # Skip common framework paths
            if any(skip in frame.lower() for skip in ['site-packages', 'asyncio', 'uvicorn']):
                continue
            key_frames.append(frame)
        
        # Take up to 5 most relevant frames
        signature_frames = key_frames[:5] if key_frames else stack_trace[:3]
        
        # Extract function names and file info
        signature_parts = []
        for frame in signature_frames:
            # Extract file:line and function info
            if 'in ' in frame and ', line ' in frame:
                parts = frame.split(', line ')
                if len(parts) >= 2:
                    file_part = parts[0].split('/')[-1] if '/' in parts[0] else parts[0]
                    signature_parts.append(f"{file_part}:{parts[1].split()[0]}")
        
        return " -> ".join(signature_parts)
    
    def _create_fingerprint(self, error: CorrelatedError) -> ErrorFingerprint:
        """Create error fingerprint for correlation"""
        # Normalize error message
        normalized_message = self._normalize_error_message(error.exception_message)
        message_hash = hashlib.md5(normalized_message.encode()).hexdigest()[:8]
        
        # Create function signature
        function_sig = f"{error.module_name}.{error.function_name}"
        
        # Create stack trace hash
        stack_sig = self._extract_stack_trace_signature(error.stack_trace)
        stack_hash = hashlib.md5(stack_sig.encode()).hexdigest()[:8]
        
        return ErrorFingerprint(
            error_type=error.exception_type,
            error_message_hash=message_hash,
            function_signature=function_sig,
            stack_trace_hash=stack_hash
        )
    
    def _classify_error_category(self, error: CorrelatedError) -> ErrorCategory:
        """Classify error into category"""
        error_type = error.exception_type.lower()
        message = error.exception_message.lower()
        
        # Network-related errors
        if any(keyword in error_type for keyword in ['connection', 'timeout', 'network']):
            return ErrorCategory.NETWORK
        if any(keyword in message for keyword in ['connection', 'timeout', 'unreachable']):
            return ErrorCategory.NETWORK
        
        # Database errors
        if any(keyword in error_type for keyword in ['sql', 'database', 'db']):
            return ErrorCategory.DATABASE
        if any(keyword in message for keyword in ['database', 'sql', 'query', 'table']):
            return ErrorCategory.DATABASE
        
        # Authentication/Authorization
        if any(keyword in error_type for keyword in ['auth', 'permission', 'unauthorized']):
            return ErrorCategory.AUTHENTICATION
        if any(keyword in message for keyword in ['unauthorized', 'forbidden', 'auth', 'login']):
            return ErrorCategory.AUTHENTICATION
        
        # Validation errors
        if any(keyword in error_type for keyword in ['validation', 'value', 'format']):
            return ErrorCategory.VALIDATION
        if any(keyword in message for keyword in ['invalid', 'validation', 'format', 'required']):
            return ErrorCategory.VALIDATION
        
        # Resource errors
        if any(keyword in error_type for keyword in ['memory', 'resource', 'limit']):
            return ErrorCategory.RESOURCE
        if any(keyword in message for keyword in ['memory', 'disk', 'quota', 'limit']):
            return ErrorCategory.RESOURCE
        
        # External API errors
        if any(keyword in message for keyword in ['api', 'external', 'service', 'endpoint']):
            return ErrorCategory.EXTERNAL_API
        
        # Configuration errors
        if any(keyword in message for keyword in ['config', 'setting', 'parameter']):
            return ErrorCategory.CONFIGURATION
        
        # Default to business logic or unknown
        if 'business' in message or 'logic' in message:
            return ErrorCategory.BUSINESS_LOGIC
        
        return ErrorCategory.UNKNOWN
    
    def _determine_error_severity(self, error: CorrelatedError) -> ErrorSeverity:
        """Determine error severity"""
        error_type = error.exception_type.lower()
        message = error.exception_message.lower()
        
        # Critical errors
        critical_keywords = ['fatal', 'critical', 'system', 'crash', 'corruption']
        if any(keyword in error_type or keyword in message for keyword in critical_keywords):
            return ErrorSeverity.CRITICAL
        
        # High severity
        high_keywords = ['security', 'auth', 'database', 'data', 'payment']
        if any(keyword in error_type or keyword in message for keyword in high_keywords):
            return ErrorSeverity.HIGH
        
        # Medium severity  
        medium_keywords = ['validation', 'api', 'network', 'timeout']
        if any(keyword in error_type or keyword in message for keyword in medium_keywords):
            return ErrorSeverity.MEDIUM
        
        # Default to low
        return ErrorSeverity.LOW
    
    def _calculate_correlation_score(self, error1: CorrelatedError, 
                                   error2: CorrelatedError) -> float:
        """Calculate correlation score between two errors"""
        score = 0.0
        
        # Same fingerprint = high correlation
        if error1.fingerprint.fingerprint == error2.fingerprint.fingerprint:
            score += 0.8
        
        # Same error type
        if error1.exception_type == error2.exception_type:
            score += 0.3
        
        # Similar error messages
        msg1_norm = self._normalize_error_message(error1.exception_message)
        msg2_norm = self._normalize_error_message(error2.exception_message)
        if msg1_norm == msg2_norm:
            score += 0.4
        elif len(set(msg1_norm.split()) & set(msg2_norm.split())) > 0:
            score += 0.2
        
        # Same module/function
        if error1.module_name == error2.module_name:
            score += 0.2
            if error1.function_name == error2.function_name:
                score += 0.3
        
        # Same trace/correlation ID
        if error1.correlation_id and error1.correlation_id == error2.correlation_id:
            score += 0.4
        
        # Time proximity (within 1 minute)
        time_diff = abs(error1.timestamp - error2.timestamp)
        if time_diff < 60:
            time_score = max(0, 1.0 - (time_diff / 60)) * 0.3
            score += time_score
        
        return min(score, 1.0)
    
    def _ensure_cleanup_task_started(self):
        """Ensure cleanup task is started when correlator is first used"""
        if not self._cleanup_task_started:
            try:
                asyncio.create_task(self._cleanup_task())
                self._cleanup_task_started = True
            except RuntimeError:
                # No event loop running yet, will be started later
                pass
    
    async def record_error(self, exception: Exception, context: Dict[str, Any] = None) -> str:
        """Record an error for correlation analysis"""
        self._ensure_cleanup_task_started()
        
        import uuid
        import traceback
        import inspect
        
        # Generate error ID
        error_id = str(uuid.uuid4())
        
        # Extract context information
        frame = inspect.currentframe()
        caller_frame = frame.f_back if frame else None
        
        function_name = "unknown"
        module_name = "unknown" 
        file_name = "unknown"
        line_number = 0
        
        if caller_frame:
            function_name = caller_frame.f_code.co_name
            file_name = caller_frame.f_code.co_filename.split('/')[-1]
            line_number = caller_frame.f_lineno
            
            # Try to get module name
            if '__name__' in caller_frame.f_globals:
                module_name = caller_frame.f_globals['__name__']
        
        # Get stack trace
        stack_trace = traceback.format_exception(type(exception), exception, exception.__traceback__)
        
        # Create correlated error
        error = CorrelatedError(
            error_id=error_id,
            timestamp=time.time(),
            trace_id=get_current_trace_id(),
            correlation_id=get_current_correlation_id(),
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            stack_trace=stack_trace,
            function_name=function_name,
            module_name=module_name,
            file_name=file_name,
            line_number=line_number,
            category=ErrorCategory.UNKNOWN,  # Will be classified
            severity=ErrorSeverity.LOW,      # Will be determined
            fingerprint=None,                # Will be created
            metadata=context or {}
        )
        
        # Classify and fingerprint
        error.category = self._classify_error_category(error)
        error.severity = self._determine_error_severity(error)
        error.fingerprint = self._create_fingerprint(error)
        
        # Store error
        self.errors[error_id] = error
        self.recent_errors.append(error)
        self.total_errors += 1
        
        # Find correlations
        await self._correlate_error(error)
        
        self.logger.info(
            f"Recorded error {error_id}: {error.exception_type} "
            f"(category: {error.category.value}, severity: {error.severity.value})"
        )
        
        return error_id
    
    async def _correlate_error(self, new_error: CorrelatedError):
        """Correlate new error with existing errors"""
        correlations_found = []
        
        # Check recent errors for correlations
        for existing_error in list(self.recent_errors):
            if existing_error.error_id == new_error.error_id:
                continue
                
            score = self._calculate_correlation_score(new_error, existing_error)
            
            if score >= self.correlation_threshold:
                correlations_found.append((existing_error, score))
                
                # Add mutual references
                new_error.related_error_ids.add(existing_error.error_id)
                existing_error.related_error_ids.add(new_error.error_id)
                
                new_error.correlation_score = max(new_error.correlation_score, score)
                existing_error.correlation_score = max(existing_error.correlation_score, score)
        
        if correlations_found:
            self.correlation_hits += 1
            self.logger.debug(
                f"Error {new_error.error_id} correlated with {len(correlations_found)} errors"
            )
        
        # Add to or create cluster
        await self._update_clusters(new_error, correlations_found)
    
    async def _update_clusters(self, error: CorrelatedError, 
                             correlations: List[Tuple[CorrelatedError, float]]):
        """Update error clusters with new error"""
        fingerprint_key = str(error.fingerprint)
        
        # Find existing cluster with same fingerprint
        target_cluster = None
        for cluster in self.clusters.values():
            if str(cluster.fingerprint) == fingerprint_key:
                target_cluster = cluster
                break
        
        if target_cluster is None:
            # Create new cluster
            cluster_id = f"cluster_{len(self.clusters) + 1}"
            target_cluster = ErrorCluster(
                cluster_id=cluster_id,
                fingerprint=error.fingerprint,
                first_seen=error.timestamp,
                last_seen=error.timestamp
            )
            self.clusters[cluster_id] = target_cluster
            self.total_clusters += 1
        
        # Add error to cluster
        target_cluster.errors.append(error)
        target_cluster.count += 1
        target_cluster.last_seen = error.timestamp
        
        # Update cluster metadata
        if error.trace_id:
            target_cluster.affected_traces.add(error.trace_id)
        
        if error.metadata.get('user_id'):
            target_cluster.affected_users.add(error.metadata['user_id'])
        
        # Update error rate (errors per minute over last hour)
        recent_cluster_errors = [
            e for e in target_cluster.errors 
            if e.timestamp > time.time() - 3600  # Last hour
        ]
        target_cluster.error_rate = len(recent_cluster_errors) / 60.0  # per minute
        
        # Analyze patterns for this cluster
        if len(target_cluster.errors) >= 3:
            await self._analyze_cluster_patterns(target_cluster)
    
    async def _analyze_cluster_patterns(self, cluster: ErrorCluster):
        """Analyze patterns within an error cluster"""
        # Temporal pattern analysis
        temporal_pattern = self.pattern_detector.analyze_temporal_pattern(cluster.errors)
        
        # Cascade pattern analysis  
        cascade_pattern = self.pattern_detector.detect_cascade_pattern(cluster.errors)
        
        # Update cluster analysis
        cluster.correlation_patterns['temporal'] = temporal_pattern
        cluster.correlation_patterns['cascade'] = cascade_pattern
        
        # Determine trend
        if len(cluster.errors) >= 5:
            recent_errors = [e for e in cluster.errors if e.timestamp > time.time() - 1800]  # 30 min
            older_errors = [e for e in cluster.errors if e.timestamp <= time.time() - 1800]
            
            if len(recent_errors) > len(older_errors) * 2:
                cluster.trend = "increasing"
            elif len(recent_errors) < len(older_errors) / 2:
                cluster.trend = "decreasing"
            elif temporal_pattern.get('pattern') == 'spike':
                cluster.trend = "spike"
            else:
                cluster.trend = "stable"
        
        # Root cause analysis
        await self._analyze_root_causes(cluster)
    
    async def _analyze_root_causes(self, cluster: ErrorCluster):
        """Analyze potential root causes for error cluster"""
        suspected_causes = []
        
        # Analyze error chain patterns
        if cluster.correlation_patterns.get('cascade', {}).get('is_cascade'):
            cascade_info = cluster.correlation_patterns['cascade']
            root_errors = set()
            
            for chain in cascade_info.get('cascade_chains', []):
                root_errors.add(chain['root_error'])
            
            if root_errors:
                suspected_causes.append(
                    f"Error cascade originating from {len(root_errors)} root error(s)"
                )
        
        # Analyze affected components
        modules = set(error.module_name for error in cluster.errors)
        if len(modules) == 1:
            suspected_causes.append(f"Isolated to module: {list(modules)[0]}")
        elif len(modules) <= 3:
            suspected_causes.append(f"Affects modules: {', '.join(modules)}")
        
        # Analyze timing patterns
        temporal = cluster.correlation_patterns.get('temporal', {})
        if temporal.get('pattern') == 'burst':
            suspected_causes.append("Burst pattern suggests sudden load or resource issue")
        elif temporal.get('pattern') == 'periodic':
            suspected_causes.append("Periodic pattern suggests scheduled job or cron issue")
        elif temporal.get('pattern') == 'spike':
            suspected_causes.append("Spike pattern suggests triggered event or external change")
        
        # Analyze error types
        error_types = [error.exception_type for error in cluster.errors]
        type_counts = {}
        for error_type in error_types:
            type_counts[error_type] = type_counts.get(error_type, 0) + 1
        
        dominant_type = max(type_counts.items(), key=lambda x: x[1])
        if dominant_type[1] / len(cluster.errors) > 0.8:
            suspected_causes.append(f"Dominated by {dominant_type[0]} errors")
        
        cluster.suspected_root_causes = suspected_causes
    
    def get_error(self, error_id: str) -> Optional[CorrelatedError]:
        """Get error by ID"""
        return self.errors.get(error_id)
    
    def get_cluster(self, cluster_id: str) -> Optional[ErrorCluster]:
        """Get cluster by ID"""
        return self.clusters.get(cluster_id)
    
    def get_recent_errors(self, limit: int = 50) -> List[CorrelatedError]:
        """Get recent errors"""
        recent = list(self.recent_errors)
        recent.sort(key=lambda e: e.timestamp, reverse=True)
        return recent[:limit]
    
    def get_error_clusters(self, limit: int = 20) -> List[ErrorCluster]:
        """Get error clusters sorted by recent activity"""
        clusters = list(self.clusters.values())
        clusters.sort(key=lambda c: c.last_seen, reverse=True)
        return clusters[:limit]
    
    def get_high_priority_clusters(self) -> List[ErrorCluster]:
        """Get clusters that need immediate attention"""
        high_priority = []
        
        for cluster in self.clusters.values():
            # High error rate
            if cluster.error_rate > 1.0:  # More than 1 error per minute
                high_priority.append(cluster)
                continue
            
            # Critical/High severity errors
            high_severity_count = sum(
                1 for error in cluster.errors 
                if error.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]
            )
            if high_severity_count > 0:
                high_priority.append(cluster)
                continue
            
            # Increasing trend
            if cluster.trend == "increasing":
                high_priority.append(cluster)
                continue
            
            # Recent spike
            if cluster.trend == "spike" and cluster.last_seen > time.time() - 3600:
                high_priority.append(cluster)
        
        # Sort by priority score
        def priority_score(cluster):
            score = 0
            score += cluster.error_rate * 10
            score += sum(10 if e.severity == ErrorSeverity.CRITICAL else
                        5 if e.severity == ErrorSeverity.HIGH else
                        1 for e in cluster.errors)
            if cluster.trend in ["increasing", "spike"]:
                score += 20
            return score
        
        high_priority.sort(key=priority_score, reverse=True)
        return high_priority
    
    def get_correlation_statistics(self) -> Dict[str, Any]:
        """Get correlation statistics"""
        active_clusters = len([c for c in self.clusters.values() if c.last_seen > time.time() - 3600])
        
        # Category distribution
        category_counts = {}
        severity_counts = {}
        
        for error in self.recent_errors:
            cat = error.category.value
            sev = error.severity.value
            category_counts[cat] = category_counts.get(cat, 0) + 1
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        return {
            "total_errors": self.total_errors,
            "total_clusters": self.total_clusters,
            "active_clusters": active_clusters,
            "correlation_hits": self.correlation_hits,
            "correlation_rate": (self.correlation_hits / max(1, self.total_errors)) * 100,
            "recent_errors": len(self.recent_errors),
            "category_distribution": category_counts,
            "severity_distribution": severity_counts,
            "high_priority_clusters": len(self.get_high_priority_clusters())
        }
    
    async def _cleanup_task(self):
        """Background cleanup task"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_old_data()
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old error data"""
        cutoff_time = time.time() - (self.retention_hours * 3600)
        
        # Remove old errors
        old_error_ids = [
            error_id for error_id, error in self.errors.items()
            if error.timestamp < cutoff_time
        ]
        
        for error_id in old_error_ids:
            del self.errors[error_id]
        
        # Remove old clusters
        old_cluster_ids = [
            cluster_id for cluster_id, cluster in self.clusters.items()
            if cluster.last_seen < cutoff_time
        ]
        
        for cluster_id in old_cluster_ids:
            del self.clusters[cluster_id]
        
        if old_error_ids or old_cluster_ids:
            self.logger.info(
                f"Cleaned up {len(old_error_ids)} old errors and "
                f"{len(old_cluster_ids)} old clusters"
            )


# Global error correlator instance
_error_correlator = ErrorCorrelator()


def get_error_correlator() -> ErrorCorrelator:
    """Get the global error correlator"""
    return _error_correlator


# Convenience functions
async def correlate_error(exception: Exception, context: Dict[str, Any] = None) -> str:
    """Correlate an error with the global correlator"""
    correlator = get_error_correlator()
    return await correlator.record_error(exception, context)


def get_error_context() -> Dict[str, Any]:
    """Get current error context for correlation"""
    return {
        "trace_id": get_current_trace_id(),
        "correlation_id": get_current_correlation_id(),
        "timestamp": datetime.now().isoformat()
    }