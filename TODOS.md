# TODOS

Deferred work items with full context. Each entry should be actionable by someone picking it up in 3 months.

---

## 1. Fix all hooks.json paths to use dynamic resolution

**What:** Replace hardcoded `/Users/coreyfoster/DevSkyy/` paths in `.claude/hooks/hooks.json` with portable `git rev-parse --show-toplevel` wrappers.

**Why:** hooks.json is a committed file shared between two machines (`/Users/coreyfoster/` and `/Users/theceo/`). The 4 existing external script references use `/Users/coreyfoster/` which only works on one machine. The new CLAUDE.md tracker hooks already use `git rev-parse` (added March 2026), creating an inconsistency — some hooks are portable, some aren't.

**Context:** The affected entries reference:
- `/Users/coreyfoster/DevSkyy/.claude/hooks/strategic-compact/suggest-compact.sh` (PreToolUse)
- `/Users/coreyfoster/DevSkyy/.claude/hooks/memory-persistence/pre-compact.sh` (PreCompact)
- `/Users/coreyfoster/DevSkyy/.claude/hooks/memory-persistence/session-start.sh` (SessionStart)

The fix is mechanical: wrap each in `bash "$(git rev-parse --show-toplevel)/.claude/hooks/..."`. The new CLAUDE.md tracker hooks demonstrate the pattern. Both machines have `git` available.

**Depends on / blocked by:** Nothing. Can be done independently.

---

## 2. Add Serena MCP change tracking for WordPress files

**What:** Implement a mechanism to detect structural changes made to WordPress theme files via Serena MCP tools, since Serena calls bypass the Claude Code hook system entirely.

**Why:** The CLAUDE.md staleness tracker (added March 2026) only fires on Write/Edit/Bash tool calls. Serena MCP tools (`replace_content`, `create_text_file`, `replace_symbol_body`, etc.) modify WordPress files directly without triggering PostToolUse hooks. This means structural changes to `wordpress-theme/skyyrose-flagship/` go untracked — a blind spot given that the WordPress theme has 14+ page templates, 31 CSS files, and 24 JS files.

**Context:** Possible approaches:
1. **Serena memory hook** — Use Serena's `write_memory` to log structural changes, then read them in session-summary.sh.
2. **Git diff at session end** — Instead of tracking changes live, `session-summary.sh` could run `git diff --name-status` at session end to catch ALL changes (including Serena). This is simpler but loses the mid-session alerting.
3. **Post-Serena poll** — A hook that runs after any Serena tool call and checks `git status` for new/deleted files. Requires Serena to be registered as a tool in the hook matcher.

The git-diff-at-session-end approach (option 2) is likely the best balance of simplicity and coverage. It could be added to `session-summary.sh` as a fallback detection path.

**Depends on / blocked by:** CLAUDE.md staleness tracker must be stable first (the March 2026 implementation).
