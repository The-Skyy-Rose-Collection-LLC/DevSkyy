"""TryonAgent — Phase B2 stub (dual-agent rebuild pending).

Scorched-earth commit swiped the broken implementation clean. This file's
filename is preserved intentionally — it is the correct home for the
rebuilt dual-agent version in Phase B2.

Planned architecture (see .claude/plans/well-lets-audit-separately-humming-beacon.md):
    Agent A: FASHN tryon
    Agent B: IDM-VTON
    Mode:    best-of-N

Do NOT import this module until Phase B2 lands — every public symbol
raises NotImplementedError with a clear pointer to the plan.
"""

from __future__ import annotations


class TryOnAgent:
    """Placeholder. Phase B2 will implement dual-agent best-of-N logic."""

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "TryonAgent is a Phase B1 stub. See .claude/plans/"
            "well-lets-audit-separately-humming-beacon.md for the dual-agent "
            "rebuild design (best-of-N mode; Agent A=FASHN tryon, Agent B=IDM-VTON)."
        )

# Aliases for backwards compatibility (different modules use different capitalization)
TryonAgent = TryOnAgent

def _find_garment_image(sku: str) -> str:
    raise NotImplementedError("TryonAgent._find_garment_image is a Phase B1 stub.")
