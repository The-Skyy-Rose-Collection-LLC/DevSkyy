"""
Approval System for Bounded Autonomy
Manages human review queue and approval workflows
"""

from datetime import datetime, timedelta
from enum import Enum
import json
import logging
from pathlib import Path
import sqlite3
from typing import Any, Optional

from fashion_ai_bounded_autonomy.i18n_loader import t


logger = logging.getLogger(__name__)


class ApprovalWorkflowType(Enum):
    """Types of approval workflows"""
    DEFAULT = "default"  # Standard 4-step workflow
    HIGH_RISK = "high_risk"  # Enhanced review for risky operations
    EXPEDITED = "expedited"  # Fast-track for urgent low-risk items


class ApprovalSystem:
    """
    Human review queue and approval workflow management.

    Features:
    - SQLite-based review queue
    - Multi-step approval workflows
    - Timeout handling
    - Approval history tracking
    - Operator notification system
    """

    def __init__(self, db_path: str = "fashion_ai_bounded_autonomy/review_queue.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

        logger.info("✅ Approval system initialized")

    def _init_database(self):
        """Initialize SQLite database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Review queue table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS review_queue (
                action_id TEXT PRIMARY KEY,
                agent_name TEXT NOT NULL,
                function_name TEXT NOT NULL,
                parameters TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                workflow_type TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                timeout_at TEXT,
                approved_at TEXT,
                approved_by TEXT,
                rejection_reason TEXT,
                execution_result TEXT
            )
        """)

        # Approval history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approval_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                operator TEXT,
                timestamp TEXT NOT NULL,
                details TEXT,
                FOREIGN KEY (action_id) REFERENCES review_queue (action_id)
            )
        """)

        # Operator activity table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operator_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operator TEXT NOT NULL,
                action TEXT NOT NULL,
                action_id TEXT,
                timestamp TEXT NOT NULL,
                metadata TEXT
            )
        """)

        conn.commit()
        conn.close()

    async def submit_for_review(
        self,
        action_id: str,
        agent_name: str,
        function_name: str,
        parameters: dict[str, Any],
        risk_level: str,
        workflow_type: ApprovalWorkflowType = ApprovalWorkflowType.DEFAULT,
        timeout_hours: int = 24
    ) -> dict[str, Any]:
        """
        Create a pending review entry for the given action and record its submission.
        
        Parameters:
            action_id (str): Unique identifier for the action being submitted.
            agent_name (str): Name of the agent requesting the action.
            function_name (str): Name of the function the action will execute.
            parameters (dict[str, Any]): Parameters that will be passed to the function.
            risk_level (str): Assessed risk level for the action.
            workflow_type (ApprovalWorkflowType): Selected approval workflow that determines the review steps.
            timeout_hours (int): Number of hours until the action expires and can no longer be approved.
        
        Returns:
            dict[str, Any]: Submission metadata containing:
                - "action_id": the submitted action's identifier,
                - "status": submission status (always "submitted"),
                - "workflow": the workflow type value used,
                - "timeout_at": ISO8601 timestamp when the action will expire.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        created_at = datetime.now()
        timeout_at = created_at + timedelta(hours=timeout_hours)

        cursor.execute("""
            INSERT INTO review_queue (
                action_id, agent_name, function_name, parameters,
                risk_level, workflow_type, status, created_at, timeout_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            action_id,
            agent_name,
            function_name,
            json.dumps(parameters),
            risk_level,
            workflow_type.value,
            "pending",
            created_at.isoformat(),
            timeout_at.isoformat()
        ))

        # Log submission event
        cursor.execute("""
            INSERT INTO approval_history (action_id, event_type, timestamp, details)
            VALUES (?, ?, ?, ?)
        """, (
            action_id,
            "submitted",
            datetime.now().isoformat(),
            json.dumps({"workflow": workflow_type.value})
        ))

        conn.commit()
        conn.close()

        logger.info(f"📝 {t('approval.submitted', action_id=action_id, workflow=workflow_type.value)}")

        # Send async notification to operator via Celery
        try:
            from fashion_ai_bounded_autonomy.tasks import send_approval_notification_task
            send_approval_notification_task.delay(action_id, agent_name, risk_level)
        except Exception as e:
            logger.warning(f"{t('approval.notification_failed', error=str(e))}")

        return {
            "action_id": action_id,
            "status": "submitted",
            "workflow": workflow_type.value,
            "timeout_at": timeout_at.isoformat()
        }

    async def approve(
        self,
        action_id: str,
        operator: str,
        notes: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Approve a pending review action and record the approval and operator activity.
        
        Parameters:
            notes (Optional[str]): Optional free-text notes to attach to the approval event.
        
        Returns:
            dict: On success, a dictionary with keys `action_id`, `status` (set to `"approved"`), `approved_by`, and `approved_at` (ISO 8601 string). On failure, a dictionary with an `error` message and a `status` describing the failure (e.g., `"error"` or `"expired"`).
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if action exists and is pending
        cursor.execute("""
            SELECT status, timeout_at FROM review_queue WHERE action_id = ?
        """, (action_id,))

        result = cursor.fetchone()
        if not result:
            conn.close()
            return {"error": "Action not found", "status": "error"}

        status, timeout_at = result

        if status != "pending":
            conn.close()
            return {"error": f"Action is {status}, cannot approve", "status": "error"}

        # Check if timed out
        if datetime.fromisoformat(timeout_at) < datetime.now():
            cursor.execute("""
                UPDATE review_queue SET status = 'expired' WHERE action_id = ?
            """, (action_id,))
            conn.commit()
            conn.close()
            return {"error": "Action has expired", "status": "expired"}

        # Approve
        approved_at = datetime.now()
        cursor.execute("""
            UPDATE review_queue
            SET status = 'approved', approved_at = ?, approved_by = ?
            WHERE action_id = ?
        """, (approved_at.isoformat(), operator, action_id))

        # Log approval
        cursor.execute("""
            INSERT INTO approval_history (action_id, event_type, operator, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
        """, (
            action_id,
            "approved",
            operator,
            approved_at.isoformat(),
            json.dumps({"notes": notes} if notes else {})
        ))

        # Log operator activity
        cursor.execute("""
            INSERT INTO operator_activity (operator, action, action_id, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            operator,
            "approve",
            action_id,
            approved_at.isoformat(),
            json.dumps({"notes": notes} if notes else {})
        ))

        conn.commit()
        conn.close()

        logger.info(f"✅ Action {action_id} approved by {operator}")

        return {
            "action_id": action_id,
            "status": "approved",
            "approved_by": operator,
            "approved_at": approved_at.isoformat()
        }

    async def reject(
        self,
        action_id: str,
        operator: str,
        reason: str
    ) -> dict[str, Any]:
        """
        Mark a pending review action as rejected and record the rejection and operator activity.
        
        Returns:
            dict: On success, a dictionary containing `action_id`, `status` (set to "rejected"), `rejected_by`, and `reason`. If the action does not exist or is not in a pending state, a dictionary with an `error` message and `status` set to `"error"`.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT status FROM review_queue WHERE action_id = ?
        """, (action_id,))

        result = cursor.fetchone()
        if not result:
            conn.close()
            return {"error": "Action not found", "status": "error"}

        status = result[0]
        if status != "pending":
            conn.close()
            return {"error": f"Action is {status}, cannot reject", "status": "error"}

        # Reject
        rejected_at = datetime.now()
        cursor.execute("""
            UPDATE review_queue
            SET status = 'rejected', rejection_reason = ?
            WHERE action_id = ?
        """, (reason, action_id))

        # Log rejection
        cursor.execute("""
            INSERT INTO approval_history (action_id, event_type, operator, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
        """, (
            action_id,
            "rejected",
            operator,
            rejected_at.isoformat(),
            json.dumps({"reason": reason})
        ))

        # Log operator activity
        cursor.execute("""
            INSERT INTO operator_activity (operator, action, action_id, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            operator,
            "reject",
            action_id,
            rejected_at.isoformat(),
            json.dumps({"reason": reason})
        ))

        conn.commit()
        conn.close()

        logger.info(f"⛔ Action {action_id} rejected by {operator}: {reason}")

        return {
            "action_id": action_id,
            "status": "rejected",
            "rejected_by": operator,
            "reason": reason
        }

    async def get_pending_actions(self) -> list[dict[str, Any]]:
        """
        Return a list of actions currently awaiting review.
        
        Each item is a dictionary containing the action's identifiers, metadata and timestamps. The `parameters` field is parsed from JSON into a dict. Results are ordered by creation time (newest first).
        
        Returns:
            list[dict[str, Any]]: List of pending action records with keys:
                - action_id: Unique action identifier.
                - agent_name: Name of the agent that requested the action.
                - function_name: Target function or operation name.
                - parameters: Parsed parameters as a dict.
                - risk_level: Declared risk level for the action.
                - workflow_type: Workflow type assigned to the action.
                - created_at: ISO or stored timestamp when the action was submitted.
                - timeout_at: Timestamp after which the action is considered expired.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT action_id, agent_name, function_name, parameters,
                   risk_level, workflow_type, created_at, timeout_at
            FROM review_queue
            WHERE status = 'pending'
            ORDER BY created_at DESC
        """)

        actions = []
        for row in cursor.fetchall():
            actions.append({
                "action_id": row[0],
                "agent_name": row[1],
                "function_name": row[2],
                "parameters": json.loads(row[3]),
                "risk_level": row[4],
                "workflow_type": row[5],
                "created_at": row[6],
                "timeout_at": row[7]
            })

        conn.close()
        return actions

    async def get_action_details(self, action_id: str) -> Optional[dict[str, Any]]:
        """
        Retrieve a detailed record for a review action, including its stored fields and ordered approval history.
        
        Returns:
            A dict with the action's stored fields (action_id, agent_name, function_name, parameters, risk_level, workflow_type, status, created_at, timeout_at, approved_at, approved_by, rejection_reason, execution_result) and a `history` list of approval events (each with `event`, `operator`, `timestamp`, and parsed `details`), or `None` if no action with `action_id` exists.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM review_queue WHERE action_id = ?
        """, (action_id,))

        result = cursor.fetchone()
        if not result:
            conn.close()
            return None

        # Get approval history
        cursor.execute("""
            SELECT event_type, operator, timestamp, details
            FROM approval_history
            WHERE action_id = ?
            ORDER BY timestamp ASC
        """, (action_id,))

        history = []
        for row in cursor.fetchall():
            history.append({
                "event": row[0],
                "operator": row[1],
                "timestamp": row[2],
                "details": json.loads(row[3]) if row[3] else {}
            })

        conn.close()

        return {
            "action_id": result[0],
            "agent_name": result[1],
            "function_name": result[2],
            "parameters": json.loads(result[3]),
            "risk_level": result[4],
            "workflow_type": result[5],
            "status": result[6],
            "created_at": result[7],
            "timeout_at": result[8],
            "approved_at": result[9],
            "approved_by": result[10],
            "rejection_reason": result[11],
            "execution_result": json.loads(result[12]) if result[12] else None,
            "history": history
        }

    async def mark_executed(self, action_id: str, result: dict[str, Any]) -> bool:
        """
        Mark an approved action as executed and record its execution result.

        This updates the action's status to "executed" only if its current status is "approved"
        and appends an "executed" event to the approval history. The provided `result` is
        serialized and stored as the action's execution result and as the event details.

        Parameters:
            action_id (str): Identifier of the action to mark as executed.
            result (dict): Execution result data to store with the action and history (will be JSON-serialized).

        Returns:
            bool: `True` if the action's status was changed to "executed", `False` otherwise.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE review_queue
            SET status = 'executed', execution_result = ?
            WHERE action_id = ? AND status = 'approved'
        """, (json.dumps(result), action_id))

        # Capture rowcount immediately after UPDATE
        rows_affected = cursor.rowcount

        cursor.execute("""
            INSERT INTO approval_history (action_id, event_type, timestamp, details)
            VALUES (?, ?, ?, ?)
        """, (
            action_id,
            "executed",
            datetime.now().isoformat(),
            json.dumps(result)
        ))

        conn.commit()
        conn.close()

        return rows_affected > 0

    async def cleanup_expired(self) -> int:
        """
        Mark pending review actions whose timeout has passed as expired.
        
        Updates review_queue rows with status 'pending' and timeout_at earlier than the current time to status 'expired' and commits the change.
        
        Returns:
            expired_count (int): Number of actions that were marked expired.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE review_queue
            SET status = 'expired'
            WHERE status = 'pending' AND timeout_at < ?
        """, (now,))

        expired_count = cursor.rowcount
        conn.commit()
        conn.close()

        if expired_count > 0:
            logger.info(f"🕐 Cleaned up {expired_count} expired actions")

        return expired_count

    async def get_operator_statistics(self, operator: Optional[str] = None) -> dict[str, Any]:
        """
        Collect statistics of operator activities recorded in the operator_activity table.
        
        When `operator` is provided, returns a mapping of action name to the number of times that operator performed the action.
        When `operator` is omitted, returns a mapping of operator name to a nested mapping of action name to count.
        
        Parameters:
            operator (Optional[str]): Optional operator identifier to filter statistics for a single operator.
        
        Returns:
            dict: If `operator` is provided, a dict mapping action (str) to count (int).
                  If `operator` is None, a dict mapping operator (str) to dicts of action (str) to count (int).
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if operator:
            cursor.execute("""
                SELECT action, COUNT(*) as count
                FROM operator_activity
                WHERE operator = ?
                GROUP BY action
            """, (operator,))
        else:
            cursor.execute("""
                SELECT operator, action, COUNT(*) as count
                FROM operator_activity
                GROUP BY operator, action
            """)

        stats = {}
        for row in cursor.fetchall():
            if operator:
                stats[row[0]] = row[1]
            else:
                if row[0] not in stats:
                    stats[row[0]] = {}
                stats[row[0]][row[1]] = row[2]

        conn.close()
        return stats