# agents/claude_sdk/prompts/ — Reusable SDK agent system prompts

Plain `.txt` files holding system prompts for `SDKSubAgent` subclasses. Loaded at agent init via `pathlib.Path.read_text()` rather than hardcoded in Python source — keeps prompts diff-friendly and editable without code changes.

## Inventory

| File | Used by | Role |
|------|---------|------|
| `research_lead.txt` | `ResearchAgent` (lead) | Orchestrates multi-step research with subagent delegation |
| `researcher.txt` | `ResearchAgent` (subagent worker) | Single-topic deep dive, returns structured findings |
| `data_analyst.txt` | analytics SDK agents, `build_analyst_agent` | Statistical analysis + chart-spec output |
| `report_writer.txt` | report-drafting agents | Synthesizes findings into executive-summary format |
| `email_triage.txt` | `EmailAutomationAgent` | 4-tier classification (skip / info_only / meeting_info / action_required) + draft replies |

## Loading pattern

```python
from pathlib import Path

PROMPT_DIR = Path(__file__).parent / "prompts"
PROMPT_PATH = PROMPT_DIR / "research_lead.txt"

class ResearchAgent(ClaudeSDKBaseAgent):
    def _build_system_prompt(self) -> str:
        return PROMPT_PATH.read_text()
```

## Conventions

- **`.txt` only — no `.md`, no `.j2`.** Keep prompts as plain text. Template substitution happens in Python (`str.format`, f-strings), not via Jinja.
- **One prompt per file.** Don't bundle multiple prompts into one file. If you need variants, create `researcher_v2.txt`, etc.
- **Filenames snake_case** to match the agent or role they serve.
- **No secrets in prompts.** Templating placeholders for inputs is fine; literal API keys / tokens never.
- **Brand voice consistency** — any prompt producing user-facing SkyyRose copy must reference brand canon. Founder voice register: "Imagery hasn't earned it." — terse, garment-as-protagonist, no urgency timers.
- **Match the agent's purpose.** `research_lead.txt` is for orchestration; `researcher.txt` is for execution. Don't conflate.

## Don't

- Don't edit a prompt without re-running the agent's eval set. Prompt changes cascade silently into agent behavior.
- Don't hardcode the prompt in the Python class when a `.txt` version exists. The `.txt` is the source of truth.
- Don't load prompts at module import time. Use lazy loading inside `_build_system_prompt()` so the file is only read when the agent runs.
- Don't paste prompts from external blog posts without adapting to SkyyRose brand canon — generic ChatGPT-style prompts produce generic output.

## Related

- Agents that load these: `agents/claude_sdk/research.py`, `email_automation.py`, `agents/claude_sdk/domain_agents/*.py`
- Brand canon: `knowledge-base/seed/from-interview.md`, project memory `project_founder_voice.md`
- Tool profiles that ship with default system prompts: `tool_bridge.build_*` factories in `agents/claude_sdk/tool_bridge.py`
