"""Agent registry for the Video & Animation venture.

Video is the alpha-status venture; only two providers exist in the
codebase today (anigen, tryon). Every import path is verified at
scaffold time; future providers (FASHN video, runway, etc.) get
appended here as they land.
"""

from __future__ import annotations

from skyyrose.elite_studio.ventures._base import AgentBinding

VIDEO_AGENTS: tuple[AgentBinding, ...] = (
    AgentBinding(
        name="AniGenAgent",
        import_path="agents.anigen_agent.AniGenAgent",
        role="animation",
        ready=False,
    ),
    AgentBinding(
        name="TryOnAgent",
        import_path="skyyrose.elite_studio.agents.tryon_agent.TryOnAgent",
        role="tryon_video",
        ready=False,
    ),
)
