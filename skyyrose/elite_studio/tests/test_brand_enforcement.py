"""Brand enforcement — retired taglines must never appear in generated content.

This test reads retired taglines from `assets/brand/brand.yaml` and asserts
they do not appear in any tracked source file EXCEPT:
  - brand.yaml itself (the source of the list)
  - this test file
  - the brand loader (it reads the list to expose it)

Run: pytest skyyrose/elite_studio/tests/test_brand_enforcement.py -v

If this test fails, a retired phrase has crept back into generated content.
Remove it or migrate the caller to read `BrandConfig.tagline_active` instead.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from skyyrose.elite_studio.brand import BrandConfig

pytest.importorskip("yaml")


_REPO_ROOT = Path(__file__).resolve().parents[3]

# Files that ARE allowed to reference retired taglines (they catalog them or
# enforce them). Any other tracked file is a violation.
_ALLOWED_PATHS = frozenset(
    {
        "assets/brand/brand.yaml",
        "skyyrose/elite_studio/tests/test_brand_enforcement.py",
        "skyyrose/elite_studio/tests/test_brand.py",
        "skyyrose/elite_studio/brand.py",
    }
)

# Directories to scan. Focused on customer-facing surfaces.
_SCAN_DIRS = ("wordpress", "wordpress-theme", "frontend", "skyyrose", "scripts")

# File extensions to scan.
_SCAN_EXTS = frozenset({".py", ".php", ".ts", ".tsx", ".js", ".jsx", ".yaml", ".yml", ".md"})


def _git_tracked_files() -> list[Path]:
    """Return all git-tracked files under _SCAN_DIRS with _SCAN_EXTS extensions."""
    try:
        result = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "ls-files", *_SCAN_DIRS],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        pytest.skip("git not available")
    if result.returncode != 0:
        pytest.skip(f"git ls-files failed: {result.stderr[:200]}")
    paths: list[Path] = []
    for line in result.stdout.splitlines():
        rel = line.strip()
        if not rel:
            continue
        if Path(rel).suffix.lower() not in _SCAN_EXTS:
            continue
        paths.append(_REPO_ROOT / rel)
    return paths


# Words/phrases on the same line that mark an enforcement mention (allowed).
# If ANY of these co-occur with a retired phrase on the same line, it's
# documentation/assertion/rejection — not an actual usage.
_ENFORCEMENT_KEYWORDS = (
    "retired",
    "RETIRED",
    "never use",
    "Never use",
    "NEVER use",
    "NEVER",
    "is dead",
    "not the tagline",
    "do not use",
    "forbidden",
    "not in",
    "assert ",
    "retired_tagline",
    "DEPRECATED",
)


def _is_enforcement_line(line: str) -> bool:
    """True if the line is declaring/rejecting the retired phrase, not using it."""
    return any(kw in line for kw in _ENFORCEMENT_KEYWORDS)


def test_retired_taglines_do_not_appear_as_actual_usage() -> None:
    brand = BrandConfig.load()
    retired = list(brand.retired_taglines)
    if not retired:
        pytest.skip("No retired taglines declared in brand.yaml")

    violations: list[tuple[str, str, int, str]] = []  # (rel_path, phrase, line_no, line)

    for path in _git_tracked_files():
        try:
            rel_path = str(path.relative_to(_REPO_ROOT))
        except ValueError:
            continue
        if rel_path in _ALLOWED_PATHS:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for phrase in retired:
            if phrase not in content:
                continue
            for line_no, line in enumerate(content.splitlines(), start=1):
                if phrase not in line:
                    continue
                if _is_enforcement_line(line):
                    continue  # enforcement mention — allowed
                violations.append((rel_path, phrase, line_no, line.strip()[:120]))

    if violations:
        msg = "Retired tagline(s) used as actual content (must be migrated):\n"
        for rel_path, phrase, line_no, snippet in violations[:30]:
            msg += f"  {rel_path}:{line_no}  — {phrase!r}\n    {snippet}\n"
        if len(violations) > 30:
            msg += f"  ... {len(violations) - 30} more\n"
        msg += (
            "\nReplace with BrandConfig.load().tagline_active, or if this is an "
            "enforcement mention (instruction to NOT use the phrase), include one "
            "of the enforcement keywords (retired, NEVER, do not use, etc.) on "
            "the same line."
        )
        pytest.fail(msg)
