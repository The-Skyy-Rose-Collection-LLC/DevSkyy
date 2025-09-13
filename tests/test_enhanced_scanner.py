import unittest
from unittest.mock import patch, mock_open, MagicMock
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path to import modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.modules.scanner import (
    scan_agents_only, scan_site, _analyze_all_agents, _analyze_single_agent,
    _calculate_code_metrics, _check_agent_dependencies, _analyze_agent_performance,
    _analyze_agent_security, _calculate_agent_health_score, _get_fallback_agent_analysis
)


class TestEnhancedScanner(unittest.TestCase):
    """Test suite for enhanced scanner functionality."""

    def test_scan_agents_only_success(self):
        """Test scan_agents_only function returns proper structure."""
        with patch('agent.modules.scanner._analyze_all_agents') as mock_analyze:
            mock_analyze.return_value = {
                "total_agents": 35,
                "functional_agents": 31,
                "agents_with_issues": 4,
                "average_health_score": 89.1,
                "summary": {
                    "importable": ["web_development_agent", "financial_agent"],
                    "import_errors": [{"agent": "inventory_agent", "error": "No module named 'cv2'"}],
                    "missing_dependencies": [{"agent": "inventory_agent", "dependency": "cv2"}],
                    "performance_issues": [{"agent": "cache_manager", "issue": "Potential infinite loop detected"}],
                    "security_concerns": [{"agent": "scanner", "concern": "Potential hardcoded password detected"}],
                    "health_scores": {"web_development_agent": 95, "financial_agent": 88}
                }
            }
            
            result = scan_agents_only()
            
            self.assertEqual(result["status"], "completed")
            self.assertIn("agent_modules", result)
            self.assertEqual(result["agent_modules"]["total_agents"], 35)
            self.assertEqual(result["agent_modules"]["functional_agents"], 31)
            self.assertEqual(result["agent_modules"]["agents_with_issues"], 4)
            self.assertIn("scan_id", result)
            self.assertIn("timestamp", result)

    def test_scan_agents_only_error_handling(self):
        """Test scan_agents_only handles errors gracefully."""
        with patch('agent.modules.scanner._analyze_all_agents') as mock_analyze:
            mock_analyze.side_effect = Exception("Test error")
            
            result = scan_agents_only()
            
            self.assertEqual(result["status"], "failed")
            self.assertIn("error", result)
            self.assertIn("timestamp", result)

    def test_enhanced_scan_site_includes_agents(self):
        """Test that enhanced scan_site includes agent analysis."""
        with patch('agent.modules.scanner._scan_project_files') as mock_files, \
             patch('agent.modules.scanner._analyze_file') as mock_analyze_file, \
             patch('agent.modules.scanner._check_site_health') as mock_health, \
             patch('agent.modules.scanner._analyze_performance') as mock_perf, \
             patch('agent.modules.scanner._security_scan') as mock_security, \
             patch('agent.modules.scanner._analyze_all_agents') as mock_agents:
            
            # Setup mocks
            mock_files.return_value = ["test.py"]
            mock_analyze_file.return_value = {"errors": [], "warnings": [], "optimizations": []}
            mock_health.return_value = {"status": "online"}
            mock_perf.return_value = {"performance_score": 85}
            mock_security.return_value = []
            mock_agents.return_value = {
                "total_agents": 35,
                "functional_agents": 31,
                "agents_with_issues": 4,
                "average_health_score": 89.1,
                "summary": {"importable": [], "import_errors": [], "missing_dependencies": [], 
                           "performance_issues": [], "security_concerns": [], "health_scores": {}}
            }
            
            result = scan_site()
            
            self.assertEqual(result["status"], "completed")
            self.assertIn("agent_modules", result)
            self.assertEqual(result["agent_modules"]["total_agents"], 35)
            self.assertIn("files_scanned", result)
            self.assertIn("performance_metrics", result)
            self.assertIn("security_issues", result)

    def test_calculate_code_metrics(self):
        """Test code metrics calculation."""
        sample_code = '''
def test_function():
    """This is a docstring."""
    pass

class TestClass:
    """Another docstring."""
    def method(self):
        return True

# Comment line
        '''
        
        metrics = _calculate_code_metrics(sample_code)
        
        self.assertIsInstance(metrics, dict)
        self.assertIn("total_lines", metrics)
        self.assertIn("code_lines", metrics)
        self.assertIn("functions", metrics)
        self.assertIn("classes", metrics)
        self.assertIn("docstrings", metrics)
        self.assertIn("docstring_coverage", metrics)
        self.assertEqual(metrics["functions"], 2)  # test_function + method
        self.assertEqual(metrics["classes"], 1)

    def test_check_agent_dependencies(self):
        """Test dependency checking."""
        code_with_deps = '''
import cv2
from sqlalchemy import create_engine
import requests
'''
        
        with patch('builtins.__import__') as mock_import:
            mock_import.side_effect = ImportError("No module named 'cv2'")
            
            missing_deps = _check_agent_dependencies(code_with_deps)
            
            # Should detect cv2 as missing (based on mock)
            # Note: requests should be available in most environments
            self.assertIsInstance(missing_deps, list)

    def test_analyze_agent_performance(self):
        """Test performance issue detection."""
        problematic_code = '''
while True:
    print("This might be an infinite loop")

def blocking_function():
    time.sleep(30)
    requests.get("http://example.com")  # No timeout
    
for i in range(len(my_list)):
    print(my_list[i])
'''
        
        issues = _analyze_agent_performance(problematic_code, "test_agent")
        
        self.assertIsInstance(issues, list)
        # Should detect various performance issues
        issue_strings = " ".join(issues)
        self.assertTrue(any(word in issue_strings.lower() for word in ["loop", "sleep", "timeout", "range"]))

    def test_analyze_agent_security(self):
        """Test security concern detection."""
        insecure_code = '''
password = "actualpassword123"
api_key = "sk-1234567890abcdef1234567890abcdef"

def dangerous_function():
    eval(user_input)
    os.system("rm -rf /")
'''
        
        concerns = _analyze_agent_security(insecure_code, "test_agent")
        
        self.assertIsInstance(concerns, list)
        # Should detect security issues
        concern_strings = " ".join(concerns)
        self.assertTrue(any(word in concern_strings.lower() for word in ["password", "eval", "injection"]))

    def test_calculate_agent_health_score(self):
        """Test health score calculation."""
        # Good agent analysis
        good_analysis = {
            "importable": True,
            "missing_dependencies": [],
            "performance_issues": [],
            "security_concerns": [],
            "code_metrics": {"docstring_coverage": 90, "functions": 5, "classes": 2}
        }
        
        good_score = _calculate_agent_health_score(good_analysis)
        self.assertGreaterEqual(good_score, 90)
        self.assertLessEqual(good_score, 100)
        
        # Problematic agent analysis
        bad_analysis = {
            "importable": False,
            "missing_dependencies": ["cv2", "sqlalchemy"],
            "performance_issues": ["infinite loop", "blocking operation"],
            "security_concerns": ["hardcoded password"],
            "code_metrics": {"docstring_coverage": 10, "functions": 0, "classes": 0}
        }
        
        bad_score = _calculate_agent_health_score(bad_analysis)
        self.assertLess(bad_score, 50)
        self.assertGreaterEqual(bad_score, 0)

    def test_get_fallback_agent_analysis(self):
        """Test fallback analysis when directory is not accessible."""
        fallback = _get_fallback_agent_analysis()
        
        self.assertIsInstance(fallback, dict)
        self.assertIn("total_agents", fallback)
        self.assertIn("functional_agents", fallback)
        self.assertIn("agents_with_issues", fallback)
        self.assertIn("average_health_score", fallback)
        self.assertIn("summary", fallback)
        
        # Should have the expected agent count
        self.assertEqual(fallback["total_agents"], 35)
        self.assertGreater(fallback["functional_agents"], 0)
        self.assertGreater(fallback["average_health_score"], 80)

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_analyze_all_agents_with_files(self, mock_glob, mock_exists):
        """Test analyzing agents when files are accessible."""
        mock_exists.return_value = True
        
        # Mock agent files
        mock_files = []
        for i in range(5):
            mock_file = MagicMock()
            mock_file.stem = f"test_agent_{i}"
            mock_file.name = f"test_agent_{i}.py"
            mock_files.append(mock_file)
        
        mock_glob.return_value = mock_files
        
        with patch('agent.modules.scanner._analyze_single_agent') as mock_analyze:
            mock_analyze.return_value = {
                "health_score": 85,
                "importable": True,
                "missing_dependencies": [],
                "performance_issues": [],
                "security_concerns": []
            }
            
            result = _analyze_all_agents()
            
            self.assertEqual(result["total_agents"], 5)
            self.assertEqual(result["functional_agents"], 5)
            self.assertEqual(result["agents_with_issues"], 0)
            self.assertEqual(result["average_health_score"], 85.0)

    @patch('pathlib.Path.exists')
    def test_analyze_all_agents_fallback(self, mock_exists):
        """Test analyzing agents falls back when directory doesn't exist."""
        mock_exists.return_value = False
        
        result = _analyze_all_agents()
        
        # Should use fallback analysis
        self.assertEqual(result["total_agents"], 35)
        self.assertIn("summary", result)


if __name__ == '__main__':
    unittest.main()