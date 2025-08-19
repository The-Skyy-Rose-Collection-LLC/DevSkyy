
from typing import Dict, List, Any
from datetime import datetime, timedelta


class CustomerServiceAgent:
    """Handles customer service automation, ticket routing, and satisfaction monitoring."""
    
    def __init__(self):
        self.response_time_threshold = 2  # hours
        self.satisfaction_threshold = 4.0  # out of 5
        
    def auto_categorize_tickets(self, ticket_content: str) -> Dict[str, Any]:
        """Automatically categorize support tickets."""
        keywords = {
            "shipping": ["shipping", "delivery", "tracking", "package"],
            "returns": ["return", "refund", "exchange", "damaged"],
            "payment": ["payment", "charge", "card", "billing"],
            "product": ["product", "quality", "defect", "broken"],
            "account": ["account", "login", "password", "profile"]
        }
        
        content_lower = ticket_content.lower()
        scores = {}
        
        for category, words in keywords.items():
            score = sum(1 for word in words if word in content_lower)
            scores[category] = score
        
        best_category = max(scores, key=scores.get) if any(scores.values()) else "general"
        confidence = scores[best_category] / len(keywords[best_category]) if best_category in keywords else 0
        
        return {
            "category": best_category,
            "confidence": confidence,
            "suggested_priority": "HIGH" if "urgent" in content_lower or "emergency" in content_lower else "NORMAL",
            "auto_response_available": best_category in ["shipping", "returns"]
        }
    
    def generate_auto_response(self, category: str, customer_name: str = "Valued Customer") -> str:
        """Generate automated responses for common inquiries."""
        responses = {
            "shipping": f"""Dear {customer_name},
            
Thank you for contacting The Skyy Rose Collection. We've received your shipping inquiry.

Your order status and tracking information can be found in your account dashboard. Most orders are processed within 1-2 business days and arrive within 3-5 business days.

If you need immediate assistance, please reply with your order number.

Best regards,
The Skyy Rose Collection Team""",
            
            "returns": f"""Dear {customer_name},
            
Thank you for reaching out regarding a return.

We offer a 30-day return policy for unworn items in original packaging. To initiate a return:
1. Log into your account
2. Go to Order History
3. Select "Return Item"
4. Print the prepaid return label

Refunds are processed within 5-7 business days after we receive your return.

Best regards,
The Skyy Rose Collection Team""",
            
            "general": f"""Dear {customer_name},
            
Thank you for contacting The Skyy Rose Collection. We've received your inquiry and will respond within 24 hours.

For immediate assistance, you can also check our FAQ section or live chat during business hours.

Best regards,
The Skyy Rose Collection Team"""
        }
        
        return responses.get(category, responses["general"])
    
    def monitor_response_times(self) -> Dict[str, Any]:
        """Monitor customer service response times."""
        # Simulate ticket data
        open_tickets = self._fetch_open_tickets()
        overdue_tickets = []
        
        for ticket in open_tickets:
            hours_elapsed = (datetime.utcnow() - ticket["created_at"]).total_seconds() / 3600
            if hours_elapsed > self.response_time_threshold:
                overdue_tickets.append({
                    "ticket_id": ticket["id"],
                    "hours_overdue": hours_elapsed - self.response_time_threshold,
                    "category": ticket["category"]
                })
        
        return {
            "total_open_tickets": len(open_tickets),
            "overdue_tickets": len(overdue_tickets),
            "overdue_details": overdue_tickets,
            "average_response_time": 1.5,  # Simulated average in hours
            "performance_status": "GOOD" if len(overdue_tickets) == 0 else "NEEDS_ATTENTION"
        }
    
    def analyze_satisfaction(self) -> Dict[str, Any]:
        """Analyze customer satisfaction metrics."""
        # Simulate satisfaction data
        recent_ratings = [5, 4, 5, 3, 4, 5, 4, 2, 5, 4]
        average_rating = sum(recent_ratings) / len(recent_ratings)
        
        low_ratings = [r for r in recent_ratings if r <= 2]
        
        return {
            "average_rating": average_rating,
            "total_responses": len(recent_ratings),
            "low_ratings_count": len(low_ratings),
            "satisfaction_status": "EXCELLENT" if average_rating >= 4.5 else "GOOD" if average_rating >= 4.0 else "NEEDS_IMPROVEMENT",
            "trend": "IMPROVING"  # Simulated trend
        }
    
    def _fetch_open_tickets(self) -> List[Dict]:
        """Fetch open support tickets."""
        return [
            {
                "id": "TK001",
                "category": "shipping",
                "created_at": datetime.utcnow() - timedelta(hours=3),
                "priority": "NORMAL"
            },
            {
                "id": "TK002", 
                "category": "returns",
                "created_at": datetime.utcnow() - timedelta(hours=1),
                "priority": "HIGH"
            }
        ]


def handle_customer_service() -> Dict[str, Any]:
    """Main customer service management function."""
    agent = CustomerServiceAgent()
    
    response_metrics = agent.monitor_response_times()
    satisfaction_metrics = agent.analyze_satisfaction()
    
    return {
        "response_metrics": response_metrics,
        "satisfaction_metrics": satisfaction_metrics,
        "overall_status": "OPTIMAL" if response_metrics["performance_status"] == "GOOD" 
                         and satisfaction_metrics["satisfaction_status"] in ["EXCELLENT", "GOOD"] 
                         else "NEEDS_ATTENTION"
    }
