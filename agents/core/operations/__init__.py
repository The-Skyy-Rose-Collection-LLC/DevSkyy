"""Operations Core Agent — deploy, security, health, code quality."""

try:
    from .agent import OperationsCoreAgent
except ImportError:
    OperationsCoreAgent = None  # type: ignore[assignment,misc]

__all__ = ["OperationsCoreAgent"]
