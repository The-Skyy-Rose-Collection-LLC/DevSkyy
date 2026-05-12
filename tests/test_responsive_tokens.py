"""
Regression gate: Phase 12 Responsive Typography (RESP-01, RESP-02, RESP-04)

Asserts that the already-shipped design-tokens.css clamp() values are well-formed,
monotonically scaled, and that the committed homepage fixture has no inline fixed
pixel widths > 320px without overflow handling.

Parser note: uses pure stdlib re — no BeautifulSoup, no cssutils.
The design-tokens.css file contains 4 separate :root {} blocks, but --text-* token
names are globally unique across all blocks, so line-level regex scanning is safe
(no brace-depth scoping required for name uniqueness).
"""

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

TOKENS_CSS_PATH = (
    Path(__file__).parent.parent / "wordpress-theme/skyyrose-flagship/assets/css/design-tokens.css"
)
FIXTURE_PATH = Path(__file__).parent / "fixtures/homepage_skyyrose.html"

# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

_CLAMP_RE = re.compile(
    r"(--text-[a-z0-9-]+)\s*:\s*clamp\(([^)]+)\)",
)
_STATIC_RE = re.compile(
    r"(--text-[a-z0-9-]+)\s*:\s*([\d.]+)rem\s*;",
)


def rem_to_float(rem_str: str) -> float:
    """Strip 'rem' suffix and return float value."""
    return float(rem_str.strip().replace("rem", "").strip())


def parse_clamp_tokens() -> dict[str, tuple[str, str, str]]:
    """
    Parse all --text-* tokens that use clamp() from design-tokens.css.

    Returns a mapping of token_name -> (min_arg, preferred_arg, max_arg).
    Each arg is a raw string as it appears inside clamp(...).
    """
    css = TOKENS_CSS_PATH.read_text(encoding="utf-8")
    result: dict[str, tuple[str, str, str]] = {}
    for match in _CLAMP_RE.finditer(css):
        name = match.group(1)
        args = [a.strip() for a in match.group(2).split(",")]
        if len(args) == 3:
            result[name] = (args[0], args[1], args[2])
    return result


def parse_static_tokens() -> dict[str, float]:
    """
    Parse all --text-* tokens that are plain rem values (no clamp).

    Returns a mapping of token_name -> rem_value as float.
    """
    css = TOKENS_CSS_PATH.read_text(encoding="utf-8")
    result: dict[str, float] = {}
    for line in css.splitlines():
        # Skip lines that contain clamp — handled by parse_clamp_tokens
        if "clamp(" in line:
            continue
        m = _STATIC_RE.search(line)
        if m:
            result[m.group(1)] = float(m.group(2))
    return result


# ---------------------------------------------------------------------------
# Tests — file guards
# ---------------------------------------------------------------------------


def test_tokens_css_exists():
    """design-tokens.css must exist at the expected path."""
    assert TOKENS_CSS_PATH.exists(), f"design-tokens.css not found at {TOKENS_CSS_PATH}"


# ---------------------------------------------------------------------------
# Tests — clamp() token structure (RESP-01)
# ---------------------------------------------------------------------------

_EXPECTED_CLAMP_NAMES = {
    "--text-3xl",
    "--text-4xl",
    "--text-5xl",
    "--text-decorative-sm",
    "--text-decorative-md",
    "--text-decorative-lg",
    "--text-decorative-xl",
}


def test_clamp_token_count():
    """At least 7 clamp tokens must be present, including all expected names."""
    tokens = parse_clamp_tokens()
    assert len(tokens) >= 7, f"Expected >= 7 clamp tokens, found {len(tokens)}: {sorted(tokens)}"
    missing = _EXPECTED_CLAMP_NAMES - set(tokens)
    assert not missing, f"Missing expected clamp tokens: {missing}"


def test_clamp_tokens_three_args():
    """Every clamp() token must have exactly three non-empty arguments."""
    tokens = parse_clamp_tokens()
    assert tokens, "No clamp tokens found — parse_clamp_tokens() returned empty"
    bad = {name: args for name, args in tokens.items() if any(a == "" for a in args)}
    assert not bad, f"Clamp tokens with empty argument(s): {bad}"


def test_clamp_min_floor():
    """
    Every clamp() min arg must be >= 0.75rem.

    Guards against accidentally setting a floor that would make text unreadable.
    """
    tokens = parse_clamp_tokens()
    violations: list[str] = []
    for name, (min_arg, _, _) in tokens.items():
        if "rem" not in min_arg:
            continue  # skip non-rem units (vw, px) — not expected but not a failure
        try:
            val = rem_to_float(min_arg)
        except ValueError:
            violations.append(f"{name}: unparseable min '{min_arg}'")
            continue
        if val < 0.75:
            violations.append(f"{name}: min={val}rem < 0.75rem floor")
    assert not violations, "Clamp min floor violations:\n" + "\n".join(violations)


def test_clamp_preferred_uses_vw():
    """
    Every clamp() preferred arg must use 'vw' units.

    Confirms fluid scaling is actually active (not a fixed fallback).
    """
    tokens = parse_clamp_tokens()
    bad = {name: args[1] for name, args in tokens.items() if "vw" not in args[1]}
    assert not bad, f"Clamp preferred args missing 'vw': {bad}"


def test_clamp_max_gte_min():
    """
    Every clamp() max value must be >= its min value.

    Both min and max must be rem-based for comparison (decorative tokens expected to be).
    """
    tokens = parse_clamp_tokens()
    violations: list[str] = []
    for name, (min_arg, _, max_arg) in tokens.items():
        if "rem" not in min_arg or "rem" not in max_arg:
            continue  # skip non-rem-comparable pairs
        try:
            min_val = rem_to_float(min_arg)
            max_val = rem_to_float(max_arg)
        except ValueError:
            continue
        if max_val < min_val:
            violations.append(f"{name}: max={max_val}rem < min={min_val}rem")
    assert not violations, "Clamp max < min violations:\n" + "\n".join(violations)


# ---------------------------------------------------------------------------
# Tests — static token scale (RESP-01)
# ---------------------------------------------------------------------------

_STATIC_SCALE_ORDER = [
    "--text-xs",
    "--text-sm",
    "--text-base",
    "--text-lg",
    "--text-xl",
    "--text-2xl",
]


def test_static_token_count():
    """All six base static scale tokens must be present."""
    tokens = parse_static_tokens()
    missing = [t for t in _STATIC_SCALE_ORDER if t not in tokens]
    assert not missing, f"Missing static tokens: {missing}"


def test_static_tokens_monotonic():
    """
    Static tokens must form a strictly ascending scale:
    xs < sm < base < lg < xl < 2xl
    """
    tokens = parse_static_tokens()
    values = [tokens[t] for t in _STATIC_SCALE_ORDER if t in tokens]
    assert len(values) == len(
        _STATIC_SCALE_ORDER
    ), "Cannot verify monotonic scale — some tokens missing"
    for i in range(len(values) - 1):
        assert values[i] < values[i + 1], (
            f"Scale violation: {_STATIC_SCALE_ORDER[i]}={values[i]}rem "
            f">= {_STATIC_SCALE_ORDER[i + 1]}={values[i + 1]}rem"
        )


# ---------------------------------------------------------------------------
# Tests — 320px inline-width overflow (RESP-02)
# ---------------------------------------------------------------------------

_INLINE_WIDTH_RE = re.compile(r"width\s*:\s*(\d+)px", re.IGNORECASE)
_OVERFLOW_RE = re.compile(r"overflow\s*:\s*(auto|hidden|scroll)", re.IGNORECASE)
_STYLE_ATTR_RE = re.compile(r'style\s*=\s*["\']([^"\']*)["\']', re.IGNORECASE)


def test_320px_no_overflow_violations():
    """
    Scan committed homepage fixture for inline style= attributes that set
    width > 320px without an overflow:auto/hidden/scroll declaration.

    A fixed pixel width wider than 320px on an inline-styled element can
    cause horizontal scroll / layout break on narrow mobile viewports.
    """
    if not FIXTURE_PATH.exists():
        pytest.skip(f"Homepage fixture not found at {FIXTURE_PATH}")

    html = FIXTURE_PATH.read_text(encoding="utf-8", errors="replace")
    violations: list[str] = []

    for m in _STYLE_ATTR_RE.finditer(html):
        style_value = m.group(1)
        width_match = _INLINE_WIDTH_RE.search(style_value)
        if not width_match:
            continue
        width_px = int(width_match.group(1))
        if width_px <= 320:
            continue
        # Width > 320px — check if overflow is handled inline
        if _OVERFLOW_RE.search(style_value):
            continue
        # Capture context (up to 120 chars around the match for diagnostics)
        start = max(0, m.start() - 40)
        end = min(len(html), m.end() + 40)
        snippet = html[start:end].replace("\n", " ")
        violations.append(f"width:{width_px}px without overflow — context: ...{snippet}...")

    assert not violations, (
        f"Found {len(violations)} inline-width > 320px violation(s) without overflow:\n"
        + "\n".join(violations[:10])  # cap output at 10
    )


# ---------------------------------------------------------------------------
# Tests — typography hierarchy (RESP-04, deviation Rule 2)
# ---------------------------------------------------------------------------


def test_clamp_tokens_monotonic():
    """
    RESP-04: heading-scale tokens must form an ascending minimum hierarchy.

    Asserts: min(--text-3xl) <= min(--text-4xl) <= min(--text-5xl)

    This regression gate ensures the heading size ordering established in v1.1
    (commits 61e42abe0 + e5e80d6d4) is not accidentally broken.
    """
    tokens = parse_clamp_tokens()
    for name in ("--text-3xl", "--text-4xl", "--text-5xl"):
        assert name in tokens, f"Required hierarchy token missing: {name}"

    def clamp_min(token_name: str) -> float:
        return rem_to_float(tokens[token_name][0])

    min_3xl = clamp_min("--text-3xl")
    min_4xl = clamp_min("--text-4xl")
    min_5xl = clamp_min("--text-5xl")

    assert (
        min_3xl <= min_4xl
    ), f"Hierarchy violation: --text-3xl min ({min_3xl}rem) > --text-4xl min ({min_4xl}rem)"
    assert (
        min_4xl <= min_5xl
    ), f"Hierarchy violation: --text-4xl min ({min_4xl}rem) > --text-5xl min ({min_5xl}rem)"
