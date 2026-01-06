"""
Tests for LLM Verification Layer
=================================
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from llm.verification import (
    LLMVerificationEngine,
    VerificationConfig,
    VerificationDecision,
    VerificationResult,
)
from llm.base import Message, CompletionResponse


@pytest.mark.unit
@pytest.mark.asyncio
async def test_verification_approved(mock_api_keys):
    """Test successful verification (code approved)."""
    # Mock generator (DeepSeek)
    generator = AsyncMock()
    gen_response = CompletionResponse(
        content="def add(a, b):\n    return a + b",
        model="deepseek-chat",
        usage=MagicMock(total_tokens=50),
        cost_usd=0.00001,
    )
    generator.complete.return_value = gen_response

    # Mock verifier (Claude) - approves
    verifier = AsyncMock()
    verify_response = CompletionResponse(
        content="DECISION: approved\nFEEDBACK: Code is correct and follows best practices.",
        model="claude-3-5-sonnet",
        usage=MagicMock(total_tokens=30),
        cost_usd=0.001,
    )
    verifier.complete.return_value = verify_response

    config = VerificationConfig()
    engine = LLMVerificationEngine(generator, verifier, config)

    messages = [Message.user("Write an add function")]
    response, verification = await engine.generate_and_verify("Add function", messages)

    assert verification.decision == VerificationDecision.APPROVED
    assert response.content == gen_response.content
    assert verification.cost_savings_pct > 90  # Should save >90%


@pytest.mark.unit
@pytest.mark.asyncio
async def test_verification_rejected_then_fixes(mock_api_keys):
    """Test verification rejection followed by successful fix."""
    # Mock generator
    generator = AsyncMock()

    # First attempt - bad code
    bad_response = CompletionResponse(
        content="def add(a, b): return a - b  # Wrong!",
        model="deepseek-chat",
        usage=MagicMock(total_tokens=40),
        cost_usd=0.00001,
    )

    # Second attempt - fixed code
    fixed_response = CompletionResponse(
        content="def add(a, b): return a + b",
        model="deepseek-chat",
        usage=MagicMock(total_tokens=40),
        cost_usd=0.00001,
    )

    generator.complete.side_effect = [bad_response, fixed_response]

    # Mock verifier
    verifier = AsyncMock()

    # First verification - reject
    reject_response = CompletionResponse(
        content="DECISION: rejected\nISSUES: Function subtracts instead of adds",
        model="claude-3-5-sonnet",
        usage=MagicMock(total_tokens=30),
        cost_usd=0.001,
    )

    # Second verification - approve
    approve_response = CompletionResponse(
        content="DECISION: approved\nFEEDBACK: Code is now correct.",
        model="claude-3-5-sonnet",
        usage=MagicMock(total_tokens=25),
        cost_usd=0.001,
    )

    verifier.complete.side_effect = [reject_response, approve_response]

    config = VerificationConfig(max_retries=2)
    engine = LLMVerificationEngine(generator, verifier, config)

    messages = [Message.user("Write an add function")]
    response, verification = await engine.generate_and_verify("Add function", messages)

    assert verification.decision == VerificationDecision.APPROVED
    assert generator.complete.call_count == 2  # Retried once
    assert verifier.complete.call_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_verification_max_retries_exceeded(mock_api_keys):
    """Test verification when max retries exceeded."""
    generator = AsyncMock()
    bad_response = CompletionResponse(
        content="bad code",
        model="deepseek-chat",
        usage=MagicMock(total_tokens=40),
        cost_usd=0.00001,
    )
    generator.complete.return_value = bad_response

    verifier = AsyncMock()
    reject_response = CompletionResponse(
        content="DECISION: rejected\nISSUES: Code is incorrect",
        model="claude-3-5-sonnet",
        usage=MagicMock(total_tokens=30),
        cost_usd=0.001,
    )
    verifier.complete.return_value = reject_response

    config = VerificationConfig(max_retries=2, auto_escalate=False)
    engine = LLMVerificationEngine(generator, verifier, config)

    messages = [Message.user("Write code")]
    response, verification = await engine.generate_and_verify("Task", messages)

    assert verification.decision == VerificationDecision.REJECTED
    assert generator.complete.call_count == 2  # Initial + 1 retry


@pytest.mark.unit
@pytest.mark.asyncio
async def test_verification_auto_escalation(mock_api_keys):
    """Test auto-escalation to premium model after failures."""
    generator = AsyncMock()
    bad_response = CompletionResponse(
        content="bad code",
        model="deepseek-chat",
        usage=MagicMock(total_tokens=40),
        cost_usd=0.00001,
    )
    generator.complete.return_value = bad_response

    verifier = AsyncMock()

    # Rejection response
    reject_response = CompletionResponse(
        content="DECISION: rejected\nISSUES: Code is incorrect",
        model="claude-3-5-sonnet",
        usage=MagicMock(total_tokens=30),
        cost_usd=0.001,
    )

    # Final approval (after escalation)
    approve_response = CompletionResponse(
        content="Good escalated code",
        model="claude-3-5-sonnet",
        usage=MagicMock(total_tokens=100),
        cost_usd=0.005,
    )

    verifier.complete.side_effect = [reject_response, reject_response, approve_response]

    config = VerificationConfig(max_retries=2, auto_escalate=True)
    engine = LLMVerificationEngine(generator, verifier, config)

    messages = [Message.user("Write code")]
    response, verification = await engine.generate_and_verify("Task", messages)

    # Should escalate to premium model
    assert verification.decision == VerificationDecision.APPROVED
    assert response.content == "Good escalated code"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_verification_cost_savings_calculation(mock_api_keys):
    """Test cost savings calculation."""
    generator = AsyncMock()
    gen_response = CompletionResponse(
        content="code",
        model="deepseek-chat",
        usage=MagicMock(total_tokens=1000),
        cost_usd=0.0002,  # DeepSeek: very cheap
    )
    generator.complete.return_value = gen_response

    verifier = AsyncMock()
    verify_response = CompletionResponse(
        content="DECISION: approved\nFEEDBACK: Good",
        model="claude-3-5-sonnet",
        usage=MagicMock(total_tokens=100),
        cost_usd=0.001,  # Claude: more expensive
    )
    verifier.complete.return_value = verify_response

    config = VerificationConfig()
    engine = LLMVerificationEngine(generator, verifier, config)

    messages = [Message.user("Write code")]
    _, verification = await engine.generate_and_verify("Task", messages)

    # DeepSeek + Claude should be much cheaper than GPT-4 alone
    # Assuming GPT-4 would cost ~$0.015 for same task
    gpt4_cost = 0.015
    actual_cost = verification.total_cost_usd
    savings_pct = ((gpt4_cost - actual_cost) / gpt4_cost) * 100

    assert verification.cost_savings_pct > 90
    assert verification.total_cost_usd < 0.002
