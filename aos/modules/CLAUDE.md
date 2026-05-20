<claude-mem-context>

</claude-mem-context>

# aos/modules/ — importlib-based dynamic module loader

Loads agent modules at runtime from filesystem paths without modifying `sys.path`. Modules must declare two module-scope attributes to be recognized; missing either raises `ModuleLoadError`.

## Key files

- `loader.py` — `load_from_path(module_path: str) → ModuleHandle`: uses `importlib.util.spec_from_file_location` + `module_from_spec` to import without polluting `sys.path`. Expects `AOS_MODULE_MANIFEST` (metadata dict) and `AOS_MODULE_FACTORIES` (dict of name → callable) at module scope; raises `ModuleLoadError(ImportError)` if either is absent.
- `registry.py` — `ModuleRegistry`: tracks loaded modules by name, prevents double-loading, exposes `get_factory(name) → callable`.
- `types.py` — `ModuleHandle` frozen Pydantic model: `name: str`, `path: str`, `manifest: dict`, `factories: dict`.

## Conventions

- Modules must export `AOS_MODULE_MANIFEST: dict` and `AOS_MODULE_FACTORIES: dict[str, Callable]` at module scope — these are the load-time contract.
- `ModuleLoadError` subclasses `ImportError` — callers catching `ImportError` will catch it.
- `load_from_path` is synchronous (importlib is sync); wrap in `asyncio.to_thread` if called from the kernel event loop.
- `ModuleHandle` uses `model_config = {"frozen": True}`.

## Don't

- Don't `import` module files directly in application code — always go through `load_from_path`.
- Don't modify `sys.path` or `sys.modules` inside module files; the loader's isolation depends on the spec approach.
- Don't swallow `ModuleLoadError` silently — missing a manifest attribute is a developer error, not a runtime condition.

## Related

- `aos/kernel/kernel.py` — calls `ModuleRegistry` to resolve agent factories at spawn time
- `aos/adapters/superagent_adapter.py` — wraps factories returned by the registry
