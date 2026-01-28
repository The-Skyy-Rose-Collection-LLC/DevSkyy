---
description: Create implementation plan. WAIT for user CONFIRM before coding.
---

# Plan Command

Invokes **planner** agent to create a plan before writing code.

## What It Does
1. Restate requirements clearly
2. Break into phases with specific steps
3. Identify risks and dependencies
4. **WAIT for user confirmation**

## When to Use
- New features
- Architectural changes
- Complex refactoring
- Multiple files affected

## Output Format
```markdown
# Plan: [Feature]
## Requirements Restatement
## Implementation Phases
### Phase 1: [Name]
- Step with file path
## Dependencies
## Risks (HIGH/MEDIUM/LOW)
## Complexity: HIGH/MEDIUM/LOW

**WAITING FOR CONFIRMATION**
```

## Responses
- "yes" / "proceed" - Start implementation
- "modify: [changes]" - Adjust plan
- "different approach: [alternative]"

## Related
- `/tdd` - Implement with tests
- `/code-review` - Review implementation
- Agent: `~/.claude/agents/planner.md`
