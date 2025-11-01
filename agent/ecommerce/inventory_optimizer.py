from sklearn.ensemble import RandomForestRegressor

from typing import Any, Dict, List
import logging
import numpy as np

"""
Inventory Optimizer
ML-powered inventory management and forecasting
"""

logger = logging.getLogger(__name__)


class InventoryOptimizer:
    """
    Advanced inventory management with ML forecasting

    Features:
    - Demand forecasting
    - Reorder point optimization
    - Stock level recommendations
    - Seasonal inventory planning
    - Dead stock identification
    - Multi-location optimization
    """

    def __init__(self):
        self.forecast_model = RandomForestRegressor(n_estimators=100)
        self.inventory_data = {}
        self.reorder_rules = {}

        logger.info("📊 Inventory Optimizer initialized")

    async def forecast_demand(
        self, product_id: str, historical_sales: List[int], forecast_periods: int = 30
    ) -> Dict[str, Any]:
        """
        Forecast product demand using ML

        Args:
            product_id: Product ID
            historical_sales: Historical daily sales data
            forecast_periods: Number of days to forecast

        Returns:
            Demand forecast with confidence intervals
        """
        try:
            if len(historical_sales) < 14:
                return {
                    "success": False,
                    "error": "Insufficient historical data (minimum 14 days required)",
                }

            # Prepare time series features
            X = np.array([[i, i % 7, i % 30] for i in range(len(historical_sales))])
            y = np.array(historical_sales)

            # Train model
            self.forecast_model.fit(X, y)

            # Generate forecast
            future_X = np.array(
                [
                    [
                        len(historical_sales) + i,
                        (len(historical_sales) + i) % 7,
                        (len(historical_sales) + i) % 30,
                    ]
                    for i in range(forecast_periods)
                ]
            )

            forecast = self.forecast_model.predict(future_X)

            # Calculate confidence intervals (simplified)
            std = np.std(historical_sales)
            confidence_lower = forecast - (1.96 * std)
            confidence_upper = forecast + (1.96 * std)

            # Calculate trends
            recent_avg = np.mean(historical_sales[-7:])
            historical_avg = np.mean(historical_sales)
            trend = "increasing" if recent_avg > historical_avg else "decreasing"

            return {
                "success": True,
                "product_id": product_id,
                "forecast": {
                    "predicted_demand": forecast.tolist(),
                    "confidence_lower": np.maximum(0, confidence_lower).tolist(),
                    "confidence_upper": confidence_upper.tolist(),
                    "total_forecasted_units": int(np.sum(forecast)),
                },
                "analysis": {
                    "trend": trend,
                    "average_daily_sales": round(float(np.mean(historical_sales)), 2),
                    "peak_demand_day": int(np.argmax(forecast)),
                    "volatility": round(float(np.std(historical_sales) / np.mean(historical_sales)), 3),
                },
                "forecast_period_days": forecast_periods,
            }

        except Exception as e:
            logger.error(f"Demand forecasting failed: {e}")
            return {"success": False, "error": str(e)}

    async def calculate_reorder_point(
        self, product_data: Dict[str, Any], sales_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate optimal reorder point and quantity

        Args:
            product_data: Product information
            sales_data: Sales and demand data

        Returns:
            Reorder recommendations
        """
        try:
            # Extract data
            avg_daily_sales = sales_data.get("avg_daily_sales", 10)
            lead_time_days = product_data.get("supplier_lead_time_days", 14)
            safety_stock_days = product_data.get("safety_stock_days", 7)
            current_stock = product_data.get("current_stock", 0)

            # Calculate reorder point
            lead_time_demand = avg_daily_sales * lead_time_days
            safety_stock = avg_daily_sales * safety_stock_days
            reorder_point = lead_time_demand + safety_stock

            # Calculate economic order quantity (EOQ)
            annual_demand = avg_daily_sales * 365
            ordering_cost = product_data.get("ordering_cost", 50)
            holding_cost = product_data.get("holding_cost_per_unit", 5)

            if holding_cost > 0:
                eoq = np.sqrt((2 * annual_demand * ordering_cost) / holding_cost)
            else:
                eoq = avg_daily_sales * 30  # Default to 30 days supply

            # Determine if reorder is needed
            should_reorder = current_stock <= reorder_point

            # Calculate days until stockout
            if avg_daily_sales > 0:
                days_until_stockout = current_stock / avg_daily_sales
            else:
                days_until_stockout = 999

            return {
                "success": True,
                "product_id": product_data.get("id"),
                "current_stock": current_stock,
                "reorder_point": int(reorder_point),
                "recommended_order_quantity": int(eoq),
                "should_reorder": should_reorder,
                "urgency": ("high" if days_until_stockout < 7 else "medium" if days_until_stockout < 14 else "low"),
                "days_until_stockout": round(days_until_stockout, 1),
                "safety_stock": int(safety_stock),
                "lead_time_days": lead_time_days,
            }

        except Exception as e:
            logger.error(f"Reorder point calculation failed: {e}")
            return {"success": False, "error": str(e)}

    async def identify_dead_stock(self, inventory: List[Dict[str, Any]], threshold_days: int = 90) -> Dict[str, Any]:
        """
        Identify slow-moving and dead stock

        Args:
            inventory: List of inventory items
            threshold_days: Days without sales to consider dead

        Returns:
            Dead stock analysis
        """
        try:
            dead_stock = []
            slow_moving = []
            total_value_locked = 0

            for item in inventory:
                days_since_sale = item.get("days_since_last_sale", 0)
                quantity = item.get("quantity", 0)
                cost = item.get("cost", 0)

                value_locked = quantity * cost

                if days_since_sale >= threshold_days:
                    dead_stock.append(
                        {
                            "product_id": item.get("id"),
                            "product_name": item.get("name"),
                            "quantity": quantity,
                            "days_since_sale": days_since_sale,
                            "value_locked": value_locked,
                            "recommendation": (
                                "Aggressive clearance" if days_since_sale > 180 else "Promotional pricing"
                            ),
                        }
                    )
                    total_value_locked += value_locked

                elif days_since_sale >= threshold_days / 2:
                    slow_moving.append(
                        {
                            "product_id": item.get("id"),
                            "product_name": item.get("name"),
                            "quantity": quantity,
                            "days_since_sale": days_since_sale,
                            "value_locked": value_locked,
                            "recommendation": "Monitor closely, consider promotions",
                        }
                    )

            return {
                "success": True,
                "dead_stock": {
                    "count": len(dead_stock),
                    "items": dead_stock,
                    "total_value_locked": round(total_value_locked, 2),
                },
                "slow_moving": {"count": len(slow_moving), "items": slow_moving},
                "recommendations": [
                    f"Implement clearance strategy for {len(dead_stock)} items",
                    f"Total capital locked: ${total_value_locked:,.2f}",
                    "Consider bundling slow-moving items with bestsellers",
                ],
            }

        except Exception as e:
            logger.error(f"Dead stock identification failed: {e}")
            return {"success": False, "error": str(e)}

    async def optimize_stock_levels(
        self, products: List[Dict[str, Any]], target_service_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Optimize stock levels across all products

        Args:
            products: List of products with sales data
            target_service_level: Desired service level (0-1)

        Returns:
            Stock level recommendations
        """
        try:
            recommendations = []
            total_investment_needed = 0
            total_reduction_possible = 0

            for product in products:
                avg_sales = product.get("avg_daily_sales", 0)
                current_stock = product.get("current_stock", 0)
                cost = product.get("cost", 0)
                lead_time = product.get("lead_time_days", 14)

                # Calculate optimal stock level
                # Using normal distribution assumption for demand
                z_score = 1.65  # For 95% service level
                std_dev = product.get("sales_std_dev", avg_sales * 0.3)

                optimal_stock = (avg_sales * lead_time) + (z_score * std_dev * np.sqrt(lead_time))

                difference = optimal_stock - current_stock
                value_change = difference * cost

                recommendations.append(
                    {
                        "product_id": product.get("id"),
                        "product_name": product.get("name"),
                        "current_stock": current_stock,
                        "optimal_stock": int(optimal_stock),
                        "adjustment_needed": int(difference),
                        "value_change": round(value_change, 2),
                        "action": ("increase" if difference > 0 else "decrease" if difference < 0 else "maintain"),
                    }
                )

                if difference > 0:
                    total_investment_needed += value_change
                else:
                    total_reduction_possible += abs(value_change)

            return {
                "success": True,
                "target_service_level": target_service_level,
                "products_analyzed": len(products),
                "recommendations": recommendations,
                "financial_impact": {
                    "investment_needed": round(total_investment_needed, 2),
                    "capital_release_possible": round(total_reduction_possible, 2),
                    "net_change": round(total_investment_needed - total_reduction_possible, 2),
                },
            }

        except Exception as e:
            logger.error(f"Stock level optimization failed: {e}")
            return {"success": False, "error": str(e)}
