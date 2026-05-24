"""Agent registry for the 3D / Immersive venture.

Composes the Elite Studio internal `three_d_agent` with the root-level
provider agents (Tripo, Meshy, TRELLIS) plus the tournament
orchestrator. Every import path is verified at scaffold time.
"""

from __future__ import annotations

from skyyrose.elite_studio.ventures._base import AgentBinding

THREED_AGENTS: tuple[AgentBinding, ...] = (
    AgentBinding(
        name="ThreeDAgent",
        import_path="skyyrose.elite_studio.agents.three_d_agent.ThreeDAgent",
        role="studio_3d",
        ready=False,
    ),
    AgentBinding(
        name="TripoAgent",
        import_path="agents.tripo_agent.TripoAssetAgent",
        role="provider_tripo",
        ready=False,
    ),
    AgentBinding(
        name="MeshyAgent",
        import_path="agents.meshy_agent.MeshyAgent",
        role="provider_meshy",
        ready=False,
    ),
    AgentBinding(
        name="TrellisAgent",
        import_path="agents.trellis_agent.TrellisAgent",
        role="provider_trellis",
        ready=False,
    ),
    AgentBinding(
        name="ThreeDRoundTable",
        import_path="orchestration.threed_round_table.ThreeDRoundTable",
        role="tournament",
        ready=True,
    ),
)
