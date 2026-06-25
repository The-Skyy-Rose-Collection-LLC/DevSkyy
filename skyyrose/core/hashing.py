"""Content hashing + timestamp helpers — the project's one hash function.

Lives in ``skyyrose.core`` (the lowest dependency layer) so every module —
``master_registry``, ``asset_manifest``, and any future consumer — shares a
single SHA-256 implementation and a single ISO-timestamp format without
inverting the dependency flow (``core`` must not import from ``elite_studio``).
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path


def sha256_of_file(path: str | Path) -> str:
    """Full SHA-256 digest of a file — the hash pin. Format: ``sha256:<hex>``."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def now_iso() -> str:
    """UTC ISO-8601 timestamp at second resolution (the manifest stamp format)."""
    return datetime.now(UTC).isoformat(timespec="seconds")
