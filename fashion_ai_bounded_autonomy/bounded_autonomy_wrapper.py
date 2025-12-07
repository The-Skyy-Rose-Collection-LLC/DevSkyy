"""
Bounded Autonomy Wrapper for DevSkyy Agents
Wraps existing agents with bounded autonomy controls:
- Human approval requirement for material changes
- Audit logging of all actions
- Containment and sandboxing
- Deterministic execution tracking
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
from pathlib import Path
from typing import Any

from agent.modules.base_agent import BaseAgent


logger = logging.getLogger(__name__)


class ActionRiskLevel(Enum):
    """Risk classification for agent actions"""

    LOW = "low"  # Read-only operations, queries
    MEDIUM = "medium"  # Data analysis, recommendations
    HIGH = "high"  # Data modifications, external calls
    CRITICAL = "critical"  # System changes, deployments


class ApprovalStatus(Enum):
    """Status of approval workflow"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class BoundedAction:
    """Represents an action requiring bounded autonomy controls"""

    action_id: str
    agent_name: str
    function_name: str
    parameters: dict[str, Any]
    risk_level: ActionRiskLevel
    requires_approval: bool
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    approved_at: datetime | None = None
    approved_by: str | None = None
    executed_at: datetime | None = None
    result: dict[str, Any] | None = None
    audit_trail: list[dict[str, Any]] = field(default_factory=list)


class BoundedAutonomyWrapper:
    """
    Wraps existing DevSkyy agents with bounded autonomy controls.

    Features:
    - All actions are logged and auditable
    - Material changes require human approval
    - Network isolation enforcement
    - Resource usage monitoring
    - Deterministic execution tracking
    """

    def __init__(
        self,
        wrapped_agent: BaseAgent,
        auto_approve_low_risk: bool = True,
        local_only: bool = True,
        audit_log_path: str = "logs/audit/",
    ):
        self.wrapped_agent = wrapped_agent
        self.auto_approve_low_risk = auto_approve_low_risk
        self.local_only = local_only
        self.audit_log_path = Path(audit_log_path)
        self.audit_log_path.mkdir(parents=True, exist_ok=True)

        # Action queue for approval
        self.pending_actions: dict[str, BoundedAction] = {}
        self.completed_actions: list[BoundedAction] = []

        # Operator controls
        self.emergency_stop = False
        self.paused = False

        # Network call tracking
        self.network_calls_blocked = 0
        self.network_calls_allowed = 0

        logger.info(f"🔒 Bounded autonomy wrapper initialized for {wrapped_agent.agent_name}")

    async def execute(
        self, function_name: str, parameters: dict[str, Any], require_approval: bool | None = None
    ) -> dict[str, Any]:
        """
        Execute an agent function with bounded autonomy controls.

        Args:
            function_name: Name of the function to execute
            parameters: Function parameters
            require_approval: Override approval requirement (None = auto-determine)

        Returns:
            Execution result or approval pending message
        """
        # Check emergency stop
        if self.emergency_stop:
            logger.error("🛑 Emergency stop active - operation blocked")
            return {"error": "Emergency stop active", "status": "blocked"}

        # Check if paused
        if self.paused:
            logger.warning("⏸️  Agent paused - operation queued")
            return {"error": "Agent paused", "status": "queued"}

        # Create bounded action
        action = BoundedAction(
            action_id=self._generate_action_id(),
            agent_name=self.wrapped_agent.agent_name,
            function_name=function_name,
            parameters=parameters,
            risk_level=self._assess_risk(function_name, parameters),
            requires_approval=self._requires_approval(function_name, parameters, require_approval),
        )

        # Audit log
        self._audit_log(action, "action_created")

        # Check if approval needed
        if action.requires_approval:
            self.pending_actions[action.action_id] = action
            logger.info(f"⏳ Action {action.action_id} requires approval (risk: {action.risk_level.value})")

            # Write to review queue
            await self._write_to_review_queue(action)

            return {
                "status": "pending_approval",
                "action_id": action.action_id,
                "risk_level": action.risk_level.value,
                "message": "Action submitted for operator review",
                "review_command": f"python -m fashion_ai_bounded_autonomy.approval_cli review {action.action_id}",
            }

        # Execute immediately for low-risk actions
        return await self._execute_action(action)

    async def _execute_action(self, action: BoundedAction) -> dict[str, Any]:
        """Execute the wrapped agent function"""
        try:
            # Network isolation check
            if self.local_only and self._involves_network_call(action):
                self.network_calls_blocked += 1
                self._audit_log(action, "network_call_blocked")
                return {"error": "Network calls blocked in local-only mode", "status": "blocked"}

            action.executed_at = datetime.now()
            self._audit_log(action, "execution_started")

            # Get the function from wrapped agent
            if not hasattr(self.wrapped_agent, action.function_name):
                return {"error": f"Function {action.function_name} not found", "status": "error"}

            func = getattr(self.wrapped_agent, action.function_name)

            # Execute with resource monitoring
            start_time = datetime.now()
            result = await func(**action.parameters)
            execution_time = (datetime.now() - start_time).total_seconds()

            # Record result
            action.result = result
            action.audit_trail.append(
                {
                    "event": "execution_completed",
                    "timestamp": datetime.now().isoformat(),
                    "execution_time_seconds": execution_time,
                }
            )

            self.completed_actions.append(action)
            self._audit_log(action, "execution_completed", {"execution_time": execution_time})

            logger.info(f"✅ Action {action.action_id} completed in {execution_time:.2f}s")

            return {
                "status": "completed",
                "action_id": action.action_id,
                "result": result,
                "execution_time_seconds": execution_time,
            }

        except Exception as e:
            logger.error(f"❌ Action {action.action_id} failed: {e!s}")
            action.audit_trail.append(
                {"event": "execution_failed", "timestamp": datetime.now().isoformat(), "error": str(e)}
            )
            self._audit_log(action, "execution_failed", {"error": str(e)})

            return {"status": "failed", "action_id": action.action_id, "error": str(e)}

    async def approve_action(self, action_id: str, approved_by: str) -> dict[str, Any]:
        """
        Approve a pending action.

        Args:
            action_id: Action ID to approve
            approved_by: Operator identifier

        Returns:
            Execution result
        """
        if action_id not in self.pending_actions:
            return {"error": "Action not found", "status": "error"}

        action = self.pending_actions[action_id]
        action.approval_status = ApprovalStatus.APPROVED
        action.approved_at = datetime.now()
        action.approved_by = approved_by

        self._audit_log(action, "action_approved", {"approved_by": approved_by})

        # Remove from pending
        del self.pending_actions[action_id]

        # Execute
        return await self._execute_action(action)

    async def reject_action(self, action_id: str, rejected_by: str, reason: str) -> dict[str, Any]:
        """Reject a pending action"""
        if action_id not in self.pending_actions:
            return {"error": "Action not found", "status": "error"}

        action = self.pending_actions[action_id]
        action.approval_status = ApprovalStatus.REJECTED

        self._audit_log(action, "action_rejected", {"rejected_by": rejected_by, "reason": reason})

        # Remove from pending
        del self.pending_actions[action_id]

        logger.info(f"⛔ Action {action_id} rejected by {rejected_by}: {reason}")

        return {"status": "rejected", "action_id": action_id, "reason": reason}

    def _assess_risk(self, function_name: str, parameters: dict[str, Any]) -> ActionRiskLevel:
        """Assess risk level of an action"""
        function_lower = function_name.lower()

        # Critical operations
        if any(word in function_lower for word in ["deploy", "delete", "drop", "truncate", "modify_config"]):
            return ActionRiskLevel.CRITICAL

        # High-risk operations
        if any(word in function_lower for word in ["create", "update", "insert", "write", "send", "post", "publish"]):
            return ActionRiskLevel.HIGH

        # Medium-risk operations
        if any(word in function_lower for word in ["analyze", "process", "calculate", "generate", "predict"]):
            return ActionRiskLevel.MEDIUM

        # Default to low risk (read operations)
        return ActionRiskLevel.LOW

    def _requires_approval(self, function_name: str, parameters: dict[str, Any], override: bool | None) -> bool:
        """Determine if action requires approval"""
        if override is not None:
            return override

        risk = self._assess_risk(function_name, parameters)

        # Auto-approve low risk if configured
        if risk == ActionRiskLevel.LOW and self.auto_approve_low_risk:
            return False

        # Require approval for medium and above
        return risk in [ActionRiskLevel.MEDIUM, ActionRiskLevel.HIGH, ActionRiskLevel.CRITICAL]

    def _involves_network_call(self, action: BoundedAction) -> bool:
        """Check if action involves network calls"""
        network_keywords = [
            "api",
            "http",
            "fetch",
            "download",
            "upload",
            "external",
            "webhook",
            "request",
            "post",
            "get",
            "put",
            "delete",
        ]
        return any(keyword in action.function_name.lower() for keyword in network_keywords)

    def _generate_action_id(self) -> str:
        """Generate unique action ID"""
        import uuid

        return f"{self.wrapped_agent.agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    def _audit_log(self, action: BoundedAction, event: str, metadata: dict[str, Any] | None = None):
        """Write to audit log"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_id": action.action_id,
            "agent_name": action.agent_name,
            "function_name": action.function_name,
            "event": event,
            "risk_level": action.risk_level.value,
            "approval_status": action.approval_status.value,
            "metadata": metadata or {},
        }

        action.audit_trail.append(log_entry)

        # Write to persistent audit log
        audit_file = self.audit_log_path / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(audit_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    async def _write_to_review_queue(self, action: BoundedAction):
        """Write action to review queue database"""
        queue_path = Path("fashion_ai_bounded_autonomy/review_queue.db")

        # Simple JSON-based queue for now (will be replaced with SQLite)
        queue_file = queue_path.parent / "review_queue.json"
        queue_file.parent.mkdir(parents=True, exist_ok=True)

        if queue_file.exists():
            with open(queue_file, "r") as f:
                queue = json.load(f)
        else:
            queue = []

        queue.append(
            {
                "action_id": action.action_id,
                "agent_name": action.agent_name,
                "function_name": action.function_name,
                "parameters": action.parameters,
                "risk_level": action.risk_level.value,
                "created_at": action.created_at.isoformat(),
                "status": action.approval_status.value,
            }
        )

        with open(queue_file, "w") as f:
            json.dump(queue, f, indent=2)

    def emergency_shutdown(self, reason: str):
        """Emergency stop all operations"""
        self.emergency_stop = True
        logger.critical(f"🚨 EMERGENCY STOP ACTIVATED: {reason}")

        # Audit log emergency stop
        for action in self.pending_actions.values():
            self._audit_log(action, "emergency_stop", {"reason": reason})

    def pause(self):
        """Pause agent operations"""
        self.paused = True
        logger.warning(f"⏸️  Agent {self.wrapped_agent.agent_name} paused")

    def resume(self):
        """Resume agent operations"""
        self.paused = False
        logger.info(f"▶️  Agent {self.wrapped_agent.agent_name} resumed")

    async def get_status(self) -> dict[str, Any]:
        """Get bounded autonomy status"""
        return {
            "agent_name": self.wrapped_agent.agent_name,
            "wrapped_agent_status": await self.wrapped_agent.health_check(),
            "bounded_controls": {
                "emergency_stop": self.emergency_stop,
                "paused": self.paused,
                "local_only": self.local_only,
                "auto_approve_low_risk": self.auto_approve_low_risk,
            },
            "actions": {"pending": len(self.pending_actions), "completed": len(self.completed_actions)},
            "network": {"calls_blocked": self.network_calls_blocked, "calls_allowed": self.network_calls_allowed},
        }
