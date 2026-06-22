"""Dynamic module loader — importlib-based loader for AOS module packages."""

from __future__ import annotations

import importlib

from aos.modules.types import AgentFactory, ModuleManifest

_MANIFEST_ATTR = "AOS_MODULE_MANIFEST"
_FACTORIES_ATTR = "AOS_MODULE_FACTORIES"


class ModuleLoadError(ImportError):
    """Raised when a module cannot be imported or is missing required attributes."""


def load_from_path(module_path: str) -> tuple[ModuleManifest, dict[str, AgentFactory]]:
    """Import module_path and extract its manifest + factories.

    The target module must export at module scope:
        AOS_MODULE_MANIFEST: ModuleManifest
        AOS_MODULE_FACTORIES: dict[str, AgentFactory]

    Raises ModuleLoadError on import failure or missing / wrong-type attributes.
    """
    try:
        mod = importlib.import_module(module_path)
    except ImportError as exc:
        raise ModuleLoadError(f"Cannot import module at {module_path!r}: {exc}") from exc

    manifest = getattr(mod, _MANIFEST_ATTR, None)
    factories = getattr(mod, _FACTORIES_ATTR, None)

    if not isinstance(manifest, ModuleManifest):
        raise ModuleLoadError(f"{module_path!r} missing {_MANIFEST_ATTR}: ModuleManifest attribute")
    if not isinstance(factories, dict):
        raise ModuleLoadError(
            f"{module_path!r} missing {_FACTORIES_ATTR}: dict[str, AgentFactory] attribute"
        )

    return manifest, factories
