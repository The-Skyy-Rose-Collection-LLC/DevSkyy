# /learn - Extract Reusable Patterns

Analyze current session and save patterns as skills.

## What to Extract
- **Error Resolution**: Root cause and fix
- **Debugging Techniques**: Non-obvious steps
- **Workarounds**: Library quirks, API limitations
- **Project Patterns**: Conventions discovered

## Output Format
Save to `~/.claude/skills/learned/[pattern-name].md`:
```markdown
# [Pattern Name]
**Context:** [When this applies]
## Problem
[What it solves]
## Solution
[The technique]
## When to Use
[Trigger conditions]
```

## Rules
- Don't extract trivial fixes
- Don't extract one-time issues
- Focus on reusable patterns
- One pattern per skill
