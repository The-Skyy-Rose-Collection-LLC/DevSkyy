"""Side-effect imports: each module registers its tools via ``@mcp.tool()``.

Tool modules are imported individually and defensively. A module whose optional
dependencies are unavailable — e.g. the heavy local render/imagery pipelines
(``scripts.oai_render``, ``imagery.*``) that ship only in the full dev/render
environment and not the slim API container — is skipped with a warning rather
than crashing the whole MCP-server import.

This keeps the HTTP-mounted ``/mcp`` surface bootable on the lightweight
production image (``main_enterprise`` mounts it at startup) while the full
toolset still registers wherever its dependencies are present.
"""

import importlib

from utils.logging_utils import get_logger

logger = get_logger(__name__)

# Registration order preserved from the original explicit import block. Each
# module performs its @mcp.tool() registration as an import side effect.
_TOOL_MODULES = (
    "advanced",
    "claude_sdk",
    "cli_anything",
    "ecommerce",
    "elite_studio",
    "infrastructure",
    "lora_generation",
    "lora_training",
    "marketing",
    "ml",
    "monitoring",
    "oai_render",
    "resources",
    "threed",
    "virtual_tryon",
    "wc_client",
    "wordpress",
    "wp_deploy",
)

for _module_name in _TOOL_MODULES:
    try:
        importlib.import_module(f"{__name__}.{_module_name}")
    except ImportError as exc:  # ModuleNotFoundError included.
        logger.warning(
            "mcp_tool_module_skipped",
            module=_module_name,
            error=str(exc),
        )
