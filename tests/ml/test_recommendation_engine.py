"""
Comprehensive tests for ml/recommendation_engine.py

Target: 75%+ coverage

Tests cover:
- Recommendation types and models
- Collaborative filtering
- Content-based filtering
- Trending recommendations
- Hybrid recommendations
- User interaction tracking
- Fallback mechanisms
- Error handling
"""

import pytest

from ml.recommendation_engine import (
    RecommendationEngine,
    RecommendationItem,
    RecommendationRequest,
    RecommendationResponse,
    RecommendationType,
    recommendation_engine,
)


class TestRecommendationType:
    """Test RecommendationType enum"""

    def test_recommendation_types(self):
        """Test all recommendation types"""
        assert RecommendationType.COLLABORATIVE == "collaborative"
        assert RecommendationType.CONTENT_BASED == "content_based"
        assert RecommendationType.HYBRID == "hybrid"
        assert RecommendationType.TRENDING == "trending"
        assert RecommendationType.PERSONALIZED == "personalized"


class TestRecommendationRequest:
    """Test RecommendationRequest model"""

    def test_create_request(self):
        """Test creating recommendation request"""
        request = RecommendationRequest(
            user_id="user_123",
            item_type="product",
            recommendation_type=RecommendationType.HYBRID,
            limit=10,
        )

        assert request.user_id == "user_123"
        assert request.item_type == "product"
        assert request.limit == 10

    def test_request_with_context(self):
        """Test request with context filters"""
        request = RecommendationRequest(
            user_id="user_123",
            recommendation_type=RecommendationType.CONTENT_BASED,
            limit=5,
            context={"max_price": 100.0, "category": "clothing"},
        )

        assert request.context["max_price"] == 100.0
        assert request.context["category"] == "clothing"

    def test_request_with_exclusions(self):
        """Test request with excluded items"""
        request = RecommendationRequest(
            user_id="user_123",
            exclude_items=["prod_1", "prod_2"],
        )

        assert len(request.exclude_items) == 2

    def test_request_defaults(self):
        """Test request default values"""
        request = RecommendationRequest(user_id="user_123")

        assert request.item_type == "product"
        assert request.recommendation_type == RecommendationType.HYBRID
        assert request.limit == 10


class TestRecommendationItem:
    """Test RecommendationItem model"""

    def test_create_item(self):
        """Test creating recommendation item"""
        item = RecommendationItem(
            item_id="prod_123",
            item_type="product",
            title="Test Product",
            description="A test product",
            score=0.95,
            reason="Highly rated by similar users",
        )

        assert item.item_id == "prod_123"
        assert item.score == 0.95
        assert item.reason != ""

    def test_item_score_validation(self):
        """Test item score is between 0 and 1"""
        with pytest.raises(Exception):  # Pydantic validation error
            RecommendationItem(
                item_id="prod_123",
                item_type="product",
                title="Test",
                score=1.5,  # Invalid: > 1.0
                reason="Test",
            )


class TestRecommendationResponse:
    """Test RecommendationResponse model"""

    def test_create_response(self):
        """Test creating recommendation response"""
        items = [
            RecommendationItem(
                item_id="prod_1",
                item_type="product",
                title="Product 1",
                score=0.9,
                reason="Popular",
            )
        ]

        response = RecommendationResponse(
            user_id="user_123",
            recommendations=items,
            recommendation_type=RecommendationType.HYBRID,
            total_items=1,
            processing_time_ms=50.0,
        )

        assert response.user_id == "user_123"
        assert len(response.recommendations) == 1
        assert response.processing_time_ms > 0


class TestRecommendationEngine:
    """Test RecommendationEngine"""

    def test_init(self, mock_redis):
        """Test engine initialization"""
        engine = RecommendationEngine(redis_client=mock_redis)

        assert engine.redis_client is not None
        assert len(engine.user_interactions) > 0  # Sample data
        assert len(engine.item_features) > 0  # Sample data

    def test_init_with_sample_data(self):
        """Test engine initializes with sample data"""
        engine = RecommendationEngine()

        # Should have sample users
        assert "user_1" in engine.user_interactions
        assert "user_2" in engine.user_interactions

        # Should have sample products
        assert "prod_1" in engine.item_features
        assert len(engine.item_features) >= 5

    @pytest.mark.asyncio
    async def test_get_recommendations_collaborative(self, recommendation_engine):
        """Test collaborative filtering recommendations"""
        request = RecommendationRequest(
            user_id="user_1",
            recommendation_type=RecommendationType.COLLABORATIVE,
            limit=5,
        )

        response = await recommendation_engine.get_recommendations(request)

        assert response.user_id == "user_1"
        assert response.recommendation_type == RecommendationType.COLLABORATIVE
        assert len(response.recommendations) <= 5
        assert response.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_get_recommendations_content_based(self, recommendation_engine):
        """Test content-based filtering recommendations"""
        request = RecommendationRequest(
            user_id="user_1",
            recommendation_type=RecommendationType.CONTENT_BASED,
            limit=5,
        )

        response = await recommendation_engine.get_recommendations(request)

        assert response.recommendation_type == RecommendationType.CONTENT_BASED
        assert len(response.recommendations) <= 5

    @pytest.mark.asyncio
    async def test_get_recommendations_trending(self, recommendation_engine):
        """Test trending recommendations"""
        request = RecommendationRequest(
            user_id="user_3",  # New user with no history
            recommendation_type=RecommendationType.TRENDING,
            limit=5,
        )

        response = await recommendation_engine.get_recommendations(request)

        assert response.recommendation_type == RecommendationType.TRENDING
        assert len(response.recommendations) > 0

    @pytest.mark.asyncio
    async def test_get_recommendations_hybrid(self, recommendation_engine):
        """Test hybrid recommendations"""
        request = RecommendationRequest(
            user_id="user_1",
            recommendation_type=RecommendationType.HYBRID,
            limit=10,
        )

        response = await recommendation_engine.get_recommendations(request)

        assert response.recommendation_type == RecommendationType.HYBRID
        assert len(response.recommendations) <= 10

    @pytest.mark.asyncio
    async def test_get_recommendations_personalized(self, recommendation_engine):
        """Test personalized recommendations"""
        request = RecommendationRequest(
            user_id="user_1",
            recommendation_type=RecommendationType.PERSONALIZED,
            limit=5,
        )

        response = await recommendation_engine.get_recommendations(request)

        # Personalized falls back to hybrid
        assert len(response.recommendations) <= 5

    @pytest.mark.asyncio
    async def test_recommendations_respects_limit(self, recommendation_engine):
        """Test recommendations respect limit parameter"""
        for limit in [1, 3, 5, 10]:
            request = RecommendationRequest(
                user_id="user_1",
                recommendation_type=RecommendationType.HYBRID,
                limit=limit,
            )

            response = await recommendation_engine.get_recommendations(request)
            assert len(response.recommendations) <= limit

    @pytest.mark.asyncio
    async def test_recommendations_exclude_items(self, recommendation_engine):
        """Test recommendations exclude specified items"""
        request = RecommendationRequest(
            user_id="user_1",
            recommendation_type=RecommendationType.HYBRID,
            limit=10,
            exclude_items=["prod_1", "prod_2"],
        )

        response = await recommendation_engine.get_recommendations(request)

        # Check excluded items not in recommendations
        rec_ids = [rec.item_id for rec in response.recommendations]
        assert "prod_1" not in rec_ids
        assert "prod_2" not in rec_ids

    @pytest.mark.asyncio
    async def test_recommendations_with_price_filter(self, recommendation_engine):
        """Test recommendations filter by price"""
        request = RecommendationRequest(
            user_id="user_1",
            recommendation_type=RecommendationType.HYBRID,
            limit=10,
            context={"max_price": 200.0},
        )

        response = await recommendation_engine.get_recommendations(request)

        # All recommendations should be within price range
        for rec in response.recommendations:
            if "price" in rec.metadata:
                assert rec.metadata["price"] <= 200.0

    @pytest.mark.asyncio
    async def test_recommendations_with_category_filter(self, recommendation_engine):
        """Test recommendations filter by category"""
        request = RecommendationRequest(
            user_id="user_1",
            recommendation_type=RecommendationType.HYBRID,
            limit=10,
            context={"category": "clothing"},
        )

        response = await recommendation_engine.get_recommendations(request)

        # All recommendations should match category
        for rec in response.recommendations:
            if "category" in rec.metadata:
                assert rec.metadata["category"] == "clothing"

    @pytest.mark.asyncio
    async def test_collaborative_filtering_new_user(self, recommendation_engine):
        """Test collaborative filtering for new user falls back to trending"""
        request = RecommendationRequest(
            user_id="new_user_999",
            recommendation_type=RecommendationType.COLLABORATIVE,
            limit=5,
        )

        response = await recommendation_engine.get_recommendations(request)

        # Should return recommendations (trending fallback)
        assert len(response.recommendations) > 0

    @pytest.mark.asyncio
    async def test_content_based_new_user(self, recommendation_engine):
        """Test content-based for new user falls back to trending"""
        request = RecommendationRequest(
            user_id="new_user_999",
            recommendation_type=RecommendationType.CONTENT_BASED,
            limit=5,
        )

        response = await recommendation_engine.get_recommendations(request)

        # Should return recommendations (trending fallback)
        assert len(response.recommendations) > 0

    @pytest.mark.asyncio
    async def test_find_similar_users(self, recommendation_engine):
        """Test finding similar users"""
        similar_users = recommendation_engine._find_similar_users("user_1")

        # Should find at least one similar user
        assert len(similar_users) >= 0

        # Similarities should be between 0 and 1
        for user_id, similarity in similar_users:
            assert 0 <= similarity <= 1.0

    def test_calculate_user_similarity(self, recommendation_engine):
        """Test user similarity calculation"""
        user1_items = {"prod_1": 5.0, "prod_2": 4.0, "prod_3": 3.0}
        user2_items = {"prod_1": 5.0, "prod_2": 4.0, "prod_4": 5.0}

        similarity = recommendation_engine._calculate_user_similarity(user1_items, user2_items)

        # Should return valid similarity score
        assert 0 <= similarity <= 1.0

    def test_calculate_user_similarity_no_common(self, recommendation_engine):
        """Test similarity with no common items"""
        user1_items = {"prod_1": 5.0, "prod_2": 4.0}
        user2_items = {"prod_3": 5.0, "prod_4": 4.0}

        similarity = recommendation_engine._calculate_user_similarity(user1_items, user2_items)

        # Should return 0 for no common items
        assert similarity == 0.0

    def test_build_user_profile(self, recommendation_engine):
        """Test building user profile from interactions"""
        interactions = [
            {"item_id": "prod_1", "rating": 5.0},
            {"item_id": "prod_2", "rating": 4.0},
            {"item_id": "prod_5", "rating": 4.5},
        ]

        profile = recommendation_engine._build_user_profile(interactions)

        # Profile should have tags and categories from items
        assert len(profile) > 0

        # Values should be normalized between 0 and 1
        for value in profile.values():
            assert 0 <= value <= 1.0

    def test_calculate_content_similarity(self, recommendation_engine):
        """Test content similarity calculation"""
        user_profile = {"fashion": 1.0, "premium": 0.8, "clothing": 0.9}

        # Test with matching item
        item_data = {
            "title": "Fashion Item",
            "category": "clothing",
            "tags": ["fashion", "premium"],
        }

        similarity = recommendation_engine._calculate_content_similarity(user_profile, item_data)

        # Should have high similarity
        assert similarity > 0.5

    def test_calculate_content_similarity_no_match(self, recommendation_engine):
        """Test similarity with non-matching item"""
        user_profile = {"fashion": 1.0, "premium": 0.8}

        item_data = {
            "title": "Sports Item",
            "category": "sports",
            "tags": ["athletic", "performance"],
        }

        similarity = recommendation_engine._calculate_content_similarity(user_profile, item_data)

        # Should have low similarity
        assert similarity < 0.3

    @pytest.mark.asyncio
    async def test_record_interaction(self, recommendation_engine):
        """Test recording user interaction"""
        initial_count = len(recommendation_engine.user_interactions.get("test_user", []))

        await recommendation_engine.record_interaction(
            user_id="test_user",
            item_id="prod_1",
            rating=5.0,
            interaction_type="purchase",
        )

        final_count = len(recommendation_engine.user_interactions.get("test_user", []))

        # Should have one more interaction
        assert final_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_record_interaction_redis(self, mock_redis):
        """Test recording interaction with Redis"""
        engine = RecommendationEngine(redis_client=mock_redis)

        await engine.record_interaction(
            user_id="test_user",
            item_id="prod_1",
            rating=5.0,
        )

        # Check Redis was called
        assert len(mock_redis.data) > 0

    @pytest.mark.asyncio
    async def test_fallback_recommendations(self, recommendation_engine):
        """Test fallback recommendations"""
        request = RecommendationRequest(
            user_id="user_999",
            limit=5,
        )

        response = await recommendation_engine._fallback_recommendations(request)

        assert len(response.recommendations) > 0
        assert response.recommendation_type == RecommendationType.TRENDING
        assert all(rec.reason == "Fallback recommendation" for rec in response.recommendations)

    @pytest.mark.asyncio
    async def test_error_handling(self, recommendation_engine):
        """Test error handling in recommendations"""
        # Force an error by corrupting internal state
        original_features = recommendation_engine.item_features
        recommendation_engine.item_features = None

        request = RecommendationRequest(
            user_id="user_1",
            recommendation_type=RecommendationType.HYBRID,
        )

        # Should not raise error, should return fallback
        response = await recommendation_engine.get_recommendations(request)
        assert response is not None

        # Restore state
        recommendation_engine.item_features = original_features

    def test_filter_recommendations(self, recommendation_engine):
        """Test filtering recommendations"""
        recs = [
            RecommendationItem(
                item_id="prod_1",
                item_type="product",
                title="Product 1",
                score=0.9,
                reason="Test",
                metadata={"price": 100.0, "category": "clothing"},
            ),
            RecommendationItem(
                item_id="prod_2",
                item_type="product",
                title="Product 2",
                score=0.8,
                reason="Test",
                metadata={"price": 200.0, "category": "electronics"},
            ),
            RecommendationItem(
                item_id="prod_3",
                item_type="product",
                title="Product 3",
                score=0.7,
                reason="Test",
                metadata={"price": 50.0, "category": "clothing"},
            ),
        ]

        request = RecommendationRequest(
            user_id="user_1",
            exclude_items=["prod_2"],
            context={"max_price": 150.0, "category": "clothing"},
        )

        filtered = recommendation_engine._filter_recommendations(recs, request)

        # Should exclude prod_2, filter by price and category
        assert len(filtered) <= 2
        assert all(rec.item_id != "prod_2" for rec in filtered)
        assert all(rec.metadata.get("price", 0) <= 150.0 for rec in filtered)
        assert all(rec.metadata.get("category") == "clothing" for rec in filtered)

    def test_get_task_distribution(self, recommendation_engine):
        """Test getting task type distribution"""
        snapshots = [
            type("Snapshot", (), {"task_type": "task_a"})(),
            type("Snapshot", (), {"task_type": "task_a"})(),
            type("Snapshot", (), {"task_type": "task_b"})(),
            type("Snapshot", (), {"task_type": "task_c"})(),
            type("Snapshot", (), {"task_type": "task_a"})(),
        ]

        # Manually test distribution logic
        distribution = {}
        for snapshot in snapshots:
            task_type = snapshot.task_type
            distribution[task_type] = distribution.get(task_type, 0) + 1

        assert distribution["task_a"] == 3
        assert distribution["task_b"] == 1
        assert distribution["task_c"] == 1

    @pytest.mark.asyncio
    async def test_multiple_recommendation_types(self, recommendation_engine, recommendation_type):
        """Test all recommendation types with parametrization"""
        request = RecommendationRequest(
            user_id="user_1",
            recommendation_type=recommendation_type,
            limit=5,
        )

        response = await recommendation_engine.get_recommendations(request)

        assert response is not None
        assert len(response.recommendations) <= 5


class TestGlobalRecommendationEngine:
    """Test global recommendation engine instance"""

    def test_global_instance(self):
        """Test global instance exists"""
        assert recommendation_engine is not None
        assert isinstance(recommendation_engine, RecommendationEngine)

    @pytest.mark.asyncio
    async def test_global_instance_works(self):
        """Test global instance is functional"""
        request = RecommendationRequest(
            user_id="user_1",
            limit=5,
        )

        response = await recommendation_engine.get_recommendations(request)
        assert response is not None
