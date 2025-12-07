"""
WordPress Categorization Tests

WHY: Validate AI-powered post categorization
HOW: Test categorization with mock AI responses
IMPACT: Ensures correct category assignment

pytest tests/test_wordpress_categorization.py -v
"""

from unittest.mock import MagicMock

import pytest

from services.wordpress_categorization import (
    CategorizationResult,
    CategoryMapping,
    WordPressCategorizationService,
)


@pytest.fixture
def categorization_service():
    """Create categorization service without AI clients"""
    return WordPressCategorizationService()


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client"""
    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = MagicMock()
    return client


@pytest.mark.asyncio
async def test_keyword_matching_categorization(categorization_service):
    """Test keyword-based categorization fallback"""
    result = categorization_service.categorize_with_keywords("How to Use AI Tools for Content Marketing")

    assert result["category_id"] in [13, 14, 15, 17, 18, 19]
    assert result["confidence"] > 0
    assert "reasoning" in result


@pytest.mark.asyncio
async def test_categorize_ai_tools_post(categorization_service):
    """Test categorization of AI tools post"""
    result = categorization_service.categorize_with_keywords("Best AI Tools for Automating Your Workflow")

    # Should match AI Tools (15) or Automation (17)
    assert result["category_id"] in [15, 17]
    assert "ai" in result["reasoning"].lower() or "automation" in result["reasoning"].lower()


@pytest.mark.asyncio
async def test_categorize_content_creation_post(categorization_service):
    """Test categorization of content creation post"""
    result = categorization_service.categorize_with_keywords("How to Write Engaging Blog Posts")

    # Should match Content Creation (13)
    assert result["category_id"] == 13
    assert result["confidence"] > 0


@pytest.mark.asyncio
async def test_categorize_marketing_post(categorization_service):
    """Test categorization of marketing post"""
    result = categorization_service.categorize_with_keywords("SEO Strategies for Growing Your Business")

    # Should match Digital Marketing (14)
    assert result["category_id"] == 14


@pytest.mark.asyncio
async def test_categorize_no_keywords_match(categorization_service):
    """Test categorization when no keywords match (uses default)"""
    result = categorization_service.categorize_with_keywords("Random Article About Nothing Specific")

    # Should use default category
    assert result["category_id"] == categorization_service.default_category_id
    assert result["confidence"] < 0.5


@pytest.mark.asyncio
async def test_categorize_single_post(categorization_service):
    """Test categorizing a single post"""
    result = await categorization_service.categorize_post(
        post_id=123, post_title="AI-Powered Marketing Automation Guide", use_ai=False  # Use keyword matching
    )

    assert isinstance(result, CategorizationResult)
    assert result.post_id == 123
    assert result.post_title == "AI-Powered Marketing Automation Guide"
    assert result.assigned_category_id in [13, 14, 15, 17, 18, 19]
    assert result.assigned_category_name is not None
    assert result.confidence >= 0


@pytest.mark.asyncio
async def test_categorize_batch_posts(categorization_service):
    """Test batch categorization"""
    posts = [
        {"id": 1, "title": "How to Create Content"},
        {"id": 2, "title": "AI Tools for Marketing"},
        {"id": 3, "title": "Productivity Apps Review"},
    ]

    results = await categorization_service.categorize_posts_batch(posts, use_ai=False)

    assert len(results) == 3
    assert all(isinstance(r, CategorizationResult) for r in results)
    assert all(r.post_id in [1, 2, 3] for r in results)
    assert all(r.error is None for r in results)


@pytest.mark.asyncio
async def test_categorize_batch_with_missing_data(categorization_service):
    """Test batch categorization skips posts with missing data"""
    posts = [
        {"id": 1, "title": "Valid Post"},
        {"id": None, "title": "Missing ID"},  # Should skip
        {"id": 3, "title": ""},  # Should skip
        {"title": "Missing ID"},  # Should skip
    ]

    results = await categorization_service.categorize_posts_batch(posts, use_ai=False)

    # Only first post should be processed
    assert len(results) == 1
    assert results[0].post_id == 1


@pytest.mark.asyncio
async def test_get_category_by_id(categorization_service):
    """Test getting category by ID"""
    category = categorization_service.get_category_by_id(13)

    assert category is not None
    assert category.category_id == 13
    assert category.category_name == "Content Creation"


@pytest.mark.asyncio
async def test_get_invalid_category_id(categorization_service):
    """Test getting non-existent category returns None"""
    category = categorization_service.get_category_by_id(999)
    assert category is None


@pytest.mark.asyncio
async def test_get_all_categories(categorization_service):
    """Test getting all available categories"""
    categories = categorization_service.get_all_categories()

    assert len(categories) == 6
    assert all(isinstance(c, CategoryMapping) for c in categories)
    assert all(c.category_id in [13, 14, 15, 17, 18, 19] for c in categories)


@pytest.mark.asyncio
async def test_categorize_with_anthropic_mock():
    """Test AI categorization with mocked Anthropic response"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(text='{"category_id": 15, "confidence": 0.95, "reasoning": "AI tools mentioned"}')
    ]
    mock_client.messages.create.return_value = mock_response

    service = WordPressCategorizationService()
    service.anthropic_client = mock_client

    result = await service.categorize_with_anthropic("Best AI Tools for 2025")

    assert result["category_id"] == 15
    assert result["confidence"] == 0.95
    assert "AI tools" in result["reasoning"]


@pytest.mark.asyncio
async def test_categorize_with_invalid_anthropic_response():
    """Test handling of invalid AI response"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"category_id": 999, "confidence": 0.95, "reasoning": "Invalid"}')]
    mock_client.messages.create.return_value = mock_response

    service = WordPressCategorizationService(default_category_id=13)
    service.anthropic_client = mock_client

    result = await service.categorize_with_anthropic("Test Post")

    # Should fall back to default category when invalid ID returned
    assert result["category_id"] == 13
    assert result["confidence"] == 0.5  # Lower confidence for fallback


@pytest.mark.asyncio
async def test_categorize_with_anthropic_error():
    """Test handling of Anthropic API errors"""
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("API Error")

    service = WordPressCategorizationService(default_category_id=13)
    service.anthropic_client = mock_client

    result = await service.categorize_with_anthropic("Test Post")

    # Should return default category on error
    assert result["category_id"] == 13
    assert result["confidence"] == 0.0
    assert "Error" in result["reasoning"]


@pytest.mark.asyncio
async def test_custom_categories():
    """Test service with custom category mappings"""
    custom_categories = [
        CategoryMapping(
            category_id=100,
            category_name="Custom Category",
            description="Custom category for testing",
            keywords=["custom", "test"],
        )
    ]

    service = WordPressCategorizationService(categories=custom_categories, default_category_id=100)

    result = service.categorize_with_keywords("Custom test post")

    assert result["category_id"] == 100
    assert "custom" in result["reasoning"].lower()


@pytest.mark.asyncio
async def test_categorize_post_with_rendered_title():
    """Test categorization with WordPress rendered title format"""
    service = WordPressCategorizationService()

    result = await service.categorize_post(
        post_id=456, post_title="How to Automate Your Workflow with n8n", use_ai=False
    )

    assert result.post_id == 456
    assert result.assigned_category_id == 17  # Automation category
    assert result.assigned_category_name == "Automation & Integration"


@pytest.mark.asyncio
async def test_multiple_keyword_matches():
    """Test post matching multiple categories chooses best one"""
    service = WordPressCategorizationService()

    # Title has both "AI" and "marketing" keywords
    result = service.categorize_with_keywords("AI-Powered Digital Marketing Strategies")

    # Should pick the category with more keyword matches
    assert result["category_id"] in [14, 15]  # Marketing or AI Tools
    assert result["confidence"] > 0.3
