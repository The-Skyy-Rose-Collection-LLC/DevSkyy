"""Side-effect imports: each module registers its tools via ``@mcp.tool()``.

Tool modules are imported individually. On the slim Fly image
(``MCP_SLIM_IMAGE=1``, set by ``Dockerfile.mcp``), a declared set of modules
whose heavy optional dependencies (``scripts.oai_render``, ``imagery.*``) are
never shipped there — :data:`SLIM_EXCLUDED_MODULES` — is skipped
*deliberately*, with one grouped WARNING naming them. This keeps the
HTTP-mounted ``/mcp`` surface bootable on the lightweight production image
while the full toolset still registers on the full backend
(``main_enterprise`` mounts it at startup).

Any OTHER module that fails to import is NOT expected to be missing — that is
an undeclared regression (e.g. a dependency the slim image's
``requirements-mcp.txt`` should have, or a genuine bug), so it is logged at
ERROR under a distinct event name rather than silently dropped alongside the
declared exclusions. The server still boots either way; the loud log is what
makes an unexpected drop visible instead of silent.
"""

import importlib
import os

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
    # Mined from the retired mcp_servers/ fleet (2026-06-22)
    "external_mcp",
    "rag",
    "orchestration",
)

# Modules deliberately excluded on the slim Fly image (MCP_SLIM_IMAGE=1) —
# their heavy optional deps (scripts.oai_render / imagery.*) are never copied
# into Dockerfile.mcp. This is the source of truth for the slim tool count:
# full tool count minus len(SLIM_EXCLUDED_MODULES) worth of tools.
SLIM_EXCLUDED_MODULES = frozenset({"oai_render", "lora_generation"})
_SLIM_EXCLUSION_REASON = (
    "heavy ML deps (scripts.oai_render / imagery.*) not present on the slim image"
)
_SLIM_IMAGE_ENV = "MCP_SLIM_IMAGE"


def _resolve_modules(all_modules: tuple[str, ...], slim: bool) -> tuple[list[str], list[str]]:
    """Split ``all_modules`` into ``(to_import, deliberately_skipped)``.

    On the full image (``slim=False``) every module is imported. On the slim
    image, modules in :data:`SLIM_EXCLUDED_MODULES` are skipped deliberately;
    everything else still imports normally.
    """
    if not slim:
        return list(all_modules), []
    skipped = [m for m in all_modules if m in SLIM_EXCLUDED_MODULES]
    return [m for m in all_modules if m not in SLIM_EXCLUDED_MODULES], skipped


_IS_SLIM_IMAGE = os.getenv(_SLIM_IMAGE_ENV) == "1"
_to_import, _deliberately_skipped = _resolve_modules(_TOOL_MODULES, _IS_SLIM_IMAGE)

if _deliberately_skipped:
    logger.warning(
        "mcp_tool_modules_slim_excluded",
        modules=list(_deliberately_skipped),
        reason=_SLIM_EXCLUSION_REASON,
    )

for _module_name in _to_import:
    try:
        importlib.import_module(f"{__name__}.{_module_name}")
    except ImportError as exc:  # ModuleNotFoundError included.
        logger.error(
            "mcp_tool_module_unexpected_skip",
            module=_module_name,
            error=str(exc),
        )
