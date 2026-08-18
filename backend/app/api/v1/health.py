"""
app/api/v1/health.py — Health Check Endpoints

WHY dedicated health endpoints:
    Kubernetes, ECS, and load balancers use health checks to determine if
    a pod is ready to receive traffic and if it should be restarted.

    TWO types of health endpoints — a critical distinction:

    1. /health/live  (Liveness Probe):
       "Is this process alive?"
       Returns 200 always (if the process is running, it's alive).
       WHY: Kubernetes restarts pods that fail liveness checks. If we
       check the DB here and DB is down, Kubernetes restarts the pod —
       but the DB is still down. This causes cascading restarts.
       Liveness should ONLY fail if the process itself is broken.

    2. /health/ready (Readiness Probe):
       "Is this pod ready to handle requests?"
       Checks DB, Redis, and Celery connectivity.
       WHY: If the DB is down, mark pod as NOT READY. The load balancer
       removes it from the rotation — no traffic until the DB recovers.
       The pod is still running (liveness is fine), just not receiving traffic.

    3. /health         (General health — for monitoring dashboards):
       Returns detailed component status with latencies.
       Used by uptime monitoring (Datadog, Grafana, PagerDuty).

This distinction prevents accidental cascading restarts during DB outages.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import check_database_connection
from app.core.redis_client import get_redis_client

router = APIRouter(prefix="/health", tags=["Health"])

settings = get_settings()


@router.get(
    "/live",
    summary="Liveness Check",
    description="Returns 200 if the application process is running. Used for Kubernetes liveness probe.",
)
async def liveness_check() -> JSONResponse:
    """
    Liveness probe — confirms the process is alive.
    Never checks external dependencies (DB, Redis).
    """
    return JSONResponse(
        content={
            "status": "alive",
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@router.get(
    "/ready",
    summary="Readiness Check",
    description="Returns 200 if all dependencies (DB, Redis) are reachable. Used for Kubernetes readiness probe.",
)
async def readiness_check() -> JSONResponse:
    """
    Readiness probe — checks all critical dependencies.
    Returns 503 if any dependency is unavailable.
    """
    db_healthy = await check_database_connection()
    redis_client = get_redis_client()
    redis_healthy = await redis_client.ping()

    all_healthy = db_healthy and redis_healthy
    status_code = 200 if all_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_healthy else "not_ready",
            "checks": {
                "database": "ok" if db_healthy else "error",
                "redis": "ok" if redis_healthy else "error",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@router.get(
    "",
    summary="Detailed Health",
    description="Returns detailed health status with latency for all components. Used by monitoring dashboards.",
)
async def detailed_health() -> JSONResponse:
    """
    Detailed health check with latency measurements.
    Used by Grafana dashboards and uptime monitoring (not by Kubernetes).
    """
    components: dict = {}
    overall_healthy = True

    # Check database
    db_start = time.perf_counter()
    db_ok = await check_database_connection()
    db_latency_ms = (time.perf_counter() - db_start) * 1000
    components["database"] = {
        "status": "ok" if db_ok else "error",
        "latency_ms": round(db_latency_ms, 2),
    }
    if not db_ok:
        overall_healthy = False

    # Check Redis
    redis_start = time.perf_counter()
    redis_client = get_redis_client()
    redis_ok = await redis_client.ping()
    redis_latency_ms = (time.perf_counter() - redis_start) * 1000
    components["redis"] = {
        "status": "ok" if redis_ok else "error",
        "latency_ms": round(redis_latency_ms, 2),
    }
    if not redis_ok:
        overall_healthy = False

    status_code = 200 if overall_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if overall_healthy else "degraded",
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
            "components": components,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
