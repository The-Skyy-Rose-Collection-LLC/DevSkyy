from api_integration.core_engine import api_gateway
from datetime import datetime, timedelta
from infrastructure.elasticsearch_manager import elasticsearch_manager
from infrastructure.notification_manager import notification_manager
from infrastructure.redis_manager import redis_manager
import json
import time

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import Enum
from fashion.intelligence_engine import fashion_intelligence
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union
import ast
import asyncio
import logging
import uuid

"""
Automation Workflow Engine
Trigger-based automation with multi-step workflow orchestration, conditional logic,
error handling with automatic retry, rollback mechanisms, and audit logging
"""

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
    VIDEO_GENERATION = "video_generation"
    BRAND_MODEL_TRAINING = "brand_model_training"
    IMAGE_GENERATION = "image_generation"

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
            # Replace variables in condition with proper sanitization
            if context:
                for var_name, var_value in context.items():
                    # Sanitize variable name to prevent injection
                    if not var_name.isidentifier():
                        logger.warning(f"Invalid variable name blocked: {var_name}")
                        continue

                    # Replace variables safely
                    placeholder = f"${{{var_name}}}"
                    condition = condition.replace(placeholder, str(var_value))

            # Use safe evaluation instead of eval()
            return self._safe_eval(condition)

        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")
            return False

    async def rollback(self, step: WorkflowStep, context: Dict[str, Any]) -> bool:
        """Rollback condition (no-op for conditions)"""
        return True

    def _safe_eval(self, expression: str) -> bool:
        """
        Safely evaluate expressions without code injection risk.

        This method replaces the dangerous eval() usage with a secure alternative
        that only allows safe literal evaluation and basic comparison operations.

        Args:
            expression: The expression to evaluate safely

        Returns:
            bool: The result of the evaluation, or False if evaluation fails
        """
        import ast
        import operator

        # Define allowed operations for security
        allowed_operators = {
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
            ast.And: operator.and_,
            ast.Or: operator.or_,
            ast.Not: operator.not_,
        }

        try:
            # First try literal evaluation for simple values
            try:
                result = ast.literal_eval(expression)
                return bool(result)
            except (ValueError, SyntaxError):
                pass

            # For more complex expressions, parse the AST safely
            try:
                node = ast.parse(expression, mode='eval')
                return self._eval_node(node.body, allowed_operators)
            except (ValueError, SyntaxError, TypeError) as e:
                logger.warning(f"Unsafe or invalid expression blocked: {expression} - {e}")
                return False

        except Exception as e:
            logger.error(f"Error in safe evaluation of '{expression}': {e}")
            return False

    def _eval_node(self, node, allowed_operators):
        """Recursively evaluate AST nodes safely"""
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.Str):  # Python < 3.8
            return node.s
        elif isinstance(node, ast.NameConstant):  # Python < 3.8
            return node.value
        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left, allowed_operators)
            for op, comparator in zip(node.ops, node.comparators):
                if type(op) not in allowed_operators:
                    raise ValueError(f"Operator {type(op)} not allowed")
                right = self._eval_node(comparator, allowed_operators)
                if not allowed_operators[type(op)](left, right):
                    return False
                left = right
            return True
        elif isinstance(node, ast.BoolOp):
            if type(node.op) not in allowed_operators:
                raise ValueError(f"Boolean operator {type(node.op)} not allowed")
            op_func = allowed_operators[type(node.op)]
            values = [self._eval_node(value, allowed_operators) for value in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            elif isinstance(node.op, ast.Or):
                return any(values)
        elif isinstance(node, ast.UnaryOp):
            if type(node.op) not in allowed_operators:
                raise ValueError(f"Unary operator {type(node.op)} not allowed")
            operand = self._eval_node(node.operand, allowed_operators)
            return allowed_operators[type(node.op)](operand)
        else:
            raise ValueError(f"Node type {type(node)} not allowed")

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
                "fashion_workflows": len()
                    [w for w in self.workflows.values() if w.fashion_context]
                ),
                "metrics": metrics,
            }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

class VideoGenerationWorkflowEngine(WorkflowEngine):
    """
    Extended workflow engine with video generation capabilities.
    Integrates with FashionComputerVisionAgent and SkyRoseBrandTrainer.
    """

    def __init__(self):
        super().__init__()

        # Import video generation modules
        try:
            from agent.modules.frontend.fashion_computer_vision_agent import fashion_vision_agent
            from agent.modules.backend.brand_model_trainer import brand_trainer

            self.fashion_vision_agent = fashion_vision_agent
            self.brand_trainer = brand_trainer

            # Register video generation actions
            self._register_video_actions()

            logger.info("✅ Video Generation Workflow Engine initialized")

        except ImportError as e:
            logger.warning(f"⚠️ Video generation modules not available: {e}")
            self.fashion_vision_agent = None
            self.brand_trainer = None

    def _register_video_actions(self):
        """Register video generation workflow actions."""

        # Fashion runway video generation
        self.register_action(
            ActionType.VIDEO_GENERATION,
            "generate_runway_video",
            self._generate_runway_video_action
        )

        # Product 360° video generation
        self.register_action(
            ActionType.VIDEO_GENERATION,
            "generate_product_360",
            self._generate_product_360_action
        )

        # Brand model training
        self.register_action(
            ActionType.BRAND_MODEL_TRAINING,
            "train_brand_model",
            self._train_brand_model_action
        )

        # Brand-specific image generation
        self.register_action(
            ActionType.IMAGE_GENERATION,
            "generate_brand_image",
            self._generate_brand_image_action
        )

        # Video upscaling
        self.register_action(
            ActionType.VIDEO_GENERATION,
            "upscale_video",
            self._upscale_video_action
        )

    async def _generate_runway_video_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Workflow action for generating fashion runway videos."""
        try:
            if not self.fashion_vision_agent:
                return {"error": "Fashion vision agent not available", "status": "failed"}

            prompt = context.get("prompt", "luxury fashion runway")
            duration = context.get("duration", 4)
            fps = context.get("fps", 8)
            width = context.get("width", 1024)
            height = context.get("height", 576)
            style = context.get("style", "luxury fashion runway")
            upscale = context.get("upscale", True)

            logger.info(f"🎬 Workflow: Generating runway video - {prompt}")

            result = await self.fashion_vision_agent.generate_fashion_runway_video(
                prompt=prompt,
                duration=duration,
                fps=fps,
                width=width,
                height=height,
                style=style,
                upscale=upscale
            )

            if result.get("success"):
                # Log successful generation
                await self._log_video_generation(
                    "runway_video",
                    result.get("video_path"),
                    context
                )

            return result

        except Exception as e:
            logger.error(f"❌ Runway video generation workflow failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def _generate_product_360_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Workflow action for generating product 360° videos."""
        try:
            if not self.fashion_vision_agent:
                return {"error": "Fashion vision agent not available", "status": "failed"}

            product_image_path = context.get("product_image_path")
            if not product_image_path:
                return {"error": "Product image path required", "status": "failed"}

            rotation_steps = context.get("rotation_steps", 24)
            duration = context.get("duration", 3)
            upscale = context.get("upscale", True)

            logger.info(f"🔄 Workflow: Generating 360° video - {product_image_path}")

            result = await self.fashion_vision_agent.generate_product_360_video(
                product_image_path=product_image_path,
                rotation_steps=rotation_steps,
                duration=duration,
                upscale=upscale
            )

            if result.get("success"):
                await self._log_video_generation(
                    "product_360",
                    result.get("video_path"),
                    context
                )

            return result

        except Exception as e:
            logger.error(f"❌ Product 360° video generation workflow failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def _train_brand_model_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Workflow action for training brand models."""
        try:
            if not self.brand_trainer:
                return {"error": "Brand trainer not available", "status": "failed"}

            dataset_path = context.get("dataset_path")
            model_name = context.get("model_name", "skyy_rose_v1")

            if not dataset_path:
                return {"error": "Dataset path required", "status": "failed"}

            logger.info(f"🚀 Workflow: Training brand model - {model_name}")

            result = await self.brand_trainer.train_lora_model(
                dataset_path=dataset_path,
                model_name=model_name
            )

            if result.get("success"):
                await self._log_model_training(model_name, result, context)

            return result

        except Exception as e:
            logger.error(f"❌ Brand model training workflow failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def _generate_brand_image_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Workflow action for generating brand-specific images."""
        try:
            if not self.brand_trainer:
                return {"error": "Brand trainer not available", "status": "failed"}

            prompt = context.get("prompt", "luxury fashion item")
            model_name = context.get("model_name", "skyy_rose_v1")
            trigger_word = context.get("trigger_word", "skyrose_collection")
            width = context.get("width", 1024)
            height = context.get("height", 1024)

            logger.info(f"🎨 Workflow: Generating brand image - {model_name}")

            result = await self.brand_trainer.generate_with_brand_model(
                prompt=prompt,
                model_name=model_name,
                trigger_word=trigger_word,
                width=width,
                height=height
            )

            return result

        except Exception as e:
            logger.error(f"❌ Brand image generation workflow failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def _upscale_video_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Workflow action for upscaling videos."""
        try:
            if not self.fashion_vision_agent:
                return {"error": "Fashion vision agent not available", "status": "failed"}

            video_path = context.get("video_path")
            if not video_path:
                return {"error": "Video path required", "status": "failed"}

            target_resolution = context.get("target_resolution", (2048, 1152))

            logger.info(f"⬆️ Workflow: Upscaling video - {video_path}")

            result = await self.fashion_vision_agent.upscale_video(
                video_path=video_path,
                target_resolution=target_resolution
            )

            return result

        except Exception as e:
            logger.error(f"❌ Video upscaling workflow failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def _log_video_generation(self, video_type: str, video_path: str, context: Dict[str, Any]):
        """Log video generation for monitoring and analytics."""
        try:
            log_data = {
                "event_type": "video_generation",
                "video_type": video_type,
                "video_path": video_path,
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "workflow_id": context.get("workflow_id"),
                "execution_id": context.get("execution_id")
            }

            # Log to Elasticsearch if available
            if hasattr(self, 'elasticsearch_manager') and self.elasticsearch_manager:
                await self.elasticsearch_manager.index_document(
                    index="video_generation_logs",
                    document=log_data
                )

            logger.info(f"📊 Video generation logged: {video_type} - {video_path}")

        except Exception as e:
            logger.warning(f"Failed to log video generation: {e}")

    async def _log_model_training(self, model_name: str, result: Dict[str, Any], context: Dict[str, Any]):
        """Log model training for monitoring and analytics."""
        try:
            log_data = {
                "event_type": "model_training",
                "model_name": model_name,
                "training_result": result,
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "workflow_id": context.get("workflow_id"),
                "execution_id": context.get("execution_id")
            }

            # Log to Elasticsearch if available
            if hasattr(self, 'elasticsearch_manager') and self.elasticsearch_manager:
                await self.elasticsearch_manager.index_document(
                    index="model_training_logs",
                    document=log_data
                )

            logger.info(f"📊 Model training logged: {model_name}")

        except Exception as e:
            logger.warning(f"Failed to log model training: {e}")

# Global workflow engine instance with video generation capabilities
workflow_engine = VideoGenerationWorkflowEngine()
