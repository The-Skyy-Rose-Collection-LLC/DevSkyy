---
name: strategic-compact
description: Manual context compaction at logical workflow boundaries.
---

# Strategic Compact

Use `/compact` at logical boundaries, not arbitrary auto-compaction points.

## When to Compact

- **After exploration, before execution** - Clear research, keep plan
- **After completing a milestone** - Fresh start for next phase
- **Before major context shifts** - Different task domain

## Hook Setup

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "tool == \"Edit\" || tool == \"Write\"",
      "hooks": [{"type": "command", "command": "~/.claude/skills/strategic-compact/suggest-compact.sh"}]
    }]
  }
}
```

## Best Practices

1. Compact after planning is finalized
2. Compact after debugging sessions
3. Don't compact mid-implementation
4. Environment: `COMPACT_THRESHOLD=50` (tool calls before suggestion)

## Related Tools

- **Command**: `/compact` to trigger manual compaction
- **Skill**: `verification-loop` before compacting
- **Agent**: `planner` for implementation plans (before compact)
