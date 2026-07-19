"""LoRA Training API Router (api/v1/lora.py).

Exposes 4 endpoints that proxy into the imagery/ SDXL backend:

  POST /lora/train               → 202 accepted; training runs as BackgroundTask
  GET  /lora/dataset/preview     → dataset summary (WooCommerce products, no GPU)
  GET  /lora/versions/{version}  → version metadata from SQLite tracker
  GET  /lora/products/{sku}/history → per-SKU training history

No paid-API gate: SDXL training is local GPU compute, not a per-call billed service.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from imagery.lora_trainer import SkyyRoseLoRATrainer
from imagery.lora_version_tracker import LoRAVersion, LoRAVersionTracker
from imagery.product_training_dataset import fetch_products_from_woocommerce

logger = logging.getLogger(__name__)

lora_router = APIRouter(prefix="/lora", tags=["LoRA Training"])

# Canonical DB path — matches SkyyRoseLoRATrainer default (lora_trainer.py:167)
LORA_VERSIONS_DB: Path = Path("models/lora-versions.db")


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class TrainLoRARequest(BaseModel):
    """Body for POST /lora/train."""

    collections: list[str] | None = Field(
        default=None,
        description="Collections to include (BLACK_ROSE, LOVE_HURTS, SIGNATURE). None = all.",
    )
    max_products: int | None = Field(default=None, description="Cap on number of products.")
    epochs: int = Field(default=100, ge=1, description="Training epochs.")
    version: str | None = Field(
        default=None, description="Version label; auto-assigned if omitted."
    )


class TrainLoRAResponse(BaseModel):
    status: str
    version: str | None
    message: str
    monitor: str


class SampleProduct(BaseModel):
    sku: str
    name: str
    collection: str
    image_count: int
    quality_score: float


class DatasetPreviewResponse(BaseModel):
    total_products: int
    total_images: int
    avg_quality_score: float
    collections: dict[str, int]
    sample_products: list[SampleProduct]


class ProductContributionOut(BaseModel):
    sku: str
    product_name: str
    collection: str
    images_count: int
    quality_score: float


class LoRAVersionOut(BaseModel):
    version: str
    base_model: str
    created_at: datetime
    training_config: dict[str, Any]
    model_path: str
    total_images: int
    total_products: int
    collections: dict[str, int]
    products: list[ProductContributionOut]


class ProductHistoryResponse(BaseModel):
    sku: str
    versions: list[LoRAVersionOut]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _version_to_out(lv: LoRAVersion) -> LoRAVersionOut:
    return LoRAVersionOut(
        version=lv.version,
        base_model=lv.base_model,
        created_at=lv.created_at,
        training_config=lv.training_config,
        model_path=lv.model_path,
        total_images=lv.total_images,
        total_products=lv.total_products,
        collections=lv.collections,
        products=[
            ProductContributionOut(
                sku=p.sku,
                product_name=p.product_name,
                collection=p.collection,
                images_count=p.images_count,
                quality_score=p.quality_score,
            )
            for p in (lv.products or [])
        ],
    )


def _make_tracker() -> LoRAVersionTracker:
    return LoRAVersionTracker(db_path=LORA_VERSIONS_DB)


# ---------------------------------------------------------------------------
# Background training wrapper (swallows + logs so 202 is never undone)
# ---------------------------------------------------------------------------


async def _run_training(
    trainer: SkyyRoseLoRATrainer,
    *,
    collections: list[str] | None,
    epochs: int,
    max_products: int | None,
    version: str | None,
) -> None:
    """Wrapper executed as a BackgroundTask.

    Catches all exceptions so Starlette never re-raises them after the 202
    response has been sent (e.g. ImportError when diffusers/peft are absent).
    """
    try:
        await trainer.train_from_products(
            collections=collections,
            epochs=epochs,
            max_products=max_products,
            version=version,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("LoRA background training failed: %s", exc, exc_info=True)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@lora_router.post("/train", status_code=202, response_model=TrainLoRAResponse)
async def start_lora_training(
    body: TrainLoRARequest,
    background_tasks: BackgroundTasks,
) -> TrainLoRAResponse:
    """Dispatch a LoRA fine-tuning run as a background task.

    Returns 202 immediately; training runs for hours on local GPU.
    Monitor progress via GET /api/v1/training/status.
    """
    trainer = SkyyRoseLoRATrainer(version_db_path=LORA_VERSIONS_DB)
    background_tasks.add_task(
        _run_training,
        trainer,
        collections=body.collections,
        epochs=body.epochs,
        max_products=body.max_products,
        version=body.version,
    )
    return TrainLoRAResponse(
        status="accepted",
        version=body.version,  # echoed back; None means auto-assigned after training
        message=(
            "LoRA training dispatched. Version will be assigned on completion when not specified."
        ),
        monitor="/api/v1/training/status",
    )


@lora_router.get("/dataset/preview", response_model=DatasetPreviewResponse)
async def preview_dataset(
    collections: str | None = None,
    max_products: int = 50,
) -> DatasetPreviewResponse:
    """Preview the training dataset without starting training.

    Args:
        collections: Comma-joined collection names (e.g. "SIGNATURE,BLACK_ROSE").
                     Omit to include all collections.
        max_products: Maximum products to fetch (default 50).
    """
    parsed_collections: list[str] | None = (
        [c.strip() for c in collections.split(",") if c.strip()] if collections else None
    )
    try:
        products = await fetch_products_from_woocommerce(
            collections=parsed_collections,
            max_products=max_products,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("WooCommerce fetch failed during dataset preview: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch products from WooCommerce. Check connectivity.",
        ) from exc

    total_images = sum(len(p.image_urls) for p in products)
    avg_quality = sum(p.quality_score for p in products) / len(products) if products else 0.0

    collection_counts: dict[str, int] = {}
    for p in products:
        collection_counts[p.collection] = collection_counts.get(p.collection, 0) + 1

    sample = [
        SampleProduct(
            sku=p.sku,
            name=p.name,
            collection=p.collection,
            image_count=len(p.image_urls),
            quality_score=p.quality_score,
        )
        for p in products[:5]
    ]

    return DatasetPreviewResponse(
        total_products=len(products),
        total_images=total_images,
        avg_quality_score=avg_quality,
        collections=collection_counts,
        sample_products=sample,
    )


@lora_router.get("/versions/{version}", response_model=LoRAVersionOut)
async def get_version_info(version: str) -> LoRAVersionOut:
    """Return metadata for a specific LoRA version.

    Raises 404 if the version does not exist in the database.
    """
    tracker = _make_tracker()
    try:
        await tracker.initialize()
        lv = await tracker.get_version(version)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=f"Version not found: {version}") from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("Version tracker error for %r: %s", version, exc, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="Failed to retrieve version from database.",
        ) from exc

    return _version_to_out(lv)


@lora_router.get("/products/{sku}/history", response_model=ProductHistoryResponse)
async def get_product_training_history(sku: str) -> ProductHistoryResponse:
    """Return all LoRA versions that included the given SKU.

    Returns an empty list (200) when the SKU has no training history.
    """
    tracker = _make_tracker()
    try:
        await tracker.initialize()
        versions = await tracker.get_product_history(sku)
    except Exception as exc:  # noqa: BLE001
        logger.error("Version tracker error for SKU %r: %s", sku, exc, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="Failed to retrieve product training history from database.",
        ) from exc

    return ProductHistoryResponse(
        sku=sku,
        versions=[_version_to_out(lv) for lv in versions],
    )
