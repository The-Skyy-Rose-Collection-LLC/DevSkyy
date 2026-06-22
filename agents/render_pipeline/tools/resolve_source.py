"""Tool 2: Resolve source image path for a SKU.

Reuses the verified 4-fallback resolver from `_validate_pipeline_multi_sku`:
    1. Catalog `source_override` (CSV-pinned filename)
    2. Bundle dir `source-photo.{ext}` or `photo-front.{ext}` (real photo)
    3. Exact-stem match `{sku}.{ext}` in products dir
    4. Glob `{sku}-*.{ext}` excluding -back/-composite/-detail variants

Per F2 (verified empirically on br-001), source-strategy is NOT the
dominant signal — render/techflat/source-photo all scored within 3 pts
on br-001. So this tool defers to whatever the resolver finds first;
no per-strategy override needed at the agent level.

State writes:
    source_path (str — Path object can't go in JSON state)
"""

from __future__ import annotations

from pathlib import Path

from agents.render_pipeline.tools._paths import REPO_ROOT, ensure_repo_paths

ensure_repo_paths()

from google.adk.tools.tool_context import ToolContext


def _resolve(sku: str, name: str, src_override: str) -> Path | None:
    """Verified resolver — copied verbatim from _validate_pipeline_multi_sku.

    Kept inline to avoid coupling the agent to the validator script
    (which is marked NOT FOR CI; the agent is the production path going
    forward). Resolution order matches the validator's tested behavior.
    """
    img_dir = REPO_ROOT / "wordpress-theme/skyyrose-flagship/assets/images/products"
    bundle_dir = REPO_ROOT / "data/product-bundles" / name if name else None

    candidates: list[Path] = []
    if src_override:
        candidates.append(img_dir / src_override)

    if bundle_dir:
        for tag in ("source-photo", "photo-front"):
            for ext in ("jpg", "jpeg", "png", "webp"):
                candidates.append(bundle_dir / f"{tag}.{ext}")

    skip_substrings = ("-back", "-composite", "-detail", "-real-")
    for ext in ("jpg", "jpeg", "png", "webp"):
        candidates.append(img_dir / f"{sku}.{ext}")
    for ext in ("jpg", "jpeg", "png", "webp"):
        for match in sorted(img_dir.glob(f"{sku}-*.{ext}")):
            if any(s in match.name.lower() for s in skip_substrings):
                continue
            candidates.append(match)

    return next((c for c in candidates if c.exists()), None)


def resolve_source_fn(sku: str, tool_context: ToolContext) -> dict:
    """Resolve the source image for a SKU. Writes path string to state.

    Returns dict with sku, source_path (str|None), filename, size_kb,
    error (only on failure). Downstream tools read state["source_path"]
    rather than the return — the LLM may not echo the full path back.
    """
    from nano_banana.catalog import load_catalog

    catalog = load_catalog()
    row = catalog.get(sku, {})
    name = row.get("name", "")
    src_override = row.get("source_override", "")

    src_path = _resolve(sku, name, src_override)
    if not src_path:
        return {
            "sku": sku,
            "source_path": None,
            "error": f"no source image found (override={src_override!r}, name={name!r})",
        }

    tool_context.state["source_path"] = str(src_path)
    return {
        "sku": sku,
        "source_path": str(src_path),
        "filename": src_path.name,
        "size_kb": round(src_path.stat().st_size / 1024, 1),
    }
