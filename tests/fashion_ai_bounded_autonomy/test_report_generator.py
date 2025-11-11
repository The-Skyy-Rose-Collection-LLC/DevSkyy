"""
Unit Tests for Report Generator
Tests report generation functionality
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from fashion_ai_bounded_autonomy.report_generator import ReportGenerator


@pytest.fixture
def temp_output():
    """
    Create a temporary directory for test output and remove it when the fixture tears down.
    
    The fixture yields the directory path to the test; the directory is deleted after the test using the fixture completes.
    
    Returns:
        temp_dir (str): Path to the created temporary directory; removed during fixture teardown.
    """
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def generator(temp_output):
    """
    Create a ReportGenerator configured to use the given temporary output directory.
    
    Parameters:
        temp_output (pathlike): Path to a temporary directory to store generated reports.
    
    Returns:
        ReportGenerator: An instance of ReportGenerator with its output_path set to `temp_output`.
    """
    return ReportGenerator(output_path=temp_output)


class TestReportGeneratorInitialization:
    """Test report generator initialization"""

    def test_initialization(self, temp_output):
        """
        Verify that initializing ReportGenerator with an output path creates the expected output subdirectories.
        
        Asserts that summaries_path, metrics_path, validation_path, and recommendations_path exist under the configured output path.
        """
        gen = ReportGenerator(output_path=temp_output)
        
        assert gen.summaries_path.exists()
        assert gen.metrics_path.exists()
        assert gen.validation_path.exists()
        assert gen.recommendations_path.exists()


class TestDailySummary:
    """Test daily summary generation"""

    @pytest.mark.asyncio
    async def test_generate_daily_summary(self, generator):
        """Test generating daily summary"""
        orchestrator_status = {
            "system_status": "healthy",
            "registered_agents": 3,
            "active_tasks": 5,
            "bounded_autonomy": {
                "system_controls": {
                    "emergency_stop": False,
                    "paused": False,
                    "local_only": True
                }
            }
        }
        
        performance_data = {
            "agent_performance": {
                "test_agent": {
                    "execution_time": {"average": 1.5, "min": 1.0, "max": 2.0}
                }
            }
        }
        
        approval_stats = {
            "pending": 2,
            "approved_today": 5,
            "rejected_today": 1
        }
        
        report_path = await generator.generate_daily_summary(
            orchestrator_status,
            performance_data,
            approval_stats
        )
        
        assert report_path.exists()
        assert report_path.suffix == ".md"


class TestWeeklyReport:
    """Test weekly report generation"""

    @pytest.mark.asyncio
    async def test_generate_weekly_report(self, generator):
        """Test generating weekly report"""
        performance_data = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-07",
            "agent_performance": {}
        }
        
        incidents = [
            {"type": "error", "agent_name": "test_agent", "timestamp": "2024-01-02"}
        ]
        
        proposals = [
            {
                "id": "prop_1",
                "type": "optimization",
                "agent": "test_agent",
                "priority": "medium",
                "recommendation": "Test recommendation"
            }
        ]
        
        report_path = await generator.generate_weekly_report(
            performance_data,
            incidents,
            proposals
        )
        
        assert report_path.exists()


class TestMetricsExport:
    """Test metrics export functionality"""

    @pytest.mark.asyncio
    async def test_export_metrics_csv(self, generator):
        """Test exporting metrics to CSV"""
        metrics_data = {
            "agent_kpis": {
                "test_agent": {
                    "execution_time": 1.5,
                    "success_rate": 0.95
                }
            }
        }
        
        csv_path = await generator.export_metrics_csv(metrics_data)
        
        assert csv_path.exists()
        assert csv_path.suffix == ".csv"


class TestValidationReport:
    """Test validation report generation"""

    @pytest.mark.asyncio
    async def test_generate_validation_report(self, generator):
        """Test generating validation report"""
        validation_results = [
            {"status": "validated", "file": "test1.csv"},
            {"status": "quarantined", "file": "test2.csv"}
        ]
        
        report_path = await generator.generate_validation_report(validation_results)
        
        assert report_path.exists()
        assert report_path.suffix == ".json"


class TestRecommendationsReport:
    """Test recommendations report generation"""

    @pytest.mark.asyncio
    async def test_generate_recommendations_report(self, generator):
        """Test generating recommendations report"""
        proposals = [
            {
                "id": "prop_1",
                "type": "performance",
                "priority": "high",
                "recommendation": "Test rec",
                "status": "pending"
            }
        ]
        
        report_path = await generator.generate_recommendations_report(proposals)
        
        assert report_path.exists()
        assert report_path.suffix == ".md"