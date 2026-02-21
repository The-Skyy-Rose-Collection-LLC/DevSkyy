"""Agent specifications for Elite Web Builder."""

from .accessibility import ACCESSIBILITY_SPEC
from .backend_dev import BACKEND_DEV_SPEC
from .design_system import DESIGN_SYSTEM_SPEC
from .frontend_dev import FRONTEND_DEV_SPEC
from .performance import PERFORMANCE_SPEC
from .qa import QA_SPEC
from .seo_content import SEO_CONTENT_SPEC

__all__ = [
    "DESIGN_SYSTEM_SPEC",
    "FRONTEND_DEV_SPEC",
    "BACKEND_DEV_SPEC",
    "ACCESSIBILITY_SPEC",
    "PERFORMANCE_SPEC",
    "SEO_CONTENT_SPEC",
    "QA_SPEC",
]
