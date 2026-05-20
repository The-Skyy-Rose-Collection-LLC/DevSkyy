# aos/memory/ — namespaced TTL key/value store with tag-based search

Process-local memory that each agent uses to retain plans, notes, or partial state across kernel events. The store is namespaced (typically by agent PID) and entries can carry tags + a TTL. A separate `MemoryIndex` provides tag-filtered search across one or all namespaces. Expiry is lazy — entries are dropped on read rather than via a background sweep.

## Key files

- `store.py` — `MemoryStore`: `write(namespace, key, value, *, tags=None, ttl=None) → MemoryEntry`; `read(namespace, key) → MemoryEntry` raises `MemoryKeyError` on miss or expiry; `get(namespace, key, default=None) → Any` is the default-returning variant; `delete(namespace, key)`; `clear_namespace(namespace) → int` removes a whole namespace and returns the count (raises `MemoryNamespaceError` if absent); `list_keys`, `list_namespaces`, `has`, and the `total_entries` property cover introspection.
- `index.py` — `MemoryIndex(store)`: tag-based query layer over a live `MemoryStore`. `search(*, namespace, tags, match_all=True) → tuple[MemoryEntry, ...]` (AND when `match_all=True`, OR when `False`). `search_all_namespaces(*, tags, match_all=True)` fans across every namespace. No separate index structure — queries iterate the live store.
- `types.py` — `MemoryEntry` `@dataclass(frozen=True)` with `key`, `value`, `namespace`, `tags: frozenset[str]`, `created_at`, `expires_at`. Method `is_expired(*, now=None) → bool`. Exceptions: `MemoryKeyError(KeyError)`, `MemoryNamespaceError(KeyError)`.

## Conventions

- Namespace is a string — typically the agent PID, but the store does not enforce that. Anything string-keyed works.
- TTL is a `float` in seconds measured from write time; `None` means no expiry. Expiry is checked on every read via `MemoryEntry.is_expired(now=...)` and drops the entry from the dict lazily.
- `MemoryEntry`, `MemoryStore`, and `MemoryIndex` are plain stdlib — no Pydantic, no async. `MemoryEntry` uses `@dataclass(frozen=True)`; `tags` is a `frozenset[str]`.
- `read()` raises on miss or expiry; use `get()` when you want a default. Tests rely on this asymmetry — don't paper over it with try/except.

## Don't

- Don't add cross-namespace reads to `MemoryStore`. Isolation is the point; use `MemoryIndex.search_all_namespaces()` if you need cross-namespace queries.
- Don't add a background eviction thread. The lazy pattern is deliberate — it keeps the store free of concurrency hazards inside the event loop.
- Don't use `MemoryStore` as a message queue. Inter-process data passing goes through `aos/ipc/message_bus.py`.
- Don't mutate `MemoryEntry` instances — they are frozen dataclasses. Write a new entry instead.

## Related

- `aos/kernel/process_manager.py` — calls `store.clear_namespace(pid)` when an agent process terminates
- `aos/ipc/message_bus.py` — the correct channel for inter-process data passing
- `aos/kernel/types.py` — `AgentProcess.pid` is the conventional namespace key
- `tests/aos/memory/` — covers store API + index search + expiry semantics
