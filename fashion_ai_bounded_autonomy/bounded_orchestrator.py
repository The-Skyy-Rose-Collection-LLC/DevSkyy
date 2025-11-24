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
from typing import Any

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

    def __init__(self, max_concurrent_tasks: int = 50, local_only: bool = True, auto_approve_low_risk: bool = True):
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
        dependencies: list[str] | None = None,
        priority: ExecutionPriority = ExecutionPriority.MEDIUM,
    ) -> bool:
        """
        Register agent with bounded autonomy wrapper.

        Args:
            agent: BaseAgent instance
            capabilities: List of capabilities
            dependencies: Agent dependencies
            priority: Execution priority

        Returns:
            True if registration successful
        """
        # Register with parent orchestrator
        success = await super().register_agent(agent, capabilities, dependencies, priority)

        if not success:
            return False

        # Wrap agent with bounded autonomy controls
        wrapped = BoundedAutonomyWrapper(
            wrapped_agent=agent, auto_approve_low_risk=self.auto_approve_low_risk, local_only=self.local_only
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
        require_approval: bool | None = None,
    ) -> dict[str, Any]:
        """
        Execute task with bounded autonomy controls.

        Args:
            task_type: Task type
            parameters: Task parameters
            required_capabilities: Required capabilities
            priority: Task priority
            require_approval: Override approval requirement

        Returns:
            Task result or approval pending message
        """
        # Check emergency stop
        if self.emergency_stop_active:
            logger.critical("🚨 Emergency stop active - task blocked")
            return {"error": "Emergency stop active", "status": "blocked"}

        # Check if system paused
        if self.system_paused:
            logger.warning("⏸️  System paused - task queued")
            return {"error": "System paused", "status": "queued"}

        task_id = f"task_{datetime.now().timestamp()}_{task_type}"

        # Find agents with required capabilities
        capable_agents = self._find_agents_with_capabilities(required_capabilities)
        if not capable_agents:
            return {"error": f"No agents found with capabilities: {required_capabilities}"}

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
        needs_approval = (
            require_approval
            if require_approval is not None
            else (task_risk in [ActionRiskLevel.HIGH, ActionRiskLevel.CRITICAL])
        )

        if needs_approval:
            # Submit for approval
            await self.approval_system.submit_for_review(
                action_id=task_id,
                agent_name="orchestrator",
                function_name=task_type,
                parameters=parameters,
                risk_level=task_risk.value,
                workflow_type=(
                    ApprovalWorkflowType.HIGH_RISK
                    if task_risk == ActionRiskLevel.CRITICAL
                    else ApprovalWorkflowType.DEFAULT
                ),
            )

            logger.info(f"⏳ Task {task_id} submitted for approval (risk: {task_risk.value})")

            return {
                "status": "pending_approval",
                "task_id": task_id,
                "risk_level": task_risk.value,
                "message": "Task submitted for operator review",
                "review_command": f"python -m fashion_ai_bounded_autonomy.approval_cli review {task_id}",
            }

        # Execute immediately
        return await self._execute_bounded_task(task)

    async def execute_approved_task(self, task_id: str, approved_by: str) -> dict[str, Any]:
        """
        Execute a task that has been approved.

        Args:
            task_id: Task ID to execute
            approved_by: Operator who approved

        Returns:
            Execution result
        """
        if task_id not in self.tasks:
            return {"error": "Task not found", "status": "error"}

        task = self.tasks[task_id]

        logger.info(f"▶️  Executing approved task {task_id} (approved by {approved_by})")

        result = await self._execute_bounded_task(task)

        # Mark as executed in approval system
        await self.approval_system.mark_executed(task_id, result)

        return result

    async def _execute_bounded_task(self, task: AgentTask) -> dict[str, Any]:
        """Execute task through bounded agents"""
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
                        require_approval=False,  # Already approved at task level
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
                        error_msg = (
                            result.get("error", "Non-completed status")
                            if isinstance(result, dict)
                            else "Invalid result"
                        )
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

    def _assess_task_risk(self, task_type: str, parameters: dict[str, Any], agents: list[str]) -> ActionRiskLevel:
        """Assess overall risk level of a task"""
        task_lower = task_type.lower()

        # Critical operations
        if any(word in task_lower for word in ["deploy", "delete", "drop", "modify", "publish"]):
            return ActionRiskLevel.CRITICAL

        # High-risk operations
        if any(word in task_lower for word in ["create", "update", "insert", "write", "send", "post"]):
            return ActionRiskLevel.HIGH

        # Check if multiple agents involved (higher risk)
        if len(agents) > 3:
            return ActionRiskLevel.HIGH

        # Medium-risk operations
        if any(word in task_lower for word in ["analyze", "process", "calculate", "generate"]):
            return ActionRiskLevel.MEDIUM

        return ActionRiskLevel.LOW

    async def emergency_stop(self, reason: str, operator: str):
        """Emergency stop all operations"""
        self.emergency_stop_active = True
        logger.critical(f"🚨 EMERGENCY STOP by {operator}: {reason}")

        # Stop all wrapped agents
        for wrapped_agent in self.wrapped_agents.values():
            wrapped_agent.emergency_shutdown(reason)

        # Cancel all pending tasks
        for task in self.tasks.values():
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
        for wrapped_agent in self.wrapped_agents.values():
            wrapped_agent.resume()

        return {"status": "resumed", "operator": operator}

    async def pause_system(self, operator: str):
        """Pause system operations"""
        self.system_paused = True
        logger.warning(f"⏸️  System paused by {operator}")

        for wrapped_agent in self.wrapped_agents.values():
            wrapped_agent.pause()

        return {"status": "paused", "operator": operator}

    async def resume_system(self, operator: str):
        """Resume system operations"""
        self.system_paused = False
        logger.info(f"▶️  System resumed by {operator}")

        for wrapped_agent in self.wrapped_agents.values():
            wrapped_agent.resume()

        return {"status": "resumed", "operator": operator}

    async def get_bounded_status(self) -> dict[str, Any]:
        """Get bounded orchestrator status"""
        base_health = await self.get_orchestrator_health()

        # Add bounded autonomy status
        bounded_status = {
            "system_controls": {
                "emergency_stop": self.emergency_stop_active,
                "paused": self.system_paused,
                "local_only": self.local_only,
                "auto_approve_low_risk": self.auto_approve_low_risk,
            },
            "wrapped_agents": {},
        }

        for agent_name, wrapped_agent in self.wrapped_agents.items():
            bounded_status["wrapped_agents"][agent_name] = await wrapped_agent.get_status()

        # Get pending approvals
        pending_actions = await self.approval_system.get_pending_actions()
        bounded_status["pending_approvals"] = len(pending_actions)

        return {**base_health, "bounded_autonomy": bounded_status}
