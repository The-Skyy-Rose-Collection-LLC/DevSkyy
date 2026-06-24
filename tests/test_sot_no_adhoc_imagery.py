"""Drift guard: product imagery must resolve through the SOT, never ad-hoc.

The canonical authority is ``skyyrose.core.sot_images`` (Python) / ``data/sot-images.json``
(the generated manifest non-Python surfaces read). This test is the *law* that keeps
"SOT is the only product-imagery reference" true over time: it fails CI on a NEW
hardcoded product image, so the rule can't silently erode.

Scope is deliberately tight (advisor-reviewed) so the guard stays trustworthy:
  1. The fabricated ``/images/scenes/<collection>-product-N.jpg`` pattern is banned
     everywhere — it has zero legitimate uses (pure placeholder fabrication, the
     original dashboard bug).
  2. Hardcoded product-image path literals in the dashboard's DISPLAY layer
     (``frontend/lib`` · ``frontend/components`` · ``frontend/app``) are banned —
     that code must read the catalog / SOT helper, not string-literal a render path.

Python pipeline / MCP write-side code legitimately CONSTRUCTS product-image paths as
generation INPUT/OUTPUT; that surface is governed by the policy doc + audit backlog
(docs/brand/sot-imagery-policy.md), not by this grep, so the guard doesn't drown in
false positives.

ALLOWLIST is a ratchet: it may only SHRINK. Removing the last entry = the dashboard
display layer is fully SOT-sourced.
"""

from __future__ import annotations

import functools
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Fabricated scene-placeholder images — banned outright, anywhere.
SCENE_FAKE = re.compile(r"/images/scenes/[\w-]*product[\w-]*\.(?:jpg|jpeg|png|webp)")

# Hardcoded product-image path literals (the render tree) in display code.
PRODUCT_PATH_LITERAL = re.compile(
    r"""['"`]/?(?:assets/)?images/products/[\w./-]+\.(?:webp|jpe?g|png|avif)['"`]"""
)

# Display-layer roots whose product imagery MUST come from the catalog/SOT helper.
DISPLAY_DIRS = ("frontend/lib", "frontend/components", "frontend/app")

# Ratchet allowlist — files with known, tracked violations. MAY ONLY SHRINK.
# Each entry is a backlog item in docs/brand/sot-imagery-policy.md.
ALLOWLIST = {
    "frontend/lib/collections.ts",  # drifted product list + fake scene images; see policy backlog
}


@functools.lru_cache(maxsize=1)
def _tracked_files() -> tuple[str, ...]:
    out = subprocess.run(
        ["git", "ls-files", "*.ts", "*.tsx", "*.js", "*.jsx"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return tuple(f for f in out.splitlines() if f)


def test_no_fabricated_scene_product_images():
    """No /images/scenes/*-product-*.jpg fabrications anywhere in tracked source."""
    offenders = []
    for rel in _tracked_files():
        if rel in ALLOWLIST:
            continue
        text = (REPO / rel).read_text(encoding="utf-8", errors="ignore")
        if SCENE_FAKE.search(text):
            offenders.append(rel)
    assert not offenders, (
        "Fabricated scene-placeholder product images found (resolve via SOT instead):\n"
        + "\n".join(f"  {o}" for o in offenders)
    )


def test_no_hardcoded_product_image_in_display_layer():
    """Dashboard display code must source product images from the catalog/SOT helper."""
    offenders = []
    for rel in _tracked_files():
        if rel in ALLOWLIST:
            continue
        if not rel.startswith(DISPLAY_DIRS):
            continue
        text = (REPO / rel).read_text(encoding="utf-8", errors="ignore")
        for m in PRODUCT_PATH_LITERAL.finditer(text):
            offenders.append(f"{rel}: {m.group(0)}")
    assert not offenders, (
        "Hardcoded product-image literal in dashboard display layer "
        "(read from @/lib/catalog or the SOT manifest instead):\n"
        + "\n".join(f"  {o}" for o in offenders)
    )


def test_allowlist_only_shrinks_no_phantoms():
    """Every allowlisted file must exist and actually still violate — no stale grandfathering."""
    for rel in ALLOWLIST:
        p = REPO / rel
        assert p.is_file(), f"Allowlisted file no longer exists; remove from ALLOWLIST: {rel}"
        text = p.read_text(encoding="utf-8", errors="ignore")
        assert SCENE_FAKE.search(text) or PRODUCT_PATH_LITERAL.search(
            text
        ), f"{rel} no longer violates — remove it from ALLOWLIST (the ratchet only shrinks)."
