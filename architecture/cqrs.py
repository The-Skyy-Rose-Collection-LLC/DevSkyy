from datetime import datetime, timezone

from pydantic import BaseModel

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar
import uuid

"""
CQRS (Command Query Responsibility Segregation) Pattern
Separates read and write operations for better scalability and maintainability
"""

# ============================================================================
# BASE TYPES
# ============================================================================


class Command(BaseModel):
    """Base class for all commands (write operations)"""

    command_id: str = None
    timestamp: datetime = None

    def __init__(self, **data):
        if "command_id" not in data or data["command_id"] is None:
            data["command_id"] = str(uuid.uuid4())
        if "timestamp" not in data or data["timestamp"] is None:
            data["timestamp"] = datetime.now(timezone.utc)
        super().__init__(**data)


class Query(BaseModel):
    """Base class for all queries (read operations)"""

    query_id: str = None
    timestamp: datetime = None

    def __init__(self, **data):
        if "query_id" not in data or data["query_id"] is None:
            data["query_id"] = str(uuid.uuid4())
        if "timestamp" not in data or data["timestamp"] is None:
            data["timestamp"] = datetime.now(timezone.utc)
        super().__init__(**data)


TCommand = TypeVar("TCommand", bound=Command)
TQuery = TypeVar("TQuery", bound=Query)
TResult = TypeVar("TResult")

# ============================================================================
# HANDLERS
# ============================================================================


class CommandHandler(ABC, Generic[TCommand, TResult]):
    """Abstract base class for command handlers"""

    @abstractmethod
    async def handle(self, command: TCommand) -> TResult:
        """
        Handle command and return result

        Args:
            command: Command to handle

        Returns:
            Result of command execution
        """


class QueryHandler(ABC, Generic[TQuery, TResult]):
    """Abstract base class for query handlers"""

    @abstractmethod
    async def handle(self, query: TQuery) -> TResult:
        """
        Handle query and return result

        Args:
            query: Query to handle

        Returns:
            Result of query execution
        """


# ============================================================================
# BUS / MEDIATOR
# ============================================================================


class CommandBus:
    """
    Command bus for dispatching commands to handlers
    Implements mediator pattern for decoupling
    """

    def __init__(self):
        self._handlers: Dict[type, CommandHandler] = {}

    def register(self, command_type: type, handler: CommandHandler):
        """
        Register command handler

        Args:
            command_type: Type of command
            handler: Handler for the command
        """
        self._handlers[command_type] = handler

    async def execute(self, command: Command) -> Any:
        """
        Execute command by dispatching to appropriate handler

        Args:
            command: Command to execute

        Returns:
            Result from command handler

        Raises:
            ValueError: If no handler found for command type
        """
        command_type = type(command)
        if command_type not in self._handlers:
            raise ValueError(f"No handler registered for command type: {command_type.__name__}")

        handler = self._handlers[command_type]
        return await handler.handle(command)


class QueryBus:
    """
    Query bus for dispatching queries to handlers
    Implements mediator pattern for decoupling
    """

    def __init__(self):
        self._handlers: Dict[type, QueryHandler] = {}

    def register(self, query_type: type, handler: QueryHandler):
        """
        Register query handler

        Args:
            query_type: Type of query
            handler: Handler for the query
        """
        self._handlers[query_type] = handler

    async def execute(self, query: Query) -> Any:
        """
        Execute query by dispatching to appropriate handler

        Args:
            query: Query to execute

        Returns:
            Result from query handler

        Raises:
            ValueError: If no handler found for query type
        """
        query_type = type(query)
        if query_type not in self._handlers:
            raise ValueError(f"No handler registered for query type: {query_type.__name__}")

        handler = self._handlers[query_type]
        return await handler.handle(query)


# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

command_bus = CommandBus()
query_bus = QueryBus()

# ============================================================================
# EXAMPLE USAGE
# ============================================================================


# Example Command
class CreateAgentCommand(Command):
    """Command to create a new agent"""

    name: str
    agent_type: str
    capabilities: Dict[str, Any]


# Example Command Handler
class CreateAgentHandler(CommandHandler[CreateAgentCommand, Dict]):
    """Handler for CreateAgentCommand"""

    async def handle(self, command: CreateAgentCommand) -> Dict:
        """
        Handle agent creation command

        Args:
            command: CreateAgentCommand instance

        Returns:
            Created agent details
        """
        # Implementation would save to database
        return {
            "agent_id": str(uuid.uuid4()),
            "name": command.name,
            "type": command.agent_type,
            "capabilities": command.capabilities,
            "created_at": command.timestamp,
        }


# Example Query
class GetAgentQuery(Query):
    """Query to get agent by ID"""

    agent_id: str


# Example Query Handler
class GetAgentHandler(QueryHandler[GetAgentQuery, Optional[Dict]]):
    """Handler for GetAgentQuery"""

    async def handle(self, query: GetAgentQuery) -> Optional[Dict]:
        """
        Handle agent retrieval query

        Args:
            query: GetAgentQuery instance

        Returns:
            Agent details or None if not found
        """
        # Implementation would fetch from read model/cache
        return {
            "agent_id": query.agent_id,
            "name": "Example Agent",
            "type": "backend",
            "status": "active",
        }


# Register handlers (would be done at startup)
# command_bus.register(CreateAgentCommand, CreateAgentHandler())
# query_bus.register(GetAgentQuery, GetAgentHandler())
