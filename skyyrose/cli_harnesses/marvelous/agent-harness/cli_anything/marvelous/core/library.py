"""Local garment template library for cli-anything-marvelous.

The library lives at ~/.cli_anything/marvelous/library/ by default.
Each entry is a subdirectory containing:
    meta.json    — LibraryEntry metadata
    garment.json — serialised Garment (optional, for pure-data templates)
    *.zpac       — source project file (optional)

Tests monkeypatch LIBRARY_DIR to a tmp_path.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from cli_anything.marvelous.core.garment import Garment
from cli_anything.marvelous.core.session import _locked_save_json

# Default location; tests monkeypatch this or set MARVELOUS_LIBRARY_DIR
LIBRARY_DIR = Path(
    os.environ.get("MARVELOUS_LIBRARY_DIR", "")
    or str(Path.home() / ".cli_anything" / "marvelous" / "library")
)


# ── Model ─────────────────────────────────────────────────────────────────


@dataclass
class LibraryEntry:
    """A garment template stored in the local library."""

    slug: str
    name: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    source_file: str = ""  # relative path inside library entry dir

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LibraryEntry":
        valid = {k for k in cls.__dataclass_fields__}
        d = {k: v for k, v in data.items() if k in valid}
        if "tags" in d and not isinstance(d["tags"], list):
            d["tags"] = []
        return cls(**d)


# ── CRUD ──────────────────────────────────────────────────────────────────


def _entry_dir(slug: str) -> Path:
    return LIBRARY_DIR / slug


def list_library() -> list[LibraryEntry]:
    """Return all library entries, sorted by slug."""
    if not LIBRARY_DIR.exists():
        return []
    entries: list[LibraryEntry] = []
    for meta_path in sorted(LIBRARY_DIR.glob("*/meta.json")):
        try:
            with meta_path.open(encoding="utf-8") as fh:
                entries.append(LibraryEntry.from_dict(json.load(fh)))
        except (json.JSONDecodeError, TypeError):
            continue
    return entries


def get_entry(slug: str) -> LibraryEntry:
    """Load a single library entry by slug.

    Raises:
        KeyError: Entry not found.
        ValueError: meta.json is malformed.
    """
    meta_path = _entry_dir(slug) / "meta.json"
    if not meta_path.exists():
        raise KeyError(f"Library entry '{slug}' not found")
    try:
        with meta_path.open(encoding="utf-8") as fh:
            return LibraryEntry.from_dict(json.load(fh))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed meta.json for '{slug}': {exc}") from exc


def import_project(
    source: str | Path,
    slug: str,
    name: str,
    description: str = "",
    tags: list[str] | None = None,
) -> LibraryEntry:
    """Import a .zpac/.zprj file into the library.

    Copies the file into the library directory under *slug* and writes
    a meta.json.

    Args:
        source:      Path to .zpac or .zprj file to import.
        slug:        Unique library identifier (e.g. "tshirt-basic").
        name:        Human-readable name.
        description: Optional description.
        tags:        Optional list of tags.

    Returns:
        The created LibraryEntry.

    Raises:
        FileNotFoundError: Source file does not exist.
        FileExistsError:   Library entry with that slug already exists.
        ValueError:        Source is not a .zpac or .zprj file.
    """
    src = Path(source)
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")
    if src.suffix.lower() not in (".zpac", ".zprj"):
        raise ValueError(f"Expected .zpac or .zprj, got: {src.suffix}")

    entry_dir = _entry_dir(slug)
    if entry_dir.exists():
        raise FileExistsError(
            f"Library entry '{slug}' already exists at {entry_dir}. "
            "Delete it first or choose a different slug."
        )

    entry_dir.mkdir(parents=True, exist_ok=True)
    dest = entry_dir / src.name
    shutil.copy2(str(src), str(dest))

    entry = LibraryEntry(
        slug=slug,
        name=name,
        description=description,
        tags=tags or [],
        source_file=src.name,
    )
    _locked_save_json(entry_dir / "meta.json", entry.to_dict())
    return entry


def delete_entry(slug: str) -> bool:
    """Remove a library entry and its files.

    Returns True if deleted, False if it did not exist.
    """
    entry_dir = _entry_dir(slug)
    if not entry_dir.exists():
        return False
    shutil.rmtree(str(entry_dir))
    return True


def entry_source_path(entry: LibraryEntry) -> Path | None:
    """Return the absolute path to the entry's source file, or None."""
    if not entry.source_file:
        return None
    p = _entry_dir(entry.slug) / entry.source_file
    return p if p.exists() else None
