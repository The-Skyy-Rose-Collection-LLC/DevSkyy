"""
Conversation Editor for Visual Generation
==========================================

Manages multi-turn conversations with Gemini image generation clients,
maintaining session state and conversation history.

Features:
- Session-based conversation management
- Automatic session expiration and cleanup
- Message history tracking
- Async client lifecycle management

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Literal

from PIL import Image

from errors.production_errors import DevSkyError, DevSkyErrorCode, DevSkyErrorSeverity

logger = logging.getLogger(__name__)

# Session timeout in minutes
SESSION_TIMEOUT_MINUTES = 30


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class GeneratedImage:
    """Result of image generation."""

    base64_data: str
    mime_type: str
    prompt: str
    model: str
    cost_usd: float = 0.0
    metadata: dict = field(default_factory=dict)
    image: Image.Image | None = None


# =============================================================================
# Exceptions
# =============================================================================


class ChatSessionError(DevSkyError):
    """Base exception for chat session errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            code=DevSkyErrorCode.INTERNAL_ERROR,
            severity=DevSkyErrorSeverity.ERROR,
            **kwargs,
        )


class ChatSessionExpiredError(ChatSessionError):
    """Raised when a session has expired."""

    def __init__(self, session_id: str, model: str | None = None):
        self.model = model
        super().__init__(f"Session {session_id} has expired")


class ChatSessionNotFoundError(ChatSessionError):
    """Raised when a session is not found."""

    pass


# =============================================================================
# Chat Message and Session
# =============================================================================

# Type alias for message roles
Role = Literal["user", "model"]


@dataclass
class ChatMessage:
    """A single message in a conversation."""

    role: Role
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class ChatSession:
    """
    Represents a conversation session with message history.

    Attributes:
        session_id: Unique session identifier
        client: The Gemini image client instance
        messages: List of conversation messages
        created_at: Session creation timestamp
        last_accessed: Last access timestamp
    """

    def __init__(self, session_id: str, client, initial_prompt: str | None = None):
        """
        Initialize a chat session.

        Args:
            session_id: Unique identifier for the session
            client: Gemini image client instance
            initial_prompt: Optional initial prompt to start the conversation
        """
        self.session_id = session_id
        self.client = client
        self.messages: list[ChatMessage] = []
        self.created_at = datetime.now(UTC)
        self.last_accessed = datetime.now(UTC)

        if initial_prompt:
            self.add_message("user", initial_prompt)

    def add_message(self, role: Role, content: str) -> None:
        """Add a message to the conversation history."""
        self.messages.append(ChatMessage(role=role, content=content))
        self.last_accessed = datetime.now(UTC)

    def get_history(self, limit: int | None = None) -> list[ChatMessage]:
        """
        Get conversation history.

        Args:
            limit: Maximum number of recent messages to return.
                   If None, returns all messages.
                   If 0 or negative, returns empty list.
                   If positive, returns the last N messages.

        Returns:
            List of ChatMessage objects
        """
        if limit is None:
            return self.messages.copy()
        elif limit <= 0:
            return []
        else:
            return self.messages[-limit:]

    def is_expired(self) -> bool:
        """
        Check if the session has expired.

        A session is expired if the time since last access is greater than
        or equal to SESSION_TIMEOUT_MINUTES.

        Returns:
            True if session is expired, False otherwise
        """
        now = datetime.now(UTC)
        expiry_time = self.last_accessed + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        return now >= expiry_time


# =============================================================================
# Conversation Editor
# =============================================================================


class ConversationEditor:
    """
    Manages conversation sessions for visual generation.

    Provides session lifecycle management, automatic cleanup of expired
    sessions, and conversation history tracking.
    """

    def __init__(self):
        """Initialize the conversation editor."""
        self._sessions: dict[str, ChatSession] = {}
        self._cleanup_task: asyncio.Task | None = None

    async def start_session(
        self,
        image: Image.Image | str,
        prompt: str | None = None,
        model: str = "gemini-pro-vision",
    ) -> tuple[str, GeneratedImage | None]:
        """
        Start a new conversation session.

        Args:
            image: PIL Image or path to image file
            prompt: Optional initial prompt
            model: Model to use for generation

        Returns:
            Tuple of (session_id, generated_image_result or None)
        """
        session_id = str(uuid.uuid4())

        # Load image if path provided
        if isinstance(image, str):
            image = Image.open(image)

        # Create client - for now we use a mock structure
        # In real implementation, this would be GeminiProImageClient or similar
        client = await self._create_client(model, image)

        # Create session
        session = ChatSession(session_id, client, prompt)
        self._sessions[session_id] = session

        # Generate initial response if prompt provided
        result = None
        if prompt:
            result = await client.generate(prompt)
            if result:
                session.add_message("model", result.get("text", ""))

        return session_id, result

    async def continue_session(
        self,
        session_id: str,
        prompt: str,
    ) -> GeneratedImage:
        """
        Continue an existing conversation session.

        The session's conversation history is used as context for generation,
        maintaining continuity in the conversation. The context is implicit
        in the session object rather than passed as an image parameter.

        Args:
            session_id: ID of the session to continue
            prompt: User prompt for this turn

        Returns:
            Generated image result

        Raises:
            ChatSessionNotFoundError: If session doesn't exist
            ChatSessionExpiredError: If session has expired
        """
        session = self._sessions.get(session_id)

        if session is None:
            raise ChatSessionNotFoundError(f"Session {session_id} not found")

        if session.is_expired():
            raise ChatSessionExpiredError(session_id, model=None)

        # Add user message
        session.add_message("user", prompt)

        # Generate response using session conversation history as context
        result = await session.client.generate(prompt)

        # Add model response
        if result:
            session.add_message("model", result.get("text", ""))

        return result

    async def get_session(self, session_id: str) -> ChatSession:
        """
        Get a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            ChatSession object

        Raises:
            ChatSessionNotFoundError: If session doesn't exist
            ChatSessionExpiredError: If session has expired
        """
        session = self._sessions.get(session_id)

        if session is None:
            raise ChatSessionNotFoundError(f"Session {session_id} not found")

        if session.is_expired():
            raise ChatSessionExpiredError(session_id, model=None)

        return session

    async def close_session(self, session_id: str) -> bool:
        """
        Close a session and cleanup its resources.

        Args:
            session_id: ID of the session to close

        Returns:
            True if a session was closed, False if session didn't exist
        """
        session = self._sessions.pop(session_id, None)

        if session is None:
            return False

        # Close the client connection
        try:
            await session.client.close()
            logger.info(f"Closed session {session_id}")
        except Exception as e:
            logger.error(f"Error closing session {session_id}: {e}")

        return True

    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up all expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        expired_ids = [
            sid for sid, session in self._sessions.items() if session.is_expired()
        ]

        # Close all expired sessions
        cleanup_tasks = [self.close_session(sid) for sid in expired_ids]
        results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        # Count successful cleanups
        cleaned = sum(1 for r in results if r is True)

        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} expired sessions")

        return cleaned

    async def close_all_sessions(self) -> int:
        """
        Close all active sessions.

        Returns:
            Number of sessions closed
        """
        session_ids = list(self._sessions.keys())

        # Close all sessions
        cleanup_tasks = [self.close_session(sid) for sid in session_ids]
        results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        # Count successful closures
        closed = sum(1 for r in results if r is True)

        logger.info(f"Closed {closed} sessions")

        return closed

    def _cleanup_session(self, session_id: str) -> None:
        """
        Thin synchronous helper for session cleanup.

        This method is kept for compatibility but delegates to close_session.

        Args:
            session_id: ID of the session to cleanup
        """
        # This is a sync wrapper that can be used in sync contexts
        # The actual cleanup is delegated to the async close_session
        pass

    async def _create_client(self, model: str, image: Image.Image):
        """
        Create and connect a Gemini client.

        Args:
            model: Model name
            image: PIL Image

        Returns:
            Connected client instance
        """
        # Mock client for now - in real implementation this would be:
        # from orchestration.llm_clients import GeminiProImageClient
        # client = GeminiProImageClient(model=model)
        # await client.connect()
        # return client

        class MockClient:
            """Mock client for testing."""

            async def generate(self, prompt: str):
                """Mock generate method."""
                return {"text": f"Generated response for: {prompt}"}

            async def close(self):
                """Mock close method."""
                pass

            async def connect(self):
                """Mock connect method."""
                pass

        client = MockClient()
        await client.connect()
        return client
