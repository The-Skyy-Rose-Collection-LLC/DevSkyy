# core/feature_flags/ — Runtime Feature Flags

**In-process flag manager.** Toggle features without redeploy. Backed by `flag_manager.py`.

## Public Surface (`core/feature_flags/__init__.py`)

- `FeatureFlag` — flag dataclass
- `FlagManager` — class with `create_flag`, `set_flag`, `get_flag`, `get_all_flags` + 8 more methods
- `flag_manager` — **global singleton instance**

## Hard Rules

- **Singleton state survives the process** — tests MUST reset flags between cases
- Flag names: lowercase snake_case (`"enable_3d_preview"`, `"use_round_table_llm"`)
- Default to **off** — explicit opt-in on every flag. Never default new flags to True in production
- Flag reads are sync (in-memory dict). Do not block on I/O inside `get_flag()`
- This is a **local** flag store. Cross-instance flag sync requires LaunchDarkly / Unleash / GrowthBook (not provided here)

## Patterns

```python
from core.feature_flags import flag_manager

flag_manager.create_flag("enable_3d_preview", default=False)
if flag_manager.get_flag("enable_3d_preview"):
    render_3d()
else:
    render_2d()
```

## Consumers

- `api/v1/*` — gate experimental endpoints
- `frontend/` — dashboard exposes flag toggle UI (admin only)
- `agents/*` — A/B test new agent variants behind flags
