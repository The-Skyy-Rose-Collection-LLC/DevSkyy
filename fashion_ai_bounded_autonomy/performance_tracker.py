"""
LAYER 6 — Performance Tracking and Self-Assessment
Evaluate system performance and propose improvements safely

All enhancements are written to proposals.json and never executed automatically.
Operator reviews and integrates approved updates manually.
"""

from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import sqlite3
from typing import Any, Optional


logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Track KPIs and generate improvement proposals.

    Features:
    - Numeric KPI logging
    - Weekly improvement computation
    - Proposal generation (never auto-executed)
    - Operator review workflow
    """

    def __init__(self, db_path: str = "fashion_ai_bounded_autonomy/performance_metrics.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

        self.proposals_path = Path("fashion_ai_bounded_autonomy/proposals.json")
        self.proposals_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("📈 Performance tracker initialized")

    def _init_database(self):
        """Initialize metrics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_timestamp
            ON agent_metrics (agent_name, timestamp)
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metadata TEXT,
                timestamp TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def log_metric(
        self,
        agent_name: str,
        metric_name: str,
        metric_value: float
    ):
        """Log agent performance metric"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO agent_metrics (agent_name, metric_name, metric_value, timestamp)
            VALUES (?, ?, ?, ?)
        """, (agent_name, metric_name, metric_value, datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def log_system_metric(
        self,
        metric_name: str,
        metric_value: float,
        metadata: Optional[dict] = None
    ):
        """
        Record a system-level metric entry to the configured SQLite database.
        
        Parameters:
            metric_name (str): Identifier for the metric (e.g., "cpu_usage", "memory_mb").
            metric_value (float): Numeric value of the metric.
            metadata (Optional[dict]): Optional additional context stored as JSON alongside the metric.
        
        Notes:
            The metric is persisted to the instance's database file with an ISO 8601 timestamp.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO system_metrics (metric_name, metric_value, metadata, timestamp)
            VALUES (?, ?, ?, ?)
        """, (
            metric_name,
            metric_value,
            json.dumps(metadata) if metadata else None,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

    async def compute_weekly_report(self) -> dict[str, Any]:
        """
        Produce a weekly performance report for agents and system metrics.
        
        Returns:
            report (dict[str, Any]): Summary containing:
                - period (str): Report period identifier, e.g., "weekly".
                - start_date (str): ISO timestamp for the start of the reporting window.
                - end_date (str): ISO timestamp for the end of the reporting window.
                - agent_performance (dict[str, dict[str, Any]]): Mapping from agent name to metrics, where each metric maps to a stats dict with keys:
                    - "average" (float): Average metric value over the period.
                    - "min" (float): Minimum recorded value over the period.
                    - "max" (float): Maximum recorded value over the period.
                    - "samples" (int): Number of samples used to compute the stats.
                - system_performance (dict[str, float]): Mapping from system metric name to its average value over the period.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        week_ago = (datetime.now() - timedelta(days=7)).isoformat()

        # Agent performance
        cursor.execute("""
            SELECT agent_name, metric_name, AVG(metric_value) as avg_value,
                   MIN(metric_value) as min_value, MAX(metric_value) as max_value,
                   COUNT(*) as sample_count
            FROM agent_metrics
            WHERE timestamp >= ?
            GROUP BY agent_name, metric_name
        """, (week_ago,))

        agent_stats = {}
        for row in cursor.fetchall():
            agent_name, metric_name, avg_val, min_val, max_val, count = row
            if agent_name not in agent_stats:
                agent_stats[agent_name] = {}

            agent_stats[agent_name][metric_name] = {
                "average": avg_val,
                "min": min_val,
                "max": max_val,
                "samples": count
            }

        # System performance
        cursor.execute("""
            SELECT metric_name, AVG(metric_value) as avg_value
            FROM system_metrics
            WHERE timestamp >= ?
            GROUP BY metric_name
        """, (week_ago,))

        system_stats = {}
        for row in cursor.fetchall():
            metric_name, avg_val = row
            system_stats[metric_name] = avg_val

        conn.close()

        report = {
            "period": "weekly",
            "start_date": week_ago,
            "end_date": datetime.now().isoformat(),
            "agent_performance": agent_stats,
            "system_performance": system_stats
        }

        logger.info("📊 Weekly performance report generated")
        return report

    async def generate_proposals(self, report: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Create improvement proposals from a weekly performance report and persist them for operator review.
        
        Analyzes agent and system performance metrics in `report` to produce actionable proposals (for example: slow execution time, high error rate, or high CPU usage). Each proposal is a suggestion only and is not executed automatically; proposals are saved for manual operator review and possible implementation.
        
        Parameters:
            report (dict[str, Any]): Weekly performance report containing keys like `agent_performance` (mapping agent names to metric stats) and `system_performance` (system-level aggregated metrics).
        
        Returns:
            list[dict[str, Any]]: A list of proposal objects. Each proposal contains metadata such as `id`, `type`, target scope (`agent` or `scope`), `issue`, `current_value`, `threshold`, `recommendation`, `priority`, `requires_testing`, and `created_at`.
        """
        proposals = []

        # Analyze agent performance
        for agent_name, metrics in report.get("agent_performance", {}).items():
            # Proposal 1: Slow execution time
            if "execution_time" in metrics:
                avg_time = metrics["execution_time"]["average"]
                if avg_time > 5.0:  # 5 seconds threshold
                    proposals.append({
                        "id": f"proposal_{len(proposals) + 1}",
                        "type": "performance_optimization",
                        "agent": agent_name,
                        "issue": "slow_execution",
                        "current_value": avg_time,
                        "threshold": 5.0,
                        "recommendation": f"Agent {agent_name} average execution time ({avg_time:.2f}s) exceeds threshold. Consider optimizing processing logic or increasing resource allocation.",
                        "priority": "medium",
                        "requires_testing": True,
                        "created_at": datetime.now().isoformat()
                    })

            # Proposal 2: High error rate
            if "error_rate" in metrics:
                error_rate = metrics["error_rate"]["average"]
                if error_rate > 0.05:  # 5% error rate
                    proposals.append({
                        "id": f"proposal_{len(proposals) + 1}",
                        "type": "reliability_improvement",
                        "agent": agent_name,
                        "issue": "high_error_rate",
                        "current_value": error_rate,
                        "threshold": 0.05,
                        "recommendation": f"Agent {agent_name} error rate ({error_rate:.2%}) exceeds acceptable threshold. Review error logs and add additional error handling.",
                        "priority": "high",
                        "requires_testing": True,
                        "created_at": datetime.now().isoformat()
                    })

        # System-wide proposals
        system_perf = report.get("system_performance", {})

        if "cpu_usage" in system_perf and system_perf["cpu_usage"] > 80:
            proposals.append({
                "id": f"proposal_{len(proposals) + 1}",
                "type": "resource_optimization",
                "scope": "system",
                "issue": "high_cpu_usage",
                "current_value": system_perf["cpu_usage"],
                "threshold": 80,
                "recommendation": "System CPU usage is high. Consider implementing request throttling or increasing hardware resources.",
                "priority": "medium",
                "requires_testing": False,
                "created_at": datetime.now().isoformat()
            })

        # Save proposals to file
        await self._save_proposals(proposals)

        logger.info(f"💡 Generated {len(proposals)} improvement proposals")
        return proposals

    async def _save_proposals(self, new_proposals: list[dict[str, Any]]):
        """
        Append new proposal objects to the instance proposals file, creating or updating the JSON list on disk.
        
        Appends the provided list of proposal dictionaries to any existing proposals stored at self.proposals_path, writes the combined list back to disk with indentation, and ensures the proposals file is created if it did not exist.
        
        Parameters:
            new_proposals (list[dict[str, Any]]): Proposals to append; each item is a proposal dictionary matching the stored proposal schema.
        """
        existing_proposals = []

        if self.proposals_path.exists():
            with open(self.proposals_path) as f:
                existing_proposals = json.load(f)

        # Append new proposals
        all_proposals = existing_proposals + new_proposals

        with open(self.proposals_path, "w") as f:
            json.dump(all_proposals, f, indent=2)

        logger.info(f"📝 Saved {len(new_proposals)} proposals to {self.proposals_path}")

    async def get_proposals(self, status: Optional[str] = None) -> list[dict[str, Any]]:
        """
        Return the list of saved proposals, optionally filtered by proposal `status`.
        
        Parameters:
            status (Optional[str]): If provided, only proposals whose `"status"` field equals this value are returned.
        
        Returns:
            list[dict[str, Any]]: A list of proposal objects; returns an empty list if the proposals file does not exist.
        """
        if not self.proposals_path.exists():
            return []

        with open(self.proposals_path) as f:
            proposals = json.load(f)

        if status:
            proposals = [p for p in proposals if p.get("status") == status]

        return proposals

    async def update_proposal_status(
        self,
        proposal_id: str,
        status: str,
        operator: str,
        notes: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Update the review status and metadata for a stored proposal.
        
        Parameters:
            proposal_id (str): Unique identifier of the proposal to update.
            status (str): New status to set (e.g., "approved", "rejected", "implemented").
            operator (str): Name or identifier of the operator performing the update.
            notes (Optional[str]): Optional review notes to attach to the proposal.
        
        Returns:
            result (dict): If successful, returns {"status": "updated", "proposal": <updated proposal dict>}.
                           If the proposals store is missing or the proposal id is not found, returns {"error": <message>}.
        """
        if not self.proposals_path.exists():
            return {"error": "No proposals found"}

        with open(self.proposals_path) as f:
            proposals = json.load(f)

        for proposal in proposals:
            if proposal["id"] == proposal_id:
                proposal["status"] = status
                proposal["reviewed_by"] = operator
                proposal["reviewed_at"] = datetime.now().isoformat()
                if notes:
                    proposal["review_notes"] = notes

                # Save updated proposals
                with open(self.proposals_path, "w") as f:
                    json.dump(proposals, f, indent=2)

                logger.info(f"✅ Proposal {proposal_id} updated to {status} by {operator}")
                return {"status": "updated", "proposal": proposal}

        return {"error": "Proposal not found"}

    async def get_kpi_summary(self, days: int = 7) -> dict[str, Any]:
        """
        Summarize per-agent KPIs over the most recent time window.
        
        Produces per-agent statistics computed from the 'execution_time' entries in the agent_metrics table for the past `days` days. The agent KPIs include:
        - `active_days`: number of distinct days the agent reported execution_time,
        - `total_operations`: total execution_time samples,
        - `avg_execution_time`: average execution_time for the period.
        
        Parameters:
        	days (int): Number of days to include in the summary window (default 7).
        
        Returns:
        	summary (dict): A dictionary with keys:
        		- "period_days" (int): the requested window size,
        		- "agent_kpis" (dict[str, dict]): mapping agent names to their KPI dicts,
        		- "generated_at" (str): ISO8601 timestamp when the summary was produced.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        # Agent KPIs
        cursor.execute("""
            SELECT agent_name,
                   COUNT(DISTINCT DATE(timestamp)) as active_days,
                   COUNT(*) as total_operations,
                   AVG(metric_value) as avg_value
            FROM agent_metrics
            WHERE timestamp >= ? AND metric_name = 'execution_time'
            GROUP BY agent_name
        """, (cutoff_date,))

        agent_kpis = {}
        for row in cursor.fetchall():
            agent_name, active_days, total_ops, avg_time = row
            agent_kpis[agent_name] = {
                "active_days": active_days,
                "total_operations": total_ops,
                "avg_execution_time": avg_time
            }

        conn.close()

        return {
            "period_days": days,
            "agent_kpis": agent_kpis,
            "generated_at": datetime.now().isoformat()
        }