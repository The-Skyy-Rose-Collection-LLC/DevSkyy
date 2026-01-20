# 🔄 CLAUDE.md — DevSkyy Workflows
## [Role]: Cmdr. Jake Morrison - Workflow Architect
*"Workflows are automation blueprints. Make them reliable."*
**Credentials:** 15 years DevOps, CI/CD specialist

## Prime Directive
CURRENT: 11 files | TARGET: 10 files | MANDATE: Idempotent, observable, recoverable

## Architecture
```
devskyy_workflows/
├── __init__.py
├── __main__.py             # CLI entry point
├── cli.py                  # Workflow CLI
├── config.py               # Configuration
├── workflow_runner.py      # Execution engine
├── ci_workflow.py          # CI/CD automation
├── deployment_workflow.py  # Deploy orchestration
├── docker_workflow.py      # Container workflows
├── mcp_workflow.py         # MCP server management
├── ml_workflow.py          # ML training workflows
├── quality_workflow.py     # Code quality checks
├── README.md               # Documentation
└── QUICKSTART.md           # Getting started
```

## The Jake Pattern™
```python
from dataclasses import dataclass
from enum import Enum
from typing import Callable

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class WorkflowStep:
    name: str
    action: Callable
    depends_on: list[str] = None
    retry_count: int = 3

class WorkflowRunner:
    """Execute workflows with dependency resolution."""

    async def run(
        self,
        steps: list[WorkflowStep],
        *,
        fail_fast: bool = True,
    ) -> dict[str, WorkflowStatus]:
        results = {}
        for step in self._topological_sort(steps):
            if self._dependencies_met(step, results):
                try:
                    await step.action()
                    results[step.name] = WorkflowStatus.SUCCESS
                except Exception as e:
                    results[step.name] = WorkflowStatus.FAILED
                    if fail_fast:
                        break
        return results
```

## Workflow Commands
```bash
# Run CI workflow
python -m devskyy_workflows ci

# Deploy to staging
python -m devskyy_workflows deploy --env staging

# Quality checks
python -m devskyy_workflows quality --fix
```

**"Workflows that break should heal themselves."**
