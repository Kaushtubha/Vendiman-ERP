"""
app/api/router.py — Master API Router

Aggregates all v1 route modules into a single router mounted at /api/v1.

PATTERN: Router aggregation — each module registers its own sub-router,
this file wires them into the application.

WHY centralized router (not direct app.include_router() in main.py):
    - main.py stays clean — it mounts one router, not 15.
    - Adding a new module = one line here. No main.py changes.
    - Enables versioned routing: /api/v1/ vs /api/v2/ easily.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.alerts import router as alerts_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.grn import router as grn_router
from app.api.v1.health import router as health_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.products import router as products_router
from app.api.v1.purchase_orders import router as purchase_orders_router
from app.api.v1.suppliers import router as suppliers_router
from app.api.v1.upload import router as upload_router

# Master v1 router — all module routers are included here
api_router = APIRouter(prefix="/api/v1")

# ── Core Infrastructure ───────────────────────────────────────────────────────
api_router.include_router(health_router)

# ── Business Modules ──────────────────────────────────────────────────────────
api_router.include_router(auth_router)
api_router.include_router(products_router)
api_router.include_router(suppliers_router)
api_router.include_router(purchase_orders_router)
api_router.include_router(grn_router)
api_router.include_router(inventory_router)
api_router.include_router(analytics_router)
api_router.include_router(alerts_router)
api_router.include_router(upload_router)
