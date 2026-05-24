"""
Collection Page Manager
=======================

Design templates and metadata for the SkyyRose collections. Used by Python
agents for consistency checks, recovery prompts, and LLM context — not for
rendering (that happens in PHP/WordPress).

**This module is a thin adapter.** Authoritative data lives in:
  - `assets/brand/brand.yaml`                                       (via skyyrose.elite_studio.brand)
  - `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`   (via skyyrose.elite_studio.catalog
                                                                     → skyyrose.core.catalog_loader)

Do not hardcode collection metadata here. Edit brand.yaml or the catalog CSV.
The legacy `assets/product-masters/catalog.yaml` was retired on 2026-04-19.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from skyyrose.elite_studio.brand import BrandConfig
from skyyrose.elite_studio.catalog import Catalog


class CollectionType(StrEnum):
    """The four SkyyRose product collections. Values match brand.yaml slugs."""

    BLACK_ROSE = "black-rose"
    LOVE_HURTS = "love-hurts"
    SIGNATURE = "signature"
    KIDS = "kids"


# WordPress template paths per collection. These aren't brand data (they're
# deployment config), so they live here rather than in brand.yaml.
_HTML_PATHS: dict[CollectionType, str] = {
    CollectionType.BLACK_ROSE: "wordpress-theme/skyyrose-flagship/template-collection-black-rose.php",
    CollectionType.LOVE_HURTS: "wordpress-theme/skyyrose-flagship/template-collection-love-hurts.php",
    CollectionType.SIGNATURE: "wordpress-theme/skyyrose-flagship/template-collection-signature.php",
    CollectionType.KIDS: "wordpress-theme/skyyrose-flagship/template-collection-kids-capsule.php",
}


@dataclass
class CollectionTemplate:
    """Design specification for one collection (assembled from brand + catalog)."""

    name: str
    theme: str
    description: str
    colors: dict[str, str]
    html_file_path: str
    metadata: dict[str, Any] | None = field(default=None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "theme": self.theme,
            "description": self.description,
            "colors": self.colors,
            "html_file_path": self.html_file_path,
            "metadata": self.metadata or {},
        }


def _build_template(
    ctype: CollectionType,
    brand: BrandConfig | None = None,
    catalog: Catalog | None = None,
) -> CollectionTemplate:
    """Assemble a CollectionTemplate from brand.yaml + catalog.yaml. Pure read — no mutation."""
    brand = brand or BrandConfig.load()
    catalog = catalog or Catalog.load()

    slug = ctype.value
    cb = brand.collection(slug)
    product_skus = [p.sku for p in catalog.products_in_collection(slug, active_only=True)]

    return CollectionTemplate(
        name=(
            f"{cb.display_name.title()} Collection"
            if cb.display_name.isupper()
            else f"{cb.display_name} Collection"
        ),
        theme=cb.theme,
        description=cb.description,
        colors=dict(cb.palette),
        html_file_path=_HTML_PATHS[ctype],
        metadata={
            "target_audience": cb.target_audience,
            "tagline": brand.tagline_active,
            "mood": cb.mood,
            "inspiration": cb.inspiration,
            "hero_scene": cb.hero_scene,
            "products": product_skus,
        },
    )


class CollectionDesignTemplates:
    """
    Registry of SkyyRose collection design templates.

    Templates are assembled on-demand from brand.yaml + catalog.yaml, so changes
    to either SoT are reflected on the next call. All methods are class-level —
    no instantiation required.
    """

    @classmethod
    def get_template(cls, collection: CollectionType) -> CollectionTemplate:
        """Return the design template for a collection."""
        return _build_template(collection)

    @classmethod
    def get_all_templates(cls) -> dict[CollectionType, CollectionTemplate]:
        """Return all templates keyed by CollectionType."""
        brand = BrandConfig.load()
        catalog = Catalog.load()
        return {ct: _build_template(ct, brand=brand, catalog=catalog) for ct in CollectionType}

    @classmethod
    def to_agent_reference(cls, collection: CollectionType) -> dict[str, Any]:
        """Serializable dict suitable for LLM prompt injection or recovery reference."""
        t = _build_template(collection)
        return {
            "collection": collection.value,
            "name": t.name,
            "theme": t.theme,
            "description": t.description,
            "colors": t.colors,
            "html_file_path": t.html_file_path,
            "metadata": t.metadata or {},
            "recovery_steps": [
                f"Restore primary color to {t.colors.get('primary', '')}",
                f"Restore secondary color to {t.colors.get('secondary', '')}",
                f"Restore accent color to {t.colors.get('accent', '')}",
                f"Reset theme to: {t.theme}",
                f"Reference HTML template: {t.html_file_path}",
            ],
        }


__all__ = ["CollectionType", "CollectionDesignTemplates", "CollectionTemplate"]
