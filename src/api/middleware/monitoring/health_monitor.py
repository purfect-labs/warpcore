#!/usr/bin/env python3
"""
WARPCORE Health Monitoring System
Comprehensive health checks, dependency monitoring, and alerting
"""

import asyncio
import logging
import time
import psutil
import gc
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Awaitable, Set
from abc import ABC, abstractmethod
import json
import traceback


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    component_name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    duration: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    dependencies: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class Alert:
    """Health monitoring alert"""
    id: str
    component: str
    level: AlertLevel
    message: str
    timestamp: str
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_timestamp: Optional[str] = None


class HealthChecker(ABC):
    """Base class for health checkers"""
    
    def __init__(self, name: str):
        self.name = name
        self.dependencies = []
        self.last_check = None
        self.check_count = 0
        self.failure_count = 0
    
    @abstractmethod
    async def check_health(self) -> HealthCheckResult:
        """Perform health check"""
        pass
    
    def add_dependency(self, dependency_name: str):
        """Add a dependency that this component requires"""
        if dependency_name not in self.dependencies:
            self.dependencies.append(dependency_name)


class SystemResourcesChecker(HealthChecker):
    """Check system resources (CPU, memory, disk)"""
    
    def __init__(self):
        super().__init__("system_resources")
        self.cpu_threshold = 80.0      # CPU usage percentage
        self.memory_threshold = 85.0   # Memory usage percentage  
        self.disk_threshold = 90.0     # Disk usage percentage
    
    async def check_health(self) -> HealthCheckResult:
        """Check system resource health"""
        start_time = time.time()
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage for current directory
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Determine overall status
            status = HealthStatus.HEALTHY
            messages = []
            
            if cpu_percent > self.cpu_threshold:
                status = HealthStatus.DEGRADED if cpu_percent < 90 else HealthStatus.UNHEALTHY
                messages.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            if memory_percent > self.memory_threshold:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.DEGRADED if memory_percent < 95 else HealthStatus.UNHEALTHY
                elif memory_percent >= 95:
                    status = HealthStatus.UNHEALTHY
                messages.append(f"High memory usage: {memory_percent:.1f}%")
            
            if disk_percent > self.disk_threshold:
                if status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]:
                    status = HealthStatus.UNHEALTHY if disk_percent >= 95 else HealthStatus.DEGRADED
                messages.append(f"High disk usage: {disk_percent:.1f}%")
            
            message = "System resources healthy"
            if messages:
                message = "; ".join(messages)
            
            return HealthCheckResult(
                component_name=self.name,
                status=status,
                message=message,
                duration=time.time() - start_time,
                details={
                    "cpu_usage_percent": round(cpu_percent, 1),
                    "memory_usage_percent": round(memory_percent, 1),
                    "disk_usage_percent": round(disk_percent, 1),
                    "available_memory_mb": round(memory.available / (1024 * 1024), 1),
                    "available_disk_gb": round(disk.free / (1024 ** 3), 1)
                },
                metrics={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                component_name=self.name,
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check system resources: {e}",
                duration=time.time() - start_time,
                details={"error": str(e)}
            )


class CircuitBreakerChecker(HealthChecker):
    """Check circuit breaker health across the system"""
    
    def __init__(self, circuit_breaker_registry):
        super().__init__("circuit_breakers")
        self.circuit_breaker_registry = circuit_breaker_registry
    
    async def check_health(self) -> HealthCheckResult:
        """Check circuit breaker health"""
        start_time = time.time()
        
        try:
            if not self.circuit_breaker_registry:
                return HealthCheckResult(
                    component_name=self.name,
                    status=HealthStatus.UNKNOWN,
                    message="Circuit breaker registry not available",
                    duration=time.time() - start_time
                )
            
            health_summary = self.circuit_breaker_registry.get_health_summary()
            all_statuses = self.circuit_breaker_registry.get_all_status()
            
            status = HealthStatus.HEALTHY
            message = f"All {health_summary['total_breakers']} circuit breakers healthy"
            
            if health_summary['overall_health'] == 'critical':
                status = HealthStatus.CRITICAL
                message = f"{health_summary['failed_breakers']} circuit breakers failed"
            elif health_summary['overall_health'] == 'degraded':
                status = HealthStatus.DEGRADED
                message = f"{health_summary['degraded_breakers']} circuit breakers degraded"
            
            # Count breakers by state
            breaker_states = {}
            for breaker_status in all_statuses.values():
                state = breaker_status['state']
                breaker_states[state] = breaker_states.get(state, 0) + 1
            
            return HealthCheckResult(
                component_name=self.name,
                status=status,
                message=message,
                duration=time.time() - start_time,
                details={
                    "total_breakers": health_summary['total_breakers'],
                    "healthy_breakers": health_summary['healthy_breakers'],
                    "degraded_breakers": health_summary['degraded_breakers'],
                    "failed_breakers": health_summary['failed_breakers'],
                    "breaker_states": breaker_states
                },
                metrics={
                    "total_breakers": health_summary['total_breakers'],
                    "healthy_ratio": health_summary['healthy_breakers'] / max(1, health_summary['total_breakers'])
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                component_name=self.name,
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check circuit breakers: {e}",
                duration=time.time() - start_time,
                details={"error": str(e)}
            )


class DatabaseChecker(HealthChecker):
    """Check database connectivity and health"""
    
    def __init__(self, connection_func: Callable[[], Awaitable[bool]] = None):
        super().__init__("database")
        self.connection_func = connection_func
        self.query_timeout = 5.0
    
    async def check_health(self) -> HealthCheckResult:
        """Check database health"""
        start_time = time.time()
        
        try:
            if not self.connection_func:
                return HealthCheckResult(
                    component_name=self.name,
                    status=HealthStatus.UNKNOWN,
                    message="No database connection function provided",
                    duration=time.time() - start_time
                )
            
            # Test database connectivity with timeout
            try:
                connected = await asyncio.wait_for(
                    self.connection_func(),
                    timeout=self.query_timeout
                )
                
                if connected:
                    return HealthCheckResult(
                        component_name=self.name,
                        status=HealthStatus.HEALTHY,
                        message="Database connection successful",
                        duration=time.time() - start_time,
                        details={"connected": True, "response_time": time.time() - start_time},
                        metrics={"response_time": time.time() - start_time}
                    )
                else:
                    return HealthCheckResult(
                        component_name=self.name,
                        status=HealthStatus.UNHEALTHY,
                        message="Database connection failed",
                        duration=time.time() - start_time,
                        details={"connected": False}
                    )
                    
            except asyncio.TimeoutError:
                return HealthCheckResult(
                    component_name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Database connection timed out after {self.query_timeout}s",
                    duration=time.time() - start_time,
                    details={"timeout": True, "timeout_seconds": self.query_timeout}
                )
                
        except Exception as e:
            return HealthCheckResult(
                component_name=self.name,
                status=HealthStatus.UNKNOWN,
                message=f"Database health check error: {e}",
                duration=time.time() - start_time,
                details={"error": str(e)}
            )


class ExternalServiceChecker(HealthChecker):
    """Check external service availability"""
    
    def __init__(self, service_name: str, health_url: str, timeout: float = 10.0):
        super().__init__(f"external_service_{service_name}")
        self.service_name = service_name
        self.health_url = health_url
        self.timeout = timeout
    
    async def check_health(self) -> HealthCheckResult:
        """Check external service health"""
        start_time = time.time()
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(self.health_url) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        return HealthCheckResult(
                            component_name=self.name,
                            status=HealthStatus.HEALTHY,
                            message=f"{self.service_name} is healthy",
                            duration=response_time,
                            details={
                                "service_name": self.service_name,
                                "url": self.health_url,
                                "status_code": response.status,
                                "response_time": response_time
                            },
                            metrics={"response_time": response_time}
                        )
                    else:
                        return HealthCheckResult(
                            component_name=self.name,
                            status=HealthStatus.UNHEALTHY,
                            message=f"{self.service_name} returned status {response.status}",
                            duration=response_time,
                            details={
                                "service_name": self.service_name,
                                "url": self.health_url,
                                "status_code": response.status
                            }
                        )
                        
        except asyncio.TimeoutError:
            return HealthCheckResult(
                component_name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"{self.service_name} health check timed out",
                duration=time.time() - start_time,
                details={"timeout": True, "timeout_seconds": self.timeout}
            )
            
        except Exception as e:
            return HealthCheckResult(
                component_name=self.name,
                status=HealthStatus.UNKNOWN,
                message=f"{self.service_name} health check failed: {e}",
                duration=time.time() - start_time,
                details={"error": str(e)}
            )


class HealthMonitor:
    """
    Comprehensive health monitoring system
    """
    
    def __init__(self):
        self.checkers: Dict[str, HealthChecker] = {}
        self.check_results: Dict[str, HealthCheckResult] = {}
        self.alerts: List[Alert] = []
        self.alert_handlers: List[Callable[[Alert], Awaitable[None]]] = []
        
        self.logger = logging.getLogger("health_monitor")
        self.monitoring_active = False
        self.check_interval = 30.0  # seconds
        self.alert_cooldown = 300.0  # 5 minutes
        self.last_alerts: Dict[str, float] = {}
        
        # Overall system health tracking
        self.system_status = HealthStatus.UNKNOWN
        self.system_start_time = time.time()
        
        # Register default system checkers
        self._register_default_checkers()
    
    def _register_default_checkers(self):
        """Register default health checkers"""
        # System resources checker
        self.register_checker(SystemResourcesChecker())
        
        # Circuit breaker checker (if available)
        try:
            from ...middleware.resilience.circuit_breaker import get_circuit_breaker_registry
            cb_registry = get_circuit_breaker_registry()
            self.register_checker(CircuitBreakerChecker(cb_registry))
        except ImportError:
            self.logger.warning("Circuit breaker registry not available for health monitoring")
    
    def register_checker(self, checker: HealthChecker):
        """Register a health checker"""
        self.checkers[checker.name] = checker
        self.logger.info(f"Registered health checker: {checker.name}")
    
    def register_alert_handler(self, handler: Callable[[Alert], Awaitable[None]]):
        """Register an alert handler"""
        self.alert_handlers.append(handler)
        self.logger.info("Registered alert handler")
    
    async def check_all_health(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks"""
        results = {}
        
        # Run all checkers concurrently
        check_tasks = []
        for name, checker in self.checkers.items():
            task = asyncio.create_task(self._run_single_check(checker))
            check_tasks.append((name, task))
        
        # Collect results
        for name, task in check_tasks:
            try:
                result = await task
                results[name] = result
                self.check_results[name] = result
            except Exception as e:
                error_result = HealthCheckResult(
                    component_name=name,
                    status=HealthStatus.UNKNOWN,
                    message=f"Health check failed: {e}",
                    details={"error": str(e), "traceback": traceback.format_exc()}
                )
                results[name] = error_result
                self.check_results[name] = error_result
        
        # Update overall system health
        self._update_system_status(results)
        
        # Check for alerts
        await self._process_alerts(results)
        
        return results
    
    async def _run_single_check(self, checker: HealthChecker) -> HealthCheckResult:
        """Run a single health check with error handling"""
        checker.check_count += 1
        
        try:
            result = await checker.check_health()
            checker.last_check = time.time()
            
            if result.status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
                checker.failure_count += 1
            
            return result
            
        except Exception as e:
            checker.failure_count += 1
            self.logger.error(f"Health check failed for {checker.name}: {e}")
            raise
    
    def _update_system_status(self, results: Dict[str, HealthCheckResult]):
        """Update overall system health status"""
        if not results:
            self.system_status = HealthStatus.UNKNOWN
            return
        
        status_counts = {status: 0 for status in HealthStatus}
        
        for result in results.values():
            status_counts[result.status] += 1
        
        total_checks = len(results)
        
        # Determine overall status based on component health
        if status_counts[HealthStatus.CRITICAL] > 0:
            self.system_status = HealthStatus.CRITICAL
        elif status_counts[HealthStatus.UNHEALTHY] > total_checks * 0.3:  # More than 30% unhealthy
            self.system_status = HealthStatus.UNHEALTHY
        elif status_counts[HealthStatus.UNHEALTHY] > 0 or status_counts[HealthStatus.DEGRADED] > 0:
            self.system_status = HealthStatus.DEGRADED
        elif status_counts[HealthStatus.HEALTHY] == total_checks:
            self.system_status = HealthStatus.HEALTHY
        else:
            self.system_status = HealthStatus.UNKNOWN
    
    async def _process_alerts(self, results: Dict[str, HealthCheckResult]):
        """Process health check results and generate alerts"""
        current_time = time.time()
        
        for name, result in results.items():
            # Skip if result is healthy
            if result.status == HealthStatus.HEALTHY:
                continue
            
            # Check cooldown period
            last_alert_time = self.last_alerts.get(name, 0)
            if current_time - last_alert_time < self.alert_cooldown:
                continue
            
            # Determine alert level
            alert_level = AlertLevel.INFO
            if result.status == HealthStatus.CRITICAL:
                alert_level = AlertLevel.CRITICAL
            elif result.status == HealthStatus.UNHEALTHY:
                alert_level = AlertLevel.ERROR
            elif result.status == HealthStatus.DEGRADED:
                alert_level = AlertLevel.WARNING
            
            # Create alert
            alert = Alert(
                id=f"{name}_{int(current_time)}",
                component=name,
                level=alert_level,
                message=f"Component {name} is {result.status.value}: {result.message}",
                timestamp=datetime.now().isoformat(),
                details={
                    "status": result.status.value,
                    "check_duration": result.duration,
                    "details": result.details,
                    "metrics": result.metrics
                }
            )
            
            self.alerts.append(alert)
            self.last_alerts[name] = current_time
            
            # Send alert to handlers
            await self._send_alert(alert)
    
    async def _send_alert(self, alert: Alert):
        """Send alert to all registered handlers"""
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler failed: {e}")
    
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.logger.info(f"Starting health monitoring with {self.check_interval}s interval")
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        self.logger.info("Stopped health monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                await self.check_all_health()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(self.check_interval)
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        uptime = time.time() - self.system_start_time
        
        # Calculate component health distribution
        status_distribution = {status.value: 0 for status in HealthStatus}
        for result in self.check_results.values():
            status_distribution[result.status.value] += 1
        
        # Get recent alerts
        recent_alerts = [
            {
                "id": alert.id,
                "component": alert.component,
                "level": alert.level.value,
                "message": alert.message,
                "timestamp": alert.timestamp,
                "resolved": alert.resolved
            }
            for alert in self.alerts[-10:]  # Last 10 alerts
        ]
        
        # Aggregate metrics from all checkers
        aggregated_metrics = {}
        for name, result in self.check_results.items():
            for metric_name, metric_value in result.metrics.items():
                key = f"{name}_{metric_name}"
                aggregated_metrics[key] = metric_value
        
        return {
            "overall_status": self.system_status.value,
            "uptime_seconds": round(uptime, 1),
            "uptime_human": self._format_duration(uptime),
            "monitoring_active": self.monitoring_active,
            "check_interval_seconds": self.check_interval,
            "component_health": {
                "total_components": len(self.checkers),
                "status_distribution": status_distribution,
                "individual_results": {
                    name: {
                        "status": result.status.value,
                        "message": result.message,
                        "duration": result.duration,
                        "timestamp": result.timestamp
                    }
                    for name, result in self.check_results.items()
                }
            },
            "alerts": {
                "total_alerts": len(self.alerts),
                "unresolved_alerts": len([a for a in self.alerts if not a.resolved]),
                "recent_alerts": recent_alerts
            },
            "metrics": aggregated_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def get_metrics(self) -> Dict[str, float]:
        """Get health monitoring metrics"""
        total_checks = sum(checker.check_count for checker in self.checkers.values())
        total_failures = sum(checker.failure_count for checker in self.checkers.values())
        
        uptime = time.time() - self.system_start_time
        
        return {
            "system_uptime_seconds": uptime,
            "total_health_checks": total_checks,
            "total_check_failures": total_failures,
            "check_success_rate": (total_checks - total_failures) / max(1, total_checks) * 100,
            "active_checkers": len(self.checkers),
            "total_alerts_generated": len(self.alerts),
            "unresolved_alerts": len([a for a in self.alerts if not a.resolved])
        }


# Global health monitor instance
_health_monitor = HealthMonitor()


def get_health_monitor() -> HealthMonitor:
    """Get global health monitor instance"""
    return _health_monitor


# Default alert handlers
async def log_alert_handler(alert: Alert):
    """Default alert handler that logs alerts"""
    logger = logging.getLogger("health_alerts")
    
    if alert.level == AlertLevel.CRITICAL:
        logger.critical(f"CRITICAL ALERT: {alert.message}")
    elif alert.level == AlertLevel.ERROR:
        logger.error(f"ERROR ALERT: {alert.message}")
    elif alert.level == AlertLevel.WARNING:
        logger.warning(f"WARNING ALERT: {alert.message}")
    else:
        logger.info(f"INFO ALERT: {alert.message}")


async def websocket_alert_handler(alert: Alert, websocket_manager=None):
    """Alert handler that sends alerts via WebSocket"""
    if websocket_manager and hasattr(websocket_manager, 'broadcast_message'):
        try:
            await websocket_manager.broadcast_message({
                'type': 'health_alert',
                'data': {
                    'id': alert.id,
                    'component': alert.component,
                    'level': alert.level.value,
                    'message': alert.message,
                    'timestamp': alert.timestamp,
                    'details': alert.details
                }
            })
        except Exception as e:
            logging.getLogger("health_alerts").error(f"Failed to send WebSocket alert: {e}")


# Register default alert handler
get_health_monitor().register_alert_handler(log_alert_handler)