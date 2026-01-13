"""
Multi-Turn Conversational Image Editing
========================================

Manages iterative image editing through multi-turn conversations with Gemini models.

Features:
- Session-based editing (60-minute timeout)
- Conversation history persistence
- Automatic session cleanup
- Brand context injection per collection
- Chat history management

Use Cases:
- Iterative product photography refinement
- AI model generation adjustments
- Campaign visual exploration
- Real-time creative direction

Created: 2026-01-08
Status: Phase 3 - Conversational Editing
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from PIL import Image

from agents.visual_generation.gemini_native import (
    GeminiNativeImageClient,
    GeminiProImageClient,
    ImageGenerationConfig,
)
from orchestration.brand_context import Collection

logger = structlog.get_logger(__name__)


# ============================================================================
# Exceptions
# ============================================================================


class ChatSessionError(Exception):
    """Base exception for chat session errors."""

    pass


class ChatSessionExpiredError(ChatSessionError):
    """Raised when chat session has expired (60-minute timeout)."""

    def __init__(self, message: str, model: str | None = None):
        """Initialize ChatSessionExpiredError.

        Args:
            message: Error message
            model: Model name
        """
        self.model = model
        super().__init__(message)


class ChatSessionNotFoundError(ChatSessionError):
    """Raised when chat session ID is not found."""

    pass


# ============================================================================
# Constants
# ============================================================================

# Session timeout (Gemini limitation)
SESSION_TIMEOUT_MINUTES = 60


@dataclass
class ChatMessage:
    """Single message in chat history."""

    role: str  # "user" or "model"
    content: str
    image: Image.Image | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatSession:
    """
    Chat session for multi-turn image editing.

    Tracks conversation history, session state, and metadata for
    iterative image refinement workflows.
    """

    session_id: str
    client: GeminiNativeImageClient
    collection: Collection | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_active: datetime = field(default_factory=lambda: datetime.now(UTC))
    messages: list[ChatMessage] = field(default_factory=list)
    current_image: Image.Image | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if session has expired (60min timeout)."""
        expiry_time = self.created_at + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        return datetime.now(UTC) > expiry_time

    def touch(self) -> None:
        """Update last_active timestamp."""
        self.last_active = datetime.now(UTC)

    def add_message(self, role: str, content: str, image: Image.Image | None = None) -> None:
        """
        Add message to conversation history.

        Args:
            role: "user" or "model"
            content: Message text
            image: Optional image attachment
        """
        message = ChatMessage(
            role=role,
            content=content,
            image=image,
        )
        self.messages.append(message)
        self.touch()

    def get_history(self, limit: int | None = None) -> list[ChatMessage]:
        """
        Get conversation history.

        Args:
            limit: Optional limit on number of messages

        Returns:
            List of ChatMessage objects
        """
        if limit:
            return self.messages[-limit:]
        return self.messages.copy()


class ConversationalImageEditor:
    """
    Multi-turn conversational image editor for Gemini models.

    Manages chat sessions for iterative image refinement:
    - Start sessions with initial image + prompt
    - Continue editing with natural language instructions
    - Automatic session cleanup after 60min
    - Brand context injection per collection

    Usage:
        editor = ConversationalImageEditor()

        # Start session
        session = await editor.start_session(
            image="product.jpg",
            initial_prompt="Make background darker",
            collection=Collection.BLACK_ROSE
        )

        # Continue editing
        result1 = await editor.continue_session(
            session_id=session.session_id,
            prompt="Add rose gold highlights to logo"
        )

        # More iterations
        result2 = await editor.continue_session(
            session_id=session.session_id,
            prompt="Increase contrast"
        )
    """

    def __init__(self, use_pro_model: bool = True) -> None:
        """
        Initialize conversational image editor.

        Args:
            use_pro_model: Use Gemini Pro (default) or Flash model
        """
        self._sessions: dict[str, ChatSession] = {}
        self._use_pro_model = use_pro_model
        logger.info("conversational_image_editor_initialized", use_pro_model=use_pro_model)

    async def start_session(
        self,
        image: str | Image.Image,
        initial_prompt: str,
        collection: Collection | None = None,
        config: ImageGenerationConfig | None = None,
    ) -> ChatSession:
        """
        Start new editing session with initial image and prompt.

        Args:
            image: Path to image file or PIL Image
            initial_prompt: Initial editing instruction
            collection: Optional SkyyRose collection context
            config: Optional generation configuration

        Returns:
            ChatSession with session_id for subsequent edits

        Raises:
            GeminiNativeError: On generation failure
        """
        # Load image if path provided
        if isinstance(image, str):
            image = Image.open(image)

        # Create client (Pro recommended for conversational editing)
        if self._use_pro_model:
            client = GeminiProImageClient()
        else:
            from agents.visual_generation.gemini_native import GeminiFlashImageClient

            client = GeminiFlashImageClient()

        await client.connect()

        # Generate initial edited image
        result = await client.generate(
            prompt=initial_prompt,
            config=config,
            collection=collection,
            inject_brand_dna=True,
        )

        # Create session
        session_id = str(uuid.uuid4())
        session = ChatSession(
            session_id=session_id,
            client=client,
            collection=collection,
            current_image=result.image,
            metadata={
                "original_prompt": initial_prompt,
                "config": config,
                "model": client.model,
            },
        )

        # Add initial messages to history
        session.add_message("user", initial_prompt, image=image)
        session.add_message("model", f"Generated edited image: {result.prompt}", image=result.image)

        # Store session
        self._sessions[session_id] = session

        logger.info(
            "chat_session_started",
            session_id=session_id,
            collection=collection.value if collection else None,
            model=client.model,
        )

        return session

    async def continue_session(
        self,
        session_id: str,
        prompt: str,
        config: ImageGenerationConfig | None = None,
    ) -> dict[str, Any]:
        """
        Continue editing in existing session.

        Args:
            session_id: Session ID from start_session()
            prompt: Next editing instruction
            config: Optional generation configuration

        Returns:
            Dict with edited image and metadata

        Raises:
            ChatSessionExpiredError: If session expired (60min)
            GeminiNativeError: On generation failure
        """
        # Get session
        session = self._sessions.get(session_id)
        if not session:
            raise ChatSessionNotFoundError(f"Session {session_id} not found")

        # Check expiration
        if session.is_expired():
            self._cleanup_session(session_id)
            raise ChatSessionExpiredError(
                f"Session {session_id} expired (60min limit)",
                model=session.client.model,
            )

        # Generate next iteration using current image as context
        result = await session.client.generate(
            prompt=prompt,
            config=config or session.metadata.get("config"),
            collection=session.collection,
            inject_brand_dna=True,
        )

        # Update session
        session.current_image = result.image
        session.add_message("user", prompt)
        session.add_message("model", f"Generated edited image: {result.prompt}", image=result.image)

        logger.info(
            "chat_session_continued",
            session_id=session_id,
            message_count=len(session.messages),
            time_since_created=str(datetime.now(UTC) - session.created_at),
        )

        return {
            "success": True,
            "session_id": session_id,
            "image": result.image,
            "prompt": result.prompt,
            "latency_ms": result.latency_ms,
            "cost_usd": result.cost_usd,
            "message_count": len(session.messages),
            "time_remaining_minutes": max(
                0,
                SESSION_TIMEOUT_MINUTES
                - (datetime.now(UTC) - session.created_at).total_seconds() / 60,
            ),
        }

    def get_session(self, session_id: str) -> ChatSession | None:
        """
        Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            ChatSession or None if not found
        """
        return self._sessions.get(session_id)

    def list_active_sessions(self) -> list[dict[str, Any]]:
        """
        List all active (non-expired) sessions.

        Returns:
            List of session summaries
        """
        active = []

        for session_id, session in self._sessions.items():
            if not session.is_expired():
                active.append(
                    {
                        "session_id": session_id,
                        "created_at": session.created_at.isoformat(),
                        "last_active": session.last_active.isoformat(),
                        "message_count": len(session.messages),
                        "collection": session.collection.value if session.collection else None,
                        "model": session.client.model,
                    }
                )

        return active

    def _cleanup_session(self, session_id: str) -> None:
        """Remove session and clean up resources."""
        session = self._sessions.pop(session_id, None)
        if session:
            asyncio.create_task(session.client.close())
            logger.info("chat_session_cleaned_up", session_id=session_id)

    async def close_session(self, session_id: str) -> bool:
        """
        Close a specific session by ID.

        Args:
            session_id: ID of session to close

        Returns:
            True if session was closed, False if not found
        """
        if session_id in self._sessions:
            self._cleanup_session(session_id)
            return True
        return False

    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up all expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        expired_ids = [
            session_id for session_id, session in self._sessions.items() if session.is_expired()
        ]

        for session_id in expired_ids:
            self._cleanup_session(session_id)

        if expired_ids:
            logger.info("expired_sessions_cleaned_up", count=len(expired_ids))

        return len(expired_ids)

    async def close_all_sessions(self) -> None:
        """Close all sessions and clean up resources."""
        session_ids = list(self._sessions.keys())

        for session_id in session_ids:
            self._cleanup_session(session_id)

        logger.info("all_sessions_closed", count=len(session_ids))


# Export
__all__ = [
    "ChatMessage",
    "ChatSession",
    "ConversationalImageEditor",
    "SESSION_TIMEOUT_MINUTES",
]
