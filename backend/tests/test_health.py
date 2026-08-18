"""
tests/test_health.py — Health Endpoint Tests

WHY these tests:
    Health endpoints are the first thing Kubernetes hits after a deployment.
    If they're broken, the pod never receives traffic and the deployment fails.
    These tests prevent silent breakage of liveness/readiness probes.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.unit
async def test_liveness_returns_200(client: AsyncClient) -> None:
    """Liveness check must always return 200 when the process is running."""
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
@pytest.mark.unit
async def test_liveness_returns_service_info(client: AsyncClient) -> None:
    """Liveness response must include service name and environment."""
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "environment" in data


@pytest.mark.asyncio
@pytest.mark.unit
async def test_health_response_has_request_id_header(client: AsyncClient) -> None:
    """All responses must include X-Request-ID header (from RequestIdMiddleware)."""
    response = await client.get("/api/v1/health/live")
    assert "x-request-id" in response.headers


@pytest.mark.asyncio
@pytest.mark.unit
async def test_unknown_route_returns_structured_error(client: AsyncClient) -> None:
    """Non-existent routes should return structured error (not bare HTML 404)."""
    response = await client.get("/api/v1/nonexistent-route")
    assert response.status_code == 404
