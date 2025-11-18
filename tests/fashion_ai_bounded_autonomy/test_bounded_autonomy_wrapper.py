"""
Unit tests for BoundedAutonomyWrapper
Tests wrapping agents with bounded autonomy controls
"""

from pathlib import Path
import shutil
import tempfile

import pytest

from agent.modules.base_agent import AgentStatus, BaseAgent
from fashion_ai_bounded_autonomy.bounded_autonomy_wrapper import ActionRiskLevel, BoundedAction, BoundedAutonomyWrapper


class MockAgent(BaseAgent):
    """Mock agent for testing"""

    def __init__(self, name: str, version: str = "1.0.0"):
        super().__init__(name, version)
        self.status = AgentStatus.HEALTHY

    async def initialize(self) -> bool:
        return True

    async def execute_core_function(self, **kwargs) -> dict:
        task = kwargs.get("task", "test")
        return {"status": "success", "task": task, "result": "completed"}

    async def read_data(self, source: str) -> dict:
        return {"status": "success", "data": f"data from {source}"}

    async def write_data(self, destination: str, _data: dict) -> dict:
        return {"status": "success", "written": True, "destination": destination}

    async def delete_resource(self, resource_id: str) -> dict:
        return {"status": "success", "deleted": resource_id}

    async def api_call(self, endpoint: str) -> dict:
        return {"status": "success", "endpoint": endpoint}


@pytest.fixture
def temp_audit_path():
    """Create temporary audit log path"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_agent():
    """Create mock agent"""
    return MockAgent("test_agent", "1.0.0")


@pytest.fixture
def wrapper(mock_agent, temp_audit_path):
    """Create BoundedAutonomyWrapper instance"""
    return BoundedAutonomyWrapper(
        wrapped_agent=mock_agent, auto_approve_low_risk=True, local_only=True, audit_log_path=temp_audit_path
    )


class TestBoundedAutonomyWrapperInitialization:
    """Test wrapper initialization"""

    def test_init_creates_audit_directory(self, mock_agent, temp_audit_path):
        """Test that initialization creates audit log directory"""
        audit_path = Path(temp_audit_path) / "custom_audit"
        BoundedAutonomyWrapper(wrapped_agent=mock_agent, audit_log_path=str(audit_path))
        assert audit_path.exists()

    def test_init_sets_default_values(self, wrapper):
        """Test that initialization sets default values"""
        assert wrapper.auto_approve_low_risk is True
        assert wrapper.local_only is True
        assert wrapper.emergency_stop is False
        assert wrapper.paused is False
        assert len(wrapper.pending_actions) == 0
        assert len(wrapper.completed_actions) == 0


class TestRiskAssessment:
    """Test risk assessment logic"""

    def test_assess_risk_critical_operations(self, wrapper):
        """Test assessment of critical operations"""
        critical_functions = ["deploy_model", "delete_database", "drop_table", "modify_config"]

        for func in critical_functions:
            risk = wrapper._assess_risk(func, {})
            assert risk == ActionRiskLevel.CRITICAL

    def test_assess_risk_high_operations(self, wrapper):
        """Test assessment of high-risk operations"""
        high_risk_functions = ["create_user", "update_product", "insert_record", "send_email"]

        for func in high_risk_functions:
            risk = wrapper._assess_risk(func, {})
            assert risk == ActionRiskLevel.HIGH

    def test_assess_risk_medium_operations(self, wrapper):
        """Test assessment of medium-risk operations"""
        medium_risk_functions = ["analyze_data", "process_batch", "calculate_metrics", "generate_report"]

        for func in medium_risk_functions:
            risk = wrapper._assess_risk(func, {})
            assert risk == ActionRiskLevel.MEDIUM

    def test_assess_risk_low_operations(self, wrapper):
        """Test assessment of low-risk operations"""
        low_risk_functions = ["get_data", "fetch_info", "query_status", "list_items"]

        for func in low_risk_functions:
            risk = wrapper._assess_risk(func, {})
            assert risk == ActionRiskLevel.LOW

    def test_assess_risk_case_insensitive(self, wrapper):
        """Test that risk assessment is case-insensitive"""
        assert wrapper._assess_risk("DELETE_user", {}) == ActionRiskLevel.CRITICAL
        assert wrapper._assess_risk("Create_Product", {}) == ActionRiskLevel.HIGH


class TestApprovalRequirement:
    """Test approval requirement determination"""

    def test_requires_approval_with_override_true(self, wrapper):
        """Test that override=True forces approval"""
        requires = wrapper._requires_approval("read_data", {}, override=True)
        assert requires is True

    def test_requires_approval_with_override_false(self, wrapper):
        """Test that override=False bypasses approval"""
        requires = wrapper._requires_approval("delete_data", {}, override=False)
        assert requires is False

    def test_requires_approval_low_risk_auto_approve(self, wrapper):
        """Test that low-risk actions don't require approval with auto_approve_low_risk"""
        requires = wrapper._requires_approval("read_data", {}, override=None)
        assert requires is False

    def test_requires_approval_medium_risk(self, wrapper):
        """Test that medium-risk actions require approval"""
        requires = wrapper._requires_approval("analyze_data", {}, override=None)
        assert requires is True

    def test_requires_approval_high_risk(self, wrapper):
        """Test that high-risk actions require approval"""
        requires = wrapper._requires_approval("update_data", {}, override=None)
        assert requires is True

    def test_requires_approval_critical_risk(self, wrapper):
        """Test that critical-risk actions require approval"""
        requires = wrapper._requires_approval("deploy_changes", {}, override=None)
        assert requires is True


class TestNetworkCallDetection:
    """Test network call detection"""

    def test_involves_network_call_api_keywords(self, wrapper):
        """Test detection of API-related keywords"""
        action = BoundedAction(
            action_id="test",
            agent_name="test",
            function_name="call_api_endpoint",
            parameters={},
            risk_level=ActionRiskLevel.HIGH,
            requires_approval=True,
        )
        assert wrapper._involves_network_call(action) is True

    def test_involves_network_call_http_keywords(self, wrapper):
        """Test detection of HTTP-related keywords"""
        network_functions = ["http_get", "fetch_data", "download_file", "upload_image"]

        for func in network_functions:
            action = BoundedAction(
                action_id="test",
                agent_name="test",
                function_name=func,
                parameters={},
                risk_level=ActionRiskLevel.MEDIUM,
                requires_approval=True,
            )
            assert wrapper._involves_network_call(action) is True

    def test_involves_network_call_local_functions(self, wrapper):
        """Test that local functions are not flagged"""
        local_functions = ["read_file", "process_data", "calculate_sum"]

        for func in local_functions:
            action = BoundedAction(
                action_id="test",
                agent_name="test",
                function_name=func,
                parameters={},
                risk_level=ActionRiskLevel.LOW,
                requires_approval=False,
            )
            assert wrapper._involves_network_call(action) is False


class TestExecuteLowRisk:
    """Test execution of low-risk actions"""

    @pytest.mark.asyncio
    async def test_execute_low_risk_auto_approved(self, wrapper):
        """Test that low-risk actions execute immediately"""
        result = await wrapper.execute(function_name="read_data", parameters={"source": "test.csv"})

        assert result["status"] == "completed"
        assert "result" in result
        assert result["action_id"] is not None

    @pytest.mark.asyncio
    async def test_execute_records_audit_log(self, wrapper, temp_audit_path):
        """Test that execution is audited"""
        await wrapper.execute(function_name="read_data", parameters={"source": "test.csv"})

        # Check audit log file was created
        audit_files = list(Path(temp_audit_path).glob("audit_*.jsonl"))
        assert len(audit_files) > 0

    @pytest.mark.asyncio
    async def test_execute_tracks_execution_time(self, wrapper):
        """Test that execution time is tracked"""
        result = await wrapper.execute(function_name="read_data", parameters={"source": "test.csv"})

        assert "execution_time_seconds" in result
        assert result["execution_time_seconds"] >= 0


class TestExecuteHighRisk:
    """Test execution of high-risk actions"""

    @pytest.mark.asyncio
    async def test_execute_high_risk_requires_approval(self, wrapper):
        """Test that high-risk actions require approval"""
        result = await wrapper.execute(
            function_name="update_data", parameters={"id": "123", "data": {"field": "value"}}
        )

        assert result["status"] == "pending_approval"
        assert "action_id" in result
        assert "review_command" in result

    @pytest.mark.asyncio
    async def test_execute_critical_requires_approval(self, wrapper):
        """Test that critical actions require approval"""
        result = await wrapper.execute(
            function_name="delete_resource", parameters={"resource_id": "important_resource"}
        )

        assert result["status"] == "pending_approval"

    @pytest.mark.asyncio
    async def test_execute_adds_to_pending_queue(self, wrapper):
        """Test that pending actions are added to queue"""
        initial_count = len(wrapper.pending_actions)

        await wrapper.execute(function_name="update_data", parameters={"id": "123"})

        assert len(wrapper.pending_actions) == initial_count + 1


class TestEmergencyControls:
    """Test emergency stop and pause controls"""

    @pytest.mark.asyncio
    async def test_emergency_stop_blocks_execution(self, wrapper):
        """Test that emergency stop blocks all execution"""
        wrapper.emergency_shutdown("Test emergency")

        result = await wrapper.execute(function_name="read_data", parameters={"source": "test.csv"})

        assert result["status"] == "blocked"
        assert "emergency" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_pause_queues_execution(self, wrapper):
        """Test that pause queues execution"""
        wrapper.pause()

        result = await wrapper.execute(function_name="read_data", parameters={"source": "test.csv"})

        assert result["status"] == "queued"
        assert "paused" in result["error"].lower()

    def test_resume_after_pause(self, wrapper):
        """Test resuming after pause"""
        wrapper.pause()
        assert wrapper.paused is True

        wrapper.resume()
        assert wrapper.paused is False

    def test_emergency_stop_audits_pending_actions(self, wrapper):
        """Test that emergency stop audits all pending actions"""
        # Create pending action
        action = BoundedAction(
            action_id="test_action",
            agent_name="test",
            function_name="update_data",
            parameters={},
            risk_level=ActionRiskLevel.HIGH,
            requires_approval=True,
        )
        wrapper.pending_actions["test_action"] = action

        wrapper.emergency_shutdown("Test emergency")

        # Check audit trail
        assert len(action.audit_trail) > 0
        assert any("emergency_stop" in str(entry) for entry in action.audit_trail)


class TestApproveAction:
    """Test action approval workflow"""

    @pytest.mark.asyncio
    async def test_approve_action_executes(self, wrapper):
        """Test that approving action executes it"""
        # Create pending action
        result = await wrapper.execute(function_name="update_data", parameters={"id": "123"})
        action_id = result["action_id"]

        # Approve and execute
        approval_result = await wrapper.approve_action(action_id, "test_operator")

        assert approval_result["status"] == "completed"
        assert action_id not in wrapper.pending_actions

    @pytest.mark.asyncio
    async def test_approve_nonexistent_action(self, wrapper):
        """Test approving non-existent action returns error"""
        result = await wrapper.approve_action("nonexistent_id", "operator")

        assert result["status"] == "error"
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_approve_updates_audit_trail(self, wrapper):
        """Test that approval updates audit trail"""
        result = await wrapper.execute(function_name="update_data", parameters={"id": "123"})
        action_id = result["action_id"]

        await wrapper.approve_action(action_id, "test_operator")

        # Check completed actions for audit trail
        assert len(wrapper.completed_actions) > 0


class TestRejectAction:
    """Test action rejection workflow"""

    @pytest.mark.asyncio
    async def test_reject_action_removes_from_queue(self, wrapper):
        """Test that rejecting action removes it from queue"""
        result = await wrapper.execute(function_name="update_data", parameters={"id": "123"})
        action_id = result["action_id"]

        reject_result = await wrapper.reject_action(action_id, "operator", "Not authorized")

        assert reject_result["status"] == "rejected"
        assert action_id not in wrapper.pending_actions

    @pytest.mark.asyncio
    async def test_reject_nonexistent_action(self, wrapper):
        """Test rejecting non-existent action returns error"""
        result = await wrapper.reject_action("nonexistent", "operator", "reason")

        assert result["status"] == "error"


class TestLocalOnlyMode:
    """Test local-only mode enforcement"""

    @pytest.mark.asyncio
    async def test_local_only_blocks_network_calls(self, wrapper):
        """Test that local-only mode blocks network calls"""
        result = await wrapper.execute(function_name="api_call", parameters={"endpoint": "https://example.com"})

        # Action requires approval first
        action_id = result["action_id"]

        # Approve it
        approval_result = await wrapper.approve_action(action_id, "operator")

        # Should be blocked by network check
        assert approval_result["status"] == "blocked"
        assert "network" in approval_result["error"].lower()

    @pytest.mark.asyncio
    async def test_local_only_tracks_blocked_calls(self, wrapper):
        """Test that blocked network calls are tracked"""
        initial_count = wrapper.network_calls_blocked

        result = await wrapper.execute(function_name="api_call", parameters={"endpoint": "https://example.com"})
        action_id = result["action_id"]
        await wrapper.approve_action(action_id, "operator")

        assert wrapper.network_calls_blocked > initial_count


class TestGetStatus:
    """Test status retrieval"""

    @pytest.mark.asyncio
    async def test_get_status_complete(self, wrapper):
        """Test getting complete wrapper status"""
        status = await wrapper.get_status()

        assert "agent_name" in status
        assert "bounded_controls" in status
        assert "actions" in status
        assert "network" in status

    @pytest.mark.asyncio
    async def test_get_status_includes_counts(self, wrapper):
        """Test that status includes action counts"""
        # Create some pending actions
        await wrapper.execute(function_name="update_data", parameters={"id": "1"})
        await wrapper.execute(function_name="update_data", parameters={"id": "2"})

        status = await wrapper.get_status()

        assert status["actions"]["pending"] == 2


class TestActionIdGeneration:
    """Test action ID generation"""

    def test_generate_action_id_unique(self, wrapper):
        """Test that generated action IDs are unique"""
        id1 = wrapper._generate_action_id()
        id2 = wrapper._generate_action_id()

        assert id1 != id2

    def test_generate_action_id_format(self, wrapper):
        """Test that action ID has expected format"""
        action_id = wrapper._generate_action_id()

        assert wrapper.wrapped_agent.agent_name in action_id
        assert "_" in action_id


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_execute_nonexistent_function(self, wrapper):
        """Test executing non-existent function"""
        result = await wrapper.execute(function_name="nonexistent_function", parameters={})

        # Should still create action and try to execute
        assert result["status"] in ["pending_approval", "error"]

    @pytest.mark.asyncio
    async def test_execute_with_empty_parameters(self, wrapper):
        """Test executing with empty parameters"""
        result = await wrapper.execute(function_name="read_data", parameters={})

        assert "status" in result

    @pytest.mark.asyncio
    async def test_execute_with_complex_parameters(self, wrapper):
        """Test executing with complex nested parameters"""
        complex_params = {
            "nested": {"level1": {"level2": "value"}},
            "array": [1, 2, 3],
            "mixed": {"key": "value", "number": 42},
        }

        result = await wrapper.execute(function_name="process_data", parameters=complex_params)

        assert "status" in result
