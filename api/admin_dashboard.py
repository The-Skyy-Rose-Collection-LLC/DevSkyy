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
from enum import Enum
from pathlib import Path
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from security import RoleChecker, TokenPayload, UserRole

logger = structlog.get_logger(__name__)

# Admin role requirement for all admin dashboard endpoints
require_admin = RoleChecker([UserRole.ADMIN])


# =============================================================================
# Enums for Asset Management
# =============================================================================


class AssetType(str, Enum):
    """Types of assets managed by the platform."""

    MODEL_3D = "3d_model"
    IMAGE = "image"
    VIDEO = "video"
    TEXTURE = "texture"


class AssetStatus(str, Enum):
    """Status of an asset in the pipeline."""

    PENDING = "pending"
    PROCESSING = "processing"
    VALIDATED = "validated"
    FAILED = "failed"
    ARCHIVED = "archived"


class PipelineType(str, Enum):
    """Types of processing pipelines."""

    MODEL_GENERATION = "model_generation"
    PHOTOSHOOT = "photoshoot"
    FIDELITY_CHECK = "fidelity_check"
    SYNC = "sync"


class PipelineStatus(str, Enum):
    """Status of a pipeline run."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SyncChannel(str, Enum):
    """E-commerce sync channels."""

    WORDPRESS = "wordpress"
    WOOCOMMERCE = "woocommerce"
    SHOPIFY = "shopify"


class SyncStatus(str, Enum):
    """Status of a sync operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# Asset Management Models
# =============================================================================


class Asset3D(BaseModel):
    """3D asset model for storage and retrieval."""

    id: str
    name: str
    type: AssetType = AssetType.MODEL_3D
    status: AssetStatus = AssetStatus.PENDING
    file_path: str | None = None
    file_size_bytes: int = 0
    format: str = "glb"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    fidelity_score: float | None = None
    fidelity_passed: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class FidelityReport(BaseModel):
    """Fidelity validation report."""

    id: str
    asset_id: str
    asset_name: str
    validation_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    overall_score: float
    passed: bool
    threshold_used: float = 95.0
    geometry_metrics: dict[str, Any] = Field(default_factory=dict)
    texture_metrics: dict[str, Any] = Field(default_factory=dict)
    material_metrics: dict[str, Any] = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class PipelineInfo(BaseModel):
    """Pipeline execution information."""

    id: str
    type: PipelineType
    status: PipelineStatus = PipelineStatus.QUEUED
    started_at: datetime | None = None
    completed_at: datetime | None = None
    asset_id: str | None = None
    progress_percent: int = 0
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DashboardMetrics(BaseModel):
    """Dashboard overview metrics."""

    total_assets: int = 0
    assets_pending: int = 0
    assets_processing: int = 0
    assets_validated: int = 0
    assets_failed: int = 0
    fidelity_pass_rate: float = 0.0
    active_pipelines: int = 0
    synced_products: int = 0


# =============================================================================
# Asset Storage
# =============================================================================


class AdminAssetStore:
    """In-memory storage for assets and reports."""

    def __init__(self) -> None:
        self._assets: dict[str, Asset3D] = {}
        self._reports: dict[str, FidelityReport] = {}
        self._pipelines: dict[str, PipelineInfo] = {}

    def add_asset(self, asset: Asset3D) -> None:
        """Add or update an asset."""
        self._assets[asset.id] = asset

    def get_asset(self, asset_id: str) -> Asset3D | None:
        """Get an asset by ID."""
        return self._assets.get(asset_id)

    def delete_asset(self, asset_id: str) -> bool:
        """Delete an asset by ID. Returns True if deleted, False if not found."""
        if asset_id in self._assets:
            del self._assets[asset_id]
            return True
        return False

    def list_assets(
        self,
        status: AssetStatus | None = None,
        asset_type: AssetType | None = None,
    ) -> list[Asset3D]:
        """List assets with optional filters."""
        assets = list(self._assets.values())
        if status:
            assets = [a for a in assets if a.status == status]
        if asset_type:
            assets = [a for a in assets if a.type == asset_type]
        return assets

    def add_report(self, report: FidelityReport) -> None:
        """Add a fidelity report."""
        self._reports[report.id] = report

    def get_report(self, report_id: str) -> FidelityReport | None:
        """Get a fidelity report by ID."""
        return self._reports.get(report_id)

    def list_reports(self, asset_id: str | None = None) -> list[FidelityReport]:
        """List fidelity reports."""
        reports = list(self._reports.values())
        if asset_id:
            reports = [r for r in reports if r.asset_id == asset_id]
        return reports

    def add_pipeline(self, pipeline: PipelineInfo) -> None:
        """Add a pipeline execution."""
        self._pipelines[pipeline.id] = pipeline

    def get_pipeline(self, pipeline_id: str) -> PipelineInfo | None:
        """Get a pipeline by ID."""
        return self._pipelines.get(pipeline_id)

    def get_metrics(self) -> DashboardMetrics:
        """Calculate dashboard metrics."""
        assets = list(self._assets.values())
        validated = [a for a in assets if a.status == AssetStatus.VALIDATED]
        passed = [a for a in validated if a.fidelity_passed]

        return DashboardMetrics(
            total_assets=len(assets),
            assets_pending=len([a for a in assets if a.status == AssetStatus.PENDING]),
            assets_processing=len([a for a in assets if a.status == AssetStatus.PROCESSING]),
            assets_validated=len(validated),
            assets_failed=len([a for a in assets if a.status == AssetStatus.FAILED]),
            fidelity_pass_rate=len(passed) / len(validated) if validated else 0.0,
            active_pipelines=len(
                [
                    p
                    for p in self._pipelines.values()
                    if p.status in (PipelineStatus.QUEUED, PipelineStatus.RUNNING)
                ]
            ),
            synced_products=0,  # Would be populated from sync engine
        )


# Singleton storage instance
storage = AdminAssetStore()

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
            if datetime.fromisoformat(o.get("created_at", "")).replace(tzinfo=UTC) >= today_start
        ]
        orders_month = [
            o
            for o in self._orders
            if datetime.fromisoformat(o.get("created_at", "")).replace(tzinfo=UTC) >= month_start
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
async def get_dashboard_stats(
    current_user: TokenPayload = Depends(require_admin),
) -> DashboardStats:
    """Get dashboard statistics. Requires admin role."""
    logger.info(
        "Admin dashboard stats requested",
        extra={"user_id": str(current_user.sub)},
    )
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
    current_user: TokenPayload = Depends(require_admin),
) -> list[ProductSummary]:
    """Get product list with filters. Requires admin role."""
    logger.info(
        "Admin product list requested",
        extra={"user_id": str(current_user.sub), "skip": skip, "limit": limit},
    )
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
    current_user: TokenPayload = Depends(require_admin),
) -> list[SyncJobSummary]:
    """Get recent sync jobs. Requires admin role."""
    logger.info(
        "Admin sync jobs list requested",
        extra={"user_id": str(current_user.sub)},
    )
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
async def trigger_full_sync(
    current_user: TokenPayload = Depends(require_admin),
) -> dict[str, Any]:
    """Trigger sync for all products. Requires admin role."""
    logger.info(
        "Admin triggered full sync",
        extra={"user_id": str(current_user.sub)},
    )
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
    current_user: TokenPayload = Depends(require_admin),
) -> SalesAnalytics:
    """Get sales analytics. Requires admin role."""
    logger.info(
        "Admin sales analytics requested",
        extra={"user_id": str(current_user.sub), "days": days},
    )
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
async def create_product(
    product: ProductSummary,
    current_user: TokenPayload = Depends(require_admin),
) -> dict[str, Any]:
    """Create or update a product. Requires admin role."""
    logger.info(
        "Admin created/updated product",
        extra={"user_id": str(current_user.sub), "product_sku": product.sku},
    )
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
async def get_product(
    product_sku: str,
    current_user: TokenPayload = Depends(require_admin),
) -> ProductSummary:
    """Get product details. Requires admin role."""
    logger.info(
        "Admin requested product details",
        extra={"user_id": str(current_user.sub), "product_sku": product_sku},
    )
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


# Response wrapper models for API endpoints
class ProductListResponse(BaseModel):
    """Response containing list of products."""

    products: list[ProductSummary] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 50


class SyncJobListResponse(BaseModel):
    """Response containing list of sync jobs."""

    jobs: list[SyncJobSummary] = Field(default_factory=list)
    total: int = 0


# Note: AdminDataStore is defined above as a separate class from AdminAssetStore
# AdminAssetStore: works with Asset3D, FidelityReport, PipelineInfo
# AdminDataStore: works with products, sync_jobs, orders


__all__ = [
    "admin_dashboard_router",
    # Enums
    "AssetType",
    "AssetStatus",
    "PipelineType",
    "PipelineStatus",
    "SyncChannel",
    "SyncStatus",
    # Models
    "Asset3D",
    "FidelityReport",
    "PipelineInfo",
    "DashboardMetrics",
    "DashboardStats",
    "ProductSummary",
    "SyncJobSummary",
    "SalesAnalytics",
    "ProductListResponse",
    "SyncJobListResponse",
    # Storage
    "storage",
    "AdminAssetStore",
    "AdminDataStore",  # Alias
]
