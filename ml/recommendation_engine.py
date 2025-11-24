from datetime import datetime
from enum import Enum
import json
import logging
import random
import time
from typing import Any

from pydantic import BaseModel, Field


"""
DevSkyy ML Recommendation Engine v1.0.0

Lightweight recommendation engine optimized for Vercel serverless deployment.
Provides collaborative filtering, content-based recommendations, and hybrid approaches.

Author: DevSkyy Team
Version: 1.0.0
Python: >=3.11
"""

logger = logging.getLogger(__name__)

# ============================================================================
# RECOMMENDATION MODELS
# ============================================================================


class RecommendationType(str, Enum):
    """Types of recommendations."""

    COLLABORATIVE = "collaborative"
    CONTENT_BASED = "content_based"
    HYBRID = "hybrid"
    TRENDING = "trending"
    PERSONALIZED = "personalized"


class RecommendationRequest(BaseModel):
    """Recommendation request model."""

    user_id: str
    item_type: str = "product"
    recommendation_type: RecommendationType = RecommendationType.HYBRID
    limit: int = Field(default=10, ge=1, le=100)
    exclude_items: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)


class RecommendationItem(BaseModel):
    """Recommended item model."""

    item_id: str
    item_type: str
    title: str
    description: str | None = None
    score: float = Field(ge=0.0, le=1.0)
    reason: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RecommendationResponse(BaseModel):
    """Recommendation response model."""

    user_id: str
    recommendations: list[RecommendationItem]
    recommendation_type: RecommendationType
    generated_at: datetime = Field(default_factory=datetime.now)
    total_items: int
    processing_time_ms: float


# ============================================================================
# RECOMMENDATION ENGINE
# ============================================================================


class RecommendationEngine:
    """
    Lightweight recommendation engine for serverless deployment.

    Features:
    - Collaborative filtering
    - Content-based recommendations
    - Hybrid recommendations
    - Real-time personalization
    - Optimized for cold starts
    """

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.user_interactions: dict[str, list[dict]] = {}
        self.item_features: dict[str, dict] = {}
        self.similarity_cache: dict[str, dict] = {}

        # Initialize with sample data for demo
        self._initialize_sample_data()

    def _initialize_sample_data(self):
        """Initialize with sample data for demonstration."""
        # Sample user interactions
        self.user_interactions = {
            "user_1": [
                {"item_id": "prod_1", "rating": 5.0, "timestamp": time.time()},
                {"item_id": "prod_2", "rating": 4.0, "timestamp": time.time()},
                {"item_id": "prod_5", "rating": 4.5, "timestamp": time.time()},
            ],
            "user_2": [
                {"item_id": "prod_1", "rating": 4.0, "timestamp": time.time()},
                {"item_id": "prod_3", "rating": 5.0, "timestamp": time.time()},
                {"item_id": "prod_4", "rating": 3.5, "timestamp": time.time()},
            ],
        }

        # Sample item features
        self.item_features = {
            "prod_1": {
                "title": "Premium Fashion Jacket",
                "category": "clothing",
                "brand": "LuxuryBrand",
                "price": 299.99,
                "tags": ["fashion", "premium", "jacket", "winter"],
            },
            "prod_2": {
                "title": "Designer Handbag",
                "category": "accessories",
                "brand": "DesignerBrand",
                "price": 599.99,
                "tags": ["handbag", "designer", "luxury", "leather"],
            },
            "prod_3": {
                "title": "Casual Sneakers",
                "category": "footwear",
                "brand": "SportsBrand",
                "price": 129.99,
                "tags": ["sneakers", "casual", "comfortable", "sports"],
            },
            "prod_4": {
                "title": "Elegant Watch",
                "category": "accessories",
                "brand": "WatchBrand",
                "price": 899.99,
                "tags": ["watch", "elegant", "luxury", "timepiece"],
            },
            "prod_5": {
                "title": "Summer Dress",
                "category": "clothing",
                "brand": "FashionBrand",
                "price": 149.99,
                "tags": ["dress", "summer", "fashion", "elegant"],
            },
        }

    async def get_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """
        Get recommendations for a user.

        Args:
            request: Recommendation request

        Returns:
            Recommendation response with items and metadata
        """
        start_time = time.time()

        try:
            if request.recommendation_type == RecommendationType.COLLABORATIVE:
                recommendations = await self._collaborative_filtering(request)
            elif request.recommendation_type == RecommendationType.CONTENT_BASED:
                recommendations = await self._content_based_filtering(request)
            elif request.recommendation_type == RecommendationType.TRENDING:
                recommendations = await self._trending_recommendations(request)
            else:  # HYBRID or PERSONALIZED
                recommendations = await self._hybrid_recommendations(request)

            # Apply filters and limits
            recommendations = self._filter_recommendations(recommendations, request)
            recommendations = recommendations[: request.limit]

            processing_time = (time.time() - start_time) * 1000

            return RecommendationResponse(
                user_id=request.user_id,
                recommendations=recommendations,
                recommendation_type=request.recommendation_type,
                total_items=len(recommendations),
                processing_time_ms=processing_time,
            )

        except Exception as e:
            logger.error(f"❌ Recommendation generation failed: {e}")
            # Return fallback recommendations
            return await self._fallback_recommendations(request)

    async def _collaborative_filtering(self, request: RecommendationRequest) -> list[RecommendationItem]:
        """Generate collaborative filtering recommendations."""
        recommendations = []

        try:
            user_interactions = self.user_interactions.get(request.user_id, [])
            if not user_interactions:
                return await self._trending_recommendations(request)

            # Find similar users
            similar_users = self._find_similar_users(request.user_id)

            # Get items liked by similar users
            recommended_items = {}
            for similar_user, similarity_score in similar_users:
                for interaction in self.user_interactions.get(similar_user, []):
                    item_id = interaction["item_id"]
                    rating = interaction["rating"]

                    # Skip items user has already interacted with
                    user_item_ids = [i["item_id"] for i in user_interactions]
                    if item_id in user_item_ids:
                        continue

                    if item_id not in recommended_items:
                        recommended_items[item_id] = 0

                    recommended_items[item_id] += rating * similarity_score

            # Convert to recommendation items
            for item_id, score in sorted(recommended_items.items(), key=lambda x: x[1], reverse=True):
                if item_id in self.item_features:
                    item_data = self.item_features[item_id]
                    recommendations.append(
                        RecommendationItem(
                            item_id=item_id,
                            item_type=request.item_type,
                            title=item_data.get("title", f"Item {item_id}"),
                            description=item_data.get("description"),
                            score=min(score / 5.0, 1.0),  # Normalize to 0-1
                            reason="Users with similar preferences also liked this",
                            metadata=item_data,
                        )
                    )

        except Exception as e:
            logger.error(f"❌ Collaborative filtering failed: {e}")

        return recommendations

    async def _content_based_filtering(self, request: RecommendationRequest) -> list[RecommendationItem]:
        """Generate content-based recommendations."""
        recommendations = []

        try:
            user_interactions = self.user_interactions.get(request.user_id, [])
            if not user_interactions:
                return await self._trending_recommendations(request)

            # Build user profile from interactions
            user_profile = self._build_user_profile(user_interactions)

            # Score items based on similarity to user profile
            item_scores = {}
            for item_id, item_data in self.item_features.items():
                # Skip items user has already interacted with
                user_item_ids = [i["item_id"] for i in user_interactions]
                if item_id in user_item_ids:
                    continue

                similarity_score = self._calculate_content_similarity(user_profile, item_data)
                item_scores[item_id] = similarity_score

            # Convert to recommendation items
            for item_id, score in sorted(item_scores.items(), key=lambda x: x[1], reverse=True):
                item_data = self.item_features[item_id]
                recommendations.append(
                    RecommendationItem(
                        item_id=item_id,
                        item_type=request.item_type,
                        title=item_data.get("title", f"Item {item_id}"),
                        description=item_data.get("description"),
                        score=score,
                        reason="Based on your preferences and past interactions",
                        metadata=item_data,
                    )
                )

        except Exception as e:
            logger.error(f"❌ Content-based filtering failed: {e}")

        return recommendations

    async def _trending_recommendations(self, request: RecommendationRequest) -> list[RecommendationItem]:
        """Generate trending recommendations."""
        recommendations = []

        try:
            # Calculate trending items based on recent interactions
            item_popularity = {}
            recent_cutoff = time.time() - (7 * 24 * 3600)  # Last 7 days

            for interactions in self.user_interactions.values():
                for interaction in interactions:
                    if interaction["timestamp"] > recent_cutoff:
                        item_id = interaction["item_id"]
                        rating = interaction["rating"]

                        if item_id not in item_popularity:
                            item_popularity[item_id] = {"total_rating": 0, "count": 0}

                        item_popularity[item_id]["total_rating"] += rating
                        item_popularity[item_id]["count"] += 1

            # Calculate average ratings and sort by popularity
            trending_items = []
            for item_id, stats in item_popularity.items():
                avg_rating = stats["total_rating"] / stats["count"]
                popularity_score = avg_rating * (stats["count"] ** 0.5)  # Weight by number of ratings
                trending_items.append((item_id, popularity_score))

            trending_items.sort(key=lambda x: x[1], reverse=True)

            # Convert to recommendation items
            for item_id, score in trending_items:
                if item_id in self.item_features:
                    item_data = self.item_features[item_id]
                    recommendations.append(
                        RecommendationItem(
                            item_id=item_id,
                            item_type=request.item_type,
                            title=item_data.get("title", f"Item {item_id}"),
                            description=item_data.get("description"),
                            score=min(score / 10.0, 1.0),  # Normalize
                            reason="Trending now - popular with other users",
                            metadata=item_data,
                        )
                    )

        except Exception as e:
            logger.error(f"❌ Trending recommendations failed: {e}")

        return recommendations

    async def _hybrid_recommendations(self, request: RecommendationRequest) -> list[RecommendationItem]:
        """Generate hybrid recommendations combining multiple approaches."""
        try:
            # Get recommendations from different approaches
            collaborative_recs = await self._collaborative_filtering(request)
            content_recs = await self._content_based_filtering(request)
            trending_recs = await self._trending_recommendations(request)

            # Combine and weight recommendations
            combined_scores = {}

            # Weight collaborative filtering (40%)
            for rec in collaborative_recs:
                combined_scores[rec.item_id] = rec.score * 0.4

            # Weight content-based (40%)
            for rec in content_recs:
                if rec.item_id in combined_scores:
                    combined_scores[rec.item_id] += rec.score * 0.4
                else:
                    combined_scores[rec.item_id] = rec.score * 0.4

            # Weight trending (20%)
            for rec in trending_recs:
                if rec.item_id in combined_scores:
                    combined_scores[rec.item_id] += rec.score * 0.2
                else:
                    combined_scores[rec.item_id] = rec.score * 0.2

            # Create final recommendations
            recommendations = []
            for item_id, score in sorted(combined_scores.items(), key=lambda x: x[1], reverse=True):
                if item_id in self.item_features:
                    item_data = self.item_features[item_id]
                    recommendations.append(
                        RecommendationItem(
                            item_id=item_id,
                            item_type=request.item_type,
                            title=item_data.get("title", f"Item {item_id}"),
                            description=item_data.get("description"),
                            score=min(score, 1.0),
                            reason="Personalized recommendation based on multiple factors",
                            metadata=item_data,
                        )
                    )

            return recommendations

        except Exception as e:
            logger.error(f"❌ Hybrid recommendations failed: {e}")
            return await self._fallback_recommendations(request)

    def _find_similar_users(self, user_id: str) -> list[tuple[str, float]]:
        """Find users similar to the given user."""
        similar_users = []
        user_interactions = self.user_interactions.get(user_id, [])

        if not user_interactions:
            return similar_users

        user_items = {i["item_id"]: i["rating"] for i in user_interactions}

        for other_user_id, other_interactions in self.user_interactions.items():
            if other_user_id == user_id:
                continue

            other_items = {i["item_id"]: i["rating"] for i in other_interactions}

            # Calculate similarity (simple cosine similarity)
            similarity = self._calculate_user_similarity(user_items, other_items)
            if similarity > 0.1:  # Minimum similarity threshold
                similar_users.append((other_user_id, similarity))

        return sorted(similar_users, key=lambda x: x[1], reverse=True)[:5]  # Top 5 similar users

    def _calculate_user_similarity(self, user1_items: dict, user2_items: dict) -> float:
        """Calculate similarity between two users based on their item ratings."""
        common_items = set(user1_items.keys()) & set(user2_items.keys())

        if not common_items:
            return 0.0

        # Simple correlation-based similarity
        sum1 = sum(user1_items[item] for item in common_items)
        sum2 = sum(user2_items[item] for item in common_items)

        sum1_sq = sum(user1_items[item] ** 2 for item in common_items)
        sum2_sq = sum(user2_items[item] ** 2 for item in common_items)

        sum_products = sum(user1_items[item] * user2_items[item] for item in common_items)

        n = len(common_items)
        numerator = sum_products - (sum1 * sum2 / n)
        denominator = ((sum1_sq - sum1**2 / n) * (sum2_sq - sum2**2 / n)) ** 0.5

        if denominator == 0:
            return 0.0

        return max(0.0, numerator / denominator)

    def _build_user_profile(self, user_interactions: list[dict]) -> dict[str, float]:
        """Build user profile from interactions."""
        profile = {}

        for interaction in user_interactions:
            item_id = interaction["item_id"]
            rating = interaction["rating"]

            if item_id in self.item_features:
                item_data = self.item_features[item_id]

                # Weight features by rating
                for tag in item_data.get("tags", []):
                    if tag not in profile:
                        profile[tag] = 0
                    profile[tag] += rating

                # Add category preference
                category = item_data.get("category")
                if category:
                    if category not in profile:
                        profile[category] = 0
                    profile[category] += rating

        # Normalize profile
        if profile:
            max_score = max(profile.values())
            profile = {k: v / max_score for k, v in profile.items()}

        return profile

    def _calculate_content_similarity(self, user_profile: dict, item_data: dict) -> float:
        """Calculate similarity between user profile and item."""
        similarity = 0.0

        # Check tag similarity
        for tag in item_data.get("tags", []):
            if tag in user_profile:
                similarity += user_profile[tag] * 0.8

        # Check category similarity
        category = item_data.get("category")
        if category and category in user_profile:
            similarity += user_profile[category] * 0.2

        return min(similarity, 1.0)

    def _filter_recommendations(
        self, recommendations: list[RecommendationItem], request: RecommendationRequest
    ) -> list[RecommendationItem]:
        """Filter recommendations based on request criteria."""
        filtered = []

        for rec in recommendations:
            # Skip excluded items
            if rec.item_id in request.exclude_items:
                continue

            # Apply context filters if provided
            if request.context:
                # Example: filter by price range
                max_price = request.context.get("max_price")
                if max_price and rec.metadata.get("price", 0) > max_price:
                    continue

                # Example: filter by category
                required_category = request.context.get("category")
                if required_category and rec.metadata.get("category") != required_category:
                    continue

            filtered.append(rec)

        return filtered

    async def _fallback_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """Generate fallback recommendations when main algorithms fail."""
        recommendations = []

        # Simple fallback: return random items

        item_ids = list(self.item_features.keys())
        random.shuffle(item_ids)

        for item_id in item_ids[: request.limit]:
            item_data = self.item_features[item_id]
            recommendations.append(
                RecommendationItem(
                    item_id=item_id,
                    item_type=request.item_type,
                    title=item_data.get("title", f"Item {item_id}"),
                    description=item_data.get("description"),
                    score=0.5,
                    reason="Fallback recommendation",
                    metadata=item_data,
                )
            )

        return RecommendationResponse(
            user_id=request.user_id,
            recommendations=recommendations,
            recommendation_type=RecommendationType.TRENDING,
            total_items=len(recommendations),
            processing_time_ms=0.0,
        )

    async def record_interaction(
        self,
        user_id: str,
        item_id: str,
        rating: float,
        interaction_type: str = "rating",
    ):
        """Record user interaction for future recommendations."""
        try:
            if user_id not in self.user_interactions:
                self.user_interactions[user_id] = []

            interaction = {
                "item_id": item_id,
                "rating": rating,
                "interaction_type": interaction_type,
                "timestamp": time.time(),
            }

            self.user_interactions[user_id].append(interaction)

            # Store in Redis if available
            if self.redis_client:
                await self.redis_client.lpush(f"user_interactions:{user_id}", json.dumps(interaction))
                await self.redis_client.ltrim(f"user_interactions:{user_id}", 0, 999)  # Keep last 1000

        except Exception as e:
            logger.error(f"❌ Failed to record interaction: {e}")


# Global recommendation engine instance
recommendation_engine = RecommendationEngine()
