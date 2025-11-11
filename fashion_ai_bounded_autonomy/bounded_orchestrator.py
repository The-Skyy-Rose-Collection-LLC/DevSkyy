"""
Bounded Orchestrator
Extends DevSkyy's existing AgentOrchestrator with bounded autonomy controls

Features:
- Wraps all agents with bounded autonomy wrapper
- Enforces human approval workflows
- Local-only execution
- Complete audit trailing
- Emergency controls
"""

from datetime import datetime
import logging
from typing import Any, Optional

from agent.modules.base_agent import BaseAgent
from agent.orchestrator import AgentOrchestrator, AgentTask, ExecutionPriority, TaskStatus
from fashion_ai_bounded_autonomy.approval_system import ApprovalSystem, ApprovalWorkflowType
from fashion_ai_bounded_autonomy.bounded_autonomy_wrapper import ActionRiskLevel, BoundedAutonomyWrapper


logger = logging.getLogger(__name__)


class BoundedOrchestrator(AgentOrchestrator):
    """
    Bounded Autonomy Orchestrator extending DevSkyy's AgentOrchestrator.

    Adds:
    - Bounded autonomy wrapper for all agents
    - Human approval workflows
    - Local-only enforcement
    - Emergency controls
    - Complete audit logging
    """

    def __init__(
        self,
        max_concurrent_tasks: int = 50,
        local_only: bool = True,
        auto_approve_low_risk: bool = True
    ):
        """
        Initialize a BoundedOrchestrator with bounded autonomy controls, approval system, and emergency controls.
        
        Parameters:
            max_concurrent_tasks (int): Maximum number of tasks the orchestrator will run concurrently.
            local_only (bool): When True, restrict agent actions to local-only execution modes where supported.
            auto_approve_low_risk (bool): When True, automatically approve tasks assessed as low risk without human review.
        """
        super().__init__(max_concurrent_tasks)

        self.local_only = local_only
        self.auto_approve_low_risk = auto_approve_low_risk

        # Bounded autonomy components
        self.wrapped_agents: dict[str, BoundedAutonomyWrapper] = {}
        self.approval_system = ApprovalSystem()

        # Emergency controls
        self.system_paused = False
        self.emergency_stop_active = False

        logger.info(
            f"🔒 Bounded Orchestrator initialized (local_only={local_only}, "
            f"auto_approve_low_risk={auto_approve_low_risk})"
        )

    async def register_agent(
        self,
        agent: BaseAgent,
        capabilities: list[str],
        dependencies: list[str] = None,
        priority: ExecutionPriority = ExecutionPriority.MEDIUM,
    ) -> bool:
        """
        Register an agent with the orchestrator and wrap it with bounded-autonomy controls.
        
        Parameters:
            agent (BaseAgent): The agent instance to register.
            capabilities (list[str]): Capability names exposed by the agent.
            dependencies (list[str], optional): Names of agents this agent depends on; may be None.
            priority (ExecutionPriority): Execution priority to assign to the agent.
        
        Returns:
            bool: `True` if the agent was registered with the base orchestrator and wrapped for bounded autonomy; `False` if base registration failed.
        """
        # Register with parent orchestrator
        success = await super().register_agent(agent, capabilities, dependencies, priority)

        if not success:
            return False

        # Wrap agent with bounded autonomy controls
        wrapped = BoundedAutonomyWrapper(
            wrapped_agent=agent,
            auto_approve_low_risk=self.auto_approve_low_risk,
            local_only=self.local_only
        )

        self.wrapped_agents[agent.agent_name] = wrapped

        logger.info(f"🔒 Agent {agent.agent_name} wrapped with bounded autonomy controls")

        return True

    async def execute_task(
        self,
        task_type: str,
        parameters: dict[str, Any],
        required_capabilities: list[str],
        priority: ExecutionPriority = ExecutionPriority.MEDIUM,
        require_approval: Optional[bool] = None
    ) -> dict[str, Any]:
        """
        Queue or execute a task under bounded-autonomy controls, performing risk assessment and submitting for human approval when required.
        
        Parameters:
            task_type (str): Identifier of the action to perform.
            parameters (dict[str, Any]): Parameters passed to the task's execution.
            required_capabilities (list[str]): Capabilities an agent must have to be considered for execution.
            priority (ExecutionPriority): Execution priority for scheduling.
            require_approval (Optional[bool]): If provided, overrides automatic approval decision for this task.
        
        Returns:
            dict[str, Any]: One of:
                - When an emergency stop is active: {"error": "Emergency stop active", "status": "blocked"}.
                - When the system is paused: {"error": "System paused", "status": "queued"}.
                - When no capable agents are found: {"error": "No agents found with capabilities: [...]"}.
                - When approval is required: {
                    "status": "pending_approval",
                    "task_id": <task_id>,
                    "risk_level": <risk string>,
                    "message": "Task submitted for operator review",
                    "review_command": <string>
                  }.
                - When executed immediately: the task execution result dictionary (contains keys such as "task_id", "status", "results", "errors", "execution_time").
        """
        # Check emergency stop
        if self.emergency_stop_active:
            logger.critical("🚨 Emergency stop active - task blocked")
            return {
                "error": "Emergency stop active",
                "status": "blocked"
            }

        # Check if system paused
        if self.system_paused:
            logger.warning("⏸️  System paused - task queued")
            return {
                "error": "System paused",
                "status": "queued"
            }

        task_id = f"task_{datetime.now().timestamp()}_{task_type}"

        # Find agents with required capabilities
        capable_agents = self._find_agents_with_capabilities(required_capabilities)
        if not capable_agents:
            return {
                "error": f"No agents found with capabilities: {required_capabilities}"
            }

        # Resolve execution order
        execution_order = self._resolve_dependencies(capable_agents)

        # Create task
        task = AgentTask(
            task_id=task_id,
            task_type=task_type,
            parameters=parameters,
            required_agents=execution_order,
            priority=priority,
        )

        self.tasks[task_id] = task

        # Assess overall task risk
        task_risk = self._assess_task_risk(task_type, parameters, execution_order)

        # Check if approval needed
        needs_approval = require_approval if require_approval is not None else (
            task_risk in [ActionRiskLevel.HIGH, ActionRiskLevel.CRITICAL]
        )

        if needs_approval:
            # Submit for approval
            await self.approval_system.submit_for_review(
                action_id=task_id,
                agent_name="orchestrator",
                function_name=task_type,
                parameters=parameters,
                risk_level=task_risk.value,
                workflow_type=ApprovalWorkflowType.HIGH_RISK if task_risk == ActionRiskLevel.CRITICAL else ApprovalWorkflowType.DEFAULT
            )

            logger.info(f"⏳ Task {task_id} submitted for approval (risk: {task_risk.value})")

            return {
                "status": "pending_approval",
                "task_id": task_id,
                "risk_level": task_risk.value,
                "message": "Task submitted for operator review",
                "review_command": f"python -m fashion_ai_bounded_autonomy.approval_cli review {task_id}"
            }

        # Execute immediately
        return await self._execute_bounded_task(task)

    async def execute_approved_task(self, task_id: str, approved_by: str) -> dict[str, Any]:
        """
        Execute a previously approved task and record its execution with the approval system.
        
        Parameters:
            task_id (str): Identifier of the approved task to execute.
            approved_by (str): Operator who approved the task.
        
        Returns:
            dict: Execution outcome containing at least `task_id`, `status`, `results`, and `execution_time`; includes `errors` when failures occurred or an `error` key with `status: "error"` if the task was not found.
        """
        if task_id not in self.tasks:
            return {"error": "Task not found", "status": "error"}

        task = self.tasks[task_id]

        logger.info(f"▶️  Executing approved task {task_id} (approved by {approved_by})")

        result = await self._execute_bounded_task(task)

        # Mark as executed in approval system
        # Sanitize result to prevent circular references before JSON serialization
        sanitized_result = self._sanitize_for_json(result)
        await self.approval_system.mark_executed(task_id, sanitized_result)

        return result

    async def _execute_bounded_task(self, task: AgentTask) -> dict[str, Any]:
        """
        Execute an AgentTask by invoking each required wrapped agent in dependency order under bounded-autonomy controls.
        
        This method updates the provided Task's lifecycle fields (status, started_at, completed_at, result, and error), merges per-agent shared data into the orchestrator's shared_context for successful agent completions, and records per-agent execution outcomes and timings. Each required agent is executed through its BoundedAutonomyWrapper; agent-level failures are collected and do not abort execution of subsequent agents. On unexpected global errors the task is marked failed and an error dict is returned.
        
        Parameters:
            task (AgentTask): The task to execute. The task object is mutated in-place with status, timestamps, result, and error information.
        
        Returns:
            dict[str, Any]: On normal completion returns a dictionary with:
                - "task_id": the task's identifier.
                - "status": the final task status string ("completed" or "failed").
                - "results": mapping of agent_name to each agent's raw result.
                - "errors": list of error messages or `None` if there were no agent errors.
                - "execution_time": total execution time in seconds (completed_at - started_at).
            On a global execution failure returns a dictionary containing:
                - "error": error message string.
                - "task_id": the task's identifier.
        """
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        results = {}
        errors = []

        try:
            # Execute agents in dependency order
            for agent_name in task.required_agents:
                if agent_name not in self.wrapped_agents:
                    errors.append(f"Wrapped agent not found: {agent_name}")
                    continue

                wrapped_agent = self.wrapped_agents[agent_name]

                # Execute through bounded wrapper
                start_time = datetime.now()
                try:
                    # Prepare parameters
                    agent_params = {
                        **task.parameters,
                        "_shared_context": self.shared_context,
                        "_previous_results": results,
                    }

                    # Execute through wrapper
                    result = await wrapped_agent.execute(
                        function_name="execute_core_function",
                        parameters=agent_params,
                        require_approval=False  # Already approved at task level
                    )

                    results[agent_name] = result
                    execution_time = (datetime.now() - start_time).total_seconds()

                    # Check result status
                    if result and isinstance(result, dict) and result.get("status") == "completed":
                        # Update shared context on success
                        self.shared_context.update(result.get("_shared_data", {}))

                        # Track success
                        self._record_execution(agent_name, True, execution_time)
                    else:
                        # Treat non-completed status as failure
                        status = result.get("status") if isinstance(result, dict) else "unknown"
                        error_msg = result.get("error", "Non-completed status") if isinstance(result, dict) else "Invalid result"
                        errors.append(f"{agent_name}: status={status}, {error_msg}")

                        # Track failure
                        self._record_execution(agent_name, False, execution_time)

                except Exception as e:
                    logger.error(f"Agent {agent_name} failed: {e}")
                    errors.append(f"{agent_name}: {e!s}")
                    results[agent_name] = {"error": str(e)}

                    execution_time = (datetime.now() - start_time).total_seconds()
                    self._record_execution(agent_name, False, execution_time)

            # Complete task
            task.status = TaskStatus.COMPLETED if not errors else TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.result = results
            if errors:
                task.error = "; ".join(errors)

            return {
                "task_id": task.task_id,
                "status": task.status.value,
                "results": results,
                "errors": errors if errors else None,
                "execution_time": (task.completed_at - task.started_at).total_seconds(),
            }

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            return {"error": str(e), "task_id": task.task_id}

    def _assess_task_risk(
        self,
        task_type: str,
        parameters: dict[str, Any],
        agents: list[str]
    ) -> ActionRiskLevel:
        """
        Assess the overall risk level for a task.
        
        Parameters:
            task_type (str): Identifier or name of the action to be performed (e.g., "deploy_service", "analyze_data").
            parameters (dict[str, Any]): Additional task parameters used to inform risk heuristics.
            agents (list[str]): Names of agents that will participate in the task; the number of agents influences risk.
        
        Returns:
            ActionRiskLevel: The assessed risk level (`CRITICAL`, `HIGH`, `MEDIUM`, or `LOW`) for the given task.
        """
        task_lower = task_type.lower()

        # Critical operations
        if any(word in task_lower for word in [
            "deploy", "delete", "drop", "modify", "publish"
        ]):
            return ActionRiskLevel.CRITICAL

        # High-risk operations
        if any(word in task_lower for word in [
            "create", "update", "insert", "write", "send", "post"
        ]):
            return ActionRiskLevel.HIGH

        # Check if multiple agents involved (higher risk)
        if len(agents) > 3:
            return ActionRiskLevel.HIGH

        # Medium-risk operations
        if any(word in task_lower for word in [
            "analyze", "process", "calculate", "generate"
        ]):
            return ActionRiskLevel.MEDIUM

        return ActionRiskLevel.LOW

    async def emergency_stop(self, reason: str, operator: str):
        """Emergency stop all operations"""
        self.emergency_stop_active = True
        logger.critical(f"🚨 EMERGENCY STOP by {operator}: {reason}")

        # Stop all wrapped agents
        for agent_name, wrapped_agent in self.wrapped_agents.items():
            wrapped_agent.emergency_shutdown(reason)

        # Cancel all pending tasks
        for task_id, task in self.tasks.items():
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.CANCELLED
                task.error = f"Emergency stop: {reason}"

    async def resume_operations(self, operator: str):
        """Resume operations after emergency stop"""
        if not self.emergency_stop_active:
            return {"error": "No emergency stop active"}

        self.emergency_stop_active = False
        logger.info(f"▶️  Operations resumed by {operator}")

        # Resume all wrapped agents
        for agent_name, wrapped_agent in self.wrapped_agents.items():
            wrapped_agent.resume()

        return {"status": "resumed", "operator": operator}

    async def pause_system(self, operator: str):
        """Pause system operations"""
        self.system_paused = True
        logger.warning(f"⏸️  System paused by {operator}")

        for agent_name, wrapped_agent in self.wrapped_agents.items():
            wrapped_agent.pause()

        return {"status": "paused", "operator": operator}

    async def resume_system(self, operator: str):
        """
        Resume system-wide operations and instruct all wrapped agents to resume.
        
        Parameters:
            operator (str): Name or identifier of the operator performing the resume action.
        
        Returns:
            dict: A dictionary with keys "status" (value "resumed") and "operator" (the provided operator).
        """
        self.system_paused = False
        logger.info(f"▶️  System resumed by {operator}")

        for agent_name, wrapped_agent in self.wrapped_agents.items():
            wrapped_agent.resume()

        return {"status": "resumed", "operator": operator}

    async def get_bounded_status(self) -> dict[str, Any]:
        """
        Retrieve health and bounded-autonomy status for the orchestrator.
        
        The returned mapping merges the base orchestrator health with additional bounded-autonomy details:
        - `bounded_autonomy.system_controls`: current control flags (`emergency_stop`, `paused`, `local_only`, `auto_approve_low_risk`).
        - `bounded_autonomy.wrapped_agents`: per-agent status mappings for every registered wrapped agent.
        - `bounded_autonomy.pending_approvals`: number of approval actions currently pending.
        
        Returns:
            dict[str, Any]: A dictionary containing the base health keys plus a `bounded_autonomy` key with the structure described above.
        """
        base_health = await self.get_orchestrator_health()

        # Add bounded autonomy status
        bounded_status = {
            "system_controls": {
                "emergency_stop": self.emergency_stop_active,
                "paused": self.system_paused,
                "local_only": self.local_only,
                "auto_approve_low_risk": self.auto_approve_low_risk
            },
            "wrapped_agents": {}
        }

        for agent_name, wrapped_agent in self.wrapped_agents.items():
            bounded_status["wrapped_agents"][agent_name] = await wrapped_agent.get_status()

        # Get pending approvals
        pending_actions = await self.approval_system.get_pending_actions()
        bounded_status["pending_approvals"] = len(pending_actions)

        return {
            **base_health,
            "bounded_autonomy": bounded_status
        }

    def _sanitize_for_json(self, data: Any) -> Any:
        """
        Produce a JSON-serializable representation of `data` by removing internal reference keys and converting non-serializable values to strings.
        
        Recursively processes dicts, lists, and tuples. For dicts, keys "_previous_results" and "_shared_context" are omitted; primitive values (str, int, float, bool, None) are preserved; other values are converted to strings.
        
        Parameters:
            data (Any): Input value to sanitize for JSON serialization.
        
        Returns:
            Any: A sanitized, JSON-serializable representation of `data` with internal reference keys removed and non-serializable values converted to strings.
        """
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Skip internal circular reference keys
                if key in ("_previous_results", "_shared_context"):
                    continue
                try:
                    # Recursively sanitize nested structures
                    sanitized[key] = self._sanitize_for_json(value)
                except (TypeError, ValueError):
                    # Skip non-serializable values
                    sanitized[key] = str(value)
            return sanitized
        elif isinstance(data, (list, tuple)):
            return [self._sanitize_for_json(item) for item in data]
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        else:
            # Convert other types to string
            return str(data)