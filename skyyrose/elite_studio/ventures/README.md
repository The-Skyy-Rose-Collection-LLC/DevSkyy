# Elite Studio Ventures

> Productized verticals inside the Elite Studio creative platform.

Per project canon, every creative pipeline (imagery, photography, 3D,
video, social, marketing, try-on, …) must run through Elite Studio so
the studio remains the single operator-facing surface. Each vertical is
a **venture** — a dedicated pipeline surface composing existing agents
and orchestration engines.

## Venture Roster

| Slug      | Title              | Status   | Location                            |
| --------- | ------------------ | -------- | ----------------------------------- |
| `imagery` | Product Imagery    | stable   | `skyyrose/elite_studio/` (top-level — original) |
| `photo`   | Editorial Photography | beta  | `skyyrose/elite_studio/ventures/photo/` |
| `threed`  | 3D / Immersive     | beta     | `skyyrose/elite_studio/ventures/threed/` |
| `video`   | Video & Animation  | alpha    | `skyyrose/elite_studio/ventures/video/` |

The Imagery venture is the original Elite Studio pipeline. It is *not*
duplicated under `ventures/imagery/` to avoid abstraction collision —
its manifest is registered from the registry's `IMAGERY_MANIFEST`
constant so the venture roster stays complete.

## Per-Venture Layout

Each venture package contains:

```
ventures/<slug>/
├── __init__.py     # MANIFEST + Pipeline export
├── __main__.py     # `python -m skyyrose.elite_studio.ventures.<slug>`
├── config.py       # Frozen VentureConfig dataclass
├── state.py        # TypedDict pipeline state
├── pipeline.py     # build_pipeline() — compiled LangGraph
├── agents.py       # Verified AgentBinding registry
├── cli.py          # `info`, `status`, `agents`, `smoke`
├── README.md       # Venture overview + roadmap
└── tests/
    └── test_smoke.py
```

## Registry API

```python
from skyyrose.elite_studio import ventures

ventures.list_ventures()       # ('imagery', 'photo', 'threed', 'video')
ventures.get_manifest('photo') # VentureManifest(...)
ventures.all_manifests()       # (VentureManifest, ...)
```

## Agent Wiring Status

This scaffold ships the venture **surfaces** (configs, registries,
compilable pipelines, CLIs, tests). Deep wiring of existing agents into
each venture's LangGraph nodes is deferred per the session scope; each
`AgentBinding.ready` flag tracks whether the agent is wired into the
venture's pipeline yet. Bindings are real imports verified at scaffold
time — not stubs.

## Adding a New Venture

1. Create `ventures/<slug>/` matching the layout above.
2. Export `MANIFEST: VentureManifest` and a `Pipeline` class.
3. Add a `_<slug>_manifest()` loader in `ventures/__init__.py` and
   register it in `_VENTURE_LOADERS`.
4. Update this table.
5. Add a `tests/test_smoke.py` that imports the package, builds the
   pipeline, runs the smoke pass, and asserts every `AgentBinding`
   resolves via `importlib`.
