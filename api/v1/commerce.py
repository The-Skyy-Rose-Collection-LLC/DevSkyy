"""Commerce API Endpoints (Bulk Products & Dynamic Pricing).

This module provides endpoints for:
- Bulk product operations
- Dynamic pricing optimization
- Integration with agents/commerce_agent.py

Version: 1.0.0
"""

import logging
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from agents.commerce_agent import CommerceAgent
from core.task_status_store import TaskStatusStore, get_initialized_task_status_store
from security.jwt_oauth2_auth import TokenPayload, get_current_user
from skyyrose.core.catalog_loader import read_catalog_rows

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/commerce", tags=["Commerce"])


# =============================================================================
# Request/Response Models
# =============================================================================


class BulkProductRequest(BaseModel):
    """Request model for bulk product operations."""

    action: Literal["create", "update", "delete"] = Field(
        ..., description="Bulk operation to perform"
    )
    products: list[dict[str, Any]] = Field(
        ..., description="List of product data", min_length=1, max_length=100
    )
    validate_only: bool = Field(default=False, description="Validate without applying changes")


class ProductResult(BaseModel):
    """Result for individual product operation."""

    product_id: str | None = None
    sku: str | None = None
    status: str  # success, failed, skipped
    message: str | None = None


class BulkProductResponse(BaseModel):
    """Response model for bulk product operations."""

    operation_id: str
    status: str
    timestamp: str
    action: str
    total_products: int
    successful: int
    failed: int
    results: list[ProductResult]


class DynamicPricingRequest(BaseModel):
    """Request model for dynamic pricing optimization."""

    product_ids: list[str] = Field(
        ...,
        description="Product IDs to optimize pricing for",
        min_length=1,
        max_length=100,
    )
    strategy: Literal["competitive", "demand_based", "ml_optimized", "time_based"] = Field(
        default="ml_optimized", description="Pricing strategy to use"
    )
    constraints: dict[str, Any] | None = Field(
        default=None,
        description="Pricing constraints (e.g., {'min_margin': 0.2, 'max_discount': 0.3})",
    )


class PriceOptimization(BaseModel):
    """Price optimization for individual product."""

    product_id: str
    current_price: float
    optimized_price: float
    price_change: float
    price_change_pct: float
    estimated_revenue_impact: float | None = None
    confidence: float


class DynamicPricingResponse(BaseModel):
    """Response model for dynamic pricing."""

    optimization_id: str
    status: str
    timestamp: str
    strategy: str
    total_products: int
    optimizations: list[PriceOptimization]
    aggregate_metrics: dict[str, Any]


# =============================================================================
# Background Task Processing
# =============================================================================


async def _dispatch_product_op(
    action: str,
    product_data: dict[str, Any],
    agent: CommerceAgent,
    validate_only: bool = False,
) -> ProductResult:
    """Dispatch a single product operation to CommerceAgent.

    Never raises — all errors map to ProductResult(status="failed", message=...).

    Args:
        action: "create", "update", or "delete"
        product_data: Raw dict from the request payload
        agent: Initialized CommerceAgent instance
        validate_only: When True validate shape only; make no write calls

    Returns:
        ProductResult with status "success", "failed", or "skipped"
    """
    sku: str | None = product_data.get("sku")

    # -- validate_only: shape check, no writes --
    if validate_only:
        if action == "create":
            if not product_data.get("name") or product_data.get("price") is None:
                return ProductResult(
                    sku=sku,
                    status="skipped",
                    message="validation only: missing name or price",
                )
        elif action in ("update", "delete"):
            if not (product_data.get("id") or product_data.get("product_id")):
                return ProductResult(
                    sku=sku,
                    status="skipped",
                    message=f"validation only: missing product id for {action}",
                )
        return ProductResult(sku=sku, status="success", message="validation only")

    # -- create --
    if action == "create":
        name = product_data.get("name")
        price = product_data.get("price")
        if not name or price is None:
            return ProductResult(sku=sku, status="failed", message="missing name/price")
        try:
            result = await agent.sync_product_to_woocommerce(
                name=str(name),
                price=float(price),
                sku=sku,
                description=str(product_data.get("description", "")),
                short_description=str(product_data.get("short_description", "")),
                stock_quantity=product_data.get("stock_quantity"),
                status=str(product_data.get("status", "draft")),
                categories=product_data.get("categories"),
                tags=product_data.get("tags"),
                images=product_data.get("images"),
            )
        except Exception as exc:
            return ProductResult(sku=sku, status="failed", message=str(exc))
        if "error" in result:
            return ProductResult(sku=sku, status="failed", message=str(result["error"]))
        wc_id = result.get("woocommerce_id") or result.get("id")
        return ProductResult(
            product_id=str(wc_id) if wc_id is not None else None,
            sku=sku,
            status="success",
        )

    # -- update --
    if action == "update":
        pid_raw = product_data.get("id") or product_data.get("product_id")
        if not pid_raw:
            return ProductResult(sku=sku, status="failed", message="missing product id for update")
        try:
            product_id_int = int(pid_raw)
        except (TypeError, ValueError):
            return ProductResult(sku=sku, status="failed", message=f"invalid product id: {pid_raw}")
        try:
            result = await agent.update_woocommerce_product(
                product_id=product_id_int, updates=product_data
            )
        except Exception as exc:
            return ProductResult(sku=sku, status="failed", message=str(exc))
        if "error" in result:
            return ProductResult(sku=sku, status="failed", message=str(result["error"]))
        result_id = result.get("id")
        return ProductResult(
            product_id=str(result_id) if result_id is not None else None,
            sku=sku,
            status="success",
        )

    # -- delete (via _wordpress_client — CommerceAgent has no public delete method) --
    if action == "delete":
        pid_raw = product_data.get("id") or product_data.get("product_id")
        if not pid_raw:
            return ProductResult(sku=sku, status="failed", message="missing product id for delete")
        try:
            product_id_int = int(pid_raw)
        except (TypeError, ValueError):
            return ProductResult(sku=sku, status="failed", message=f"invalid product id: {pid_raw}")
        try:
            await agent._ensure_wordpress_client()
            if agent._wordpress_client is None:
                return ProductResult(
                    sku=sku, status="failed", message="WordPress client not available"
                )
            result = await agent._wordpress_client.delete_product(product_id_int, force=False)
        except Exception as exc:
            return ProductResult(sku=sku, status="failed", message=str(exc))
        if isinstance(result, dict) and "error" in result:
            return ProductResult(sku=sku, status="failed", message=str(result["error"]))
        return ProductResult(product_id=str(product_id_int), sku=sku, status="success")

    # Should not reach here — BulkProductRequest.action is a Literal
    return ProductResult(sku=sku, status="failed", message=f"unsupported action: {action}")


async def _process_bulk_products_background(
    operation_id: str,
    action: str,
    products: list[dict[str, Any]],
    user_id: str,
    store: TaskStatusStore,
) -> None:
    """Process bulk product operations in the background.

    This prevents request timeouts for large batch operations.
    Results can be polled via GET /commerce/products/bulk/{operation_id}/status

    Args:
        operation_id: Unique operation identifier
        action: Bulk operation type (create, update, delete)
        products: List of product data to process
        user_id: ID of user who initiated the operation
        store: TaskStatusStore for persisting status (Redis-backed)
    """
    logger.info(f"Background task started: {operation_id}")

    started_at = datetime.now(UTC).isoformat()

    try:
        await store.set_status(
            operation_id,
            {
                "status": "processing",
                "progress": 0,
                "total": len(products),
                "started_at": started_at,
            },
        )

        results: list[dict[str, Any]] = []
        successful = 0
        failed = 0

        # Initialize CommerceAgent once for the entire background batch.
        agent = CommerceAgent()
        try:
            await agent.initialize()
        except Exception as exc:
            logger.exception(
                "CommerceAgent initialization failed for background task %s", operation_id
            )
            await store.set_status(
                operation_id,
                {
                    "status": "failed",
                    "error": f"Commerce agent unavailable: {exc}",
                    "completed_at": datetime.now(UTC).isoformat(),
                },
            )
            return

        for i, product_data in enumerate(products):
            op_result = await _dispatch_product_op(action, product_data, agent)
            results.append(
                {
                    "product_id": op_result.product_id,
                    "sku": op_result.sku,
                    "status": op_result.status,
                    "message": op_result.message,
                }
            )
            if op_result.status == "success":
                successful += 1
            else:
                failed += 1

            # Update progress periodically (every 10 items to reduce Redis calls)
            if (i + 1) % 10 == 0 or i == len(products) - 1:
                await store.update_status(operation_id, {"progress": i + 1})

        # Store final results
        await store.set_status(
            operation_id,
            {
                "status": "completed",
                "progress": len(products),
                "total": len(products),
                "started_at": started_at,
                "completed_at": datetime.now(UTC).isoformat(),
                "action": action,
                "successful": successful,
                "failed": failed,
                "results": results,
            },
        )
        logger.info(f"Background task completed: {operation_id}")

    except Exception as e:
        logger.error(f"Background task failed: {operation_id}: {e}", exc_info=True)
        await store.set_status(
            operation_id,
            {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now(UTC).isoformat(),
            },
        )


# =============================================================================
# Endpoints
# =============================================================================


class BulkTaskStatusResponse(BaseModel):
    """Response for bulk operation status check."""

    operation_id: str
    status: str  # pending, processing, completed, failed
    progress: int | None = None
    total: int | None = None
    started_at: str | None = None
    completed_at: str | None = None
    action: str | None = None
    successful: int | None = None
    failed: int | None = None
    results: list[ProductResult] | None = None
    error: str | None = None


@router.post(
    "/products/bulk",
    response_model=BulkProductResponse,
    status_code=status.HTTP_200_OK,
)
async def bulk_product_operations(
    request: BulkProductRequest,
    background_tasks: BackgroundTasks,
    user: TokenPayload = Depends(get_current_user),
    store: TaskStatusStore = Depends(get_initialized_task_status_store),
) -> BulkProductResponse:
    """Perform bulk operations on products.

    For large batches (>50 products), operations run in the background.
    Use GET /commerce/products/bulk/{operation_id}/status to check progress.

    **Features:**
    - Batch processing with background task support
    - Automatic validation
    - AI-powered SEO optimization for new products
    - Inventory sync across platforms
    - Error handling with partial success support

    Args:
        request: Bulk operation configuration (action, products, validate_only)
        background_tasks: FastAPI background tasks handler
        user: Authenticated user (from JWT token)

    Returns:
        BulkProductResponse with operation results or task_id for background ops

    Raises:
        HTTPException: If bulk operation fails
    """
    operation_id = str(uuid4())
    logger.info(
        f"Starting bulk product operation {operation_id} for user {user.sub}: "
        f"{request.action} ({len(request.products)} products)"
    )

    # For large batches, use background processing to prevent timeouts
    if len(request.products) > 50 and not request.validate_only:
        # Start background task with Redis-backed store
        background_tasks.add_task(
            _process_bulk_products_background,
            operation_id,
            request.action,
            request.products,
            user.sub,
            store,
        )

        # Return immediately with task reference
        return BulkProductResponse(
            operation_id=operation_id,
            status="processing",
            timestamp=datetime.now(UTC).isoformat(),
            action=request.action,
            total_products=len(request.products),
            successful=0,
            failed=0,
            results=[],
        )

    try:
        # Process synchronously for small batches.
        results: list[ProductResult] = []
        successful = 0
        failed = 0

        # Initialize CommerceAgent once for the entire batch.
        agent = CommerceAgent()
        try:
            await agent.initialize()
        except Exception as exc:
            logger.exception("CommerceAgent initialization failed for operation %s", operation_id)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Commerce agent unavailable",
            ) from exc

        for product_data in request.products:
            op_result = await _dispatch_product_op(
                request.action, product_data, agent, request.validate_only
            )
            results.append(op_result)
            if op_result.status == "success":
                successful += 1
            else:
                failed += 1

        return BulkProductResponse(
            operation_id=operation_id,
            status="completed",
            timestamp=datetime.now(UTC).isoformat(),
            action=request.action,
            total_products=len(request.products),
            successful=successful,
            failed=failed,
            results=results,
        )

    except Exception as e:
        logger.error(f"Bulk product operation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk product operation failed: {str(e)}",
        )


@router.get(
    "/products/bulk/{operation_id}/status",
    response_model=BulkTaskStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_bulk_operation_status(
    operation_id: str,
    user: TokenPayload = Depends(get_current_user),
    store: TaskStatusStore = Depends(get_initialized_task_status_store),
) -> BulkTaskStatusResponse:
    """Get the status of a background bulk operation.

    Poll this endpoint to check progress of large batch operations.

    Args:
        operation_id: The operation ID returned from POST /products/bulk
        user: Authenticated user (from JWT token)
        store: TaskStatusStore for retrieving status (Redis-backed)

    Returns:
        BulkTaskStatusResponse with current status and progress

    Raises:
        HTTPException: If operation not found
    """
    status_data = await store.get_status(operation_id)

    if status_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operation {operation_id} not found",
        )

    return BulkTaskStatusResponse(
        operation_id=operation_id,
        status=status_data.get("status", "unknown"),
        progress=status_data.get("progress"),
        total=status_data.get("total"),
        started_at=status_data.get("started_at"),
        completed_at=status_data.get("completed_at"),
        action=status_data.get("action"),
        successful=status_data.get("successful"),
        failed=status_data.get("failed"),
        results=(
            [ProductResult(**r) for r in status_data.get("results", [])]
            if status_data.get("results")
            else None
        ),
        error=status_data.get("error"),
    )


def _coerce_price(value: Any) -> float | None:
    """Best-effort float coercion for a price; None if missing or not positive."""
    if value is None or value == "":
        return None
    try:
        price = float(value)
    except (TypeError, ValueError):
        return None
    return price if price > 0 else None


def _catalog_price_map() -> dict[str, float]:
    """Map SKU -> current price from the canonical catalog CSV (the SOT)."""
    prices: dict[str, float] = {}
    for row in read_catalog_rows():
        price = _coerce_price(row.get("price"))
        if price is not None:
            prices[row["sku"]] = price
    return prices


@router.post(
    "/pricing/optimize",
    response_model=DynamicPricingResponse,
    status_code=status.HTTP_200_OK,
)
async def optimize_pricing(
    request: DynamicPricingRequest, user: TokenPayload = Depends(get_current_user)
) -> DynamicPricingResponse:
    """Optimize product pricing using ML and market intelligence.

    The Dynamic Pricing Agent uses advanced algorithms to maximize revenue:

    **Strategies:**

    1. **Competitive**: Match or beat competitor pricing
    2. **Demand-Based**: Adjust based on demand signals
    3. **ML-Optimized**: Machine learning price optimization
    4. **Time-Based**: Dynamic pricing by time of day/week

    **Features:**
    - Real-time competitor price scraping
    - Demand forecasting
    - Margin protection
    - Revenue impact projections

    Args:
        request: Pricing configuration (product_ids, strategy, constraints)
        user: Authenticated user (from JWT token)

    Returns:
        DynamicPricingResponse with optimized prices

    Raises:
        HTTPException: If optimization fails
    """
    optimization_id = str(uuid4())
    logger.info(
        f"Starting price optimization {optimization_id} for user {user.sub}: "
        f"{request.strategy} ({len(request.product_ids)} products)"
    )

    price_by_sku = _catalog_price_map()

    agent = CommerceAgent()
    try:
        await agent.initialize()
    except Exception as e:
        logger.exception("Pricing agent initialization failed for %s", optimization_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pricing engine is unavailable",
        ) from e

    optimizations: list[PriceOptimization] = []
    skipped: list[dict[str, str]] = []

    for product_id in request.product_ids:
        current_price = price_by_sku.get(product_id)
        if current_price is None:
            skipped.append({"product_id": product_id, "reason": "not in catalog"})
            continue

        try:
            result = await agent.optimize_price(product_id, factors=request.constraints)
        except Exception:
            logger.exception("optimize_price failed for %s", product_id)
            skipped.append({"product_id": product_id, "reason": "optimization error"})
            continue

        optimized_price = _coerce_price(result.get("recommended_price"))
        if optimized_price is None:
            skipped.append(
                {"product_id": product_id, "reason": result.get("error", "no recommendation")}
            )
            continue

        price_change = optimized_price - current_price
        price_change_pct = (price_change / current_price * 100.0) if current_price else 0.0
        optimizations.append(
            PriceOptimization(
                product_id=product_id,
                current_price=round(current_price, 2),
                optimized_price=round(optimized_price, 2),
                price_change=round(price_change, 2),
                price_change_pct=round(price_change_pct, 2),
                estimated_revenue_impact=None,
                confidence=float(result.get("confidence") or 0.0),
            )
        )

    if not optimizations:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No prices could be optimized (pricing model unavailable or unknown SKUs)",
        )

    avg_change = sum(o.price_change_pct for o in optimizations) / len(optimizations)
    aggregate_metrics = {
        "optimized_count": len(optimizations),
        "skipped_count": len(skipped),
        "skipped": skipped,
        "avg_price_change_pct": round(avg_change, 2),
    }

    return DynamicPricingResponse(
        optimization_id=optimization_id,
        status="completed",
        timestamp=datetime.now(UTC).isoformat(),
        strategy=request.strategy,
        total_products=len(request.product_ids),
        optimizations=optimizations,
        aggregate_metrics=aggregate_metrics,
    )
