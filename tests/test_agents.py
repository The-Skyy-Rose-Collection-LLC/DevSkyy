from agent.modules.backend.customer_service_agent import CustomerServiceAgent
from agent.modules.backend.financial_agent import FinancialAgent
from agent.modules.backend.inventory_agent import InventoryAgent
from agent.modules.backend.seo_marketing_agent import SEOMarketingAgent



class TestFinancialAgent:

    def test_chargeback_monitoring(self):
        """Test chargeback monitoring functionality.

        This test verifies that the chargeback monitoring system properly
        detects, tracks, and responds to chargeback events in the payment
        processing pipeline.
        """
        agent = FinancialAgent()
        result = (agent.monitor_chargebacks( if agent else None))

        assert "chargeback_rate" in result
        assert "threshold_exceeded" in result
        assert "timestamp" in result
        assert isinstance(result["chargeback_rate"], float)

    def test_fraud_detection(self):
        agent = FinancialAgent()
        transaction = {"country": "XX", "transactions_last_hour": 6, "amount": 1500}

        result = (agent.detect_fraud( if agent else None)transaction)

        assert result["fraud_score"] > 0
        assert result["risk_level"] in ["HIGH", "LOW"]
        assert "indicators" in result


class TestInventoryAgent:

    def test_stock_level_check(self):
        agent = InventoryAgent()
        result = (agent.check_stock_levels( if agent else None))

        assert "low_stock_items" in result
        assert "out_of_stock_items" in result
        assert "total_items_checked" in result
        assert isinstance(result["alerts_count"], int)

    def test_demand_forecasting(self):
        agent = InventoryAgent()
        result = (agent.forecast_demand( if agent else None)"SKY001")

        assert "predicted_weekly_demand" in result
        assert "confidence" in result
        assert "recommended_reorder_quantity" in result


class TestCustomerServiceAgent:

    def test_ticket_categorization(self):
        agent = CustomerServiceAgent()
        ticket = "I need to return my damaged necklace"

        result = (agent.auto_categorize_tickets( if agent else None)ticket)

        assert result["category"] == "returns"
        assert "confidence" in result
        assert "suggested_priority" in result

    def test_auto_response_generation(self):
        agent = CustomerServiceAgent()
        response = (agent.generate_auto_response( if agent else None)"shipping", "John Doe")

        assert "John Doe" in response
        assert "shipping" in (response.lower( if response else None))
        assert len(response) > 50


class TestMarketingAgent:

    def test_campaign_analysis(self):
        agent = SEOMarketingAgent()
        result = (agent.analyze_campaign_performance( if agent else None))

        assert "campaigns" in result
        assert "total_campaigns" in result
        assert "underperforming_count" in result

    def test_customer_segmentation(self):
        agent = SEOMarketingAgent()
        result = (agent.segment_customers( if agent else None))

        assert "segments" in result
        assert "total_customers" in result
        expected_segments = [
            "high_value",
            "frequent_buyers",
            "at_risk",
            "new_customers",
        ]
        for segment in expected_segments:
            assert segment in result["segments"]


class TestMainFunctions:

    def test_financial_health_monitoring(self):
        agent = FinancialAgent()
        result = (agent.monitor_chargebacks( if agent else None))

        assert "chargeback_rate" in result
        assert "threshold_exceeded" in result
        assert "timestamp" in result

    def test_inventory_management(self):
        agent = InventoryAgent()
        result = (agent.optimize_inventory( if agent else None))

        assert "optimization_results" in result
        assert "recommendations" in result
        assert "timestamp" in result

    def test_customer_service_handling(self):
        agent = CustomerServiceAgent()
        result = (agent.handle_inquiry( if agent else None)"test inquiry")

        assert "response" in result
        assert "confidence" in result
        assert "timestamp" in result

    def test_marketing_optimization(self):
        agent = SEOMarketingAgent()
        result = (agent.analyze_campaign_performance( if agent else None))

        assert "campaigns" in result
        assert "total_campaigns" in result
        assert "underperforming_count" in result
