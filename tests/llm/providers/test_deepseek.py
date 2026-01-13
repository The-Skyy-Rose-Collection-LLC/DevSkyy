"""
Tests for DeepSeek LLM Provider
================================
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from llm.base import Message
from llm.providers.deepseek import DeepSeekClient


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deepseek_chat_completion(mock_api_keys, mock_deepseek_response):
    """Test basic chat completion with DeepSeek."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_deepseek_response
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        client = DeepSeekClient()
        messages = [Message.user("Write a factorial function")]

        response = await client.complete(messages, model="deepseek-chat")

        assert response.content
        assert "factorial" in response.content.lower()
        assert response.model == "deepseek-chat"
        assert response.total_tokens == 70


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deepseek_reasoning_model(mock_api_keys):
    """Test DeepSeek-R1 reasoning model."""
    reasoning_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Solution using DP...",
                    "reasoning_content": "Step 1: Identify subproblems...",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 20, "completion_tokens": 100, "total_tokens": 120},
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = reasoning_response
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        client = DeepSeekClient()
        messages = [Message.user("Solve this optimization problem")]

        response = await client.complete(messages, model="deepseek-reasoner")

        assert response.content == "Solution using DP..."
        assert response.metadata.get("reasoning_content") == "Step 1: Identify subproblems..."


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deepseek_cost_calculation(mock_api_keys, mock_deepseek_response):
    """Test cost calculation for DeepSeek (should be very cheap)."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_deepseek_response
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        client = DeepSeekClient()
        messages = [Message.user("Test")]

        response = await client.complete(messages)

        # DeepSeek pricing: $0.14/$0.28 per 1M tokens
        expected_input_cost = (20 / 1_000_000) * 0.14
        expected_output_cost = (50 / 1_000_000) * 0.28
        expected_total = expected_input_cost + expected_output_cost

        # Cost should be very low (< $0.01)
        assert response.cost_usd < 0.01
        assert abs(response.cost_usd - expected_total) < 0.0001


@pytest.mark.unit
def test_deepseek_provider_config(mock_api_keys):
    """Test DeepSeek provider configuration."""
    assert DeepSeekClient.provider == "deepseek"
    assert DeepSeekClient.default_model == "deepseek-chat"

    # Check default base_url via instance (it's an instance variable)
    client = DeepSeekClient()
    assert client.base_url == "https://api.deepseek.com/v1"
