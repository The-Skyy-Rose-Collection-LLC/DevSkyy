"""
Tests for Conversation Editor
==============================

Tests for session management, conversation history, and client lifecycle.
"""

from __future__ import annotations

import base64
import io
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from agents.visual_generation.conversation_editor import (
    SESSION_TIMEOUT_MINUTES,
    ChatMessage,
    ChatSession,
    ChatSessionError,
    ChatSessionExpiredError,
    ChatSessionNotFoundError,
    ConversationEditor,
    GeneratedImage,
)
from errors.production_errors import DevSkyError

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_api_key() -> str:
    """Mock API key for testing."""
    return "test-api-key-12345"


@pytest.fixture
def mock_image() -> Image.Image:
    """Create a mock PIL Image for testing."""
    # Create a simple 100x100 RGB image
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    return img


@pytest.fixture
def mock_generation_result(mock_image: Image.Image) -> GeneratedImage:
    """Mock generation result fixture."""
    # Convert image to base64
    buffer = io.BytesIO()
    mock_image.save(buffer, format="PNG")
    base64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return GeneratedImage(
        base64_data=base64_data,
        mime_type="image/png",
        prompt="test prompt",
        model="gemini-pro-vision",
        cost_usd=0.01,
        metadata={"test": "data"},
        image=mock_image,
    )


# =============================================================================
# ChatMessage Tests
# =============================================================================


def test_chat_message_creation():
    """Test creating a chat message."""
    msg = ChatMessage(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"
    assert isinstance(msg.timestamp, datetime)


def test_chat_message_timestamp():
    """Test that chat message has a timestamp."""
    msg = ChatMessage(role="model", content="Response")
    assert msg.timestamp.tzinfo == UTC


# =============================================================================
# ChatSession Tests
# =============================================================================


@pytest.fixture
def mock_client():
    """Mock Gemini client."""
    client = AsyncMock()
    client.generate = AsyncMock(return_value={"text": "Generated response"})
    client.close = AsyncMock()
    client.connect = AsyncMock()
    return client


def test_chat_session_initialization(mock_client):
    """Test creating a new chat session."""
    session = ChatSession("test-session-123", mock_client)
    assert session.session_id == "test-session-123"
    assert session.client == mock_client
    assert len(session.messages) == 0
    assert isinstance(session.created_at, datetime)
    assert isinstance(session.last_accessed, datetime)


def test_chat_session_with_initial_prompt(mock_client):
    """Test creating a session with an initial prompt."""
    session = ChatSession("test-session-456", mock_client, "Initial prompt")
    assert len(session.messages) == 1
    assert session.messages[0].role == "user"
    assert session.messages[0].content == "Initial prompt"


def test_add_message(mock_client):
    """Test adding messages to a session."""
    session = ChatSession("test-session-789", mock_client)
    session.add_message("user", "Hello")
    session.add_message("model", "Hi there!")

    assert len(session.messages) == 2
    assert session.messages[0].role == "user"
    assert session.messages[0].content == "Hello"
    assert session.messages[1].role == "model"
    assert session.messages[1].content == "Hi there!"


def test_get_history_all(mock_client):
    """Test getting full conversation history."""
    session = ChatSession("test-session", mock_client)
    session.add_message("user", "Message 1")
    session.add_message("model", "Response 1")
    session.add_message("user", "Message 2")

    history = session.get_history()
    assert len(history) == 3
    assert history[0].content == "Message 1"
    assert history[-1].content == "Message 2"


def test_get_history_with_limit(mock_client):
    """Test getting limited conversation history."""
    session = ChatSession("test-session", mock_client)
    session.add_message("user", "Message 1")
    session.add_message("model", "Response 1")
    session.add_message("user", "Message 2")
    session.add_message("model", "Response 2")

    history = session.get_history(limit=2)
    assert len(history) == 2
    assert history[0].content == "Message 2"
    assert history[1].content == "Response 2"


def test_get_history_with_zero_limit(mock_client):
    """Test getting history with limit=0 returns empty list."""
    session = ChatSession("test-session", mock_client)
    session.add_message("user", "Message 1")
    session.add_message("model", "Response 1")

    history = session.get_history(limit=0)
    assert len(history) == 0
    assert history == []


def test_is_expired_not_expired(mock_client):
    """Test that a recent session is not expired."""
    session = ChatSession("test-session", mock_client)
    assert not session.is_expired()


def test_is_expired_expired(mock_client):
    """Test that an old session is expired."""
    session = ChatSession("test-session", mock_client)
    # Set last_accessed to be older than SESSION_TIMEOUT_MINUTES
    session.last_accessed = datetime.now(UTC) - timedelta(minutes=SESSION_TIMEOUT_MINUTES + 1)
    assert session.is_expired()


def test_is_expired_boundary(mock_client):
    """Test that a session at exact timeout boundary is expired (uses >= comparison)."""
    session = ChatSession("test-session", mock_client)
    # Set last_accessed to be exactly SESSION_TIMEOUT_MINUTES ago
    session.last_accessed = datetime.now(UTC) - timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    assert session.is_expired()


# =============================================================================
# ConversationEditor Tests
# =============================================================================


@pytest.mark.asyncio
async def test_conversation_editor_initialization():
    """Test creating a conversation editor."""
    editor = ConversationEditor()
    assert len(editor._sessions) == 0


@pytest.mark.asyncio
async def test_start_session(mock_image: Image.Image):
    """Test starting a new session."""
    editor = ConversationEditor()

    session_id, result = await editor.start_session(
        image=mock_image,
        prompt=None,
        model="gemini-pro-vision",
    )

    assert session_id is not None
    assert session_id in editor._sessions
    assert result is None  # No result when no prompt


@pytest.mark.asyncio
async def test_start_session_with_prompt(mock_image: Image.Image):
    """Test starting a session with an initial prompt."""
    editor = ConversationEditor()

    # Patch the client methods to avoid real I/O
    with patch("uuid.uuid4") as mock_uuid:
        mock_uuid.return_value = MagicMock(__str__=MagicMock(return_value="test-uuid-12345"))

        # Patch the client creation to return a proper mock
        with patch.object(editor, "_create_client", return_value=AsyncMock()) as mock_create_client:
            mock_client = AsyncMock()
            mock_client.generate = AsyncMock(return_value={"text": "Generated response"})
            mock_client.close = AsyncMock()
            mock_client.connect = AsyncMock()
            mock_create_client.return_value = mock_client

            session_id, result = await editor.start_session(
                image=mock_image,
                prompt="Generate an image",
                model="gemini-pro-vision",
            )

            assert session_id == "test-uuid-12345"
            assert session_id in editor._sessions
            mock_client.generate.assert_called_once()


@pytest.mark.asyncio
async def test_continue_session_not_found():
    """Test continuing a non-existent session raises ChatSessionNotFoundError."""
    editor = ConversationEditor()

    with pytest.raises(ChatSessionNotFoundError):
        await editor.continue_session("non-existent-session", "Hello")


@pytest.mark.asyncio
async def test_continue_session_expired(mock_client):
    """Test continuing an expired session raises ChatSessionExpiredError."""
    editor = ConversationEditor()
    session = ChatSession("expired-session", mock_client)
    session.last_accessed = datetime.now(UTC) - timedelta(minutes=SESSION_TIMEOUT_MINUTES + 1)
    editor._sessions["expired-session"] = session

    with pytest.raises(ChatSessionExpiredError):
        await editor.continue_session("expired-session", "Hello")


@pytest.mark.asyncio
async def test_continue_session_success(mock_client):
    """Test successfully continuing a session."""
    editor = ConversationEditor()
    session = ChatSession("active-session", mock_client, "Initial prompt")
    editor._sessions["active-session"] = session

    result = await editor.continue_session("active-session", "Follow-up question")

    assert result is not None
    assert len(session.messages) == 3  # Initial + user + model
    assert session.messages[1].content == "Follow-up question"
    mock_client.generate.assert_called_once_with("Follow-up question")


@pytest.mark.asyncio
async def test_get_session(mock_client):
    """Test retrieving a session."""
    editor = ConversationEditor()
    session = ChatSession("test-session", mock_client)
    editor._sessions["test-session"] = session

    retrieved = await editor.get_session("test-session")
    assert retrieved == session


@pytest.mark.asyncio
async def test_get_session_not_found():
    """Test getting a non-existent session raises error."""
    editor = ConversationEditor()

    with pytest.raises(ChatSessionNotFoundError):
        await editor.get_session("non-existent")


@pytest.mark.asyncio
async def test_close_session(mock_client):
    """Test closing a session."""
    editor = ConversationEditor()
    session = ChatSession("test-session", mock_client)
    editor._sessions["test-session"] = session

    result = await editor.close_session("test-session")

    assert result is True
    assert "test-session" not in editor._sessions
    mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_close_session_not_found():
    """Test closing a non-existent session returns False."""
    editor = ConversationEditor()

    result = await editor.close_session("non-existent")
    assert result is False


@pytest.mark.asyncio
async def test_cleanup_expired_sessions(mock_client):
    """Test cleanup of expired sessions."""
    editor = ConversationEditor()

    # Create active and expired sessions
    active = ChatSession("active", mock_client)
    expired1 = ChatSession("expired1", mock_client)
    expired1.last_accessed = datetime.now(UTC) - timedelta(minutes=SESSION_TIMEOUT_MINUTES + 1)
    expired2 = ChatSession("expired2", mock_client)
    expired2.last_accessed = datetime.now(UTC) - timedelta(minutes=SESSION_TIMEOUT_MINUTES + 5)

    editor._sessions["active"] = active
    editor._sessions["expired1"] = expired1
    editor._sessions["expired2"] = expired2

    cleaned = await editor.cleanup_expired_sessions()

    assert cleaned == 2
    assert "active" in editor._sessions
    assert "expired1" not in editor._sessions
    assert "expired2" not in editor._sessions


@pytest.mark.asyncio
async def test_close_all_sessions(mock_client):
    """Test closing all sessions."""
    editor = ConversationEditor()

    # Create multiple sessions
    for i in range(3):
        session = ChatSession(f"session-{i}", mock_client)
        editor._sessions[f"session-{i}"] = session

    closed = await editor.close_all_sessions()

    assert closed == 3
    assert len(editor._sessions) == 0


# =============================================================================
# Exception Tests
# =============================================================================


def test_chat_session_error_inheritance():
    """Test that ChatSessionError inherits from DevSkyError."""
    error = ChatSessionError("Test error")
    assert isinstance(error, DevSkyError)


def test_chat_session_expired_error():
    """Test ChatSessionExpiredError with model attribute."""
    error = ChatSessionExpiredError("session-123", model="gemini-pro")
    assert error.model == "gemini-pro"
    assert "session-123" in str(error)


def test_chat_session_not_found_error():
    """Test ChatSessionNotFoundError."""
    error = ChatSessionNotFoundError("Session not-found-123 not found")
    assert "not-found-123" in str(error)
