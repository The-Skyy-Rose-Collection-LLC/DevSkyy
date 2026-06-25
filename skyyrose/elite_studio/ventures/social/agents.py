"""Agent registry for the Social Media venture.

All three bindings reference real, importable agents in the DevSkyy
`agents/` package and are wired into LangGraph nodes (see pipeline.py):

- **publisher** (`SocialMediaAgent`) — runs live on every pipeline pass.
  Template-based brand-voice caption + hashtag generation; no paid calls.
- **graphics** (`CreativeAgent`) — wired into the `compose_graphics` node
  but invoked only when `state["generate_graphics"]` is True (paid image
  generation, gated per the STOP-AND-SHOW protocol).
- **strategist** (`MarketingAgent`) — wired into the `strategize` node but
  invoked only when `state["run_strategy"]` is True (LLM-backed).

`ready=True` reflects wiring status (all three have nodes). It does NOT
mean the agent fires unconditionally — the cost gate governs invocation.
Import paths are verified at scaffold time (see tests/test_smoke.py).
"""

from __future__ import annotations

from skyyrose.elite_studio.ventures._base import AgentBinding

SOCIAL_AGENTS: tuple[AgentBinding, ...] = (
    AgentBinding(
        name="SocialMediaAgent",
        import_path="agents.social_media_agent.SocialMediaAgent",
        role="publisher",
        ready=True,
    ),
    AgentBinding(
        name="CreativeAgent",
        import_path="agents.creative_agent.CreativeAgent",
        role="graphics",
        ready=True,
    ),
    AgentBinding(
        name="MarketingAgent",
        import_path="agents.marketing_agent.MarketingAgent",
        role="strategist",
        ready=True,
    ),
)
