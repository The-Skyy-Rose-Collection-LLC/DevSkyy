"""
Unit Tests for Gemini Native Image Generation
==============================================

Tests for GeminiNativeImageClient, GeminiFlashImageClient, and GeminiProImageClient.

Author: DevSkyy Platform Team
"""

import base64
from io import BytesIO
from unittest.mock import AsyncMock, patch

import pytest
from PIL import Image

from agents.visual_generation.gemini_native import (
    AspectRatio,
    GeminiAuthenticationError,
    GeminiFlashImageClient,
    GeminiNativeError,
    GeminiNativeImageClient,
    GeminiProImageClient,
    GeminiRateLimitError,
    GeminiServiceUnavailableError,
    GeminiTimeoutError,
    ImageGenerationConfig,
    ImageSize,
)
from orchestration.brand_context import Collection

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_api_key():
    """Mock API key for testing."""
    return "test-api-key-123"


@pytest.fixture
def mock_success_response():
    """Mock successful API response with image data."""
    # Create a small test image
    img = Image.new("RGB", (100, 100), color="red")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    img_bytes = buffer.getvalue()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": img_b64,
                            }
                        }
                    ]
                },
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 50,
            "candidatesTokenCount": 1290,
            "totalTokenCount": 1340,
        },
    }


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient."""
    with patch("httpx.AsyncClient") as mock:
        client = AsyncMock()
        mock.return_value = client
        yield client


# =============================================================================
# Test Base Client Initialization
# =============================================================================


def test_client_init_with_api_key(mock_api_key):
    """Test client initialization with explicit API key."""
    client = GeminiNativeImageClient(api_key=mock_api_key)
    assert client.api_key == mock_api_key
    assert client.model == "gemini-2.5-flash-image"
    assert client.timeout == 60.0
    assert client.max_retries == 3


def test_client_init_no_api_key_raises_error():
    """Test client initialization without API key raises error."""
    with patch.dict("os.environ", {}, clear=True), pytest.raises(GeminiAuthenticationError):
        GeminiNativeImageClient()


def test_flash_client_init(mock_api_key):
    """Test Flash client initialization."""
    client = GeminiFlashImageClient(api_key=mock_api_key)
    assert client.model == "gemini-2.5-flash-image"
    assert client.COST_PER_IMAGE == 0.02


def test_pro_client_init(mock_api_key):
    """Test Pro client initialization."""
    client = GeminiProImageClient(api_key=mock_api_key)
    assert client.model == "gemini-3-pro-image-preview"
    assert client.COST_PER_IMAGE == 0.08
    assert client.timeout == 90.0  # Longer timeout for Pro


# =============================================================================
# Test Brand DNA Injection
# =============================================================================


def test_brand_dna_injection_no_collection(mock_api_key):
    """Test brand DNA injection without collection."""
    client = GeminiNativeImageClient(api_key=mock_api_key)
    prompt = "luxury hoodie"
    enhanced = client._inject_brand_dna(prompt, collection=None)

    assert "luxury hoodie" in enhanced
    assert "SkyyRose" in enhanced
    assert "#B76E79" in enhanced or "Rose Gold" in enhanced


def test_brand_dna_injection_with_collection(mock_api_key):
    """Test brand DNA injection with BLACK_ROSE collection."""
    client = GeminiNativeImageClient(api_key=mock_api_key)
    prompt = "gothic hoodie"
    enhanced = client._inject_brand_dna(prompt, collection=Collection.BLACK_ROSE)

    assert "gothic hoodie" in enhanced
    assert "SkyyRose" in enhanced
    assert "Black Rose" in enhanced or "BLACK_ROSE" in enhanced


# =============================================================================
# Test Image Generation
# =============================================================================


@pytest.mark.asyncio
async def test_generate_image_success(mock_api_key, mock_success_response, mock_httpx_client):
    """Test successful image generation."""
    client = GeminiNativeImageClient(api_key=mock_api_key)

    # Mock the HTTP response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_success_response
    mock_httpx_client.request.return_value = mock_response

    # Manually set the client
    await client.connect()
    client._client = mock_httpx_client

    result = await client.generate(
        prompt="test prompt", inject_brand_dna=False  # Disable for simpler testing
    )

    assert result.image is not None
    assert result.prompt == "test prompt"
    assert result.model == "gemini-2.5-flash-image"
    assert result.latency_ms > 0
    assert result.cost_usd == 0.02
    assert result.metadata["usage"]["total_tokens"] == 1340


@pytest.mark.asyncio
async def test_generate_image_with_config(mock_api_key, mock_success_response, mock_httpx_client):
    """Test image generation with custom config."""
    client = GeminiNativeImageClient(api_key=mock_api_key)

    # Mock response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_success_response
    mock_httpx_client.request.return_value = mock_response

    await client.connect()
    client._client = mock_httpx_client

    config = ImageGenerationConfig(
        aspect_ratio=AspectRatio.LANDSCAPE_16_9, negative_prompt="low quality"
    )

    result = await client.generate(prompt="test", config=config, inject_brand_dna=False)

    assert result.metadata["config"]["aspect_ratio"] == "16:9"
    assert result.metadata["config"]["negative_prompt"] == "low quality"


@pytest.mark.asyncio
async def test_generate_image_with_collection(
    mock_api_key, mock_success_response, mock_httpx_client
):
    """Test image generation with collection context."""
    client = GeminiFlashImageClient(api_key=mock_api_key)

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_success_response
    mock_httpx_client.request.return_value = mock_response

    await client.connect()
    client._client = mock_httpx_client

    result = await client.generate(
        prompt="luxury hoodie", collection=Collection.SIGNATURE, inject_brand_dna=True
    )

    assert result.metadata["collection"] == "SIGNATURE"
    assert "SkyyRose" in result.prompt or "Signature" in result.prompt


# =============================================================================
# Test Error Handling
# =============================================================================


@pytest.mark.asyncio
async def test_authentication_error(mock_api_key, mock_httpx_client):
    """Test authentication error handling."""
    client = GeminiNativeImageClient(api_key=mock_api_key)

    # Mock 401 response
    mock_response = AsyncMock()
    mock_response.status_code = 401
    mock_httpx_client.request.return_value = mock_response

    await client.connect()
    client._client = mock_httpx_client

    with pytest.raises(GeminiAuthenticationError):
        await client._make_request("POST", "https://test.com", json={})


@pytest.mark.asyncio
async def test_rate_limit_error_with_retry(mock_api_key, mock_httpx_client):
    """Test rate limit error triggers retry."""
    client = GeminiNativeImageClient(api_key=mock_api_key)

    # Mock 429 response
    mock_response = AsyncMock()
    mock_response.status_code = 429
    mock_response.headers = {"retry-after": "2"}
    mock_httpx_client.request.return_value = mock_response

    await client.connect()
    client._client = mock_httpx_client

    with pytest.raises(GeminiRateLimitError) as exc_info:
        await client._make_request("POST", "https://test.com", json={})

    assert exc_info.value.retry_after == 2.0
    # Should have tried 3 times
    assert mock_httpx_client.request.call_count == 3


@pytest.mark.asyncio
async def test_service_unavailable_error_with_retry(mock_api_key, mock_httpx_client):
    """Test service unavailable error triggers retry."""
    client = GeminiNativeImageClient(api_key=mock_api_key)

    # Mock 503 response
    mock_response = AsyncMock()
    mock_response.status_code = 503
    mock_httpx_client.request.return_value = mock_response

    await client.connect()
    client._client = mock_httpx_client

    with pytest.raises(GeminiServiceUnavailableError):
        await client._make_request("POST", "https://test.com", json={})

    # Should have tried 3 times
    assert mock_httpx_client.request.call_count == 3


@pytest.mark.asyncio
async def test_timeout_error(mock_api_key, mock_httpx_client):
    """Test timeout error handling."""
    import httpx

    client = GeminiNativeImageClient(api_key=mock_api_key, timeout=1.0)

    # Mock timeout
    mock_httpx_client.request.side_effect = httpx.TimeoutException("timeout")

    await client.connect()
    client._client = mock_httpx_client

    with pytest.raises(GeminiTimeoutError):
        await client._make_request("POST", "https://test.com", json={})


@pytest.mark.asyncio
async def test_no_image_in_response(mock_api_key, mock_httpx_client):
    """Test error when response contains no image data."""
    client = GeminiNativeImageClient(api_key=mock_api_key)

    # Mock response without image data
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"candidates": []}
    mock_httpx_client.request.return_value = mock_response

    await client.connect()
    client._client = mock_httpx_client

    with pytest.raises(GeminiNativeError) as exc_info:
        await client.generate("test", inject_brand_dna=False)

    assert "No image generated" in str(exc_info.value)


# =============================================================================
# Test Async Context Manager
# =============================================================================


@pytest.mark.asyncio
async def test_async_context_manager(mock_api_key):
    """Test async context manager properly connects and closes."""
    async with GeminiNativeImageClient(api_key=mock_api_key) as client:
        assert client._client is not None

    # Client should be closed after context exit
    assert client._client is None


# =============================================================================
# Test Flash vs Pro Specific Behavior
# =============================================================================


@pytest.mark.asyncio
async def test_flash_ignores_image_size(mock_api_key, mock_success_response, mock_httpx_client):
    """Test Flash client ignores image_size parameter."""
    client = GeminiFlashImageClient(api_key=mock_api_key)

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_success_response
    mock_httpx_client.request.return_value = mock_response

    await client.connect()
    client._client = mock_httpx_client

    config = ImageGenerationConfig(image_size=ImageSize.SIZE_4K)  # Should be ignored

    result = await client.generate("test", config=config, inject_brand_dna=False)

    # image_size should be None after generation
    assert result.metadata["config"]["image_size"] is None


@pytest.mark.asyncio
async def test_pro_sets_default_image_size(mock_api_key, mock_success_response, mock_httpx_client):
    """Test Pro client sets default image_size to 2K."""
    client = GeminiProImageClient(api_key=mock_api_key)

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_success_response
    mock_httpx_client.request.return_value = mock_response

    await client.connect()
    client._client = mock_httpx_client

    result = await client.generate("test", inject_brand_dna=False)

    # Should default to 2K
    assert result.metadata["config"]["image_size"] == "2K"


# =============================================================================
# Test Image Decoding
# =============================================================================


def test_decode_image_valid_base64():
    """Test decoding valid base64 image data."""
    # Create test image
    img = Image.new("RGB", (50, 50), color="blue")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    client = GeminiNativeImageClient(api_key="test")
    decoded = client._decode_image(img_b64, "image/png")

    assert decoded.size == (50, 50)
    assert decoded.mode == "RGB"


# =============================================================================
# Test Cost Calculations
# =============================================================================


def test_flash_cost():
    """Test Flash client cost is $0.02."""
    client = GeminiFlashImageClient(api_key="test")
    assert client.COST_PER_IMAGE == 0.02


def test_pro_cost():
    """Test Pro client cost is $0.08."""
    client = GeminiProImageClient(api_key="test")
    assert client.COST_PER_IMAGE == 0.08
