"""
API Integration Enums Module
Centralized enum definitions with serialization support for improved code clarity and maintenance
"""

from enum import Enum


class SerializableEnum(Enum):
    """
    Base enum class with built-in JSON serialization support.

    Provides a consistent to_json() method for all enum types to ensure
    proper serialization without direct string value references.

    Usage:
        class MyStatus(SerializableEnum):
            PENDING = "pending"
            RUNNING = "running"

        status = MyStatus.PENDING
        json_value = status.to_json()  # Returns "pending"
    """

    def to_json(self) -> str:
        """
        Convert enum to JSON-serializable string value.

        Returns:
            str: The string value of the enum member
        """
        return self.value

    @classmethod
    def from_string(cls, value: str) -> "SerializableEnum":
        """
        Create enum instance from string value.

        Args:
            value: String value to convert to enum

        Returns:
            SerializableEnum: The corresponding enum member

        Raises:
            ValueError: If the value doesn't match any enum member
        """
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"No {cls.__name__} member with value '{value}'")


class WorkflowStatus(SerializableEnum):
    """
    Workflow execution status enum.

    Represents the various states a workflow can be in during its lifecycle.
    Inherits from SerializableEnum for consistent serialization support.
    """

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    ROLLED_BACK = "rolled_back"
