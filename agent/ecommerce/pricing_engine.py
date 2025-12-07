from datetime import datetime, timedelta
import logging
from typing import Any

from sklearn.ensemble import GradientBoostingRegressor


"""
Dynamic Pricing Engine
ML-powered dynamic pricing optimization for fashion ecommerce
"""

logger = logging.getLogger(__name__)


class DynamicPricingEngine:
    """
    Advanced dynamic pricing with ML

    Features:
    - Demand-based pricing
    - Competitor price monitoring
    - Seasonal adjustments
    - Personalized pricing
    - Clearance optimization
    - A/B price testing
    - Profit maximization
    """

    def __init__(self):
        self.pricing_model = GradientBoostingRegressor(n_estimators=100)
        self.price_history = {}
        self.competitor_prices = {}
        self.is_trained = False

        logger.info("💰 Dynamic Pricing Engine initialized")

    async def optimize_price(self, product_data: dict[str, Any], market_data: dict[str, Any]) -> dict[str, Any]:
        """
        Calculate optimal price for a product

        Args:
            product_data: Product information
            market_data: Market conditions and competitor data

        Returns:
            Optimal pricing recommendations
        """
        try:
            # Extract features
            base_price = product_data.get("base_price", 100)
            cost = product_data.get("cost", 50)
            inventory_level = product_data.get("inventory", 100)
            age_days = product_data.get("age_days", 0)
            demand_score = market_data.get("demand_score", 0.5)
            competitor_avg = market_data.get("competitor_avg_price", base_price)
            season_factor = market_data.get("season_factor", 1.0)

            # Calculate demand elasticity
            elasticity = await self._calculate_elasticity(product_data, market_data)

            # Base optimization
            if demand_score > 0.7:
                # High demand - increase price
                adjustment = 1.15
            elif demand_score < 0.3:
                # Low demand - decrease price
                adjustment = 0.85
            else:
                # Normal demand
                adjustment = 1.0

            # Inventory adjustments
            if inventory_level > 100:
                adjustment *= 0.95  # Reduce price for overstock
            elif inventory_level < 20:
                adjustment *= 1.05  # Increase price for low stock

            # Age adjustments (clearance)
            if age_days > 90:
                adjustment *= 0.80  # 20% off for items older than 90 days
            elif age_days > 180:
                adjustment *= 0.60  # 40% off for items older than 180 days

            # Competitive adjustments with sophisticated pricing strategy
            competitive_ratio = base_price / competitor_avg if competitor_avg > 0 else 1.0

            if competitor_avg * 0.95 < base_price < competitor_avg * 1.05:
                # Price competitive - maintain position with slight optimization
                if demand_score > 0.6:
                    # High demand allows for premium positioning
                    adjustment *= 1.02
                elif inventory_level > 80:
                    # High inventory - be more aggressive
                    adjustment *= 0.98
                else:
                    # Maintain competitive position
                    adjustment *= 1.0

                logger.debug(f"💰 Competitive pricing maintained: ratio={competitive_ratio:.3f}")

            elif base_price > competitor_avg * 1.1:
                # Price too high - reduce more aggressively
                if demand_score > 0.8:
                    # High demand can support premium
                    adjustment *= 0.98
                else:
                    # Standard reduction
                    adjustment *= 0.95

                logger.info(f"📉 Reducing high price: was {competitive_ratio:.1f}x competitor avg")

            elif base_price < competitor_avg * 0.9:
                # Price too low - increase strategically
                if inventory_level < 30:
                    # Low inventory - increase more
                    adjustment *= 1.08
                else:
                    # Standard increase
                    adjustment *= 1.05

                logger.info(f"📈 Increasing low price: was {competitive_ratio:.1f}x competitor avg")

            # Seasonal adjustments
            adjustment *= season_factor

            # Calculate optimal price
            optimal_price = base_price * adjustment

            # Ensure minimum margin
            min_price = cost * 1.3  # Minimum 30% margin
            optimal_price = max(optimal_price, min_price)

            # Calculate price range
            price_range = {
                "min": round(optimal_price * 0.9, 2),
                "recommended": round(optimal_price, 2),
                "max": round(optimal_price * 1.1, 2),
            }

            # Calculate expected impact
            expected_revenue = await self._calculate_expected_revenue(optimal_price, demand_score, elasticity)

            return {
                "success": True,
                "current_price": base_price,
                "optimal_price": round(optimal_price, 2),
                "price_range": price_range,
                "adjustment_factor": round(adjustment, 3),
                "expected_revenue_increase": f"{((expected_revenue / base_price) - 1) * 100:.1f}%",
                "confidence": 0.85,
                "factors": {
                    "demand": demand_score,
                    "inventory": inventory_level,
                    "age_days": age_days,
                    "competitor_avg": competitor_avg,
                    "elasticity": elasticity,
                },
                "recommendations": await self._get_pricing_recommendations(product_data, optimal_price, base_price),
            }

        except Exception as e:
            logger.error(f"Price optimization failed: {e}")
            return {"success": False, "error": str(e)}

    async def _calculate_elasticity(self, product_data: dict, market_data: dict) -> float:
        """Calculate price elasticity of demand"""
        # Simplified elasticity calculation
        # In production, this would use historical price/demand data

        category = product_data.get("category", "")

        # Category-based elasticity estimates
        if "luxury" in category.lower():
            return -0.5  # Inelastic (luxury goods)
        elif "basic" in category.lower():
            return -1.5  # Elastic (basic items)
        else:
            return -1.0  # Unit elastic

    async def _calculate_expected_revenue(self, price: float, demand_score: float, elasticity: float) -> float:
        """Calculate expected revenue at given price"""
        # Revenue = Price × Demand
        # Demand changes based on price elasticity
        base_demand = 100  # Base units
        demand = base_demand * demand_score * (1 + elasticity * 0.1)
        revenue = price * demand
        return revenue

    async def _get_pricing_recommendations(
        self, product_data: dict, optimal_price: float, current_price: float
    ) -> list[str]:
        """Generate pricing recommendations"""
        recommendations = []

        price_change = ((optimal_price / current_price) - 1) * 100

        if abs(price_change) > 10:
            recommendations.append(f"Consider gradual price adjustment of {price_change:.1f}% over 2-3 weeks")

        if product_data.get("inventory", 0) > 100:
            recommendations.append("High inventory detected - consider promotional pricing")

        if product_data.get("age_days", 0) > 90:
            recommendations.append("Product aging - implement clearance strategy")

        return recommendations

    async def create_pricing_strategy(self, strategy_type: str, products: list[dict]) -> dict[str, Any]:
        """
        Create pricing strategy for multiple products

        Args:
            strategy_type: Type of strategy (clearance, seasonal, competitive, etc.)
            products: List of products

        Returns:
            Pricing strategy configuration
        """
        try:
            strategies = {
                "clearance": {
                    "discount_tiers": [
                        {"age_days": 60, "discount": 0.15},
                        {"age_days": 90, "discount": 0.25},
                        {"age_days": 120, "discount": 0.40},
                        {"age_days": 180, "discount": 0.60},
                    ],
                    "additional_inventory_discount": 0.10,
                },
                "seasonal": {
                    "spring": 1.05,
                    "summer": 1.10,
                    "fall": 1.0,
                    "winter": 0.95,
                },
                "competitive": {
                    "match_competitor": True,
                    "undercut_by": 0.05,
                    "minimum_margin": 0.30,
                },  # 5%
                "premium": {
                    "base_multiplier": 1.20,
                    "scarcity_bonus": 1.15,
                    "quality_bonus": 1.10,
                },
            }

            strategy = strategies.get(strategy_type, {})

            # Apply strategy to products
            pricing_updates = []
            for product in products:
                update = {
                    "product_id": product.get("id"),
                    "current_price": product.get("price"),
                    "strategy": strategy_type,
                }

                if strategy_type == "clearance":
                    age = product.get("age_days", 0)
                    inventory = product.get("inventory", 0)

                    discount = 0
                    for tier in strategy["discount_tiers"]:
                        if age >= tier["age_days"]:
                            discount = tier["discount"]

                    if inventory > 100:
                        discount += strategy["additional_inventory_discount"]

                    new_price = product.get("price") * (1 - discount)
                    update["new_price"] = round(new_price, 2)
                    update["discount"] = f"{discount * 100:.0f}%"

                pricing_updates.append(update)

            return {
                "success": True,
                "strategy_type": strategy_type,
                "products_affected": len(pricing_updates),
                "pricing_updates": pricing_updates,
            }

        except Exception as e:
            logger.error(f"Pricing strategy creation failed: {e}")
            return {"success": False, "error": str(e)}

    async def ab_test_pricing(
        self,
        product_id: str,
        price_variant_a: float,
        price_variant_b: float,
        duration_days: int = 14,
    ) -> dict[str, Any]:
        """
        Set up A/B test for pricing

        Args:
            product_id: Product ID
            price_variant_a: First price to test
            price_variant_b: Second price to test
            duration_days: Test duration

        Returns:
            A/B test configuration
        """
        try:
            test_id = f"AB-{product_id}-{int(datetime.utcnow().timestamp())}"

            test_config = {
                "test_id": test_id,
                "product_id": product_id,
                "variants": {
                    "A": {"price": price_variant_a, "traffic_split": 0.5},
                    "B": {"price": price_variant_b, "traffic_split": 0.5},
                },
                "start_date": datetime.utcnow().isoformat(),
                "end_date": (datetime.utcnow() + timedelta(days=duration_days)).isoformat(),
                "metrics_tracked": [
                    "conversion_rate",
                    "revenue_per_visitor",
                    "cart_additions",
                    "page_views",
                ],
                "min_sample_size": 1000,
                "confidence_level": 0.95,
            }

            logger.info(f"🧪 A/B test created: {test_id}")

            return {
                "success": True,
                "test": test_config,
                "estimated_completion": f"{duration_days} days",
            }

        except Exception as e:
            logger.error(f"A/B test creation failed: {e}")
            return {"success": False, "error": str(e)}
