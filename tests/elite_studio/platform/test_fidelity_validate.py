from skyyrose.elite_studio.platform.fidelity.validate import (
    BRAND_PALETTE,
    color_in_brand_palette,
    mesh_sanity_ok,
)


def test_rose_gold_is_in_palette():
    assert color_in_brand_palette((183, 110, 121), tolerance=10) is True  # #B76E79


def test_off_brand_green_is_not_in_palette():
    assert color_in_brand_palette((0, 200, 0), tolerance=10) is False


def test_palette_contains_documented_brand_hexes():
    assert "#B76E79" in BRAND_PALETTE and "#D4AF37" in BRAND_PALETTE


def test_mesh_sanity_rejects_empty_mesh():
    ok, detail = mesh_sanity_ok(vertex_count=0, face_count=0, is_watertight=False)
    assert ok is False and "empty" in detail.lower()


def test_mesh_sanity_accepts_well_formed_mesh():
    ok, _ = mesh_sanity_ok(vertex_count=5000, face_count=9000, is_watertight=True)
    assert ok is True
