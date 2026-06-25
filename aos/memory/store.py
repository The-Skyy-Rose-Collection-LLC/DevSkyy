"""AOS MemoryStore — namespaced key/value store with TTL expiry."""

from __future__ import annotations

import time
from typing import Any

from aos.memory.types import MemoryEntry, MemoryKeyError, MemoryNamespaceError


class MemoryStore:
    """Namespaced in-process key/value store with optional TTL.

    Each namespace (typically an agent PID) holds its own isolated dict.
    TTL expiry is checked lazily on read — no background sweep required.

    Usage::

        store = MemoryStore()
        store.write("42", "goal", "summarise Q4 results", ttl=300.0)
        entry = store.read("42", "goal")
        store.delete("42", "goal")
        store.clear_namespace("42")
    """

    def __init__(self) -> None:
        self._store: dict[str, dict[str, MemoryEntry]] = {}

    # ------------------------------------------------------------------ write

    def write(
        self,
        namespace: str,
        key: str,
        value: Any,
        *,
        tags: frozenset[str] | set[str] | None = None,
        ttl: float | None = None,
    ) -> MemoryEntry:
        """Write a value to namespace/key. Replaces any existing entry.

        Args:
            namespace: Isolating scope (e.g. agent PID).
            key:       Lookup key.
            value:     Payload — anything serialisable.
            tags:      Optional labels for MemoryIndex queries.
            ttl:       Seconds until expiry.  None = no expiry.

        Returns:
            The written MemoryEntry.
        """
        now = time.time()
        entry = MemoryEntry(
            key=key,
            value=value,
            namespace=namespace,
            tags=frozenset(tags) if tags else frozenset(),
            created_at=now,
            expires_at=now + ttl if ttl is not None else None,
        )
        self._store.setdefault(namespace, {})[key] = entry
        return entry

    # ------------------------------------------------------------------ read

    def read(self, namespace: str, key: str) -> MemoryEntry:
        """Return the entry at namespace/key, or raise MemoryKeyError if absent/expired."""
        namespace_data = self._store.get(namespace)
        if namespace_data is None:
            raise MemoryKeyError(f"namespace {namespace!r} not found")
        entry = namespace_data.get(key)
        if entry is None or entry.is_expired():
            if entry is not None and entry.is_expired():
                del namespace_data[key]
            raise MemoryKeyError(f"key {key!r} not found in namespace {namespace!r}")
        return entry

    def get(self, namespace: str, key: str, default: Any = None) -> Any:
        """Return the value at namespace/key, or default if absent/expired."""
        try:
            return self.read(namespace, key).value
        except MemoryKeyError:
            return default

    # ------------------------------------------------------------------ delete

    def delete(self, namespace: str, key: str) -> None:
        """Remove a key from a namespace. Raises MemoryKeyError if missing."""
        namespace_data = self._store.get(namespace)
        if namespace_data is None or key not in namespace_data:
            raise MemoryKeyError(f"key {key!r} not found in namespace {namespace!r}")
        del namespace_data[key]

    def clear_namespace(self, namespace: str) -> int:
        """Remove all entries in a namespace and return count cleared.

        Raises MemoryNamespaceError if the namespace does not exist.
        """
        if namespace not in self._store:
            raise MemoryNamespaceError(f"namespace {namespace!r} not found")
        count = len(self._store.pop(namespace))
        return count

    # ------------------------------------------------------------------ query

    def list_keys(self, namespace: str) -> tuple[str, ...]:
        """Return all non-expired keys in a namespace (creates namespace if absent)."""
        namespace_data = self._store.get(namespace, {})
        now = time.time()
        live = [k for k, e in namespace_data.items() if not e.is_expired(now=now)]
        return tuple(live)

    def list_namespaces(self) -> tuple[str, ...]:
        """Return all namespaces that have at least one live entry."""
        now = time.time()
        return tuple(
            ns
            for ns, data in self._store.items()
            if any(not e.is_expired(now=now) for e in data.values())
        )

    def has(self, namespace: str, key: str) -> bool:
        """Return True if namespace/key exists and has not expired."""
        try:
            self.read(namespace, key)
            return True
        except MemoryKeyError:
            return False

    # ------------------------------------------------------------------ stats

    @property
    def total_entries(self) -> int:
        """Count of all live entries across all namespaces."""
        now = time.time()
        return sum(
            1 for data in self._store.values() for e in data.values() if not e.is_expired(now=now)
        )
