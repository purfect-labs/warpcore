#!/usr/bin/env python3
"""
WARPCORE Resource Management API Endpoints
Monitoring and control endpoints for async resource management system
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..middleware.resource_management import (
    get_resource_manager,
    ResourceType,
    ResourceState,
    managed_resource
)
from ..middleware.tracing.request_tracer import TraceSpan, SpanType


# Pydantic models for API responses
class ResourceInfo(BaseModel):
    resource_id: str
    resource_type: str
    state: str
    age: float
    idle_time: float
    access_count: int
    memory_usage: int
    correlation_id: Optional[str] = None
    context_info: Dict[str, Any] = Field(default_factory=dict)


class ResourcePoolInfo(BaseModel):
    pool_name: str
    resource_count: int
    resource_types: Dict[str, int] = Field(default_factory=dict)
    total_memory: int = 0


class ResourceStats(BaseModel):
    total_resources: int
    resources_by_type: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    resource_pools: Dict[str, int] = Field(default_factory=dict)
    management_stats: Dict[str, Any] = Field(default_factory=dict)
    system_memory: Dict[str, Any] = Field(default_factory=dict)
    leak_detection: Dict[str, Any] = Field(default_factory=dict)
    configuration: Dict[str, Any] = Field(default_factory=dict)


class CleanupRequest(BaseModel):
    resource_type: Optional[str] = None
    pool_name: Optional[str] = None
    force: bool = False
    max_age_seconds: Optional[float] = None
    max_idle_seconds: Optional[float] = None


class ResourceTestRequest(BaseModel):
    resource_type: str
    count: int = Field(default=1, ge=1, le=100)
    auto_cleanup_timeout: Optional[float] = None
    simulate_leak: bool = False


# Create router
router = APIRouter(prefix="/api/resource-management", tags=["resource_management"])
logger = logging.getLogger("resource_management_api")


@router.get("/health", summary="Check resource management system health")
async def get_resource_management_health():
    """Check if resource management systems are operational"""
    async with TraceSpan("resource_health_check", SpanType.REQUEST):
        manager = await get_resource_manager()
        stats = manager.get_resource_stats()
        
        # Health indicators
        total_resources = stats['total_resources']
        leak_count = stats['leak_detection']['recent_leaks']
        cleanup_errors = stats['management_stats']['cleanup_errors']
        memory_growth = stats['system_memory']['growth_bytes']
        
        # Determine health status
        health_issues = []
        
        if total_resources > 5000:
            health_issues.append("High resource count")
        
        if leak_count > 10:
            health_issues.append("Recent resource leaks detected")
        
        if cleanup_errors > 50:
            health_issues.append("High cleanup error rate")
        
        if memory_growth > 200 * 1024 * 1024:  # 200MB
            health_issues.append("Significant memory growth")
        
        status = "healthy" if not health_issues else "degraded"
        
        return JSONResponse({
            "status": status,
            "issues": health_issues,
            "total_resources": total_resources,
            "recent_leaks": leak_count,
            "cleanup_errors": cleanup_errors,
            "memory_growth_mb": memory_growth / (1024 * 1024),
            "timestamp": datetime.now().isoformat()
        })


@router.get("/statistics", response_model=ResourceStats, summary="Get comprehensive resource statistics")
async def get_resource_statistics():
    """Get detailed statistics about resource usage and management"""
    async with TraceSpan("get_resource_statistics", SpanType.REQUEST):
        manager = await get_resource_manager()
        stats = manager.get_resource_stats()
        
        return JSONResponse(ResourceStats(**stats).dict())


@router.get("/resources", summary="Get list of managed resources")
async def get_managed_resources(
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    state: Optional[str] = Query(None, description="Filter by resource state"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of resources to return"),
    show_details: bool = Query(False, description="Include detailed resource information")
):
    """Get list of currently managed resources with optional filtering"""
    async with TraceSpan("get_managed_resources", SpanType.REQUEST, {
        "resource_type": resource_type or "all",
        "state": state or "all",
        "limit": str(limit)
    }):
        manager = await get_resource_manager()
        
        # Get all resources
        resources = []
        count = 0
        
        for resource_id, managed_resource in manager.resources.items():
            if count >= limit:
                break
            
            # Apply filters
            if resource_type and managed_resource.resource_type.value != resource_type:
                continue
            
            if state and managed_resource.state.value != state:
                continue
            
            resource_info = ResourceInfo(
                resource_id=resource_id,
                resource_type=managed_resource.resource_type.value,
                state=managed_resource.state.value,
                age=managed_resource.metrics.age,
                idle_time=managed_resource.metrics.idle_time,
                access_count=managed_resource.metrics.access_count,
                memory_usage=managed_resource.metrics.memory_usage,
                correlation_id=managed_resource.correlation_id,
                context_info=managed_resource.context_info if show_details else {}
            )
            
            resources.append(resource_info.dict())
            count += 1
        
        return JSONResponse({
            "resources": resources,
            "total_returned": len(resources),
            "filtered": bool(resource_type or state),
            "available_types": list(set(r.resource_type.value for r in manager.resources.values())),
            "available_states": list(set(r.state.value for r in manager.resources.values()))
        })


@router.get("/resources/{resource_id}", summary="Get detailed resource information")
async def get_resource_details(resource_id: str):
    """Get detailed information about a specific managed resource"""
    async with TraceSpan("get_resource_details", SpanType.REQUEST, {"resource_id": resource_id}):
        manager = await get_resource_manager()
        
        if resource_id not in manager.resources:
            raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found")
        
        managed_resource = manager.resources[resource_id]
        
        # Get child resources
        child_resources = []
        for child_id in managed_resource.child_resource_ids:
            if child_id in manager.resources:
                child = manager.resources[child_id]
                child_resources.append({
                    "resource_id": child_id,
                    "resource_type": child.resource_type.value,
                    "state": child.state.value,
                    "age": child.metrics.age
                })
        
        # Get parent resource info
        parent_info = None
        if managed_resource.parent_resource_id and managed_resource.parent_resource_id in manager.resources:
            parent = manager.resources[managed_resource.parent_resource_id]
            parent_info = {
                "resource_id": managed_resource.parent_resource_id,
                "resource_type": parent.resource_type.value,
                "state": parent.state.value
            }
        
        return JSONResponse({
            "resource": ResourceInfo(
                resource_id=resource_id,
                resource_type=managed_resource.resource_type.value,
                state=managed_resource.state.value,
                age=managed_resource.metrics.age,
                idle_time=managed_resource.metrics.idle_time,
                access_count=managed_resource.metrics.access_count,
                memory_usage=managed_resource.metrics.memory_usage,
                correlation_id=managed_resource.correlation_id,
                context_info=managed_resource.context_info
            ).dict(),
            "parent_resource": parent_info,
            "child_resources": child_resources,
            "metrics": {
                "created_at": datetime.fromtimestamp(managed_resource.metrics.created_at).isoformat(),
                "last_accessed": datetime.fromtimestamp(managed_resource.metrics.last_accessed).isoformat(),
                "cleanup_attempts": managed_resource.metrics.cleanup_attempts,
                "estimated_cost": managed_resource.metrics.estimated_cost
            },
            "configuration": {
                "leak_detection_enabled": managed_resource.leak_detection_enabled,
                "auto_cleanup_timeout": managed_resource.auto_cleanup_timeout
            }
        })


@router.get("/pools", summary="Get resource pool information")
async def get_resource_pools():
    """Get information about all resource pools"""
    async with TraceSpan("get_resource_pools", SpanType.REQUEST):
        manager = await get_resource_manager()
        
        pools_info = []
        for pool_name, resource_ids in manager.resource_pools.items():
            # Count resources by type in this pool
            type_counts = {}
            total_memory = 0
            
            for resource_id in resource_ids:
                if resource_id in manager.resources:
                    resource = manager.resources[resource_id]
                    resource_type = resource.resource_type.value
                    type_counts[resource_type] = type_counts.get(resource_type, 0) + 1
                    total_memory += resource.metrics.memory_usage
            
            pool_info = ResourcePoolInfo(
                pool_name=pool_name,
                resource_count=len(resource_ids),
                resource_types=type_counts,
                total_memory=total_memory
            )
            pools_info.append(pool_info.dict())
        
        return JSONResponse({
            "pools": pools_info,
            "total_pools": len(manager.resource_pools),
            "total_pooled_resources": sum(len(pool) for pool in manager.resource_pools.values())
        })


@router.post("/cleanup", summary="Trigger resource cleanup")
async def trigger_cleanup(cleanup_request: CleanupRequest):
    """Trigger cleanup of resources based on criteria"""
    async with TraceSpan("trigger_cleanup", SpanType.REQUEST, {
        "resource_type": cleanup_request.resource_type or "all",
        "pool_name": cleanup_request.pool_name or "none",
        "force": str(cleanup_request.force)
    }):
        manager = await get_resource_manager()
        cleaned_count = 0
        
        try:
            if cleanup_request.pool_name:
                # Clean up specific pool
                cleaned_count = await manager.cleanup_pool(
                    cleanup_request.pool_name, 
                    cleanup_request.force
                )
                
            elif cleanup_request.resource_type:
                # Clean up specific resource type
                try:
                    resource_type = ResourceType(cleanup_request.resource_type)
                    cleaned_count = await manager.cleanup_by_type(
                        resource_type,
                        cleanup_request.force
                    )
                except ValueError:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Invalid resource type: {cleanup_request.resource_type}"
                    )
            
            else:
                # Clean up all resources
                cleaned_count = await manager.cleanup_all_resources(cleanup_request.force)
            
            return JSONResponse({
                "success": True,
                "cleaned_resources": cleaned_count,
                "cleanup_type": (
                    f"pool:{cleanup_request.pool_name}" if cleanup_request.pool_name else
                    f"type:{cleanup_request.resource_type}" if cleanup_request.resource_type else
                    "all"
                ),
                "forced": cleanup_request.force,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            return JSONResponse({
                "success": False,
                "error": str(e),
                "cleaned_resources": cleaned_count
            }, status_code=500)


@router.delete("/resources/{resource_id}", summary="Force cleanup specific resource")
async def force_cleanup_resource(resource_id: str):
    """Force cleanup of a specific resource"""
    async with TraceSpan("force_cleanup_resource", SpanType.REQUEST, {"resource_id": resource_id}):
        manager = await get_resource_manager()
        
        if resource_id not in manager.resources:
            raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found")
        
        success = await manager.cleanup_resource(resource_id, force=True)
        
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Resource {resource_id} cleaned up successfully",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return JSONResponse({
                "success": False,
                "message": f"Failed to cleanup resource {resource_id}"
            }, status_code=500)


@router.get("/leaks", summary="Get resource leak detection report")
async def get_leak_report():
    """Get comprehensive resource leak detection report"""
    async with TraceSpan("get_leak_report", SpanType.REQUEST):
        manager = await get_resource_manager()
        leak_report = manager.leak_detector.get_leak_report()
        
        return JSONResponse({
            "leak_detection_report": leak_report,
            "analysis": {
                "leak_rate": (
                    leak_report['recent_leaks'] / max(1, manager.get_resource_stats()['total_resources']) * 100
                ),
                "most_problematic_type": (
                    max(leak_report['leak_by_type'].items(), key=lambda x: x[1])[0]
                    if leak_report['leak_by_type'] else None
                ),
                "recommendations": [
                    "Check for unclosed connections" if 'connection' in str(leak_report['leak_by_type']) else None,
                    "Review file handle management" if 'file' in str(leak_report['leak_by_type']) else None,
                    "Monitor subprocess cleanup" if 'subprocess' in str(leak_report['leak_by_type']) else None
                ]
            }
        })


@router.post("/test/create-resources", summary="Create test resources (WARP TEST endpoint)")
async def create_test_resources(test_request: ResourceTestRequest):
    """Create test resources for testing resource management"""
    async with TraceSpan("create_test_resources", SpanType.REQUEST, {
        "resource_type": test_request.resource_type,
        "count": str(test_request.count),
        "simulate_leak": str(test_request.simulate_leak)
    }):
        manager = await get_resource_manager()
        
        try:
            resource_type = ResourceType(test_request.resource_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid resource type: {test_request.resource_type}"
            )
        
        created_resources = []
        
        for i in range(test_request.count):
            # Create different types of test resources
            if resource_type == ResourceType.FILE_HANDLE:
                import tempfile
                test_resource = tempfile.NamedTemporaryFile(mode='w', delete=False)
                test_resource.write(f"WARP TEST file content {i}")
                test_resource.flush()
            
            elif resource_type == ResourceType.MEMORY_BUFFER:
                test_resource = bytearray(1024 * 100)  # 100KB buffer
                
            elif resource_type == ResourceType.ASYNC_TASK:
                async def test_task():
                    await asyncio.sleep(3600 if test_request.simulate_leak else 1)
                    return f"WARP TEST task result {i}"
                
                test_resource = asyncio.create_task(test_task())
                
            elif resource_type == ResourceType.TEMP_FILE:
                import tempfile
                test_resource = tempfile.NamedTemporaryFile(mode='w', delete=False)
                test_resource.write(f"WARP TEST temporary file {i}")
                test_resource.close()
                
            else:
                # Generic test resource
                test_resource = {
                    'test_data': f'WARP TEST resource {i}',
                    'resource_type': test_request.resource_type,
                    'created_at': datetime.now().isoformat()
                }
            
            # Register with resource manager
            resource_id = manager.register_resource(
                resource=test_resource,
                resource_type=resource_type,
                auto_cleanup_timeout=test_request.auto_cleanup_timeout,
                context_info={
                    'test_mode': True,
                    'test_batch': datetime.now().isoformat(),
                    'simulate_leak': test_request.simulate_leak,
                    'test_index': i
                },
                pool_name='test_resources'
            )
            
            created_resources.append(resource_id)
        
        return JSONResponse({
            "success": True,
            "message": f"Created {len(created_resources)} test resources",
            "resource_type": test_request.resource_type,
            "resource_ids": created_resources,
            "simulate_leak": test_request.simulate_leak,
            "auto_cleanup_timeout": test_request.auto_cleanup_timeout,
            "timestamp": datetime.now().isoformat()
        })


@router.get("/test/memory-usage", summary="Get detailed memory usage analysis")
async def get_memory_analysis():
    """Get detailed memory usage analysis including system and process metrics"""
    async with TraceSpan("get_memory_analysis", SpanType.REQUEST):
        manager = await get_resource_manager()
        
        try:
            import psutil
            import gc
            
            # Process memory info
            process = manager.process
            memory_info = process.memory_info()
            
            # System memory info
            system_memory = psutil.virtual_memory()
            
            # Garbage collection stats
            gc_stats = {
                'counts': gc.get_count(),
                'stats': gc.get_stats() if hasattr(gc, 'get_stats') else None
            }
            
            # Resource manager stats
            resource_stats = manager.get_resource_stats()
            
            return JSONResponse({
                "process_memory": {
                    "rss_bytes": memory_info.rss,
                    "rss_mb": memory_info.rss / (1024 * 1024),
                    "vms_bytes": memory_info.vms,
                    "vms_mb": memory_info.vms / (1024 * 1024),
                    "percent": process.memory_percent(),
                    "baseline_rss": manager._baseline_memory,
                    "growth_bytes": memory_info.rss - manager._baseline_memory,
                    "growth_mb": (memory_info.rss - manager._baseline_memory) / (1024 * 1024)
                },
                "system_memory": {
                    "total_bytes": system_memory.total,
                    "total_gb": system_memory.total / (1024**3),
                    "available_bytes": system_memory.available,
                    "available_gb": system_memory.available / (1024**3),
                    "percent_used": system_memory.percent,
                    "free_bytes": system_memory.free,
                    "free_gb": system_memory.free / (1024**3)
                },
                "garbage_collection": gc_stats,
                "resource_tracking": {
                    "tracked_resources": resource_stats['total_resources'],
                    "tracked_memory_bytes": resource_stats['system_memory']['tracked_memory'],
                    "tracked_memory_mb": resource_stats['system_memory']['tracked_memory'] / (1024 * 1024)
                },
                "analysis_timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Memory analysis failed: {str(e)}")
            return JSONResponse({
                "error": f"Memory analysis failed: {str(e)}",
                "basic_stats": manager.get_resource_stats()['system_memory']
            }, status_code=500)


# Add router to main application
def setup_resource_management_routes(app):
    """Setup resource management routes on FastAPI app"""
    app.include_router(router)
    logger.info("WARP RESOURCE MANAGEMENT API routes configured")