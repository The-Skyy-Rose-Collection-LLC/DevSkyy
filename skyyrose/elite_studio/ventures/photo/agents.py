"""Agent registry for the Editorial Photography venture.

Bindings reference existing agents in the Elite Studio codebase. Each
import path is verified at scaffold time (see tests/test_smoke.py).
The `ready` flag is False where the agent exists but has not yet been
wired into the venture's LangGraph nodes — preserving the no-stub
invariant while honestly reporting wiring status.
"""

from __future__ import annotations

from skyyrose.elite_studio.ventures._base import AgentBinding

PHOTO_AGENTS: tuple[AgentBinding, ...] = (
    AgentBinding(
        name="VisionAgent",
        import_path="skyyrose.elite_studio.agents.vision_agent.VisionAgent",
        role="vision",
        ready=False,
    ),
    AgentBinding(
        name="GeneratorAgent",
        import_path="skyyrose.elite_studio.agents.generator_agent.GeneratorAgent",
        role="renderer",
        ready=False,
    ),
    AgentBinding(
        name="QualityAgent",
        import_path="skyyrose.elite_studio.agents.quality_agent.QualityAgent",
        role="quality",
        ready=False,
    ),
    AgentBinding(
        name="PromptEnrichmentAgent",
        import_path=("skyyrose.elite_studio.agents.prompt_enrichment_agent.PromptEnrichmentAgent"),
        role="prompt",
        ready=False,
    ),
    AgentBinding(
        name="PhotographyDirector",
        import_path="skyyrose.elite_studio.fashion.photography.PhotographyDirector",
        role="standards_director",
        ready=True,
    ),
)
