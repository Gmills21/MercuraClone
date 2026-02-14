"""
Monitoring and Health API Routes
System health checks, metrics, and monitoring data.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.services.monitoring_service import monitoring_service
from app.middleware.organization import get_current_user_and_org
from app.utils.observability import (
    performance_metrics,
    sentry_manager,
    ObservabilityHealthChecker,
)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health")
async def get_health():
    """Get comprehensive health check results."""
    return monitoring_service.check_health()


@router.get("/metrics")
async def get_metrics(
    hours: Optional[int] = 24,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Get system metrics summary."""
    user_id, org_id = user_org
    return monitoring_service.get_metrics_summary(hours=hours)


@router.post("/collect")
async def collect_metrics(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Trigger metrics collection."""
    user_id, org_id = user_org
    metrics = monitoring_service.collect_metrics()
    return {
        "success": True,
        "metrics": {
            "timestamp": metrics.timestamp,
            "cpu_percent": metrics.cpu_percent,
            "memory_percent": metrics.memory_percent,
            "disk_percent": metrics.disk_percent,
            "db_size_mb": metrics.db_size_mb,
            "uptime_seconds": metrics.uptime_seconds
        }
    }


@router.get("/status")
async def get_system_status():
    """Get quick system status (for load balancers)."""
    health = monitoring_service.check_health()
    
    # Simplified status for load balancers
    if health["status"] == "healthy":
        return {"status": "ok", "timestamp": health["timestamp"]}
    elif health["status"] == "degraded":
        return {"status": "degraded", "timestamp": health["timestamp"]}
    else:
        raise HTTPException(status_code=503, detail="Service unhealthy")


# =============================================================================
# OBSERVABILITY & TELEMETRY ENDPOINTS
# =============================================================================

@router.get("/observability/health")
async def get_observability_health():
    """Get observability system health status."""
    return ObservabilityHealthChecker.get_health()


@router.get("/observability/performance")
async def get_performance_metrics(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Get API and database performance metrics."""
    user_id, org_id = user_org
    return {
        "metrics": performance_metrics.get_all_stats(),
        "timestamp": monitoring_service.collect_metrics().timestamp,
    }


@router.get("/observability/sentry/status")
async def get_sentry_status(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Get Sentry error tracking status."""
    user_id, org_id = user_org
    return {
        "enabled": sentry_manager.enabled,
        "environment": sentry_manager.sentry_sdk._client.options["environment"] if sentry_manager.enabled else None,
    }


@router.post("/observability/sentry/test")
async def test_sentry(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Test Sentry integration by sending a test event."""
    user_id, org_id = user_org
    
    if not sentry_manager.enabled:
        raise HTTPException(status_code=400, detail="Sentry not configured")
    
    sentry_manager.capture_message(
        "Test message from OpenMercura monitoring",
        level="info",
        context={"user_id": user_id, "org_id": org_id, "test": True}
    )
    
    return {"success": True, "message": "Test event sent to Sentry"}
