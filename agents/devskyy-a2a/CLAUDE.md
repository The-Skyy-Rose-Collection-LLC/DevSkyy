<claude-mem-context>

</claude-mem-context>

# agents/devskyy-a2a/ — Agent-to-Agent (A2A) framework placeholder

Stub directory for the planned A2A communication framework. No implementation exists yet — only the directory structure has been created.

## Key files

- `agents/` — empty; will hold A2A participant agent definitions
- `tests/unit/` — empty; will hold unit tests
- `tests/integration/` — empty; will hold integration tests

## Conventions

- When implementing: A2A agents should follow the same `AgentSpec` pattern used in `agents/elite_web_builder/agents/` — single `*_SPEC` constant per file, no class instantiation.
- Communication protocol TBD — align with `agents/core/base.py` `SuperAgent` message bus before writing the first participant.

## Don't

- Don't add implementation files here until the A2A protocol is designed and documented in `.planning/`.
- Don't copy the `elite_web_builder` Director pattern directly — A2A has different coordination semantics.

## Related

- `agents/core/base.py` — `SuperAgent` base class that A2A participants will extend
- `agents/elite_web_builder/agents/base.py` — reference pattern for `AgentSpec` definitions
- `.planning/ROADMAP.md` — tracks when A2A work is scheduled
