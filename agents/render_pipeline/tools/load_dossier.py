"""Tool 1: Load the canonical dossier for a SKU.

Wraps `nano_banana.spec_builder.build_dna_from_sku`. Tier 2 contract:
the pipeline HARD-FAILS if the dossier is missing — we do not fall back
to inferred DNA. The whole point of Layer 3 is that the canonical truth
overrides whatever Gemini-vision describes from the (possibly defective)
on-disk image.

State writes (downstream tools read these):
    sku, product_name, collection, engine_override (if catalog-pinned)

Raises:
    KeyError: SKU not in catalog CSV.
    DossierMissingError: SKU has no dossier file.
"""

from __future__ import annotations

from agents.render_pipeline.tools._paths import ensure_repo_paths

ensure_repo_paths()

from google.adk.tools.tool_context import ToolContext


def load_dossier_fn(sku: str, tool_context: ToolContext) -> dict:
    """Load the canonical design spec for `sku`. State + return both populated.

    Args:
        sku: Canonical SKU code from `data/skyyrose-catalog.csv`.
        tool_context: ADK auto-injected; we use `tool_context.state` for cross-tool data flow.

    Returns:
        Dict with sku, name, collection, spec_chars, garment_type_lock excerpt,
        engine_override (None if not catalog-pinned). The full Dossier object
        stays out of the JSON return — downstream tools re-load via
        `build_dna_from_sku(sku)` (file read, idempotent, free).
    """
    from nano_banana.catalog import load_catalog
    from nano_banana.spec_builder import build_dna_from_sku

    dna = build_dna_from_sku(sku)  # raises if missing — Tier 2 hard-fail
    catalog = load_catalog()
    catalog_row = catalog.get(sku, {})

    name = dna.catalog.get("name", "")
    collection = dna.catalog.get("collection", "")
    engine_override = catalog_row.get("engine_override", "")

    tool_context.state["sku"] = sku
    tool_context.state["product_name"] = name
    tool_context.state["collection"] = collection
    if engine_override:
        tool_context.state["engine_override"] = engine_override

    type_lock_excerpt = ""
    if dna.dossier and dna.dossier.garment_type_lock:
        type_lock_excerpt = dna.dossier.garment_type_lock[:120]

    return {
        "sku": sku,
        "name": name,
        "collection": collection,
        "spec_chars": len(dna.spec or ""),
        "garment_type_lock_excerpt": type_lock_excerpt,
        "engine_override": engine_override or None,
        "loaded": True,
    }
