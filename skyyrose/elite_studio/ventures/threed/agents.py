"""Agent registry for the 3D / Immersive venture (TRELLIS-only / self-hosted).

Per the product directive — *be* the engine, don't refer out to a vendor —
this venture's only live generation path is the self-hosted TRELLIS.2 model
(`agents.trellis_agent.TrellisAgent`, role `generator`, `ready=True`). It runs
microsoft/TRELLIS.2-4B in the isolated `trellis2` conda env on our own GPU.

Tripo and Meshy are paid SaaS providers. They stay registered (real, importable
bindings) but `ready=False` — they are NOT invoked by this venture's pipeline.
The `ThreeDRoundTable` tournament and the broader `ThreeDAgent` replica workflow
both route to those SaaS providers, so they are likewise registered but not the
TRELLIS-only path. To revive a multi-provider tournament, flip the flags and wire
them into pipeline.py (see git history for the round-table plan).

Every import path is verified at scaffold time (see tests/test_smoke.py).
"""

from __future__ import annotations

from skyyrose.elite_studio.ventures._base import AgentBinding

THREED_AGENTS: tuple[AgentBinding, ...] = (
    AgentBinding(
        name="TrellisAgent",
        import_path="agents.trellis_agent.TrellisAgent",
        role="generator",
        ready=True,
    ),
    AgentBinding(
        name="ThreeDAgent",
        import_path="skyyrose.elite_studio.agents.three_d_agent.ThreeDAgent",
        role="replica_workflow",
        ready=False,
    ),
    AgentBinding(
        name="ThreeDRoundTable",
        import_path="orchestration.threed_round_table.ThreeDRoundTable",
        role="tournament",
        ready=False,
    ),
    AgentBinding(
        name="TripoAgent",
        import_path="agents.tripo_agent.TripoAssetAgent",
        role="provider_tripo_legacy",
        ready=False,
    ),
    AgentBinding(
        name="MeshyAgent",
        import_path="agents.meshy_agent.MeshyAgent",
        role="provider_meshy_legacy",
        ready=False,
    ),
)
