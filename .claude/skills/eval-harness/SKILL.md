---
name: eval-harness
description: Eval-driven development - define expected behavior before implementing.
---

# Eval Harness

## Eval Types
- **Capability**: Test new functionality
- **Regression**: Ensure existing behavior unchanged

## Metrics
- **pass@k**: At least one success in k attempts (target: pass@3 > 90%)
- **pass^k**: All k trials succeed (for critical paths)

## Workflow
```bash
/eval define feature-name   # Create eval definition
/eval check feature-name    # Run evals
/eval report feature-name   # Full report
```

## Eval Definition
```markdown
## EVAL: feature-name
### Capability Evals
- [ ] Can do X
### Regression Evals
- [ ] Existing Y works
### Success: pass@3 > 90%
```

## Graders
- **Code-based**: `npm test && echo "PASS"`
- **Model-based**: Claude evaluates quality
- **Human**: Manual review flag

## Related Tools
- **Command**: `/eval` for eval management
- **Agent**: `tdd-guide` for test-driven approach
- **Skill**: `tdd-workflow` for testing patterns
