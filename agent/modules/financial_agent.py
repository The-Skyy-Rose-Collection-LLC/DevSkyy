
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import json


class TransactionStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    DISPUTED = "disputed"
    REFUNDED = "refunded"


class ChargebackReason(Enum):
    FRAUD = "fraud"
    AUTHORIZATION = "authorization"
    PROCESSING_ERROR = "processing_error"
    CONSUMER_DISPUTE = "consumer_dispute"
    NON_RECEIPT = "non_receipt"
    DUPLICATE_PROCESSING = "duplicate_processing"


@dataclass
class Transaction:
    id: str
    amount: float
    currency: str
    status: TransactionStatus
    customer_id: str
    product_id: str
    timestamp: datetime
    payment_method: str
    gateway: str
    metadata: Dict[str, Any]


@dataclass
class Chargeback:
    id: str
    transaction_id: str
    amount: float
    reason: ChargebackReason
    status: str
    created_at: datetime
    due_date: datetime
    evidence_submitted: bool = False
    outcome: Optional[str] = None


class FinancialAgent:
    """Agent for handling financial operations, chargebacks, and payment processing."""
    
    def __init__(self):
        self.transactions: List[Transaction] = []
        self.chargebacks: List[Chargeback] = []
        self.risk_rules: Dict[str, Any] = self._default_risk_rules()
    
    def _default_risk_rules(self) -> Dict[str, Any]:
        """Default risk assessment rules."""
        return {
            "high_amount_threshold": 500.0,
            "velocity_limit": 5,  # Max transactions per hour
            "suspicious_countries": ["XX", "YY"],  # Country codes
            "max_failed_attempts": 3,
            "chargeback_rate_threshold": 0.01  # 1%
        }
    
    def process_payment(self, amount: float, currency: str, customer_id: str, 
                       product_id: str, payment_method: str, gateway: str,
                       metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a payment transaction with risk assessment."""
        
        # Generate transaction ID
        transaction_id = f"txn_{datetime.now().strftime('%Y%m%d%H%M%S')}_{customer_id[:8]}"
        
        # Risk assessment
        risk_score = self._assess_risk(amount, customer_id, payment_method, metadata or {})
        
        if risk_score > 0.8:
            status = TransactionStatus.FAILED
            result = {"status": "rejected", "reason": "high_risk", "risk_score": risk_score}
        else:
            status = TransactionStatus.COMPLETED
            result = {"status": "approved", "risk_score": risk_score}
        
        # Create transaction record
        transaction = Transaction(
            id=transaction_id,
            amount=amount,
            currency=currency,
            status=status,
            customer_id=customer_id,
            product_id=product_id,
            timestamp=datetime.now(),
            payment_method=payment_method,
            gateway=gateway,
            metadata=metadata or {}
        )
        
        self.transactions.append(transaction)
        
        result.update({
            "transaction_id": transaction_id,
            "amount": amount,
            "currency": currency,
            "timestamp": transaction.timestamp.isoformat()
        })
        
        return result
    
    def _assess_risk(self, amount: float, customer_id: str, payment_method: str, 
                    metadata: Dict[str, Any]) -> float:
        """Assess transaction risk score (0-1, higher = riskier)."""
        risk_score = 0.0
        
        # High amount risk
        if amount > self.risk_rules["high_amount_threshold"]:
            risk_score += 0.3
        
        # Customer velocity check
        recent_transactions = [
            t for t in self.transactions 
            if t.customer_id == customer_id and 
            t.timestamp > datetime.now() - timedelta(hours=1)
        ]
        
        if len(recent_transactions) > self.risk_rules["velocity_limit"]:
            risk_score += 0.4
        
        # Failed transaction history
        failed_count = len([
            t for t in self.transactions 
            if t.customer_id == customer_id and t.status == TransactionStatus.FAILED
        ])
        
        if failed_count > self.risk_rules["max_failed_attempts"]:
            risk_score += 0.5
        
        # Geographic risk
        country = metadata.get("country", "")
        if country in self.risk_rules["suspicious_countries"]:
            risk_score += 0.3
        
        return min(risk_score, 1.0)
    
    def create_chargeback(self, transaction_id: str, reason: ChargebackReason, 
                         amount: float = None) -> Dict[str, Any]:
        """Create a chargeback case."""
        
        # Find the original transaction
        transaction = next((t for t in self.transactions if t.id == transaction_id), None)
        if not transaction:
            return {"error": "Transaction not found"}
        
        chargeback_amount = amount or transaction.amount
        chargeback_id = f"cb_{datetime.now().strftime('%Y%m%d%H%M%S')}_{transaction_id[-8:]}"
        
        chargeback = Chargeback(
            id=chargeback_id,
            transaction_id=transaction_id,
            amount=chargeback_amount,
            reason=reason,
            status="open",
            created_at=datetime.now(),
            due_date=datetime.now() + timedelta(days=7)  # 7 days to respond
        )
        
        self.chargebacks.append(chargeback)
        
        # Update transaction status
        transaction.status = TransactionStatus.DISPUTED
        
        return {
            "chargeback_id": chargeback_id,
            "transaction_id": transaction_id,
            "amount": chargeback_amount,
            "reason": reason.value,
            "due_date": chargeback.due_date.isoformat(),
            "status": "created"
        }
    
    def submit_chargeback_evidence(self, chargeback_id: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Submit evidence for a chargeback dispute."""
        
        chargeback = next((cb for cb in self.chargebacks if cb.id == chargeback_id), None)
        if not chargeback:
            return {"error": "Chargeback not found"}
        
        if chargeback.status != "open":
            return {"error": "Chargeback is not open for evidence submission"}
        
        chargeback.evidence_submitted = True
        chargeback.status = "under_review"
        
        # Store evidence (in real implementation, this would go to a database)
        evidence_data = {
            "chargeback_id": chargeback_id,
            "evidence": evidence,
            "submitted_at": datetime.now().isoformat()
        }
        
        return {
            "status": "evidence_submitted",
            "chargeback_id": chargeback_id,
            "submitted_at": evidence_data["submitted_at"]
        }
    
    def get_financial_dashboard(self) -> Dict[str, Any]:
        """Generate comprehensive financial dashboard."""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)
        
        # Transaction metrics
        total_transactions = len(self.transactions)
        today_transactions = [t for t in self.transactions if t.timestamp >= today_start]
        week_transactions = [t for t in self.transactions if t.timestamp >= week_start]
        month_transactions = [t for t in self.transactions if t.timestamp >= month_start]
        
        # Revenue metrics
        total_revenue = sum(t.amount for t in self.transactions if t.status == TransactionStatus.COMPLETED)
        today_revenue = sum(t.amount for t in today_transactions if t.status == TransactionStatus.COMPLETED)
        week_revenue = sum(t.amount for t in week_transactions if t.status == TransactionStatus.COMPLETED)
        month_revenue = sum(t.amount for t in month_transactions if t.status == TransactionStatus.COMPLETED)
        
        # Chargeback metrics
        total_chargebacks = len(self.chargebacks)
        open_chargebacks = len([cb for cb in self.chargebacks if cb.status == "open"])
        chargeback_amount = sum(cb.amount for cb in self.chargebacks)
        
        # Calculate chargeback rate
        completed_transactions = [t for t in self.transactions if t.status == TransactionStatus.COMPLETED]
        chargeback_rate = total_chargebacks / len(completed_transactions) if completed_transactions else 0
        
        return {
            "dashboard_generated": now.isoformat(),
            "transactions": {
                "total": total_transactions,
                "today": len(today_transactions),
                "week": len(week_transactions),
                "month": len(month_transactions)
            },
            "revenue": {
                "total": round(total_revenue, 2),
                "today": round(today_revenue, 2),
                "week": round(week_revenue, 2),
                "month": round(month_revenue, 2)
            },
            "chargebacks": {
                "total": total_chargebacks,
                "open": open_chargebacks,
                "total_amount": round(chargeback_amount, 2),
                "rate": round(chargeback_rate * 100, 2)  # Percentage
            },
            "alerts": self._generate_alerts()
        }
    
    def _generate_alerts(self) -> List[Dict[str, Any]]:
        """Generate financial alerts and warnings."""
        alerts = []
        
        # High chargeback rate alert
        completed_transactions = [t for t in self.transactions if t.status == TransactionStatus.COMPLETED]
        if completed_transactions:
            chargeback_rate = len(self.chargebacks) / len(completed_transactions)
            if chargeback_rate > self.risk_rules["chargeback_rate_threshold"]:
                alerts.append({
                    "type": "chargeback_rate",
                    "severity": "high",
                    "message": f"Chargeback rate ({chargeback_rate:.2%}) exceeds threshold",
                    "action": "Review risk rules and transaction patterns"
                })
        
        # Pending chargebacks due soon
        due_soon = [
            cb for cb in self.chargebacks 
            if cb.status == "open" and cb.due_date <= datetime.now() + timedelta(days=2)
        ]
        
        if due_soon:
            alerts.append({
                "type": "chargeback_due",
                "severity": "medium",
                "message": f"{len(due_soon)} chargebacks due within 2 days",
                "action": "Submit evidence or accept chargeback"
            })
        
        return alerts
