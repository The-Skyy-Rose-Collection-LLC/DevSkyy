"""
Tests for api_integration.enums module
Tests the SerializableEnum base class and WorkflowStatus enum
"""
import unittest
import pytest
from api_integration.enums import SerializableEnum, WorkflowStatus


class TestSerializableEnum(unittest.TestCase):
    """Test cases for SerializableEnum base class"""
    
    def test_to_json_returns_string_value(self):
        """Test that to_json() returns the string value of the enum"""
        status = WorkflowStatus.PENDING
        self.assertEqual(status.to_json(), "pending")
        
        status = WorkflowStatus.RUNNING
        self.assertEqual(status.to_json(), "running")
    
    def test_to_json_for_all_workflow_statuses(self):
        """Test to_json() for all WorkflowStatus values"""
        self.assertEqual(WorkflowStatus.PENDING.to_json(), "pending")
        self.assertEqual(WorkflowStatus.RUNNING.to_json(), "running")
        self.assertEqual(WorkflowStatus.SUCCESS.to_json(), "success")
        self.assertEqual(WorkflowStatus.FAILED.to_json(), "failed")
        self.assertEqual(WorkflowStatus.CANCELLED.to_json(), "cancelled")
        self.assertEqual(WorkflowStatus.PAUSED.to_json(), "paused")
        self.assertEqual(WorkflowStatus.ROLLED_BACK.to_json(), "rolled_back")
    
    def test_from_string_creates_correct_enum(self):
        """Test that from_string() creates the correct enum member"""
        status = WorkflowStatus.from_string("pending")
        self.assertEqual(status, WorkflowStatus.PENDING)
        
        status = WorkflowStatus.from_string("running")
        self.assertEqual(status, WorkflowStatus.RUNNING)
    
    def test_from_string_for_all_workflow_statuses(self):
        """Test from_string() for all WorkflowStatus values"""
        self.assertEqual(WorkflowStatus.from_string("pending"), WorkflowStatus.PENDING)
        self.assertEqual(WorkflowStatus.from_string("running"), WorkflowStatus.RUNNING)
        self.assertEqual(WorkflowStatus.from_string("success"), WorkflowStatus.SUCCESS)
        self.assertEqual(WorkflowStatus.from_string("failed"), WorkflowStatus.FAILED)
        self.assertEqual(WorkflowStatus.from_string("cancelled"), WorkflowStatus.CANCELLED)
        self.assertEqual(WorkflowStatus.from_string("paused"), WorkflowStatus.PAUSED)
        self.assertEqual(WorkflowStatus.from_string("rolled_back"), WorkflowStatus.ROLLED_BACK)
    
    def test_from_string_raises_value_error_for_invalid_value(self):
        """Test that from_string() raises ValueError for invalid values"""
        with pytest.raises(ValueError) as exc_info:
            WorkflowStatus.from_string("invalid_status")
        
        self.assertIn("No WorkflowStatus member with value 'invalid_status'", str(exc_info.value))
    
    def test_enum_members_have_correct_values(self):
        """Test that enum members have the expected string values"""
        self.assertEqual(WorkflowStatus.PENDING.value, "pending")
        self.assertEqual(WorkflowStatus.RUNNING.value, "running")
        self.assertEqual(WorkflowStatus.SUCCESS.value, "success")
        self.assertEqual(WorkflowStatus.FAILED.value, "failed")
        self.assertEqual(WorkflowStatus.CANCELLED.value, "cancelled")
        self.assertEqual(WorkflowStatus.PAUSED.value, "paused")
        self.assertEqual(WorkflowStatus.ROLLED_BACK.value, "rolled_back")
    
    def test_enum_comparison(self):
        """Test that enum members can be compared correctly"""
        status1 = WorkflowStatus.PENDING
        status2 = WorkflowStatus.PENDING
        status3 = WorkflowStatus.RUNNING
        
        self.assertEqual(status1, status2)
        self.assertNotEqual(status1, status3)
        self.assertIs(status1, status2  # Same instance)
    
    def test_enum_iteration(self):
        """Test that we can iterate over all enum members"""
        all_statuses = list(WorkflowStatus)
        
        self.assertEqual(len(all_statuses), 7)
        self.assertIn(WorkflowStatus.PENDING, all_statuses)
        self.assertIn(WorkflowStatus.RUNNING, all_statuses)
        self.assertIn(WorkflowStatus.SUCCESS, all_statuses)
        self.assertIn(WorkflowStatus.FAILED, all_statuses)
        self.assertIn(WorkflowStatus.CANCELLED, all_statuses)
        self.assertIn(WorkflowStatus.PAUSED, all_statuses)
        self.assertIn(WorkflowStatus.ROLLED_BACK, all_statuses)
    
    def test_enum_in_dict_serialization(self):
        """Test that enum serializes correctly in dictionaries"""
        data = {
            "status": WorkflowStatus.PENDING.to_json(),
            "message": "Workflow is pending"
        }
        
        self.assertEqual(data["status"], "pending")
        self.assertIsInstance(data["status"], str)
    
    def test_enum_roundtrip_serialization(self):
        """Test roundtrip serialization: enum -> json -> enum"""
        original = WorkflowStatus.SUCCESS
        json_value = original.to_json()
        restored = WorkflowStatus.from_string(json_value)
        
        self.assertEqual(original, restored)
        self.assertEqual(original.value, restored.value)


class TestWorkflowStatus(unittest.TestCase):
    """Test cases specific to WorkflowStatus enum"""
    
    def test_workflow_status_has_all_expected_members(self):
        """Test that WorkflowStatus has all expected status values"""
        expected_members = {
            "PENDING", "RUNNING", "SUCCESS", "FAILED", 
            "CANCELLED", "PAUSED", "ROLLED_BACK"
        }
        
        actual_members = {member.name for member in WorkflowStatus}
        self.assertEqual(actual_members, expected_members)
    
    def test_workflow_status_pending_is_default(self):
        """Test that PENDING is a valid initial status"""
        # This is important for workflow initialization
        status = WorkflowStatus.PENDING
        self.assertEqual(status.to_json(), "pending")
    
    def test_workflow_status_transitions(self):
        """Test common workflow status transitions"""
        # Simulate a workflow lifecycle
        statuses = [
            WorkflowStatus.PENDING,
            WorkflowStatus.RUNNING,
            WorkflowStatus.SUCCESS
        ]
        
        json_values = [s.to_json() for s in statuses]
        self.assertEqual(json_values, ["pending", "running", "success"])
    
    def test_workflow_status_failure_states(self):
        """Test that failure states are properly defined"""
        failure_states = [
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
            WorkflowStatus.ROLLED_BACK
        ]
        
        for state in failure_states:
            self.assertIn(state.to_json(), ["failed", "cancelled", "rolled_back"])
    
    def test_workflow_status_inherits_from_serializable_enum(self):
        """Test that WorkflowStatus inherits from SerializableEnum"""
        self.assertTrue(issubclass(WorkflowStatus, SerializableEnum))
        
        # Ensure it has the to_json method
        status = WorkflowStatus.RUNNING
        self.assertTrue(hasattr(status, 'to_json'))
        self.assertTrue(callable(status.to_json))
    
    def test_workflow_status_string_representation(self):
        """Test the string representation of WorkflowStatus"""
        status = WorkflowStatus.RUNNING
        
        # The name should be accessible
        self.assertEqual(status.name, "RUNNING")
        
        # The value should be accessible
        self.assertEqual(status.value, "running")
        
        # The to_json() should return the value
        self.assertEqual(status.to_json(), "running")


class TestEnumModularity(unittest.TestCase):
    """Test cases for enum module organization and imports"""
    
    def test_enums_module_exists(self):
        """Test that the enums module can be imported"""
        import api_integration.enums
        self.assertIsNotNone(api_integration.enums)
    
    def test_serializable_enum_is_importable(self):
        """Test that SerializableEnum can be imported"""
        from api_integration.enums import SerializableEnum
        self.assertIsNotNone(SerializableEnum)
    
    def test_workflow_status_is_importable(self):
        """Test that WorkflowStatus can be imported"""
        from api_integration.enums import WorkflowStatus
        self.assertIsNotNone(WorkflowStatus)
    
    def test_enum_module_has_correct_exports(self):
        """Test that the enums module exports expected classes"""
        import api_integration.enums as enums_module
        
        self.assertTrue(hasattr(enums_module, 'SerializableEnum'))
        self.assertTrue(hasattr(enums_module, 'WorkflowStatus'))


class TestSerializableEnumEdgeCases(unittest.TestCase):
    """Test edge cases and error handling for SerializableEnum"""
    
    def test_from_string_with_empty_string(self):
        """Test from_string() with empty string"""
        with pytest.raises(ValueError):
            WorkflowStatus.from_string("")
    
    def test_from_string_case_sensitivity(self):
        """Test that from_string() is case-sensitive"""
        # Valid lowercase value
        status = WorkflowStatus.from_string("pending")
        self.assertEqual(status, WorkflowStatus.PENDING)
        
        # Invalid uppercase value should fail
        with pytest.raises(ValueError):
            WorkflowStatus.from_string("PENDING")
    
    def test_to_json_is_idempotent(self):
        """Test that calling to_json() multiple times gives same result"""
        status = WorkflowStatus.SUCCESS
        
        json1 = status.to_json()
        json2 = status.to_json()
        json3 = status.to_json()
        
        self.assertEqual(json1, json2 == json3 == "success")
    
    def test_enum_cannot_be_modified(self):
        """Test that enum values are immutable"""
        status = WorkflowStatus.PENDING
        
        # Attempting to modify should raise an error
        with pytest.raises(AttributeError):
            status.value = "modified"
