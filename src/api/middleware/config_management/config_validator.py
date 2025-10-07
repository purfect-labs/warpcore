#!/usr/bin/env python3
"""
WARPCORE Configuration Validation and Hot Reloading System
Comprehensive configuration management with validation, hot reloading, and automatic rollback
"""

import asyncio
import json
import logging
import os
import time
import yaml
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Callable, Union
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import hashlib
import copy

from ..tracing.request_tracer import TraceSpan, SpanType, get_current_correlation_id
from ..resource_management import get_resource_manager, ResourceType


class ConfigValidationLevel(Enum):
    """Configuration validation levels"""
    BASIC = "basic"          # Basic type and structure validation
    STRICT = "strict"        # Strict validation with business rules
    PARANOID = "paranoid"    # Maximum validation including cross-references


class ConfigChangeType(Enum):
    """Types of configuration changes"""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
    PERMISSION_CHANGED = "permission_changed"


class ConfigSource(Enum):
    """Sources of configuration"""
    FILE = "file"
    ENVIRONMENT = "environment"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    RUNTIME = "runtime"


@dataclass
class ValidationResult:
    """Result of configuration validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validation_time: float = field(default_factory=time.time)
    validation_level: ConfigValidationLevel = ConfigValidationLevel.BASIC
    
    def add_error(self, message: str, field_path: str = ""):
        """Add validation error"""
        error_msg = f"{field_path}: {message}" if field_path else message
        self.errors.append(error_msg)
        self.is_valid = False
    
    def add_warning(self, message: str, field_path: str = ""):
        """Add validation warning"""
        warning_msg = f"{field_path}: {message}" if field_path else message
        self.warnings.append(warning_msg)


@dataclass
class ConfigSnapshot:
    """Snapshot of configuration state"""
    config_data: Dict[str, Any]
    checksum: str
    timestamp: float
    source: ConfigSource
    file_paths: List[str] = field(default_factory=list)
    validation_result: Optional[ValidationResult] = None
    
    def __post_init__(self):
        """Post-initialization setup"""
        if not self.checksum:
            self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate configuration checksum"""
        config_str = json.dumps(self.config_data, sort_keys=True, default=str)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]


@dataclass
class ConfigChangeEvent:
    """Configuration change event"""
    change_type: ConfigChangeType
    file_path: str
    old_snapshot: Optional[ConfigSnapshot]
    new_snapshot: Optional[ConfigSnapshot]
    timestamp: float = field(default_factory=time.time)
    correlation_id: Optional[str] = field(default_factory=get_current_correlation_id)
    applied: bool = False
    rollback_attempted: bool = False


class ConfigValidator:
    """Configuration validation engine"""
    
    def __init__(self):
        self.logger = logging.getLogger("config_validator")
        self.validators: Dict[str, Callable] = {}
        self.schemas: Dict[str, Dict] = {}
        self.required_fields: Dict[str, Set[str]] = defaultdict(set)
        self.field_types: Dict[str, Dict[str, type]] = defaultdict(dict)
        self.validation_rules: Dict[str, List[Callable]] = defaultdict(list)
    
    def register_schema(self, config_section: str, schema: Dict[str, Any]):
        """Register configuration schema for validation"""
        self.schemas[config_section] = schema
        
        # Extract required fields and types
        if 'required' in schema:
            self.required_fields[config_section].update(schema['required'])
        
        if 'properties' in schema:
            for field, field_schema in schema['properties'].items():
                if 'type' in field_schema:
                    python_type = self._json_type_to_python_type(field_schema['type'])
                    self.field_types[config_section][field] = python_type
    
    def register_validator(self, config_section: str, validator_func: Callable):
        """Register custom validator function"""
        self.validators[config_section] = validator_func
    
    def add_validation_rule(self, config_section: str, rule_func: Callable):
        """Add validation rule for a configuration section"""
        self.validation_rules[config_section].append(rule_func)
    
    def _json_type_to_python_type(self, json_type: str) -> type:
        """Convert JSON schema type to Python type"""
        type_mapping = {
            'string': str,
            'integer': int,
            'number': float,
            'boolean': bool,
            'array': list,
            'object': dict,
            'null': type(None)
        }
        return type_mapping.get(json_type, str)
    
    async def validate_config(
        self, 
        config_data: Dict[str, Any], 
        level: ConfigValidationLevel = ConfigValidationLevel.BASIC
    ) -> ValidationResult:
        """Validate configuration data"""
        async with TraceSpan("validate_config", SpanType.COMPUTATION, {
            "validation_level": level.value,
            "config_sections": str(len(config_data))
        }):
            result = ValidationResult(is_valid=True, validation_level=level)
            
            try:
                # Basic structure validation
                await self._validate_structure(config_data, result)
                
                # Schema validation
                await self._validate_schemas(config_data, result)
                
                # Custom validator functions
                await self._run_custom_validators(config_data, result)
                
                # Validation rules
                await self._run_validation_rules(config_data, result)
                
                # Advanced validation for higher levels
                if level in [ConfigValidationLevel.STRICT, ConfigValidationLevel.PARANOID]:
                    await self._validate_business_rules(config_data, result)
                
                if level == ConfigValidationLevel.PARANOID:
                    await self._validate_cross_references(config_data, result)
                    await self._validate_security_constraints(config_data, result)
                
            except Exception as e:
                result.add_error(f"Validation failed with exception: {str(e)}")
                self.logger.error(f"Configuration validation error: {str(e)}")
            
            return result
    
    async def _validate_structure(self, config_data: Dict[str, Any], result: ValidationResult):
        """Validate basic configuration structure"""
        if not isinstance(config_data, dict):
            result.add_error("Configuration must be a dictionary/object")
            return
        
        # Check for empty configuration
        if not config_data:
            result.add_warning("Configuration is empty")
    
    async def _validate_schemas(self, config_data: Dict[str, Any], result: ValidationResult):
        """Validate against registered schemas"""
        for section_name, section_data in config_data.items():
            if section_name not in self.schemas:
                result.add_warning(f"No schema registered for section '{section_name}'")
                continue
            
            schema = self.schemas[section_name]
            await self._validate_section_schema(section_name, section_data, schema, result)
    
    async def _validate_section_schema(
        self, 
        section_name: str, 
        section_data: Any, 
        schema: Dict, 
        result: ValidationResult
    ):
        """Validate a configuration section against its schema"""
        # Check required fields
        if 'required' in schema and isinstance(section_data, dict):
            for required_field in schema['required']:
                if required_field not in section_data:
                    result.add_error(f"Required field '{required_field}' missing", section_name)
        
        # Check field types
        if 'properties' in schema and isinstance(section_data, dict):
            for field_name, field_value in section_data.items():
                if field_name in schema['properties']:
                    field_schema = schema['properties'][field_name]
                    await self._validate_field(
                        f"{section_name}.{field_name}", 
                        field_value, 
                        field_schema, 
                        result
                    )
    
    async def _validate_field(
        self, 
        field_path: str, 
        field_value: Any, 
        field_schema: Dict, 
        result: ValidationResult
    ):
        """Validate individual field"""
        # Type validation
        if 'type' in field_schema:
            expected_type = self._json_type_to_python_type(field_schema['type'])
            if not isinstance(field_value, expected_type):
                result.add_error(
                    f"Expected {expected_type.__name__}, got {type(field_value).__name__}",
                    field_path
                )
        
        # Range validation
        if isinstance(field_value, (int, float)):
            if 'minimum' in field_schema and field_value < field_schema['minimum']:
                result.add_error(f"Value {field_value} below minimum {field_schema['minimum']}", field_path)
            if 'maximum' in field_schema and field_value > field_schema['maximum']:
                result.add_error(f"Value {field_value} above maximum {field_schema['maximum']}", field_path)
        
        # String validation
        if isinstance(field_value, str):
            if 'minLength' in field_schema and len(field_value) < field_schema['minLength']:
                result.add_error(f"String too short (min: {field_schema['minLength']})", field_path)
            if 'maxLength' in field_schema and len(field_value) > field_schema['maxLength']:
                result.add_error(f"String too long (max: {field_schema['maxLength']})", field_path)
            if 'pattern' in field_schema:
                import re
                if not re.match(field_schema['pattern'], field_value):
                    result.add_error(f"String doesn't match pattern", field_path)
        
        # Enum validation
        if 'enum' in field_schema and field_value not in field_schema['enum']:
            result.add_error(f"Value must be one of: {field_schema['enum']}", field_path)
    
    async def _run_custom_validators(self, config_data: Dict[str, Any], result: ValidationResult):
        """Run custom validator functions"""
        for section_name, validator_func in self.validators.items():
            if section_name in config_data:
                try:
                    if asyncio.iscoroutinefunction(validator_func):
                        await validator_func(config_data[section_name], result, section_name)
                    else:
                        validator_func(config_data[section_name], result, section_name)
                except Exception as e:
                    result.add_error(f"Custom validator failed: {str(e)}", section_name)
    
    async def _run_validation_rules(self, config_data: Dict[str, Any], result: ValidationResult):
        """Run validation rules"""
        for section_name, rules in self.validation_rules.items():
            if section_name in config_data:
                for rule_func in rules:
                    try:
                        if asyncio.iscoroutinefunction(rule_func):
                            await rule_func(config_data[section_name], result, section_name)
                        else:
                            rule_func(config_data[section_name], result, section_name)
                    except Exception as e:
                        result.add_error(f"Validation rule failed: {str(e)}", section_name)
    
    async def _validate_business_rules(self, config_data: Dict[str, Any], result: ValidationResult):
        """Validate business-specific rules"""
        # Database configuration validation
        if 'database' in config_data:
            db_config = config_data['database']
            if isinstance(db_config, dict):
                # Check connection pool settings
                if 'pool_size' in db_config and 'max_overflow' in db_config:
                    pool_size = db_config.get('pool_size', 0)
                    max_overflow = db_config.get('max_overflow', 0)
                    if pool_size + max_overflow > 100:
                        result.add_warning("High database connection pool configuration may cause resource issues")
        
        # API configuration validation  
        if 'api' in config_data:
            api_config = config_data['api']
            if isinstance(api_config, dict):
                # Check rate limiting
                if 'rate_limit' in api_config:
                    rate_limit = api_config.get('rate_limit', 0)
                    if rate_limit > 10000:
                        result.add_warning("Very high rate limit may impact system performance")
    
    async def _validate_cross_references(self, config_data: Dict[str, Any], result: ValidationResult):
        """Validate cross-references between configuration sections"""
        # Validate provider references
        if 'controllers' in config_data and 'providers' in config_data:
            controllers = config_data['controllers']
            providers = config_data['providers']
            
            if isinstance(controllers, dict) and isinstance(providers, dict):
                for controller_name, controller_config in controllers.items():
                    if isinstance(controller_config, dict) and 'provider' in controller_config:
                        provider_ref = controller_config['provider']
                        if provider_ref not in providers:
                            result.add_error(
                                f"Controller '{controller_name}' references unknown provider '{provider_ref}'"
                            )
    
    async def _validate_security_constraints(self, config_data: Dict[str, Any], result: ValidationResult):
        """Validate security-related constraints"""
        # Check for sensitive data in configuration
        sensitive_patterns = ['password', 'secret', 'key', 'token', 'credential']
        
        def check_sensitive_data(data: Any, path: str = ""):
            if isinstance(data, dict):
                for key, value in data.items():
                    current_path = f"{path}.{key}" if path else key
                    if any(pattern in key.lower() for pattern in sensitive_patterns):
                        if isinstance(value, str) and len(value) > 0:
                            result.add_warning(f"Sensitive data detected in configuration", current_path)
                    check_sensitive_data(value, current_path)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    check_sensitive_data(item, f"{path}[{i}]")
        
        check_sensitive_data(config_data)


class ConfigFileWatcher(FileSystemEventHandler):
    """File system watcher for configuration files"""
    
    def __init__(self, config_manager: 'ConfigManager'):
        self.config_manager = config_manager
        self.logger = logging.getLogger("config_file_watcher")
        self.debounce_delay = 1.0  # 1 second debounce
        self.pending_changes: Dict[str, float] = {}
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
        
        self._handle_change(ConfigChangeType.MODIFIED, event.src_path)
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
        
        self._handle_change(ConfigChangeType.CREATED, event.src_path)
    
    def on_deleted(self, event):
        """Handle file deletion events"""
        if event.is_directory:
            return
        
        self._handle_change(ConfigChangeType.DELETED, event.src_path)
    
    def on_moved(self, event):
        """Handle file move/rename events"""
        if event.is_directory:
            return
        
        self._handle_change(ConfigChangeType.RENAMED, event.dest_path)
    
    def _handle_change(self, change_type: ConfigChangeType, file_path: str):
        """Handle configuration file change with debouncing"""
        current_time = time.time()
        
        # Debounce rapid changes
        if file_path in self.pending_changes:
            if current_time - self.pending_changes[file_path] < self.debounce_delay:
                return
        
        self.pending_changes[file_path] = current_time
        
        # Schedule change processing
        asyncio.create_task(
            self.config_manager.handle_file_change(change_type, file_path)
        )


class ConfigManager:
    """Comprehensive configuration management system"""
    
    def __init__(self):
        self.logger = logging.getLogger("config_manager")
        
        # Core components
        self.validator = ConfigValidator()
        self.file_watcher: Optional[Observer] = None
        
        # Configuration state
        self.current_config: Optional[ConfigSnapshot] = None
        self.config_history: deque = deque(maxlen=50)  # Keep last 50 configurations
        self.watched_files: Set[str] = set()
        self.watched_directories: Set[str] = set()
        
        # Change management
        self.change_events: deque = deque(maxlen=1000)
        self.rollback_stack: List[ConfigSnapshot] = []
        self.max_rollback_depth = 10
        
        # Settings
        self.validation_level = ConfigValidationLevel.STRICT
        self.auto_reload_enabled = True
        self.auto_rollback_enabled = True
        self.reload_delay = 2.0  # seconds
        
        # Callbacks
        self.change_callbacks: List[Callable] = []
        self.validation_callbacks: List[Callable] = []
        
        # Statistics
        self.stats = {
            'configs_loaded': 0,
            'validations_performed': 0,
            'validation_failures': 0,
            'hot_reloads': 0,
            'rollbacks': 0,
            'file_changes_detected': 0
        }
    
    async def initialize(self, config_paths: List[str] = None):
        """Initialize configuration manager"""
        self.logger.info("🚀 WARP CONFIG: Initializing configuration management")
        
        # Setup default validation schemas
        await self._setup_default_schemas()
        
        # Load initial configuration
        if config_paths:
            for config_path in config_paths:
                await self.load_config_file(config_path)
        
        # Start file watching if auto-reload enabled
        if self.auto_reload_enabled:
            await self._start_file_watching()
        
        self.logger.info("✅ WARP CONFIG: Configuration management initialized")
    
    async def _setup_default_schemas(self):
        """Setup default validation schemas"""
        # Database configuration schema
        db_schema = {
            "type": "object",
            "required": ["host", "port", "database"],
            "properties": {
                "host": {"type": "string", "minLength": 1},
                "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                "database": {"type": "string", "minLength": 1},
                "username": {"type": "string"},
                "password": {"type": "string"},
                "pool_size": {"type": "integer", "minimum": 1, "maximum": 100},
                "max_overflow": {"type": "integer", "minimum": 0, "maximum": 100},
                "timeout": {"type": "number", "minimum": 0.1, "maximum": 300}
            }
        }
        self.validator.register_schema("database", db_schema)
        
        # API configuration schema
        api_schema = {
            "type": "object",
            "required": ["host", "port"],
            "properties": {
                "host": {"type": "string", "minLength": 1},
                "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                "debug": {"type": "boolean"},
                "rate_limit": {"type": "integer", "minimum": 1, "maximum": 100000},
                "cors_origins": {"type": "array", "items": {"type": "string"}},
                "ssl_enabled": {"type": "boolean"}
            }
        }
        self.validator.register_schema("api", api_schema)
        
        # Logging configuration schema
        logging_schema = {
            "type": "object",
            "properties": {
                "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
                "format": {"type": "string", "minLength": 1},
                "file_path": {"type": "string"},
                "max_bytes": {"type": "integer", "minimum": 1024},
                "backup_count": {"type": "integer", "minimum": 1, "maximum": 100}
            }
        }
        self.validator.register_schema("logging", logging_schema)
    
    async def load_config_file(self, file_path: str) -> bool:
        """Load configuration from file"""
        async with TraceSpan("load_config_file", SpanType.IO_OPERATION, {"file_path": file_path}):
            try:
                path_obj = Path(file_path)
                if not path_obj.exists():
                    self.logger.error(f"Configuration file not found: {file_path}")
                    return False
                
                # Read file content
                with open(path_obj, 'r', encoding='utf-8') as f:
                    if path_obj.suffix.lower() in ['.yaml', '.yml']:
                        config_data = yaml.safe_load(f)
                    elif path_obj.suffix.lower() == '.json':
                        config_data = json.load(f)
                    else:
                        self.logger.error(f"Unsupported configuration file format: {file_path}")
                        return False
                
                # Create snapshot
                snapshot = ConfigSnapshot(
                    config_data=config_data or {},
                    checksum="",
                    timestamp=time.time(),
                    source=ConfigSource.FILE,
                    file_paths=[file_path]
                )
                
                # Validate configuration
                validation_result = await self.validator.validate_config(
                    config_data, 
                    self.validation_level
                )
                snapshot.validation_result = validation_result
                
                self.stats['configs_loaded'] += 1
                self.stats['validations_performed'] += 1
                
                if not validation_result.is_valid:
                    self.stats['validation_failures'] += 1
                    self.logger.error(f"Configuration validation failed for {file_path}")
                    for error in validation_result.errors:
                        self.logger.error(f"  - {error}")
                    
                    if not self.auto_rollback_enabled:
                        return False
                
                # Apply configuration if valid or rollback enabled
                success = await self._apply_config_snapshot(snapshot)
                
                if success:
                    # Add to watch list
                    self.watched_files.add(file_path)
                    self.watched_directories.add(str(path_obj.parent))
                    
                    self.logger.info(f"✅ WARP CONFIG: Loaded configuration from {file_path}")
                    
                    if validation_result.warnings:
                        for warning in validation_result.warnings:
                            self.logger.warning(f"Config warning: {warning}")
                
                return success
                
            except Exception as e:
                self.logger.error(f"Failed to load configuration from {file_path}: {str(e)}")
                return False
    
    async def _apply_config_snapshot(self, snapshot: ConfigSnapshot) -> bool:
        """Apply configuration snapshot"""
        try:
            # Store previous config for rollback
            if self.current_config and snapshot.validation_result and snapshot.validation_result.is_valid:
                self.rollback_stack.append(self.current_config)
                if len(self.rollback_stack) > self.max_rollback_depth:
                    self.rollback_stack.pop(0)
            
            # Apply new configuration
            old_config = self.current_config
            self.current_config = snapshot
            self.config_history.append(snapshot)
            
            # Notify change callbacks
            for callback in self.change_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(old_config, snapshot)
                    else:
                        callback(old_config, snapshot)
                except Exception as e:
                    self.logger.error(f"Configuration change callback failed: {str(e)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply configuration snapshot: {str(e)}")
            return False
    
    async def handle_file_change(self, change_type: ConfigChangeType, file_path: str):
        """Handle configuration file change"""
        async with TraceSpan("handle_file_change", SpanType.IO_OPERATION, {
            "change_type": change_type.value,
            "file_path": file_path
        }):
            if file_path not in self.watched_files:
                return  # Not a watched configuration file
            
            self.stats['file_changes_detected'] += 1
            self.logger.info(f"📝 WARP CONFIG: File change detected - {change_type.value}: {file_path}")
            
            # Add delay to allow file write to complete
            await asyncio.sleep(self.reload_delay)
            
            old_snapshot = self.current_config
            
            if change_type == ConfigChangeType.DELETED:
                # Handle file deletion
                change_event = ConfigChangeEvent(
                    change_type=change_type,
                    file_path=file_path,
                    old_snapshot=old_snapshot,
                    new_snapshot=None
                )
                self.change_events.append(change_event)
                
                self.logger.warning(f"Configuration file deleted: {file_path}")
                # Could trigger fallback to default config or previous version
                
            else:
                # Reload configuration
                success = await self.load_config_file(file_path)
                
                change_event = ConfigChangeEvent(
                    change_type=change_type,
                    file_path=file_path,
                    old_snapshot=old_snapshot,
                    new_snapshot=self.current_config,
                    applied=success
                )
                self.change_events.append(change_event)
                
                if success:
                    self.stats['hot_reloads'] += 1
                    self.logger.info(f"🔥 WARP CONFIG: Hot reload successful for {file_path}")
                else:
                    self.logger.error(f"❌ WARP CONFIG: Hot reload failed for {file_path}")
                    
                    # Attempt rollback if enabled
                    if self.auto_rollback_enabled and self.rollback_stack:
                        await self._rollback_configuration()
                        change_event.rollback_attempted = True
    
    async def _rollback_configuration(self) -> bool:
        """Rollback to previous configuration"""
        if not self.rollback_stack:
            self.logger.error("No configuration available for rollback")
            return False
        
        try:
            # Get previous configuration
            previous_config = self.rollback_stack.pop()
            
            # Apply rollback
            old_config = self.current_config
            self.current_config = previous_config
            
            self.stats['rollbacks'] += 1
            self.logger.info("🔄 WARP CONFIG: Configuration rolled back to previous version")
            
            # Notify callbacks about rollback
            for callback in self.change_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(old_config, previous_config)
                    else:
                        callback(old_config, previous_config)
                except Exception as e:
                    self.logger.error(f"Rollback callback failed: {str(e)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration rollback failed: {str(e)}")
            return False
    
    async def _start_file_watching(self):
        """Start file system watching"""
        if self.file_watcher:
            return
        
        try:
            self.file_watcher = Observer()
            event_handler = ConfigFileWatcher(self)
            
            # Watch all directories containing configuration files
            for directory in self.watched_directories:
                self.file_watcher.schedule(event_handler, directory, recursive=False)
            
            self.file_watcher.start()
            self.logger.info(f"👁️  WARP CONFIG: File watching started for {len(self.watched_directories)} directories")
            
        except Exception as e:
            self.logger.error(f"Failed to start file watching: {str(e)}")
    
    async def stop_file_watching(self):
        """Stop file system watching"""
        if self.file_watcher:
            self.file_watcher.stop()
            self.file_watcher.join()
            self.file_watcher = None
            self.logger.info("🛑 WARP CONFIG: File watching stopped")
    
    def register_change_callback(self, callback: Callable):
        """Register callback for configuration changes"""
        self.change_callbacks.append(callback)
    
    def register_validation_callback(self, callback: Callable):
        """Register callback for validation events"""
        self.validation_callbacks.append(callback)
    
    async def validate_current_config(self) -> Optional[ValidationResult]:
        """Validate current configuration"""
        if not self.current_config:
            return None
        
        result = await self.validator.validate_config(
            self.current_config.config_data,
            self.validation_level
        )
        
        self.stats['validations_performed'] += 1
        if not result.is_valid:
            self.stats['validation_failures'] += 1
        
        return result
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key path"""
        if not self.current_config:
            return default
        
        keys = key_path.split('.')
        value = self.current_config.config_data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_config_section(self, section_name: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        if not self.current_config:
            return {}
        
        return self.current_config.config_data.get(section_name, {})
    
    def get_current_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        if not self.current_config:
            return {}
        
        return copy.deepcopy(self.current_config.config_data)
    
    def get_config_history(self, limit: int = 10) -> List[ConfigSnapshot]:
        """Get configuration history"""
        history = list(self.config_history)
        return history[-limit:] if limit > 0 else history
    
    def get_change_events(self, limit: int = 50) -> List[ConfigChangeEvent]:
        """Get recent configuration change events"""
        events = list(self.change_events)
        return events[-limit:] if limit > 0 else events
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get configuration management statistics"""
        return {
            **self.stats,
            'current_config_checksum': self.current_config.checksum if self.current_config else None,
            'watched_files_count': len(self.watched_files),
            'rollback_stack_depth': len(self.rollback_stack),
            'validation_level': self.validation_level.value,
            'auto_reload_enabled': self.auto_reload_enabled,
            'auto_rollback_enabled': self.auto_rollback_enabled,
            'file_watching_active': self.file_watcher is not None and self.file_watcher.is_alive()
        }
    
    async def shutdown(self):
        """Shutdown configuration manager"""
        self.logger.info("🛑 WARP CONFIG: Shutting down configuration management")
        
        await self.stop_file_watching()
        
        # Clear callbacks
        self.change_callbacks.clear()
        self.validation_callbacks.clear()
        
        self.logger.info("✅ WARP CONFIG: Configuration management shutdown complete")


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


async def get_config_manager() -> ConfigManager:
    """Get or create the global configuration manager"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


async def shutdown_config_manager():
    """Shutdown the global configuration manager"""
    global _config_manager
    if _config_manager is not None:
        await _config_manager.shutdown()
        _config_manager = None