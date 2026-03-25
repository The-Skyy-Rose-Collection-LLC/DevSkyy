# Eval Command

Manage eval-driven development workflow.

## Usage
`/eval [define|check|report|list] [feature-name]`

## Define
Create `.claude/evals/feature-name.md`:
```markdown
## EVAL: feature-name
### Capability Evals
- [ ] [Capability 1]
### Regression Evals
- [ ] [Existing behavior works]
### Success: pass@3 > 90%
```

## Check
Run evals, record PASS/FAIL in `.claude/evals/feature-name.log`

## Report
```
EVAL: feature-name
Capability: X/Y, Regression: X/Y
Status: IN PROGRESS / READY
Recommendation: SHIP / NEEDS WORK
```

## Arguments
- `define <name>` - Create eval
- `check <name>` - Run evals
- `report <name>` - Full report
- `list` - Show all evals
