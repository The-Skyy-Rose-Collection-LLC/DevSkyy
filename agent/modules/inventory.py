from typing import Any, Dict, List


class InventoryAgent:
    """Handles inventory management, stock alerts, and demand forecasting."""

    def __init__(self):
        self.low_stock_threshold = 10
        self.high_demand_threshold = 50

    def check_stock_levels(self) -> Dict[str, Any]:
        """Check current stock levels and identify low inventory."""
        low_stock_items = []
        out_of_stock_items = []

        # Simulate inventory data
        inventory_data = self._fetch_inventory_data()

        for item in inventory_data:
            if item["quantity"] == 0:
                out_of_stock_items.append(item)
            elif item["quantity"] <= self.low_stock_threshold:
                low_stock_items.append(item)

        return {
            "low_stock_items": low_stock_items,
            "out_of_stock_items": out_of_stock_items,
            "total_items_checked": len(inventory_data),
            "alerts_count": len(low_stock_items) + len(out_of_stock_items),
        }

    def forecast_demand(self, product_id: str) -> Dict[str, Any]:
        """Forecast demand for specific products."""
        # Simulate demand forecasting based on historical data
        historical_sales = self._get_historical_sales(product_id)
        seasonal_factor = self._get_seasonal_factor()

        predicted_demand = sum(historical_sales[-7:]) * seasonal_factor

        return {
            "product_id": product_id,
            "predicted_weekly_demand": predicted_demand,
            "confidence": 0.85,
            "recommended_reorder_quantity": max(int(predicted_demand * 2), 20),
        }

    def auto_reorder_suggestions(self) -> List[Dict[str, Any]]:
        """Generate automatic reorder suggestions."""
        suggestions = []
        stock_data = self.check_stock_levels()

        for item in stock_data["low_stock_items"]:
            forecast = self.forecast_demand(item["product_id"])
            suggestions.append(
                {
                    "product_id": item["product_id"],
                    "current_stock": item["quantity"],
                    "suggested_order_quantity": forecast["recommended_reorder_quantity"],
                    "urgency": "HIGH" if item["quantity"] < 5 else "MEDIUM",
                }
            )

        return suggestions

    def _fetch_inventory_data(self) -> List[Dict]:
        """Fetch current inventory data."""
        return [
            {"product_id": "SKY001", "name": "Rose Gold Necklace", "quantity": 5},
            {"product_id": "SKY002", "name": "Diamond Ring", "quantity": 0},
            {"product_id": "SKY003", "name": "Pearl Earrings", "quantity": 25},
        ]

    def _get_historical_sales(self, product_id: str) -> List[int]:
        """Get historical sales data for demand forecasting."""
        # Simulate 30 days of sales data
        return [12, 15, 8, 22, 18, 14, 19, 25, 11, 16, 20, 13, 17, 24, 9]

    def _get_seasonal_factor(self) -> float:
        """Calculate seasonal demand factor."""
        # Simulate seasonal adjustment (e.g., holiday season boost)
        return 1.2


def manage_inventory() -> Dict[str, Any]:
    """Main inventory management function."""
    agent = InventoryAgent()

    stock_status = agent.check_stock_levels()
    reorder_suggestions = agent.auto_reorder_suggestions()

    return {
        "stock_status": stock_status,
        "reorder_suggestions": reorder_suggestions,
        "action_required": len(reorder_suggestions) > 0,
    }
