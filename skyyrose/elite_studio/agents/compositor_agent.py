"""CompositorAgent — public entry point (thin re-export shim).

This module was refactored in H-03 of the elite_studio audit (2026-05-24).
The 1241-line monolith has been split into stage modules under the
``compositor/`` sub-package. This file is now a shim that:

1. Re-exports the public symbols (CompositorAgent, SCENE_LOOKBOOK, upload_to_fal)
   so all existing import paths continue to work without change.
2. Re-imports the module-level names that the test suite patches via
   ``unittest.mock.patch("...compositor_agent.<name>")`` — patching only works
   when the name exists in this namespace.

External callers (coordinator.py, cli.py, graph/nodes.py) require no changes.
"""

from __future__ import annotations

import httpx  # noqa: F401 — patched by tests at this namespace
from PIL import Image, ImageFilter  # noqa: F401

from ..config import get_anthropic_client  # noqa: F401 — patched by tests at this namespace
from ..gemini_rest import analyze_vision  # noqa: F401 — patched by tests at this namespace

# rembg optional import — same sentinel / shim pattern as original
from .compositor.infra import fal_client  # noqa: F401 — patched by tests at this namespace
from .compositor.infra import remove  # noqa: F401 — patched by tests at this namespace
from .compositor.infra import upload_to_fal  # noqa: F401
from .compositor.infra import (  # noqa: F401
    _REMBG_UNAVAILABLE_SENTINEL,
    _b64_image,
    _b64_image_for_claude,
    _cache_dir,
    _extract_first_image_url,
    _file_hash,
    _gate_budget,
    _matte_via_fal,
    _safe_json_extract,
    _strict_budget_enabled,
)
from .compositor.lighting import SCENE_LOOKBOOK  # noqa: F401
from .compositor.orchestrator import CompositorAgent  # noqa: F401

# Module-level helpers preserved for any callers that import them directly.
from .compositor.stage_g_visual_qa import (  # noqa: F401
    _DEFAULT_CENTROID_PATH,
    _DEFAULT_QA_RUBRIC,
)
from .compositor.stage_g_visual_qa import maybe_apply_gate as _maybe_apply_gate  # noqa: F401
from .compositor.stage_g_visual_qa import visual_qa_gemini as _visual_qa_gemini  # noqa: F401

# ---------------------------------------------------------------------------
# Stage module imports — kept at this namespace so tests can patch them.
# ``patch("skyyrose.elite_studio.agents.compositor_agent.remove")`` replaces
# the ``remove`` binding in THIS module, which the stage modules reference
# via ``compositor_agent.remove`` when called through CompositorAgent methods.
#
# NOTE: The stage modules import these names from ``infra.py`` at their own
# import time. For patch() to intercept calls made inside stage functions
# (stage_a_matte, stage_d_flux, etc.) the tests would need to patch the name
# at the infra namespace too. The existing test suite patches at
# compositor_agent namespace and calls methods on CompositorAgent instances,
# which delegate to stage functions — this works because CompositorAgent's
# method shims call the stage functions at call time, not import time.
# ---------------------------------------------------------------------------


__all__ = [
    "CompositorAgent",
    "SCENE_LOOKBOOK",
    "upload_to_fal",
]
