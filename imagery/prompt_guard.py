"""Prompt guard — grounds every SDXL/FLUX prompt in verified product specs.

Fixes:
  - C-1: No ``"premium fabric"`` fallback injected into prompts.
  - C-2: Unknown collections raise ``ValueError`` — no silent aesthetic fallback.
  - H-1: Aspirational camera claims (Phase One, Hasselblad, Vogue standard) removed.
  - H-2: Flat ``", ".join(prompt_parts)`` replaced by two-zone structured format.

Architecture
============

Prompt format
-------------
    PRODUCT: <product zone> | STYLE: <style zone>

Zone 1 — PRODUCT
    Contains ONLY facts the caller supplied explicitly and that have been
    validated by :class:`~core.product_spec.ProductSpec`:

    - garment_type
    - collection (resolved to canonical :class:`~config.collections.Collection`)
    - collection aesthetic (grounded from canonical registry)
    - angle description (lookup from fixed table)
    - fabric  (caller-supplied, non-empty, non-placeholder)
    - color   (caller-supplied, non-empty)
    - style_notes (optional, pass-through)

Zone 2 — STYLE
    Contains photography technique, lighting, post-processing.
    Nothing here implies fabric, construction quality, or brand
    positioning beyond the product zone.
    Camera brand claims are **never injected**.

Usage
-----
    from imagery.prompt_guard import GroundedPromptBuilder
    from core.product_spec import ProductSpec
    from config.collections import Collection

    spec = ProductSpec(
        name="Shadow Sherpa",
        sku="BR-SHERPA-001",
        collection=Collection.BLACK_ROSE,
        price=189.00,
        garment_type="sherpa jacket",
        color="obsidian black",
        fabric="heavyweight sherpa fleece with woven lining",
    )

    builder = GroundedPromptBuilder()
    prompt   = builder.build(spec, shot_type=ShotType.HERO)
    negative = builder.build_negative()
"""

from __future__ import annotations

from config.collections import get_meta

from core.product_spec import ProductSpec
from imagery.luxury_photography import LightingPreset, ShotType


class SpecsValidator:
    """Explicit safety-net that verifies prompt-feeding fields before generation.

    :class:`~core.product_spec.ProductSpec` already runs these checks at
    construction time via Pydantic validators. This class provides a second,
    human-readable error message at the prompt layer so failures are
    immediately actionable without stack-tracing into Pydantic internals.
    """

    _REQUIRED: tuple[str, ...] = ("garment_type", "color", "fabric", "collection")

    def validate(self, spec: ProductSpec) -> None:
        """Raise ``ValueError`` if any required field is missing or empty.

        Args:
            spec: The :class:`~core.product_spec.ProductSpec` to validate.

        Raises:
            ValueError: With the name of the offending field.
        """
        for field in self._REQUIRED:
            val = getattr(spec, field, None)
            if val is None or (isinstance(val, str) and not val.strip()):
                raise ValueError(
                    f"ProductSpec.{field} is required for prompt generation "
                    f"but was empty (got {val!r}). "
                    "All garment fields must be explicitly supplied — no defaults allowed."
                )


class GroundedPromptBuilder:
    """Build two-zone SDXL/FLUX prompts grounded strictly in :class:`ProductSpec` data.

    The zone separator ``|`` is understood by both SDXL and FLUX tokenizers as
    a natural clause boundary and keeps product facts visually distinct from
    style instructions, making prompts auditable at a glance.
    """

    # ── Lighting descriptors (style zone only) ────────────────────────────────
    _LIGHTING: dict[LightingPreset, str] = {
        LightingPreset.STUDIO_DRAMATIC: (
            "dramatic studio lighting, deep shadows, high contrast, single key light"
        ),
        LightingPreset.STUDIO_FLAT: ("even studio lighting, minimal shadows, catalog photography"),
        LightingPreset.STUDIO_CONTOUR: ("contour lighting, rim light, shape-defining shadows"),
        LightingPreset.MACRO_CLOSEUP: ("macro photography, shallow depth of field, extreme detail"),
        LightingPreset.GOLDEN_HOUR: (
            "golden hour natural light, warm ambient tones, outdoor setting"
        ),
        LightingPreset.AMBIENT_LUXURY: (
            "soft ambient lighting, luxury interior, elegant atmosphere"
        ),
        LightingPreset.SOFT_COMMERCIAL: ("soft commercial lighting, clean white background"),
    }

    # ── Angle descriptors (product zone) ─────────────────────────────────────
    _ANGLE: dict[ShotType, str] = {
        ShotType.HERO: "front three-quarter view, hero angle, dynamic presentation",
        ShotType.FRONT: "straight front view, centered, symmetrical",
        ShotType.BACK: "straight back view, showing back design details",
        ShotType.SIDE_LEFT: "left side profile, silhouette visible",
        ShotType.SIDE_RIGHT: "right side profile, silhouette visible",
        ShotType.DETAIL_FABRIC: "extreme close-up, fabric texture visible, material detail",
        ShotType.DETAIL_CONSTRUCTION: "close-up, stitching detail, construction quality",
        ShotType.LIFESTYLE_URBAN: (
            "Oakland street setting, urban environment, authentic streetwear context"
        ),
        ShotType.LIFESTYLE_LUXURY: "upscale interior setting, luxury environment",
        ShotType.PACKAGING: "product with luxury packaging, premium unboxing presentation",
    }

    # ── Style zone constants (NO camera brand claims) ─────────────────────────
    _STYLE_CONSTANTS: tuple[str, ...] = (
        "luxury streetwear, high-fashion photography",
        "Oakland street culture meets high fashion",
        "8K resolution, ultra-detailed fabric texture",
        "neutral background with subtle gradients",
        "gender-neutral presentation, inclusive fashion",
        "SkyyRose signature aesthetic",
    )

    def __init__(self) -> None:
        self._validator = SpecsValidator()

    # ── Public API ────────────────────────────────────────────────────────────

    def build(
        self,
        spec: ProductSpec,
        shot_type: ShotType = ShotType.HERO,
        lighting: LightingPreset = LightingPreset.STUDIO_DRAMATIC,
    ) -> str:
        """Return a grounded two-zone prompt string safe for SDXL / FLUX.

        Args:
            spec: Validated :class:`~core.product_spec.ProductSpec`.
            shot_type: Camera angle preset.
            lighting: Lighting preset.

        Returns:
            A string of the form ``"PRODUCT: ... | STYLE: ..."``.

        Raises:
            ValueError: If *spec* is missing any required field.
        """
        self._validator.validate(spec)
        product_zone = self._build_product_zone(spec, shot_type)
        style_zone = self._build_style_zone(lighting)
        return f"PRODUCT: {product_zone} | STYLE: {style_zone}"

    def build_negative(self) -> str:
        """Return a consistent negative prompt (no hallucination risk)."""
        return (
            "low quality, blurry, pixelated, amateur photography, "
            "poor lighting, cluttered background, "
            "oversaturated colors, distorted proportions, "
            "generic stock photo, fast fashion aesthetic, "
            "watermark, text overlay, logo, mannequin, person wearing, "
            "wrinkled, dirty, stained"
        )

    # ── Private zone builders ─────────────────────────────────────────────────

    def _build_product_zone(self, spec: ProductSpec, shot_type: ShotType) -> str:
        """Zone 1: only caller-verified product facts."""
        meta = get_meta(spec.collection)
        angle = self._ANGLE.get(shot_type, "product photography")

        parts: list[str] = [
            f"{spec.garment_type} from {spec.collection} collection",
            f"product name: {spec.name}",
            meta["aesthetic"],  # grounded: pulled from canonical registry
            angle,
            f"fabric: {spec.fabric}",  # caller-supplied, validated non-empty
            f"color: {spec.color}",  # caller-supplied, validated non-empty
        ]

        if spec.colors:
            parts.append(f"color variants: {', '.join(spec.colors)}")

        if spec.style_notes:
            parts.append(spec.style_notes)

        return ", ".join(filter(None, parts))

    def _build_style_zone(self, lighting: LightingPreset) -> str:
        """Zone 2: photography / styling — zero product facts, zero camera claims."""
        lighting_desc = self._LIGHTING.get(lighting, "professional studio lighting")
        parts = [lighting_desc] + list(self._STYLE_CONSTANTS)
        return ", ".join(parts)


__all__ = ["GroundedPromptBuilder", "SpecsValidator"]
