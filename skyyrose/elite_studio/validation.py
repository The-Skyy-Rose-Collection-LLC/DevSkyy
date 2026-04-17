"""Shared validation utilities for registry files.

Used by:
  - skyyrose.elite_studio.catalog (product catalog)
  - skyyrose.elite_studio.prompts (prompt library)
  - future registries (scene library, pricing tables, etc.)

Two tiers of validation:

  1. **Structural** — field-level checks in `__post_init__`. Raises `ValueError`
     immediately. Use for: type coercion failures, malformed hex colors, empty
     required fields, invalid enum values. A structural failure means the file
     itself is broken and can't safely be parsed.

  2. **Referential** — cross-reference checks after all entries loaded. Returns
     a list of `Violation` objects. Use for: series referencing a missing SKU,
     duplicate aliases, dangling cross-registry links. These can accumulate and
     be surfaced as a single audit report.

The registry decides whether referential violations are fatal (strict=True)
or advisory (load succeeds with a `.violations` property).
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

# ─── Violation types ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Violation:
    """A single integrity violation found during registry load."""

    severity: str  # 'structural' | 'referential'
    code: str  # stable identifier (e.g. 'duplicate_alias')
    path: str  # dotted path (e.g. 'products[5].aliases[0]')
    message: str

    def format(self) -> str:
        return f"[{self.severity}:{self.code}] {self.path}: {self.message}"


class IntegrityError(Exception):
    """Raised when a registry fails strict integrity validation."""

    def __init__(self, violations: list[Violation]):
        self.violations = list(violations)
        lines = [f"{len(violations)} integrity violation(s):"]
        lines.extend(f"  {v.format()}" for v in violations)
        super().__init__("\n".join(lines))


# ─── Structural validators (raise ValueError on bad input) ────────────────────


_HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_SKU_RE = re.compile(r"^[a-z]+-(?:d?\d{2,3})$")
_ISO_DATE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)?$"
)


def validate_hex_color(value: Any, field_path: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_path}: expected hex color string, got {type(value).__name__}")
    if not _HEX_COLOR_RE.match(value):
        raise ValueError(f"{field_path}: invalid hex color {value!r} (expected #RRGGBB)")
    return value


def validate_enum(value: Any, allowed: set[str], field_path: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_path}: expected str, got {type(value).__name__}")
    if value not in allowed:
        raise ValueError(f"{field_path}: {value!r} not in allowed values {sorted(allowed)}")
    return value


def validate_sku_format(value: Any, field_path: str) -> str:
    """SkyyRose SKU format: <collection>-<nnn> or <collection>-d<nn>."""
    if not isinstance(value, str):
        raise ValueError(f"{field_path}: expected str, got {type(value).__name__}")
    if not _SKU_RE.match(value):
        raise ValueError(
            f"{field_path}: invalid SKU format {value!r} "
            "(expected like 'br-001', 'kids-002', 'br-d01')"
        )
    return value


def validate_not_empty(value: Any, field_path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_path}: must be a non-empty string")
    return value


def validate_non_negative(value: Any, field_path: str) -> float:
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field_path}: expected number, got {type(value).__name__}")
    if value < 0:
        raise ValueError(f"{field_path}: must be >= 0, got {value}")
    return float(value)


def validate_iso_date(value: Any, field_path: str, *, allow_null: bool = True) -> str | None:
    if value is None:
        if allow_null:
            return None
        raise ValueError(f"{field_path}: expected ISO date, got None")
    if not isinstance(value, str):
        raise ValueError(f"{field_path}: expected ISO date string, got {type(value).__name__}")
    if not _ISO_DATE_RE.match(value):
        raise ValueError(
            f"{field_path}: invalid ISO date {value!r} (expected YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)"
        )
    return value


# ─── Helpers for referential checks ──────────────────────────────────────────


def collect_duplicates(items: Iterable[str]) -> list[str]:
    """Return the subset of items that appear more than once."""
    seen: set[str] = set()
    dupes: set[str] = set()
    for i in items:
        if i in seen:
            dupes.add(i)
        seen.add(i)
    return sorted(dupes)
