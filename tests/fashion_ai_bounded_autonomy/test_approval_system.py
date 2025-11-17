"""
Unit tests for ApprovalSystem
Tests human review queue and approval workflow management
"""

from datetime import datetime, timedelta
from pathlib import Path
import shutil
import sqlite3
import tempfile

import pytest

from fashion_ai_bounded_autonomy.approval_system import ApprovalSystem, ApprovalWorkflowType


@pytest.fixture
def temp_db_path():
    """Create temporary database path"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_review_queue.db"
    yield str(db_path)
    shutil.rmtree(temp_dir)


@pytest.fixture
def approval_system(temp_db_path):
    """Create ApprovalSystem instance with temporary database"""
    return ApprovalSystem(db_path=temp_db_path)


class TestApprovalSystemInitialization:
    """Test ApprovalSystem initialization"""

    def test_init_creates_database(self, temp_db_path):
        """Test that initialization creates database file"""
        ApprovalSystem(db_path=temp_db_path)
        assert Path(temp_db_path).exists()

    def test_init_creates_tables(self, temp_db_path):
        """Test that initialization creates required tables"""
        ApprovalSystem(db_path=temp_db_path)
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Check review_queue table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='review_queue'")
        assert cursor.fetchone() is not None

        # Check approval_history table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='approval_history'")
        assert cursor.fetchone() is not None

        # Check operator_activity table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='operator_activity'")
        assert cursor.fetchone() is not None

        conn.close()

    def test_init_creates_parent_directory(self, temp_db_path):
        """Test that initialization creates parent directories"""
        nested_path = str(Path(temp_db_path).parent / "nested" / "path" / "review_queue.db")
        ApprovalSystem(db_path=nested_path)
        assert Path(nested_path).parent.exists()


class TestSubmitForReview:
    """Test submitting actions for review"""

    @pytest.mark.asyncio
    async def test_submit_action_basic(self, approval_system):
        """Test basic action submission"""
        result = await approval_system.submit_for_review(
            action_id="test_action_001",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1"},
            risk_level="medium",
        )

        assert result["action_id"] == "test_action_001"
        assert result["status"] == "submitted"
        assert result["workflow"] == "default"
        assert "timeout_at" in result

    @pytest.mark.asyncio
    async def test_submit_action_with_custom_workflow(self, approval_system):
        """Test submission with custom workflow type"""
        result = await approval_system.submit_for_review(
            action_id="test_action_002",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1"},
            risk_level="critical",
            workflow_type=ApprovalWorkflowType.HIGH_RISK,
        )

        assert result["workflow"] == "high_risk"

    @pytest.mark.asyncio
    async def test_submit_action_with_custom_timeout(self, approval_system):
        """Test submission with custom timeout"""
        result = await approval_system.submit_for_review(
            action_id="test_action_003",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1"},
            risk_level="low",
            timeout_hours=48,
        )

        timeout_at = datetime.fromisoformat(result["timeout_at"])
        created_at = datetime.now()
        time_diff = (timeout_at - created_at).total_seconds() / 3600

        assert 47 <= time_diff <= 49  # Allow for timing variations

    @pytest.mark.asyncio
    async def test_submit_action_creates_history_entry(self, approval_system):
        """Test that submission creates history entry"""
        await approval_system.submit_for_review(
            action_id="test_action_004",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1"},
            risk_level="medium",
        )

        details = await approval_system.get_action_details("test_action_004")
        assert len(details["history"]) == 1
        assert details["history"][0]["event"] == "submitted"


class TestApproveAction:
    """Test approving actions"""

    @pytest.mark.asyncio
    async def test_approve_pending_action(self, approval_system):
        """Test approving a pending action"""
        # Submit action
        await approval_system.submit_for_review(
            action_id="test_action_005",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1"},
            risk_level="medium",
        )

        # Approve action
        result = await approval_system.approve(
            action_id="test_action_005", operator="test_operator", notes="Test approval"
        )

        assert result["action_id"] == "test_action_005"
        assert result["status"] == "approved"
        assert result["approved_by"] == "test_operator"
        assert "approved_at" in result

    @pytest.mark.asyncio
    async def test_approve_nonexistent_action(self, approval_system):
        """Test approving non-existent action returns error"""
        result = await approval_system.approve(action_id="nonexistent_action", operator="test_operator")

        assert "error" in result
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_approve_already_approved_action(self, approval_system):
        """Test approving already approved action returns error"""
        # Submit and approve action
        await approval_system.submit_for_review(
            action_id="test_action_006",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1"},
            risk_level="medium",
        )
        await approval_system.approve(action_id="test_action_006", operator="test_operator")

        # Try to approve again
        result = await approval_system.approve(action_id="test_action_006", operator="test_operator")

        assert "error" in result
        assert "approved" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_approve_expired_action(self, approval_system, temp_db_path):
        """Test approving expired action returns error"""
        # Submit action
        await approval_system.submit_for_review(
            action_id="test_action_007",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1"},
            risk_level="medium",
            timeout_hours=0,  # Immediate expiry
        )

        # Manually set timeout to past
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        past_time = (datetime.now() - timedelta(hours=1)).isoformat()
        cursor.execute("UPDATE review_queue SET timeout_at = ? WHERE action_id = ?", (past_time, "test_action_007"))
        conn.commit()
        conn.close()

        # Try to approve
        result = await approval_system.approve(action_id="test_action_007", operator="test_operator")

        assert result["status"] == "expired"

    @pytest.mark.asyncio
    async def test_approve_creates_operator_activity(self, approval_system, temp_db_path):
        """Test that approval creates operator activity record"""
        await approval_system.submit_for_review(
            action_id="test_action_008",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1"},
            risk_level="medium",
        )

        await approval_system.approve(action_id="test_action_008", operator="test_operator")

        # Check operator activity
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM operator_activity WHERE action_id = ?", ("test_action_008",))
        activity = cursor.fetchone()
        conn.close()

        assert activity is not None


class TestRejectAction:
    """Test rejecting actions"""

    @pytest.mark.asyncio
    async def test_reject_pending_action(self, approval_system):
        """Test rejecting a pending action"""
        await approval_system.submit_for_review(
            action_id="test_action_009",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1"},
            risk_level="medium",
        )

        result = await approval_system.reject(
            action_id="test_action_009", operator="test_operator", reason="Security concerns"
        )

        assert result["action_id"] == "test_action_009"
        assert result["status"] == "rejected"
        assert result["rejected_by"] == "test_operator"
        assert result["reason"] == "Security concerns"

    @pytest.mark.asyncio
    async def test_reject_nonexistent_action(self, approval_system):
        """Test rejecting non-existent action returns error"""
        result = await approval_system.reject(action_id="nonexistent_action", operator="test_operator", reason="Test")

        assert "error" in result

    @pytest.mark.asyncio
    async def test_reject_creates_history_entry(self, approval_system):
        """Test that rejection creates history entry"""
        await approval_system.submit_for_review(
            action_id="test_action_010",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1"},
            risk_level="medium",
        )

        await approval_system.reject(action_id="test_action_010", operator="test_operator", reason="Test rejection")

        details = await approval_system.get_action_details("test_action_010")
        history_events = [h["event"] for h in details["history"]]
        assert "rejected" in history_events


class TestGetPendingActions:
    """Test retrieving pending actions"""

    @pytest.mark.asyncio
    async def test_get_pending_actions_empty(self, approval_system):
        """Test getting pending actions when queue is empty"""
        actions = await approval_system.get_pending_actions()
        assert actions == []

    @pytest.mark.asyncio
    async def test_get_pending_actions_single(self, approval_system):
        """Test getting single pending action"""
        await approval_system.submit_for_review(
            action_id="test_action_011",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1"},
            risk_level="medium",
        )

        actions = await approval_system.get_pending_actions()
        assert len(actions) == 1
        assert actions[0]["action_id"] == "test_action_011"

    @pytest.mark.asyncio
    async def test_get_pending_actions_multiple(self, approval_system):
        """Test getting multiple pending actions"""
        for i in range(5):
            await approval_system.submit_for_review(
                action_id=f"test_action_{i}",
                agent_name="test_agent",
                function_name="test_function",
                parameters={"param1": "value1"},
                risk_level="medium",
            )

        actions = await approval_system.get_pending_actions()
        assert len(actions) == 5

    @pytest.mark.asyncio
    async def test_get_pending_actions_excludes_approved(self, approval_system):
        """Test that approved actions are not included"""
        await approval_system.submit_for_review(
            action_id="test_action_012",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1"},
            risk_level="medium",
        )
        await approval_system.submit_for_review(
            action_id="test_action_013",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1"},
            risk_level="medium",
        )

        await approval_system.approve("test_action_012", "operator")

        actions = await approval_system.get_pending_actions()
        action_ids = [a["action_id"] for a in actions]
        assert "test_action_012" not in action_ids
        assert "test_action_013" in action_ids


class TestGetActionDetails:
    """Test retrieving action details"""

    @pytest.mark.asyncio
    async def test_get_action_details_complete(self, approval_system):
        """Test getting complete action details"""
        await approval_system.submit_for_review(
            action_id="test_action_014",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1", "param2": 42},
            risk_level="medium",
        )

        details = await approval_system.get_action_details("test_action_014")

        assert details["action_id"] == "test_action_014"
        assert details["agent_name"] == "test_agent"
        assert details["function_name"] == "test_function"
        assert details["parameters"]["param1"] == "value1"
        assert details["parameters"]["param2"] == 42
        assert details["risk_level"] == "medium"
        assert details["status"] == "pending"
        assert "history" in details

    @pytest.mark.asyncio
    async def test_get_action_details_nonexistent(self, approval_system):
        """Test getting details for non-existent action"""
        details = await approval_system.get_action_details("nonexistent")
        assert details is None


class TestMarkExecuted:
    """Test marking actions as executed"""

    @pytest.mark.asyncio
    async def test_mark_executed_approved_action(self, approval_system):
        """Test marking approved action as executed"""
        await approval_system.submit_for_review(
            action_id="test_action_015",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1"},
            risk_level="medium",
        )
        await approval_system.approve("test_action_015", "operator")

        result = await approval_system.mark_executed("test_action_015", {"output": "success", "duration": 1.5})

        assert result is True

    @pytest.mark.asyncio
    async def test_mark_executed_pending_action_fails(self, approval_system):
        """Test that marking pending action as executed fails"""
        await approval_system.submit_for_review(
            action_id="test_action_016",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1"},
            risk_level="medium",
        )

        result = await approval_system.mark_executed("test_action_016", {"output": "success"})

        assert result is False


class TestCleanupExpired:
    """Test cleaning up expired actions"""

    @pytest.mark.asyncio
    async def test_cleanup_expired_actions(self, approval_system, temp_db_path):
        """Test cleanup of expired actions"""
        # Submit actions with past timeout
        await approval_system.submit_for_review(
            action_id="test_action_017",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1"},
            risk_level="medium",
        )

        # Manually expire the action
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        past_time = (datetime.now() - timedelta(hours=1)).isoformat()
        cursor.execute("UPDATE review_queue SET timeout_at = ? WHERE action_id = ?", (past_time, "test_action_017"))
        conn.commit()
        conn.close()

        count = await approval_system.cleanup_expired()
        assert count == 1

    @pytest.mark.asyncio
    async def test_cleanup_no_expired_actions(self, approval_system):
        """Test cleanup when no actions are expired"""
        await approval_system.submit_for_review(
            action_id="test_action_018",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1"},
            risk_level="medium",
            timeout_hours=24,
        )

        count = await approval_system.cleanup_expired()
        assert count == 0


class TestOperatorStatistics:
    """Test operator statistics tracking"""

    @pytest.mark.asyncio
    async def test_get_operator_statistics_single_operator(self, approval_system):
        """Test getting statistics for single operator"""
        # Create and approve multiple actions
        for i in range(3):
            await approval_system.submit_for_review(
                action_id=f"test_action_{i}",
                agent_name="test_agent",
                function_name="test_function",
                parameters={"param1": "value1"},
                risk_level="medium",
            )
            await approval_system.approve(f"test_action_{i}", "operator1")

        stats = await approval_system.get_operator_statistics("operator1")
        assert stats["approve"] == 3

    @pytest.mark.asyncio
    async def test_get_operator_statistics_all_operators(self, approval_system):
        """Test getting statistics for all operators"""
        # Create actions for multiple operators
        await approval_system.submit_for_review(
            action_id="test_action_019",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1"},
            risk_level="medium",
        )
        await approval_system.approve("test_action_019", "operator1")

        await approval_system.submit_for_review(
            action_id="test_action_020",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1"},
            risk_level="medium",
        )
        await approval_system.reject("test_action_020", "operator2", "Test")

        stats = await approval_system.get_operator_statistics()
        assert "operator1" in stats
        assert "operator2" in stats


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_submit_with_empty_parameters(self, approval_system):
        """Test submitting action with empty parameters"""
        result = await approval_system.submit_for_review(
            action_id="test_action_021",
            agent_name="test_agent",
            function_name="test_function",
            parameters={},
            risk_level="low",
        )

        assert result["status"] == "submitted"

    @pytest.mark.asyncio
    async def test_submit_with_complex_parameters(self, approval_system):
        """Test submitting action with complex nested parameters"""
        complex_params = {
            "nested": {"level1": {"level2": ["item1", "item2"]}},
            "array": [1, 2, 3, 4, 5],
            "mixed": {"key": "value", "number": 42},
        }

        await approval_system.submit_for_review(
            action_id="test_action_022",
            agent_name="test_agent",
            function_name="test_function",
            parameters=complex_params,
            risk_level="medium",
        )

        details = await approval_system.get_action_details("test_action_022")
        assert details["parameters"] == complex_params
