"""Hidden-face validation: inferred views have no ground truth, so validate
them against the brand palette + garment-type plausibility + mesh sanity.

The dossier has no structured palette field (text blocks only), so the
documented canonical brand palette is the allowed-color set. Inferred views
always route to human regardless — this validation flags obvious violations
early, it does not grant auto-pass.
"""

from __future__ import annotations

# Canonical brand palette (CLAUDE.md brand tokens).
BRAND_PALETTE: dict[str, tuple[int, int, int]] = {
    "#B76E79": (183, 110, 121),  # rose gold
    "#0A0A0A": (10, 10, 10),  # dark
    "#C0C0C0": (192, 192, 192),  # silver
    "#DC143C": (220, 20, 60),  # crimson
    "#D4AF37": (212, 175, 55),  # gold
    "#FFFFFF": (255, 255, 255),  # white (garment base)
}


def color_in_brand_palette(rgb: tuple[int, int, int], *, tolerance: int = 24) -> bool:
    """True if rgb is within Chebyshev `tolerance` of any brand color."""
    return any(
        all(abs(c - b) <= tolerance for c, b in zip(rgb, brand)) for brand in BRAND_PALETTE.values()
    )


def mesh_sanity_ok(*, vertex_count: int, face_count: int, is_watertight: bool) -> tuple[bool, str]:
    """Reject degenerate meshes. Returns (ok, detail)."""
    if vertex_count == 0 or face_count == 0:
        return False, "empty mesh (no geometry)"
    if face_count < 100:
        return False, f"degenerate mesh ({face_count} faces)"
    if not is_watertight:
        return True, "non-watertight (acceptable for open garment surfaces, flagged)"
    return True, "ok"


def inspect_glb_geometry(glb_path: str) -> dict:
    """Load a GLB with trimesh and return geometry stats for mesh_sanity_ok."""
    import trimesh  # type: ignore[import]

    scene = trimesh.load(glb_path, force="scene")
    geo = scene.dump(concatenate=True) if hasattr(scene, "dump") else scene
    return {
        "vertex_count": int(len(geo.vertices)),
        "face_count": int(len(geo.faces)),
        "is_watertight": bool(getattr(geo, "is_watertight", False)),
    }
