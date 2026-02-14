"""
Monitoring and Alerting Service
Tracks system health, performance metrics, and sends alerts.
"""

import os
import time
from datetime import datetime, timedelta

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not installed. Monitoring features will be limited.")
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import asyncio

from loguru import logger

from app.database_sqlite import get_db, DB_PATH
from app.config import settings
from app.utils.resilience import (
    with_retry,
    RetryConfig,
    CircuitBreaker
)

# Retry configuration for webhook alerts
WEBHOOK_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    base_delay=1.0,
    max_delay=10.0,
    retryable_exceptions=[Exception]
)


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SystemMetrics:
    """System resource metrics."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_percent: float
    disk_free_gb: float
    db_size_mb: float
    uptime_seconds: float


@dataclass
class HealthCheck:
    """Health check result."""
    name: str
    status: str  # healthy, degraded, unhealthy
    response_time_ms: float
    message: Optional[str] = None
    last_checked: Optional[str] = None


class MonitoringService:
    """
    Service for monitoring system health and performance.
    
    Features:
    - System resource monitoring (CPU, memory, disk)
    - Database health checks
    - API response time tracking
    - Alert generation and notification
    - Metrics history
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics_history: List[SystemMetrics] = []
        self.max_history_size = 1000
        self.alert_handlers = []
        self.webhook_circuit_breaker = CircuitBreaker("monitoring_webhook")
        
        # Alert thresholds
        self.cpu_threshold = float(os.getenv("ALERT_CPU_THRESHOLD", "80"))
        self.memory_threshold = float(os.getenv("ALERT_MEMORY_THRESHOLD", "85"))
        self.disk_threshold = float(os.getenv("ALERT_DISK_THRESHOLD", "90"))
        self.db_size_threshold_mb = float(os.getenv("ALERT_DB_SIZE_MB", "1000"))
        
        # Register default alert handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default alert handlers."""
        self.alert_handlers.append(self._log_alert)
        
        # Add webhook handler if configured
        webhook_url = os.getenv("ALERT_WEBHOOK_URL")
        if webhook_url:
            self.alert_handlers.append(
                lambda severity, title, message: asyncio.create_task(
                    self._webhook_alert(webhook_url, severity, title, message)
                )
            )
    
    def _log_alert(self, severity: AlertSeverity, title: str, message: str):
        """Log an alert."""
        log_func = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.ERROR: logger.error,
            AlertSeverity.CRITICAL: logger.critical
        }.get(severity, logger.info)
        
        log_func(f"[ALERT:{severity.value.upper()}] {title}: {message}")
    
    async def _webhook_alert(self, webhook_url: str, severity: AlertSeverity, title: str, message: str):
        """Send alert to webhook with retry logic."""
        if self.webhook_circuit_breaker.is_open:
            logger.warning("Webhook circuit breaker open, skipping alert")
            return
        
        @self.webhook_circuit_breaker.protect
        async def _send_webhook():
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(webhook_url, json={
                    "severity": severity.value,
                    "title": title,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "service": "mercura"
                })
                response.raise_for_status()
        
        try:
            await with_retry(_send_webhook, config=WEBHOOK_RETRY_CONFIG)
        except Exception as e:
            logger.error(f"Failed to send webhook alert after retries: {e}")
    
    def send_alert(self, severity: AlertSeverity, title: str, message: str):
        """Send an alert through all registered handlers."""
        for handler in self.alert_handlers:
            try:
                handler(severity, title, message)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
    
    def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        if PSUTIL_AVAILABLE:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disk
            disk = psutil.disk_usage(os.path.dirname(DB_PATH) or ".")
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024 ** 3)
        else:
            # Fallback values when psutil not available
            cpu_percent = 0.0
            memory_percent = 0.0
            memory_available_mb = 0.0
            disk_percent = 0.0
            disk_free_gb = 0.0
        
        # Database size
        db_size_mb = 0
        try:
            if os.path.exists(DB_PATH):
                db_size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
        except:
            pass
        
        # Uptime
        uptime_seconds = time.time() - self.start_time
        
        metrics = SystemMetrics(
            timestamp=datetime.utcnow().isoformat(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_mb=memory_available_mb,
            disk_percent=disk_percent,
            disk_free_gb=disk_free_gb,
            db_size_mb=db_size_mb,
            uptime_seconds=uptime_seconds
        )
        
        # Store in history
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]
        
        # Check thresholds and alert
        self._check_thresholds(metrics)
        
        return metrics
    
    def _check_thresholds(self, metrics: SystemMetrics):
        """Check metrics against thresholds and send alerts."""
        # CPU
        if metrics.cpu_percent > self.cpu_threshold:
            self.send_alert(
                AlertSeverity.WARNING,
                "High CPU Usage",
                f"CPU usage is {metrics.cpu_percent:.1f}% (threshold: {self.cpu_threshold}%)"
            )
        
        # Memory
        if metrics.memory_percent > self.memory_threshold:
            self.send_alert(
                AlertSeverity.WARNING,
                "High Memory Usage",
                f"Memory usage is {metrics.memory_percent:.1f}% (threshold: {self.memory_threshold}%)"
            )
        
        # Disk
        if metrics.disk_percent > self.disk_threshold:
            self.send_alert(
                AlertSeverity.ERROR,
                "Low Disk Space",
                f"Disk usage is {metrics.disk_percent:.1f}% (threshold: {self.disk_threshold}%)"
            )
        
        # Database size
        if metrics.db_size_mb > self.db_size_threshold_mb:
            self.send_alert(
                AlertSeverity.WARNING,
                "Large Database",
                f"Database size is {metrics.db_size_mb:.0f}MB (threshold: {self.db_size_threshold_mb}MB)"
            )
    
    def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive health checks."""
        checks = []
        overall_status = "healthy"
        
        # Database check
        db_check = self._check_database()
        checks.append(db_check)
        if db_check.status != "healthy":
            overall_status = db_check.status
        
        # Disk space check
        disk_check = self._check_disk_space()
        checks.append(disk_check)
        if disk_check.status == "unhealthy":
            overall_status = "unhealthy"
        elif disk_check.status == "degraded" and overall_status == "healthy":
            overall_status = "degraded"
        
        # Memory check
        memory_check = self._check_memory()
        checks.append(memory_check)
        if memory_check.status == "unhealthy":
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": [asdict(c) for c in checks],
            "uptime_seconds": time.time() - self.start_time
        }
    
    def _check_database(self) -> HealthCheck:
        """Check database connectivity and performance."""
        start = time.time()
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users")
                cursor.fetchone()
            
            response_time = (time.time() - start) * 1000
            
            status = "healthy"
            message = None
            
            if response_time > 1000:  # > 1 second
                status = "degraded"
                message = f"Slow response time: {response_time:.0f}ms"
            
            return HealthCheck(
                name="database",
                status=status,
                response_time_ms=response_time,
                message=message,
                last_checked=datetime.utcnow().isoformat()
            )
        except Exception as e:
            return HealthCheck(
                name="database",
                status="unhealthy",
                response_time_ms=(time.time() - start) * 1000,
                message=str(e),
                last_checked=datetime.utcnow().isoformat()
            )
    
    def _check_disk_space(self) -> HealthCheck:
        """Check available disk space."""
        if not PSUTIL_AVAILABLE:
            return HealthCheck(
                name="disk",
                status="healthy",
                response_time_ms=0,
                message="psutil not installed - disk monitoring disabled",
                last_checked=datetime.utcnow().isoformat()
            )
        
        start = time.time()
        try:
            disk = psutil.disk_usage(os.path.dirname(DB_PATH) or ".")
            response_time = (time.time() - start) * 1000
            
            if disk.percent > 95:
                status = "unhealthy"
                message = f"Critical disk usage: {disk.percent:.1f}%"
            elif disk.percent > 80:
                status = "degraded"
                message = f"High disk usage: {disk.percent:.1f}%"
            else:
                status = "healthy"
                message = f"Disk usage: {disk.percent:.1f}%"
            
            return HealthCheck(
                name="disk",
                status=status,
                response_time_ms=response_time,
                message=message,
                last_checked=datetime.utcnow().isoformat()
            )
        except Exception as e:
            return HealthCheck(
                name="disk",
                status="unhealthy",
                response_time_ms=0,
                message=str(e),
                last_checked=datetime.utcnow().isoformat()
            )
    
    def _check_memory(self) -> HealthCheck:
        """Check available memory."""
        if not PSUTIL_AVAILABLE:
            return HealthCheck(
                name="memory",
                status="healthy",
                response_time_ms=0,
                message="psutil not installed - memory monitoring disabled",
                last_checked=datetime.utcnow().isoformat()
            )
        
        start = time.time()
        try:
            memory = psutil.virtual_memory()
            response_time = (time.time() - start) * 1000
            
            if memory.percent > 95:
                status = "unhealthy"
                message = f"Critical memory usage: {memory.percent:.1f}%"
            elif memory.percent > 85:
                status = "degraded"
                message = f"High memory usage: {memory.percent:.1f}%"
            else:
                status = "healthy"
                message = f"Memory usage: {memory.percent:.1f}%"
            
            return HealthCheck(
                name="memory",
                status=status,
                response_time_ms=response_time,
                message=message,
                last_checked=datetime.utcnow().isoformat()
            )
        except Exception as e:
            return HealthCheck(
                name="memory",
                status="unhealthy",
                response_time_ms=0,
                message=str(e),
                last_checked=datetime.utcnow().isoformat()
            )
    
    def get_metrics_summary(self, hours: int = 24) -> Dict:
        """Get summary of metrics over a time period."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp) > cutoff
        ]
        
        if not recent_metrics:
            return {"error": "No metrics available for this period"}
        
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        
        return {
            "period_hours": hours,
            "samples": len(recent_metrics),
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values),
                "min": min(cpu_values),
                "max": max(cpu_values)
            },
            "memory": {
                "avg": sum(memory_values) / len(memory_values),
                "min": min(memory_values),
                "max": max(memory_values)
            },
            "latest": asdict(recent_metrics[-1]) if recent_metrics else None
        }


# Global monitoring service instance
monitoring_service = MonitoringService()
