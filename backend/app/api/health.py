"""
Health Check API Endpoints

Provides health check endpoints for monitoring and service discovery.
"""

import logging
import psutil
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.models.response import HealthResponse, HealthStatus


logger = logging.getLogger(__name__)
router = APIRouter()

# Track application start time
_start_time = datetime.utcnow()


@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.

    Returns:
        HealthResponse: Current health status and basic information
    """
    try:
        uptime = (datetime.utcnow() - _start_time).total_seconds()

        # Perform basic health checks
        checks = {
            "application": True,
            "memory": _check_memory(),
            "disk": _check_disk_space(),
        }

        # Determine overall health status
        if all(checks.values()):
            status = HealthStatus.HEALTHY
        elif any(checks.values()):
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.UNHEALTHY

        return HealthResponse(
            status=status,
            timestamp=datetime.utcnow(),
            version=settings.APP_VERSION,
            uptime=uptime,
            checks=checks
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status=HealthStatus.UNHEALTHY,
            timestamp=datetime.utcnow(),
            version=settings.APP_VERSION,
            uptime=0,
            checks={"application": False}
        )


@router.get("/detailed", response_model=dict)
async def detailed_health_check():
    """
    Detailed health check with system information.

    Returns:
        dict: Comprehensive system and application status
    """
    try:
        uptime = (datetime.utcnow() - _start_time).total_seconds()

        # System information
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=1)

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "application": {
                "name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "uptime_seconds": uptime,
                "debug_mode": settings.DEBUG
            },
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "free": disk.free,
                    "used": disk.used,
                    "percent": (disk.used / disk.total) * 100
                }
            },
            "configuration": {
                "max_pages": settings.MAX_PAGES,
                "max_concurrent_requests": settings.MAX_CONCURRENT_REQUESTS,
                "output_dir": settings.OUTPUT_DIR,
                "browser_type": settings.BROWSER_TYPE
            }
        }

    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/ready")
async def readiness_check():
    """
    Readiness check for Kubernetes/container orchestration.

    Returns:
        dict: Simple ready/not ready status
    """
    try:
        # Check if critical services are available
        # For now, just check if we can create basic objects
        test_datetime = datetime.utcnow()

        return {
            "ready": True,
            "timestamp": test_datetime.isoformat()
        }

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/live")
async def liveness_check():
    """
    Liveness check for Kubernetes/container orchestration.

    Returns:
        dict: Simple alive/dead status
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat()
    }


def _check_memory() -> bool:
    """Check if memory usage is within acceptable limits."""
    try:
        memory = psutil.virtual_memory()
        # Consider healthy if less than 90% memory used
        return memory.percent < 90
    except Exception:
        return False


def _check_disk_space() -> bool:
    """Check if disk space is sufficient."""
    try:
        disk = psutil.disk_usage(settings.OUTPUT_DIR)
        # Consider healthy if more than 1GB free space
        return disk.free > (1 * 1024 * 1024 * 1024)  # 1GB in bytes
    except Exception:
        return False
