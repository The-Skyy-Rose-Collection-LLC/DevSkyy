"""
WCAG AA contrast regression gate — Phase 11 / CNTR-01..04.

Parses design-tokens.css to extract --skyyrose-text, --skyyrose-text-muted,
and --skyyrose-bg for :root and each [data-collection="..."] scope, then asserts
all combinations meet WCAG AA (4.5:1 normal text).

No external deps beyond stdlib + pytest.
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# WCAG helpers (inline, no external deps)
# ---------------------------------------------------------------------------

TOKENS_CSS_PATH = (
    Path(__file__).parent.parent / "wordpress-theme/skyyrose-flagship/assets/css/design-tokens.css"
)


def srgb_linearize(channel_8bit: int) -> float:
    """Convert 8-bit sRGB channel value to linear light (WCAG 2.x formula)."""
    c = channel_8bit / 255.0
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    """Return WCAG relative luminance for a #RRGGBB hex colour string."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        raise ValueError(f"Expected #RRGGBB, got: #{hex_color}")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * srgb_linearize(r) + 0.7152 * srgb_linearize(g) + 0.0722 * srgb_linearize(b)


def wcag_ratio(hex_a: str, hex_b: str) -> float:
    """Return WCAG contrast ratio between two #RRGGBB colours (order-independent)."""
    la = relative_luminance(hex_a)
    lb = relative_luminance(hex_b)
    lighter, darker = (la, lb) if la >= lb else (lb, la)
    return (lighter + 0.05) / (darker + 0.05)


def alpha_blend(r: int, g: int, b: int, alpha: float, bg_hex: str) -> str:
    """
    Flatten an rgba(r, g, b, alpha) foreground onto a solid #RRGGBB background.

    Returns a #RRGGBB string suitable for wcag_ratio().
    """
    bg_hex = bg_hex.lstrip("#")
    bg_r, bg_g, bg_b = (int(bg_hex[i : i + 2], 16) for i in (0, 2, 4))
    out_r = round(alpha * r + (1 - alpha) * bg_r)
    out_g = round(alpha * g + (1 - alpha) * bg_g)
    out_b = round(alpha * b + (1 - alpha) * bg_b)
    return f"#{out_r:02X}{out_g:02X}{out_b:02X}"


# ---------------------------------------------------------------------------
# CSS token parser
# ---------------------------------------------------------------------------

_HEX_RE = re.compile(r"--skyyrose-(text|text-muted|bg)\s*:\s*(#[0-9A-Fa-f]{3,8}|rgba\([^)]+\))")


def _extract_tokens(block: str) -> dict[str, str]:
    """Pull --skyyrose-text / text-muted / bg values out of a CSS block string."""
    tokens: dict[str, str] = {}
    for m in _HEX_RE.finditer(block):
        tokens[m.group(1)] = m.group(2).strip()
    return tokens


def _extract_root_blocks(css: str) -> list[str]:
    """
    Return content of all :root { ... } blocks using balanced-brace parsing.

    Needed because design-tokens.css has multiple :root declarations and the
    simple `[^}]+` regex stops at the first `}` inside a comment or layout block.
    """
    blocks: list[str] = []
    for m in re.finditer(r":root\s*\{", css):
        start = m.end()
        depth = 1
        i = start
        while i < len(css) and depth > 0:
            if css[i] == "{":
                depth += 1
            elif css[i] == "}":
                depth -= 1
            i += 1
        blocks.append(css[start : i - 1])
    return blocks


def parse_root_tokens() -> dict[str, str]:
    """
    Return tokens defined across all :root { ... } blocks.

    design-tokens.css uses multiple :root declarations; we merge them so that
    the semantic-colour block (containing --skyyrose-text / bg) is found
    regardless of declaration order.
    """
    css = TOKENS_CSS_PATH.read_text(encoding="utf-8")
    merged: dict[str, str] = {}
    for block in _extract_root_blocks(css):
        merged.update(_extract_tokens(block))
    return merged


def parse_collection_tokens() -> dict[str, dict[str, str]]:
    """Return per-collection token overrides keyed by collection slug."""
    css = TOKENS_CSS_PATH.read_text(encoding="utf-8")
    result: dict[str, dict[str, str]] = {}
    for m in re.finditer(r'\[data-collection="([^"]+)"\]\s*\{([^}]+)\}', css, re.DOTALL):
        slug, block = m.group(1), m.group(2)
        overrides = _extract_tokens(block)
        if overrides:
            result[slug] = overrides
    return result


def effective_tokens(slug: str | None = None) -> dict[str, str]:
    """
    Merge :root tokens with per-collection overrides.

    slug=None → :root only (default palette).
    """
    root = parse_root_tokens()
    if slug is None:
        return root
    overrides = parse_collection_tokens().get(slug, {})
    return {**root, **overrides}


def resolve_text_colour(tokens: dict[str, str], key: str = "text") -> str:
    """
    Resolve a token value to a flat #RRGGBB hex string.

    Handles rgba() by blending onto the scope's --skyyrose-bg.
    """
    raw = tokens.get(key, "")
    bg = tokens.get("bg", "#0A0A0A")

    # Plain hex
    if raw.startswith("#"):
        return raw

    # rgba(r, g, b, alpha)
    m = re.match(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)", raw)
    if m:
        r, g, b, a = int(m.group(1)), int(m.group(2)), int(m.group(3)), float(m.group(4))
        return alpha_blend(r, g, b, a, bg)

    raise ValueError(f"Unrecognised token format for {key!r}: {raw!r}")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_tokens_css_exists() -> None:
    """design-tokens.css must exist at the expected path."""
    assert TOKENS_CSS_PATH.exists(), (
        f"design-tokens.css not found at {TOKENS_CSS_PATH}. "
        "Run from the repo root or check the path constant."
    )


def test_wcag_helper_known_pair() -> None:
    """Black on white must be exactly 21:1 (canonical WCAG reference pair)."""
    ratio = wcag_ratio("#FFFFFF", "#000000")
    assert abs(ratio - 21.0) < 0.01, f"Expected ~21.0, got {ratio:.4f}"


def test_wcag_ratio_order_independent() -> None:
    """wcag_ratio(a, b) == wcag_ratio(b, a) for any pair."""
    a, b = "#F5E6D3", "#0A0A0A"
    assert wcag_ratio(a, b) == wcag_ratio(b, a)


def test_text_muted_blend() -> None:
    """
    rgba(245,230,211,0.7) blended on #0A0A0A must still meet WCAG AA (>=4.5:1).

    The blended colour is ≈#AFA497. Verified against the known luminance formula.
    """
    blended = alpha_blend(245, 230, 211, 0.7, "#0A0A0A")
    ratio = wcag_ratio(blended, "#0A0A0A")
    assert (
        ratio >= 4.5
    ), f"text-muted blended ({blended}) on bg fails WCAG AA: {ratio:.2f}:1 < 4.5:1"


def test_root_text_bg_meets_wcag_aa() -> None:
    """
    Default (root) --skyyrose-text on --skyyrose-bg must meet WCAG AA and
    be well above the noise floor (>= 15.0:1) to catch accidental regressions.
    """
    tokens = effective_tokens()
    text_hex = resolve_text_colour(tokens, "text")
    bg_hex = tokens["bg"]
    ratio = wcag_ratio(text_hex, bg_hex)
    assert ratio >= 4.5, f"Root text/bg fails WCAG AA: {ratio:.2f}:1 (text={text_hex}, bg={bg_hex})"
    assert ratio >= 15.0, (
        f"Root text/bg ratio unexpectedly low ({ratio:.2f}:1) — "
        f"possible regression in design-tokens.css. "
        f"text={text_hex}, bg={bg_hex}"
    )


def test_all_collections_inherit_root_text_bg() -> None:
    """
    Every [data-collection] scope must meet WCAG AA for both --skyyrose-text
    (solid) and --skyyrose-text-muted (rgba-blended). Collections that don't
    override these tokens inherit :root values and must pass.
    """
    known_collections = ["black-rose", "love-hurts", "signature", "kids-capsule"]
    failures: list[str] = []

    for slug in known_collections:
        tokens = effective_tokens(slug)
        bg_hex = tokens.get("bg", "#0A0A0A")

        # Solid text
        try:
            text_hex = resolve_text_colour(tokens, "text")
            ratio = wcag_ratio(text_hex, bg_hex)
            if ratio < 4.5:
                failures.append(f"[{slug}] text ({text_hex}) on bg ({bg_hex}): {ratio:.2f}:1 < 4.5")
        except (ValueError, KeyError) as exc:
            failures.append(f"[{slug}] text token error: {exc}")

        # Muted text (rgba blend)
        if "text-muted" in tokens:
            try:
                muted_hex = resolve_text_colour(tokens, "text-muted")
                ratio = wcag_ratio(muted_hex, bg_hex)
                if ratio < 4.5:
                    failures.append(
                        f"[{slug}] text-muted ({muted_hex}) on bg ({bg_hex}): {ratio:.2f}:1 < 4.5"
                    )
            except (ValueError, KeyError) as exc:
                failures.append(f"[{slug}] text-muted token error: {exc}")

    assert not failures, "WCAG AA failures:\n" + "\n".join(failures)
