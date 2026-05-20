# agents/elite_web_builder/tools/ — Specialist agent tools (8 modules)

Concrete tool implementations the specialist agents and `VerificationLoop` consume. Not generic utilities — each tool exists to support a specific specialist or gate check.

## Inventory

| File | Used by | Role |
|------|---------|------|
| `context7_bridge.py` | All specialists | Wrapper over Context7 MCP for live library docs (lib resolve + query) |
| `contrast_checker.py` | accessibility | WCAG 2.2 AA contrast ratio validation (text + non-text targets) |
| `file_validator.py` | qa, output_writer | Validates generated files (PHP syntax, CSS valid, no XSS sinks) |
| `lighthouse_runner.py` | performance gate | Lighthouse CI invocation + result parsing → `VerificationLoop` PERF gate |
| `screenshot_diff.py` | qa gate | Image diff + perceptual-threshold comparison → `VerificationLoop` DIFF gate |
| `spacing_scale.py` | design_system, frontend_dev | Validates spacing values against design tokens (4/8/16/24/32/...) |
| `template_scaffold.py` | theme_builder, backend_dev | Bootstraps WordPress block-theme + PHP template skeletons |
| `type_scale.py` | design_system, frontend_dev | Typography scale validator (modular scale 1.125/1.25/1.333) |

## context7_bridge.py — Library docs lookup

```python
from agents.elite_web_builder.tools.context7_bridge import resolve_library_id, query_docs

# Resolve library name → Context7 lib ID
lib_id = resolve_library_id("anthropic")

# Pull current docs for a topic
docs = query_docs(lib_id, "tool use")
```

**Mandatory before any Context7-MCP-aware specialist makes external library calls.** The project's Context7-First protocol applies — agents should resolve + query before generating library-specific code.

## Gate-specific tools

The PERF and DIFF gates in `VerificationLoop` invoke these tools directly:

- **PERF gate** → `lighthouse_runner.run(url)` → parses to `LighthouseResult(perf, a11y, best_practices, seo, pwa)` → fails gate if perf < threshold (default 90)
- **DIFF gate** → `screenshot_diff.compare(baseline_path, current_path, threshold=0.1)` → returns `DiffResult(pixel_delta, percent_delta)` → fails gate above threshold
- **A11Y gate** → `contrast_checker.check_page(url)` — supplements axe-core results with explicit WCAG ratio math

## Conventions

- **Tools are pure functions or thin classes.** No state across invocations. Each call self-contained.
- **Async where the work allows it.** `context7_bridge`, `lighthouse_runner` are async; sync tools (`spacing_scale`, `type_scale`) stay sync for simplicity.
- **Pydantic for result types.** Tool outputs are `BaseModel` subclasses so they serialize cleanly into the learning journal.
- **No HTTP client in tools.** When a tool needs to call an external service, it goes through `core/provider_adapters.py` (for LLMs) or imports the dedicated wrapper module.
- **Errors are typed.** Tool-specific exceptions inherit from a `ToolError` base — `VerificationLoop` distinguishes tool failures from gate failures.

## Don't

- Don't put domain logic in tools. Design-token enforcement (`spacing_scale`, `type_scale`) is OK; SEO content generation is not.
- Don't write to disk from tools — except `template_scaffold.py` which is explicitly scaffolding to `output/`. Output paths go through `core/output_writer.py`.
- Don't add LLM calls to tools. Tools are deterministic; LLM calls happen in specialist agents via `provider_adapters.py`.
- Don't bypass `lighthouse_runner.py` to call Lighthouse directly from a specialist agent — perf checks must go through the verification loop so cost + result are tracked.

## Related

- Consumers (specialists): `agents/elite_web_builder/agents/<role>.py`
- Consumers (gates): `agents/elite_web_builder/core/gate_checkers.py`
- Output destination: `agents/elite_web_builder/output/` (gitignored)
- Context7 MCP server: provided by `claude.ai Context7` MCP registration
- Lighthouse CI: requires `lighthouse` npm package in PATH (or `npx lighthouse`)
