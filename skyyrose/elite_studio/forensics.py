"""Forensic manifest writer + interactive confirmation gate.

Two complementary defenses from the design plan:

H5 — Per-render forensic manifest
---------------------------------
Every render writes a manifest.json alongside the output capturing the dossier
hash, full RAS prompt, model+version, vision-audit result, and output paths.
When a future render goes wrong, ``git log -p data/dossiers/{slug}.md`` plus
the manifest history binary-searches the regression in minutes.

H6 — Pre-render confirmation gate
---------------------------------
For interactive single-product CLI runs, ``confirm_prompt(prompt, dossier)``
prints the constructed RAS prompt + dossier slug + estimated cost and waits
for ``y`` before the paid API call. Uses the same STOP-AND-SHOW protocol the
project already enforces for FASHN, Gemini, and other paid actions.

Off in non-interactive contexts (no TTY, ``SKYYROSE_AUTO_CONFIRM=1`` env var,
or ``confirm_prompt(..., interactive=False)``).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_MANIFEST_ROOT = Path("renders/output")


def _utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _sha256_path(path: str | Path) -> str:
    p = Path(path)
    if not p.is_file():
        return ""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_bytes(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def manifest_dir_for(
    name_slug: str, root: str | Path | None = None, *, timestamp: str | None = None
) -> Path:
    """Compute (do not create) the directory where a manifest will land."""
    base = Path(root) if root else DEFAULT_MANIFEST_ROOT
    return base / name_slug / (timestamp or _utc_timestamp())


def write_manifest(
    *,
    product: dict,
    dossier_path: str | Path,
    ras_prompt: str,
    model: str,
    output_path: str | Path,
    vision_audit_result: dict | None = None,
    extra: dict | None = None,
    root: str | Path | None = None,
) -> Path:
    """Write a per-render forensic manifest. Returns the manifest path.

    Args:
        product: Merged product+dossier dict from get_product_with_dossier().
        dossier_path: Path to the dossier markdown file used for this render.
        ras_prompt: The full RAS prompt as sent to the generative model.
        model: Model identifier (e.g. ``gemini-3.1-flash-image-preview``).
        output_path: Path to the rendered image on disk.
        vision_audit_result: Optional dict from VisionAuditAgent.audit().to_dict().
        extra: Free-form additional metadata to embed.
        root: Override the manifest root directory (default: renders/output/).
    """
    name_slug = (product.get("dossier_slug") or product.get("sku") or "unknown").strip()
    target_dir = manifest_dir_for(name_slug, root)
    target_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema_version": 1,
        "product_name": product.get("name", ""),
        "sku": product.get("sku", ""),
        "collection": product.get("collection", ""),
        "dossier": {
            "slug": name_slug,
            "path": str(dossier_path),
            "sha256": _sha256_path(dossier_path),
        },
        "ras_prompt": ras_prompt,
        "ras_prompt_sha256": _sha256_bytes(ras_prompt),
        "model": model,
        "timestamp": datetime.now(UTC).isoformat(),
        "output": {
            "path": str(output_path),
            "sha256": _sha256_path(output_path),
        },
        "vision_audit_result": vision_audit_result or {},
    }
    if extra:
        manifest["extra"] = extra

    manifest_path = target_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    logger.info("forensic manifest written: %s", manifest_path)
    return manifest_path


def confirm_prompt(
    *,
    product: dict,
    ras_prompt: str,
    model: str,
    estimated_cost_usd: float,
    interactive: bool | None = None,
) -> bool:
    """Print STOP-AND-SHOW confirmation banner; return True iff user types 'y'.

    Off when:
      - ``interactive=False`` is passed explicitly (for batch jobs)
      - stdin is not a TTY (CI, piped input, daemonized runs)
      - ``SKYYROSE_AUTO_CONFIRM=1`` env var is set (advanced CLI flag)
    """
    if interactive is False:
        return True
    if interactive is None:
        if os.getenv("SKYYROSE_AUTO_CONFIRM") == "1":
            return True
        if not sys.stdin.isatty():
            return True

    name = product.get("name", "<unknown>")
    sku = product.get("sku", "<unknown>")
    slug = product.get("dossier_slug", "<unknown>")

    banner = (
        "\n"
        "STOP — Confirm before proceeding:\n\n"
        f"  Action  : RAS render (3D replica)\n"
        f"  Product : {name}\n"
        f"  SKU     : {sku}\n"
        f"  Dossier : data/dossiers/{slug}.md\n"
        f"  Model   : {model}\n"
        f"  Cost    : ~${estimated_cost_usd:.3f} per render\n"
        f"  Prompt  : {len(ras_prompt)} chars (first 240): {ras_prompt[:240]!r}…\n\n"
        "Proceed? [y/N] "
    )
    sys.stdout.write(banner)
    sys.stdout.flush()
    try:
        reply = input().strip().lower()
    except EOFError:
        return False
    return reply in {"y", "yes"}


def quarantine_path(name_slug: str, *, root: str | Path | None = None) -> Path:
    """Return the per-product quarantine directory for failed audits."""
    base = Path(root) if root else Path("renders/quarantine")
    target = base / name_slug / _utc_timestamp()
    target.mkdir(parents=True, exist_ok=True)
    return target


__all__ = [
    "DEFAULT_MANIFEST_ROOT",
    "manifest_dir_for",
    "write_manifest",
    "confirm_prompt",
    "quarantine_path",
]
