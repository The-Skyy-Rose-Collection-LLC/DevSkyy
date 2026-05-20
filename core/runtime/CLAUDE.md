# core/runtime/ — Tool registry, input validation, sandboxed execution

The consolidated tool execution surface every SuperAgent depends on. Houses the canonical `ToolRegistry`, the input sanitizer that runs before every tool dispatch, and the Anthropic-managed code-execution sandbox spec. Three real modules plus an `__init__.py` re-export shim.

## Key files

- `tool_registry.py` — `ToolRegistry` (register / lookup / execute), `ToolSpec` (Pydantic spec with parameters + severity), `ToolCallContext` (dataclass carrying permissions + correlation ID for tracing), `ToolParameter` + `ParameterType` enum, `ExecutionStatus` enum, `ToolExecutionResult`, `ToolCategory` + `ToolSeverity` enums, `ToolDefinition`, `BUILTIN_TOOLS` list, `get_tool_registry()` process-wide factory.
- `input_validator.py` — `ToolInputValidator` and `ToolInputValidationError`. Enforces hard caps: 10K-char strings, 1K-element arrays, 10-level nesting. Blocks XSS and SQLi patterns before the registry sees the call.
- `code_execution_tool.py` — `CODE_EXECUTION_TOOL` — a `ToolSpec` wrapping Anthropic's managed Python sandbox (5 GiB RAM, 4.5 min timeout). Imported by agents that need eval-style execution; do not extend its limits.
- `__init__.py` — Re-exports 12 symbols. Anything imported from `core.runtime` lives here.

## Conventions

- Instantiate via `get_tool_registry()` — never construct `ToolRegistry()` directly. The factory enforces singleton semantics across the process.
- Every tool call must pass through `ToolInputValidator` before `ToolRegistry.execute()`. Agents do `validator.validate(payload, spec) → registry.execute(name, payload, ctx)`.
- Set `ToolSeverity` accurately on every `ToolSpec`. Downstream callers (12 agent files including `agents/enhanced_base.py`, `agents/analytics_agent.py`, `agents/commerce_agent.py`) gate execution on severity.
- Raise `ToolExecutionError` from `core.errors` on failure — never a bare `Exception`. The error carries the correlation ID from `ToolCallContext`.
- New tools added by importing into `BUILTIN_TOOLS` at module import time. Runtime mutation is forbidden.

## Don't

- Don't bypass `ToolInputValidator` because the input "looks safe". The validator is the only thing standing between user-shaped payloads and the sandbox.
- Don't mutate `BUILTIN_TOOLS` at runtime — its contents are part of the import-time contract.
- Don't pass user-supplied strings into `ToolCallContext.permissions`. Permissions come from the auth layer, not the request body.
- Don't widen `CODE_EXECUTION_TOOL` limits (RAM, timeout) — they match Anthropic's managed sandbox; mismatched limits silently truncate runs.

## Related

- `core/CLAUDE.md` — parent foundation layer
- `core/errors/CLAUDE.md` — `ToolExecutionError`, severity-to-error mapping
- `agents/enhanced_base.py` — primary consumer; 12 agent files import from here
- `BUILTIN_TOOLS` consumers: `agents/analytics_agent.py`, `agents/commerce_agent.py`, `agents/creative_agent.py`, `agents/marketing_agent.py`, `agents/operations_agent.py`
