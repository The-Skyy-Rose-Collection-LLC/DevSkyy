# Claude Agent SDK Integration Plan

## Goal
Integrate 4 patterns from `claude-agent-sdk-demos` into DevSkyy's agent system:
1. **V2 Session API** (hello-world-v2) — session management utility
2. **Research Multi-Agent** (research-agent) — lead + researcher + data-analyst + report-writer
3. **Email Automation** (email-agent) — IMAP email processing with AI triage
4. **Excel Handler** (excel-demo) — spreadsheet generation/analysis with openpyxl

## Source Locations
- Cloned to: `/Users/theceo/claude-agent-sdk-demos/`
- Research agent core: `research-agent/research_agent/agent.py` (Python, `ClaudeSDKClient`)
- Research prompts: `research-agent/research_agent/prompts/{lead_agent,researcher,data_analyst,report_writer}.txt`
- Research tracker: `research-agent/research_agent/utils/subagent_tracker.py`
- Email agent: `email-agent/server/server.ts` (Bun/TS — port to Python)
- Email CCSDK: `email-agent/ccsdk/websocket-handler.ts` (WebSocket + Claude Code SDK)
- Excel skill: `excel-demo/agent/.claude/skills/xlsx/SKILL.md` + `recalc.py`
- V2 API: `hello-world-v2/v2-examples.ts` (TS — port session patterns to Python)

## SDK Dependencies
```
claude-agent-sdk  # Python SDK — NOT yet in requirements.txt
openpyxl          # For excel handler (may already be installed)
imaplib           # stdlib — for email
```

## Architecture

### File Structure
```
agents/claude_sdk/
├── __init__.py              # Package exports
├── base.py                  # SDK client wrapper adapted for DevSkyy
├── research.py              # Multi-agent research (from research-agent demo)
├── email_automation.py      # Email triage/automation (ported from email-agent)
├── excel_handler.py         # Spreadsheet ops (from excel-demo patterns)
├── session.py               # V2 session management utility
└── prompts/
    ├── research_lead.txt    # Copy from demos, adapt for SkyyRose context
    ├── researcher.txt
    ├── data_analyst.txt
    ├── report_writer.txt
    └── email_triage.txt
```

### API Router
```
api/v1/claude_sdk.py         # FastAPI router with endpoints:
  POST /claude-sdk/research   — Trigger research pipeline
  POST /claude-sdk/email      — Process/triage email
  POST /claude-sdk/excel      — Generate/analyze spreadsheet
  POST /claude-sdk/session    — Create/resume V2 session
```

### MCP Tool Registration
Add to `devskyy_mcp.py`:
- `devskyy_research_topic` — Research any topic, get PDF report
- `devskyy_email_triage` — AI email triage and response drafting
- `devskyy_generate_spreadsheet` — Create Excel from natural language
- `devskyy_analyze_spreadsheet` — Analyze existing Excel data

## Key SDK Patterns to Port

### 1. Research Agent (Python → Python, cleanest port)
```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AgentDefinition, HookMatcher

agents = {
    "researcher": AgentDefinition(
        description="...", tools=["WebSearch", "Write"],
        prompt=researcher_prompt, model="haiku"
    ),
    "data-analyst": AgentDefinition(
        description="...", tools=["Glob", "Read", "Bash", "Write"],
        prompt=data_analyst_prompt, model="haiku"
    ),
    "report-writer": AgentDefinition(
        description="...", tools=["Skill", "Write", "Glob", "Read", "Bash"],
        prompt=report_writer_prompt, model="haiku"
    )
}

options = ClaudeAgentOptions(
    permission_mode="bypassPermissions",
    system_prompt=lead_agent_prompt,
    allowed_tools=["Task"],
    agents=agents,
    hooks=hooks,
    model="haiku"
)
```
- Wrap in `EnhancedSuperAgent` subclass
- Add DevSkyy structured logging via `SubagentTracker` pattern
- Output to `data/research/{topic}/` instead of `files/`

### 2. V2 Session API (TypeScript → Python)
```python
# Port these three core functions:
# unstable_v2_createSession → create_session()
# unstable_v2_resumeSession → resume_session()
# unstable_v2_prompt → one_shot_prompt()
```
- Useful for stateful agent conversations in the API
- Session resume enables multi-request workflows

### 3. Email Automation (TypeScript/Bun → Python)
- Use stdlib `imaplib` + `email` for IMAP (no Bun dependency)
- Port the CCSDK WebSocket handler pattern to FastAPI WebSocket
- AI triage: classify emails, draft responses, extract action items
- Store in DevSkyy's existing database via `db_manager`

### 4. Excel Handler (Python skill → DevSkyy agent)
- Copy `recalc.py` to `agents/claude_sdk/utils/recalc.py`
- Port SKILL.md patterns into agent system prompt
- Use openpyxl for creation, pandas for analysis
- Output to `data/spreadsheets/`

## Integration Points with Existing DevSkyy

| Demo Pattern | DevSkyy Integration |
|-------------|-------------------|
| `ClaudeSDKClient` | Wrap in `EnhancedSuperAgent` subclass |
| `SubagentTracker` hooks | Feed into DevSkyy `structlog` + `core/telemetry` |
| Research output (PDF) | Store in `data/research/`, serve via assets API |
| Email IMAP | Use env vars `EMAIL_USER`, `EMAIL_PASSWORD`, `IMAP_HOST` |
| Excel output | Store in `data/spreadsheets/`, serve via assets API |
| `AgentDefinition` subagents | Register as DevSkyy sub-agents under coordinator |

## Execution Order
1. Add `claude-agent-sdk` to `requirements.txt`
2. Create `agents/claude_sdk/` package with all files
3. Copy + adapt prompts from demos
4. Create `api/v1/claude_sdk.py` router
5. Wire router in `main_enterprise.py`
6. Register MCP tools
7. Test each agent independently
