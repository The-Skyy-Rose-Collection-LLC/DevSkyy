"""Specialist agents for Elite Web Builder.

Each agent is defined as an AgentSpec with role, system prompt, and capabilities.
Import individual specs or use ALL_SPECS for the complete team.

Note: Sub-modules use CWD-relative absolute imports (e.g., ``from agents.base
import ...``).  When running via ``run.py`` the CWD is ``elite_web_builder/``
so these resolve correctly.  For external imports from the project root, use
the subprocess helper in ``scripts/verify_pipelines.py``.
"""

import sys
from pathlib import Path

_EWB_ROOT = str(Path(__file__).resolve().parent.parent)
if _EWB_ROOT not in sys.path:
    sys.path.insert(0, _EWB_ROOT)

from agents.accessibility import ACCESSIBILITY_SPEC  # noqa: E402
from agents.backend_dev import BACKEND_DEV_SPEC  # noqa: E402
from agents.base import AgentCapability, AgentOutput, AgentRole, AgentSpec  # noqa: E402
from agents.competitor_scout import COMPETITOR_SCOUT_SPEC  # noqa: E402
from agents.design_system import DESIGN_SYSTEM_SPEC  # noqa: E402
from agents.ecommerce_photography import ECOMMERCE_PHOTOGRAPHY_SPEC  # noqa: E402
from agents.frontend_dev import FRONTEND_DEV_SPEC  # noqa: E402
from agents.garment_3d import GARMENT_3D_SPEC  # noqa: E402
from agents.imagery import IMAGERY_SPEC  # noqa: E402
from agents.performance import PERFORMANCE_SPEC  # noqa: E402
from agents.provider_adapters import (  # noqa: E402
    LLMMessage,
    LLMResponse,
    get_adapter,
)
from agents.qa import QA_SPEC  # noqa: E402
from agents.runtime import AgentRuntime  # noqa: E402
from agents.seo_content import SEO_CONTENT_SPEC  # noqa: E402
from agents.social_media import SOCIAL_MEDIA_SPEC  # noqa: E402
from agents.theme_builder import THEME_BUILDER_SPEC  # noqa: E402

# Convention: new specs append at the end. Test regression guards
# (tests/test_new_specs.py::test_legacy_specs_preserved_at_original_indices)
# pin indices 0-9 to the original specs so reorderings surface in CI.
ALL_SPECS: tuple[AgentSpec, ...] = (
    THEME_BUILDER_SPEC,
    DESIGN_SYSTEM_SPEC,
    FRONTEND_DEV_SPEC,
    BACKEND_DEV_SPEC,
    ACCESSIBILITY_SPEC,
    PERFORMANCE_SPEC,
    SEO_CONTENT_SPEC,
    QA_SPEC,
    IMAGERY_SPEC,
    SOCIAL_MEDIA_SPEC,
    ECOMMERCE_PHOTOGRAPHY_SPEC,
    GARMENT_3D_SPEC,
    COMPETITOR_SCOUT_SPEC,
)

__all__ = [
    "AgentCapability",
    "AgentOutput",
    "AgentRole",
    "AgentSpec",
    "ACCESSIBILITY_SPEC",
    "BACKEND_DEV_SPEC",
    "COMPETITOR_SCOUT_SPEC",
    "DESIGN_SYSTEM_SPEC",
    "ECOMMERCE_PHOTOGRAPHY_SPEC",
    "FRONTEND_DEV_SPEC",
    "GARMENT_3D_SPEC",
    "IMAGERY_SPEC",
    "PERFORMANCE_SPEC",
    "QA_SPEC",
    "SEO_CONTENT_SPEC",
    "SOCIAL_MEDIA_SPEC",
    "THEME_BUILDER_SPEC",
    "ALL_SPECS",
    "AgentRuntime",
    "LLMMessage",
    "LLMResponse",
    "get_adapter",
]
