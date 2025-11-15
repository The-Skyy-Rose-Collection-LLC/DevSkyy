"""
Tests for api_integration.enums module
Tests the SerializableEnum base class and WorkflowStatus enum
"""

import pytest

from api_integration.enums import SerializableEnum, WorkflowStatus


class TestSerializableEnum:
    """Test cases for SerializableEnum base class"""

    def test_to_json_returns_string_value(self):
        """Test that to_json() returns the string value of the enum"""
        status = WorkflowStatus.PENDING
        assert status.to_json() == "pending"

        status = WorkflowStatus.RUNNING
        assert status.to_json() == "running"

    def test_to_json_for_all_workflow_statuses(self):
        """Test to_json() for all WorkflowStatus values"""
        assert WorkflowStatus.PENDING.to_json() == "pending"
        assert WorkflowStatus.RUNNING.to_json() == "running"
        assert WorkflowStatus.SUCCESS.to_json() == "success"
        assert WorkflowStatus.FAILED.to_json() == "failed"
        assert WorkflowStatus.CANCELLED.to_json() == "cancelled"
        assert WorkflowStatus.PAUSED.to_json() == "paused"
        assert WorkflowStatus.ROLLED_BACK.to_json() == "rolled_back"

    def test_from_string_creates_correct_enum(self):
        """Test that from_string() creates the correct enum member"""
        status = WorkflowStatus.from_string("pending")
        assert status == WorkflowStatus.PENDING

        status = WorkflowStatus.from_string("running")
        assert status == WorkflowStatus.RUNNING

    def test_from_string_for_all_workflow_statuses(self):
        """Test from_string() for all WorkflowStatus values"""
        assert WorkflowStatus.from_string("pending") == WorkflowStatus.PENDING
        assert WorkflowStatus.from_string("running") == WorkflowStatus.RUNNING
        assert WorkflowStatus.from_string("success") == WorkflowStatus.SUCCESS
        assert WorkflowStatus.from_string("failed") == WorkflowStatus.FAILED
        assert WorkflowStatus.from_string("cancelled") == WorkflowStatus.CANCELLED
        assert WorkflowStatus.from_string("paused") == WorkflowStatus.PAUSED
        assert WorkflowStatus.from_string("rolled_back") == WorkflowStatus.ROLLED_BACK

    def test_from_string_raises_value_error_for_invalid_value(self):
        """Test that from_string() raises ValueError for invalid values"""
        with pytest.raises(ValueError) as exc_info:
            WorkflowStatus.from_string("invalid_status")

        assert "No WorkflowStatus member with value 'invalid_status'" in str(exc_info.value)

    def test_enum_members_have_correct_values(self):
        """Test that enum members have the expected string values"""
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.RUNNING.value == "running"
        assert WorkflowStatus.SUCCESS.value == "success"
        assert WorkflowStatus.FAILED.value == "failed"
        assert WorkflowStatus.CANCELLED.value == "cancelled"
        assert WorkflowStatus.PAUSED.value == "paused"
        assert WorkflowStatus.ROLLED_BACK.value == "rolled_back"

    def test_enum_comparison(self):
        """Test that enum members can be compared correctly"""
        status1 = WorkflowStatus.PENDING
        status2 = WorkflowStatus.PENDING
        status3 = WorkflowStatus.RUNNING

        assert status1 == status2
        assert status1 != status3
        assert status1 is status2  # Same instance

    def test_enum_iteration(self):
        """Test that we can iterate over all enum members"""
        all_statuses = list(WorkflowStatus)

        assert len(all_statuses) == 7
        assert WorkflowStatus.PENDING in all_statuses
        assert WorkflowStatus.RUNNING in all_statuses
        assert WorkflowStatus.SUCCESS in all_statuses
        assert WorkflowStatus.FAILED in all_statuses
        assert WorkflowStatus.CANCELLED in all_statuses
        assert WorkflowStatus.PAUSED in all_statuses
        assert WorkflowStatus.ROLLED_BACK in all_statuses

    def test_enum_in_dict_serialization(self):
        """Test that enum serializes correctly in dictionaries"""
        data = {"status": WorkflowStatus.PENDING.to_json(), "message": "Workflow is pending"}

        assert data["status"] == "pending"
        assert isinstance(data["status"], str)

    def test_enum_roundtrip_serialization(self):
        """Test roundtrip serialization: enum -> json -> enum"""
        original = WorkflowStatus.SUCCESS
        json_value = original.to_json()
        restored = WorkflowStatus.from_string(json_value)

        assert original == restored
        assert original.value == restored.value


class TestWorkflowStatus:
    """Test cases specific to WorkflowStatus enum"""

    def test_workflow_status_has_all_expected_members(self):
        """Test that WorkflowStatus has all expected status values"""
        expected_members = {"PENDING", "RUNNING", "SUCCESS", "FAILED", "CANCELLED", "PAUSED", "ROLLED_BACK"}

        actual_members = {member.name for member in WorkflowStatus}
        assert actual_members == expected_members

    def test_workflow_status_pending_is_default(self):
        """Test that PENDING is a valid initial status"""
        # This is important for workflow initialization
        status = WorkflowStatus.PENDING
        assert status.to_json() == "pending"

    def test_workflow_status_transitions(self):
        """Test common workflow status transitions"""
        # Simulate a workflow lifecycle
        statuses = [WorkflowStatus.PENDING, WorkflowStatus.RUNNING, WorkflowStatus.SUCCESS]

        json_values = [s.to_json() for s in statuses]
        assert json_values == ["pending", "running", "success"]

    def test_workflow_status_failure_states(self):
        """Test that failure states are properly defined"""
        failure_states = [WorkflowStatus.FAILED, WorkflowStatus.CANCELLED, WorkflowStatus.ROLLED_BACK]

        for state in failure_states:
            assert state.to_json() in ["failed", "cancelled", "rolled_back"]

    def test_workflow_status_inherits_from_serializable_enum(self):
        """Test that WorkflowStatus inherits from SerializableEnum"""
        assert issubclass(WorkflowStatus, SerializableEnum)

        # Ensure it has the to_json method
        status = WorkflowStatus.RUNNING
        assert hasattr(status, "to_json")
        assert callable(status.to_json)

    def test_workflow_status_string_representation(self):
        """Test the string representation of WorkflowStatus"""
        status = WorkflowStatus.RUNNING

        # The name should be accessible
        assert status.name == "RUNNING"

        # The value should be accessible
        assert status.value == "running"

        # The to_json() should return the value
        assert status.to_json() == "running"


class TestEnumModularity:
    """Test cases for enum module organization and imports"""

    def test_enums_module_exists(self):
        """Test that the enums module can be imported"""
        import api_integration.enums

        assert api_integration.enums is not None

    def test_serializable_enum_is_importable(self):
        """Test that SerializableEnum can be imported"""
        from api_integration.enums import SerializableEnum

        assert SerializableEnum is not None

    def test_workflow_status_is_importable(self):
        """Test that WorkflowStatus can be imported"""
        from api_integration.enums import WorkflowStatus

        assert WorkflowStatus is not None

    def test_enum_module_has_correct_exports(self):
        """Test that the enums module exports expected classes"""
        import api_integration.enums as enums_module

        assert hasattr(enums_module, "SerializableEnum")
        assert hasattr(enums_module, "WorkflowStatus")


class TestSerializableEnumEdgeCases:
    """Test edge cases and error handling for SerializableEnum"""

    def test_from_string_with_empty_string(self):
        """Test from_string() with empty string"""
        with pytest.raises(ValueError):
            WorkflowStatus.from_string("")

    def test_from_string_case_sensitivity(self):
        """Test that from_string() is case-sensitive"""
        # Valid lowercase value
        status = WorkflowStatus.from_string("pending")
        assert status == WorkflowStatus.PENDING

        # Invalid uppercase value should fail
        with pytest.raises(ValueError):
            WorkflowStatus.from_string("PENDING")

    def test_to_json_is_idempotent(self):
        """Test that calling to_json() multiple times gives same result"""
        status = WorkflowStatus.SUCCESS

        json1 = status.to_json()
        json2 = status.to_json()
        json3 = status.to_json()

        assert json1 == json2 == json3 == "success"

    def test_enum_cannot_be_modified(self):
        """Test that enum values are immutable"""
        status = WorkflowStatus.PENDING

        # Attempting to modify should raise an error
        with pytest.raises(AttributeError):
            status.value = "modified"
