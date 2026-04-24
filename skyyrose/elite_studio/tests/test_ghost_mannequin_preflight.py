from unittest.mock import patch, MagicMock
from skyyrose.elite_studio.graph.nodes import preflight_node
from skyyrose.elite_studio.graph.state import create_initial_state

def _state(sku: str, style: str = "ghost_mannequin") -> dict:
    return create_initial_state(sku=sku, view="front", style=style)

def test_preflight_passes_sets_preflight_result():
    state = _state("br-004")
    # Patch from its home module, not where it's used inside the node locally
    with patch(
        "skyyrose.elite_studio.agents.vision_agent.DualVisionGate"
    ) as mock_gate_class:
        from skyyrose.elite_studio.models import PreflightResult
        mock_gate = mock_gate_class.return_value
        mock_gate.verify_reference.return_value = PreflightResult(
            passed=True, sku="br-004",
            agent_a_verdict="YES: hoodie", agent_b_verdict="YES: hoodie",
        )
        with patch("skyyrose.elite_studio.catalog.Catalog.load") as mock_load:
            mock_product = MagicMock()
            mock_product.name = "BLACK Rose Hoodie"
            mock_load.return_value.require.return_value = mock_product
            
            update = preflight_node(state)
            
    assert update["preflight_result"].passed

def test_preflight_fail_sets_error_status():
    state = _state("br-011")
    with patch("skyyrose.elite_studio.agents.vision_agent.DualVisionGate") as MockGate:
        from skyyrose.elite_studio.models import PreflightResult
        instance = MockGate.return_value
        instance.verify_reference.return_value = PreflightResult(
            passed=False, sku="br-011",
            agent_a_verdict="NO: baseball jersey",
            agent_b_verdict="NO: wrong sport",
            blocking_reason="Agent A: baseball jersey, not hockey",
        )
        with patch("skyyrose.elite_studio.catalog.Catalog.load") as mock_load:
            mock_product = MagicMock()
            mock_product.name = "BR-011 Hockey Jersey"
            mock_load.return_value.require.return_value = mock_product
            
            update = preflight_node(state)
            
    assert update["status"] == "error"
    assert "baseball" in update["error"]

def test_preflight_skipped_for_flat_lay():
    """flat_lay style skips preflight — returns empty dict (node is a no-op)."""
    state = _state("br-004", style="flat_lay")
    update = preflight_node(state)
    assert update == {} or update.get("preflight_result") is None
