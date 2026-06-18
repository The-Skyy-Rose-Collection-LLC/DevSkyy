from skyyrose.elite_studio.graph.builder import _GENERATOR, _THREE_D, GraphConfig, build_graph


def test_graph_topology_3d_activation():
    # Build graph with 3D enabled
    config = GraphConfig(enable_3d=True)
    graph = build_graph(config)

    # Access the underlying StateGraph to check nodes
    # CompiledGraph stores the state_graph in 'builder' or similar depending on LangGraph version
    # In some versions it's graph.builder.nodes
    nodes = graph.nodes
    assert _THREE_D in nodes
    # generator node must NOT be registered when 3D is active — no dead nodes
    assert _GENERATOR not in nodes


def test_graph_topology_default_generator():
    config = GraphConfig(enable_3d=False)
    graph = build_graph(config)

    nodes = graph.nodes
    assert _THREE_D not in nodes
    assert _GENERATOR in nodes
