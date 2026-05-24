"""compositor — stage modules for the 6-stage scene compositing pipeline.

Public API re-exported for back-compat. External callers should import from
``skyyrose.elite_studio.agents.compositor_agent`` which is the legacy shim.
"""

from .infra import upload_to_fal
from .lighting import SCENE_LOOKBOOK
from .orchestrator import CompositorAgent

__all__ = [
    "CompositorAgent",
    "SCENE_LOOKBOOK",
    "upload_to_fal",
]
