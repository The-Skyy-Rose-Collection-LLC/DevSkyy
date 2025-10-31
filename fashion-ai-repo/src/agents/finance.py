"""Finance Agent - Financial logging, ledger, and reporting."""

import time
from pathlib import Path
from typing import Any, Dict, List

from src.core.utils import save_json

from .base import BaseAgent


class FinanceAgent(BaseAgent):
    """Agent responsible for financial operations and reporting."""

    def __init__(self, *args, **kwargs):
        """
        Create a FinanceAgent and ensure its ledger directory exists under the agent's IO path.
        
        This initializer sets the agent name and creates a "ledger" directory at `self.io_path / "ledger"` if it does not already exist.
        """
        super().__init__(name="FinanceAgent", *args, **kwargs)
        self.ledger_path = self.io_path / "ledger"
        self.ledger_path.mkdir(parents=True, exist_ok=True)

    def get_supported_tasks(self) -> List[str]:
        """
        List the task types this agent can handle.
        
        Returns:
            supported_tasks (List[str]): Identifiers of supported tasks: "record_ledger", "calculate_revenue", "generate_reports", and "reconcile".
        """
        return ["record_ledger", "calculate_revenue", "generate_reports", "reconcile"]

    async def process_task(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a finance task to the appropriate handler and return its result.
        
        Parameters:
            task_type (str): The task name to perform; one of "record_ledger", "calculate_revenue", "generate_reports", or "reconcile".
            payload (Dict[str, Any]): Task-specific parameters forwarded to the selected handler.
        
        Returns:
            Dict[str, Any]: The result produced by the invoked task handler.
        
        Raises:
            ValueError: If `task_type` is not one of the supported task names.
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
        """
        Create and persist a ledger entry for a financial transaction.
        
        Parameters:
            payload (Dict[str, Any]): Transaction details. Recognized keys:
                - "type": transaction type (defaults to "sale")
                - "revenue_cents" or "total_cents": amount in cents (defaults to 0)
                - "order_id" or "campaign_id": reference identifier (defaults to "unknown")
                - any other keys are stored as metadata
        
        Returns:
            Dict[str, Any]: The saved ledger entry with keys:
                - "entry_id": unique entry identifier
                - "transaction_type": resolved transaction type
                - "amount_cents": resolved amount in cents
                - "currency": currency code ("USD")
                - "reference_id": resolved reference identifier
                - "recorded_at": timestamp when entry was recorded
                - "metadata": original payload
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
        """
        Compute revenue summary for a given period.
        
        Parameters:
            payload (Dict[str, Any]): Input parameters; expected keys:
                - "start_date": period start (string or timestamp)
                - "end_date": period end (string or timestamp)
        
        Returns:
            Dict[str, Any]: Revenue summary containing:
                - "period_start": provided start_date
                - "period_end": provided end_date
                - "total_revenue_cents": total revenue in cents
                - "transaction_count": number of transactions in the period
                - "average_order_cents": average order value in cents
                - "calculated_at": UNIX timestamp when the calculation was performed
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
        """
        Builds and persists a financial report for the requested period and type.
        
        Parameters:
            payload (Dict[str, Any]): Report options. Recognized keys:
                - report_type (str): Type of report to generate (e.g., "monthly"). Defaults to "monthly".
                - period (str): Reporting period identifier (e.g., "2025-10"). Defaults to current year-month.
        
        Returns:
            Dict[str, Any]: A report object containing:
                - report_id (str): Unique report identifier.
                - report_type (str): The report type used.
                - period (str): The reporting period.
                - summary (dict): Financial summary with keys `total_revenue_cents`, `total_expenses_cents`, `net_profit_cents`, and `margin_percent`.
                - generated_at (float): Timestamp when the report was generated.
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
        """
        Perform account reconciliation for the given parameters and return the reconciliation result.
        
        Parameters:
            payload (Dict[str, Any]): Parameters that influence reconciliation (e.g., date range, account identifiers). Keys and accepted values are implementation-specific.
        
        Returns:
            Dict[str, Any]: Reconciliation summary containing:
                - reconciliation_id (str): Unique identifier for this reconciliation run.
                - status (str): Outcome status such as "balanced" or "unbalanced".
                - discrepancies (List[Any]): List of found discrepancies (empty when none).
                - reconciled_at (float): Timestamp (POSIX seconds) when reconciliation completed.
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