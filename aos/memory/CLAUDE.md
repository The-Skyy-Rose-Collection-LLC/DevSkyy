<claude-mem-context>

</claude-mem-context>

# aos/memory/ — namespaced TTL key/value store per agent PID

Each running agent process gets an isolated memory namespace keyed by its PID. Entries optionally expire; stale values are purged lazily on read, not by a background sweep.

## Key files

- `store.py` — `MemoryStore`: `write(pid, key, value, ttl=None)`, `read(pid, key) → value | None`, `delete(pid, key)`, `clear(pid)`. Lazy expiry: `read()` checks TTL before returning, discards expired entries silently.
- `index.py` — maintains a per-PID key index for efficient `clear()` without scanning all entries.
- `types.py` — `MemoryEntry` frozen Pydantic model: `value: Any`, `expires_at: float | None`.

## Conventions

- Namespace is always `pid` (string) — never share entries between PIDs.
- TTL is in seconds as a `float` (`ttl=300.0`), measured from write time. `None` = no expiry.
- Lazy expiry only — there is no background eviction thread. Expired entries remain in memory until read or `clear()` is called.
- `MemoryEntry` uses `model_config = {"frozen": True}`.

## Don't

- Don't add cross-PID reads — isolation is intentional and enforced by namespace.
- Don't add a background eviction thread — the lazy pattern is deliberate to avoid concurrency complexity in the event loop.
- Don't use `MemoryStore` as a message queue; use `aos/ipc/message_bus.py` for inter-process communication.

## Related

- `aos/kernel/process_manager.py` — calls `store.clear(pid)` on process termination
- `aos/ipc/message_bus.py` — the correct channel for inter-process data passing
- `aos/kernel/types.py` — `AgentProcess.pid` is the namespace key
