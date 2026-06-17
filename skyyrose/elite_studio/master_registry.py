"""
Master product registry — hash-pinning registry for locked product reference imagery.

Wave 1 of the commercial compositor retrofit: **reference-first pipeline**.

A "master" is the immutable, locked image that represents a product exactly. All downstream
renders (compositor scene variants, marketing derivatives) MUST derive from a master — never
from a generated variant. This module enforces that by hash-pinning.

NOTE (2026-06-16 SOT cutover): The old `assets/product-masters/` tree (manifest.json +
catalog.yaml) was deleted. That directory now holds only a README. Product data (SKUs, names,
prices, collection membership) is authoritative in `data/skyyrose-catalog.csv`, accessed via
`skyyrose.core.catalog_loader.read_catalog_rows`. This module's hash-pinning machinery
(`Manifest`, `MasterEntry`, `sha256_of_file`) remains intact for render provenance; the
default manifest path resolves to the same directory but will load an empty manifest when no
manifest.json is present. Override via `SKYYROSE_MASTER_MANIFEST_PATH` (used by tests).

Master sources (`master_source` field):
    photograph        — physical product photographed against neutral background
    cad_render        — rendered from CAD / tech pack (for pre-order SKUs)
    3d_model          — rendered deterministically from a 3D model (e.g., Meshy output)
    generative_locked — one-time generative output, locked by hash forever

Intentionally does NOT enforce at runtime yet — enforcement becomes Wave 2 once the
manifest is populated for all live SKUs.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

MasterSource = Literal["photograph", "cad_render", "3d_model", "generative_locked", "pending"]
MasterStatus = Literal["pending", "locked", "retired"]

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
# NOTE: assets/product-masters/ exists but holds only a README; manifest.json was deleted
# in the SOT cutover (2026-06-16).  Manifest.load() returns an empty Manifest when the file
# is absent, so this default is safe.  Override via SKYYROSE_MASTER_MANIFEST_PATH in tests.
_DEFAULT_MASTERS_DIR = _REPO_ROOT / "assets" / "product-masters"
_MANIFEST_FILENAME = "manifest.json"


def masters_dir() -> Path:
    override = os.environ.get("SKYYROSE_MASTER_MANIFEST_PATH")
    if override:
        return Path(override).parent
    return _DEFAULT_MASTERS_DIR


def manifest_path() -> Path:
    override = os.environ.get("SKYYROSE_MASTER_MANIFEST_PATH")
    if override:
        return Path(override)
    return _DEFAULT_MASTERS_DIR / _MANIFEST_FILENAME


def sha256_of_file(path: str | Path) -> str:
    """Full SHA-256 digest of a file — the hash pin. Format: 'sha256:<hex>'."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


@dataclass(frozen=True)
class MasterEntry:
    """One canonical product reference. Immutable once status='locked'."""

    sku: str
    master_path: str  # relative to masters_dir(); "" when status=pending
    master_hash: str | None  # 'sha256:<hex>' when locked; None when pending
    master_source: MasterSource
    status: MasterStatus = "locked"
    collection: str = ""
    alpha_path: str | None = None
    alpha_hash: str | None = None
    color_spec: dict[str, Any] = field(default_factory=dict)
    text_spec: list[str] = field(default_factory=list)
    photographed_at: str | None = None  # ISO-8601 UTC
    locked_at_version: str | None = None
    notes: str = ""

    @property
    def is_locked(self) -> bool:
        return self.status == "locked" and self.master_hash is not None

    def resolved_master_path(self, base: Path | None = None) -> Path:
        return (base or masters_dir()) / self.master_path

    def resolved_alpha_path(self, base: Path | None = None) -> Path | None:
        if not self.alpha_path:
            return None
        return (base or masters_dir()) / self.alpha_path


@dataclass
class Manifest:
    version: int = 1
    generated_at: str = ""
    masters: dict[str, MasterEntry] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | None = None) -> Manifest:
        p = path or manifest_path()
        if not p.exists():
            return cls(version=1, generated_at=_now_iso(), masters={})
        raw = json.loads(p.read_text(encoding="utf-8"))
        masters = {sku: MasterEntry(**entry) for sku, entry in raw.get("masters", {}).items()}
        return cls(
            version=int(raw.get("version", 1)),
            generated_at=raw.get("generated_at", ""),
            masters=masters,
        )

    def save(self, path: Path | None = None) -> Path:
        """Atomic write. Updates generated_at to now."""
        p = path or manifest_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        self.generated_at = _now_iso()
        payload = {
            "version": self.version,
            "generated_at": self.generated_at,
            "masters": {sku: asdict(entry) for sku, entry in self.masters.items()},
        }
        with tempfile.NamedTemporaryFile(
            "w", dir=p.parent, prefix=".manifest-", suffix=".tmp", delete=False, encoding="utf-8"
        ) as f:
            json.dump(payload, f, indent=2, sort_keys=False)
            tmp = Path(f.name)
        os.replace(tmp, p)
        return p

    def get(self, sku: str) -> MasterEntry | None:
        return self.masters.get(sku)

    def require(self, sku: str) -> MasterEntry:
        entry = self.get(sku)
        if entry is None:
            raise KeyError(f"no master registered for sku={sku!r}")
        return entry

    def list_skus(self) -> list[str]:
        return sorted(self.masters.keys())

    def register(
        self,
        *,
        sku: str,
        master_path: str,
        master_source: MasterSource,
        base_dir: Path | None = None,
        alpha_path: str | None = None,
        collection: str = "",
        color_spec: dict[str, Any] | None = None,
        text_spec: Iterable[str] | None = None,
        photographed_at: str | None = None,
        locked_at_version: str | None = None,
        notes: str = "",
        overwrite: bool = False,
    ) -> MasterEntry:
        """Register a new master. Hashes the file(s) at registration time."""
        if sku in self.masters and not overwrite:
            raise ValueError(
                f"master already registered for sku={sku!r} (pass overwrite=True to replace)"
            )
        base = base_dir or masters_dir()
        master_file = base / master_path
        if not master_file.exists():
            raise FileNotFoundError(f"master file not found: {master_file}")
        master_hash = sha256_of_file(master_file)

        alpha_hash: str | None = None
        if alpha_path:
            alpha_file = base / alpha_path
            if not alpha_file.exists():
                raise FileNotFoundError(f"alpha file not found: {alpha_file}")
            alpha_hash = sha256_of_file(alpha_file)

        entry = MasterEntry(
            sku=sku,
            master_path=master_path,
            master_hash=master_hash,
            master_source=master_source,
            collection=collection,
            alpha_path=alpha_path,
            alpha_hash=alpha_hash,
            color_spec=dict(color_spec or {}),
            text_spec=list(text_spec or []),
            photographed_at=photographed_at,
            locked_at_version=locked_at_version,
            notes=notes,
        )
        self.masters[sku] = entry
        return entry

    def verify(self, sku: str, image_path: str | Path, base_dir: Path | None = None) -> bool:
        """Return True iff the given file's hash matches the registered master_hash."""
        entry = self.get(sku)
        if entry is None or not entry.is_locked:
            return False
        actual = sha256_of_file(image_path)
        return actual == entry.master_hash

    def register_pending(
        self,
        *,
        sku: str,
        collection: str = "",
        color_spec: dict[str, Any] | None = None,
        text_spec: Iterable[str] | None = None,
        notes: str = "",
        overwrite: bool = False,
    ) -> MasterEntry:
        """Reserve a catalog slot without a file yet. Transition to locked via `lock()`."""
        if sku in self.masters and not overwrite:
            raise ValueError(
                f"master already registered for sku={sku!r} (pass overwrite=True to replace)"
            )
        entry = MasterEntry(
            sku=sku,
            master_path="",
            master_hash=None,
            master_source="pending",
            status="pending",
            collection=collection,
            color_spec=dict(color_spec or {}),
            text_spec=list(text_spec or []),
            notes=notes,
        )
        self.masters[sku] = entry
        return entry

    def lock(
        self,
        *,
        sku: str,
        master_path: str,
        master_source: MasterSource,
        base_dir: Path | None = None,
        alpha_path: str | None = None,
        photographed_at: str | None = None,
        locked_at_version: str | None = None,
    ) -> MasterEntry:
        """Transition a pending entry to locked by hashing the supplied files."""
        if master_source in ("pending",):
            raise ValueError("lock() requires a concrete master_source (not 'pending')")
        existing = self.get(sku)
        if existing is None:
            raise KeyError(f"no pending or locked entry for sku={sku!r}")
        if existing.status == "locked":
            raise ValueError(
                f"sku={sku!r} is already locked at version={existing.locked_at_version!r}; "
                "re-locking would overwrite immutable provenance"
            )
        base = base_dir or masters_dir()
        master_file = base / master_path
        if not master_file.exists():
            raise FileNotFoundError(f"master file not found: {master_file}")
        master_hash = sha256_of_file(master_file)
        alpha_hash: str | None = None
        if alpha_path:
            alpha_file = base / alpha_path
            if not alpha_file.exists():
                raise FileNotFoundError(f"alpha file not found: {alpha_file}")
            alpha_hash = sha256_of_file(alpha_file)
        entry = MasterEntry(
            sku=sku,
            master_path=master_path,
            master_hash=master_hash,
            master_source=master_source,
            status="locked",
            collection=existing.collection,
            alpha_path=alpha_path,
            alpha_hash=alpha_hash,
            color_spec=dict(existing.color_spec),
            text_spec=list(existing.text_spec),
            photographed_at=photographed_at,
            locked_at_version=locked_at_version,
            notes=existing.notes,
        )
        self.masters[sku] = entry
        return entry


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
