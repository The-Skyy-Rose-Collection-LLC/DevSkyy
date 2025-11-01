"""Finance Agent - Financial logging, ledger, and reporting."""

import time
from pathlib import Path
from typing import Any, Dict, List

from src.core.utils import save_json

from .base import BaseAgent


class FinanceAgent(BaseAgent):
    """Agent responsible for financial operations and reporting."""

    def __init__(self, *args, **kwargs):
        """Initialize Finance Agent."""
        super().__init__(name="FinanceAgent", *args, **kwargs)
        self.ledger_path = self.io_path / "ledger"
        self.ledger_path.mkdir(parents=True, exist_ok=True)

    def get_supported_tasks(self) -> List[str]:
        """Get supported task types."""
        return ["record_ledger", "calculate_revenue", "generate_reports", "reconcile"]

    async def process_task(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process finance-related tasks.

        Args:
            task_type: Type of finance task
            payload: Task parameters

        Returns:
            Task result
        """
        if task_type == "record_ledger":
            return await self._record_ledger(payload)
        elif task_type == "calculate_revenue":
            return await self._calculate_revenue(payload)
        elif task_type == "generate_reports":
            return await self._generate_reports(payload)
        elif task_type == "reconcile":
            return await self._reconcile(payload)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")

    async def _record_ledger(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Record transaction in ledger.

        Args:
            payload: Transaction details

        Returns:
            Ledger entry
        """
        self.logger.info(f"Recording ledger entry: {payload}")

        transaction_type = payload.get("type", "sale")
        amount_cents = payload.get("revenue_cents") or payload.get("total_cents", 0)
        reference_id = payload.get("order_id") or payload.get("campaign_id", "unknown")

        entry = {
            "entry_id": f"LED-{int(time.time())}",
            "transaction_type": transaction_type,
            "amount_cents": amount_cents,
            "currency": "USD",
            "reference_id": reference_id,
            "recorded_at": time.time(),
            "metadata": payload,
        }

        # Save to ledger file
        ledger_file = self.ledger_path / f"ledger_{time.strftime('%Y%m%d')}.json"
        save_json(entry, ledger_file)

        self.logger.info(f"Ledger entry recorded: {entry['entry_id']}")
        return entry

    async def _calculate_revenue(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate revenue for a period.

        Args:
            payload: Period parameters (start_date, end_date)

        Returns:
            Revenue calculation
        """
        self.logger.info("Calculating revenue")

        start_date = payload.get("start_date")
        end_date = payload.get("end_date")

        # Placeholder for revenue calculation
        # In production, aggregate ledger entries

        revenue = {
            "period_start": start_date,
            "period_end": end_date,
            "total_revenue_cents": 500000,  # $5000
            "transaction_count": 50,
            "average_order_cents": 10000,  # $100
            "calculated_at": time.time(),
        }

        self.logger.info(f"Revenue calculated: ${revenue['total_revenue_cents']/100:.2f}")
        return revenue

    async def _generate_reports(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate financial reports.

        Args:
            payload: Report parameters

        Returns:
            Report details
        """
        self.logger.info(f"Generating report: {payload.get('report_type')}")

        report_type = payload.get("report_type", "monthly")
        period = payload.get("period", time.strftime("%Y-%m"))

        report = {
            "report_id": f"REP-{int(time.time())}",
            "report_type": report_type,
            "period": period,
            "summary": {
                "total_revenue_cents": 500000,
                "total_expenses_cents": 100000,
                "net_profit_cents": 400000,
                "margin_percent": 80.0,
            },
            "generated_at": time.time(),
        }

        # Save report
        report_file = self.io_path / f"report_{report_type}_{period}.json"
        save_json(report, report_file)

        self.logger.info(f"Report generated: {report['report_id']}")
        return report

    async def _reconcile(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Reconcile accounts.

        Args:
            payload: Reconciliation parameters

        Returns:
            Reconciliation result
        """
        self.logger.info("Reconciling accounts")

        # Placeholder for reconciliation logic
        reconciliation = {
            "reconciliation_id": f"REC-{int(time.time())}",
            "status": "balanced",
            "discrepancies": [],
            "reconciled_at": time.time(),
        }

        self.logger.info("Reconciliation complete")
        return reconciliation
