# DevSkyy Workflows

> Idempotent, observable, recoverable | 11 files

## Architecture
```
devskyy_workflows/
├── workflow_runner.py      # Execution engine
├── ci_workflow.py          # CI/CD automation
├── deployment_workflow.py  # Deploy orchestration
├── docker_workflow.py      # Container workflows
├── mcp_workflow.py         # MCP management
└── quality_workflow.py     # Code quality
```

## Pattern
```python
class WorkflowRunner:
    async def run(self, steps: list[WorkflowStep], *, fail_fast: bool = True) -> dict:
        for step in self._topological_sort(steps):
            if self._dependencies_met(step, results):
                try:
                    await step.action()
                    results[step.name] = WorkflowStatus.SUCCESS
                except Exception:
                    results[step.name] = WorkflowStatus.FAILED
                    if fail_fast: break
        return results
```

## Commands
```bash
python -m devskyy_workflows ci           # CI workflow
python -m devskyy_workflows deploy       # Deploy
python -m devskyy_workflows quality      # Quality checks
```

## USE THESE TOOLS
| Task | Tool |
|------|------|
| Deploy | **MCP**: `wordpress_sync`, Vercel `deploy_to_vercel` |
| Quality | **Command**: `/verify` |
| Workflow errors | **Agent**: `build-error-resolver` |

**"Workflows that break should heal themselves."**
