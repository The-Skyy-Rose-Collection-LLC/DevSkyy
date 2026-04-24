from unittest.mock import patch, MagicMock
from skyyrose.elite_studio.agents.vision_agent import DualVisionGate, VisionAgent

def _make_gate() -> DualVisionGate:
    # We need to mock anthropic.Anthropic within __init__
    with patch("anthropic.Anthropic"):
        return DualVisionGate()

def test_alias_works():
    """VisionAgent must remain importable for nodes.py compatibility."""
    assert VisionAgent is DualVisionGate

def test_consensus_both_yes(tmp_path):
    """Both models YES → passed=True, verdict=consensus."""
    img = tmp_path / "test.jpg"
    img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)  # minimal JPEG header

    gate = _make_gate()
    with (
        patch.object(gate, "_call_claude", return_value="YES: confirms hoodie"),
        patch.object(gate, "_call_gemini", return_value="YES: hoodie confirmed"),
    ):
        result = gate.verify_reference(str(img), sku="br-004", expected_garment="hoodie")

    assert result.passed

def test_consensus_a_no_blocks(tmp_path):
    """Agent A NO → passed=False even if B says YES."""
    img = tmp_path / "test.jpg"
    img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)

    gate = _make_gate()
    with (
        patch.object(gate, "_call_claude", return_value="NO: this is a baseball jersey"),
        patch.object(gate, "_call_gemini", return_value="YES: looks like a hoodie"),
    ):
        result = gate.verify_reference(str(img), sku="br-011", expected_garment="hockey jersey")

    assert not result.passed
    assert "baseball jersey" in result.blocking_reason

def test_consensus_b_no_blocks(tmp_path):
    """Agent B NO → passed=False even if A says YES."""
    img = tmp_path / "test.jpg"
    img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)

    gate = _make_gate()
    with (
        patch.object(gate, "_call_claude", return_value="YES: hoodie confirmed"),
        patch.object(gate, "_call_gemini", return_value="NO: this is a crewneck, not a hoodie"),
    ):
        result = gate.verify_reference(str(img), sku="br-004", expected_garment="hoodie")

    assert not result.passed

def test_analyze_wraps_verify_reference(tmp_path):
    """analyze() is the nodes.py interface — must return SynthesizedVision."""
    img = tmp_path / "ref.jpg"
    img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)

    gate = _make_gate()
    with (
        patch.object(gate, "_call_claude", return_value="YES: sg-013 mint crewneck confirmed"),
        patch.object(gate, "_call_gemini", return_value="YES: confirmed crewneck"),
        patch("skyyrose.elite_studio.agents.vision_agent._reference_path", return_value=str(img)),
        patch("skyyrose.elite_studio.catalog.Catalog.load") as mock_load,
    ):
        mock_product = MagicMock()
        mock_product.name = "Mint & Lavender Crewneck"
        mock_product.branding_summary = "SR monogram"
        mock_load.return_value.require.return_value = mock_product
        
        from skyyrose.elite_studio.models import SynthesizedVision
        result = gate.analyze("sg-013", "front")
    assert isinstance(result, SynthesizedVision)
    assert result.success
