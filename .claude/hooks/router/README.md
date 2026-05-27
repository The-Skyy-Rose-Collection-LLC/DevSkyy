# DevSkyy Task Router

Project-scoped `UserPromptSubmit` hook. Pattern-matches user prompts against
trigger map → emits `additionalContext` recommending which skills/agents/
plugins are relevant for the task domain.

## Why

Default Claude Code session injects all installed skills (~30K tokens) every
prompt. Most are irrelevant to any given task. Router biases selection toward
the right subset, reducing skill-list noise and cache thrash.

**Nudge only** — does not enforce. Claude can still invoke off-pack tools.

## Files

```
.claude/hooks/router/
├── router.py              # UserPromptSubmit handler (executable)
├── triggers.json          # pattern → resource pack map
├── README.md              # this file
└── helpers/
    ├── enable-pack.sh     # flip global plugin enabled state
    └── backup-settings.sh # timestamped settings.json backup
```

## Wiring

Add to `.claude/settings.json` under `hooks.UserPromptSubmit`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 /Users/theceo/DevSkyy/.claude/hooks/router/router.py",
            "timeout": 3
          }
        ]
      }
    ]
  }
}
```

Hook contract: reads JSON from stdin, writes JSON `additionalContext` to stdout, exits 0.

## Trigger Patterns

10 patterns, first-match-wins, case-insensitive. Edit `triggers.json` to adjust.

| # | Pattern | Domain |
|---|---------|--------|
| 1 | `wordpress\|wp-theme\|woocommerce\|...` | WordPress / WC / PHP |
| 2 | `next.js\|react\|tsx\|vercel\|...` | Frontend |
| 3 | `fastapi\|pytest\|pydantic\|...` | Python backend |
| 4 | `image\|nano-banana\|fashn\|flux\|...` | Imagery |
| 5 | `catalog\|sku\|dossier\|...` | Catalog / SKU |
| 6 | `deploy\|ship\|production\|...` | Deploy |
| 7 | `bug\|fix\|debug\|error\|...` | Debug |
| 8 | `docs\|readme\|...` | Documentation |
| 9 | `audit\|review\|p0\|...` | Audit / review |
| 10 | `.*` | Default catch-all |

## Plugin Disable Strategy

This router pairs with hard-disabling unused global plugins:

- `gopls-lsp@claude-plugins-official` → disabled (no Go in stack)
- `watch@claude-video` → disabled (niche video use)

Kept enabled (soft-suppress via router context):
- `caveman@caveman`
- `claude-mem@thedotmack`
- `superpowers@claude-plugins-official`
- `serena@claude-plugins-official`
- `skill-creator@claude-plugins-official`
- `banana-claude@banana-claude-marketplace`
- `cli-anything@HKUDS`

## Rollback

```bash
# Restore most-recent global settings backup
.claude/hooks/router/helpers/enable-pack.sh --restore-backup

# Or remove the UserPromptSubmit hook entry manually
$EDITOR .claude/settings.json
```

## Testing

```bash
# Dry run with a sample prompt
echo '{"prompt": "fix the wordpress theme deploy"}' | \
    python3 .claude/hooks/router/router.py
```

Expected output (JSON): `additionalContext` with `wordpress` pack listed.

## Extending

Add a new pattern to `triggers.json`:

```json
{
  "name": "my-domain",
  "regex": "\\b(keyword1|keyword2)\\b",
  "skills": ["skill-name-1"],
  "agents": ["Agent Name"],
  "plugins": ["plugin@source"]
}
```

Insert before the `default` entry. First-match-wins.

## Known Limitations

1. **Hooks cannot dynamically load plugins.** `enabledPlugins` is read at session
   start. Router can suggest "enable plugin X" but you must run `enable-pack.sh`
   and restart Claude Code to apply.
2. **Skill-list injection is core Claude Code behavior.** Router reduces
   *recommended* set but the full skill list still gets injected on session start.
3. **Pattern matching is regex-only.** Doesn't understand intent. A prompt
   like "I want to delete the wordpress theme" matches pattern 1 even though
   the task is destructive.
