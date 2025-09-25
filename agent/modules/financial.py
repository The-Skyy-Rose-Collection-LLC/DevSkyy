from datetime import datetime, timezone
from typing import Any, Dict, List


class FinancialAgent:
    """Handles financial operations, chargebacks, fraud detection, and payment monitoring."""

    def __init__(self):
        self.chargeback_threshold = 1.0  # 1% chargeback rate threshold
        self.fraud_score_threshold = 70

    def monitor_chargebacks(self) -> Dict[str, Any]:
        """Monitor and analyze chargeback patterns."""
        # Simulate chargeback data analysis
        recent_chargebacks = self._fetch_recent_chargebacks()
        chargeback_rate = self._calculate_chargeback_rate(recent_chargebacks)

        alert_data = {
            "chargeback_rate": chargeback_rate,
            "threshold_exceeded": chargeback_rate > self.chargeback_threshold,
            "recent_chargebacks": len(recent_chargebacks),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if alert_data["threshold_exceeded"]:
            self._trigger_chargeback_alert(alert_data)

        return alert_data

    def detect_fraud(self, transaction_data: Dict) -> Dict[str, Any]:
        """Analyze transaction for fraud indicators."""
        fraud_score = 0
        indicators = []

        # High-risk country check
        high_risk_countries = ["XX", "YY"]  # Replace with actual high-risk ISO codes
        if transaction_data.get("country") in high_risk_countries:
            fraud_score += 25
            indicators.append("high_risk_country")

        # Velocity checks
        if transaction_data.get("transactions_last_hour", 0) > 5:
            fraud_score += 30
            indicators.append("high_velocity")

        # Amount anomaly
        if transaction_data.get("amount", 0) > 1000:
            fraud_score += 20
            indicators.append("high_amount")

        return {
            "fraud_score": fraud_score,
            "risk_level": "HIGH" if fraud_score > self.fraud_score_threshold else "LOW",
            "indicators": indicators,
            "recommended_action": "BLOCK" if fraud_score > 80 else "REVIEW" if fraud_score > 50 else "APPROVE",
        }

    def reconcile_payments(self) -> Dict[str, Any]:
        """Reconcile payments across payment processors."""
        discrepancies = []
        total_processed = 0

        # Simulate payment reconciliation
        payment_processors = ["stripe", "paypal", "shopify_payments"]

        for processor in payment_processors:
            processor_data = self._fetch_processor_data(processor)
            total_processed += processor_data.get("amount", 0)

            if processor_data.get("discrepancy"):
                discrepancies.append(
                    {
                        "processor": processor,
                        "amount": processor_data["discrepancy"],
                        "type": processor_data.get("discrepancy_type", "unknown"),
                    }
                )

        return {
            "total_processed": total_processed,
            "discrepancies": discrepancies,
            "status": "CLEAN" if not discrepancies else "NEEDS_REVIEW",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _fetch_recent_chargebacks(self) -> List[Dict]:
        """Fetch recent chargeback data."""
        # Simulate API call to payment processor
        return [
            {"id": "cb_1", "amount": 150.00, "reason": "fraudulent"},
            {"id": "cb_2", "amount": 89.99, "reason": "product_not_received"},
        ]

    def _calculate_chargeback_rate(self, chargebacks: List[Dict]) -> float:
        """Calculate current chargeback rate."""
        # Simulate calculation based on total transactions vs chargebacks
        return 0.8  # 0.8% example rate

    def _trigger_chargeback_alert(self, alert_data: Dict) -> None:
        """Send chargeback alert to management."""
        print(f"🚨 CHARGEBACK ALERT: Rate {alert_data['chargeback_rate']}% exceeds threshold")

    def _fetch_processor_data(self, processor: str) -> Dict:
        """Fetch data from payment processor."""
        # Simulate processor API calls
        return {"processor": processor, "amount": 5000.00, "discrepancy": None}


def monitor_financial_health() -> Dict[str, Any]:
    """Main function to monitor overall financial health."""
    agent = FinancialAgent()

    chargeback_status = agent.monitor_chargebacks()
    reconciliation_status = agent.reconcile_payments()

    return {
        "chargebacks": chargeback_status,
        "reconciliation": reconciliation_status,
        "overall_status": (
            "HEALTHY"
            if not chargeback_status["threshold_exceeded"] and reconciliation_status["status"] == "CLEAN"
            else "NEEDS_ATTENTION"
        ),
    }
