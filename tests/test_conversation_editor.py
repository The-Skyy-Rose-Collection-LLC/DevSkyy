"""
Unit tests for Gemini Native conversational image editor.

Tests:
- ChatMessage creation and validation
- ChatSession creation and expiration
- ConversationalImageEditor session management
- Session cleanup and timeout handling
- Multi-turn conversation flow
- Brand DNA injection in conversations
- Error handling for expired/invalid sessions
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from agents.visual_generation.conversation_editor import (
    SESSION_TIMEOUT_MINUTES,
    ChatMessage,
    ChatSession,
    ChatSessionExpiredError,
    ChatSessionNotFoundError,
    ConversationalImageEditor,
)
from agents.visual_generation.gemini_native import (
    GeminiProImageClient,
    GeneratedImage,
)
from orchestration.brand_context import Collection

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_api_key():
    """Mock Google AI API key."""
    return "test_api_key_12345"


@pytest.fixture
def mock_image():
    """Mock PIL Image."""
    img = Image.new("RGB", (256, 256), color="red")
    return img


@pytest.fixture
def test_image_file(tmp_path):
    """Create a temporary test image file."""
    img = Image.new("RGB", (256, 256), color="red")
    img_path = tmp_path / "product.jpg"
    img.save(img_path, "JPEG")
    return str(img_path)


@pytest.fixture
def mock_generation_result(mock_image):
    """Mock successful image generation result."""
    return GeneratedImage(
        image=mock_image,
        base64_data="",
        mime_type="image/jpeg",
        prompt="test prompt",
        model="gemini-3-pro-image-preview",
        latency_ms=100.0,
        cost_usd=0.08,
        metadata={"resolution": "1K", "aspect_ratio": "1:1"},
    )


# ============================================================================
# ChatMessage Tests
# ============================================================================


def test_chat_message_creation_user():
    """Test ChatMessage creation for user message."""
    msg = ChatMessage(role="user", content="Make background darker")

    assert msg.role == "user"
    assert msg.content == "Make background darker"
    assert msg.image is None
    assert isinstance(msg.timestamp, datetime)
    assert msg.timestamp.tzinfo == UTC


def test_chat_message_creation_model():
    """Test ChatMessage creation for model response."""
    test_image = Image.new("RGB", (512, 512), color="blue")
    msg = ChatMessage(role="model", content="Background darkened", image=test_image)

    assert msg.role == "model"
    assert msg.content == "Background darkened"
    assert msg.image is not None
    assert msg.image.size == (512, 512)


def test_chat_message_timestamp_utc():
    """Test ChatMessage timestamp is in UTC."""
    msg = ChatMessage(role="user", content="test")

    assert msg.timestamp.tzinfo == UTC
    now = datetime.now(UTC)
    assert abs((now - msg.timestamp).total_seconds()) < 1  # Within 1 second


# ============================================================================
# ChatSession Tests
# ============================================================================


def test_chat_session_creation(mock_api_key):
    """Test ChatSession creation with default values."""
    client = GeminiProImageClient(api_key=mock_api_key)
    session = ChatSession(session_id="test_session", client=client)

    assert session.session_id == "test_session"
    assert session.client is client
    assert session.collection is None
    assert len(session.messages) == 0
    assert session.current_image is None
    assert isinstance(session.created_at, datetime)
    assert session.created_at.tzinfo == UTC


def test_chat_session_with_collection(mock_api_key):
    """Test ChatSession creation with BLACK_ROSE collection."""
    client = GeminiProImageClient(api_key=mock_api_key)
    session = ChatSession(
        session_id="test_session", client=client, collection=Collection.BLACK_ROSE
    )

    assert session.collection == Collection.BLACK_ROSE


def test_chat_session_is_expired_false():
    """Test ChatSession.is_expired() returns False for recent session."""
    client = MagicMock()
    session = ChatSession(session_id="test", client=client)

    assert session.is_expired() is False


def test_chat_session_is_expired_true():
    """Test ChatSession.is_expired() returns True after timeout."""
    client = MagicMock()
    # Create session with old timestamp (61 minutes ago)
    old_timestamp = datetime.now(UTC) - timedelta(minutes=SESSION_TIMEOUT_MINUTES + 1)
    session = ChatSession(session_id="test", client=client, created_at=old_timestamp)

    assert session.is_expired() is True


def test_chat_session_expiry_boundary():
    """Test ChatSession expiration at exact timeout boundary."""
    client = MagicMock()
    # Create session exactly at timeout boundary
    boundary_timestamp = datetime.now(UTC) - timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    session = ChatSession(session_id="test", client=client, created_at=boundary_timestamp)

    # Should be expired (>= timeout)
    assert session.is_expired() is True


# ============================================================================
# ConversationalImageEditor Tests
# ============================================================================


@pytest.mark.asyncio
async def test_editor_init():
    """Test ConversationalImageEditor initialization."""
    editor = ConversationalImageEditor()

    assert isinstance(editor._sessions, dict)
    assert len(editor._sessions) == 0


@pytest.mark.asyncio
async def test_start_session_with_prompt(mock_api_key, mock_generation_result, test_image_file):
    """Test starting a new session with initial prompt."""
    editor = ConversationalImageEditor()

    # Mock the GeminiProImageClient.generate method
    with patch.object(
        GeminiProImageClient, "generate", return_value=mock_generation_result
    ) as mock_generate:
        with patch("agents.visual_generation.conversation_editor.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")

            session = await editor.start_session(
                image=test_image_file, initial_prompt="Make background darker"
            )

            # Verify session creation
            assert session.session_id == "12345678-1234-5678-1234-567812345678"
            assert len(session.messages) == 2  # User prompt + model response
            assert session.messages[0].role == "user"
            assert session.messages[0].content == "Make background darker"
            assert session.messages[1].role == "model"
            assert session.current_image is not None

            # Verify session stored
            assert session.session_id in editor._sessions

            # Verify client was called
            mock_generate.assert_called_once()


@pytest.mark.asyncio
async def test_start_session_with_collection(mock_api_key, mock_generation_result, test_image_file):
    """Test starting session with BLACK_ROSE collection."""
    editor = ConversationalImageEditor()

    with patch.object(GeminiProImageClient, "generate", return_value=mock_generation_result):
        with patch("agents.visual_generation.conversation_editor.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")

            session = await editor.start_session(
                image=test_image_file,
                initial_prompt="Gothic elegance",
                collection=Collection.BLACK_ROSE,
            )

            assert session.collection == Collection.BLACK_ROSE


@pytest.mark.asyncio
async def test_continue_session_success(mock_api_key, mock_generation_result, test_image_file):
    """Test continuing an existing session."""
    editor = ConversationalImageEditor()

    # Create initial session
    with patch.object(GeminiProImageClient, "generate", return_value=mock_generation_result):
        with patch("agents.visual_generation.conversation_editor.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")
            session = await editor.start_session(
                image=test_image_file, initial_prompt="Initial prompt"
            )

    # Continue session
    with patch.object(GeminiProImageClient, "generate", return_value=mock_generation_result):
        result = await editor.continue_session(
            session_id=session.session_id, prompt="Add rose gold highlights"
        )

        # Verify result
        assert result["success"] is True
        assert result["image"] is not None
        assert result["session_id"] == session.session_id
        assert result["message_count"] == 4  # 2 initial + 2 new


@pytest.mark.asyncio
async def test_continue_session_expired_raises_error(
    mock_api_key, mock_generation_result, test_image_file
):
    """Test continuing expired session raises ChatSessionExpiredError."""
    editor = ConversationalImageEditor()

    # Create session
    with patch.object(GeminiProImageClient, "generate", return_value=mock_generation_result):
        with patch("agents.visual_generation.conversation_editor.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")
            session = await editor.start_session(image=test_image_file, initial_prompt="Initial")

    # Manually expire session
    session.created_at = datetime.now(UTC) - timedelta(minutes=SESSION_TIMEOUT_MINUTES + 1)

    # Try to continue expired session
    with pytest.raises(ChatSessionExpiredError) as exc_info:
        await editor.continue_session(session_id=session.session_id, prompt="Continue")

    assert "expired" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_continue_session_not_found_raises_error():
    """Test continuing non-existent session raises ChatSessionNotFoundError."""
    editor = ConversationalImageEditor()

    with pytest.raises(ChatSessionNotFoundError) as exc_info:
        await editor.continue_session(session_id="non_existent_session", prompt="Test")

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_session_existing(mock_api_key, mock_generation_result, test_image_file):
    """Test getting an existing session."""
    editor = ConversationalImageEditor()

    # Create session
    with patch.object(GeminiProImageClient, "generate", return_value=mock_generation_result):
        with patch("agents.visual_generation.conversation_editor.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")
            session = await editor.start_session(image=test_image_file, initial_prompt="Test")

    # Get session
    retrieved = editor.get_session(session.session_id)

    assert retrieved is not None
    assert retrieved.session_id == session.session_id
    assert retrieved.messages == session.messages


@pytest.mark.asyncio
async def test_get_session_not_found():
    """Test getting non-existent session returns None."""
    editor = ConversationalImageEditor()

    retrieved = editor.get_session("non_existent_id")

    assert retrieved is None


@pytest.mark.asyncio
async def test_list_active_sessions_empty():
    """Test listing active sessions when none exist."""
    editor = ConversationalImageEditor()

    sessions = editor.list_active_sessions()

    assert len(sessions) == 0


@pytest.mark.asyncio
async def test_list_active_sessions_with_sessions(
    mock_api_key, mock_generation_result, test_image_file
):
    """Test listing active sessions excludes expired ones."""
    editor = ConversationalImageEditor()

    # Create 2 active sessions
    with patch.object(GeminiProImageClient, "generate", return_value=mock_generation_result):
        with patch("agents.visual_generation.conversation_editor.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = uuid.UUID("11111111-1111-1111-1111-111111111111")
            session1 = await editor.start_session(image=test_image_file, initial_prompt="Test 1")

            mock_uuid.return_value = uuid.UUID("22222222-2222-2222-2222-222222222222")
            session2 = await editor.start_session(image=test_image_file, initial_prompt="Test 2")

    # Expire session1
    session1.created_at = datetime.now(UTC) - timedelta(minutes=SESSION_TIMEOUT_MINUTES + 1)

    # List active sessions
    active = editor.list_active_sessions()

    assert len(active) == 1
    assert active[0]["session_id"] == session2.session_id


@pytest.mark.asyncio
async def test_cleanup_expired_sessions_none_expired(
    mock_api_key, mock_generation_result, test_image_file
):
    """Test cleanup when no sessions are expired."""
    editor = ConversationalImageEditor()

    # Create 2 active sessions
    with patch.object(GeminiProImageClient, "generate", return_value=mock_generation_result):
        with patch("agents.visual_generation.conversation_editor.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = uuid.UUID("11111111-1111-1111-1111-111111111111")
            await editor.start_session(image=test_image_file, initial_prompt="Test 1")

            mock_uuid.return_value = uuid.UUID("22222222-2222-2222-2222-222222222222")
            await editor.start_session(image=test_image_file, initial_prompt="Test 2")

    # Cleanup
    cleaned = await editor.cleanup_expired_sessions()

    assert cleaned == 0
    assert len(editor._sessions) == 2


@pytest.mark.asyncio
async def test_cleanup_expired_sessions_removes_expired(
    mock_api_key, mock_generation_result, test_image_file
):
    """Test cleanup removes expired sessions."""
    editor = ConversationalImageEditor()

    # Create 3 sessions
    with patch.object(GeminiProImageClient, "generate", return_value=mock_generation_result):
        with patch("agents.visual_generation.conversation_editor.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = uuid.UUID("11111111-1111-1111-1111-111111111111")
            session1 = await editor.start_session(image=test_image_file, initial_prompt="Test 1")

            mock_uuid.return_value = uuid.UUID("22222222-2222-2222-2222-222222222222")
            session2 = await editor.start_session(image=test_image_file, initial_prompt="Test 2")

            mock_uuid.return_value = uuid.UUID("33333333-3333-3333-3333-333333333333")
            session3 = await editor.start_session(image=test_image_file, initial_prompt="Test 3")

    # Expire sessions 1 and 2
    session1.created_at = datetime.now(UTC) - timedelta(minutes=SESSION_TIMEOUT_MINUTES + 1)
    session2.created_at = datetime.now(UTC) - timedelta(minutes=SESSION_TIMEOUT_MINUTES + 1)

    # Cleanup
    cleaned = await editor.cleanup_expired_sessions()

    assert cleaned == 2
    assert len(editor._sessions) == 1
    assert session3.session_id in editor._sessions


@pytest.mark.asyncio
async def test_close_session(mock_api_key, mock_generation_result, test_image_file):
    """Test manually closing a session."""
    editor = ConversationalImageEditor()

    # Create session
    with patch.object(GeminiProImageClient, "generate", return_value=mock_generation_result):
        with patch("agents.visual_generation.conversation_editor.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")
            session = await editor.start_session(image=test_image_file, initial_prompt="Test")

    # Close session
    success = await editor.close_session(session.session_id)

    assert success is True
    assert session.session_id not in editor._sessions


@pytest.mark.asyncio
async def test_close_session_not_found():
    """Test closing non-existent session returns False."""
    editor = ConversationalImageEditor()

    success = await editor.close_session("non_existent_id")

    assert success is False


@pytest.mark.asyncio
async def test_multi_turn_conversation_flow(mock_api_key, mock_generation_result, test_image_file):
    """Test complete multi-turn conversation workflow."""
    editor = ConversationalImageEditor()

    # Turn 1: Start session
    with patch.object(GeminiProImageClient, "generate", return_value=mock_generation_result):
        with patch("agents.visual_generation.conversation_editor.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")
            session = await editor.start_session(
                image=test_image_file,
                initial_prompt="Make background darker",
                collection=Collection.BLACK_ROSE,
            )

    # Turn 2: Add rose gold highlights
    with patch.object(GeminiProImageClient, "generate", return_value=mock_generation_result):
        await editor.continue_session(
            session_id=session.session_id, prompt="Add rose gold highlights to logo"
        )

    # Turn 3: Increase contrast
    with patch.object(GeminiProImageClient, "generate", return_value=mock_generation_result):
        result3 = await editor.continue_session(
            session_id=session.session_id, prompt="Increase contrast"
        )

    # Verify conversation history
    final_session = editor.get_session(session.session_id)
    assert len(final_session.messages) == 6  # 3 turns × 2 messages each
    assert final_session.messages[0].content == "Make background darker"
    assert final_session.messages[2].content == "Add rose gold highlights to logo"
    assert final_session.messages[4].content == "Increase contrast"
    assert result3["message_count"] == 6


@pytest.mark.asyncio
async def test_concurrent_sessions(mock_api_key, mock_generation_result, test_image_file):
    """Test managing multiple concurrent sessions."""
    editor = ConversationalImageEditor()

    # Create 5 concurrent sessions
    session_ids = []
    with patch.object(GeminiProImageClient, "generate", return_value=mock_generation_result):
        for i in range(5):
            with patch("agents.visual_generation.conversation_editor.uuid.uuid4") as mock_uuid:
                mock_uuid.return_value = uuid.UUID(f"12345678-1234-5678-1234-{i:012d}")
                session = await editor.start_session(
                    image=test_image_file, initial_prompt=f"Prompt {i}"
                )
                session_ids.append(session.session_id)

    # Verify all sessions exist
    assert len(editor._sessions) == 5

    # Continue each session
    with patch.object(GeminiProImageClient, "generate", return_value=mock_generation_result):
        for session_id in session_ids:
            result = await editor.continue_session(session_id=session_id, prompt="Continue")
            assert result["success"] is True

    # Verify all sessions still exist and have correct message count
    for session_id in session_ids:
        session = editor.get_session(session_id)
        assert len(session.messages) == 4  # 2 initial + 2 continue


@pytest.mark.asyncio
async def test_session_timeout_prevents_modification(test_image_file):
    """Test that expired sessions cannot be modified."""
    editor = ConversationalImageEditor()
    mock_result = MagicMock()

    # Create and expire session
    with patch.object(GeminiProImageClient, "generate", return_value=mock_result):
        with patch("agents.visual_generation.conversation_editor.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")
            session = await editor.start_session(image=test_image_file, initial_prompt="Test")

    # Expire session
    session.created_at = datetime.now(UTC) - timedelta(minutes=SESSION_TIMEOUT_MINUTES + 1)

    # Attempt to continue should raise error
    with pytest.raises(ChatSessionExpiredError):
        await editor.continue_session(session_id=session.session_id, prompt="Continue")

    # Verify session wasn't modified
    assert len(session.messages) == 2  # Only initial messages
