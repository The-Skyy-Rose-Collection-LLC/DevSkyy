"""AOS MemoryIndex — tag-based filter index over a MemoryStore."""

from __future__ import annotations

import time

from aos.memory.store import MemoryStore
from aos.memory.types import MemoryEntry


class MemoryIndex:
    """Tag-based query layer over a MemoryStore.

    Provides label filtering without external embedding or vector dependencies.
    The index is computed on the fly from the live store entries — no separate
    index structure to keep in sync.

    Usage::

        store = MemoryStore()
        index = MemoryIndex(store)

        store.write("42", "plan", "...", tags={"goal", "priority-high"})
        store.write("42", "note", "...", tags={"note"})

        results = index.search(namespace="42", tags={"goal"})
        # → [MemoryEntry(key="plan", ...)]
    """

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def search(
        self,
        *,
        namespace: str,
        tags: frozenset[str] | set[str],
        match_all: bool = True,
    ) -> tuple[MemoryEntry, ...]:
        """Return all non-expired entries in namespace whose tags satisfy the filter.

        Args:
            namespace: The namespace to search within.
            tags:      Labels to match against each entry's tags.
            match_all: If True (default), all tags must be present (AND logic).
                       If False, any single matching tag qualifies (OR logic).

        Returns:
            Tuple of matching MemoryEntry objects, newest first.
        """
        tag_set = frozenset(tags)
        if not tag_set:
            return ()

        namespace_data = self._store._store.get(namespace, {})
        now = time.time()
        results: list[MemoryEntry] = []

        for entry in namespace_data.values():
            if entry.is_expired(now=now):
                continue
            if match_all:
                if tag_set <= entry.tags:
                    results.append(entry)
            else:
                if tag_set & entry.tags:
                    results.append(entry)

        results.sort(key=lambda e: e.created_at, reverse=True)
        return tuple(results)

    def search_all_namespaces(
        self,
        *,
        tags: frozenset[str] | set[str],
        match_all: bool = True,
    ) -> tuple[MemoryEntry, ...]:
        """Search every namespace and return matching entries, newest first."""
        all_results: list[MemoryEntry] = []
        for ns in self._store.list_namespaces():
            all_results.extend(self.search(namespace=ns, tags=tags, match_all=match_all))
        all_results.sort(key=lambda e: e.created_at, reverse=True)
        return tuple(all_results)
