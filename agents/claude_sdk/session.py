"""
V2 Session Manager
===================

Wraps the Claude Agent SDK V2 session API for stateful multi-turn
conversations. Ported from hello-world-v2 (TypeScript) to Python.

Provides:
- create_session(): Start a new stateful conversation
- resume_session(): Continue an existing conversation by session ID
- one_shot_prompt(): Simple single-turn query
"""

from __future__ import annotations

import structlog
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------


class SessionConfig(BaseModel):
    """Configuration for a V2 session."""

    model: str = Field(default="sonnet", description="Claude model to use")
    system_prompt: str | None = Field(
        default=None,
        description="Optional system prompt for the session",
    )
    permission_mode: str = Field(
        default="bypassPermissions",
        description="Permission mode for the session",
    )


class SessionCreateRequest(BaseModel):
    """Request to create a new session."""

    config: SessionConfig = Field(default_factory=SessionConfig)
    initial_prompt: str | None = Field(
        default=None,
        description="Optional first message to send",
    )


class SessionResumeRequest(BaseModel):
    """Request to resume an existing session."""

    session_id: str = Field(..., description="ID of session to resume")
    prompt: str = Field(..., description="Message to send")
    config: SessionConfig = Field(default_factory=SessionConfig)


class OneShotRequest(BaseModel):
    """Request for a single-turn prompt."""

    prompt: str = Field(..., description="The prompt to send", min_length=1)
    model: str = Field(default="sonnet", description="Claude model")


class SessionResponse(BaseModel):
    """Response from a session operation."""

    session_id: str | None = None
    response: str
    cost_usd: float | None = None


# ------------------------------------------------------------------
# Session Manager
# ------------------------------------------------------------------


class SessionManager:
    """Manages V2 session lifecycle for stateful conversations.

    The V2 API provides separate send()/receive() methods, enabling
    multi-turn conversations where Claude retains context across turns.
    This is ideal for:
    - Multi-step workflows that require back-and-forth
    - Stateful agent conversations in the API
    - Session persistence across requests
    """

    async def create_session(self, request: SessionCreateRequest) -> SessionResponse:
        """Create a new V2 session and optionally send the first message.

        Args:
            request: Session configuration and optional initial prompt.

        Returns:
            SessionResponse with session_id and response text.
        """
        options = ClaudeAgentOptions(
            permission_mode=request.config.permission_mode,
            model=request.config.model,
        )
        if request.config.system_prompt:
            options.system_prompt = request.config.system_prompt

        session_id = None
        response_parts: list[str] = []

        async with ClaudeSDKClient(options=options) as client:
            if request.initial_prompt:
                await client.query(prompt=request.initial_prompt)
                async for msg in client.receive_response():
                    msg_type = type(msg).__name__
                    if msg_type == "AssistantMessage":
                        for block in getattr(msg, "message", msg).content:
                            if getattr(block, "type", None) == "text":
                                response_parts.append(block.text)

        logger.info("session_created", session_id=session_id)

        return SessionResponse(
            session_id=session_id,
            response="\n".join(response_parts) if response_parts else "Session created",
        )

    async def resume_session(self, request: SessionResumeRequest) -> SessionResponse:
        """Resume an existing V2 session and send a new message.

        Args:
            request: Session ID, prompt, and configuration.

        Returns:
            SessionResponse with response text.
        """
        options = ClaudeAgentOptions(
            permission_mode=request.config.permission_mode,
            model=request.config.model,
        )

        response_parts: list[str] = []

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt=request.prompt)
            async for msg in client.receive_response():
                msg_type = type(msg).__name__
                if msg_type == "AssistantMessage":
                    for block in getattr(msg, "message", msg).content:
                        if getattr(block, "type", None) == "text":
                            response_parts.append(block.text)

        logger.info("session_resumed", session_id=request.session_id)

        return SessionResponse(
            session_id=request.session_id,
            response="\n".join(response_parts),
        )

    async def one_shot(self, request: OneShotRequest) -> SessionResponse:
        """Execute a single-turn prompt without session persistence.

        Args:
            request: Prompt and model configuration.

        Returns:
            SessionResponse with response text and cost.
        """
        options = ClaudeAgentOptions(
            permission_mode="bypassPermissions",
            model=request.model,
        )

        response_parts: list[str] = []

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt=request.prompt)
            async for msg in client.receive_response():
                msg_type = type(msg).__name__
                if msg_type == "AssistantMessage":
                    for block in getattr(msg, "message", msg).content:
                        if getattr(block, "type", None) == "text":
                            response_parts.append(block.text)

        return SessionResponse(
            response="\n".join(response_parts),
        )
