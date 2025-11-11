"""
Unit tests for ReportGenerator
Tests report generation and formatting
"""

import unittest
import pytest
import tempfile
import shutil

from fashion_ai_bounded_autonomy.report_generator import ReportGenerator


@pytest.fixture
def temp_output_path():
    """Create temporary output path"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def report_gen(temp_output_path):
    """Create ReportGenerator instance"""
    return ReportGenerator(output_path=temp_output_path)


class TestReportGeneratorInitialization(unittest.TestCase):
    """Test ReportGenerator initialization"""

    def test_init_creates_directories(self, report_gen):
        """Test that initialization creates output directories"""
        self.assertTrue(report_gen.summaries_path.exists())
        self.assertTrue(report_gen.metrics_path.exists())
        self.assertTrue(report_gen.validation_path.exists())
        self.assertTrue(report_gen.recommendations_path.exists())


class TestDailySummary(unittest.TestCase):
    """Test daily summary generation"""

    @pytest.mark.asyncio
    async def test_generate_daily_summary(self, report_gen):
        """Test generating daily summary"""
        orchestrator_status = {
            "system_status": "healthy",
            "registered_agents": 5,
            "active_tasks": 2,
            "total_tasks": 10,
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
                "agent1": {
                    "execution_time": {"average": 1.5, "min": 1.0, "max": 2.0}
                }
            }
        }
        
        approval_stats = {
            "pending": 3,
            "approved_today": 5,
            "rejected_today": 1
        }
        
        report_file = await report_gen.generate_daily_summary(
            orchestrator_status, performance_data, approval_stats
        )
        
        self.assertTrue(report_file.exists())
        self.assertEqual(report_file.suffix, ".md")

    @pytest.mark.asyncio
    async def test_daily_summary_includes_key_sections(self, report_gen):
        """Test that daily summary includes all key sections"""
        orchestrator_status = {"system_status": "healthy", "registered_agents": 0}
        performance_data = {"agent_performance": {}}
        approval_stats = {"pending": 0}
        
        report_file = await report_gen.generate_daily_summary(
            orchestrator_status, performance_data, approval_stats
        )
        
        content = report_file.read_text()
        self.assertIn("System Status", content)
        self.assertIn("Bounded Autonomy Controls", content)
        self.assertIn("Approval Queue", content)


class TestWeeklyReport(unittest.TestCase):
    """Test weekly report generation"""

    @pytest.mark.asyncio
    async def test_generate_weekly_report(self, report_gen):
        """Test generating weekly report"""
        performance_data = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-07",
            "agent_performance": {
                "agent1": {
                    "metric1": {"average": 1.5, "min": 1.0, "max": 2.0, "samples": 100}
                }
            }
        }
        
        incidents = [
            {"type": "agent_failure", "agent_name": "agent1", "timestamp": "2024-01-01", "status": "resolved"}
        ]
        
        proposals = [
            {"id": "prop1", "type": "optimization", "priority": "medium", "agent": "agent1", "recommendation": "Test"}
        ]
        
        report_file = await report_gen.generate_weekly_report(
            performance_data, incidents, proposals
        )
        
        self.assertTrue(report_file.exists())
        self.assertEqual(report_file.suffix, ".md")

    @pytest.mark.asyncio
    async def test_weekly_report_with_no_incidents(self, report_gen):
        """Test weekly report with no incidents"""
        performance_data = {"agent_performance": {}}
        incidents = []
        proposals = []
        
        report_file = await report_gen.generate_weekly_report(
            performance_data, incidents, proposals
        )
        
        content = report_file.read_text()
        self.assertIn("No incidents", content)


class TestMetricsExport(unittest.TestCase):
    """Test metrics export to CSV"""

    @pytest.mark.asyncio
    async def test_export_metrics_csv(self, report_gen):
        """Test exporting metrics to CSV"""
        metrics_data = {
            "agent_kpis": {
                "agent1": {
                    "active_days": 7,
                    "total_operations": 100,
                    "avg_execution_time": 1.5
                }
            }
        }
        
        csv_file = await report_gen.export_metrics_csv(metrics_data)
        
        self.assertTrue(csv_file.exists())
        self.assertEqual(csv_file.suffix, ".csv")

    @pytest.mark.asyncio
    async def test_export_metrics_csv_empty_data(self, report_gen):
        """Test exporting empty metrics data"""
        metrics_data = {"agent_kpis": {}}
        
        csv_file = await report_gen.export_metrics_csv(metrics_data)
        
        # Should handle empty data gracefully
        self.assertTrue(csv_file.exists())


class TestValidationReport(unittest.TestCase):
    """Test validation report generation"""

    @pytest.mark.asyncio
    async def test_generate_validation_report(self, report_gen):
        """Test generating validation report"""
        validation_results = [
            {"status": "validated", "file": "file1.csv"},
            {"status": "quarantined", "file": "file2.csv", "errors": ["missing_field"]}
        ]
        
        report_file = await report_gen.generate_validation_report(validation_results)
        
        self.assertTrue(report_file.exists())
        self.assertEqual(report_file.suffix, ".json")

    @pytest.mark.asyncio
    async def test_validation_report_calculates_summary(self, report_gen):
        """Test that validation report includes summary statistics"""
        validation_results = [
            {"status": "validated"},
            {"status": "validated"},
            {"status": "quarantined"}
        ]
        
        report_file = await report_gen.generate_validation_report(validation_results)
        
        import json
        with open(report_file) as f:
            report = json.load(f)
        
        self.assertEqual(report["total_validations"], 3)
        self.assertEqual(report["passed"], 2)
        self.assertEqual(report["failed"], 1)


class TestRecommendationsReport(unittest.TestCase):
    """Test recommendations report generation"""

    @pytest.mark.asyncio
    async def test_generate_recommendations_report(self, report_gen):
        """Test generating recommendations report"""
        proposals = [
            {"id": "prop1", "type": "optimization", "priority": "high", "recommendation": "Test", "status": "pending"},
            {"id": "prop2", "type": "fix", "priority": "medium", "recommendation": "Test2", "status": "approved"}
        ]
        
        report_file = await report_gen.generate_recommendations_report(proposals)
        
        self.assertTrue(report_file.exists())
        self.assertEqual(report_file.suffix, ".md")

    @pytest.mark.asyncio
    async def test_recommendations_report_groups_by_priority(self, report_gen):
        """Test that recommendations are grouped by priority"""
        proposals = [
            {"id": "p1", "priority": "high", "type": "test", "recommendation": "Fix1"},
            {"id": "p2", "priority": "low", "type": "test", "recommendation": "Fix2"},
            {"id": "p3", "priority": "high", "type": "test", "recommendation": "Fix3"}
        ]
        
        report_file = await report_gen.generate_recommendations_report(proposals)
        
        content = report_file.read_text()
        self.assertIn("HIGH Priority", content)
        self.assertIn("LOW Priority", content)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases"""

    @pytest.mark.asyncio
    async def test_generate_report_with_empty_data(self, report_gen):
        """Test generating reports with empty data"""
        orchestrator_status = {}
        performance_data = {}
        approval_stats = {}
        
        # Should not raise exception
        report_file = await report_gen.generate_daily_summary(
            orchestrator_status, performance_data, approval_stats
        )
        
        self.assertTrue(report_file.exists())

    @pytest.mark.asyncio
    async def test_export_csv_with_custom_filename(self, report_gen):
        """Test exporting CSV with custom filename"""
        metrics_data = {"agent_kpis": {"agent1": {"metric": 1.0}}}
        
        csv_file = await report_gen.export_metrics_csv(metrics_data, "custom.csv")
        
        self.assertEqual(csv_file.name, "custom.csv")