# Quick Start Guide: Code-Based Workflows

## Overview
DevSkyy now uses **code-based workflows** written in Python instead of YAML configuration files. This provides better type safety, testability, and integration with the existing infrastructure.

## Installation

```bash
# Install DevSkyy with workflow dependencies
pip install -e .
```

## Running Workflows

### List Available Workflows
```bash
python -m workflows list
```

Output:
```
ci          - CI/CD Pipeline (testing, linting, security)
deployment  - Deployment Pipeline (staging/production)
docker      - Docker Workflow (container builds)
mcp         - MCP Workflow (Model Context Protocol)
ml          - ML Workflow (AI/ML model testing)
quality     - Quality Workflow (code standards)
```

### Run a Single Workflow
```bash
# CI/CD Pipeline
python -m workflows run ci

# Quality Checks
python -m workflows run quality

# Deployment to Staging
python -m workflows run deployment --environment=staging

# Deployment to Production
python -m workflows run deployment --environment=production
```

### Run All Workflows
```bash
python -m workflows run all
```

### Check Workflow Status
```bash
python -m workflows status
```

## Programmatic Usage

### Basic Example
```python
import asyncio
from workflows import WorkflowRunner, CIWorkflow

async def main():
    # Create runner
    runner = WorkflowRunner()
    runner.register("ci", CIWorkflow)
    
    # Run workflow
    result = await runner.run("ci")
    
    # Check results
    print(f"Status: {result.status}")
    print(f"Duration: {result.duration_seconds}s")
    print(f"Outputs: {result.outputs}")

asyncio.run(main())
```

### Run Multiple Workflows in Parallel
```python
import asyncio
from workflows import WorkflowRunner, CIWorkflow, QualityWorkflow

async def main():
    runner = WorkflowRunner()
    runner.register("ci", CIWorkflow)
    runner.register("quality", QualityWorkflow)
    
    # Run both workflows in parallel
    results = await runner.run_multiple(["ci", "quality"])
    
    for result in results:
        print(f"{result.name}: {result.status}")

asyncio.run(main())
```

## GitHub Actions Integration

The code-based workflows can be triggered from GitHub Actions using a minimal YAML file:

```yaml
name: Run Workflows
on: [push, pull_request]

jobs:
  workflows:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e .
      - run: python -m workflows run all
```

## Workflow Details

### CI Workflow
Tests code quality, runs tests, and builds the project.

**Steps:**
1. Security scanning (npm audit, pip-audit, bandit)
2. Code quality (ruff, mypy, eslint, prettier)
3. Tests (pytest, jest)
4. Build (Python package, frontend)

### Deployment Workflow
Deploys to staging or production environments.

**Steps:**
1. Pre-deployment validation
2. Docker image building
3. Security scanning (Trivy)
4. Environment deployment
5. Health checks
6. Rollback on failure

### Docker Workflow
Builds and tests Docker containers.

**Steps:**
1. Docker build test
2. Container startup validation
3. Multi-platform builds
4. Security scanning

### Quality Workflow
Ensures code quality and standards.

**Steps:**
1. Linting (Ruff, ESLint)
2. Formatting (Ruff, Prettier)
3. Type checking (MyPy, TypeScript)
4. Complexity analysis

### MCP Workflow
Tests Model Context Protocol integration.

**Steps:**
1. MCP server startup
2. Configuration validation
3. Integration tests
4. Performance benchmarks

### ML Workflow
Tests machine learning components.

**Steps:**
1. ML dependency validation
2. Model configuration
3. Agent validation
4. Performance benchmarks

## Troubleshooting

### Import Errors
If you get import errors, install the project:
```bash
pip install -e .
```

### Missing Dependencies
Install required dependencies:
```bash
pip install pydantic httpx
```

### Workflow Failures
Check detailed logs:
```bash
python -m workflows run ci 2>&1 | tee workflow.log
```

View status:
```bash
python -m workflows status
```

## Configuration

Workflow configuration is in `workflows/config.py`:

```python
# Modify trigger conditions
WORKFLOW_TRIGGERS = {
    "ci": {
        "branches": ["main", "develop"],
        "schedule": "0 2 * * *",  # Daily at 2 AM
    },
}

# Modify environments
ENVIRONMENTS = {
    "staging": {"url": "https://staging.devskyy.com"},
    "production": {"url": "https://devskyy.com"},
}

# Modify timeouts
TIMEOUTS = {
    "ci": 3600,  # 1 hour
    "deployment": 3600,
}
```

## Creating Custom Workflows

1. Create a new workflow class:

```python
# workflows/my_workflow.py
from orchestration.langgraph_integration import WorkflowState, WorkflowStatus

class MyWorkflow:
    async def execute(self, state: WorkflowState) -> WorkflowState:
        state.status = WorkflowStatus.RUNNING
        
        # Your workflow logic here
        
        state.status = WorkflowStatus.COMPLETED
        state.outputs = {"result": "success"}
        return state
```

2. Register in `workflows/__init__.py`:

```python
from .my_workflow import MyWorkflow

__all__ = [..., "MyWorkflow"]
```

3. Add to CLI in `workflows/cli.py`:

```python
runner.register("my_workflow", MyWorkflow)
```

## Best Practices

1. **Error Handling**: Always wrap workflow steps in try-except
2. **Logging**: Use Python logging for detailed output
3. **State Management**: Store intermediate results in state.outputs
4. **Idempotency**: Make workflows safe to re-run
5. **Testing**: Write unit tests for custom workflows

## Migration Guide

**Old YAML Workflow:**
```yaml
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest
```

**New Code-Based Workflow:**
```python
class CIWorkflow:
    async def execute(self, state: WorkflowState) -> WorkflowState:
        state.status = WorkflowStatus.RUNNING
        
        # Run tests
        proc = await asyncio.create_subprocess_exec("pytest")
        await proc.communicate()
        
        state.status = WorkflowStatus.COMPLETED
        return state
```

## Support

For help:
- Check `workflows/README.md` for detailed documentation
- Review example workflows in `workflows/` directory
- Consult LangGraph integration in `orchestration/`

## License
Part of DevSkyy Enterprise Platform - Proprietary License
