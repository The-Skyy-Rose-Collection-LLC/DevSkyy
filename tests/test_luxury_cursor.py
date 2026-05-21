"""
Phase 13 — Luxury Cursor Verification
CURS-01: cursor z-index > 9999 (above all modals/overlays)
CURS-03: cursor JS must NOT load on immersive templates (slug gate required)

test_cursor_not_loaded_on_immersive is expected to FAIL against the current
enqueue.php implementation — this failure IS the CURS-03 gap report.
The luxury cursor JS is enqueued unconditionally in skyyrose_enqueue_global_scripts()
with no immersive-slug exclusion (see inc/enqueue.php lines 249-259).
Fix target: move enqueue to skyyrose_enqueue_template_scripts() with
    if ($slug !== 'immersive') guard.
"""

import re
from pathlib import Path

MODULE_DIR = Path(__file__).parent.parent / "wordpress-theme/skyyrose-flagship"
CSS_FILE = MODULE_DIR / "assets/css/luxury-cursor.css"
ENQUEUE_FILE = MODULE_DIR / "inc/enqueue.php"


def extract_function_body(php_text: str, fn_name: str) -> str:
    """Extract the body of a PHP function by brace-depth counting.

    Returns the content between the opening and closing braces of fn_name.
    Raises ValueError if function not found or braces unbalanced.
    """
    # Find the function declaration
    pattern = re.compile(
        r"function\s+" + re.escape(fn_name) + r"\s*\([^)]*\)\s*\{",
        re.DOTALL,
    )
    match = pattern.search(php_text)
    if not match:
        raise ValueError(f"Function '{fn_name}' not found in PHP source")

    start = match.end()  # position just after the opening brace
    depth = 1
    pos = start
    while pos < len(php_text) and depth > 0:
        ch = php_text[pos]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        pos += 1

    if depth != 0:
        raise ValueError(f"Unbalanced braces in function '{fn_name}'")

    return php_text[start : pos - 1]


# ---------------------------------------------------------------------------
# CURS-01: z-index verification
# ---------------------------------------------------------------------------


def test_cursor_zindex_above_modals() -> None:
    """CURS-01: .cursor-dot and .cursor-ring must have z-index > 9999."""
    css = CSS_FILE.read_text(encoding="utf-8")

    # Extract z-index values from CSS rules containing cursor-dot or cursor-ring
    # Pattern: rule block that includes either selector
    block_pattern = re.compile(
        r"([^{}]*(?:\.cursor-dot|\.cursor-ring)[^{}]*)\{([^}]+)\}",
        re.DOTALL,
    )
    found_zindex_values: list[int] = []

    for block_match in block_pattern.finditer(css):
        rule_body = block_match.group(2)
        for zidx_match in re.finditer(r"z-index\s*:\s*(\d+)", rule_body):
            found_zindex_values.append(int(zidx_match.group(1)))

    assert found_zindex_values, (
        f"No z-index declarations found for .cursor-dot or .cursor-ring in {CSS_FILE}"
    )

    for val in found_zindex_values:
        assert val > 9999, (
            f"CURS-01 FAIL: z-index {val} is not above 9999 (modals/overlays threshold). "
            f"luxury-cursor.css must use z-index > 9999 for cursor elements."
        )


# ---------------------------------------------------------------------------
# Sanity: CSS is enqueued globally (prerequisite for CURS-01 at runtime)
# ---------------------------------------------------------------------------


def test_cursor_css_enqueued_globally() -> None:
    """luxury-cursor CSS must be registered inside skyyrose_enqueue_global_styles."""
    php = ENQUEUE_FILE.read_text(encoding="utf-8")
    body = extract_function_body(php, "skyyrose_enqueue_global_styles")
    assert "luxury-cursor" in body, (
        "luxury-cursor CSS is not enqueued in skyyrose_enqueue_global_styles(). "
        "Global CSS enqueue is required for CURS-01 to function on all pages."
    )


# ---------------------------------------------------------------------------
# CURS-03: immersive exclusion gate (EXPECTED TO FAIL — gap report)
# ---------------------------------------------------------------------------


def test_cursor_not_loaded_on_immersive() -> None:
    """CURS-03: luxury cursor JS must NOT load on immersive templates.

    This test INTENTIONALLY FAILS against the current implementation.
    The cursor JS is enqueued unconditionally in skyyrose_enqueue_global_scripts()
    with no slug=immersive exclusion guard.

    Failure = CURS-03 GAP confirmed. Do not xfail — let CI surface this.
    Fix: move wp_enqueue_script('skyyrose-luxury-cursor', ...) into
         skyyrose_enqueue_template_scripts() behind:
             if ($slug !== 'immersive') { ... }
    """
    php = ENQUEUE_FILE.read_text(encoding="utf-8")
    global_body = extract_function_body(php, "skyyrose_enqueue_global_scripts")

    cursor_in_global = "luxury-cursor" in global_body

    if not cursor_in_global:
        # Cursor JS was moved out of global enqueue — verify it has an immersive guard
        # in the template-specific enqueue function instead.
        template_body = extract_function_body(php, "skyyrose_enqueue_template_scripts")
        if "luxury-cursor" not in template_body:
            import pytest

            pytest.fail(
                "CURS-03 GAP: luxury cursor JS is neither in global_scripts nor in "
                "template_scripts. Cannot verify immersive exclusion."
            )
        # Check for immersive guard
        has_guard = bool(
            re.search(r"immersive", template_body) and re.search(r"luxury-cursor", template_body)
        )
        assert has_guard, (
            "CURS-03 FAIL: luxury cursor JS is in skyyrose_enqueue_template_scripts() "
            "but no immersive exclusion guard found. "
            "Add: if (\\$slug !== 'immersive') { wp_enqueue_script('skyyrose-luxury-cursor', ...); }"
        )
        # CURS-03 PASSES: cursor JS in template_scripts with immersive guard
        return

    # Cursor is in global_scripts — check if there is any immersive-slug guard
    # around the luxury-cursor enqueue call.
    # Extract the luxury-cursor block specifically
    cursor_block_match = re.search(
        r"((?:if\s*\([^)]*\)\s*\{[^}]*\}|)\s*"
        r"\$cursor_file\s*=.*?wp_enqueue_script\s*\(\s*['\"]skyyrose-luxury-cursor['\"].*?\)\s*;(?:\s*\})?)",
        global_body,
        re.DOTALL,
    )
    # Simpler: look for 'immersive' within ~500 chars before/after cursor enqueue
    cursor_pos = global_body.find("luxury-cursor")
    window_start = max(0, cursor_pos - 500)
    window_end = min(len(global_body), cursor_pos + 500)
    context_window = global_body[window_start:window_end]

    has_immersive_guard = bool(re.search(r"immersive", context_window))

    assert has_immersive_guard, (
        "CURS-03 GAP: luxury cursor JS is loaded unconditionally in "
        "skyyrose_enqueue_global_scripts() with no immersive-slug exclusion. "
        "On immersive templates (template-immersive-*.php, slug='immersive'), "
        "the cursor JS conflicts with the Three.js/WebGL scene. "
        "Fix: move wp_enqueue_script('skyyrose-luxury-cursor', ...) into "
        "skyyrose_enqueue_template_scripts() behind: "
        "if (\\$slug !== 'immersive') { ... }"
    )
