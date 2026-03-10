"""Unified product specification — single source of truth for all pipelines.

Fixes:
  - C-4: Empty ``color`` / ``fabric`` strings no longer silently pass to FLUX/SDXL.
  - C-5: No ``material = "premium fabric"`` default — fabric is mandatory.
  - Issue 1 (cross-cutting): Three incompatible spec types unified into one.

All pipeline entry points accept :class:`ProductSpec`.
Legacy dataclasses (ProductConcept, DesignSpecs) are converted via the
adapter helpers :func:`from_concept` and :func:`from_design_specs`.
"""

from __future__ import annotations

import warnings

from config.collections import Collection, get_collection, get_meta
from pydantic import BaseModel, Field, field_validator, model_validator


class ProductSpec(BaseModel):
    """Validated, immutable product specification.

    Every field that flows into a generative prompt is **required and
    non-empty**. The model is frozen after construction so no downstream code
    can silently mutate a spec that has already been validated.
    """

    # ── Identity ──────────────────────────────────────────────────────────────
    name: str = Field(..., min_length=1, description="Product display name")
    sku: str = Field(..., min_length=1, description="Unique product SKU")
    collection: Collection = Field(..., description="SkyyRose collection")
    price: float = Field(..., gt=0, description="Retail price in USD")

    # ── Garment (all feed into SDXL / FLUX prompts) ───────────────────────────
    garment_type: str = Field(..., min_length=1, description="e.g. 'oversized hoodie' — no default")
    color: str = Field(..., min_length=1, description="Primary color description — no default")
    fabric: str = Field(
        ..., min_length=1, description="Fabric description — no default, never 'premium fabric'"
    )

    # ── Optional ──────────────────────────────────────────────────────────────
    colors: list[str] = Field(default_factory=list, description="All available colorways")
    sizes: list[str] = Field(default_factory=lambda: ["XS", "S", "M", "L", "XL", "2XL"])
    style_notes: str = ""
    require_approval: bool = False

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("name", "sku", "garment_type", "color", "fabric", mode="before")
    @classmethod
    def must_not_be_empty(cls, v: object) -> str:
        """Reject empty or whitespace-only strings for all prompt-feeding fields."""
        if not isinstance(v, str) or not v.strip():
            raise ValueError(
                f"field must be a non-empty string, got {v!r}. "
                "All product fields that feed into generative prompts are required."
            )
        return v.strip()

    @field_validator("fabric", mode="after")
    @classmethod
    def fabric_not_placeholder(cls, v: str) -> str:
        """Prevent the historic 'premium fabric' placeholder from sneaking in."""
        if v.lower().strip() in {"premium fabric", "fabric", "material", ""}:
            raise ValueError(
                f"fabric value {v!r} is a placeholder, not a real material. "
                "Supply the actual fabric (e.g. 'heavyweight brushed cotton fleece')."
            )
        return v

    @field_validator("collection", mode="before")
    @classmethod
    def resolve_collection(cls, v: object) -> Collection:
        """Accept string keys and resolve to a :class:`Collection` enum value."""
        if isinstance(v, Collection):
            return v
        return get_collection(str(v))

    @model_validator(mode="after")
    def validate_price_range(self) -> ProductSpec:
        """Warn (do not block) if price falls outside the collection's expected range."""
        lo, hi = get_meta(self.collection)["price_range"]
        if not (lo <= self.price <= hi):
            warnings.warn(
                f"Price ${self.price:.2f} is outside {self.collection} range "
                f"(${lo}–${hi}). Proceeding with supplied value.",
                UserWarning,
                stacklevel=2,
            )
        return self

    model_config = {"frozen": True}


# ── Adapter helpers ───────────────────────────────────────────────────────────


def from_concept(concept: dict) -> ProductSpec:
    """Convert a legacy ``ProductConcept`` dict to :class:`ProductSpec`.

    Maps ``sku_base`` → ``sku``; passes ``style_notes`` through.
    """
    return ProductSpec(
        name=concept["name"],
        sku=concept.get("sku_base") or concept.get("sku", ""),
        collection=concept["collection"],
        price=concept["price"],
        garment_type=concept["garment_type"],
        color=concept["color"],
        fabric=concept["fabric"],
        style_notes=concept.get("style_notes", ""),
    )


def from_design_specs(specs: object) -> ProductSpec:
    """Convert a ``DesignSpecs`` dataclass instance to :class:`ProductSpec`.

    Raises ``ValueError`` (via ProductSpec validators) if ``specs.material`` is
    the historic ``"premium fabric"`` placeholder.
    """
    return ProductSpec(
        name=specs.name,  # type: ignore[attr-defined]
        sku=specs.sku,  # type: ignore[attr-defined]
        collection=specs.collection,  # type: ignore[attr-defined]
        price=specs.price,  # type: ignore[attr-defined]
        garment_type=specs.garment_type,  # type: ignore[attr-defined]
        color=specs.colors[0] if getattr(specs, "colors", []) else "",
        fabric=specs.material,  # type: ignore[attr-defined]
        colors=getattr(specs, "colors", []),
        sizes=getattr(specs, "sizes", ["XS", "S", "M", "L", "XL", "2XL"]),
        require_approval=getattr(specs, "require_approval", False),
    )


__all__ = ["ProductSpec", "from_concept", "from_design_specs"]
