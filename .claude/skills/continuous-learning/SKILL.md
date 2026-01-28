---
name: continuous-learning
description: Extract reusable patterns from sessions and save as skills.
---

# Continuous Learning Skill

Runs as **Stop hook** to extract patterns from Claude Code sessions.

## What Gets Extracted
- Error resolution patterns
- User correction patterns
- Framework workarounds
- Debugging techniques
- Project-specific conventions

## Skill Output Format
Saves to `~/.claude/skills/learned/[pattern-name].md`:
```markdown
# [Pattern Name]
**Context:** [When this applies]
## Problem - Solution - When to Use
```

## Hook Setup
Add to `~/.claude/settings.json`:
```json
{"hooks": {"Stop": [{"matcher": "*", "hooks": [...]}]}}
```

## Related Tools
- **Command**: `/learn` for manual extraction
- **Skill**: All skills in `.claude/skills/`
- **Agent**: Reference agents for patterns

Keep skills focused - one pattern per file.
