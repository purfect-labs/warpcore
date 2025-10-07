#!/usr/bin/env python3
"""
WARPCORE Async Resource Management System
Comprehensive resource tracking, cleanup, and leak prevention for all async operations
"""

import asyncio
import gc
import logging
import os
import psutil
import time
import traceback
import weakref
from collections import defaultdict, deque
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Set, Callable, AsyncGenerator, Union
import uuid

from ..tracing.request_tracer import get_current_correlation_id, TraceSpan, SpanType


class ResourceType(Enum):
    """Types of managed resources"""
    DATABASE_CONNECTION = "database_connection"
    HTTP_CONNECTION = "http_connection"
    FILE_HANDLE = "file_handle"
    SUBPROCESS = "subprocess"
    WEBSOCKET = "websocket"
    MEMORY_BUFFER = "memory_buffer"
    TEMP_FILE = "temp_file"
    THREAD_POOL = "thread_pool"
    ASYNC_TASK = "async_task"
    EVENT_LOOP = "event_loop"
    SOCKET = "socket"
    CACHE_ENTRY = "cache_entry"
    LOCK = "lock"
    SEMAPHORE = "semaphore"
    UNKNOWN = "unknown"


class ResourceState(Enum):
    """Resource lifecycle states"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    IDLE = "idle"
    CLEANUP_PENDING = "cleanup_pending"
    CLEANING_UP = "cleaning_up"
    CLOSED = "closed"
    LEAKED = "leaked"
    ERROR = "error"


@dataclass
class ResourceMetrics:
    """Resource usage metrics"""
    created_at: float
    last_accessed: float
    access_count: int = 0
    cleanup_attempts: int = 0
    memory_usage: int = 0  # bytes
    estimated_cost: float = 0.0  # arbitrary cost units
    
    @property
    def age(self) -> float:
        """Resource age in seconds"""
        return time.time() - self.created_at
    
    @property
    def idle_time(self) -> float:
        """Time since last access in seconds"""
        return time.time() - self.last_accessed


@dataclass
class ManagedResource:
    """A managed resource with lifecycle tracking"""
    resource_id: str
    resource_type: ResourceType
    resource: Any  # The actual resource object
    state: ResourceState
    metrics: ResourceMetrics
    cleanup_callback: Optional[Callable] = None
    context_info: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    parent_resource_id: Optional[str] = None
    child_resource_ids: Set[str] = field(default_factory=set)
    leak_detection_enabled: bool = True
    auto_cleanup_timeout: Optional[float] = None  # seconds
    
    def __post_init__(self):
        """Post-initialization setup"""
        if not self.correlation_id:
            self.correlation_id = get_current_correlation_id()
    
    def update_access(self):
        """Update access tracking"""
        self.metrics.last_accessed = time.time()
        self.metrics.access_count += 1
    
    def is_idle(self, idle_threshold: float = 300.0) -> bool:
        """Check if resource has been idle for too long"""
        return self.metrics.idle_time > idle_threshold
    
    def is_old(self, max_age: float = 3600.0) -> bool:
        """Check if resource is too old"""
        return self.metrics.age > max_age
    
    def should_cleanup(self) -> bool:
        """Determine if resource should be cleaned up"""
        if self.state in [ResourceState.CLOSED, ResourceState.LEAKED]:
            return False
        
        if self.auto_cleanup_timeout and self.metrics.idle_time > self.auto_cleanup_timeout:
            return True
        
        # Default cleanup conditions
        return (
            self.is_idle(600.0) or  # 10 minutes idle
            self.is_old(3600.0)     # 1 hour old
        )


class ResourceLeakDetector:
    """Detects and reports resource leaks"""
    
    def __init__(self):
        self.logger = logging.getLogger("resource_leak_detector")
        self.leak_threshold = 100  # Max resources per type before warning
        self.scan_interval = 300   # 5 minutes
        self.last_scan = time.time()
        self.leak_history = deque(maxlen=1000)
        self._gc_stats = defaultdict(int)
    
    def detect_leaks(self, resources: Dict[str, ManagedResource]) -> List[ManagedResource]:
        """Detect potential resource leaks"""
        current_time = time.time()
        potential_leaks = []
        
        # Group resources by type
        by_type = defaultdict(list)
        for resource in resources.values():
            by_type[resource.resource_type].append(resource)
        
        # Check each resource type
        for resource_type, resource_list in by_type.items():
            # Check for excessive count
            if len(resource_list) > self.leak_threshold:
                self.logger.warning(
                    f"WARP RESOURCE LEAK WARNING: {len(resource_list)} {resource_type.value} resources detected"
                )
            
            # Check for old, unused resources
            for resource in resource_list:
                if self._is_potential_leak(resource, current_time):
                    potential_leaks.append(resource)
                    resource.state = ResourceState.LEAKED
                    
                    leak_info = {
                        'resource_id': resource.resource_id,
                        'resource_type': resource.resource_type.value,
                        'age': resource.metrics.age,
                        'idle_time': resource.metrics.idle_time,
                        'access_count': resource.metrics.access_count,
                        'correlation_id': resource.correlation_id,
                        'context': resource.context_info,
                        'detected_at': current_time
                    }
                    
                    self.leak_history.append(leak_info)
                    
                    self.logger.error(
                        f"WARP RESOURCE LEAK: {resource.resource_type.value} "
                        f"({resource.resource_id}) - Age: {resource.metrics.age:.1f}s, "
                        f"Idle: {resource.metrics.idle_time:.1f}s, "
                        f"Access count: {resource.metrics.access_count}"
                    )
        
        self.last_scan = current_time
        return potential_leaks
    
    def _is_potential_leak(self, resource: ManagedResource, current_time: float) -> bool:
        """Determine if a resource is a potential leak"""
        if not resource.leak_detection_enabled:
            return False
        
        if resource.state in [ResourceState.CLOSED, ResourceState.LEAKED]:
            return False
        
        # Aggressive leak detection criteria
        age_threshold = 1800  # 30 minutes
        idle_threshold = 900  # 15 minutes
        
        is_old_and_idle = (
            resource.metrics.age > age_threshold and
            resource.metrics.idle_time > idle_threshold and
            resource.metrics.access_count < 5  # Very few accesses
        )
        
        # Special handling for different resource types
        if resource.resource_type == ResourceType.TEMP_FILE:
            # Temp files should be cleaned up quickly
            return resource.metrics.age > 300  # 5 minutes
        elif resource.resource_type == ResourceType.SUBPROCESS:
            # Long-running processes might be intentional
            return resource.metrics.age > 3600 and resource.metrics.idle_time > 1800
        elif resource.resource_type in [ResourceType.DATABASE_CONNECTION, ResourceType.HTTP_CONNECTION]:
            # Connections should be reused but not held forever
            return is_old_and_idle
        
        return is_old_and_idle
    
    def get_leak_report(self) -> Dict[str, Any]:
        """Generate comprehensive leak report"""
        recent_leaks = [
            leak for leak in self.leak_history
            if time.time() - leak['detected_at'] < 3600  # Last hour
        ]
        
        leak_by_type = defaultdict(int)
        for leak in recent_leaks:
            leak_by_type[leak['resource_type']] += 1
        
        return {
            'total_leaks_detected': len(self.leak_history),
            'recent_leaks': len(recent_leaks),
            'leak_by_type': dict(leak_by_type),
            'last_scan': datetime.fromtimestamp(self.last_scan).isoformat(),
            'leak_threshold': self.leak_threshold,
            'recent_leak_details': recent_leaks[-10:] if recent_leaks else []
        }


class AsyncResourceManager:
    """Comprehensive async resource management system"""
    
    def __init__(self):
        self.logger = logging.getLogger("async_resource_manager")
        
        # Resource storage
        self.resources: Dict[str, ManagedResource] = {}
        self.resource_pools: Dict[str, Set[str]] = defaultdict(set)
        
        # Management components
        self.leak_detector = ResourceLeakDetector()
        self.exit_stack = AsyncExitStack()
        
        # Configuration
        self.cleanup_interval = 60  # 1 minute
        self.max_resources_per_type = 1000
        self.default_idle_timeout = 300  # 5 minutes
        
        # Statistics
        self.stats = {
            'resources_created': 0,
            'resources_cleaned_up': 0,
            'cleanup_errors': 0,
            'leaks_detected': 0,
            'auto_cleanups_performed': 0
        }
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown = False
        
        # Process monitoring
        self.process = psutil.Process()
        self._baseline_memory = self.process.memory_info().rss
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.shutdown()
    
    async def start(self):
        """Start the resource manager"""
        self.logger.info("🚀 WARP RESOURCE MANAGER: Starting async resource management")
        
        # Start background tasks
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        self.logger.info("✅ WARP RESOURCE MANAGER: Background tasks started")
    
    async def shutdown(self):
        """Shutdown the resource manager"""
        self.logger.info("🛑 WARP RESOURCE MANAGER: Shutting down...")
        self._shutdown = True
        
        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Clean up all remaining resources
        await self.cleanup_all_resources(force=True)
        
        # Close exit stack
        await self.exit_stack.aclose()
        
        self.logger.info("✅ WARP RESOURCE MANAGER: Shutdown complete")
    
    def register_resource(
        self,
        resource: Any,
        resource_type: ResourceType,
        cleanup_callback: Optional[Callable] = None,
        auto_cleanup_timeout: Optional[float] = None,
        context_info: Dict[str, Any] = None,
        parent_resource_id: Optional[str] = None,
        pool_name: Optional[str] = None
    ) -> str:
        """Register a resource for management"""
        resource_id = str(uuid.uuid4())
        
        # Check resource limits
        type_count = sum(1 for r in self.resources.values() if r.resource_type == resource_type)
        if type_count >= self.max_resources_per_type:
            self.logger.warning(
                f"WARP RESOURCE WARNING: Maximum resources reached for {resource_type.value} "
                f"({type_count}/{self.max_resources_per_type})"
            )
        
        # Create managed resource
        managed_resource = ManagedResource(
            resource_id=resource_id,
            resource_type=resource_type,
            resource=resource,
            state=ResourceState.INITIALIZING,
            metrics=ResourceMetrics(
                created_at=time.time(),
                last_accessed=time.time()
            ),
            cleanup_callback=cleanup_callback,
            auto_cleanup_timeout=auto_cleanup_timeout or self.default_idle_timeout,
            context_info=context_info or {},
            parent_resource_id=parent_resource_id
        )
        
        # Handle parent-child relationships
        if parent_resource_id and parent_resource_id in self.resources:
            parent = self.resources[parent_resource_id]
            parent.child_resource_ids.add(resource_id)
        
        # Store resource
        self.resources[resource_id] = managed_resource
        
        # Add to pool if specified
        if pool_name:
            self.resource_pools[pool_name].add(resource_id)
        
        # Update statistics
        self.stats['resources_created'] += 1
        managed_resource.state = ResourceState.ACTIVE
        
        self.logger.debug(
            f"🔧 WARP RESOURCE: Registered {resource_type.value} ({resource_id}) "
            f"[correlation: {managed_resource.correlation_id}]"
        )
        
        return resource_id
    
    async def get_resource(self, resource_id: str) -> Optional[Any]:
        """Get a managed resource and update access tracking"""
        if resource_id not in self.resources:
            return None
        
        managed_resource = self.resources[resource_id]
        
        if managed_resource.state == ResourceState.CLOSED:
            return None
        
        managed_resource.update_access()
        return managed_resource.resource
    
    async def cleanup_resource(self, resource_id: str, force: bool = False) -> bool:
        """Clean up a specific resource"""
        if resource_id not in self.resources:
            return False
        
        managed_resource = self.resources[resource_id]
        
        if managed_resource.state in [ResourceState.CLOSED, ResourceState.CLEANING_UP]:
            return True
        
        if not force and managed_resource.state == ResourceState.ACTIVE:
            # Check if resource is still being used
            if managed_resource.metrics.idle_time < 10:  # Active in last 10 seconds
                return False
        
        managed_resource.state = ResourceState.CLEANING_UP
        managed_resource.metrics.cleanup_attempts += 1
        
        try:
            # Clean up child resources first
            for child_id in managed_resource.child_resource_ids.copy():
                await self.cleanup_resource(child_id, force=True)
            
            # Use custom cleanup callback if provided
            if managed_resource.cleanup_callback:
                if asyncio.iscoroutinefunction(managed_resource.cleanup_callback):
                    await managed_resource.cleanup_callback(managed_resource.resource)
                else:
                    managed_resource.cleanup_callback(managed_resource.resource)
            else:
                # Default cleanup based on resource type
                await self._default_cleanup(managed_resource)
            
            managed_resource.state = ResourceState.CLOSED
            self.stats['resources_cleaned_up'] += 1
            
            # Remove from pools
            for pool_resources in self.resource_pools.values():
                pool_resources.discard(resource_id)
            
            # Remove from parent's children
            if managed_resource.parent_resource_id:
                parent_id = managed_resource.parent_resource_id
                if parent_id in self.resources:
                    self.resources[parent_id].child_resource_ids.discard(resource_id)
            
            self.logger.debug(
                f"🧹 WARP RESOURCE: Cleaned up {managed_resource.resource_type.value} ({resource_id})"
            )
            
            return True
            
        except Exception as e:
            managed_resource.state = ResourceState.ERROR
            self.stats['cleanup_errors'] += 1
            
            self.logger.error(
                f"❌ WARP RESOURCE: Failed to cleanup {managed_resource.resource_type.value} "
                f"({resource_id}): {str(e)}"
            )
            
            return False
    
    async def _default_cleanup(self, managed_resource: ManagedResource):
        """Default cleanup implementation based on resource type"""
        resource = managed_resource.resource
        resource_type = managed_resource.resource_type
        
        if resource_type == ResourceType.FILE_HANDLE:
            if hasattr(resource, 'close'):
                resource.close()
        
        elif resource_type == ResourceType.TEMP_FILE:
            if hasattr(resource, 'name') and os.path.exists(resource.name):
                try:
                    os.unlink(resource.name)
                except OSError:
                    pass
            if hasattr(resource, 'close'):
                resource.close()
        
        elif resource_type in [ResourceType.DATABASE_CONNECTION, ResourceType.HTTP_CONNECTION]:
            if hasattr(resource, 'close'):
                if asyncio.iscoroutinefunction(resource.close):
                    await resource.close()
                else:
                    resource.close()
        
        elif resource_type == ResourceType.SUBPROCESS:
            if hasattr(resource, 'terminate'):
                resource.terminate()
                try:
                    await asyncio.wait_for(resource.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    if hasattr(resource, 'kill'):
                        resource.kill()
        
        elif resource_type == ResourceType.WEBSOCKET:
            if hasattr(resource, 'close'):
                if asyncio.iscoroutinefunction(resource.close):
                    await resource.close()
                else:
                    resource.close()
        
        elif resource_type == ResourceType.ASYNC_TASK:
            if hasattr(resource, 'cancel'):
                resource.cancel()
                try:
                    await resource
                except asyncio.CancelledError:
                    pass
        
        elif resource_type == ResourceType.SOCKET:
            if hasattr(resource, 'close'):
                resource.close()
    
    async def cleanup_pool(self, pool_name: str, force: bool = False) -> int:
        """Clean up all resources in a specific pool"""
        if pool_name not in self.resource_pools:
            return 0
        
        resource_ids = list(self.resource_pools[pool_name])
        cleaned_count = 0
        
        for resource_id in resource_ids:
            if await self.cleanup_resource(resource_id, force):
                cleaned_count += 1
        
        return cleaned_count
    
    async def cleanup_by_type(self, resource_type: ResourceType, force: bool = False) -> int:
        """Clean up all resources of a specific type"""
        resource_ids = [
            rid for rid, resource in self.resources.items()
            if resource.resource_type == resource_type
        ]
        
        cleaned_count = 0
        for resource_id in resource_ids:
            if await self.cleanup_resource(resource_id, force):
                cleaned_count += 1
        
        return cleaned_count
    
    async def cleanup_all_resources(self, force: bool = False) -> int:
        """Clean up all managed resources"""
        resource_ids = list(self.resources.keys())
        cleaned_count = 0
        
        for resource_id in resource_ids:
            if await self.cleanup_resource(resource_id, force):
                cleaned_count += 1
        
        # Remove cleaned resources from tracking
        if force:
            closed_ids = [
                rid for rid, resource in self.resources.items()
                if resource.state == ResourceState.CLOSED
            ]
            for resource_id in closed_ids:
                del self.resources[resource_id]
        
        return cleaned_count
    
    async def _cleanup_loop(self):
        """Background cleanup task"""
        while not self._shutdown:
            try:
                async with TraceSpan("resource_cleanup_cycle", SpanType.COMPUTATION):
                    # Auto-cleanup eligible resources
                    auto_cleaned = await self._auto_cleanup()
                    if auto_cleaned > 0:
                        self.stats['auto_cleanups_performed'] += auto_cleaned
                        self.logger.info(f"🧹 WARP RESOURCE: Auto-cleaned {auto_cleaned} resources")
                    
                    # Detect and handle leaks
                    leaks = self.leak_detector.detect_leaks(self.resources)
                    if leaks:
                        self.stats['leaks_detected'] += len(leaks)
                        self.logger.warning(f"🚨 WARP RESOURCE: Detected {len(leaks)} potential leaks")
                        
                        # Force cleanup leaked resources
                        for leak in leaks:
                            await self.cleanup_resource(leak.resource_id, force=True)
                    
                    # Remove closed resources from tracking
                    await self._garbage_collect()
                
                await asyncio.sleep(self.cleanup_interval)
                
            except Exception as e:
                self.logger.error(f"❌ WARP RESOURCE: Cleanup loop error: {str(e)}")
                await asyncio.sleep(self.cleanup_interval)
    
    async def _auto_cleanup(self) -> int:
        """Automatically clean up eligible resources"""
        eligible_resources = [
            resource_id for resource_id, resource in self.resources.items()
            if resource.should_cleanup() and resource.state == ResourceState.ACTIVE
        ]
        
        cleaned_count = 0
        for resource_id in eligible_resources:
            if await self.cleanup_resource(resource_id):
                cleaned_count += 1
        
        return cleaned_count
    
    async def _garbage_collect(self):
        """Remove closed resources and perform garbage collection"""
        # Remove closed resources from tracking
        closed_ids = [
            rid for rid, resource in self.resources.items()
            if resource.state == ResourceState.CLOSED
        ]
        
        for resource_id in closed_ids:
            del self.resources[resource_id]
        
        # Force Python garbage collection periodically
        if len(closed_ids) > 10 or time.time() % 300 < 60:  # Every 5 minutes
            collected = gc.collect()
            if collected > 0:
                self.logger.debug(f"🗑️  WARP RESOURCE: Garbage collected {collected} objects")
    
    async def _monitoring_loop(self):
        """Background monitoring task"""
        while not self._shutdown:
            try:
                async with TraceSpan("resource_monitoring_cycle", SpanType.COMPUTATION):
                    # Update resource metrics
                    await self._update_metrics()
                    
                    # Check memory usage
                    current_memory = self.process.memory_info().rss
                    memory_growth = current_memory - self._baseline_memory
                    
                    if memory_growth > 100 * 1024 * 1024:  # 100MB growth
                        self.logger.warning(
                            f"📈 WARP RESOURCE: Memory growth detected: "
                            f"{memory_growth / 1024 / 1024:.1f}MB since baseline"
                        )
                
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                self.logger.error(f"❌ WARP RESOURCE: Monitoring loop error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _update_metrics(self):
        """Update resource metrics"""
        for resource in self.resources.values():
            if resource.state == ResourceState.ACTIVE:
                # Estimate memory usage for certain resource types
                if resource.resource_type in [ResourceType.MEMORY_BUFFER]:
                    if hasattr(resource.resource, '__sizeof__'):
                        resource.metrics.memory_usage = resource.resource.__sizeof__()
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """Get comprehensive resource statistics"""
        stats_by_type = defaultdict(lambda: {
            'count': 0,
            'active': 0,
            'idle': 0,
            'closed': 0,
            'leaked': 0,
            'memory_usage': 0
        })
        
        total_memory = 0
        
        for resource in self.resources.values():
            type_stats = stats_by_type[resource.resource_type.value]
            type_stats['count'] += 1
            
            if resource.state == ResourceState.ACTIVE:
                type_stats['active'] += 1
            elif resource.state == ResourceState.IDLE:
                type_stats['idle'] += 1
            elif resource.state == ResourceState.CLOSED:
                type_stats['closed'] += 1
            elif resource.state == ResourceState.LEAKED:
                type_stats['leaked'] += 1
            
            type_stats['memory_usage'] += resource.metrics.memory_usage
            total_memory += resource.metrics.memory_usage
        
        # System memory info
        try:
            current_memory = self.process.memory_info().rss
            memory_percent = self.process.memory_percent()
        except:
            current_memory = 0
            memory_percent = 0.0
        
        return {
            'total_resources': len(self.resources),
            'resources_by_type': dict(stats_by_type),
            'resource_pools': {name: len(pool) for name, pool in self.resource_pools.items()},
            'management_stats': self.stats.copy(),
            'leak_detection': self.leak_detector.get_leak_report(),
            'system_memory': {
                'current_rss': current_memory,
                'baseline_rss': self._baseline_memory,
                'growth_bytes': current_memory - self._baseline_memory,
                'memory_percent': memory_percent,
                'tracked_memory': total_memory
            },
            'configuration': {
                'cleanup_interval': self.cleanup_interval,
                'max_resources_per_type': self.max_resources_per_type,
                'default_idle_timeout': self.default_idle_timeout,
                'leak_threshold': self.leak_detector.leak_threshold
            }
        }


# Resource context managers and utilities
@asynccontextmanager
async def managed_resource(
    resource: Any,
    resource_type: ResourceType,
    manager: AsyncResourceManager,
    cleanup_callback: Optional[Callable] = None,
    auto_cleanup_timeout: Optional[float] = None,
    context_info: Dict[str, Any] = None
) -> AsyncGenerator[Any, None]:
    """Context manager for automatic resource registration and cleanup"""
    resource_id = manager.register_resource(
        resource=resource,
        resource_type=resource_type,
        cleanup_callback=cleanup_callback,
        auto_cleanup_timeout=auto_cleanup_timeout,
        context_info=context_info
    )
    
    try:
        yield resource
    finally:
        await manager.cleanup_resource(resource_id, force=True)


def resource_wrapper(resource_type: ResourceType, auto_cleanup_timeout: float = None):
    """Decorator for automatic resource management"""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                manager = get_resource_manager()
                resource = await func(*args, **kwargs)
                
                resource_id = manager.register_resource(
                    resource=resource,
                    resource_type=resource_type,
                    auto_cleanup_timeout=auto_cleanup_timeout,
                    context_info={'function': func.__name__, 'args_count': len(args)}
                )
                
                return resource
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                manager = get_resource_manager()
                resource = func(*args, **kwargs)
                
                resource_id = manager.register_resource(
                    resource=resource,
                    resource_type=resource_type,
                    auto_cleanup_timeout=auto_cleanup_timeout,
                    context_info={'function': func.__name__, 'args_count': len(args)}
                )
                
                return resource
            return sync_wrapper
    
    return decorator


# Global resource manager instance
_resource_manager: Optional[AsyncResourceManager] = None


async def get_resource_manager() -> AsyncResourceManager:
    """Get or create the global resource manager"""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = AsyncResourceManager()
        await _resource_manager.start()
    return _resource_manager


async def shutdown_resource_manager():
    """Shutdown the global resource manager"""
    global _resource_manager
    if _resource_manager is not None:
        await _resource_manager.shutdown()
        _resource_manager = None