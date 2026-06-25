"""AOS module types — manifest and factory type alias."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

AgentFactory = Callable[[], Awaitable[Any]]


@dataclass(frozen=True)
class ModuleManifest:
    """Metadata describing a single loadable AOS module.

    A module is a named capability unit that registers one or more agent_types
    into the kernel's ModuleRegistry.

    module_path: dotted import path used by the dynamic loader (optional;
                 leave blank for manifests constructed in-process).
    """

    name: str
    version: str
    agent_types: tuple[str, ...]
    description: str = ""
    module_path: str = ""
