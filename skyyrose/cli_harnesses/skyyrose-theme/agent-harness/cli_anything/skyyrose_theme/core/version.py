"""
Version management for the SkyyRose theme.

Reads and writes the version string across three canonical files:
  - wordpress-theme/skyyrose-flagship/functions.php  (SKYYROSE_VERSION constant)
  - wordpress-theme/skyyrose-flagship/style.css       (Version: header)
  - wordpress-theme/skyyrose-flagship/readme.txt      (Stable tag: line)

All writes are atomic: temp file → fsync → os.replace (same directory).
The three files are written sequentially; on failure the caller can roll back
by re-running version bump --to <old-version>.
"""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Theme root resolution
# ---------------------------------------------------------------------------

_DEFAULT_THEME_ROOT = Path(
    os.environ.get(
        "SKYYROSE_THEME_ROOT",
        str(Path.home() / "DevSkyy/wordpress-theme/skyyrose-flagship"),
    )
)


def _theme_root() -> Path:
    """Return the resolved theme root directory."""
    root = Path(os.environ.get("SKYYROSE_THEME_ROOT", str(_DEFAULT_THEME_ROOT)))
    return root


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_FUNCTIONS_PHP_RE = re.compile(r"(define\s*\(\s*'SKYYROSE_VERSION'\s*,\s*')[^']+('\s*\))")
_STYLE_CSS_RE = re.compile(r"^(Version:\s*)(.+)$", re.MULTILINE)
_README_TXT_RE = re.compile(r"^(Stable tag:\s*)(.+)$", re.MULTILINE)


# ---------------------------------------------------------------------------
# Typed exceptions
# ---------------------------------------------------------------------------


class VersionError(RuntimeError):
    """Raised when version read/write fails."""


class VersionMismatchError(VersionError):
    """Raised when the three canonical version sources disagree."""


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VersionState:
    functions_php: str
    style_css: str
    readme_txt: str

    @property
    def consistent(self) -> bool:
        return self.functions_php == self.style_css == self.readme_txt

    @property
    def current(self) -> str:
        """Return the version if consistent, else raise."""
        if not self.consistent:
            raise VersionMismatchError(
                f"Version sources disagree: functions.php={self.functions_php!r}, "
                f"style.css={self.style_css!r}, readme.txt={self.readme_txt!r}"
            )
        return self.functions_php


# ---------------------------------------------------------------------------
# Readers
# ---------------------------------------------------------------------------


def _read_functions_php(theme_root: Path) -> str:
    path = theme_root / "functions.php"
    text = path.read_text(encoding="utf-8")
    m = _FUNCTIONS_PHP_RE.search(text)
    if not m:
        raise VersionError(f"SKYYROSE_VERSION constant not found in {path}")
    return m.group(0).split("'")[3]  # value between inner quotes


def _read_style_css(theme_root: Path) -> str:
    path = theme_root / "style.css"
    text = path.read_text(encoding="utf-8")
    m = _STYLE_CSS_RE.search(text)
    if not m:
        raise VersionError(f"Version: header not found in {path}")
    return m.group(2).strip()


def _read_readme_txt(theme_root: Path) -> str:
    path = theme_root / "readme.txt"
    text = path.read_text(encoding="utf-8")
    m = _README_TXT_RE.search(text)
    if not m:
        raise VersionError(f"Stable tag: line not found in {path}")
    return m.group(2).strip()


def read_version(theme_root: Path | None = None) -> VersionState:
    """Read version from all three canonical sources and return VersionState."""
    root = theme_root or _theme_root()
    return VersionState(
        functions_php=_read_functions_php(root),
        style_css=_read_style_css(root),
        readme_txt=_read_readme_txt(root),
    )


# ---------------------------------------------------------------------------
# Atomic writer
# ---------------------------------------------------------------------------


def _atomic_write(path: Path, content: str) -> None:
    """Write *content* to *path* atomically (temp + fsync + os.replace)."""
    dir_ = path.parent
    fd, tmp_path = tempfile.mkstemp(dir=dir_, prefix=".skyyrose-ver-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------


def _write_functions_php(theme_root: Path, new_version: str) -> None:
    path = theme_root / "functions.php"
    original = path.read_text(encoding="utf-8")
    updated, count = _FUNCTIONS_PHP_RE.subn(
        lambda m: m.group(1) + new_version + m.group(2),
        original,
    )
    if count == 0:
        raise VersionError(f"SKYYROSE_VERSION pattern not found in {path}")
    _atomic_write(path, updated)


def _write_style_css(theme_root: Path, new_version: str) -> None:
    path = theme_root / "style.css"
    original = path.read_text(encoding="utf-8")
    updated, count = _STYLE_CSS_RE.subn(
        lambda m: m.group(1) + new_version,
        original,
    )
    if count == 0:
        raise VersionError(f"Version: header not found in {path}")
    _atomic_write(path, updated)


def _write_readme_txt(theme_root: Path, new_version: str) -> None:
    path = theme_root / "readme.txt"
    original = path.read_text(encoding="utf-8")
    updated, count = _README_TXT_RE.subn(
        lambda m: m.group(1) + new_version,
        original,
    )
    if count == 0:
        raise VersionError(f"Stable tag: line not found in {path}")
    _atomic_write(path, updated)


def write_version(new_version: str, theme_root: Path | None = None) -> VersionState:
    """
    Atomically write *new_version* to all three canonical files.

    Precondition: the three files must currently agree on version.
    On any write failure the exception propagates; caller can roll back
    by calling write_version(<old_version>).

    Returns the resulting VersionState.
    """
    root = theme_root or _theme_root()
    # Precondition: sources must agree before we write.
    current = read_version(root)
    current.current  # raises VersionMismatchError if inconsistent

    _write_functions_php(root, new_version)
    _write_style_css(root, new_version)
    _write_readme_txt(root, new_version)

    return read_version(root)
