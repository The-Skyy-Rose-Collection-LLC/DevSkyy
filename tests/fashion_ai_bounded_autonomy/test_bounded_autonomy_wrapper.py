"""
Unit Tests for Bounded Autonomy Wrapper
Tests agent wrapping with approval workflows
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from fashion_ai_bounded_autonomy.bounded_autonomy_wrapper import (
    BoundedAutonomyWrapper,
    ActionRiskLevel,
    ApprovalStatus,
    BoundedAction
)
from agent.modules.base_agent import BaseAgent, AgentStatus


class MockAgent(BaseAgent):
    """Mock agent for testing"""

    async def initialize(self) -> bool:
        """
        Set the agent's status to AgentStatus.HEALTHY and indicate successful initialization.
        
        Sets the agent's status attribute to AgentStatus.HEALTHY as a visible side effect.
        
        Returns:
            True if initialization succeeded.
        """
        self.status = AgentStatus.HEALTHY
        return True

    async def execute_core_function(self, **kwargs):
        """
        Execute the agent's core function and return a standardized success result.
        
        Returns:
            dict: A result mapping with:
                - "status": the string "success".
                - "data": a dict containing the keyword arguments passed to the call.
        """
        return {"status": "success", "data": kwargs}

    async def health_check(self):
        """
        Report the agent's health status.
        
        Returns:
            dict: A dictionary with key "status" whose value is "healthy".
        """
        return {"status": "healthy"}

    def __getattr__(self, name):
        """
        Provide a dynamic async method for any attribute access to simulate agent behavior in tests.
        
        Parameters:
            name (str): The attribute or method name being accessed.
        
        Returns:
            callable: An async function that accepts keyword arguments and returns a dict with keys:
                - "status": "success"
                - "function": the accessed attribute name
                - "data": the provided keyword arguments
        """
        # Return an async function that simulates successful execution
        async def dynamic_method(**kwargs):
            """
            Echoes received keyword arguments in a standardized success response for a simulated dynamic agent method.
            
            Parameters:
                **kwargs: Arbitrary keyword arguments to include in the response.
            
            Returns:
                dict: A mapping with keys:
                    - "status": the string "success".
                    - "function": the name of the simulated function.
                    - "data": a dict containing the passed keyword arguments.
            """
            return {"status": "success", "function": name, "data": kwargs}
        return dynamic_method


@pytest.fixture
def temp_audit_dir():
    """
    Create a temporary directory for audit logs and remove it during fixture teardown.
    
    Returns:
        temp_dir (str): Path to the temporary directory created for audit logs; removed after the test finishes.
    """
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_agent():
    """
    Provide a MockAgent instance named "test_agent" with version "1.0.0" for use in tests.
    
    Returns:
        MockAgent: A mock agent configured with name "test_agent" and version "1.0.0".
    """
    return MockAgent("test_agent", version="1.0.0")


@pytest.fixture
def wrapper(mock_agent, temp_audit_dir):
    """
    Create a BoundedAutonomyWrapper configured for tests.
    
    Parameters:
        mock_agent: The agent instance to be wrapped.
        temp_audit_dir (str or pathlib.Path): Filesystem path used as the wrapper's audit_log_path.
    
    Returns:
        BoundedAutonomyWrapper: A wrapper with auto_approve_low_risk enabled, local_only mode enabled, and audit logging directed to `temp_audit_dir`.
    """
    return BoundedAutonomyWrapper(
        wrapped_agent=mock_agent,
        auto_approve_low_risk=True,
        local_only=True,
        audit_log_path=temp_audit_dir
    )


class TestWrapperInitialization:
    """Test wrapper initialization"""

    def test_initialization(self, mock_agent, temp_audit_dir):
        """Test basic initialization"""
        wrapper = BoundedAutonomyWrapper(
            wrapped_agent=mock_agent,
            auto_approve_low_risk=True,
            local_only=True,
            audit_log_path=temp_audit_dir
        )
        
        assert wrapper.wrapped_agent == mock_agent
        assert wrapper.auto_approve_low_risk is True
        assert wrapper.local_only is True
        assert wrapper.emergency_stop is False
        assert wrapper.paused is False

    def test_audit_directory_creation(self, mock_agent):
        """Test that audit directory is created"""
        temp_dir = tempfile.mkdtemp()
        audit_path = Path(temp_dir) / "nested" / "audit"
        
        BoundedAutonomyWrapper(
            wrapped_agent=mock_agent,
            audit_log_path=str(audit_path)
        )
        
        assert audit_path.exists()
        shutil.rmtree(temp_dir)


class TestRiskAssessment:
    """Test risk assessment functionality"""

    def test_low_risk_read_operations(self, wrapper):
        """Test that read operations are assessed as low risk"""
        risk = wrapper._assess_risk("get_data", {})
        assert risk == ActionRiskLevel.LOW
        
        risk = wrapper._assess_risk("query_database", {})
        assert risk == ActionRiskLevel.LOW
        
        risk = wrapper._assess_risk("fetch_records", {})
        assert risk == ActionRiskLevel.LOW

    def test_medium_risk_operations(self, wrapper):
        """Test that analysis operations are medium risk"""
        risk = wrapper._assess_risk("analyze_trends", {})
        assert risk == ActionRiskLevel.MEDIUM
        
        risk = wrapper._assess_risk("process_data", {})
        assert risk == ActionRiskLevel.MEDIUM
        
        risk = wrapper._assess_risk("calculate_metrics", {})
        assert risk == ActionRiskLevel.MEDIUM

    def test_high_risk_operations(self, wrapper):
        """Test that write operations are high risk"""
        risk = wrapper._assess_risk("create_record", {})
        assert risk == ActionRiskLevel.HIGH
        
        risk = wrapper._assess_risk("update_database", {})
        assert risk == ActionRiskLevel.HIGH
        
        risk = wrapper._assess_risk("send_email", {})
        assert risk == ActionRiskLevel.HIGH

    def test_critical_risk_operations(self, wrapper):
        """Test that critical operations are marked critical"""
        risk = wrapper._assess_risk("deploy_system", {})
        assert risk == ActionRiskLevel.CRITICAL
        
        risk = wrapper._assess_risk("delete_production", {})
        assert risk == ActionRiskLevel.CRITICAL
        
        risk = wrapper._assess_risk("modify_config", {})
        assert risk == ActionRiskLevel.CRITICAL


class TestApprovalRequirement:
    """Test approval requirement logic"""

    def test_auto_approve_low_risk(self, wrapper):
        """Test auto-approval of low-risk operations"""
        wrapper.auto_approve_low_risk = True
        requires = wrapper._requires_approval("get_data", {}, None)
        assert requires is False

    def test_require_approval_medium_risk(self, wrapper):
        """Test that medium-risk operations require approval"""
        requires = wrapper._requires_approval("analyze_data", {}, None)
        assert requires is True

    def test_require_approval_high_risk(self, wrapper):
        """Test that high-risk operations require approval"""
        requires = wrapper._requires_approval("create_user", {}, None)
        assert requires is True

    def test_override_approval_requirement(self, wrapper):
        """Test override of approval requirement"""
        # Override to not require approval
        requires = wrapper._requires_approval("delete_data", {}, False)
        assert requires is False
        
        # Override to require approval
        requires = wrapper._requires_approval("get_data", {}, True)
        assert requires is True


class TestExecution:
    """Test execution functionality"""

    @pytest.mark.asyncio
    async def test_execute_low_risk_auto_approved(self, wrapper):
        """Test auto-execution of low-risk operations"""
        result = await wrapper.execute(
            function_name="execute_core_function",
            parameters={"task": "query"}
        )
        
        assert result["status"] == "completed"
        assert "result" in result

    @pytest.mark.asyncio
    async def test_execute_high_risk_requires_approval(self, wrapper):
        """Test that high-risk operations require approval"""
        result = await wrapper.execute(
            function_name="create_record",
            parameters={"data": "test"}
        )
        
        assert result["status"] == "pending_approval"
        assert "action_id" in result
        assert result["risk_level"] == "high"

    @pytest.mark.asyncio
    async def test_emergency_stop_blocks_execution(self, wrapper):
        """Test that emergency stop blocks execution"""
        wrapper.emergency_stop = True
        
        result = await wrapper.execute(
            function_name="execute_core_function",
            parameters={}
        )
        
        assert "error" in result
        assert result["status"] == "blocked"

    @pytest.mark.asyncio
    async def test_paused_queues_operations(self, wrapper):
        """Test that paused state queues operations"""
        wrapper.paused = True
        
        result = await wrapper.execute(
            function_name="execute_core_function",
            parameters={}
        )
        
        assert result["status"] == "queued"

    @pytest.mark.asyncio
    async def test_execution_creates_audit_log(self, wrapper, temp_audit_dir):
        """Test that execution creates audit log entry"""
        await wrapper.execute(
            function_name="execute_core_function",
            parameters={"test": "data"}
        )
        
        # Check audit log exists
        audit_files = list(Path(temp_audit_dir).glob("*.jsonl"))
        assert len(audit_files) > 0


class TestApproval:
    """Test approval functionality"""

    @pytest.mark.asyncio
    async def test_approve_pending_action(self, wrapper):
        """Test approving a pending action"""
        # Create pending action
        result = await wrapper.execute(
            function_name="create_record",
            parameters={"data": "test"},
            require_approval=True
        )
        
        action_id = result["action_id"]
        
        # Approve
        approval_result = await wrapper.approve_action(action_id, "test_operator")
        
        assert approval_result["status"] == "completed"
        assert "result" in approval_result

    @pytest.mark.asyncio
    async def test_approve_nonexistent_action(self, wrapper):
        """Test approving non-existent action"""
        result = await wrapper.approve_action("nonexistent", "test_operator")
        
        assert "error" in result
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_approval_removes_from_pending(self, wrapper):
        """Test that approval removes action from pending queue"""
        result = await wrapper.execute(
            function_name="update_data",
            parameters={},
            require_approval=True
        )
        
        action_id = result["action_id"]
        assert action_id in wrapper.pending_actions
        
        await wrapper.approve_action(action_id, "operator")
        assert action_id not in wrapper.pending_actions


class TestRejection:
    """Test rejection functionality"""

    @pytest.mark.asyncio
    async def test_reject_pending_action(self, wrapper):
        """Test rejecting a pending action"""
        result = await wrapper.execute(
            function_name="create_user",
            parameters={},
            require_approval=True
        )
        
        action_id = result["action_id"]
        
        rejection_result = await wrapper.reject_action(
            action_id,
            "test_operator",
            "Not approved"
        )
        
        assert rejection_result["status"] == "rejected"
        assert rejection_result["reason"] == "Not approved"

    @pytest.mark.asyncio
    async def test_reject_removes_from_pending(self, wrapper):
        """Test that rejection removes action from pending"""
        result = await wrapper.execute(
            function_name="delete_data",
            parameters={},
            require_approval=True
        )
        
        action_id = result["action_id"]
        await wrapper.reject_action(action_id, "operator", "test")
        
        assert action_id not in wrapper.pending_actions


class TestNetworkIsolation:
    """Test network isolation functionality"""

    def test_network_call_detection(self, wrapper):
        """Test detection of network calls"""
        action = BoundedAction(
            action_id="test",
            agent_name="test",
            function_name="api_call",
            parameters={},
            risk_level=ActionRiskLevel.HIGH,
            requires_approval=False
        )
        
        assert wrapper._involves_network_call(action) is True
        
        action.function_name = "query_local"
        assert wrapper._involves_network_call(action) is False

    @pytest.mark.asyncio
    async def test_network_calls_blocked_in_local_mode(self, wrapper):
        """Test that network calls are blocked in local-only mode"""
        wrapper.local_only = True
        
        result = await wrapper.execute(
            function_name="http_request",
            parameters={},
            require_approval=False
        )
        
        assert "error" in result
        assert wrapper.network_calls_blocked > 0


class TestEmergencyControls:
    """Test emergency control functionality"""

    def test_emergency_shutdown(self, wrapper):
        """Test emergency shutdown"""
        wrapper.emergency_shutdown("Security incident")
        
        assert wrapper.emergency_stop is True

    def test_pause_and_resume(self, wrapper):
        """Test pause and resume"""
        wrapper.pause()
        assert wrapper.paused is True
        
        wrapper.resume()
        assert wrapper.paused is False

    @pytest.mark.asyncio
    async def test_get_status(self, wrapper):
        """Test status retrieval"""
        status = await wrapper.get_status()
        
        assert "agent_name" in status
        assert "bounded_controls" in status
        assert "actions" in status
        assert "network" in status


class TestAuditLogging:
    """Test audit logging functionality"""

    @pytest.mark.asyncio
    async def test_audit_log_created(self, wrapper, temp_audit_dir):
        """Test that audit log file is created"""
        await wrapper.execute(
            function_name="execute_core_function",
            parameters={}
        )
        
        audit_files = list(Path(temp_audit_dir).glob("*.jsonl"))
        assert len(audit_files) > 0

    def test_audit_log_entry_format(self, wrapper):
        """Test audit log entry format"""
        action = BoundedAction(
            action_id="test_action",
            agent_name="test_agent",
            function_name="test_function",
            parameters={"key": "value"},
            risk_level=ActionRiskLevel.MEDIUM,
            requires_approval=True
        )
        
        wrapper._audit_log(action, "test_event", {"meta": "data"})
        
        assert len(action.audit_trail) > 0
        entry = action.audit_trail[-1]
        
        assert "timestamp" in entry
        assert entry["event"] == "test_event"
        assert entry["metadata"] == {"meta": "data"}