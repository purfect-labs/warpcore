#!/usr/bin/env python3
"""
WARPCORE Configuration Management API Endpoints
Monitoring and control endpoints for configuration validation and hot reloading
"""

import asyncio
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..middleware.config_management import (
    get_config_manager,
    ConfigValidationLevel,
    ConfigChangeType,
    ConfigSource,
    ValidationResult
)
from ..middleware.tracing.request_tracer import TraceSpan, SpanType


# Pydantic models for API responses
class ValidationResultModel(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    validation_time: float
    validation_level: str


class ConfigSnapshotModel(BaseModel):
    checksum: str
    timestamp: float
    source: str
    file_paths: List[str] = Field(default_factory=list)
    validation_result: Optional[ValidationResultModel] = None


class ConfigChangeEventModel(BaseModel):
    change_type: str
    file_path: str
    timestamp: float
    correlation_id: Optional[str] = None
    applied: bool = False
    rollback_attempted: bool = False


class ConfigStatsModel(BaseModel):
    configs_loaded: int
    validations_performed: int
    validation_failures: int
    hot_reloads: int
    rollbacks: int
    file_changes_detected: int
    current_config_checksum: Optional[str] = None
    watched_files_count: int
    rollback_stack_depth: int
    validation_level: str
    auto_reload_enabled: bool
    auto_rollback_enabled: bool
    file_watching_active: bool


class ConfigValidationRequest(BaseModel):
    config_data: Dict[str, Any]
    validation_level: str = "strict"


class ConfigUpdateRequest(BaseModel):
    config_section: Optional[str] = None
    config_data: Dict[str, Any]
    validate_only: bool = False


# Create router
router = APIRouter(prefix="/api/config-management", tags=["config_management"])
logger = logging.getLogger("config_management_api")


@router.get("/health", summary="Check configuration management system health")
async def get_config_management_health():
    """Check if configuration management systems are operational"""
    async with TraceSpan("config_health_check", SpanType.REQUEST):
        manager = await get_config_manager()
        stats = manager.get_statistics()
        
        # Health indicators
        validation_failures = stats['validation_failures']
        recent_rollbacks = stats['rollbacks']
        file_watching_active = stats['file_watching_active']
        
        # Determine health status
        health_issues = []
        
        if validation_failures > 10:
            health_issues.append("High validation failure rate")
        
        if recent_rollbacks > 5:
            health_issues.append("Frequent configuration rollbacks")
        
        if not file_watching_active and stats['auto_reload_enabled']:
            health_issues.append("File watching not active despite being enabled")
        
        status = "healthy" if not health_issues else "degraded"
        
        return JSONResponse({
            "status": status,
            "issues": health_issues,
            "validation_failures": validation_failures,
            "recent_rollbacks": recent_rollbacks,
            "file_watching_active": file_watching_active,
            "watched_files": stats['watched_files_count'],
            "timestamp": datetime.now().isoformat()
        })


@router.get("/statistics", response_model=ConfigStatsModel, summary="Get configuration management statistics")
async def get_config_statistics():
    """Get detailed statistics about configuration management"""
    async with TraceSpan("get_config_statistics", SpanType.REQUEST):
        manager = await get_config_manager()
        stats = manager.get_statistics()
        
        return JSONResponse(ConfigStatsModel(**stats).dict())


@router.get("/current", summary="Get current configuration")
async def get_current_config(
    section: Optional[str] = Query(None, description="Get specific configuration section"),
    key_path: Optional[str] = Query(None, description="Get value by dot-separated key path")
):
    """Get current configuration or specific section/value"""
    async with TraceSpan("get_current_config", SpanType.REQUEST, {
        "section": section or "all",
        "key_path": key_path or "none"
    }):
        manager = await get_config_manager()
        
        if key_path:
            # Get specific value by path
            value = manager.get_config_value(key_path)
            return JSONResponse({
                "key_path": key_path,
                "value": value,
                "exists": value is not None,
                "timestamp": datetime.now().isoformat()
            })
        
        elif section:
            # Get specific section
            section_data = manager.get_config_section(section)
            return JSONResponse({
                "section": section,
                "data": section_data,
                "exists": bool(section_data),
                "timestamp": datetime.now().isoformat()
            })
        
        else:
            # Get full configuration
            current_config = manager.get_current_config()
            current_snapshot = manager.current_config
            
            response_data = {
                "config_data": current_config,
                "timestamp": datetime.now().isoformat()
            }
            
            if current_snapshot:
                response_data.update({
                    "checksum": current_snapshot.checksum,
                    "source": current_snapshot.source.value,
                    "file_paths": current_snapshot.file_paths,
                    "config_timestamp": current_snapshot.timestamp
                })
            
            return JSONResponse(response_data)


@router.post("/validate", summary="Validate configuration data")
async def validate_config(validation_request: ConfigValidationRequest):
    """Validate configuration data without applying it"""
    async with TraceSpan("validate_config", SpanType.REQUEST, {
        "validation_level": validation_request.validation_level,
        "sections_count": str(len(validation_request.config_data))
    }):
        manager = await get_config_manager()
        
        try:
            # Parse validation level
            validation_level = ConfigValidationLevel(validation_request.validation_level.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid validation level: {validation_request.validation_level}"
            )
        
        # Validate configuration
        result = await manager.validator.validate_config(
            validation_request.config_data,
            validation_level
        )
        
        return JSONResponse({
            "validation_result": ValidationResultModel(
                is_valid=result.is_valid,
                errors=result.errors,
                warnings=result.warnings,
                validation_time=result.validation_time,
                validation_level=result.validation_level.value
            ).dict(),
            "timestamp": datetime.now().isoformat()
        })


@router.get("/history", summary="Get configuration history")
async def get_config_history(
    limit: int = Query(10, ge=1, le=50, description="Number of historical configurations to return")
):
    """Get configuration change history"""
    async with TraceSpan("get_config_history", SpanType.REQUEST, {"limit": str(limit)}):
        manager = await get_config_manager()
        history = manager.get_config_history(limit)
        
        history_data = []
        for snapshot in history:
            snapshot_data = ConfigSnapshotModel(
                checksum=snapshot.checksum,
                timestamp=snapshot.timestamp,
                source=snapshot.source.value,
                file_paths=snapshot.file_paths
            )
            
            if snapshot.validation_result:
                snapshot_data.validation_result = ValidationResultModel(
                    is_valid=snapshot.validation_result.is_valid,
                    errors=snapshot.validation_result.errors,
                    warnings=snapshot.validation_result.warnings,
                    validation_time=snapshot.validation_result.validation_time,
                    validation_level=snapshot.validation_result.validation_level.value
                )
            
            history_data.append(snapshot_data.dict())
        
        return JSONResponse({
            "history": history_data,
            "total_returned": len(history_data),
            "timestamp": datetime.now().isoformat()
        })


@router.get("/changes", summary="Get configuration change events")
async def get_config_changes(
    limit: int = Query(20, ge=1, le=100, description="Number of change events to return"),
    change_type: Optional[str] = Query(None, description="Filter by change type")
):
    """Get recent configuration change events"""
    async with TraceSpan("get_config_changes", SpanType.REQUEST, {
        "limit": str(limit),
        "change_type": change_type or "all"
    }):
        manager = await get_config_manager()
        events = manager.get_change_events(limit)
        
        # Apply filter if specified
        if change_type:
            try:
                filter_type = ConfigChangeType(change_type.lower())
                events = [e for e in events if e.change_type == filter_type]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid change type: {change_type}"
                )
        
        events_data = []
        for event in events:
            event_data = ConfigChangeEventModel(
                change_type=event.change_type.value,
                file_path=event.file_path,
                timestamp=event.timestamp,
                correlation_id=event.correlation_id,
                applied=event.applied,
                rollback_attempted=event.rollback_attempted
            )
            events_data.append(event_data.dict())
        
        return JSONResponse({
            "change_events": events_data,
            "total_returned": len(events_data),
            "available_change_types": [ct.value for ct in ConfigChangeType],
            "timestamp": datetime.now().isoformat()
        })


@router.post("/load", summary="Load configuration from file")
async def load_config_file(
    file_path: str = Query(..., description="Path to configuration file to load")
):
    """Load configuration from a file"""
    async with TraceSpan("load_config_file", SpanType.IO_OPERATION, {"file_path": file_path}):
        manager = await get_config_manager()
        
        # Validate file path
        path_obj = Path(file_path)
        if not path_obj.exists():
            raise HTTPException(status_code=404, detail=f"Configuration file not found: {file_path}")
        
        if not path_obj.is_file():
            raise HTTPException(status_code=400, detail=f"Path is not a file: {file_path}")
        
        # Load configuration
        success = await manager.load_config_file(file_path)
        
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Configuration loaded successfully from {file_path}",
                "file_path": file_path,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return JSONResponse({
                "success": False,
                "message": f"Failed to load configuration from {file_path}",
                "file_path": file_path,
                "timestamp": datetime.now().isoformat()
            }, status_code=500)


@router.post("/upload", summary="Upload and load configuration file")
async def upload_config_file(
    file: UploadFile = File(..., description="Configuration file to upload"),
    validate_only: bool = Query(False, description="Only validate, don't apply configuration")
):
    """Upload and optionally load a configuration file"""
    async with TraceSpan("upload_config_file", SpanType.IO_OPERATION, {
        "filename": file.filename,
        "validate_only": str(validate_only)
    }):
        # Validate file type
        if not file.filename.endswith(('.json', '.yaml', '.yml')):
            raise HTTPException(
                status_code=400,
                detail="Only JSON and YAML configuration files are supported"
            )
        
        try:
            # Read file content
            content = await file.read()
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                mode='w+b', 
                suffix=Path(file.filename).suffix,
                delete=False
            ) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            manager = await get_config_manager()
            
            if validate_only:
                # Just validate without applying
                try:
                    import json
                    import yaml
                    
                    # Parse content
                    if file.filename.endswith('.json'):
                        config_data = json.loads(content.decode('utf-8'))
                    else:
                        config_data = yaml.safe_load(content.decode('utf-8'))
                    
                    # Validate
                    result = await manager.validator.validate_config(config_data)
                    
                    return JSONResponse({
                        "validation_only": True,
                        "filename": file.filename,
                        "validation_result": ValidationResultModel(
                            is_valid=result.is_valid,
                            errors=result.errors,
                            warnings=result.warnings,
                            validation_time=result.validation_time,
                            validation_level=result.validation_level.value
                        ).dict(),
                        "timestamp": datetime.now().isoformat()
                    })
                    
                finally:
                    # Clean up temp file
                    Path(temp_file_path).unlink(missing_ok=True)
            
            else:
                # Load configuration
                success = await manager.load_config_file(temp_file_path)
                
                # Clean up temp file
                Path(temp_file_path).unlink(missing_ok=True)
                
                if success:
                    return JSONResponse({
                        "success": True,
                        "message": f"Configuration uploaded and loaded successfully from {file.filename}",
                        "filename": file.filename,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    return JSONResponse({
                        "success": False,
                        "message": f"Failed to load uploaded configuration from {file.filename}",
                        "filename": file.filename
                    }, status_code=500)
        
        except Exception as e:
            logger.error(f"Configuration upload failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/rollback", summary="Rollback to previous configuration")
async def rollback_configuration():
    """Rollback to the previous configuration version"""
    async with TraceSpan("rollback_configuration", SpanType.REQUEST):
        manager = await get_config_manager()
        
        if not manager.rollback_stack:
            raise HTTPException(
                status_code=400,
                detail="No previous configuration available for rollback"
            )
        
        success = await manager._rollback_configuration()
        
        if success:
            return JSONResponse({
                "success": True,
                "message": "Configuration rolled back to previous version",
                "rollback_stack_depth": len(manager.rollback_stack),
                "timestamp": datetime.now().isoformat()
            })
        else:
            return JSONResponse({
                "success": False,
                "message": "Configuration rollback failed"
            }, status_code=500)


@router.get("/schemas", summary="Get registered validation schemas")
async def get_validation_schemas():
    """Get all registered configuration validation schemas"""
    async with TraceSpan("get_validation_schemas", SpanType.REQUEST):
        manager = await get_config_manager()
        schemas = manager.validator.schemas
        
        return JSONResponse({
            "schemas": schemas,
            "schema_count": len(schemas),
            "registered_sections": list(schemas.keys()),
            "timestamp": datetime.now().isoformat()
        })


@router.post("/test/create-config", summary="Create test configuration (WARP TEST endpoint)")
async def create_test_config():
    """Create a test configuration for testing validation and hot reload"""
    async with TraceSpan("create_test_config", SpanType.REQUEST):
        test_config = {
            "api": {
                "host": "localhost",
                "port": 8000,
                "debug": True,
                "rate_limit": 1000,
                "cors_origins": ["*"],
                "ssl_enabled": False
            },
            "database": {
                "host": "localhost",
                "port": 5432,
                "database": "warp_test_db",
                "username": "warp_test_user",
                "password": "WARP_TEST_PASSWORD",
                "pool_size": 10,
                "max_overflow": 20,
                "timeout": 30.0
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file_path": "/tmp/warp_test.log",
                "max_bytes": 1048576,
                "backup_count": 5
            },
            "warp_test": {
                "enabled": True,
                "test_mode": "configuration_validation",
                "created_at": datetime.now().isoformat(),
                "features": ["validation", "hot_reload", "rollback"]
            }
        }
        
        # Create temporary test config file
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.yaml',
            delete=False,
            prefix='warp_test_config_'
        ) as temp_file:
            import yaml
            yaml.dump(test_config, temp_file, default_flow_style=False)
            temp_file_path = temp_file.name
        
        manager = await get_config_manager()
        
        # Load test configuration
        success = await manager.load_config_file(temp_file_path)
        
        return JSONResponse({
            "success": success,
            "message": "WARP TEST configuration created and loaded" if success else "WARP TEST configuration creation failed",
            "config_file_path": temp_file_path,
            "test_config_data": test_config,
            "validation_level": manager.validation_level.value,
            "timestamp": datetime.now().isoformat()
        })


@router.get("/test/validation-levels", summary="Test different validation levels")
async def test_validation_levels():
    """Test configuration validation at different levels"""
    async with TraceSpan("test_validation_levels", SpanType.REQUEST):
        # Test configuration with various issues
        test_configs = {
            "valid_config": {
                "api": {"host": "localhost", "port": 8000},
                "database": {"host": "db", "port": 5432, "database": "test"}
            },
            "invalid_types": {
                "api": {"host": "localhost", "port": "not_a_number"},
                "database": {"host": "db", "port": 5432, "database": "test"}
            },
            "missing_required": {
                "api": {"host": "localhost"},  # missing port
                "database": {"host": "db", "port": 5432}  # missing database
            },
            "security_issues": {
                "api": {"host": "localhost", "port": 8000},
                "database": {
                    "host": "db", 
                    "port": 5432, 
                    "database": "test",
                    "password": "secret123"  # sensitive data warning
                }
            }
        }
        
        manager = await get_config_manager()
        results = {}
        
        for config_name, config_data in test_configs.items():
            level_results = {}
            
            for level in ConfigValidationLevel:
                validation_result = await manager.validator.validate_config(config_data, level)
                level_results[level.value] = {
                    "is_valid": validation_result.is_valid,
                    "errors": validation_result.errors,
                    "warnings": validation_result.warnings,
                    "validation_time": validation_result.validation_time
                }
            
            results[config_name] = level_results
        
        return JSONResponse({
            "validation_test_results": results,
            "validation_levels_tested": [level.value for level in ConfigValidationLevel],
            "timestamp": datetime.now().isoformat()
        })


# Add router to main application
def setup_config_management_routes(app):
    """Setup configuration management routes on FastAPI app"""
    app.include_router(router)
    logger.info("WARP CONFIGURATION MANAGEMENT API routes configured")