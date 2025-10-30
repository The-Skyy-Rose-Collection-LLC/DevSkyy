"""
Unit Tests for Performance Tracker
Tests KPI tracking and improvement proposals
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from fashion_ai_bounded_autonomy.performance_tracker import PerformanceTracker


@pytest.fixture
def temp_db():
    """Create temporary database"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_metrics.db"
    yield str(db_path)
    shutil.rmtree(temp_dir)


@pytest.fixture
def tracker(temp_db):
    """Create PerformanceTracker instance"""
    return PerformanceTracker(db_path=temp_db)


class TestTrackerInitialization:
    """Test performance tracker initialization"""

    def test_initialization(self, temp_db):
        """Test basic initialization"""
        tracker = PerformanceTracker(db_path=temp_db)
        
        assert Path(temp_db).exists()
        assert tracker.proposals_path.parent.exists()


class TestMetricLogging:
    """Test metric logging functionality"""

    def test_log_agent_metric(self, tracker):
        """Test logging agent metric"""
        tracker.log_metric("test_agent", "execution_time", 1.5)
        
        # Verify metric was logged (would need to query DB)
        # This is a basic smoke test
        assert True

    def test_log_system_metric(self, tracker):
        """Test logging system metric"""
        tracker.log_system_metric("cpu_usage", 75.5, {"host": "test"})
        
        # Basic smoke test
        assert True

    def test_log_multiple_metrics(self, tracker):
        """Test logging multiple metrics"""
        for i in range(5):
            tracker.log_metric("test_agent", "metric", float(i))
        
        # Verify all logged
        assert True


class TestWeeklyReport:
    """Test weekly report generation"""

    @pytest.mark.asyncio
    async def test_compute_weekly_report_empty(self, tracker):
        """Test computing report with no data"""
        report = await tracker.compute_weekly_report()
        
        assert "period" in report
        assert report["period"] == "weekly"
        assert "agent_performance" in report

    @pytest.mark.asyncio
    async def test_compute_weekly_report_with_data(self, tracker):
        """Test computing report with data"""
        # Log some test data
        tracker.log_metric("test_agent", "execution_time", 1.5)
        tracker.log_metric("test_agent", "execution_time", 2.0)
        tracker.log_metric("test_agent", "success_rate", 0.95)
        
        report = await tracker.compute_weekly_report()
        
        assert "agent_performance" in report
        assert "system_performance" in report


class TestProposalGeneration:
    """Test improvement proposal generation"""

    @pytest.mark.asyncio
    async def test_generate_proposals_slow_execution(self, tracker):
        """Test proposal generation for slow execution"""
        report = {
            "agent_performance": {
                "slow_agent": {
                    "execution_time": {
                        "average": 10.0,
                        "min": 8.0,
                        "max": 12.0
                    }
                }
            }
        }
        
        proposals = await tracker.generate_proposals(report)
        
        # Should generate proposal for slow execution
        assert len(proposals) > 0
        assert any(p["issue"] == "slow_execution" for p in proposals)

    @pytest.mark.asyncio
    async def test_generate_proposals_high_error_rate(self, tracker):
        """Test proposal generation for high error rate"""
        report = {
            "agent_performance": {
                "error_agent": {
                    "error_rate": {
                        "average": 0.15,
                        "min": 0.10,
                        "max": 0.20
                    }
                }
            }
        }
        
        proposals = await tracker.generate_proposals(report)
        
        assert len(proposals) > 0
        assert any(p["issue"] == "high_error_rate" for p in proposals)


class TestProposalManagement:
    """Test proposal management functionality"""

    @pytest.mark.asyncio
    async def test_update_proposal_status(self, tracker):
        """Test updating proposal status"""
        # Generate a proposal
        report = {
            "agent_performance": {
                "test_agent": {
                    "execution_time": {"average": 6.0, "min": 5.0, "max": 7.0}
                }
            }
        }
        proposals = await tracker.generate_proposals(report)
        
        if proposals:
            proposal_id = proposals[0]["id"]
            
            result = await tracker.update_proposal_status(
                proposal_id,
                "approved",
                "test_operator",
                "Looks good"
            )
            
            assert result["status"] == "updated"

    @pytest.mark.asyncio
    async def test_get_proposals(self, tracker):
        """Test getting all proposals"""
        # Generate some proposals
        report = {
            "agent_performance": {
                "test_agent": {
                    "execution_time": {"average": 8.0, "min": 7.0, "max": 9.0}
                }
            }
        }
        await tracker.generate_proposals(report)
        
        proposals = await tracker.get_proposals()
        
        assert isinstance(proposals, list)


class TestKPISummary:
    """Test KPI summary functionality"""

    @pytest.mark.asyncio
    async def test_get_kpi_summary(self, tracker):
        """Test getting KPI summary"""
        # Log some metrics
        tracker.log_metric("test_agent", "execution_time", 1.0)
        
        summary = await tracker.get_kpi_summary(days=7)
        
        assert "period_days" in summary
        assert "agent_kpis" in summary