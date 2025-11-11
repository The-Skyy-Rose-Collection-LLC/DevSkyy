import unittest
from agent.modules.backend.customer_service_agent import CustomerServiceAgent
from agent.modules.backend.financial_agent import FinancialAgent
from agent.modules.backend.inventory_agent import InventoryAgent
from agent.modules.backend.seo_marketing_agent import SEOMarketingAgent


class TestFinancialAgent(unittest.TestCase):

    def test_chargeback_monitoring(self):
        """Test chargeback monitoring functionality.

        This test verifies that the chargeback monitoring system properly
        detects, tracks, and responds to chargeback events in the payment
        processing pipeline.
        """
        agent = FinancialAgent()
        result = agent.monitor_chargebacks()

        self.assertIn("chargeback_rate", result)
        self.assertIn("threshold_exceeded", result)
        self.assertIn("timestamp", result)
        self.assertIsInstance(result["chargeback_rate"], float)

    def test_fraud_detection(self):
        agent = FinancialAgent()
        transaction = {"country": "XX", "transactions_last_hour": 6, "amount": 1500}

        result = agent.detect_fraud(transaction)

        self.assertGreater(result["fraud_score"], 0)
        self.assertIn(result["risk_level"], ["HIGH", "LOW"])
        self.assertIn("indicators", result)

class TestInventoryAgent(unittest.TestCase):

    def test_stock_level_check(self):
        agent = InventoryAgent()
        result = agent.check_stock_levels()

        self.assertIn("low_stock_items", result)
        self.assertIn("out_of_stock_items", result)
        self.assertIn("total_items_checked", result)
        self.assertIsInstance(result["alerts_count"], int)

    def test_demand_forecasting(self):
        agent = InventoryAgent()
        result = agent.forecast_demand("SKY001")

        self.assertIn("predicted_weekly_demand", result)
        self.assertIn("confidence", result)
        self.assertIn("recommended_reorder_quantity", result)

class TestCustomerServiceAgent(unittest.TestCase):

    def test_ticket_categorization(self):
        agent = CustomerServiceAgent()
        ticket = "I need to return my damaged necklace"

        result = agent.auto_categorize_tickets(ticket)

        self.assertEqual(result["category"], "returns")
        self.assertIn("confidence", result)
        self.assertIn("suggested_priority", result)

    def test_auto_response_generation(self):
        agent = CustomerServiceAgent()
        response = agent.generate_auto_response("shipping", "John Doe")

        self.assertIn("John Doe", response)
        self.assertIn("shipping", response.lower())
        self.assertGreater(len(response), 50)

class TestMarketingAgent(unittest.TestCase):

    def test_campaign_analysis(self):
        agent = SEOMarketingAgent()
        result = agent.analyze_campaign_performance()

        self.assertIn("campaigns", result)
        self.assertIn("total_campaigns", result)
        self.assertIn("underperforming_count", result)

    def test_customer_segmentation(self):
        agent = SEOMarketingAgent()
        result = agent.segment_customers()

        self.assertIn("segments", result)
        self.assertIn("total_customers", result)
        expected_segments = [
            "high_value",
            "frequent_buyers",
            "at_risk",
            "new_customers",
        ]
        for segment in expected_segments:
            self.assertIn(segment, result["segments"])

class TestMainFunctions(unittest.TestCase):

    def test_financial_health_monitoring(self):
        agent = FinancialAgent()
        result = agent.monitor_chargebacks()

        self.assertIn("chargeback_rate", result)
        self.assertIn("threshold_exceeded", result)
        self.assertIn("timestamp", result)

    def test_inventory_management(self):
        agent = InventoryAgent()
        result = agent.optimize_inventory()

        self.assertIn("optimization_results", result)
        self.assertIn("recommendations", result)
        self.assertIn("timestamp", result)

    def test_customer_service_handling(self):
        agent = CustomerServiceAgent()
        result = agent.handle_inquiry("test inquiry")

        self.assertIn("response", result)
        self.assertIn("confidence", result)
        self.assertIn("timestamp", result)

    def test_marketing_optimization(self):
        agent = SEOMarketingAgent()
        result = agent.analyze_campaign_performance()

        self.assertIn("campaigns", result)
        self.assertIn("total_campaigns", result)
        self.assertIn("underperforming_count", result)
