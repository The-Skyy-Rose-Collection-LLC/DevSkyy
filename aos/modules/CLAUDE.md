# aos/modules/ — importlib-based dynamic module loader

Loads agent modules at runtime by dotted import path. Every module must declare two module-scope attributes (`AOS_MODULE_MANIFEST` and `AOS_MODULE_FACTORIES`) — missing or wrong-typed attributes raise `ModuleLoadError`. The registry tracks loaded manifests so unloading is safe and reversible.

## Key files

- `loader.py` — `load_from_path(module_path: str) → tuple[ModuleManifest, dict[str, AgentFactory]]`. Uses `importlib.import_module(module_path)` — relies on standard Python module resolution rather than file-path-based loading. Raises `ModuleLoadError(ImportError)` on import failure or when either expected module-scope attribute is missing / wrong-typed (manifest must be a `ModuleManifest`, factories must be a `dict`).
- `registry.py` — `ModuleRegistry`: in-memory, no I/O. `register_type(agent_type, factory)` for bare registrations; `load(manifest, factories)` raises `DuplicateModuleError` on name collision; `unload(manifest_name) → frozenset[str]` raises `ModuleNotFoundError` if absent; `get_factory(agent_type) → AgentFactory | None`; `is_loaded(manifest_name) → bool`. Properties `registered_types: frozenset[str]` and `manifests: tuple[ModuleManifest, ...]`.
- `types.py` — `ModuleManifest` `@dataclass(frozen=True)` with `name: str`, `version: str`, `agent_types: tuple[str, ...]`, `description: str = ""`, `module_path: str = ""`. `AgentFactory = Callable[[], Awaitable[Any]]` (the loaded factory must be async). Exceptions: `DuplicateModuleError(ValueError)`, `ModuleNotFoundError(KeyError)`.

## Conventions

- Modules must export two module-scope attributes: `AOS_MODULE_MANIFEST: ModuleManifest` (a frozen-dataclass instance, **not** a dict) and `AOS_MODULE_FACTORIES: dict[str, AgentFactory]`. These are the load-time contract checked by `load_from_path`.
- `ModuleLoadError` subclasses `ImportError` — callers catching `ImportError` will catch it. `DuplicateModuleError` subclasses `ValueError`; `ModuleNotFoundError` subclasses `KeyError`.
- `load_from_path` is synchronous (importlib is sync). Wrap it in `asyncio.to_thread` if called from inside the kernel event loop.
- `ModuleManifest` is a frozen dataclass — construct new instances; never mutate. Factories are async callables; the registry doesn't await them, it only stores and returns them.
- `registered_types` and `manifests` are read-only `@property` views. Don't mutate the underlying dicts directly.

## Don't

- Don't `import` agent module files directly in application code — always go through `load_from_path` so manifest / factory validation runs.
- Don't pass a `dict` for `AOS_MODULE_MANIFEST`. The loader does `isinstance(manifest, ModuleManifest)` and raises if it doesn't match.
- Don't swallow `ModuleLoadError` silently — missing or mistyped manifest attributes are developer errors, not runtime conditions.
- Don't call `register_type` and `load` for the same `agent_type` — the second write overwrites without raising. Use `load` only for manifest-tracked registrations.

## Related

- `aos/kernel/kernel.py` — resolves agent factories from `ModuleRegistry` at spawn time
- `aos/adapters/superagent_adapter.py` — wraps factories returned by `get_factory`
- `aos/CLAUDE.md` — parent kernel doc; lists `modules/` in the public surface table
- `tests/aos/modules/` — loader + registry coverage
