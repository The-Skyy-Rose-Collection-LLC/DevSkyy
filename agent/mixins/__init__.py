"""
Agent Mixins - Composable capabilities for DevSkyy agents.

Mixins add specific functionality without modifying base agent behavior.
Use multiple inheritance to combine capabilities.

Example:
    class SmartAgent(BaseAgent, ReActCapableMixin, IterativeRetrievalMixin):
        def __init__(self):
            super().__init__("smart_agent")
            self.__init_react__()  # Initialize ReAct
"""

from agent.mixins.react_mixin import (
    IterativeRetrievalMixin,
    ReActCapableMixin,
    ReasoningStep,
    ReasoningStepType,
    ReasoningTrace,
)


__all__ = [
    "IterativeRetrievalMixin",
    "ReActCapableMixin",
    "ReasoningStep",
    "ReasoningStepType",
    "ReasoningTrace",
]
