<claude-mem-context>

</claude-mem-context>

# aos/shell/ — interactive REPL and command dispatch

Provides a text-driven interface for inspecting and controlling a running `Kernel` instance. The REPL loop is pure I/O glue; all business logic lives in `commands.py`.

## Key files

- `repl.py` — `AosShell`: `run()` starts the interactive readline loop (blocks until `exit`/`quit`); `feed(line: str)` dispatches a single command string for scripted use or tests. No command logic here — delegates everything to `commands.py`.
- `commands.py` — all command implementations: `spawn`, `list`, `kill`, `pause`, `resume`, `status`, `memory`, `help`. Each command is an `async def` that receives a parsed args list and the live `Kernel` reference.

## Conventions

- `AosShell.feed()` is the test-safe entry point — use it in unit tests instead of `run()`.
- All command functions are `async` — they await kernel methods directly.
- `repl.py` owns only I/O (readline, print, prompt string); logic stays in `commands.py`.
- Unknown commands print a help hint and return without raising.

## Don't

- Don't add command logic to `repl.py` — keep the split: REPL = I/O, commands = logic.
- Don't import from `agents/` in the shell layer — commands interact with the kernel API only.
- Don't make `AosShell` hold a reference to subsystems other than `Kernel`; all kernel access goes through `Kernel`'s public methods.

## Related

- `aos/kernel/kernel.py` — `Kernel` instance passed to `AosShell` at construction
- `aos/kernel/types.py` — `AgentProcess` is the primary data type printed by `list` and `status` commands
- `main_enterprise.py` — optionally starts `AosShell.run()` in a background task for debug access
