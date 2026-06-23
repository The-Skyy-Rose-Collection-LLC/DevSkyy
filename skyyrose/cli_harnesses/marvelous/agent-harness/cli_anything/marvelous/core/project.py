"""Marvelous Designer project file (.zpac / .zprj) parser.

.zpac and .zprj files are standard ZIP containers.  This module
extracts garment metadata from the archive without requiring
Marvelous Designer to be installed.

Archive layout (typical):
    project.json   — top-level metadata (name, version, creation date)
    garment.json   — pattern / fabric inventory
    fabric/        — per-fabric JSON or binary data
    pattern/       — per-pattern SVG or binary data
    thumbnail.png  — cover image
"""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cli_anything.marvelous.core.garment import (FabricProperty, Garment,
                                                 PatternPiece)

# ── Exceptions ────────────────────────────────────────────────────────────


class ProjectFileError(Exception):
    """Raised when a .zpac/.zprj file cannot be read or parsed."""


# ── Metadata model ────────────────────────────────────────────────────────


@dataclass
class ProjectMeta:
    """Lightweight metadata extracted from a .zpac/.zprj archive."""

    path: str
    name: str
    file_format: str  # "zpac" | "zprj"
    md_version: str = ""
    created_at: str = ""
    pattern_count: int = 0
    fabric_count: int = 0
    has_thumbnail: bool = False
    raw_manifest: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "name": self.name,
            "file_format": self.file_format,
            "md_version": self.md_version,
            "created_at": self.created_at,
            "pattern_count": self.pattern_count,
            "fabric_count": self.fabric_count,
            "has_thumbnail": self.has_thumbnail,
        }


# ── Parser ────────────────────────────────────────────────────────────────


def _read_zip_json(zf: zipfile.ZipFile, *candidates: str) -> dict[str, Any] | None:
    """Try each candidate filename and return parsed JSON, or None."""
    names_lower = {n.lower(): n for n in zf.namelist()}
    for cand in candidates:
        real = names_lower.get(cand.lower())
        if real:
            try:
                return json.loads(zf.read(real).decode("utf-8", errors="replace"))
            except (json.JSONDecodeError, KeyError):
                return None
    return None


def read_project_meta(path: str | Path) -> ProjectMeta:
    """Parse a .zpac or .zprj file and return its ProjectMeta.

    Only reads ZIP index + small JSON blobs — does not load textures or
    binary geometry data.

    Args:
        path: Filesystem path to the .zpac or .zprj file.

    Returns:
        ProjectMeta populated from the archive.

    Raises:
        FileNotFoundError: File does not exist.
        ProjectFileError: Not a valid ZIP/MD archive.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Project file not found: {p}")

    suffix = p.suffix.lower().lstrip(".")
    if suffix not in ("zpac", "zprj"):
        raise ProjectFileError(f"Unsupported format '{p.suffix}'. Expected .zpac or .zprj")

    if not zipfile.is_zipfile(p):
        raise ProjectFileError(f"File is not a valid ZIP archive: {p}")

    try:
        with zipfile.ZipFile(p, "r") as zf:
            names = zf.namelist()

            # Read top-level manifest
            manifest = _read_zip_json(zf, "project.json", "manifest.json") or {}

            # Garment inventory
            garment_data = _read_zip_json(zf, "garment.json", "data/garment.json") or {}

            pattern_count = len(garment_data.get("patterns", []))
            fabric_count = len(garment_data.get("fabrics", []))

            # Fallback: count from directory listing
            if pattern_count == 0:
                pattern_count = sum(
                    1 for n in names if "/pattern/" in n.lower() and not n.endswith("/")
                )
            if fabric_count == 0:
                fabric_count = sum(
                    1 for n in names if "/fabric/" in n.lower() and not n.endswith("/")
                )

            has_thumbnail = any(
                n.lower().endswith((".png", ".jpg", ".jpeg")) and "thumbnail" in n.lower()
                for n in names
            )

            name = manifest.get("name") or p.stem

            return ProjectMeta(
                path=str(p),
                name=name,
                file_format=suffix,
                md_version=str(manifest.get("md_version", manifest.get("version", ""))),
                created_at=str(manifest.get("created_at", manifest.get("date", ""))),
                pattern_count=pattern_count,
                fabric_count=fabric_count,
                has_thumbnail=has_thumbnail,
                raw_manifest=manifest,
            )

    except zipfile.BadZipFile as exc:
        raise ProjectFileError(f"Corrupt ZIP archive: {p}") from exc


def load_garment_from_project(path: str | Path) -> Garment:
    """Parse garment data from a .zpac/.zprj and return a Garment object.

    Best-effort: if the archive lacks structured JSON we return a Garment
    populated only from what the ZIP index reveals.

    Args:
        path: Filesystem path to the .zpac or .zprj file.

    Returns:
        Garment populated from archive contents.

    Raises:
        FileNotFoundError: File does not exist.
        ProjectFileError: Not a valid ZIP/MD archive.
    """
    meta = read_project_meta(path)
    p = Path(path)

    try:
        with zipfile.ZipFile(p, "r") as zf:
            garment_data = _read_zip_json(zf, "garment.json", "data/garment.json") or {}
    except zipfile.BadZipFile as exc:
        raise ProjectFileError(f"Corrupt ZIP archive: {p}") from exc

    # Build pattern pieces
    patterns: list[PatternPiece] = []
    for raw in garment_data.get("patterns", []):
        if isinstance(raw, dict):
            patterns.append(PatternPiece.from_dict(raw))
        elif isinstance(raw, str):
            patterns.append(PatternPiece(name=raw))

    # Build fabrics
    fabrics: list[FabricProperty] = []
    for raw in garment_data.get("fabrics", []):
        if isinstance(raw, dict):
            fabrics.append(FabricProperty.from_dict(raw))
        elif isinstance(raw, str):
            fabrics.append(FabricProperty(name=raw))

    return Garment(
        name=meta.name,
        source_file=str(p),
        patterns=patterns,
        fabrics=fabrics,
        simulation_frames=int(garment_data.get("simulation_frames", 100)),
        notes=garment_data.get("notes", ""),
    )
