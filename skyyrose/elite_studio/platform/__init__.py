"""Multi-tenant platform layer for Elite Studio (Replica Foundry).

Cross-venture primitives: tenancy, capability probing, fidelity gating,
approval. Each venture (threed first, 2D later) composes these through a
tenant-scoped service so every delivered asset is a verified replica.
"""

from __future__ import annotations

from skyyrose.elite_studio.platform.service import GenerationResult, generate_3d

__all__ = ["GenerationResult", "generate_3d"]
