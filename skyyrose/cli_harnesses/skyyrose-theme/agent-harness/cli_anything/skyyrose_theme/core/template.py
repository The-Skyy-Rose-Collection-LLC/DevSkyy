"""
Template discovery for the SkyyRose theme.

Parses the $template_map array from inc/enqueue.php to build a
slug → template-file mapping, then enriches it by globbing all
template-*.php files in the theme root.

No PHP interpreter needed — pure regex against the PHP source text.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

_DEFAULT_THEME_ROOT = Path(
    os.environ.get(
        "SKYYROSE_THEME_ROOT",
        str(Path.home() / "DevSkyy/wordpress-theme/skyyrose-flagship"),
    )
)


def _theme_root() -> Path:
    return Path(os.environ.get("SKYYROSE_THEME_ROOT", str(_DEFAULT_THEME_ROOT)))


# ---------------------------------------------------------------------------
# Typed exceptions
# ---------------------------------------------------------------------------


class TemplateError(RuntimeError):
    """Raised when template discovery fails."""


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TemplateInfo:
    slug: str | None  # None if not in enqueue.php $template_map
    filename: str  # e.g. "template-about.php"
    path: Path  # absolute path

    @property
    def exists(self) -> bool:
        return self.path.exists()


@dataclass
class TemplateMap:
    templates: list[TemplateInfo] = field(default_factory=list)

    def by_slug(self, slug: str) -> TemplateInfo | None:
        for t in self.templates:
            if t.slug == slug:
                return t
        return None

    def by_filename(self, filename: str) -> TemplateInfo | None:
        for t in self.templates:
            if t.filename == filename:
                return t
        return None

    def slugged(self) -> list[TemplateInfo]:
        return [t for t in self.templates if t.slug is not None]

    def unregistered(self) -> list[TemplateInfo]:
        return [t for t in self.templates if t.slug is None]


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

# Matches lines like:  'template-about.php'   => 'about',
_MAP_ENTRY_RE = re.compile(r"""['"](template-[^'"]+\.php)['"]\s*=>\s*['"]([^'"]+)['"]""")


def _parse_enqueue_map(enqueue_php: Path) -> dict[str, str]:
    """Return {filename: slug} from $template_map in enqueue.php."""
    if not enqueue_php.exists():
        return {}
    text = enqueue_php.read_text(encoding="utf-8")
    result: dict[str, str] = {}
    for m in _MAP_ENTRY_RE.finditer(text):
        filename, slug = m.group(1), m.group(2)
        result[filename] = slug
    return result


def load_templates(theme_root: Path | None = None) -> TemplateMap:
    """
    Discover all template-*.php files in the theme root and annotate
    each with its registered slug (from inc/enqueue.php $template_map).

    Files not found in the map get slug=None.
    """
    root = theme_root or _theme_root()
    enqueue_php = root / "inc" / "enqueue.php"
    filename_to_slug = _parse_enqueue_map(enqueue_php)

    template_files = sorted(root.glob("template-*.php"))
    if not template_files:
        # Fallback: check if root even exists
        if not root.exists():
            raise TemplateError(f"Theme root not found: {root}")

    infos: list[TemplateInfo] = []
    for path in template_files:
        filename = path.name
        slug = filename_to_slug.get(filename)
        infos.append(TemplateInfo(slug=slug, filename=filename, path=path))

    # Also surface slugs that appear in the map but have no matching file
    # (useful for diagnosing orphaned registrations)
    found_files = {t.filename for t in infos}
    for filename, slug in filename_to_slug.items():
        if filename not in found_files:
            infos.append(TemplateInfo(slug=slug, filename=filename, path=root / filename))

    return TemplateMap(templates=infos)
