from unittest.mock import patch

from skyyrose.elite_studio.graph.nodes import ghost_mannequin_composite_node
from skyyrose.elite_studio.graph.state import create_initial_state
from skyyrose.elite_studio.models import GenerationResult


def _state_with_renders(sku: str, front: str, back: str) -> dict:
    s = create_initial_state(sku=sku, view="front", style="ghost_mannequin")
    s["generation_result"] = GenerationResult(
        success=True, output_path=front, provider="test", model="test"
    )
    s["ghost_mannequin_front_path"] = front
    s["ghost_mannequin_back_path"] = back
    return s


def test_collar_garment_applies_neck_in(tmp_path):
    """br-004 is a hoodie — neck-in composite must be applied."""
    front = tmp_path / "front.webp"
    back = tmp_path / "back.webp"
    # Write minimal valid images (Pillow will use them)
    from PIL import Image

    img = Image.new("RGB", (1024, 1024), color=(10, 10, 10))
    img.save(str(front), "WEBP")
    img.save(str(back), "WEBP")

    state = _state_with_renders("br-004", str(front), str(back))
    with patch("skyyrose.elite_studio.graph.nodes._is_collar_garment", return_value=True):
        update = ghost_mannequin_composite_node(state)

    result = update.get("ghost_mannequin_composite_result")
    assert result is not None
    assert result.neck_in_applied
    assert result.success


def test_non_collar_garment_skips_neck_in(tmp_path):
    """br-002 is joggers — neck-in composite is skipped."""
    from PIL import Image

    front = tmp_path / "front.webp"
    Image.new("RGB", (1024, 1024)).save(str(front), "WEBP")

    state = _state_with_renders("br-002", str(front), "")
    with patch("skyyrose.elite_studio.graph.nodes._is_collar_garment", return_value=False):
        update = ghost_mannequin_composite_node(state)

    result = update.get("ghost_mannequin_composite_result")
    assert result is not None
    assert not result.neck_in_applied
    assert result.success
