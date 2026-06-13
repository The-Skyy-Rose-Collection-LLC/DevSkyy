# agents/elite_web_builder/config/ — Elite Web Builder runtime configuration

Three JSON files that drive routing, quality enforcement, and learning across all Director story cycles. Modified at runtime by `core/learning_journal.py` and `core/model_router.py` — never hand-edit during an active build.

## Key files

- `provider_routing.json` — Maps each `AgentRole` to a preferred provider/model pair. Read at startup by `core/model_router.py` to populate `ProviderConfig` objects. Override a role's model here; do NOT patch `model_router.py` directly.
- `quality_gates.json` — Gate thresholds (score floor per `Gate` enum value) used by `core/verification_loop.py`. Lowering a threshold lets stories pass with weaker output — only do this in a documented experiment with a rollback plan.
- `learning_journal.json` — JSONL append-only win-rate log written by `core/learning_journal.py` after each story completion. Fields: `story_id`, `role`, `provider`, `model`, `gate_scores`, `passed`, `timestamp`. Do not truncate or reformat; the journal reader scans from the end.

## Conventions

- `provider_routing.json` and `quality_gates.json` are read once at Director boot (not hot-reloaded). Restart the Director after changing them.
- `learning_journal.json` is append-only — new lines only, never rewrite existing entries. The file may grow large; rotate by year if needed (`learning_journal_2025.json`, etc.).
- Gate threshold keys in `quality_gates.json` must match the `Gate(Enum)` values in `core/verification_loop.py` exactly. Mismatched keys are silently ignored.
- When adding a new `AgentRole`, add its routing entry to `provider_routing.json` in the same commit as the role definition in `agents/base.py`.

## Don't

- Don't lower a `quality_gates.json` threshold below `0.6` for any gate without explicit sign-off — this disables meaningful quality enforcement.
- Don't commit a truncated or reformatted `learning_journal.json` — the journal reader assumes append-only JSONL ordering.
- Don't add computed or ephemeral keys to `provider_routing.json` — it is config, not state.

## Related

- `agents/elite_web_builder/core/model_router.py` — reads `provider_routing.json` at init
- `agents/elite_web_builder/core/verification_loop.py` — reads `quality_gates.json` for gate thresholds
- `agents/elite_web_builder/core/learning_journal.py` — appends to `learning_journal.json` after each story
- `agents/elite_web_builder/agents/base.py` — `AgentRole` enum whose values must match routing keys
