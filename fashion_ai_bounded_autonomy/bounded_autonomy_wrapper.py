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
from typing import Any, Optional

from agent.modules.base_agent import BaseAgent
from fashion_ai_bounded_autonomy.i18n_loader import t


logger = logging.getLogger(__name__)


class ActionRiskLevel(Enum):
    """Risk classification for agent actions"""
    LOW = "low"  # Read-only operations, queries
    MEDIUM = "medium"  # Data analysis, recommendations
    HIGH = "high"  # Data modifications, external calls
    CRITICAL = "critical"  # System changes, deployments

    @property
    def priority(self) -> int:
        """
        Get numeric priority used to order risk levels.
        
        Returns:
            int: Priority value where 1 = LOW, 2 = MEDIUM, 3 = HIGH, 4 = CRITICAL.
        """
        priorities = {
            ActionRiskLevel.LOW: 1,
            ActionRiskLevel.MEDIUM: 2,
            ActionRiskLevel.HIGH: 3,
            ActionRiskLevel.CRITICAL: 4
        }
        return priorities[self]

    def __lt__(self, other):
        """
        Compare the numeric priority of this ActionRiskLevel with another.
        
        Parameters:
            other (ActionRiskLevel): The ActionRiskLevel to compare against.
        
        Returns:
            bool or NotImplemented: `True` if this level's priority is less than `other`'s priority, `False` otherwise; returns `NotImplemented` if `other` is not an ActionRiskLevel.
        """
        if not isinstance(other, ActionRiskLevel):
            return NotImplemented
        return self.priority < other.priority

    def __le__(self, other):
        """
        Compare this risk level to another by their numeric priority.
        
        Parameters:
            other (ActionRiskLevel): The risk level to compare against.
        
        Returns:
            bool or NotImplemented: `True` if this level's priority is less than or equal to `other`'s priority, `False` otherwise. Returns `NotImplemented` if `other` is not an ActionRiskLevel.
        """
        if not isinstance(other, ActionRiskLevel):
            return NotImplemented
        return self.priority <= other.priority

    def __gt__(self, other):
        """
        Determine whether this risk level is greater than another based on numeric priority.
        
        @returns:
            `True` if this risk level's priority is greater than `other`'s priority, `False` otherwise.
        """
        if not isinstance(other, ActionRiskLevel):
            return NotImplemented
        return self.priority > other.priority

    def __ge__(self, other):
        """
        Return whether this risk level is greater than or equal to another risk level.
        
        Parameters:
            other (ActionRiskLevel): The risk level to compare against.
        
        Returns:
            `True` if this level's priority is greater than or equal to `other`'s priority, `False` otherwise; returns `NotImplemented` if `other` is not an ActionRiskLevel.
        """
        if not isinstance(other, ActionRiskLevel):
            return NotImplemented
        return self.priority >= other.priority


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
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    executed_at: Optional[datetime] = None
    result: Optional[dict[str, Any]] = None
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
        audit_log_path: str = "logs/audit/"
    ):
        """
        Initialize the BoundedAutonomyWrapper and prepare its runtime state.
        
        Parameters:
            wrapped_agent (BaseAgent): Agent instance to be wrapped and controlled.
            auto_approve_low_risk (bool): If True, actions assessed as LOW risk are auto-approved.
            local_only (bool): If True, network-involving actions will be blocked to enforce local-only execution.
            audit_log_path (str): Filesystem path where persistent audit logs and review queue files will be stored.
        
        Description:
            Creates internal structures for pending and completed actions, operator controls (emergency stop, pause),
            and counters for network call observations. Ensures the audit log directory exists and logs initialization.
        """
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

        logger.info(
            f"🔒 Bounded autonomy wrapper initialized for {wrapped_agent.agent_name}"
        )

    async def execute(
        self,
        function_name: str,
        parameters: dict[str, Any],
        require_approval: Optional[bool] = None
    ) -> dict[str, Any]:
        """
        Create and (when permitted) execute a bounded-autonomy action for the wrapped agent.
        
        Parameters:
            function_name (str): Name of the wrapped agent function to invoke.
            parameters (dict[str, Any]): Keyword arguments passed to the function.
            require_approval (Optional[bool]): If not None, override automatic approval decision (True requires manual approval, False bypasses approval).
        
        Returns:
            dict[str, Any]: A status dictionary. Possible shapes:
              - Emergency/paused: {"status": "blocked"|"queued", "error": "<reason>"}.
              - Pending approval: {"status": "pending_approval", "action_id": str, "risk_level": str, "message": str, "review_command": str}.
              - Execution outcome: {"status": "completed"|"failed", "action_id": str, "result": dict, "execution_time_seconds": float} or {"status": "failed", "action_id": str, "error": str}.
        """
        # Check emergency stop
        if self.emergency_stop:
            logger.error("🛑 Emergency stop active - operation blocked")
            return {
                "error": "Emergency stop active",
                "status": "blocked"
            }

        # Check if paused
        if self.paused:
            logger.warning("⏸️  Agent paused - operation queued")
            return {
                "error": "Agent paused",
                "status": "queued"
            }

        # Create bounded action
        action = BoundedAction(
            action_id=self._generate_action_id(),
            agent_name=self.wrapped_agent.agent_name,
            function_name=function_name,
            parameters=parameters,
            risk_level=self._assess_risk(function_name, parameters),
            requires_approval=self._requires_approval(
                function_name, parameters, require_approval
            )
        )

        # Audit log
        self._audit_log(action, "action_created")

        # Check if approval needed
        if action.requires_approval:
            self.pending_actions[action.action_id] = action
            logger.info(
                f"⏳ Action {action.action_id} requires approval (risk: {action.risk_level.value})"
            )

            # Write to review queue
            await self._write_to_review_queue(action)

            return {
                "status": "pending_approval",
                "action_id": action.action_id,
                "risk_level": action.risk_level.value,
                "message": "Action submitted for operator review",
                "review_command": f"python -m fashion_ai_bounded_autonomy.approval_cli review {action.action_id}"
            }

        # Execute immediately for low-risk actions
        return await self._execute_action(action)

    async def _execute_action(self, action: BoundedAction) -> dict[str, Any]:
        """
        Execute a BoundedAction by invoking the corresponding method on the wrapped agent and record audit and execution details.
        
        Parameters:
            action (BoundedAction): Action to execute, containing function_name, parameters, and metadata used for auditing and recording results.
        
        Returns:
            dict[str, Any]: Result object with one of:
                - Completed: {"status": "completed", "action_id": str, "result": Any, "execution_time_seconds": float}
                - Blocked (network isolation): {"error": "Network calls blocked in local-only mode", "status": "blocked"}
                - Missing function: {"error": "Function <name> not found", "status": "error"}
                - Failed execution: {"status": "failed", "action_id": str, "error": str}
        """
        try:
            # Network isolation check
            if self.local_only and self._involves_network_call(action):
                self.network_calls_blocked += 1
                self._audit_log(action, "network_call_blocked")
                return {
                    "error": "Network calls blocked in local-only mode",
                    "status": "blocked"
                }

            action.executed_at = datetime.now()
            self._audit_log(action, "execution_started")

            # Get the function from wrapped agent
            if not hasattr(self.wrapped_agent, action.function_name):
                return {
                    "error": f"Function {action.function_name} not found",
                    "status": "error"
                }

            func = getattr(self.wrapped_agent, action.function_name)

            # Execute with resource monitoring
            start_time = datetime.now()
            result = await func(**action.parameters)
            execution_time = (datetime.now() - start_time).total_seconds()

            # Record result
            action.result = result
            action.audit_trail.append({
                "event": "execution_completed",
                "timestamp": datetime.now().isoformat(),
                "execution_time_seconds": execution_time
            })

            self.completed_actions.append(action)
            self._audit_log(action, "execution_completed", {"execution_time": execution_time})

            logger.info(
                f"✅ Action {action.action_id} completed in {execution_time:.2f}s"
            )

            return {
                "status": "completed",
                "action_id": action.action_id,
                "result": result,
                "execution_time_seconds": execution_time
            }

        except Exception as e:
            logger.error(f"❌ Action {action.action_id} failed: {e!s}")
            action.audit_trail.append({
                "event": "execution_failed",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            })
            self._audit_log(action, "execution_failed", {"error": str(e)})

            return {
                "status": "failed",
                "action_id": action.action_id,
                "error": str(e)
            }

    async def approve_action(self, action_id: str, approved_by: str) -> dict[str, Any]:
        """
        Approve a pending BoundedAction and execute it.
        
        Parameters:
            action_id (str): Identifier of the pending action to approve.
            approved_by (str): Identifier of the approver.
        
        Returns:
            dict[str, Any]: Execution result of the action after approval, or an error dict (e.g., {"error": "Action not found", "status": "error"}) if the action was not pending.
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
        """
        Mark a pending bounded action as rejected and record the rejection in the audit trail.
        
        Parameters:
            action_id (str): Identifier of the pending action to reject.
            rejected_by (str): Identifier of the user or system that rejected the action.
            reason (str): Human-readable reason for the rejection.
        
        Returns:
            dict[str, Any]: If the action was found and rejected, returns
                {"status": "rejected", "action_id": action_id, "reason": reason}.
                If no matching pending action exists, returns
                {"error": "Action not found", "status": "error"}.
        """
        if action_id not in self.pending_actions:
            return {"error": "Action not found", "status": "error"}

        action = self.pending_actions[action_id]
        action.approval_status = ApprovalStatus.REJECTED

        self._audit_log(
            action,
            "action_rejected",
            {"rejected_by": rejected_by, "reason": reason}
        )

        # Remove from pending
        del self.pending_actions[action_id]

        logger.info(f"⛔ Action {action_id} rejected by {rejected_by}: {reason}")

        return {
            "status": "rejected",
            "action_id": action_id,
            "reason": reason
        }

    def _assess_risk(self, function_name: str, parameters: dict[str, Any]) -> ActionRiskLevel:
        """
        Determine the ActionRiskLevel for an action based on keywords found in the function name.
        
        Inspects the lowercased `function_name` for keywords associated with risk categories:
        CRITICAL for deployment/destructive/config modifications, HIGH for create/update/write/send operations,
        MEDIUM for analysis/generation operations, and LOW otherwise.
        
        Returns:
            ActionRiskLevel: The assessed risk level for the action.
        """
        function_lower = function_name.lower()

        # Critical operations
        if any(word in function_lower for word in [
            "deploy", "delete", "drop", "truncate", "modify_config"
        ]):
            return ActionRiskLevel.CRITICAL

        # High-risk operations
        if any(word in function_lower for word in [
            "create", "update", "insert", "write", "send", "post", "publish"
        ]):
            return ActionRiskLevel.HIGH

        # Medium-risk operations
        if any(word in function_lower for word in [
            "analyze", "process", "calculate", "generate", "predict"
        ]):
            return ActionRiskLevel.MEDIUM

        # Default to low risk (read operations)
        return ActionRiskLevel.LOW

    def _requires_approval(
        self,
        function_name: str,
        parameters: dict[str, Any],
        override: Optional[bool]
    ) -> bool:
        """
        Decide whether the given action must be approved before execution.
        
        If `override` is not None, its boolean value is returned. Otherwise the action's assessed risk determines approval: low-risk actions are not required when `auto_approve_low_risk` is enabled; medium, high, or critical risk actions require approval.
        
        Parameters:
        	function_name (str): Name of the function to be executed.
        	parameters (dict[str, Any]): Parameters that will be passed to the function.
        	override (Optional[bool]): Explicit override of approval requirement; when provided, takes precedence.
        
        Returns:
        	bool: `True` if the action requires human approval, `False` otherwise.
        """
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
            "api", "http", "fetch", "download", "upload", "external",
            "webhook", "request", "post", "get", "put", "delete"
        ]
        return any(
            keyword in action.function_name.lower()
            for keyword in network_keywords
        )

    def _generate_action_id(self) -> str:
        """Generate unique action ID"""
        import uuid
        return f"{self.wrapped_agent.agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    def _audit_log(
        self,
        action: BoundedAction,
        event: str,
        metadata: Optional[dict[str, Any]] = None
    ):
        """
        Append a timestamped audit entry for the given action to its in-memory audit trail and persist the entry to the daily JSONL audit file.
        
        Parameters:
            action (BoundedAction): The action being audited; the created entry is appended to its `audit_trail`.
            event (str): A short label for the audit event (e.g., "action_created", "execution_started", "execution_failed").
            metadata (Optional[dict[str, Any]]): Optional additional context to include in the audit entry.
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_id": action.action_id,
            "agent_name": action.agent_name,
            "function_name": action.function_name,
            "event": event,
            "risk_level": action.risk_level.value,
            "approval_status": action.approval_status.value,
            "metadata": metadata or {}
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

        queue.append({
            "action_id": action.action_id,
            "agent_name": action.agent_name,
            "function_name": action.function_name,
            "parameters": action.parameters,
            "risk_level": action.risk_level.value,
            "created_at": action.created_at.isoformat(),
            "status": action.approval_status.value
        })

        with open(queue_file, "w") as f:
            json.dump(queue, f, indent=2)

    def emergency_shutdown(self, reason: str):
        """Emergency stop all operations"""
        self.emergency_stop = True
        logger.critical(f"🚨 EMERGENCY STOP ACTIVATED: {reason}")

        # Audit log emergency stop
        for action_id, action in self.pending_actions.items():
            self._audit_log(
                action,
                "emergency_stop",
                {"reason": reason}
            )

    def pause(self):
        """Pause agent operations"""
        self.paused = True
        logger.warning(f"⏸️  Agent {self.wrapped_agent.agent_name} paused")

    def resume(self):
        """Resume agent operations"""
        self.paused = False
        logger.info(f"▶️  Agent {self.wrapped_agent.agent_name} resumed")

    async def get_status(self) -> dict[str, Any]:
        """
        Return a snapshot of the wrapper's operational status.
        
        Returns:
            dict[str, Any]: A status dictionary with the following keys:
                - agent_name (str): Name of the wrapped agent.
                - wrapped_agent_status (Any): Health/status value returned by the wrapped agent's health_check().
                - bounded_controls (dict): Current control flags:
                    - emergency_stop (bool)
                    - paused (bool)
                    - local_only (bool)
                    - auto_approve_low_risk (bool)
                - actions (dict): Action counts:
                    - pending (int): Number of actions awaiting approval.
                    - completed (int): Number of actions that have finished.
                - network (dict): Network call counters:
                    - calls_blocked (int)
                    - calls_allowed (int)
        """
        return {
            "agent_name": self.wrapped_agent.agent_name,
            "wrapped_agent_status": await self.wrapped_agent.health_check(),
            "bounded_controls": {
                "emergency_stop": self.emergency_stop,
                "paused": self.paused,
                "local_only": self.local_only,
                "auto_approve_low_risk": self.auto_approve_low_risk
            },
            "actions": {
                "pending": len(self.pending_actions),
                "completed": len(self.completed_actions)
            },
            "network": {
                "calls_blocked": self.network_calls_blocked,
                "calls_allowed": self.network_calls_allowed
            }
        }