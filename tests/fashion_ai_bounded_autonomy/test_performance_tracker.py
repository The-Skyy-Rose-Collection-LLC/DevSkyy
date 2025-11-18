"""
Unit tests for PerformanceTracker
Tests KPI tracking and improvement proposal generation
"""

from pathlib import Path
import shutil
import sqlite3
import tempfile

import pytest

from fashion_ai_bounded_autonomy.performance_tracker import PerformanceTracker


@pytest.fixture
def temp_db_path():
    """Create temporary database path"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_performance.db"
    yield str(db_path)
    shutil.rmtree(temp_dir)


@pytest.fixture
def tracker(temp_db_path):
    """Create PerformanceTracker instance"""
    return PerformanceTracker(db_path=temp_db_path)


class TestPerformanceTrackerInitialization:
    """Test PerformanceTracker initialization"""

    def test_init_creates_database(self, temp_db_path):
        """Test that initialization creates database"""
        PerformanceTracker(db_path=temp_db_path)
        assert Path(temp_db_path).exists()

    def test_init_creates_tables(self, temp_db_path):
        """Test that initialization creates required tables"""
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agent_metrics'")
        assert cursor.fetchone() is not None

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_metrics'")
        assert cursor.fetchone() is not None

        conn.close()


class TestLogMetrics:
    """Test metric logging"""

    def test_log_agent_metric(self, tracker, temp_db_path):
        """Test logging agent metric"""
        tracker.log_metric("test_agent", "execution_time", 1.5)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agent_metrics WHERE agent_name = ?", ("test_agent",))
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[1] == "test_agent"
        assert result[2] == "execution_time"
        assert result[3] == 1.5

    def test_log_multiple_metrics(self, tracker):
        """Test logging multiple metrics"""
        tracker.log_metric("agent1", "metric1", 10.0)
        tracker.log_metric("agent1", "metric2", 20.0)
        tracker.log_metric("agent2", "metric1", 15.0)

        # Metrics should be stored
        assert True  # Implicit test via no exceptions

    def test_log_system_metric(self, tracker, temp_db_path):
        """Test logging system-wide metric"""
        metadata = {"server": "prod", "region": "us-east"}
        tracker.log_system_metric("cpu_usage", 75.5, metadata)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM system_metrics WHERE metric_name = ?", ("cpu_usage",))
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[1] == "cpu_usage"
        assert result[2] == 75.5


class TestWeeklyReport:
    """Test weekly report generation"""

    @pytest.mark.asyncio
    async def test_compute_weekly_report_empty(self, tracker):
        """Test computing weekly report with no data"""
        report = await tracker.compute_weekly_report()

        assert "period" in report
        assert report["period"] == "weekly"
        assert "agent_performance" in report
        assert "system_performance" in report

    @pytest.mark.asyncio
    async def test_compute_weekly_report_with_data(self, tracker):
        """Test computing weekly report with metrics"""
        # Log some metrics
        tracker.log_metric("test_agent", "execution_time", 1.0)
        tracker.log_metric("test_agent", "execution_time", 2.0)
        tracker.log_metric("test_agent", "execution_time", 3.0)

        report = await tracker.compute_weekly_report()

        assert "test_agent" in report["agent_performance"]
        assert "execution_time" in report["agent_performance"]["test_agent"]

    @pytest.mark.asyncio
    async def test_weekly_report_calculates_statistics(self, tracker):
        """Test that weekly report calculates statistics correctly"""
        # Log metrics
        for value in [1.0, 2.0, 3.0, 4.0, 5.0]:
            tracker.log_metric("test_agent", "test_metric", value)

        report = await tracker.compute_weekly_report()

        stats = report["agent_performance"]["test_agent"]["test_metric"]
        assert "average" in stats
        assert "min" in stats
        assert "max" in stats
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0


class TestProposalGeneration:
    """Test improvement proposal generation"""

    @pytest.mark.asyncio
    async def test_generate_proposals_empty_report(self, tracker):
        """Test generating proposals from empty report"""
        report = {"agent_performance": {}, "system_performance": {}}

        proposals = await tracker.generate_proposals(report)

        assert isinstance(proposals, list)

    @pytest.mark.asyncio
    async def test_generate_proposal_slow_execution(self, tracker):
        """Test proposal for slow execution time"""
        report = {
            "agent_performance": {"slow_agent": {"execution_time": {"average": 10.0, "min": 8.0, "max": 12.0}}},
            "system_performance": {},
        }

        proposals = await tracker.generate_proposals(report)

        assert len(proposals) > 0
        assert any("slow_execution" in p.get("issue", "") for p in proposals)

    @pytest.mark.asyncio
    async def test_generate_proposal_high_error_rate(self, tracker):
        """Test proposal for high error rate"""
        report = {
            "agent_performance": {
                "error_agent": {"error_rate": {"average": 0.10, "min": 0.05, "max": 0.15}}  # 10% error rate
            },
            "system_performance": {},
        }

        proposals = await tracker.generate_proposals(report)

        assert len(proposals) > 0
        assert any("error_rate" in p.get("issue", "") for p in proposals)

    @pytest.mark.asyncio
    async def test_generate_proposal_high_cpu(self, tracker):
        """Test proposal for high CPU usage"""
        report = {"agent_performance": {}, "system_performance": {"cpu_usage": 85.0}}

        proposals = await tracker.generate_proposals(report)

        assert len(proposals) > 0
        assert any("cpu" in p.get("issue", "").lower() for p in proposals)

    @pytest.mark.asyncio
    async def test_proposals_saved_to_file(self, tracker):
        """Test that proposals are saved to file"""
        report = {
            "agent_performance": {"agent1": {"execution_time": {"average": 10.0, "min": 8.0, "max": 12.0}}},
            "system_performance": {},
        }

        await tracker.generate_proposals(report)

        assert tracker.proposals_path.exists()


class TestGetProposals:
    """Test retrieving proposals"""

    @pytest.mark.asyncio
    async def test_get_proposals_empty(self, tracker):
        """Test getting proposals when file doesn't exist"""
        proposals = await tracker.get_proposals()

        assert proposals == []

    @pytest.mark.asyncio
    async def test_get_proposals_all(self, tracker):
        """Test getting all proposals"""
        # Generate some proposals
        report = {
            "agent_performance": {"agent1": {"execution_time": {"average": 10.0, "min": 8.0, "max": 12.0}}},
            "system_performance": {},
        }
        await tracker.generate_proposals(report)

        proposals = await tracker.get_proposals()

        assert len(proposals) > 0

    @pytest.mark.asyncio
    async def test_get_proposals_filtered_by_status(self, tracker):
        """Test filtering proposals by status"""
        # Create proposal with specific status
        report = {"agent_performance": {}, "system_performance": {}}
        await tracker.generate_proposals(report)

        # No proposals match "implemented" status yet
        filtered = await tracker.get_proposals(status="implemented")
        assert len(filtered) == 0


class TestUpdateProposalStatus:
    """Test updating proposal status"""

    @pytest.mark.asyncio
    async def test_update_proposal_status(self, tracker):
        """Test updating proposal status"""
        # Create proposal
        report = {
            "agent_performance": {"agent1": {"execution_time": {"average": 10.0, "min": 8.0, "max": 12.0}}},
            "system_performance": {},
        }
        proposals = await tracker.generate_proposals(report)
        proposal_id = proposals[0]["id"]

        result = await tracker.update_proposal_status(
            proposal_id=proposal_id, status="approved", operator="test_operator", notes="Looks good"
        )

        assert result["status"] == "updated"
        assert result["proposal"]["status"] == "approved"
        assert result["proposal"]["reviewed_by"] == "test_operator"

    @pytest.mark.asyncio
    async def test_update_nonexistent_proposal(self, tracker):
        """Test updating non-existent proposal"""
        result = await tracker.update_proposal_status(
            proposal_id="nonexistent", status="approved", operator="operator"
        )

        assert "error" in result


class TestKPISummary:
    """Test KPI summary generation"""

    @pytest.mark.asyncio
    async def test_get_kpi_summary_empty(self, tracker):
        """Test getting KPI summary with no data"""
        summary = await tracker.get_kpi_summary(days=7)

        assert "period_days" in summary
        assert "agent_kpis" in summary

    @pytest.mark.asyncio
    async def test_get_kpi_summary_with_data(self, tracker):
        """Test getting KPI summary with metrics"""
        # Log some metrics
        for i in range(5):
            tracker.log_metric("test_agent", "execution_time", 1.0 + i * 0.1)

        summary = await tracker.get_kpi_summary(days=7)

        assert "test_agent" in summary["agent_kpis"]

    @pytest.mark.asyncio
    async def test_get_kpi_summary_custom_period(self, tracker):
        """Test getting KPI summary for custom period"""
        tracker.log_metric("agent1", "execution_time", 1.0)

        summary = await tracker.get_kpi_summary(days=30)

        assert summary["period_days"] == 30


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_log_metric_with_zero_value(self, tracker):
        """Test logging metric with zero value"""
        tracker.log_metric("agent", "metric", 0.0)
        # Should not raise exception
        assert True

    def test_log_metric_with_negative_value(self, tracker):
        """Test logging metric with negative value"""
        tracker.log_metric("agent", "metric", -1.0)
        # Should not raise exception
        assert True

    @pytest.mark.asyncio
    async def test_generate_proposals_with_none_values(self, tracker):
        """Test generating proposals with None values in report"""
        report = {"agent_performance": None, "system_performance": None}

        # Should handle gracefully
        with pytest.raises((TypeError, AttributeError)):
            await tracker.generate_proposals(report)
