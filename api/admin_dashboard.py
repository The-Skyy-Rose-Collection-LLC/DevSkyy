"""
Admin Dashboard API Endpoints
=============================

Administrative endpoints for the SkyyRose Admin Dashboard.

Endpoints:
- GET /api/v1/admin/stats - Dashboard statistics
- GET /api/v1/admin/products - Product list with filters
- GET /api/v1/admin/sync-jobs - Recent sync jobs
- POST /api/v1/admin/sync-all - Trigger full sync
- GET /api/v1/admin/analytics/sales - Sales analytics

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

admin_dashboard_router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


# =============================================================================
# Response Models
# =============================================================================


class DashboardStats(BaseModel):
    """Dashboard statistics."""

    total_products: int = 0
    products_with_3d: int = 0
    products_synced: int = 0
    pending_sync: int = 0
    total_orders_today: int = 0
    revenue_today: float = 0.0
    total_orders_month: int = 0
    revenue_month: float = 0.0


class ProductSummary(BaseModel):
    """Product summary for list view."""

    sku: str
    name: str
    status: str = "draft"
    has_3d_model: bool = False
    synced: bool = False
    stock: int = 0
    price: float = 0.0


class SyncJobSummary(BaseModel):
    """Sync job summary."""

    id: str
    product_sku: str
    status: str
    started_at: str
    completed_at: str | None = None
    errors: list[str] = Field(default_factory=list)


class SalesDataPoint(BaseModel):
    """Sales data for analytics."""

    date: str
    orders: int
    revenue: float


class SalesAnalytics(BaseModel):
    """Sales analytics response."""

    period_days: int
    total_orders: int
    total_revenue: float
    data: list[SalesDataPoint] = Field(default_factory=list)


# =============================================================================
# In-Memory Data Store (would be database in production)
# =============================================================================


class AdminDataStore:
    """In-memory admin data store."""

    def __init__(self) -> None:
        self._products: dict[str, dict[str, Any]] = {}
        self._sync_jobs: dict[str, dict[str, Any]] = {}
        self._orders: list[dict[str, Any]] = []

    def add_product(self, sku: str, data: dict[str, Any]) -> None:
        """Add or update product."""
        self._products[sku] = {
            "sku": sku,
            **data,
            "created_at": datetime.now(UTC).isoformat(),
        }

    def get_products(
        self,
        skip: int = 0,
        limit: int = 50,
        status: str | None = None,
        has_3d: bool | None = None,
    ) -> list[dict[str, Any]]:
        """Get products with filters."""
        products = list(self._products.values())

        if status:
            products = [p for p in products if p.get("status") == status]
        if has_3d is not None:
            products = [p for p in products if p.get("has_3d_model") == has_3d]

        return products[skip : skip + limit]

    def add_sync_job(self, job_id: str, data: dict[str, Any]) -> None:
        """Add sync job."""
        self._sync_jobs[job_id] = data

    def get_sync_jobs(
        self,
        limit: int = 20,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get recent sync jobs."""
        jobs = sorted(
            self._sync_jobs.values(),
            key=lambda x: x.get("started_at", ""),
            reverse=True,
        )
        if status:
            jobs = [j for j in jobs if j.get("status") == status]
        return jobs[:limit]

    def add_order(self, order: dict[str, Any]) -> None:
        """Add order."""
        self._orders.append(order)

    def get_stats(self) -> dict[str, Any]:
        """Get dashboard stats."""
        products = list(self._products.values())
        now = datetime.now(UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Filter orders
        orders_today = [
            o
            for o in self._orders
            if datetime.fromisoformat(o.get("created_at", "")).replace(tzinfo=UTC)
            >= today_start
        ]
        orders_month = [
            o
            for o in self._orders
            if datetime.fromisoformat(o.get("created_at", "")).replace(tzinfo=UTC)
            >= month_start
        ]

        return {
            "total_products": len(products),
            "products_with_3d": sum(1 for p in products if p.get("has_3d_model")),
            "products_synced": sum(1 for p in products if p.get("synced")),
            "pending_sync": sum(1 for p in products if not p.get("synced")),
            "total_orders_today": len(orders_today),
            "revenue_today": sum(o.get("total", 0) for o in orders_today),
            "total_orders_month": len(orders_month),
            "revenue_month": sum(o.get("total", 0) for o in orders_month),
        }


admin_data = AdminDataStore()


# =============================================================================
# Endpoints
# =============================================================================


@admin_dashboard_router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats() -> DashboardStats:
    """Get dashboard statistics."""
    stats = admin_data.get_stats()

    # Add file-based stats
    models_dir = Path("./generated_models/models")
    if models_dir.exists():
        model_count = len(list(models_dir.glob("*.glb")))
        stats["products_with_3d"] = max(stats["products_with_3d"], model_count)

    return DashboardStats(**stats)


@admin_dashboard_router.get("/products", response_model=list[ProductSummary])
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: str | None = None,
    has_3d: bool | None = None,
) -> list[ProductSummary]:
    """Get product list with filters."""
    products = admin_data.get_products(skip, limit, status, has_3d)

    # Supplement with file-based 3D model info
    models_dir = Path("./generated_models/models")
    model_skus = set()
    if models_dir.exists():
        model_skus = {p.stem for p in models_dir.glob("*.glb")}

    result = []
    for p in products:
        sku = p.get("sku", "")
        result.append(
            ProductSummary(
                sku=sku,
                name=p.get("name", sku),
                status=p.get("status", "draft"),
                has_3d_model=p.get("has_3d_model", False) or sku in model_skus,
                synced=p.get("synced", False),
                stock=p.get("stock", 0),
                price=p.get("price", 0.0),
            )
        )

    return result


@admin_dashboard_router.get("/sync-jobs", response_model=list[SyncJobSummary])
async def get_sync_jobs(
    status: str | None = None,
    limit: int = Query(20, ge=1, le=100),
) -> list[SyncJobSummary]:
    """Get recent sync jobs."""
    jobs = admin_data.get_sync_jobs(limit, status)

    # Also check sync_endpoints job store
    try:
        from api.sync_endpoints import sync_job_store

        sync_jobs = sync_job_store.list_jobs(limit)
        for job in sync_jobs:
            if status is None or job.get("status") == status:
                jobs.append(job)
    except ImportError:
        pass

    # Sort and deduplicate
    seen = set()
    unique_jobs = []
    for job in sorted(jobs, key=lambda x: x.get("started_at", ""), reverse=True):
        job_id = job.get("job_id") or job.get("id")
        if job_id and job_id not in seen:
            seen.add(job_id)
            unique_jobs.append(
                SyncJobSummary(
                    id=job_id,
                    product_sku=job.get("product_sku", ""),
                    status=job.get("status", "unknown"),
                    started_at=job.get("started_at", ""),
                    completed_at=job.get("completed_at"),
                    errors=job.get("errors", []),
                )
            )

    return unique_jobs[:limit]


@admin_dashboard_router.post("/sync-all")
async def trigger_full_sync() -> dict[str, Any]:
    """Trigger sync for all products."""
    products = admin_data.get_products(limit=1000)
    unsynced = [p for p in products if not p.get("synced")]

    # Queue sync jobs
    queued = 0
    try:
        from api.sync_endpoints import sync_job_store

        for product in unsynced:
            sync_job_store.create(product.get("sku", ""))
            queued += 1
    except ImportError:
        pass

    return {
        "message": "Full sync triggered",
        "total_products": len(products),
        "queued": queued,
    }


@admin_dashboard_router.get("/analytics/sales", response_model=SalesAnalytics)
async def get_sales_analytics(
    days: int = Query(30, ge=1, le=365),
) -> SalesAnalytics:
    """Get sales analytics."""
    # Generate sample data (would come from database in production)
    now = datetime.now(UTC)
    data = []

    for i in range(days):
        date = now - timedelta(days=i)
        data.append(
            SalesDataPoint(
                date=date.strftime("%Y-%m-%d"),
                orders=0,  # Would come from database
                revenue=0.0,
            )
        )

    data.reverse()  # Chronological order

    return SalesAnalytics(
        period_days=days,
        total_orders=0,
        total_revenue=0.0,
        data=data,
    )


@admin_dashboard_router.post("/products")
async def create_product(product: ProductSummary) -> dict[str, Any]:
    """Create or update a product."""
    admin_data.add_product(
        product.sku,
        {
            "name": product.name,
            "status": product.status,
            "has_3d_model": product.has_3d_model,
            "synced": product.synced,
            "stock": product.stock,
            "price": product.price,
        },
    )

    return {"success": True, "sku": product.sku}


@admin_dashboard_router.get("/products/{product_sku}")
async def get_product(product_sku: str) -> ProductSummary:
    """Get product details."""
    products = admin_data.get_products(limit=1000)
    product = next((p for p in products if p.get("sku") == product_sku), None)

    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_sku} not found")

    return ProductSummary(
        sku=product.get("sku", ""),
        name=product.get("name", ""),
        status=product.get("status", "draft"),
        has_3d_model=product.get("has_3d_model", False),
        synced=product.get("synced", False),
        stock=product.get("stock", 0),
        price=product.get("price", 0.0),
    )


__all__ = ["admin_dashboard_router"]
