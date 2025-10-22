"""
Automation Workflow Engine
Trigger-based automation with multi-step workflow orchestration, conditional logic,
error handling with automatic retry, rollback mechanisms, and audit logging
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from api_integration.core_engine import api_gateway
from fashion.intelligence_engine import fashion_intelligence
from infrastructure.elasticsearch_manager import elasticsearch_manager
from infrastructure.notification_manager import notification_manager
from infrastructure.redis_manager import redis_manager

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Workflow trigger types"""

    WEBHOOK = "webhook"
    SCHEDULED = "scheduled"
    EVENT = "event"
    API_RESPONSE = "api_response"
    THRESHOLD = "threshold"
    MANUAL = "manual"


class WorkflowStatus(Enum):
    """Workflow execution status"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    ROLLED_BACK = "rolled_back"


class StepStatus(Enum):
    """Workflow step status"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


class ActionType(Enum):
    """Workflow action types"""

    API_CALL = "api_call"
    DATA_TRANSFORM = "data_transform"
    NOTIFICATION = "notification"
    CONDITION = "condition"
    DELAY = "delay"
    PARALLEL = "parallel"
    FASHION_ANALYSIS = "fashion_analysis"
    CACHE_OPERATION = "cache_operation"
    DATABASE_OPERATION = "database_operation"


@dataclass
class WorkflowTrigger:
    """Workflow trigger configuration"""

    trigger_id: str
    trigger_type: TriggerType
    name: str
    description: str
    config: Dict[str, Any]
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["trigger_type"] = self.trigger_type.value
        data["created_at"] = self.created_at.isoformat()
        return data


@dataclass
class WorkflowStep:
    """Individual workflow step"""

    step_id: str
    name: str
    action_type: ActionType
    config: Dict[str, Any]
    depends_on: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 300
    rollback_config: Optional[Dict[str, Any]] = None
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Any = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["action_type"] = self.action_type.value
        data["status"] = self.status.value
        if self.started_at:
            data["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        return data


@dataclass
class Workflow:
    """Complete workflow definition"""

    workflow_id: str
    name: str
    description: str
    trigger: WorkflowTrigger
    steps: List[WorkflowStep]
    variables: Dict[str, Any] = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: float = 0.0
    fashion_context: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["trigger"] = self.trigger.to_dict()
        data["steps"] = [step.to_dict() for step in self.steps]
        data["status"] = self.status.value
        data["created_at"] = self.created_at.isoformat()
        if self.started_at:
            data["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        return data


class WorkflowAction(ABC):
    """Abstract base class for workflow actions"""

    @abstractmethod
    async def execute(
        self, step: WorkflowStep, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the workflow action"""
        pass

    @abstractmethod
    async def rollback(self, step: WorkflowStep, context: Dict[str, Any]) -> bool:
        """Rollback the workflow action"""
        pass


class APICallAction(WorkflowAction):
    """API call workflow action"""

    async def execute(
        self, step: WorkflowStep, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute API call"""

        config = step.config

        # Resolve variables in config
        resolved_config = self._resolve_variables(config, context)

        # Make API call
        result = await api_gateway.make_request(
            api_id=resolved_config["api_id"],
            endpoint=resolved_config["endpoint"],
            method=resolved_config.get("method", "GET"),
            params=resolved_config.get("params"),
            data=resolved_config.get("data"),
            headers=resolved_config.get("headers"),
            timeout=step.timeout,
        )

        return result

    async def rollback(self, step: WorkflowStep, context: Dict[str, Any]) -> bool:
        """Rollback API call (if rollback config provided)"""

        if not step.rollback_config:
            return True

        try:
            rollback_result = await api_gateway.make_request(
                api_id=step.rollback_config["api_id"],
                endpoint=step.rollback_config["endpoint"],
                method=step.rollback_config.get("method", "POST"),
                params=step.rollback_config.get("params"),
                data=step.rollback_config.get("data"),
                headers=step.rollback_config.get("headers"),
            )

            return rollback_result.get("success", False)

        except Exception as e:
            logger.error(f"Rollback failed for step {step.step_id}: {e}")
            return False

    def _resolve_variables(
        self, config: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve variables in configuration"""

        resolved = {}

        for key, value in config.items():
            if (
                isinstance(value, str)
                and value.startswith("${")
                and value.endswith("}")
            ):
                var_name = value[2:-1]
                resolved[key] = context.get(var_name, value)
            elif isinstance(value, dict):
                resolved[key] = self._resolve_variables(value, context)
            else:
                resolved[key] = value

        return resolved


class NotificationAction(WorkflowAction):
    """Notification workflow action"""

    async def execute(
        self, step: WorkflowStep, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send notification"""

        config = step.config

        message_id = await notification_manager.send_from_template(
            template_name=config["template_name"],
            webhook_url=config["webhook_url"],
            context=context,
            priority=config.get("priority", "normal"),
        )

        return {"success": True, "message_id": message_id, "notification_sent": True}

    async def rollback(self, step: WorkflowStep, context: Dict[str, Any]) -> bool:
        """Rollback notification (no-op for notifications)"""
        return True


class FashionAnalysisAction(WorkflowAction):
    """Fashion analysis workflow action"""

    async def execute(
        self, step: WorkflowStep, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform fashion analysis"""

        config = step.config
        analysis_type = config.get("analysis_type", "context")

        if analysis_type == "context":
            text = config.get("text") or context.get("text", "")
            result = await fashion_intelligence.analyze_fashion_context(text)

        elif analysis_type == "trends":
            result = await fashion_intelligence.get_trend_recommendations(
                category=config.get("category"),
                season=config.get("season"),
                target_demographic=config.get("target_demographic"),
                sustainability_focus=config.get("sustainability_focus", False),
            )

        elif analysis_type == "market_intelligence":
            result = await fashion_intelligence.get_market_intelligence(
                region=config.get("region", "global"), segment=config.get("segment")
            )

        else:
            result = {"error": f"Unknown analysis type: {analysis_type}"}

        return {
            "success": True,
            "analysis_result": result,
            "analysis_type": analysis_type,
        }

    async def rollback(self, step: WorkflowStep, context: Dict[str, Any]) -> bool:
        """Rollback fashion analysis (no-op for analysis)"""
        return True


class ConditionAction(WorkflowAction):
    """Conditional logic workflow action"""

    async def execute(
        self, step: WorkflowStep, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate condition"""

        config = step.config
        condition = config["condition"]

        # Simple condition evaluation
        result = self._evaluate_condition(condition, context)

        return {"success": True, "condition_result": result, "condition": condition}

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate condition string"""

        # Simple condition evaluation (in production, use a proper expression evaluator)
        try:
            # Replace variables in condition
            for var_name, var_value in context.items():
                condition = condition.replace(f"${{{var_name}}}", str(var_value))

            # Evaluate condition (be careful with eval in production!)
            return eval(condition)

        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")
            return False

    async def rollback(self, step: WorkflowStep, context: Dict[str, Any]) -> bool:
        """Rollback condition (no-op for conditions)"""
        return True


class WorkflowEngine:
    """Main workflow automation engine"""

    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.triggers: Dict[str, WorkflowTrigger] = {}
        self.running_workflows: Dict[str, asyncio.Task] = {}

        # Action registry
        self.actions = {
            ActionType.API_CALL: APICallAction(),
            ActionType.NOTIFICATION: NotificationAction(),
            ActionType.FASHION_ANALYSIS: FashionAnalysisAction(),
            ActionType.CONDITION: ConditionAction(),
        }

        # Execution metrics
        self.metrics = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_execution_time": 0.0,
            "workflows_by_trigger": {},
            "last_updated": datetime.now(),
        }

        logger.info("Workflow Engine initialized")

    async def register_workflow(self, workflow: Workflow) -> bool:
        """Register a new workflow"""

        try:
            # Validate workflow
            if not self._validate_workflow(workflow):
                return False

            # Store workflow
            self.workflows[workflow.workflow_id] = workflow

            # Register trigger
            self.triggers[workflow.trigger.trigger_id] = workflow.trigger

            # Cache in Redis
            cache_key = f"workflow:{workflow.workflow_id}"
            await redis_manager.set(
                cache_key, workflow.to_dict(), ttl=86400, prefix="workflows"  # 24 hours
            )

            logger.info(f"Registered workflow: {workflow.name}")
            return True

        except Exception as e:
            logger.error(f"Error registering workflow {workflow.workflow_id}: {e}")
            return False

    def _validate_workflow(self, workflow: Workflow) -> bool:
        """Validate workflow configuration"""

        # Check for circular dependencies
        if self._has_circular_dependencies(workflow.steps):
            logger.error(
                f"Circular dependencies detected in workflow {workflow.workflow_id}"
            )
            return False

        # Validate step configurations
        for step in workflow.steps:
            if step.action_type not in self.actions:
                logger.error(f"Unknown action type: {step.action_type}")
                return False

        return True

    def _has_circular_dependencies(self, steps: List[WorkflowStep]) -> bool:
        """Check for circular dependencies in workflow steps"""

        # Simple cycle detection using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(step_id: str) -> bool:
            if step_id in rec_stack:
                return True
            if step_id in visited:
                return False

            visited.add(step_id)
            rec_stack.add(step_id)

            # Find step by ID
            step = next((s for s in steps if s.step_id == step_id), None)
            if step:
                for dep in step.depends_on:
                    if has_cycle(dep):
                        return True

            rec_stack.remove(step_id)
            return False

        for step in steps:
            if step.step_id not in visited:
                if has_cycle(step.step_id):
                    return True

        return False

    async def trigger_workflow(
        self, workflow_id: str, trigger_data: Dict[str, Any] = None
    ) -> str:
        """Trigger workflow execution"""

        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow = self.workflows[workflow_id]
        execution_id = str(uuid.uuid4())

        # Create execution context
        context = {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "trigger_data": trigger_data or {},
            "variables": workflow.variables.copy(),
            "start_time": datetime.now(),
        }

        # Start workflow execution
        task = asyncio.create_task(self._execute_workflow(workflow, context))

        self.running_workflows[execution_id] = task

        logger.info(
            f"Triggered workflow {workflow.name} with execution ID: {execution_id}"
        )
        return execution_id

    async def _execute_workflow(
        self, workflow: Workflow, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute workflow with all steps"""

        execution_id = context["execution_id"]
        start_time = time.time()

        try:
            workflow.status = WorkflowStatus.RUNNING
            workflow.started_at = datetime.now()

            # Log workflow start
            await self._log_workflow_event(workflow, "started", context)

            # Execute steps in dependency order
            executed_steps = set()
            step_results = {}

            while len(executed_steps) < len(workflow.steps):
                # Find steps ready to execute
                ready_steps = [
                    step
                    for step in workflow.steps
                    if (
                        step.step_id not in executed_steps
                        and all(dep in executed_steps for dep in step.depends_on)
                    )
                ]

                if not ready_steps:
                    raise Exception(
                        "No steps ready to execute - possible circular dependency"
                    )

                # Execute ready steps (can be parallel)
                step_tasks = []
                for step in ready_steps:
                    task = asyncio.create_task(
                        self._execute_step(step, context, step_results)
                    )
                    step_tasks.append((step, task))

                # Wait for all steps to complete
                for step, task in step_tasks:
                    try:
                        result = await task
                        step_results[step.step_id] = result
                        executed_steps.add(step.step_id)

                        # Update context with step result
                        context[f"step_{step.step_id}_result"] = result

                    except Exception as e:
                        logger.error(f"Step {step.step_id} failed: {e}")

                        # Handle step failure
                        if step.retry_count < step.max_retries:
                            step.retry_count += 1
                            logger.info(
                                f"Retrying step {step.step_id} (attempt {step.retry_count})"
                            )
                            # Remove from executed_steps to retry
                            continue
                        else:
                            # Step failed permanently
                            step.status = StepStatus.FAILED
                            step.error_message = str(e)

                            # Rollback workflow
                            await self._rollback_workflow(
                                workflow, executed_steps, context
                            )

                            workflow.status = WorkflowStatus.FAILED
                            raise e

            # All steps completed successfully
            workflow.status = WorkflowStatus.SUCCESS
            workflow.completed_at = datetime.now()
            workflow.execution_time = time.time() - start_time

            # Update metrics
            await self._update_metrics(workflow, True)

            # Log workflow completion
            await self._log_workflow_event(workflow, "completed", context)

            logger.info(f"Workflow {workflow.name} completed successfully")

            return {
                "success": True,
                "execution_id": execution_id,
                "execution_time": workflow.execution_time,
                "step_results": step_results,
            }

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.now()
            workflow.execution_time = time.time() - start_time

            # Update metrics
            await self._update_metrics(workflow, False)

            # Log workflow failure
            await self._log_workflow_event(workflow, "failed", context, str(e))

            logger.error(f"Workflow {workflow.name} failed: {e}")

            return {
                "success": False,
                "execution_id": execution_id,
                "error": str(e),
                "execution_time": workflow.execution_time,
            }

        finally:
            # Clean up running workflow
            if execution_id in self.running_workflows:
                del self.running_workflows[execution_id]

    async def _execute_step(
        self, step: WorkflowStep, context: Dict[str, Any], step_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute individual workflow step"""

        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()

        try:
            # Get action handler
            action = self.actions.get(step.action_type)
            if not action:
                raise Exception(f"No action handler for type: {step.action_type}")

            # Execute action with timeout
            result = await asyncio.wait_for(
                action.execute(step, context), timeout=step.timeout
            )

            step.status = StepStatus.SUCCESS
            step.completed_at = datetime.now()
            step.result = result

            logger.info(f"Step {step.name} completed successfully")
            return result

        except asyncio.TimeoutError:
            step.status = StepStatus.FAILED
            step.error_message = f"Step timed out after {step.timeout} seconds"
            step.completed_at = datetime.now()
            raise Exception(step.error_message)

        except Exception as e:
            step.status = StepStatus.FAILED
            step.error_message = str(e)
            step.completed_at = datetime.now()
            raise e

    async def _rollback_workflow(
        self, workflow: Workflow, executed_steps: set, context: Dict[str, Any]
    ):
        """Rollback executed workflow steps"""

        logger.info(f"Rolling back workflow {workflow.name}")

        # Rollback steps in reverse order
        rollback_steps = [
            step
            for step in reversed(workflow.steps)
            if step.step_id in executed_steps and step.status == StepStatus.SUCCESS
        ]

        for step in rollback_steps:
            try:
                action = self.actions.get(step.action_type)
                if action:
                    success = await action.rollback(step, context)
                    if success:
                        step.status = StepStatus.ROLLED_BACK
                        logger.info(f"Rolled back step {step.name}")
                    else:
                        logger.error(f"Failed to rollback step {step.name}")

            except Exception as e:
                logger.error(f"Error rolling back step {step.name}: {e}")

        workflow.status = WorkflowStatus.ROLLED_BACK

    async def _log_workflow_event(
        self,
        workflow: Workflow,
        event_type: str,
        context: Dict[str, Any],
        error_message: str = None,
    ):
        """Log workflow event to Elasticsearch"""

        try:
            log_data = {
                "workflow_id": workflow.workflow_id,
                "workflow_name": workflow.name,
                "execution_id": context["execution_id"],
                "event_type": event_type,
                "status": workflow.status.value,
                "timestamp": datetime.now().isoformat(),
                "execution_time": workflow.execution_time,
                "fashion_context": workflow.fashion_context,
                "trigger_type": workflow.trigger.trigger_type.value,
                "step_count": len(workflow.steps),
                "error_message": error_message,
            }

            await elasticsearch_manager.index_document("analytics", log_data)

        except Exception as e:
            logger.error(f"Error logging workflow event: {e}")

    async def _update_metrics(self, workflow: Workflow, success: bool):
        """Update workflow execution metrics"""

        self.metrics["total_workflows"] += 1

        if success:
            self.metrics["successful_workflows"] += 1
        else:
            self.metrics["failed_workflows"] += 1

        # Update average execution time
        if self.metrics["average_execution_time"] == 0:
            self.metrics["average_execution_time"] = workflow.execution_time
        else:
            alpha = 0.1
            self.metrics["average_execution_time"] = (
                alpha * workflow.execution_time
                + (1 - alpha) * self.metrics["average_execution_time"]
            )

        # Update trigger type metrics
        trigger_type = workflow.trigger.trigger_type.value
        if trigger_type not in self.metrics["workflows_by_trigger"]:
            self.metrics["workflows_by_trigger"][trigger_type] = 0
        self.metrics["workflows_by_trigger"][trigger_type] += 1

        self.metrics["last_updated"] = datetime.now()

    async def get_workflow_status(self, execution_id: str) -> Dict[str, Any]:
        """Get workflow execution status"""

        if execution_id in self.running_workflows:
            task = self.running_workflows[execution_id]
            return {
                "execution_id": execution_id,
                "status": "running",
                "done": task.done(),
            }

        # Check completed workflows in cache/database
        # This would typically query a persistent store
        return {"execution_id": execution_id, "status": "unknown"}

    async def get_metrics(self) -> Dict[str, Any]:
        """Get workflow engine metrics"""

        return {
            "workflow_metrics": self.metrics,
            "registered_workflows": len(self.workflows),
            "registered_triggers": len(self.triggers),
            "running_workflows": len(self.running_workflows),
            "available_actions": list(self.actions.keys()),
        }

    async def health_check(self) -> Dict[str, Any]:
        """Health check for workflow engine"""

        try:
            metrics = await self.get_metrics()

            # Calculate success rate
            total = self.metrics["total_workflows"]
            success_rate = (
                self.metrics["successful_workflows"] / total if total > 0 else 1.0
            )

            return {
                "status": "healthy",
                "registered_workflows": len(self.workflows),
                "running_workflows": len(self.running_workflows),
                "success_rate": success_rate,
                "average_execution_time": self.metrics["average_execution_time"],
                "fashion_workflows": len(
                    [w for w in self.workflows.values() if w.fashion_context]
                ),
                "metrics": metrics,
            }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global workflow engine instance
workflow_engine = WorkflowEngine()
