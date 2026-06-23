"""Phase 1 / P-paths: render outputs are scene-addressed and written atomically.

Model-free. A same-SKU render for two different scenes must not collide on a
single ``{sku}-shadow.png`` path (the gate would score whichever bytes happen to
be on disk). The shadow write is atomic (tmp + os.replace).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from skyyrose.elite_studio.agents.compositor.stage_f_shadows import generate_shadows

pytestmark = pytest.mark.unit


def _composite_with_ground(p: Path) -> str:
    """A composite whose subject occupies <85% of the frame (so a shadow is drawn)."""
    composite = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    composite.paste(Image.new("RGBA", (40, 40), (200, 0, 0, 255)), (80, 80))
    composite.save(p)
    return str(p)


def test_shadow_path_includes_scene_and_differs(tmp_path):
    src = _composite_with_ground(tmp_path / "c.png")
    p1 = generate_shadows(src, "br-001", str(tmp_path), scene_name="rooftop")
    p2 = generate_shadows(src, "br-001", str(tmp_path), scene_name="lot")
    assert p1 != p2
    assert "rooftop" in p1 and "lot" in p2
    assert Path(p1).exists() and Path(p2).exists()


def test_shadow_default_no_scene_is_backward_compatible(tmp_path):
    src = _composite_with_ground(tmp_path / "c.png")
    p = generate_shadows(src, "br-001", str(tmp_path))  # no scene_name
    assert p.endswith("br-001-shadow.png") and Path(p).exists()
