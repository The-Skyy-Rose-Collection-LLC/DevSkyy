from skyyrose.elite_studio.graph.state import create_initial_state


def test_create_initial_state_ghost_mannequin():
    state = create_initial_state(sku="br-004", view="front", style="ghost_mannequin")
    assert state["style"] == "ghost_mannequin"
    assert state["preflight_result"] is None
    assert state["ghost_mannequin_front_path"] == ""
    assert state["ghost_mannequin_back_path"] == ""
