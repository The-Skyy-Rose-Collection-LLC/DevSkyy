"""
Lightweight PHP source parser utilities for the SkyyRose theme.

No PHP interpreter required — pure regex against PHP source text.

Provides:
  - extract_template_map(): parse $template_map from inc/enqueue.php
  - extract_version_constant(): extract SKYYROSE_VERSION value
  - extract_php_string(): generic PHP single-quoted string extractor
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Matches: 'template-about.php' => 'about',
_TEMPLATE_MAP_ENTRY_RE = re.compile(r"""['"](template-[^'"]+\.php)['"]\s*=>\s*['"]([^'"]+)['"]""")

# Matches: define( 'SKYYROSE_VERSION', '1.5.20' );
_SKYYROSE_VERSION_RE = re.compile(
    r"""define\s*\(\s*['"]SKYYROSE_VERSION['"]\s*,\s*['"]([^'"]+)['"]\s*\)"""
)

# Matches: Version:   1.5.20  (CSS header)
_STYLE_CSS_VERSION_RE = re.compile(r"^Version:\s*(.+)$", re.MULTILINE)

# Matches: Stable tag: 1.5.20  (readme.txt)
_README_STABLE_TAG_RE = re.compile(r"^Stable tag:\s*(.+)$", re.MULTILINE)

# Matches: Theme Name: SkyyRose
_THEME_NAME_RE = re.compile(r"^Theme Name:\s*(.+)$", re.MULTILINE)

# Matches: Text Domain: skyyrose
_TEXT_DOMAIN_RE = re.compile(r"^Text Domain:\s*(.+)$", re.MULTILINE)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_template_map(php_text: str) -> dict[str, str]:
    """
    Parse all template_map entries from PHP source text.

    Returns:
        {filename: slug}  e.g. {"template-about.php": "about"}
    """
    result: dict[str, str] = {}
    for m in _TEMPLATE_MAP_ENTRY_RE.finditer(php_text):
        filename, slug = m.group(1), m.group(2)
        result[filename] = slug
    return result


def extract_template_map_from_file(path: Path) -> dict[str, str]:
    """Read *path* and return extract_template_map() result."""
    if not path.exists():
        return {}
    return extract_template_map(path.read_text(encoding="utf-8"))


def extract_version_constant(php_text: str) -> str | None:
    """
    Extract the SKYYROSE_VERSION constant value from PHP source text.

    Returns:
        Version string, e.g. "1.5.20", or None if not found.
    """
    m = _SKYYROSE_VERSION_RE.search(php_text)
    return m.group(1) if m else None


def extract_style_css_version(css_text: str) -> str | None:
    """Extract Version: header value from style.css text."""
    m = _STYLE_CSS_VERSION_RE.search(css_text)
    return m.group(1).strip() if m else None


def extract_readme_stable_tag(readme_text: str) -> str | None:
    """Extract Stable tag: value from readme.txt text."""
    m = _README_STABLE_TAG_RE.search(readme_text)
    return m.group(1).strip() if m else None


def extract_theme_name(css_text: str) -> str | None:
    """Extract Theme Name: value from style.css text."""
    m = _THEME_NAME_RE.search(css_text)
    return m.group(1).strip() if m else None


def extract_text_domain(css_text: str) -> str | None:
    """Extract Text Domain: value from style.css text."""
    m = _TEXT_DOMAIN_RE.search(css_text)
    return m.group(1).strip() if m else None


def extract_php_string(php_text: str, constant_name: str) -> str | None:
    """
    Generic extractor for a single-quoted PHP define() constant.

    Example:
        extract_php_string(text, "MY_CONST")
        # matches: define( 'MY_CONST', 'value' );
    """
    pattern = re.compile(
        rf"""define\s*\(\s*['"]{re.escape(constant_name)}['"]\s*,\s*['"]([^'"]+)['"]\s*\)"""
    )
    m = pattern.search(php_text)
    return m.group(1) if m else None
