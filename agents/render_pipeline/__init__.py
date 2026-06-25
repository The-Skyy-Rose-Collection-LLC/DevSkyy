"""RenderPipeline ADK agent — generates validated product renders for SkyyRose SKUs.

The agent orchestrates the 7-step nano_banana pipeline (load_dossier →
resolve_source → route_engine → build_prompt → generate_image →
qa_tournament → refine_image-and-rejudge) as ADK FunctionTools, with
deterministic engine routing via catalog `engine_override` (the
load-bearing fix from this session's empirical investigation — see
DESIGN.md F3).

Quickstart:
    from agents.render_pipeline import root_agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    runner = Runner(agent=root_agent, app_name="render", session_service=InMemorySessionService())
    # ... see DESIGN.md "CLI / entry points"

CLI:
    adk run agents/render_pipeline --input '{"sku": "br-001", "view": "front"}'
"""

from agents.render_pipeline.agent import root_agent

__all__ = ["root_agent"]
