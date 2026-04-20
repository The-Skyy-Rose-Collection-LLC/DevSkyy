"""UpscalingAgent — Phase B2 stub (dual-agent rebuild pending).

Scorched-earth commit swiped the broken implementation clean. This file's
filename is preserved intentionally — it is the correct home for the
rebuilt dual-agent version in Phase B2.

Planned architecture (see .claude/plans/well-lets-audit-separately-humming-beacon.md):
    Agent A: FLUX upscaler
    Agent B: Real-ESRGAN
    Mode:    best-of-N

Do NOT import this module until Phase B2 lands — every public symbol
raises NotImplementedError with a clear pointer to the plan.
"""

from __future__ import annotations


class UpscalingAgent:
    """Placeholder. Phase B2 will implement dual-agent best-of-N logic."""

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "UpscalingAgent is a Phase B1 stub. See .claude/plans/"
            "well-lets-audit-separately-humming-beacon.md for the dual-agent "
            "rebuild design (best-of-N mode; Agent A=FLUX upscaler, Agent B=Real-ESRGAN)."
        )
