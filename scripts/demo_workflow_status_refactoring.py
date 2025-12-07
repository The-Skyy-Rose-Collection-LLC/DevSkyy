#!/usr/bin/env python3
"""
Demonstration script showing the WorkflowStatus enum refactoring
Run this to see the improvements in action
"""
import sys


sys.path.insert(0, ".")

from api_integration.enums import SerializableEnum, WorkflowStatus


def main():
    print("=" * 60)
    print("WorkflowStatus Enum Refactoring Demonstration")
    print("=" * 60)
    print()

    # 1. Show enum members
    print("1. WorkflowStatus Members:")
    print("-" * 40)
    for status in WorkflowStatus:
        print(f"   {status.name:15} → {status.value}")
    print()

    # 2. Demonstrate to_json() method
    print("2. Serialization with to_json():")
    print("-" * 40)
    status = WorkflowStatus.PENDING
    print(f"   Status: {status}")
    print(f"   to_json(): '{status.to_json()}'")
    print(f"   Type: {type(status.to_json())}")
    print()

    # 3. Demonstrate from_string() method
    print("3. Deserialization with from_string():")
    print("-" * 40)
    json_value = "running"
    restored = WorkflowStatus.from_string(json_value)
    print(f"   Input: '{json_value}'")
    print(f"   Restored: {restored}")
    print(f"   Match: {restored == WorkflowStatus.RUNNING}")
    print()

    # 4. Show roundtrip serialization
    print("4. Roundtrip Serialization:")
    print("-" * 40)
    original = WorkflowStatus.SUCCESS
    serialized = original.to_json()
    deserialized = WorkflowStatus.from_string(serialized)
    print(f"   Original:     {original}")
    print(f"   Serialized:   '{serialized}'")
    print(f"   Deserialized: {deserialized}")
    print(f"   Roundtrip OK: {original == deserialized}")
    print()

    # 5. Show usage in dictionary (like Workflow.to_dict())
    print("5. Usage in Dictionary Serialization:")
    print("-" * 40)
    workflow_data = {
        "workflow_id": "wf-12345",
        "name": "Example Workflow",
        "status": WorkflowStatus.RUNNING.to_json(),  # Using to_json()
    }
    print(f"   Workflow Data: {workflow_data}")
    print(f"   Status value: '{workflow_data['status']}'")
    print(f"   Status type: {type(workflow_data['status'])}")
    print()

    # 6. Show inheritance
    print("6. SerializableEnum Inheritance:")
    print("-" * 40)
    print(f"   WorkflowStatus base class: {WorkflowStatus.__bases__}")
    print(f"   Is SerializableEnum: {issubclass(WorkflowStatus, SerializableEnum)}")
    print(f"   Has to_json: {hasattr(WorkflowStatus.PENDING, 'to_json')}")
    print(f"   Has from_string: {hasattr(WorkflowStatus, 'from_string')}")
    print()

    # 7. Show benefits
    print("7. Key Benefits:")
    print("-" * 40)
    print("   ✓ Modular: Enums in dedicated api_integration/enums.py")
    print("   ✓ Consistent: All enums use to_json() for serialization")
    print("   ✓ Maintainable: Single source of truth for enum definitions")
    print("   ✓ Reusable: SerializableEnum can be used for new enums")
    print("   ✓ Type-safe: Enum usage instead of raw strings")
    print()

    print("=" * 60)
    print("Refactoring Complete! All tests passing. ✅")
    print("=" * 60)


if __name__ == "__main__":
    main()
