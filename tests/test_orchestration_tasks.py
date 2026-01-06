"""
Tests for orchestration.tasks module
=====================================

Verify background task definitions for worker.

Test Coverage:
- Task input validation (Pydantic models)
- Task execution (mocked agents)
- Error handling and DLQ behavior
- Task output schema validation
"""

from unittest.mock import AsyncMock, patch

import pytest

from orchestration.tasks import (
    MarketingCampaignInput,
    MLPredictionInput,
    MLTrainingInput,
    ThreeDGenerationInput,
    execute_marketing_campaign,
    process_3d_asset_generation,
    run_ml_prediction,
    train_ml_model,
)

# =============================================================================
# Input Model Tests
# =============================================================================


def test_3d_generation_input_validation():
    """Test 3D generation input model validates correctly."""
    # Valid input
    valid_input = ThreeDGenerationInput(
        prompt="Black Rose t-shirt with premium embroidery",
        user_id="user-123",
        style="realistic",
    )
    assert valid_input.prompt == "Black Rose t-shirt with premium embroidery"
    assert valid_input.user_id == "user-123"
    assert valid_input.style == "realistic"
    assert valid_input.collection == "SIGNATURE"  # Default

    # With image
    input_with_image = ThreeDGenerationInput(
        prompt="Luxury hoodie",
        image_url="https://example.com/ref.jpg",
        user_id="user-456",
    )
    assert input_with_image.image_url == "https://example.com/ref.jpg"

    # Missing required field
    with pytest.raises(ValueError):
        ThreeDGenerationInput(prompt="Test")  # Missing user_id


def test_marketing_campaign_input_validation():
    """Test marketing campaign input model validates correctly."""
    # Valid email campaign
    valid_input = MarketingCampaignInput(
        campaign_id="camp-001",
        campaign_type="email",
        recipients=["user1@example.com", "user2@example.com"],
        content={"subject": "New Collection", "body": "Check it out!"},
        user_id="user-123",
    )
    assert valid_input.campaign_type == "email"
    assert len(valid_input.recipients) == 2

    # Missing required field
    with pytest.raises(ValueError):
        MarketingCampaignInput(
            campaign_id="camp-002",
            campaign_type="social",
            content={},
            user_id="user-123",
        )  # Missing recipients


def test_ml_training_input_validation():
    """Test ML training input model validates correctly."""
    # Valid input
    valid_input = MLTrainingInput(
        model_id="sentiment_analyzer",
        training_data_path="/data/reviews.csv",
        user_id="user-123",
        epochs=20,
        hyperparameters={"learning_rate": 0.001},
    )
    assert valid_input.model_id == "sentiment_analyzer"
    assert valid_input.epochs == 20

    # Default epochs
    default_input = MLTrainingInput(
        model_id="trend_predictor", training_data_path="/data/trends.csv", user_id="user-123"
    )
    assert default_input.epochs == 10  # Default


def test_ml_prediction_input_validation():
    """Test ML prediction input model validates correctly."""
    # Single prediction
    single_input = MLPredictionInput(
        model_id="sentiment_analyzer",
        input_data={"text": "This product is amazing!"},
        user_id="user-123",
    )
    assert isinstance(single_input.input_data, dict)

    # Batch prediction
    batch_input = MLPredictionInput(
        model_id="sentiment_analyzer",
        input_data=[{"text": "Great!"}, {"text": "Bad."}],
        user_id="user-123",
    )
    assert isinstance(batch_input.input_data, list)


# =============================================================================
# Task Execution Tests
# =============================================================================


@pytest.mark.asyncio
async def test_process_3d_asset_generation_success():
    """Test 3D asset generation task succeeds with valid input."""
    with patch("orchestration.tasks.TripoAssetAgent") as mock_agent_class:
        # Mock agent instance
        mock_agent = AsyncMock()
        mock_agent._tool_generate_from_text = AsyncMock(
            return_value={
                "task_id": "tripo-abc123",
                "model_url": "https://example.com/model.glb",
                "status": "success",
            }
        )
        mock_agent.close = AsyncMock()
        mock_agent_class.return_value = mock_agent

        # Execute task
        result = await process_3d_asset_generation(
            task_id="task-001",
            input_data={
                "prompt": "Black Rose t-shirt",
                "user_id": "user-123",
                "style": "realistic",
            },
        )

        # Verify result
        assert result["status"] == "success"
        assert result["task_id"] == "task-001"
        assert "result" in result
        assert result["result"]["task_id"] == "tripo-abc123"
        assert result["user_id"] == "user-123"

        # Verify agent called
        mock_agent._tool_generate_from_text.assert_called_once()
        mock_agent.close.assert_called_once()


@pytest.mark.asyncio
async def test_process_3d_asset_generation_with_image():
    """Test 3D asset generation with image input."""
    with patch("orchestration.tasks.TripoAssetAgent") as mock_agent_class:
        mock_agent = AsyncMock()
        mock_agent._tool_generate_from_image = AsyncMock(
            return_value={"task_id": "tripo-xyz789", "status": "success"}
        )
        mock_agent.close = AsyncMock()
        mock_agent_class.return_value = mock_agent

        # Execute with image
        result = await process_3d_asset_generation(
            task_id="task-002",
            input_data={
                "prompt": "Luxury hoodie",
                "image_url": "https://example.com/ref.jpg",
                "user_id": "user-456",
            },
        )

        # Verify image-to-3D called
        assert result["status"] == "success"
        mock_agent._tool_generate_from_image.assert_called_once()


@pytest.mark.asyncio
async def test_process_3d_asset_generation_failure():
    """Test 3D asset generation handles errors correctly."""
    with patch("orchestration.tasks.TripoAssetAgent") as mock_agent_class:
        mock_agent = AsyncMock()
        mock_agent._tool_generate_from_text = AsyncMock(side_effect=RuntimeError("API error"))
        mock_agent.close = AsyncMock()
        mock_agent_class.return_value = mock_agent

        # Execute task
        result = await process_3d_asset_generation(
            task_id="task-003",
            input_data={"prompt": "Test", "user_id": "user-123"},
        )

        # Verify error handling
        assert result["status"] == "failed"
        assert "error" in result
        assert result["error"] == "API error"
        assert result["error_type"] == "RuntimeError"


@pytest.mark.asyncio
async def test_execute_marketing_campaign_email():
    """Test marketing campaign execution (email)."""
    with patch("orchestration.tasks.MarketingAgent") as mock_agent_class:
        mock_agent = AsyncMock()
        mock_agent.initialize = AsyncMock()
        mock_agent_class.return_value = mock_agent

        # Execute email campaign
        result = await execute_marketing_campaign(
            task_id="task-004",
            input_data={
                "campaign_id": "camp-001",
                "campaign_type": "email",
                "recipients": ["user1@example.com", "user2@example.com"],
                "content": {"subject": "Test", "body": "Test email"},
                "user_id": "user-123",
            },
        )

        # Verify result
        assert result["status"] == "success"
        assert result["campaign_id"] == "camp-001"
        assert "result" in result
        assert result["result"]["sent_count"] == 2

        # Verify agent initialized
        mock_agent.initialize.assert_called_once()


@pytest.mark.asyncio
async def test_execute_marketing_campaign_invalid_type():
    """Test marketing campaign with invalid type."""
    with patch("orchestration.tasks.MarketingAgent") as mock_agent_class:
        mock_agent = AsyncMock()
        mock_agent.initialize = AsyncMock()
        mock_agent_class.return_value = mock_agent

        # Execute with invalid type
        result = await execute_marketing_campaign(
            task_id="task-005",
            input_data={
                "campaign_id": "camp-002",
                "campaign_type": "invalid",
                "recipients": ["user@example.com"],
                "content": {},
                "user_id": "user-123",
            },
        )

        # Verify error
        assert result["status"] == "failed"
        assert "Unknown campaign type" in result["error"]


@pytest.mark.asyncio
async def test_train_ml_model_success():
    """Test ML model training succeeds."""
    # Execute training
    result = await train_ml_model(
        task_id="task-006",
        input_data={
            "model_id": "sentiment_analyzer",
            "training_data_path": "/data/reviews.csv",
            "user_id": "user-123",
            "epochs": 10,
        },
    )

    # Verify result (placeholder implementation)
    assert result["status"] == "success"
    assert result["model_id"] == "sentiment_analyzer"
    assert "result" in result
    assert "accuracy" in result["result"]


@pytest.mark.asyncio
async def test_train_ml_model_invalid_model_id():
    """Test ML training with invalid model ID."""
    result = await train_ml_model(
        task_id="task-007",
        input_data={
            "model_id": "invalid_model",
            "training_data_path": "/data/test.csv",
            "user_id": "user-123",
        },
    )

    # Verify error
    assert result["status"] == "failed"
    assert "Unknown model ID" in result["error"]


@pytest.mark.asyncio
async def test_run_ml_prediction_single():
    """Test ML prediction with single input."""
    result = await run_ml_prediction(
        task_id="task-008",
        input_data={
            "model_id": "sentiment_analyzer",
            "input_data": {"text": "This product is great!"},
            "user_id": "user-123",
        },
    )

    # Verify result
    assert result["status"] == "success"
    assert result["model_id"] == "sentiment_analyzer"
    assert "result" in result
    assert "predictions" in result["result"]


@pytest.mark.asyncio
async def test_run_ml_prediction_batch():
    """Test ML prediction with batch input."""
    result = await run_ml_prediction(
        task_id="task-009",
        input_data={
            "model_id": "sentiment_analyzer",
            "input_data": [
                {"text": "Love it!"},
                {"text": "Terrible quality."},
            ],
            "user_id": "user-123",
        },
    )

    # Verify batch result
    assert result["status"] == "success"
    assert isinstance(result["result"]["predictions"], list)


# =============================================================================
# Integration Tests (require Redis)
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_task_integration_with_redis():
    """
    Integration test for task queue + worker.

    NOTE: Requires Redis running and proper environment setup.
    Run with: pytest -m integration
    """
    pytest.skip("Integration test - requires Redis")

    # TODO: Implement full integration test
    # 1. Enqueue task via TaskQueue
    # 2. Worker picks up task
    # 3. Verify result stored in Redis
    # 4. Check DLQ if failed


# =============================================================================
# Performance Tests
# =============================================================================


@pytest.mark.slow
@pytest.mark.asyncio
async def test_concurrent_task_execution():
    """Test multiple tasks can execute concurrently."""
    pytest.skip("Performance test - slow")

    # TODO: Implement concurrent execution test
    # Execute 100 tasks concurrently and verify all complete


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "test_3d_generation_input_validation",
    "test_marketing_campaign_input_validation",
    "test_ml_training_input_validation",
    "test_ml_prediction_input_validation",
    "test_process_3d_asset_generation_success",
    "test_process_3d_asset_generation_with_image",
    "test_process_3d_asset_generation_failure",
    "test_execute_marketing_campaign_email",
    "test_execute_marketing_campaign_invalid_type",
    "test_train_ml_model_success",
    "test_train_ml_model_invalid_model_id",
    "test_run_ml_prediction_single",
    "test_run_ml_prediction_batch",
]
