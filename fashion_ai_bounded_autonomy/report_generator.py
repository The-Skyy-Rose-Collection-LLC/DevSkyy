"""
LAYER 9 — OUTPUT AND REPORTING
Generate organized, human-readable reports for operator review
"""

import csv
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generate comprehensive reports for bounded autonomy system.

    Output Structure:
    /output/
        ├── summaries/     - Daily/weekly/monthly summaries
        ├── metrics/       - Performance metrics
        ├── validation/    - Data validation reports
        └── recommendations/ - System improvement proposals
    """

    def __init__(self, output_path: str = "fashion_ai_bounded_autonomy/output"):
        self.output_path = Path(output_path)

        # Create output directories
        self.summaries_path = self.output_path / "summaries"
        self.metrics_path = self.output_path / "metrics"
        self.validation_path = self.output_path / "validation"
        self.recommendations_path = self.output_path / "recommendations"

        for path in [self.summaries_path, self.metrics_path, self.validation_path, self.recommendations_path]:
            path.mkdir(parents=True, exist_ok=True)

        logger.info("📊 Report generator initialized")

    async def generate_daily_summary(
        self, orchestrator_status: dict[str, Any], performance_data: dict[str, Any], approval_stats: dict[str, Any]
    ) -> Path:
        """Generate daily operations summary"""
        timestamp = datetime.now()
        report_date = timestamp.strftime("%Y-%m-%d")
        report_file = self.summaries_path / f"daily_summary_{report_date}.md"

        report = f"""# Daily Summary - {report_date}
Generated: {timestamp.isoformat()}

## System Status

**Orchestrator Health:** {orchestrator_status.get('system_status', 'unknown')}
**Registered Agents:** {orchestrator_status.get('registered_agents', 0)}
**Active Tasks:** {orchestrator_status.get('active_tasks', 0)}
**Total Tasks:** {orchestrator_status.get('total_tasks', 0)}

## Bounded Autonomy Controls

**Emergency Stop:** {'🔴 ACTIVE' if orchestrator_status.get('bounded_autonomy', {}).get('system_controls', {}).get('emergency_stop') else '✅ Inactive'}
**System Paused:** {'⏸️ YES' if orchestrator_status.get('bounded_autonomy', {}).get('system_controls', {}).get('paused') else '▶️ NO'}
**Local Only Mode:** {'🔒 ENABLED' if orchestrator_status.get('bounded_autonomy', {}).get('system_controls', {}).get('local_only') else '⚠️ DISABLED'}

## Approval Queue

**Pending Approvals:** {approval_stats.get('pending', 0)}
**Approved Today:** {approval_stats.get('approved_today', 0)}
**Rejected Today:** {approval_stats.get('rejected_today', 0)}

## Agent Performance

"""

        # Add agent metrics
        for agent_name, metrics in performance_data.get("agent_performance", {}).items():
            report += f"### {agent_name}\n\n"
            for metric_name, stats in metrics.items():
                report += f"- **{metric_name}:** {stats.get('average', 0):.2f} "
                report += f"(min: {stats.get('min', 0):.2f}, max: {stats.get('max', 0):.2f})\n"
            report += "\n"

        report += """
## Next Steps

1. Review pending approvals: `python -m fashion_ai_bounded_autonomy.approval_cli list`
2. Check system health: Review agent status above
3. Address any flagged issues
4. Review weekly report for trends

---
*This report is automatically generated. All timestamps are in ISO 8601 format.*
"""

        with open(report_file, "w") as f:
            f.write(report)

        logger.info(f"✅ Daily summary generated: {report_file}")
        return report_file

    async def generate_weekly_report(
        self, performance_data: dict[str, Any], incidents: list[dict[str, Any]], proposals: list[dict[str, Any]]
    ) -> Path:
        """Generate weekly performance and improvement report"""
        timestamp = datetime.now()
        report_date = timestamp.strftime("%Y-W%W")  # Year-Week number
        report_file = self.summaries_path / f"weekly_report_{report_date}.md"

        report = f"""# Weekly Report - Week {timestamp.strftime('%W, %Y')}
Generated: {timestamp.isoformat()}

## Executive Summary

**Reporting Period:** {performance_data.get('start_date', 'N/A')} to {performance_data.get('end_date', 'N/A')}
**Total Incidents:** {len(incidents)}
**Improvement Proposals:** {len(proposals)}

## Performance Trends

"""

        # Agent performance
        for agent_name, metrics in performance_data.get("agent_performance", {}).items():
            report += f"### {agent_name}\n\n"
            report += "| Metric | Average | Min | Max | Samples |\n"
            report += "|--------|---------|-----|-----|\n"

            for metric_name, stats in metrics.items():
                report += f"| {metric_name} | {stats['average']:.2f} | {stats['min']:.2f} | {stats['max']:.2f} | {stats['samples']} |\n"

            report += "\n"

        # Incidents
        report += "## Incidents\n\n"
        if incidents:
            for idx, incident in enumerate(incidents, 1):
                report += f"{idx}. **{incident.get('type', 'unknown')}** - {incident.get('agent_name', 'system')}\n"
                report += f"   - Timestamp: {incident.get('timestamp', 'N/A')}\n"
                report += f"   - Status: {incident.get('status', 'unresolved')}\n\n"
        else:
            report += "*No incidents this week.*\n\n"

        # Improvement proposals
        report += "## Improvement Proposals\n\n"
        if proposals:
            for proposal in proposals:
                report += f"### Proposal {proposal.get('id', 'N/A')}\n\n"
                report += f"**Type:** {proposal.get('type', 'N/A')}\n"
                report += f"**Priority:** {proposal.get('priority', 'N/A')}\n"
                report += f"**Agent:** {proposal.get('agent', 'system')}\n\n"
                report += f"**Recommendation:**\n{proposal.get('recommendation', 'No recommendation provided')}\n\n"
                report += f"**Status:** {proposal.get('status', 'pending_review')}\n\n"
                report += "---\n\n"
        else:
            report += "*No proposals this week - system performing optimally.*\n\n"

        report += """
## Action Items

1. Review and address high-priority proposals
2. Investigate any unresolved incidents
3. Monitor trending performance issues
4. Update configurations as approved

---
*Generated by Fashion AI Bounded Autonomy System*
"""

        with open(report_file, "w") as f:
            f.write(report)

        logger.info(f"✅ Weekly report generated: {report_file}")
        return report_file

    async def export_metrics_csv(self, metrics_data: dict[str, Any], filename: str | None = None) -> Path:
        """Export metrics to CSV for analysis"""
        if not filename:
            filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        csv_file = self.metrics_path / filename

        # Flatten metrics data
        rows = []
        for agent_name, metrics in metrics_data.get("agent_kpis", {}).items():
            for metric_name, value in metrics.items():
                rows.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "agent": agent_name,
                        "metric": metric_name,
                        "value": value,
                    }
                )

        if rows:
            with open(csv_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "agent", "metric", "value"])
                writer.writeheader()
                writer.writerows(rows)

            logger.info(f"✅ Metrics exported to CSV: {csv_file}")
        else:
            logger.warning("⚠️  No metrics data to export")

        return csv_file

    async def generate_validation_report(self, validation_results: list[dict[str, Any]]) -> Path:
        """Generate data validation report"""
        timestamp = datetime.now()
        report_file = self.validation_path / f"validation_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"

        report = {
            "timestamp": timestamp.isoformat(),
            "total_validations": len(validation_results),
            "passed": sum(1 for r in validation_results if r.get("status") == "validated"),
            "failed": sum(1 for r in validation_results if r.get("status") == "quarantined"),
            "details": validation_results,
        }

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"✅ Validation report generated: {report_file}")
        return report_file

    async def generate_recommendations_report(self, proposals: list[dict[str, Any]]) -> Path:
        """Generate formatted recommendations report"""
        timestamp = datetime.now()
        report_file = self.recommendations_path / f"recommendations_{timestamp.strftime('%Y%m%d')}.md"

        report = f"""# System Improvement Recommendations
Generated: {timestamp.isoformat()}

## Summary

**Total Proposals:** {len(proposals)}
**Pending Review:** {sum(1 for p in proposals if p.get('status') == 'pending')}
**Approved:** {sum(1 for p in proposals if p.get('status') == 'approved')}
**Implemented:** {sum(1 for p in proposals if p.get('status') == 'implemented')}

## Proposals by Priority

"""

        # Group by priority
        by_priority = {"high": [], "medium": [], "low": []}
        for proposal in proposals:
            priority = proposal.get("priority", "medium")
            by_priority[priority].append(proposal)

        for priority in ["high", "medium", "low"]:
            proposals_list = by_priority[priority]
            if proposals_list:
                report += f"### {priority.upper()} Priority ({len(proposals_list)})\n\n"

                for proposal in proposals_list:
                    status_icon = {"pending": "⏳", "approved": "✅", "rejected": "⛔", "implemented": "🎉"}.get(
                        proposal.get("status", "pending"), "❓"
                    )

                    report += f"{status_icon} **{proposal.get('id', 'N/A')}** - {proposal.get('type', 'unknown')}\n"
                    report += f"   {proposal.get('recommendation', 'No details')}\n\n"

        report += """
## Action Required

Review pending proposals and update status using:
```bash
python -c "
from fashion_ai_bounded_autonomy.performance_tracker import PerformanceTracker
import asyncio

async def main():
    tracker = PerformanceTracker()
    await tracker.update_proposal_status(
        'proposal_id',
        'approved',  # or 'rejected'
        'operator_name',
        'Optional notes'
    )

asyncio.run(main())
"
```

---
*All recommendations require manual operator review and approval.*
"""

        with open(report_file, "w") as f:
            f.write(report)

        logger.info(f"✅ Recommendations report generated: {report_file}")
        return report_file
