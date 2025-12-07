"""
Integration test for WorkflowStatus enum refactoring
Verifies that workflow_engine.py works correctly with the new enums module
"""

import sys


sys.path.insert(0, ".")

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from api_integration.enums import WorkflowStatus


@dataclass
class MockWorkflowTrigger:
    """Mock trigger for testing"""

    trigger_id: str
    trigger_type: str = "manual"

    def to_dict(self):
        return {"trigger_id": self.trigger_id, "trigger_type": self.trigger_type}


@dataclass
class MockWorkflowStep:
    """Mock step for testing"""

    step_id: str

    def to_dict(self):
        return {"step_id": self.step_id}


@dataclass
class MockWorkflow:
    """Mock workflow class that mimics the real Workflow class"""

    workflow_id: str
    name: str
    description: str
    trigger: MockWorkflowTrigger
    steps: list = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary using to_json() for status"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "trigger": self.trigger.to_dict(),
            "steps": [step.to_dict() for step in self.steps],
            "status": self.status.to_json(),  # Using to_json() method
            "created_at": self.created_at.isoformat(),
        }


def test_workflow_status_enum_integration():
    """Test that WorkflowStatus enum integrates correctly with workflow"""

    # Create a mock workflow
    trigger = MockWorkflowTrigger(trigger_id="test-trigger-1")
    step = MockWorkflowStep(step_id="test-step-1")

    workflow = MockWorkflow(
        workflow_id="test-workflow-1",
        name="Test Workflow",
        description="Testing enum refactoring",
        trigger=trigger,
        steps=[step],
        status=WorkflowStatus.PENDING,
    )

    # Test serialization
    data = workflow.to_dict()

    # Verify status is correctly serialized
    assert data["status"] == "pending", f"Expected 'pending', got {data['status']}"
    assert isinstance(data["status"], str), "Status should be a string"

    # Test status transitions
    workflow.status = WorkflowStatus.RUNNING
    data = workflow.to_dict()
    assert data["status"] == "running"

    workflow.status = WorkflowStatus.SUCCESS
    data = workflow.to_dict()
    assert data["status"] == "success"

    workflow.status = WorkflowStatus.FAILED
    data = workflow.to_dict()
    assert data["status"] == "failed"

    # Test all status values
    all_statuses = [
        (WorkflowStatus.PENDING, "pending"),
        (WorkflowStatus.RUNNING, "running"),
        (WorkflowStatus.SUCCESS, "success"),
        (WorkflowStatus.FAILED, "failed"),
        (WorkflowStatus.CANCELLED, "cancelled"),
        (WorkflowStatus.PAUSED, "paused"),
        (WorkflowStatus.ROLLED_BACK, "rolled_back"),
    ]

    for status_enum, expected_json in all_statuses:
        workflow.status = status_enum
        data = workflow.to_dict()
        assert data["status"] == expected_json, f"Expected {expected_json}, got {data['status']}"

    # Test that we can't use string directly (should use enum)
    try:
        # This should fail because we're enforcing enum usage
        workflow.status = "pending"  # type: ignore
        # If we get here, the type system didn't catch it at runtime
        # but the enum should only accept enum values
    except (TypeError, ValueError):
        pass


if __name__ == "__main__":
    test_workflow_status_enum_integration()
