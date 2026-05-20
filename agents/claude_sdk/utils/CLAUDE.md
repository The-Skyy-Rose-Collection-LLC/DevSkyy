# agents/claude_sdk/utils/ — SDK telemetry + Excel helpers

Internal utilities for the Claude SDK integration. Two concerns: subagent invocation tracking (telemetry) and Excel formula recalculation (used by `ExcelHandlerAgent`).

## Inventory

| File | Purpose | Used by |
|------|---------|---------|
| `tracker.py` | `DevSkyySubagentTracker` — records every SDK subagent invocation + tool call to JSONL for telemetry | `ClaudeSDKBaseAgent` (via `_tracker` field) |
| `recalc.py` | LibreOffice-backed Excel formula recalculation (`subprocess` call to `soffice --headless`) | `ExcelHandlerAgent` |

## `tracker.py` — subagent telemetry

```python
@dataclass
class ToolCallRecord:
    timestamp: str
    tool_name: str
    tool_input: dict[str, Any]
    tool_use_id: str
    subagent_type: str
    parent_tool_use_id: str | None = None
    tool_output: Any | None = None
    error: str | None = None

@dataclass
class SubagentSession:
    subagent_type: str
    parent_tool_use_id: str
    spawned_at: str
    description: str
    prompt_preview: str
    subagent_id: str
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
```

- Adapted from `research-agent/utils/subagent_tracker.py` upstream.
- Writes JSONL telemetry — one record per tool call. Downstream log aggregation can consume directly.
- Integrates with `structlog` (the SDK layer's structured logging convention).
- `HookMetrics` in `agents/claude_sdk/hooks.py` pulls aggregated stats from the tracker.

## `recalc.py` — LibreOffice formula recalc

- **macOS path:** `~/Library/Application Support/LibreOffice/4/user/basic/Standard`
- **Linux path:** `~/.config/libreoffice/4/user/basic/Standard`
- **Mechanism:** Installs a `Module1.xba` macro (`RecalculateAndSave`) on first run, then invokes `soffice --headless` to apply it.
- **openpyxl** for post-recalc workbook inspection.
- **Required for:** any Excel file with formulas that need server-side recalculation before downstream processing (e.g. `ExcelHandlerAgent` ingesting customer-supplied spreadsheets).

### Dependency: LibreOffice must be installed

- `brew install --cask libreoffice` on macOS
- `apt install libreoffice` on Linux
- **`soffice` must be on PATH.** If missing → `subprocess.run` raises and the agent surfaces a clear setup error.

## Conventions

- **`structlog` only** — `logger = structlog.get_logger(__name__)`. Matches the SDK layer's logging convention. Do not use stdlib `logging`.
- **`@dataclass(frozen=False)` for mutable records, `frozen=True` for value objects.** `ToolCallRecord` is frozen (immutable event); `SubagentSession` mutates as tool calls accrue.
- **Path objects, not strings.** All file paths are `pathlib.Path` — `os.path` is for legacy interop only.
- **No prints to stdout.** Tracker writes to JSONL files; the agent layer reads them. Mixing stdout output corrupts the SDK message pipeline.

## Don't

- Don't write tracker data to arbitrary paths. Default goes under `SDKAgentConfig.output_dir / "telemetry"`. Override via config, not by hardcoding.
- Don't run `recalc.py` in a hot path. LibreOffice startup is ~3-5s per invocation; batch Excel work, recalc once.
- Don't swallow `subprocess` errors in `recalc.py`. If LibreOffice fails, surface the exit code + stderr so the operator can diagnose.
- Don't add a third utility here without justifying it can't live in the agent that needs it. This dir is for cross-SDK-agent shared helpers, not domain logic.

## Related

- Telemetry consumer: `agents/claude_sdk/hooks.py` `HookMetrics`
- Telemetry producer integration point: `agents/claude_sdk/base.py` `ClaudeSDKBaseAgent._tracker`
- Excel consumer: `agents/claude_sdk/excel_handler.py` `ExcelHandlerAgent`
- Upstream reference: research-agent's `subagent_tracker.py`
- LibreOffice install docs: https://www.libreoffice.org/download/
