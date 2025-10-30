"""
Unit Tests for Approval System
Tests human review queue and approval workflows
"""

import pytest
import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil


from fashion_ai_bounded_autonomy.approval_system import (
    ApprovalSystem,
    ApprovalWorkflowType
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_review_queue.db"
    yield str(db_path)
    shutil.rmtree(temp_dir)


@pytest.fixture
def approval_system(temp_db):
    """Create ApprovalSystem instance with temporary database"""
    return ApprovalSystem(db_path=temp_db)


class TestApprovalSystemInitialization:
    """Test approval system initialization"""

    def test_database_creation(self, temp_db):
        """Test that database and tables are created"""
        ApprovalSystem(db_path=temp_db)
        
        # Verify database exists
        assert Path(temp_db).exists()
        
        # Verify tables exist
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='review_queue'
        """)
        assert cursor.fetchone() is not None
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='approval_history'
        """)
        assert cursor.fetchone() is not None
        
        conn.close()

    def test_directory_creation(self):
        """Test that parent directories are created"""
        nested_path = Path(tempfile.mkdtemp()) / "nested" / "path" / "review.db"
        ApprovalSystem(db_path=str(nested_path))
        
        assert nested_path.parent.exists()
        assert nested_path.exists()
        
        shutil.rmtree(nested_path.parent.parent.parent)


class TestSubmitForReview:
    """Test submission of actions for review"""

    @pytest.mark.asyncio
    async def test_submit_basic_action(self, approval_system):
        """Test submitting a basic action for review"""
        result = await approval_system.submit_for_review(
            action_id="test_action_001",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"param1": "value1"},
            risk_level="medium",
            workflow_type=ApprovalWorkflowType.DEFAULT
        )
        
        assert result["action_id"] == "test_action_001"
        assert result["status"] == "submitted"
        assert result["workflow"] == "default"
        assert "timeout_at" in result

    @pytest.mark.asyncio
    async def test_submit_high_risk_action(self, approval_system):
        """Test submitting high-risk action"""
        result = await approval_system.submit_for_review(
            action_id="test_action_002",
            agent_name="test_agent",
            function_name="delete_data",
            parameters={"target": "critical_data"},
            risk_level="critical",
            workflow_type=ApprovalWorkflowType.HIGH_RISK
        )
        
        assert result["workflow"] == "high_risk"
        assert result["status"] == "submitted"

    @pytest.mark.asyncio
    async def test_submit_with_custom_timeout(self, approval_system):
        """Test submission with custom timeout"""
        result = await approval_system.submit_for_review(
            action_id="test_action_003",
            agent_name="test_agent",
            function_name="test_function",
            parameters={},
            risk_level="low",
            timeout_hours=48
        )
        
        timeout_at = datetime.fromisoformat(result["timeout_at"])
        now = datetime.now()
        
        # Should be approximately 48 hours from now
        time_diff = (timeout_at - now).total_seconds()
        assert 47 * 3600 < time_diff < 49 * 3600

    @pytest.mark.asyncio
    async def test_submit_creates_history_entry(self, approval_system, temp_db):
        """Test that submission creates history entry"""
        await approval_system.submit_for_review(
            action_id="test_action_004",
            agent_name="test_agent",
            function_name="test_function",
            parameters={},
            risk_level="low"
        )
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT event_type FROM approval_history 
            WHERE action_id = 'test_action_004'
        """)
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == "submitted"


class TestApproveAction:
    """Test action approval functionality"""

    @pytest.mark.asyncio
    async def test_approve_pending_action(self, approval_system):
        """Test approving a pending action"""
        # Submit action
        await approval_system.submit_for_review(
            action_id="test_action_005",
            agent_name="test_agent",
            function_name="test_function",
            parameters={},
            risk_level="medium"
        )
        
        # Approve action
        result = await approval_system.approve(
            action_id="test_action_005",
            operator="test_operator",
            notes="Approved for testing"
        )
        
        assert result["status"] == "approved"
        assert result["action_id"] == "test_action_005"
        assert result["approved_by"] == "test_operator"
        assert "approved_at" in result

    @pytest.mark.asyncio
    async def test_approve_nonexistent_action(self, approval_system):
        """Test approving non-existent action returns error"""
        result = await approval_system.approve(
            action_id="nonexistent",
            operator="test_operator"
        )
        
        assert "error" in result
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_approve_already_approved(self, approval_system):
        """Test approving already approved action"""
        # Submit and approve
        await approval_system.submit_for_review(
            action_id="test_action_006",
            agent_name="test_agent",
            function_name="test_function",
            parameters={},
            risk_level="low"
        )
        await approval_system.approve(
            action_id="test_action_006",
            operator="operator1"
        )
        
        # Try to approve again
        result = await approval_system.approve(
            action_id="test_action_006",
            operator="operator2"
        )
        
        assert "error" in result

    @pytest.mark.asyncio
    async def test_approve_expired_action(self, approval_system, temp_db):
        """Test approving expired action"""
        # Submit action
        await approval_system.submit_for_review(
            action_id="test_action_007",
            agent_name="test_agent",
            function_name="test_function",
            parameters={},
            risk_level="low",
            timeout_hours=1
        )
        
        # Manually set timeout to past
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        past_time = (datetime.now() - timedelta(hours=2)).isoformat()
        cursor.execute("""
            UPDATE review_queue 
            SET timeout_at = ? 
            WHERE action_id = 'test_action_007'
        """, (past_time,))
        conn.commit()
        conn.close()
        
        # Try to approve
        result = await approval_system.approve(
            action_id="test_action_007",
            operator="test_operator"
        )
        
        assert result["status"] == "expired"

    @pytest.mark.asyncio
    async def test_approval_creates_history(self, approval_system, temp_db):
        """Test that approval creates history entry"""
        await approval_system.submit_for_review(
            action_id="test_action_008",
            agent_name="test_agent",
            function_name="test_function",
            parameters={},
            risk_level="low"
        )
        
        await approval_system.approve(
            action_id="test_action_008",
            operator="test_operator"
        )
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT event_type, operator FROM approval_history 
            WHERE action_id = 'test_action_008' AND event_type = 'approved'
        """)
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == "approved"
        assert result[1] == "test_operator"


class TestRejectAction:
    """Test action rejection functionality"""

    @pytest.mark.asyncio
    async def test_reject_pending_action(self, approval_system):
        """Test rejecting a pending action"""
        await approval_system.submit_for_review(
            action_id="test_action_009",
            agent_name="test_agent",
            function_name="test_function",
            parameters={},
            risk_level="medium"
        )
        
        result = await approval_system.reject(
            action_id="test_action_009",
            operator="test_operator",
            reason="Does not meet requirements"
        )
        
        assert result["status"] == "rejected"
        assert result["rejected_by"] == "test_operator"
        assert result["reason"] == "Does not meet requirements"

    @pytest.mark.asyncio
    async def test_reject_nonexistent_action(self, approval_system):
        """Test rejecting non-existent action"""
        result = await approval_system.reject(
            action_id="nonexistent",
            operator="test_operator",
            reason="test"
        )
        
        assert "error" in result

    @pytest.mark.asyncio
    async def test_reject_approved_action(self, approval_system):
        """Test rejecting already approved action"""
        await approval_system.submit_for_review(
            action_id="test_action_010",
            agent_name="test_agent",
            function_name="test_function",
            parameters={},
            risk_level="low"
        )
        
        await approval_system.approve(
            action_id="test_action_010",
            operator="operator1"
        )
        
        result = await approval_system.reject(
            action_id="test_action_010",
            operator="operator2",
            reason="test"
        )
        
        assert "error" in result


class TestGetPendingActions:
    """Test retrieval of pending actions"""

    @pytest.mark.asyncio
    async def test_get_empty_queue(self, approval_system):
        """Test getting pending actions from empty queue"""
        actions = await approval_system.get_pending_actions()
        assert actions == []

    @pytest.mark.asyncio
    async def test_get_pending_actions(self, approval_system):
        """Test getting multiple pending actions"""
        # Submit multiple actions
        for i in range(3):
            await approval_system.submit_for_review(
                action_id=f"test_action_{i}",
                agent_name="test_agent",
                function_name="test_function",
                parameters={},
                risk_level="medium"
            )
        
        actions = await approval_system.get_pending_actions()
        
        assert len(actions) == 3
        assert all(action["parameters"] == {} for action in actions)

    @pytest.mark.asyncio
    async def test_pending_excludes_approved(self, approval_system):
        """Test that pending actions exclude approved ones"""
        await approval_system.submit_for_review(
            action_id="pending_action",
            agent_name="test_agent",
            function_name="test_function",
            parameters={},
            risk_level="low"
        )
        
        await approval_system.submit_for_review(
            action_id="approved_action",
            agent_name="test_agent",
            function_name="test_function",
            parameters={},
            risk_level="low"
        )
        
        await approval_system.approve(
            action_id="approved_action",
            operator="test_operator"
        )
        
        actions = await approval_system.get_pending_actions()
        
        assert len(actions) == 1
        assert actions[0]["action_id"] == "pending_action"


class TestGetActionDetails:
    """Test retrieval of action details"""

    @pytest.mark.asyncio
    async def test_get_details_with_history(self, approval_system):
        """Test getting action details including history"""
        await approval_system.submit_for_review(
            action_id="test_action_011",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"key": "value"},
            risk_level="medium"
        )
        
        details = await approval_system.get_action_details("test_action_011")
        
        assert details is not None
        assert details["action_id"] == "test_action_011"
        assert details["agent_name"] == "test_agent"
        assert details["function_name"] == "test_function"
        assert details["parameters"] == {"key": "value"}
        assert details["risk_level"] == "medium"
        assert len(details["history"]) > 0

    @pytest.mark.asyncio
    async def test_get_nonexistent_action(self, approval_system):
        """Test getting details of non-existent action"""
        details = await approval_system.get_action_details("nonexistent")
        assert details is None

    @pytest.mark.asyncio
    async def test_details_include_approval_info(self, approval_system):
        """Test that details include approval information"""
        await approval_system.submit_for_review(
            action_id="test_action_012",
            agent_name="test_agent",
            function_name="test_function",
            parameters={},
            risk_level="low"
        )
        
        await approval_system.approve(
            action_id="test_action_012",
            operator="test_operator",
            notes="Test approval"
        )
        
        details = await approval_system.get_action_details("test_action_012")
        
        assert details["status"] == "approved"
        assert details["approved_by"] == "test_operator"
        assert details["approved_at"] is not None


class TestMarkExecuted:
    """Test marking actions as executed"""

    @pytest.mark.asyncio
    async def test_mark_approved_as_executed(self, approval_system):
        """Test marking approved action as executed"""
        await approval_system.submit_for_review(
            action_id="test_action_013",
            agent_name="test_agent",
            function_name="test_function",
            parameters={},
            risk_level="low"
        )
        
        await approval_system.approve(
            action_id="test_action_013",
            operator="test_operator"
        )
        
        result = await approval_system.mark_executed(
            action_id="test_action_013",
            result={"status": "success", "output": "completed"}
        )
        
        assert result is True

    @pytest.mark.asyncio
    async def test_mark_pending_as_executed_fails(self, approval_system):
        """Test that pending actions cannot be marked as executed"""
        await approval_system.submit_for_review(
            action_id="test_action_014",
            agent_name="test_agent",
            function_name="test_function",
            parameters={},
            risk_level="low"
        )
        
        result = await approval_system.mark_executed(
            action_id="test_action_014",
            result={"status": "success"}
        )
        
        assert result is False


class TestCleanupExpired:
    """Test cleanup of expired actions"""

    @pytest.mark.asyncio
    async def test_cleanup_no_expired(self, approval_system):
        """Test cleanup when no actions are expired"""
        await approval_system.submit_for_review(
            action_id="test_action_015",
            agent_name="test_agent",
            function_name="test_function",
            parameters={},
            risk_level="low",
            timeout_hours=24
        )
        
        count = await approval_system.cleanup_expired()
        assert count == 0

    @pytest.mark.asyncio
    async def test_cleanup_expired_actions(self, approval_system, temp_db):
        """Test cleanup of expired actions"""
        # Submit actions
        await approval_system.submit_for_review(
            action_id="expired_1",
            agent_name="test_agent",
            function_name="test_function",
            parameters={},
            risk_level="low"
        )
        
        await approval_system.submit_for_review(
            action_id="expired_2",
            agent_name="test_agent",
            function_name="test_function",
            parameters={},
            risk_level="low"
        )
        
        # Manually expire them
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        past_time = (datetime.now() - timedelta(hours=1)).isoformat()
        cursor.execute("""
            UPDATE review_queue 
            SET timeout_at = ? 
            WHERE action_id IN ('expired_1', 'expired_2')
        """, (past_time,))
        conn.commit()
        conn.close()
        
        # Cleanup
        count = await approval_system.cleanup_expired()
        assert count == 2


class TestOperatorStatistics:
    """Test operator statistics functionality"""

    @pytest.mark.asyncio
    async def test_statistics_for_operator(self, approval_system):
        """Test getting statistics for specific operator"""
        # Create some operator activity
        await approval_system.submit_for_review(
            action_id="stat_action_1",
            agent_name="test_agent",
            function_name="test_function",
            parameters={},
            risk_level="low"
        )
        
        await approval_system.approve(
            action_id="stat_action_1",
            operator="operator_1"
        )
        
        stats = await approval_system.get_operator_statistics("operator_1")
        
        assert "approve" in stats
        assert stats["approve"] >= 1

    @pytest.mark.asyncio
    async def test_statistics_all_operators(self, approval_system):
        """Test getting statistics for all operators"""
        # Create activity for multiple operators
        for i in range(2):
            await approval_system.submit_for_review(
                action_id=f"stat_action_{i + 2}",
                agent_name="test_agent",
                function_name="test_function",
                parameters={},
                risk_level="low"
            )
            
            await approval_system.approve(
                action_id=f"stat_action_{i + 2}",
                operator=f"operator_{i + 2}"
            )
        
        stats = await approval_system.get_operator_statistics()
        
        assert isinstance(stats, dict)
        assert len(stats) >= 2


class TestWorkflowTypes:
    """Test different workflow types"""

    @pytest.mark.asyncio
    async def test_default_workflow(self, approval_system):
        """Test default workflow type"""
        result = await approval_system.submit_for_review(
            action_id="workflow_test_1",
            agent_name="test_agent",
            function_name="test_function",
            parameters={},
            risk_level="medium",
            workflow_type=ApprovalWorkflowType.DEFAULT
        )
        
        assert result["workflow"] == "default"

    @pytest.mark.asyncio
    async def test_high_risk_workflow(self, approval_system):
        """Test high-risk workflow type"""
        result = await approval_system.submit_for_review(
            action_id="workflow_test_2",
            agent_name="test_agent",
            function_name="delete_critical_data",
            parameters={},
            risk_level="critical",
            workflow_type=ApprovalWorkflowType.HIGH_RISK
        )
        
        assert result["workflow"] == "high_risk"

    @pytest.mark.asyncio
    async def test_expedited_workflow(self, approval_system):
        """Test expedited workflow type"""
        result = await approval_system.submit_for_review(
            action_id="workflow_test_3",
            agent_name="test_agent",
            function_name="urgent_query",
            parameters={},
            risk_level="low",
            workflow_type=ApprovalWorkflowType.EXPEDITED
        )
        
        assert result["workflow"] == "expedited"