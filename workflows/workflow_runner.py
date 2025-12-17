"""
Workflow Runner
==============

Executes code-based workflows using LangGraph infrastructure.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from orchestration.langgraph_integration import WorkflowState, WorkflowStatus

logger = logging.getLogger(__name__)


class WorkflowConfig(BaseModel):
    """Workflow configuration"""

    name: str
    description: str
    triggers: list[str] = []
    environment_vars: dict[str, str] = {}
    timeout_seconds: int = 3600
    max_retries: int = 3


class WorkflowResult(BaseModel):
    """Workflow execution result"""

    workflow_id: str
    name: str
    status: WorkflowStatus
    started_at: str
    completed_at: str | None = None
    duration_seconds: float | None = None
    outputs: dict[str, Any] = {}
    errors: list[str] = []


class WorkflowRunner:
    """
    Executes code-based workflows.

    Provides:
    - Workflow execution engine
    - State management
    - Error handling and retries
    - Result reporting
    """

    def __init__(self):
        self.workflows: dict[str, Any] = {}
        self.results: list[WorkflowResult] = []

    def register(self, name: str, workflow_class: type) -> None:
        """Register a workflow"""
        self.workflows[name] = workflow_class
        logger.info(f"Registered workflow: {name}")

    async def run(
        self,
        workflow_name: str,
        inputs: dict[str, Any] | None = None,
        config: WorkflowConfig | None = None,
    ) -> WorkflowResult:
        """
        Run a workflow by name.

        Args:
            workflow_name: Name of registered workflow
            inputs: Input parameters for workflow
            config: Optional workflow configuration

        Returns:
            WorkflowResult with execution details
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_name}")

        workflow_class = self.workflows[workflow_name]
        workflow = workflow_class()

        # Create initial state
        state = WorkflowState(
            inputs=inputs or {},
            started_at=datetime.now(UTC).isoformat(),
        )

        logger.info(f"Starting workflow: {workflow_name}")
        start_time = datetime.now(UTC)

        try:
            # Execute workflow
            result_state = await workflow.execute(state)

            # Create result
            end_time = datetime.now(UTC)
            duration = (end_time - start_time).total_seconds()

            result = WorkflowResult(
                workflow_id=result_state.workflow_id,
                name=workflow_name,
                status=result_state.status,
                started_at=result_state.started_at or "",
                completed_at=end_time.isoformat(),
                duration_seconds=duration,
                outputs=result_state.outputs,
                errors=[str(e) for e in result_state.errors],
            )

            self.results.append(result)
            logger.info(
                f"Workflow completed: {workflow_name} "
                f"[{result.status}] in {duration:.2f}s"
            )

            return result

        except Exception as e:
            logger.error(f"Workflow failed: {workflow_name} - {e}")
            end_time = datetime.now(UTC)
            duration = (end_time - start_time).total_seconds()

            result = WorkflowResult(
                workflow_id=state.workflow_id,
                name=workflow_name,
                status=WorkflowStatus.FAILED,
                started_at=state.started_at or "",
                completed_at=end_time.isoformat(),
                duration_seconds=duration,
                errors=[str(e)],
            )

            self.results.append(result)
            raise

    async def run_multiple(
        self,
        workflow_names: list[str],
        inputs: dict[str, Any] | None = None,
    ) -> list[WorkflowResult]:
        """Run multiple workflows in parallel"""
        tasks = [self.run(name, inputs) for name in workflow_names]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def get_results(self, workflow_name: str | None = None) -> list[WorkflowResult]:
        """Get workflow execution results"""
        if workflow_name:
            return [r for r in self.results if r.name == workflow_name]
        return self.results
