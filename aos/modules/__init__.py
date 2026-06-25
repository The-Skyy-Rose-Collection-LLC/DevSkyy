"""AOS Modules — pluggable capability registration for agent types and tools."""

from aos.modules.loader import ModuleLoadError, load_from_path
from aos.modules.registry import DuplicateModuleError, ModuleNotFoundError, ModuleRegistry
from aos.modules.types import AgentFactory, ModuleManifest

__all__ = [
    "AgentFactory",
    "ModuleManifest",
    "ModuleRegistry",
    "DuplicateModuleError",
    "ModuleNotFoundError",
    "ModuleLoadError",
    "load_from_path",
]
