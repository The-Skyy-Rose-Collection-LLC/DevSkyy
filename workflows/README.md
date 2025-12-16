# Code-Based Workflows

Modern workflow orchestration using LangGraph infrastructure, replacing YAML-based GitHub Actions.

## Overview

DevSkyy now uses **code-based workflows** instead of traditional YAML configuration files. This provides:

- ✅ **Type Safety**: Full Python type checking and IDE support
- ✅ **Testability**: Workflows can be tested like any other Python code
- ✅ **Reusability**: Share logic between workflows using standard Python imports
- ✅ **Flexibility**: Dynamic workflow execution based on runtime conditions
- ✅ **Observability**: Better logging, monitoring, and debugging capabilities
- ✅ **Integration**: Seamless integration with existing infrastructure

## Available Workflows

### CI/CD Pipeline (`ci`)
Continuous integration workflow for code quality, testing, and security.

**Executes:**
- Security vulnerability scanning (npm audit, pip-audit, bandit)
- Code quality checks (ruff, mypy, eslint, prettier)
- Unit and integration tests (pytest, jest)
- Build validation (Python package, frontend assets)

### Deployment Pipeline (`deployment`)
Handles deployment to staging and production environments.

**Executes:**
- Pre-deployment validation
- Docker image building and tagging
- Security scanning of images (Trivy)
- Environment-specific deployment
- Health checks and smoke tests
- Automatic rollback on failure

### Docker Workflow (`docker`)
Docker container build, test, and deployment workflow.

**Executes:**
- Docker build testing
- Container startup validation
- Multi-platform builds (linux/amd64, linux/arm64)
- Container registry push
- Security scanning (Trivy)

### MCP Workflow (`mcp`)
Model Context Protocol testing and validation.

**Executes:**
- MCP server startup tests
- Configuration validation
- Integration tests (OpenAI, tools)
- Security scanning
- Performance benchmarks
- Documentation validation

### ML Workflow (`ml`)
Machine Learning and AI agent testing.

**Executes:**
- ML dependency validation
- Model loading and configuration tests
- Agent validation (FashnAgent, TripoAgent)
- Performance benchmarks
- Security scanning

### Quality Workflow (`quality`)
Code quality and standards verification.

**Executes:**
- Code linting (Ruff, ESLint)
- Code formatting checks (Ruff, Prettier)
- Type checking (MyPy, TypeScript)
- Complexity analysis (Radon)

## Usage

### Command Line Interface

```bash
# Run a specific workflow
python -m workflows.cli run ci
python -m workflows.cli run deployment --environment=staging
python -m workflows.cli run docker

# Run all workflows
python -m workflows.cli run all

# List available workflows
python -m workflows.cli list

# Show execution status
python -m workflows.cli status
```

### Programmatic Usage

```python
import asyncio
from workflows import WorkflowRunner, CIWorkflow

# Create runner
runner = WorkflowRunner()
runner.register("ci", CIWorkflow)

# Run workflow
result = asyncio.run(runner.run("ci"))

print(f"Status: {result.status}")
print(f"Duration: {result.duration_seconds}s")
```

### Running in CI/CD Environments

The workflows can be triggered from:

1. **GitHub Actions** (trigger Python workflows from minimal YAML)
2. **GitLab CI** (call workflows from .gitlab-ci.yml)
3. **Jenkins** (execute as pipeline steps)
4. **Locally** (run directly with CLI)

Example GitHub Actions integration:

```yaml
name: Minimal CI Trigger
on: [push, pull_request]

jobs:
  run-workflows:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e .
      - run: python -m workflows.cli run all
```

## Architecture

### Workflow Structure

Each workflow is a Python class that:
1. Inherits workflow capabilities from the LangGraph infrastructure
2. Defines execution steps as async methods
3. Maintains state through `WorkflowState` objects
4. Handles errors and provides detailed results

```python
class CustomWorkflow:
    async def execute(self, state: WorkflowState) -> WorkflowState:
        # Step 1: Initialize
        state.status = WorkflowStatus.RUNNING
        
        # Step 2: Execute tasks
        result = await self._run_task(state)
        
        # Step 3: Complete
        state.status = WorkflowStatus.COMPLETED
        state.outputs = result
        
        return state
```

### State Management

Workflows use Pydantic models for type-safe state management:

- **WorkflowState**: Base state with core workflow metadata
- **Custom State**: Extended state for workflow-specific data
- **WorkflowResult**: Final execution results with metrics

### Error Handling

Workflows include comprehensive error handling:
- Automatic error capture and logging
- Retry logic with exponential backoff
- Rollback capabilities for deployment workflows
- Detailed error reporting in results

## Configuration

Workflow configuration is defined in `workflows/config.py`:

```python
WORKFLOW_TRIGGERS = {
    "ci": {
        "branches": ["main", "develop"],
        "schedule": "0 2 * * *",  # Daily at 2 AM UTC
    },
}

ENVIRONMENTS = {
    "staging": {"url": "https://staging.devskyy.com"},
    "production": {"url": "https://devskyy.com"},
}
```

## Adding New Workflows

1. Create a new workflow class in `workflows/your_workflow.py`
2. Implement the `execute()` method
3. Register it in `workflows/__init__.py`
4. Add configuration in `workflows/config.py`
5. Update CLI runner in `workflows/cli.py`

Example:

```python
# workflows/custom_workflow.py
from orchestration.langgraph_integration import WorkflowState, WorkflowStatus

class CustomWorkflow:
    async def execute(self, state: WorkflowState) -> WorkflowState:
        state.status = WorkflowStatus.RUNNING
        
        # Your logic here
        
        state.status = WorkflowStatus.COMPLETED
        return state
```

## Testing Workflows

Workflows can be tested like any Python code:

```python
import pytest
from workflows import CIWorkflow
from orchestration.langgraph_integration import WorkflowState

@pytest.mark.asyncio
async def test_ci_workflow():
    workflow = CIWorkflow()
    state = WorkflowState(inputs={"test": True})
    
    result = await workflow.execute(state)
    
    assert result.status == "completed"
    assert "security" in result.outputs
```

## Migration from YAML Workflows

The code-based workflows replace the following YAML files:
- `.github/workflows/ci.yml` → `workflows/ci_workflow.py`
- `.github/workflows/deploy.yml` → `workflows/deployment_workflow.py`
- `.github/workflows/docker.yml` → `workflows/docker_workflow.py`
- `.github/workflows/mcp.yml` → `workflows/mcp_workflow.py`
- `.github/workflows/ml.yml` → `workflows/ml_workflow.py`
- `.github/workflows/quality-check.yml` → `workflows/quality_workflow.py`

## Benefits Over YAML Workflows

1. **Type Safety**: Python's type system catches errors before runtime
2. **IDE Support**: Full autocomplete, go-to-definition, refactoring
3. **Testing**: Unit test workflows with pytest
4. **Debugging**: Use standard Python debuggers
5. **Reusability**: Import and compose workflow logic
6. **Dynamic Execution**: Runtime decisions based on conditions
7. **Better Error Messages**: Stack traces instead of YAML parsing errors
8. **Version Control**: Standard Python code review practices

## Monitoring and Observability

Workflows provide detailed execution metrics:
- Start and end timestamps
- Duration in seconds
- Step-by-step execution history
- Detailed error information
- Output artifacts and results

## Security

All workflows include:
- Security vulnerability scanning
- Secret detection
- Dependency auditing
- Container image scanning
- Code quality enforcement

## Support

For issues or questions about workflows:
1. Check the workflow logs for detailed error messages
2. Run workflows locally with `--debug` flag for more information
3. Review workflow code in `workflows/` directory
4. Consult LangGraph infrastructure in `orchestration/`

## License

Part of the DevSkyy Enterprise Platform - Proprietary License
