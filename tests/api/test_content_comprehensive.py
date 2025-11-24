"""
Comprehensive Tests for Content Publishing API Endpoints (api/v1/content.py)
Tests content creation, publishing, batch operations, categorization, and configuration

Coverage target: ≥80% for api/v1/content.py

Author: DevSkyy Team
Version: 1.0.0
Python: >=3.11.0
Per CLAUDE.md Truth Protocol requirements
"""

from datetime import datetime
import os
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from fastapi import HTTPException
import pytest


# Mock external dependencies before importing the content module
sys.modules["google"] = MagicMock()
sys.modules["google.oauth2"] = MagicMock()
sys.modules["google.oauth2.credentials"] = MagicMock()
sys.modules["google.auth"] = MagicMock()
sys.modules["google.auth.transport"] = MagicMock()
sys.modules["google.auth.transport.requests"] = MagicMock()
sys.modules["googleapiclient"] = MagicMock()
sys.modules["googleapiclient.discovery"] = MagicMock()
sys.modules["services.content_publishing_orchestrator"] = MagicMock()
sys.modules["services.wordpress_categorization"] = MagicMock()
sys.modules["services.content_generator"] = MagicMock()
sys.modules["services.pexels_service"] = MagicMock()
sys.modules["services.wordpress_service"] = MagicMock()
sys.modules["services.telegram_service"] = MagicMock()
sys.modules["services.google_sheets_service"] = MagicMock()

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for content publishing"""
    with patch.dict(
        os.environ,
        {
            "ANTHROPIC_API_KEY": "test-anthropic-key",
            "PEXELS_API_KEY": "test-pexels-key",
            "TELEGRAM_BOT_TOKEN": "test-telegram-token",
            "TELEGRAM_CHAT_ID": "test-chat-id",
            "OPENAI_API_KEY": "test-openai-key",
            "GOOGLE_SHEETS_ID": "test-sheets-id",
            "SKYY_ROSE_SITE_URL": "https://test-site.com",
        },
    ):
        yield


@pytest.fixture
def mock_orchestrator():
    """Mock ContentPublishingOrchestrator"""
    orchestrator = Mock()
    orchestrator.execute_workflow = AsyncMock()
    orchestrator.telegram_service = Mock()
    orchestrator.telegram_service.send_notification = AsyncMock()
    return orchestrator


@pytest.fixture
def mock_categorization_service():
    """Mock WordPressCategorizationService"""
    service = Mock()
    service.categorize_posts_batch = AsyncMock()
    service.get_all_categories = Mock()
    return service


@pytest.fixture
def successful_workflow_result():
    """Mock successful workflow execution result"""
    return {
        "success": True,
        "content": {
            "title": "Test Content Title",
            "word_count": 850,
            "body": "Test content body...",
        },
        "wordpress_post": {
            "url": "https://example.com/test-post",
            "id": 123,
        },
        "image": {
            "url": "https://images.pexels.com/test.jpg",
        },
        "duration_seconds": 5.2,
        "delay_applied": 120.0,
    }


@pytest.fixture
def failed_workflow_result():
    """Mock failed workflow execution result"""
    return {
        "success": False,
        "error": "Content generation failed",
    }


# ============================================================================
# TEST DEPENDENCY INJECTION
# ============================================================================


class TestGetOrchestratorService:
    """Test get_orchestrator_service dependency"""

    def test_get_orchestrator_success(self, mock_env_vars):
        """Should create orchestrator when env vars are set"""
        from api.v1.content import get_orchestrator_service

        with patch("api.v1.content.ContentPublishingOrchestrator") as mock_cls:
            mock_cls.return_value = Mock()
            orchestrator = get_orchestrator_service()

            assert orchestrator is not None
            mock_cls.assert_called_once_with(
                anthropic_api_key="test-anthropic-key",
                pexels_api_key="test-pexels-key",
                telegram_bot_token="test-telegram-token",
                telegram_chat_id="test-chat-id",
            )

    def test_get_orchestrator_missing_anthropic_key(self):
        """Should raise HTTPException when ANTHROPIC_API_KEY is missing"""
        from api.v1.content import get_orchestrator_service

        with patch.dict(os.environ, {"PEXELS_API_KEY": "test-key"}, clear=True):
            with pytest.raises(HTTPException) as exc_info:
                get_orchestrator_service()

            assert exc_info.value.status_code == 500
            assert "ANTHROPIC_API_KEY" in str(exc_info.value.detail)

    def test_get_orchestrator_missing_pexels_key(self):
        """Should raise HTTPException when PEXELS_API_KEY is missing"""
        from api.v1.content import get_orchestrator_service

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True):
            with pytest.raises(HTTPException) as exc_info:
                get_orchestrator_service()

            assert exc_info.value.status_code == 500
            assert "PEXELS_API_KEY" in str(exc_info.value.detail)


# ============================================================================
# TEST PUBLISH CONTENT ENDPOINT
# ============================================================================


class TestPublishContent:
    """Test POST /content/publish endpoint"""

    @pytest.mark.asyncio
    async def test_publish_content_success(self, mock_orchestrator, successful_workflow_result):
        """Should publish content successfully"""
        from fastapi import BackgroundTasks

        from api.v1.content import PublishContentRequest, publish_content

        # Setup mock
        mock_orchestrator.execute_workflow.return_value = successful_workflow_result

        # Create request
        request = PublishContentRequest(
            topic="Luxury Fashion Trends 2025",
            keywords=["luxury", "fashion"],
            tone="luxury",
            length=1000,
            apply_random_delay=True,
            max_delay_hours=2,
        )

        # Call endpoint
        result = await publish_content(
            request=request,
            background_tasks=BackgroundTasks(),
            orchestrator=mock_orchestrator,
        )

        # Assertions
        assert result.success is True
        assert result.message == "Content published successfully"
        assert result.title == "Test Content Title"
        assert result.wordpress_url == "https://example.com/test-post"
        assert result.wordpress_id == 123
        assert result.word_count == 850
        assert result.image_url == "https://images.pexels.com/test.jpg"
        assert result.duration_seconds == 5.2
        assert result.delay_applied_seconds == 120.0

        # Verify orchestrator was called correctly
        mock_orchestrator.execute_workflow.assert_called_once_with(
            topic="Luxury Fashion Trends 2025",
            keywords=["luxury", "fashion"],
            tone="luxury",
            length=1000,
            apply_random_delay=True,
            min_delay_hours=0,
            max_delay_hours=2,
            publish_status="publish",
            notify=True,
            log_to_sheets=True,
        )

    @pytest.mark.asyncio
    async def test_publish_content_failure(self, mock_orchestrator, failed_workflow_result):
        """Should raise HTTPException on workflow failure"""
        from fastapi import BackgroundTasks

        from api.v1.content import PublishContentRequest, publish_content

        # Setup mock
        mock_orchestrator.execute_workflow.return_value = failed_workflow_result

        # Create request
        request = PublishContentRequest(topic="Test Topic")

        # Call endpoint and expect exception
        with pytest.raises(HTTPException) as exc_info:
            await publish_content(
                request=request,
                background_tasks=BackgroundTasks(),
                orchestrator=mock_orchestrator,
            )

        assert exc_info.value.status_code == 500
        assert "Content generation failed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_publish_content_exception(self, mock_orchestrator):
        """Should handle unexpected exceptions"""
        from fastapi import BackgroundTasks

        from api.v1.content import PublishContentRequest, publish_content

        # Setup mock to raise exception
        mock_orchestrator.execute_workflow.side_effect = Exception("Unexpected error")

        # Create request
        request = PublishContentRequest(topic="Test Topic")

        # Call endpoint and expect exception
        with pytest.raises(HTTPException) as exc_info:
            await publish_content(
                request=request,
                background_tasks=BackgroundTasks(),
                orchestrator=mock_orchestrator,
            )

        assert exc_info.value.status_code == 500
        assert "Unexpected error" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_publish_content_no_image(self, mock_orchestrator):
        """Should handle workflow result without image"""
        from fastapi import BackgroundTasks

        from api.v1.content import PublishContentRequest, publish_content

        # Setup mock result without image
        result = {
            "success": True,
            "content": {"title": "Test", "word_count": 500},
            "wordpress_post": {"url": "https://example.com/test", "id": 1},
            "duration_seconds": 3.0,
        }
        mock_orchestrator.execute_workflow.return_value = result

        # Create request
        request = PublishContentRequest(topic="Test Topic")

        # Call endpoint
        response = await publish_content(
            request=request,
            background_tasks=BackgroundTasks(),
            orchestrator=mock_orchestrator,
        )

        # Assertions
        assert response.success is True
        assert response.image_url is None


# ============================================================================
# TEST BATCH PUBLISH ENDPOINT
# ============================================================================


class TestPublishContentBatch:
    """Test POST /content/publish-batch endpoint"""

    @pytest.mark.asyncio
    async def test_batch_publish_success(self, mock_orchestrator):
        """Should publish multiple topics successfully"""
        from api.v1.content import publish_content_batch

        # Setup mock - all succeed
        mock_orchestrator.execute_workflow.return_value = {
            "success": True,
            "content": {"title": "Test Title", "word_count": 800},
            "wordpress_post": {"url": "https://example.com/test", "id": 1},
        }

        # Call endpoint
        topics = ["Topic 1", "Topic 2", "Topic 3"]
        result = await publish_content_batch(
            topics=topics,
            keywords=["test", "keywords"],
            tone="professional",
            length=800,
            orchestrator=mock_orchestrator,
        )

        # Assertions
        assert result["success"] is True
        assert result["total"] == 3
        assert result["succeeded"] == 3
        assert result["failed"] == 0
        assert len(result["results"]) == 3

        # Verify each result
        for res in result["results"]:
            assert res["success"] is True
            assert res["title"] == "Test Title"
            assert res["url"] == "https://example.com/test"

        # Verify orchestrator called correctly for each topic
        assert mock_orchestrator.execute_workflow.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_publish_partial_failure(self, mock_orchestrator):
        """Should handle partial failures in batch"""
        from api.v1.content import publish_content_batch

        # Setup mock - second one fails
        call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return {"success": False, "error": "Failed"}
            return {
                "success": True,
                "content": {"title": f"Title {call_count}", "word_count": 800},
                "wordpress_post": {"url": f"https://example.com/test-{call_count}", "id": call_count},
            }

        mock_orchestrator.execute_workflow.side_effect = mock_execute

        # Call endpoint
        topics = ["Topic 1", "Topic 2", "Topic 3"]
        result = await publish_content_batch(
            topics=topics,
            orchestrator=mock_orchestrator,
        )

        # Assertions
        assert result["success"] is True
        assert result["total"] == 3
        assert result["succeeded"] == 2
        assert result["failed"] == 1

    @pytest.mark.asyncio
    async def test_batch_publish_with_exception(self, mock_orchestrator):
        """Should handle exceptions during batch processing"""
        from api.v1.content import publish_content_batch

        # Setup mock - second one raises exception
        call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Network error")
            return {
                "success": True,
                "content": {"title": f"Title {call_count}", "word_count": 800},
                "wordpress_post": {"url": f"https://example.com/test-{call_count}", "id": call_count},
            }

        mock_orchestrator.execute_workflow.side_effect = mock_execute

        # Call endpoint
        topics = ["Topic 1", "Topic 2", "Topic 3"]
        result = await publish_content_batch(
            topics=topics,
            orchestrator=mock_orchestrator,
        )

        # Assertions
        assert result["success"] is True
        assert result["total"] == 3
        assert result["succeeded"] == 2
        assert result["failed"] == 1

        # Check failed result
        failed_results = [r for r in result["results"] if not r["success"]]
        assert len(failed_results) == 1
        assert "error" in failed_results[0]

    @pytest.mark.asyncio
    async def test_batch_publish_sends_summary(self, mock_orchestrator):
        """Should send Telegram summary notification"""
        from api.v1.content import publish_content_batch

        # Setup mock
        mock_orchestrator.execute_workflow.return_value = {
            "success": True,
            "content": {"title": "Test", "word_count": 800},
            "wordpress_post": {"url": "https://example.com/test", "id": 1},
        }

        # Call endpoint
        topics = ["Topic 1", "Topic 2"]
        result = await publish_content_batch(
            topics=topics,
            orchestrator=mock_orchestrator,
        )

        # Verify telegram notification was sent
        mock_orchestrator.telegram_service.send_notification.assert_called_once()
        notification_text = mock_orchestrator.telegram_service.send_notification.call_args[0][0]
        assert "Batch Publishing Complete" in notification_text
        assert "Total:" in notification_text
        assert "Succeeded:" in notification_text

    @pytest.mark.asyncio
    async def test_batch_publish_no_keywords(self, mock_orchestrator):
        """Should handle None keywords parameter"""
        from api.v1.content import publish_content_batch

        # Setup mock
        mock_orchestrator.execute_workflow.return_value = {
            "success": True,
            "content": {"title": "Test", "word_count": 800},
            "wordpress_post": {"url": "https://example.com/test", "id": 1},
        }

        # Call endpoint with None keywords
        result = await publish_content_batch(
            topics=["Topic 1"],
            keywords=None,  # Explicitly None
            orchestrator=mock_orchestrator,
        )

        # Should work and convert None to empty list
        assert result["success"] is True
        mock_orchestrator.execute_workflow.assert_called_once()
        call_kwargs = mock_orchestrator.execute_workflow.call_args[1]
        assert call_kwargs["keywords"] == []

    @pytest.mark.asyncio
    async def test_batch_publish_exception_handling(self, mock_orchestrator):
        """Should raise HTTPException on critical failure during telegram notification"""
        from api.v1.content import publish_content_batch

        # Setup mock - workflow succeeds but telegram fails
        mock_orchestrator.execute_workflow.return_value = {
            "success": True,
            "content": {"title": "Test", "word_count": 800},
            "wordpress_post": {"url": "https://example.com/test", "id": 1},
        }
        mock_orchestrator.telegram_service.send_notification = AsyncMock(
            side_effect=Exception("Telegram error")
        )

        # Call endpoint and expect exception
        with pytest.raises(HTTPException) as exc_info:
            await publish_content_batch(
                topics=["Topic 1"],
                orchestrator=mock_orchestrator,
            )

        assert exc_info.value.status_code == 500
        assert "Batch publishing failed" in str(exc_info.value.detail)


# ============================================================================
# TEST SCHEDULE ENDPOINT
# ============================================================================


class TestScheduleContentPublishing:
    """Test POST /content/schedule endpoint"""

    @pytest.mark.asyncio
    async def test_schedule_content(self, mock_orchestrator):
        """Should return scheduling not implemented message"""
        from api.v1.content import ScheduledPublishRequest, schedule_content_publishing

        # Create request
        request = ScheduledPublishRequest(
            topics=["Topic 1", "Topic 2"],
            schedule_days=["tuesday", "thursday"],
            schedule_time="12:00",
        )

        # Call endpoint
        result = await schedule_content_publishing(
            request=request,
            orchestrator=mock_orchestrator,
        )

        # Assertions
        assert result.success is True
        assert "not yet implemented" in result.message.lower()
        assert result.schedule_id is None
        assert result.next_execution is None

    @pytest.mark.asyncio
    async def test_schedule_content_exception(self, mock_orchestrator):
        """Should handle exceptions during scheduling"""
        from api.v1.content import ScheduledPublishRequest, schedule_content_publishing

        # This endpoint doesn't actually use orchestrator, so we'll test exception handling
        # by patching the logger to raise an exception
        with patch("api.v1.content.logger") as mock_logger:
            mock_logger.info.side_effect = Exception("Logger error")

            request = ScheduledPublishRequest(topics=["Topic 1"])

            with pytest.raises(HTTPException) as exc_info:
                await schedule_content_publishing(
                    request=request,
                    orchestrator=mock_orchestrator,
                )

            assert exc_info.value.status_code == 500
            assert "Scheduling failed" in str(exc_info.value.detail)


# ============================================================================
# TEST CATEGORIZE ENDPOINT
# ============================================================================


class TestCategorizeWordPressPosts:
    """Test POST /content/categorize endpoint"""

    @pytest.mark.asyncio
    async def test_categorize_all_posts(self, mock_env_vars):
        """Should categorize all posts successfully"""
        from api.v1.content import categorize_wordpress_posts

        # Mock categorization results
        mock_results = [
            Mock(
                post_id=123,
                post_title="Test Post 1",
                assigned_category_id=13,
                assigned_category_name="Content Creation",
                confidence=0.95,
                reasoning="Post is about content creation",
                error=None,
            ),
            Mock(
                post_id=456,
                post_title="Test Post 2",
                assigned_category_id=15,
                assigned_category_name="AI Tools",
                confidence=0.88,
                reasoning="Post discusses AI tools",
                error=None,
            ),
        ]

        with patch("api.v1.content.WordPressCategorizationService") as mock_service_cls:
            mock_service = Mock()
            mock_service.categorize_posts_batch = AsyncMock(return_value=mock_results)
            mock_service_cls.return_value = mock_service

            # Call endpoint without specific post IDs
            result = await categorize_wordpress_posts(use_ai=True)

            # Assertions
            assert result["success"] is True
            assert result["total"] == 2
            assert result["succeeded"] == 2
            assert result["failed"] == 0
            assert result["method"] == "AI"
            assert len(result["results"]) == 2

            # Verify first result
            assert result["results"][0]["post_id"] == 123
            assert result["results"][0]["assigned_category_id"] == 13
            assert result["results"][0]["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_categorize_specific_posts(self, mock_env_vars):
        """Should categorize only specific post IDs"""
        from api.v1.content import categorize_wordpress_posts

        # Mock categorization results
        mock_results = [
            Mock(
                post_id=123,
                post_title="Test Post 1",
                assigned_category_id=13,
                assigned_category_name="Content Creation",
                confidence=0.95,
                reasoning="Post is about content creation",
                error=None,
            ),
        ]

        with patch("api.v1.content.WordPressCategorizationService") as mock_service_cls:
            mock_service = Mock()
            mock_service.categorize_posts_batch = AsyncMock(return_value=mock_results)
            mock_service_cls.return_value = mock_service

            # Call endpoint with specific post IDs
            result = await categorize_wordpress_posts(post_ids=[123], use_ai=True)

            # Assertions
            assert result["success"] is True
            assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_categorize_with_failures(self, mock_env_vars):
        """Should handle categorization failures"""
        from api.v1.content import categorize_wordpress_posts

        # Mock categorization results with one error
        mock_results = [
            Mock(
                post_id=123,
                post_title="Test Post 1",
                assigned_category_id=13,
                assigned_category_name="Content Creation",
                confidence=0.95,
                reasoning="Success",
                error=None,
            ),
            Mock(
                post_id=456,
                post_title="Test Post 2",
                assigned_category_id=None,
                assigned_category_name=None,
                confidence=None,
                reasoning=None,
                error="Failed to categorize",
            ),
        ]

        with patch("api.v1.content.WordPressCategorizationService") as mock_service_cls:
            mock_service = Mock()
            mock_service.categorize_posts_batch = AsyncMock(return_value=mock_results)
            mock_service_cls.return_value = mock_service

            # Call endpoint
            result = await categorize_wordpress_posts(use_ai=True)

            # Assertions
            assert result["success"] is True
            assert result["total"] == 2
            assert result["succeeded"] == 1
            assert result["failed"] == 1

    @pytest.mark.asyncio
    async def test_categorize_keyword_matching(self, mock_env_vars):
        """Should use keyword matching when use_ai=False"""
        from api.v1.content import categorize_wordpress_posts

        # Mock categorization results
        mock_results = [
            Mock(
                post_id=123,
                post_title="Test Post",
                assigned_category_id=13,
                assigned_category_name="Content Creation",
                confidence=1.0,
                reasoning="Keyword match",
                error=None,
            ),
        ]

        with patch("api.v1.content.WordPressCategorizationService") as mock_service_cls:
            mock_service = Mock()
            mock_service.categorize_posts_batch = AsyncMock(return_value=mock_results)
            mock_service_cls.return_value = mock_service

            # Call endpoint with use_ai=False
            result = await categorize_wordpress_posts(use_ai=False)

            # Assertions
            assert result["success"] is True
            assert result["method"] == "keyword matching"

            # Verify categorize_posts_batch was called with use_ai=False
            call_kwargs = mock_service.categorize_posts_batch.call_args[1]
            assert call_kwargs["use_ai"] is False

    @pytest.mark.asyncio
    async def test_categorize_exception_handling(self, mock_env_vars):
        """Should handle exceptions during categorization"""
        from api.v1.content import categorize_wordpress_posts

        with patch("api.v1.content.WordPressCategorizationService") as mock_service_cls:
            mock_service = Mock()
            mock_service.categorize_posts_batch = AsyncMock(side_effect=Exception("Service error"))
            mock_service_cls.return_value = mock_service

            # Call endpoint and expect exception
            with pytest.raises(HTTPException) as exc_info:
                await categorize_wordpress_posts(use_ai=True)

            assert exc_info.value.status_code == 500
            assert "Categorization failed" in str(exc_info.value.detail)


# ============================================================================
# TEST CATEGORIES ENDPOINT
# ============================================================================


class TestGetAvailableCategories:
    """Test GET /content/categories endpoint"""

    @pytest.mark.asyncio
    async def test_get_categories_success(self):
        """Should return available categories"""
        from api.v1.content import get_available_categories

        # Mock category data
        mock_categories = [
            Mock(
                category_id=13,
                category_name="Content Creation",
                description="Articles about content creation",
                keywords=["content", "creation", "writing"],
            ),
            Mock(
                category_id=15,
                category_name="AI Tools",
                description="Articles about AI tools",
                keywords=["ai", "artificial intelligence", "tools"],
            ),
        ]

        with patch("api.v1.content.WordPressCategorizationService") as mock_service_cls:
            mock_service = Mock()
            mock_service.get_all_categories.return_value = mock_categories
            mock_service_cls.return_value = mock_service

            # Call endpoint
            result = await get_available_categories()

            # Assertions
            assert result["total"] == 2
            assert len(result["categories"]) == 2

            # Verify first category
            assert result["categories"][0]["id"] == 13
            assert result["categories"][0]["name"] == "Content Creation"
            assert result["categories"][0]["description"] == "Articles about content creation"
            assert result["categories"][0]["keywords"] == ["content", "creation", "writing"]


# ============================================================================
# TEST HEALTH CHECK ENDPOINT
# ============================================================================


class TestHealthCheck:
    """Test GET /content/health endpoint"""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Should return healthy status"""
        from api.v1.content import health_check

        result = await health_check()

        assert result["status"] == "healthy"
        assert result["service"] == "Content Publishing"
        assert "timestamp" in result

        # Verify timestamp is valid ISO format
        timestamp = result["timestamp"]
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


# ============================================================================
# TEST CONFIG ENDPOINT
# ============================================================================


class TestGetConfiguration:
    """Test GET /content/config endpoint"""

    @pytest.mark.asyncio
    async def test_config_all_configured(self):
        """Should show all services configured"""
        from api.v1.content import get_configuration

        with patch.dict(
            os.environ,
            {
                "ANTHROPIC_API_KEY": "test-key",
                "OPENAI_API_KEY": "test-key",
                "PEXELS_API_KEY": "test-key",
                "TELEGRAM_BOT_TOKEN": "test-token",
                "TELEGRAM_CHAT_ID": "test-id",
                "GOOGLE_SHEETS_ID": "test-sheets",
                "SKYY_ROSE_SITE_URL": "https://test.com",
            },
        ):
            result = await get_configuration()

            assert result["anthropic_configured"] is True
            assert result["openai_configured"] is True
            assert result["pexels_configured"] is True
            assert result["telegram_configured"] is True
            assert result["google_sheets_configured"] is True
            assert result["wordpress_credentials_configured"] is True

    @pytest.mark.asyncio
    async def test_config_partial_configured(self):
        """Should show partial configuration"""
        from api.v1.content import get_configuration

        with patch.dict(
            os.environ,
            {
                "ANTHROPIC_API_KEY": "test-key",
                "PEXELS_API_KEY": "test-key",
                # Missing other services
            },
            clear=True,
        ):
            result = await get_configuration()

            assert result["anthropic_configured"] is True
            assert result["pexels_configured"] is True
            assert result["openai_configured"] is False
            assert result["telegram_configured"] is False
            assert result["google_sheets_configured"] is False
            assert result["wordpress_credentials_configured"] is False

    @pytest.mark.asyncio
    async def test_config_none_configured(self):
        """Should show no services configured"""
        from api.v1.content import get_configuration

        with patch.dict(os.environ, {}, clear=True):
            result = await get_configuration()

            assert result["anthropic_configured"] is False
            assert result["openai_configured"] is False
            assert result["pexels_configured"] is False
            assert result["telegram_configured"] is False
            assert result["google_sheets_configured"] is False
            assert result["wordpress_credentials_configured"] is False


# ============================================================================
# TEST REQUEST/RESPONSE MODELS
# ============================================================================


class TestRequestResponseModels:
    """Test Pydantic request and response models"""

    def test_publish_content_request_defaults(self):
        """Should use default values correctly"""
        from api.v1.content import PublishContentRequest

        request = PublishContentRequest(topic="Test Topic")

        assert request.topic == "Test Topic"
        assert request.keywords == []
        assert request.tone == "professional"
        assert request.length == 800
        assert request.apply_random_delay is False
        assert request.min_delay_hours == 0
        assert request.max_delay_hours == 6
        assert request.publish_status == "publish"
        assert request.notify_telegram is True
        assert request.log_to_sheets is True

    def test_publish_content_request_validation(self):
        """Should validate request fields"""
        from pydantic import ValidationError

        from api.v1.content import PublishContentRequest

        # Test min_length validation
        with pytest.raises(ValidationError):
            PublishContentRequest(topic="")

        # Test max_length validation
        with pytest.raises(ValidationError):
            PublishContentRequest(topic="x" * 201)

        # Test length range validation
        with pytest.raises(ValidationError):
            PublishContentRequest(topic="Test", length=100)  # Below minimum 200

        with pytest.raises(ValidationError):
            PublishContentRequest(topic="Test", length=5000)  # Above maximum 3000

    def test_publish_content_response(self):
        """Should create response model correctly"""
        from api.v1.content import PublishContentResponse

        response = PublishContentResponse(
            success=True,
            message="Content published",
            title="Test Title",
            wordpress_url="https://example.com/test",
            wordpress_id=123,
            word_count=850,
            image_url="https://images.pexels.com/test.jpg",
            duration_seconds=5.2,
            delay_applied_seconds=120.0,
        )

        assert response.success is True
        assert response.message == "Content published"
        assert response.title == "Test Title"
        assert response.wordpress_id == 123

    def test_scheduled_publish_request_defaults(self):
        """Should use default values for scheduled publish"""
        from api.v1.content import ScheduledPublishRequest

        request = ScheduledPublishRequest(topics=["Topic 1"])

        assert request.topics == ["Topic 1"]
        assert request.keywords == []
        assert request.schedule_days == ["tuesday", "thursday", "sunday"]
        assert request.schedule_time == "12:00"
        assert request.timezone == "UTC"
        assert request.random_delay_enabled is True
        assert request.max_delay_hours == 6

    def test_scheduled_publish_request_validation(self):
        """Should validate scheduled publish request"""
        from pydantic import ValidationError

        from api.v1.content import ScheduledPublishRequest

        # Test min_items validation
        with pytest.raises(ValidationError):
            ScheduledPublishRequest(topics=[])  # Empty list not allowed
