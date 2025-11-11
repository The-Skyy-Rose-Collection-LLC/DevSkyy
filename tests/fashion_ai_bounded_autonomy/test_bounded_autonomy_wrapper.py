"""
Unit tests for BoundedAutonomyWrapper
Tests wrapping agents with bounded autonomy controls
"""

import unittest
import pytest
import tempfile
import shutil
from pathlib import Path

from fashion_ai_bounded_autonomy.bounded_autonomy_wrapper import (
    BoundedAutonomyWrapper,
    ActionRiskLevel,
    BoundedAction
)
from agent.modules.base_agent import BaseAgent, AgentStatus


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
        wrapped_agent=mock_agent,
        auto_approve_low_risk=True,
        local_only=True,
        audit_log_path=temp_audit_path
    )


class TestBoundedAutonomyWrapperInitialization(unittest.TestCase):
    """Test wrapper initialization"""

    def test_init_creates_audit_directory(self, mock_agent, temp_audit_path):
        """Test that initialization creates audit log directory"""
        audit_path = Path(temp_audit_path) / "custom_audit"
        BoundedAutonomyWrapper(
            wrapped_agent=mock_agent,
            audit_log_path=str(audit_path)
        )
        self.assertTrue(audit_path.exists())

    def test_init_sets_default_values(self, wrapper):
        """Test that initialization sets default values"""
        self.assertIs(wrapper.auto_approve_low_risk, True)
        self.assertIs(wrapper.local_only, True)
        self.assertIs(wrapper.emergency_stop, False)
        self.assertIs(wrapper.paused, False)
        self.assertEqual(len(wrapper.pending_actions), 0)
        self.assertEqual(len(wrapper.completed_actions), 0)


class TestRiskAssessment(unittest.TestCase):
    """Test risk assessment logic"""

    def test_assess_risk_critical_operations(self, wrapper):
        """Test assessment of critical operations"""
        critical_functions = ["deploy_model", "delete_database", "drop_table", "modify_config"]
        
        for func in critical_functions:
            risk = wrapper._assess_risk(func, {})
            self.assertEqual(risk, ActionRiskLevel.CRITICAL)

    def test_assess_risk_high_operations(self, wrapper):
        """Test assessment of high-risk operations"""
        high_risk_functions = ["create_user", "update_product", "insert_record", "send_email"]
        
        for func in high_risk_functions:
            risk = wrapper._assess_risk(func, {})
            self.assertEqual(risk, ActionRiskLevel.HIGH)

    def test_assess_risk_medium_operations(self, wrapper):
        """Test assessment of medium-risk operations"""
        medium_risk_functions = ["analyze_data", "process_batch", "calculate_metrics", "generate_report"]
        
        for func in medium_risk_functions:
            risk = wrapper._assess_risk(func, {})
            self.assertEqual(risk, ActionRiskLevel.MEDIUM)

    def test_assess_risk_low_operations(self, wrapper):
        """Test assessment of low-risk operations"""
        low_risk_functions = ["get_data", "fetch_info", "query_status", "list_items"]
        
        for func in low_risk_functions:
            risk = wrapper._assess_risk(func, {})
            self.assertEqual(risk, ActionRiskLevel.LOW)

    def test_assess_risk_case_insensitive(self, wrapper):
        """Test that risk assessment is case-insensitive"""
        self.assertEqual(wrapper._assess_risk("DELETE_user", {}), ActionRiskLevel.CRITICAL)
        self.assertEqual(wrapper._assess_risk("Create_Product", {}), ActionRiskLevel.HIGH)


class TestApprovalRequirement(unittest.TestCase):
    """Test approval requirement determination"""

    def test_requires_approval_with_override_true(self, wrapper):
        """Test that override=True forces approval"""
        requires = wrapper._requires_approval("read_data", {}, override=True)
        self.assertIs(requires, True)

    def test_requires_approval_with_override_false(self, wrapper):
        """Test that override=False bypasses approval"""
        requires = wrapper._requires_approval("delete_data", {}, override=False)
        self.assertIs(requires, False)

    def test_requires_approval_low_risk_auto_approve(self, wrapper):
        """Test that low-risk actions don't require approval with auto_approve_low_risk"""
        requires = wrapper._requires_approval("read_data", {}, override=None)
        self.assertIs(requires, False)

    def test_requires_approval_medium_risk(self, wrapper):
        """Test that medium-risk actions require approval"""
        requires = wrapper._requires_approval("analyze_data", {}, override=None)
        self.assertIs(requires, True)

    def test_requires_approval_high_risk(self, wrapper):
        """Test that high-risk actions require approval"""
        requires = wrapper._requires_approval("update_data", {}, override=None)
        self.assertIs(requires, True)

    def test_requires_approval_critical_risk(self, wrapper):
        """Test that critical-risk actions require approval"""
        requires = wrapper._requires_approval("deploy_changes", {}, override=None)
        self.assertIs(requires, True)


class TestNetworkCallDetection(unittest.TestCase):
    """Test network call detection"""

    def test_involves_network_call_api_keywords(self, wrapper):
        """Test detection of API-related keywords"""
        action = BoundedAction(
            action_id="test",
            agent_name="test",
            function_name="call_api_endpoint",
            parameters={},
            risk_level=ActionRiskLevel.HIGH,
            requires_approval=True
        )
        self.assertIs(wrapper._involves_network_call(action), True)

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
                requires_approval=True
            )
            self.assertIs(wrapper._involves_network_call(action), True)

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
                requires_approval=False
            )
            self.assertIs(wrapper._involves_network_call(action), False)


class TestExecuteLowRisk(unittest.TestCase):
    """Test execution of low-risk actions"""

    @pytest.mark.asyncio
    async def test_execute_low_risk_auto_approved(self, wrapper):
        """Test that low-risk actions execute immediately"""
        result = await wrapper.execute(
            function_name="read_data",
            parameters={"source": "test.csv"}
        )
        
        self.assertEqual(result["status"], "completed")
        self.assertIn("result", result)
        self.assertIsNotNone(result["action_id"])

    @pytest.mark.asyncio
    async def test_execute_records_audit_log(self, wrapper, temp_audit_path):
        """Test that execution is audited"""
        await wrapper.execute(
            function_name="read_data",
            parameters={"source": "test.csv"}
        )
        
        # Check audit log file was created
        audit_files = list(Path(temp_audit_path).glob("audit_*.jsonl"))
        self.assertGreater(len(audit_files), 0)

    @pytest.mark.asyncio
    async def test_execute_tracks_execution_time(self, wrapper):
        """Test that execution time is tracked"""
        result = await wrapper.execute(
            function_name="read_data",
            parameters={"source": "test.csv"}
        )
        
        self.assertIn("execution_time_seconds", result)
        self.assertGreater(result["execution_time_seconds"], = 0)


class TestExecuteHighRisk(unittest.TestCase):
    """Test execution of high-risk actions"""

    @pytest.mark.asyncio
    async def test_execute_high_risk_requires_approval(self, wrapper):
        """Test that high-risk actions require approval"""
        result = await wrapper.execute(
            function_name="update_data",
            parameters={"id": "123", "data": {"field": "value"}}
        )
        
        self.assertEqual(result["status"], "pending_approval")
        self.assertIn("action_id", result)
        self.assertIn("review_command", result)

    @pytest.mark.asyncio
    async def test_execute_critical_requires_approval(self, wrapper):
        """Test that critical actions require approval"""
        result = await wrapper.execute(
            function_name="delete_resource",
            parameters={"resource_id": "important_resource"}
        )
        
        self.assertEqual(result["status"], "pending_approval")

    @pytest.mark.asyncio
    async def test_execute_adds_to_pending_queue(self, wrapper):
        """Test that pending actions are added to queue"""
        initial_count = len(wrapper.pending_actions)
        
        await wrapper.execute(
            function_name="update_data",
            parameters={"id": "123"}
        )
        
        self.assertEqual(len(wrapper.pending_actions), initial_count + 1)


class TestEmergencyControls(unittest.TestCase):
    """Test emergency stop and pause controls"""

    @pytest.mark.asyncio
    async def test_emergency_stop_blocks_execution(self, wrapper):
        """Test that emergency stop blocks all execution"""
        wrapper.emergency_shutdown("Test emergency")
        
        result = await wrapper.execute(
            function_name="read_data",
            parameters={"source": "test.csv"}
        )
        
        self.assertEqual(result["status"], "blocked")
        self.assertIn("emergency", result["error"].lower())

    @pytest.mark.asyncio
    async def test_pause_queues_execution(self, wrapper):
        """Test that pause queues execution"""
        wrapper.pause()
        
        result = await wrapper.execute(
            function_name="read_data",
            parameters={"source": "test.csv"}
        )
        
        self.assertEqual(result["status"], "queued")
        self.assertIn("paused", result["error"].lower())

    def test_resume_after_pause(self, wrapper):
        """Test resuming after pause"""
        wrapper.pause()
        self.assertIs(wrapper.paused, True)
        
        wrapper.resume()
        self.assertIs(wrapper.paused, False)

    def test_emergency_stop_audits_pending_actions(self, wrapper):
        """Test that emergency stop audits all pending actions"""
        # Create pending action
        action = BoundedAction(
            action_id="test_action",
            agent_name="test",
            function_name="update_data",
            parameters={},
            risk_level=ActionRiskLevel.HIGH,
            requires_approval=True
        )
        wrapper.pending_actions["test_action"] = action
        
        wrapper.emergency_shutdown("Test emergency")
        
        # Check audit trail
        self.assertGreater(len(action.audit_trail), 0)
        self.assertIn(any("emergency_stop", str(entry) for entry in action.audit_trail))


class TestApproveAction(unittest.TestCase):
    """Test action approval workflow"""

    @pytest.mark.asyncio
    async def test_approve_action_executes(self, wrapper):
        """Test that approving action executes it"""
        # Create pending action
        result = await wrapper.execute(
            function_name="update_data",
            parameters={"id": "123"}
        )
        action_id = result["action_id"]
        
        # Approve and execute
        approval_result = await wrapper.approve_action(action_id, "test_operator")
        
        self.assertEqual(approval_result["status"], "completed")
        self.assertIn(action_id not, wrapper.pending_actions)

    @pytest.mark.asyncio
    async def test_approve_nonexistent_action(self, wrapper):
        """Test approving non-existent action returns error"""
        result = await wrapper.approve_action("nonexistent_id", "operator")
        
        self.assertEqual(result["status"], "error")
        self.assertIn("not found", result["error"].lower())

    @pytest.mark.asyncio
    async def test_approve_updates_audit_trail(self, wrapper):
        """Test that approval updates audit trail"""
        result = await wrapper.execute(
            function_name="update_data",
            parameters={"id": "123"}
        )
        action_id = result["action_id"]
        
        await wrapper.approve_action(action_id, "test_operator")
        
        # Check completed actions for audit trail
        self.assertGreater(len(wrapper.completed_actions), 0)


class TestRejectAction(unittest.TestCase):
    """Test action rejection workflow"""

    @pytest.mark.asyncio
    async def test_reject_action_removes_from_queue(self, wrapper):
        """Test that rejecting action removes it from queue"""
        result = await wrapper.execute(
            function_name="update_data",
            parameters={"id": "123"}
        )
        action_id = result["action_id"]
        
        reject_result = await wrapper.reject_action(action_id, "operator", "Not authorized")
        
        self.assertEqual(reject_result["status"], "rejected")
        self.assertIn(action_id not, wrapper.pending_actions)

    @pytest.mark.asyncio
    async def test_reject_nonexistent_action(self, wrapper):
        """Test rejecting non-existent action returns error"""
        result = await wrapper.reject_action("nonexistent", "operator", "reason")
        
        self.assertEqual(result["status"], "error")


class TestLocalOnlyMode(unittest.TestCase):
    """Test local-only mode enforcement"""

    @pytest.mark.asyncio
    async def test_local_only_blocks_network_calls(self, wrapper):
        """Test that local-only mode blocks network calls"""
        result = await wrapper.execute(
            function_name="api_call",
            parameters={"endpoint": "https://example.com"}
        )
        
        # Action requires approval first
        action_id = result["action_id"]
        
        # Approve it
        approval_result = await wrapper.approve_action(action_id, "operator")
        
        # Should be blocked by network check
        self.assertEqual(approval_result["status"], "blocked")
        self.assertIn("network", approval_result["error"].lower())

    @pytest.mark.asyncio
    async def test_local_only_tracks_blocked_calls(self, wrapper):
        """Test that blocked network calls are tracked"""
        initial_count = wrapper.network_calls_blocked
        
        result = await wrapper.execute(
            function_name="api_call",
            parameters={"endpoint": "https://example.com"}
        )
        action_id = result["action_id"]
        await wrapper.approve_action(action_id, "operator")
        
        self.assertGreater(wrapper.network_calls_blocked, initial_count)


class TestGetStatus(unittest.TestCase):
    """Test status retrieval"""

    @pytest.mark.asyncio
    async def test_get_status_complete(self, wrapper):
        """Test getting complete wrapper status"""
        status = await wrapper.get_status()
        
        self.assertIn("agent_name", status)
        self.assertIn("bounded_controls", status)
        self.assertIn("actions", status)
        self.assertIn("network", status)

    @pytest.mark.asyncio
    async def test_get_status_includes_counts(self, wrapper):
        """Test that status includes action counts"""
        # Create some pending actions
        await wrapper.execute(function_name="update_data", parameters={"id": "1"})
        await wrapper.execute(function_name="update_data", parameters={"id": "2"})
        
        status = await wrapper.get_status()
        
        self.assertEqual(status["actions"]["pending"], 2)


class TestActionIdGeneration(unittest.TestCase):
    """Test action ID generation"""

    def test_generate_action_id_unique(self, wrapper):
        """Test that generated action IDs are unique"""
        id1 = wrapper._generate_action_id()
        id2 = wrapper._generate_action_id()
        
        self.assertNotEqual(id1, id2)

    def test_generate_action_id_format(self, wrapper):
        """Test that action ID has expected format"""
        action_id = wrapper._generate_action_id()
        
        self.assertIn(wrapper.wrapped_agent.agent_name, action_id)
        self.assertIn("_", action_id)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_execute_nonexistent_function(self, wrapper):
        """Test executing non-existent function"""
        result = await wrapper.execute(
            function_name="nonexistent_function",
            parameters={}
        )
        
        # Should still create action and try to execute
        self.assertIn(result["status"], ["pending_approval", "error"])

    @pytest.mark.asyncio
    async def test_execute_with_empty_parameters(self, wrapper):
        """Test executing with empty parameters"""
        result = await wrapper.execute(
            function_name="read_data",
            parameters={}
        )
        
        self.assertIn("status", result)

    @pytest.mark.asyncio
    async def test_execute_with_complex_parameters(self, wrapper):
        """Test executing with complex nested parameters"""
        complex_params = {
            "nested": {"level1": {"level2": "value"}},
            "array": [1, 2, 3],
            "mixed": {"key": "value", "number": 42}
        }
        
        result = await wrapper.execute(
            function_name="process_data",
            parameters=complex_params
        )
        
        self.assertIn("status", result)