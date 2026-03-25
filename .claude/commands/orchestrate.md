# Orchestrate Command

Sequential agent workflow for complex tasks.

## Usage
`/orchestrate [workflow-type] [task-description]`

## Workflow Types
- **feature**: planner → tdd-guide → code-reviewer → security-reviewer
- **bugfix**: explorer → tdd-guide → code-reviewer
- **refactor**: architect → code-reviewer → tdd-guide
- **security**: security-reviewer → code-reviewer → architect

## Handoff Format
```markdown
## HANDOFF: [prev-agent] → [next-agent]
### Context, Findings, Files Modified
### Open Questions, Recommendations
```

## Final Report
```
ORCHESTRATION REPORT
Workflow: [type], Task: [desc]
SUMMARY, AGENT OUTPUTS, FILES CHANGED
TEST RESULTS, SECURITY STATUS
RECOMMENDATION: SHIP / NEEDS WORK / BLOCKED
```

## Arguments
- `feature <desc>` - Full feature workflow
- `bugfix <desc>` - Bug fix workflow
- `refactor <desc>` - Refactoring workflow
- `custom "<agents>" <desc>` - Custom sequence
