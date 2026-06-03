"""Resolve a job's source image and guard against missing/ambiguous sources.

A paid 3D job must never dispatch without a confirmed canonical source. Priority:
  1. An explicit image path (must exist).
  2. SKU -> canonical flatlay: assets/product-source/<sku>__*/flatlay/
     preferring a file whose name starts with 'front', else first sorted image.
"""

from __future__ import annotations

import re
from pathlib import Path

_DEFAULT_SOURCE_ROOT = Path("assets/product-source")
_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")
#: Canonical SKU shape: prefix (br/lh/sg/kids) + 3-digit number, e.g. ``br-001``.
#: Enforced before any glob or output-path use so ``sku="*"`` / ``"../.."`` can
#: never widen a glob or escape the output dir into a wrong (paid) product job.
_SKU_RE = re.compile(r"^[a-z]{2,4}-\d{3}$")


class PreflightError(RuntimeError):
    """The source image could not be resolved — do not dispatch."""


def resolve_source(
    *,
    sku: str,
    image: str | Path | None = None,
    source_root: str | Path | None = None,
) -> Path:
    """Return the resolved source image path or raise PreflightError."""
    if not _SKU_RE.match(sku):
        raise PreflightError(f"invalid sku format: {sku!r} (expected like 'br-001')")
    if image is not None:
        p = Path(image)
        if not p.is_file():
            raise PreflightError(f"explicit image not found: {p}")
        return p

    root = Path(source_root) if source_root is not None else _DEFAULT_SOURCE_ROOT
    matches = sorted(root.glob(f"{sku}__*"))
    if not matches:
        raise PreflightError(f"no canonical source folder for sku={sku!r} under {root}")

    for folder in matches:
        flatlay = folder / "flatlay"
        if not flatlay.is_dir():
            continue
        images = sorted(p for p in flatlay.iterdir() if p.suffix.lower() in _IMAGE_EXTS)
        if not images:
            continue
        for img in images:
            if img.name.lower().startswith("front"):
                return img
        return images[0]

    raise PreflightError(f"no flatlay image found for sku={sku!r} under {root}")


__all__ = ["resolve_source", "PreflightError"]
