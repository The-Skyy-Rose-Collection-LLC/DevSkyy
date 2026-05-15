"""ModuleRegistry — pluggable agent-factory store for the AOS kernel."""

from __future__ import annotations

from aos.modules.types import AgentFactory, ModuleManifest


class DuplicateModuleError(ValueError):
    """Raised when a module name is already registered."""


class ModuleNotFoundError(KeyError):
    """Raised when unloading an unknown module name."""


class ModuleRegistry:
    """Stores agent factories keyed by agent_type, grouped by ModuleManifest.

    Factories are registered synchronously (no I/O). Audit events are emitted
    by the Kernel wrapper — the registry itself is pure in-memory state.
    """

    def __init__(self) -> None:
        self._factories: dict[str, AgentFactory] = {}
        self._manifests: dict[str, ModuleManifest] = {}
        self._type_to_manifest: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Single-type registration (no manifest tracking)
    # ------------------------------------------------------------------

    def register_type(self, agent_type: str, factory: AgentFactory) -> None:
        """Register a factory under agent_type without manifest tracking."""
        self._factories[agent_type] = factory

    # ------------------------------------------------------------------
    # Manifest-level load / unload
    # ------------------------------------------------------------------

    def load(self, manifest: ModuleManifest, factories: dict[str, AgentFactory]) -> None:
        """Load a manifest and its factories.

        Raises DuplicateModuleError if manifest.name is already loaded.
        """
        if manifest.name in self._manifests:
            raise DuplicateModuleError(f"Module already loaded: {manifest.name!r}")
        for agent_type, factory in factories.items():
            self._factories[agent_type] = factory
            self._type_to_manifest[agent_type] = manifest.name
        self._manifests[manifest.name] = manifest

    def unload(self, manifest_name: str) -> frozenset[str]:
        """Unload a manifest and remove its factories.

        Returns the set of agent_types that were removed.
        Raises ModuleNotFoundError if manifest_name is not loaded.
        """
        manifest = self._manifests.get(manifest_name)
        if manifest is None:
            raise ModuleNotFoundError(f"Module not loaded: {manifest_name!r}")
        removed: set[str] = set()
        for agent_type in manifest.agent_types:
            self._factories.pop(agent_type, None)
            self._type_to_manifest.pop(agent_type, None)
            removed.add(agent_type)
        del self._manifests[manifest_name]
        return frozenset(removed)

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    def get_factory(self, agent_type: str) -> AgentFactory | None:
        """Return the factory for agent_type, or None if not registered."""
        return self._factories.get(agent_type)

    def is_loaded(self, manifest_name: str) -> bool:
        """Return True if a manifest with this name is currently loaded."""
        return manifest_name in self._manifests

    @property
    def registered_types(self) -> frozenset[str]:
        """All currently registered agent_types across all manifests and bare registrations."""
        return frozenset(self._factories)

    @property
    def manifests(self) -> tuple[ModuleManifest, ...]:
        """All loaded manifests in insertion order."""
        return tuple(self._manifests.values())
