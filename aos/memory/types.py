"""AOS Memory — entry type and exceptions."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MemoryEntry:
    """A single namespaced memory record stored by an agent process.

    Attributes:
        key:        Lookup key within the namespace.
        value:      Arbitrary serialisable payload.
        namespace:  Typically the agent PID string; isolates each process's memory.
        tags:       Searchable labels used by MemoryIndex queries.
        created_at: Unix timestamp when the entry was written.
        expires_at: Unix timestamp after which the entry is expired, or None for no expiry.
    """

    key: str
    value: Any
    namespace: str
    tags: frozenset[str] = field(default_factory=frozenset)
    created_at: float = field(default_factory=time.time)
    expires_at: float | None = None

    def is_expired(self, *, now: float | None = None) -> bool:
        if self.expires_at is None:
            return False
        return (now if now is not None else time.time()) >= self.expires_at


class MemoryKeyError(KeyError):
    """Raised when a key is not found (or has expired) in a MemoryStore namespace."""


class MemoryNamespaceError(KeyError):
    """Raised when a namespace does not exist in the store."""
