from pathlib import Path

from skyyrose.elite_studio.platform.fidelity.render import (
    RENDER_ANGLES,
    RenderViews,
    coverage_from_references,
)


def test_render_angles_include_front_back_sides():
    assert {"front", "back", "left", "right"} <= set(RENDER_ANGLES)


def test_coverage_marks_referenced_angles_verified():
    refs = {"front": Path("/x/front.jpg")}
    cov = coverage_from_references(refs, RENDER_ANGLES)
    assert cov["front"] is True  # has reference -> verifiable
    assert cov["back"] is False  # no reference -> inferred


def test_render_views_reports_inferred_angles():
    views = RenderViews(
        angle_paths={"front": Path("/r/front.png"), "back": Path("/r/back.png")},
        coverage={"front": True, "back": False},
    )
    assert views.inferred_angles() == ("back",)
    assert views.verified_angles() == ("front",)
