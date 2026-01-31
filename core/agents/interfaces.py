"""
Agent Component Interfaces
==========================

Abstract base classes defining contracts for agent components.

These interfaces enable:
- Dependency injection for testing
- Loose coupling between components
- Type-safe service contracts
- Future agent implementation swapping

Author: DevSkyy Platform Team
Version: 1.0.0 (Phase 4 Refactoring)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from adk.base import AgentResult


class IAgent(Protocol):
    """
    Base agent interface - all agents must implement.

    This protocol defines the minimum contract for any agent in the system.
    """

    name: str
    agent_type: str

    @abstractmethod
    async def execute(
        self, prompt: str, *, correlation_id: str | None = None
    ) -> AgentResult:
        """
        Execute agent task.

        Args:
            prompt: Task description
            correlation_id: Optional correlation ID for tracking

        Returns:
            AgentResult with execution outcome
        """
        ...

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize agent resources (connections, models, etc.)."""
        ...

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """Return list of agent capabilities."""
        ...


class ISuperAgent(IAgent, Protocol):
    """
    Enhanced agent interface with prompt engineering.

    Extends IAgent with auto-execution and technique selection.
    """

    @abstractmethod
    async def execute_auto(
        self, prompt: str, *, correlation_id: str | None = None
    ) -> AgentResult:
        """
        Execute with automatic technique selection.

        Args:
            prompt: Task description
            correlation_id: Optional correlation ID

        Returns:
            AgentResult with selected technique metadata
        """
        ...

    @abstractmethod
    def select_technique(self, prompt: str) -> str:
        """
        Select optimal prompt engineering technique.

        Args:
            prompt: Task description

        Returns:
            Technique name (e.g., "chain_of_thought", "react")
        """
        ...


class IAgentOrchestrator(ABC):
    """
    Routes tasks to appropriate agents.

    Manages agent registry and intelligent task routing.
    """

    @abstractmethod
    async def route(
        self, task: str, *, correlation_id: str | None = None
    ) -> IAgent:
        """
        Route task to most appropriate agent.

        Args:
            task: Task description
            correlation_id: Optional correlation ID

        Returns:
            Agent capable of handling the task

        Raises:
            ValueError: If no suitable agent found
        """
        ...

    @abstractmethod
    def register_agent(self, agent: IAgent) -> None:
        """
        Register agent with orchestrator.

        Args:
            agent: Agent to register
        """
        ...

    @abstractmethod
    def get_agent(self, name: str) -> IAgent | None:
        """
        Get agent by name.

        Args:
            name: Agent name

        Returns:
            Agent if found, None otherwise
        """
        ...

    @abstractmethod
    def list_agents(self) -> list[IAgent]:
        """
        List all registered agents.

        Returns:
            List of all agents
        """
        ...
