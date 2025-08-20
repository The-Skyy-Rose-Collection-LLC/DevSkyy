import importlib
import sys
import types
from pathlib import Path
from unittest.mock import patch
from typing import Dict, Any, List, Optional

from fastapi.testclient import TestClient


def test_run_endpoint_calls_functions_in_sequence():
    """TODO: Add docstring for test_run_endpoint_calls_functions_in_sequence."""
    modules = {
        "agent": types.ModuleType("agent"),
        "agent.modules": types.ModuleType("agent.modules"),
        "agent.modules.scanner": types.ModuleType("agent.modules.scanner"),
        "agent.modules.fixer": types.ModuleType("agent.modules.fixer"),
        "agent.scheduler": types.ModuleType("agent.scheduler"),
        "agent.scheduler.cron": types.ModuleType("agent.scheduler.cron"),
        "agent.git_commit": types.ModuleType("agent.git_commit"),
    }
    sys.modules.update(modules)
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    call_order = []

    def scan_side_effect():
        call_order.append("scan")
        return "raw"

    def fix_side_effect(_):
        call_order.append("fix")
        return "fixed"

    def commit_side_effect(_):
        call_order.append("commit")

    def schedule_side_effect():
        call_order.append("schedule")

    with patch("agent.modules.scanner.scan_site", side_effect=scan_side_effect, create=True) as mock_scan, \
            patch("agent.modules.fixer.fix_code", side_effect=fix_side_effect, create=True) as mock_fix, \
            patch("agent.git_commit.commit_fixes", side_effect=commit_side_effect, create=True) as mock_commit, \
            patch("agent.scheduler.cron.schedule_hourly_job", side_effect=schedule_side_effect, create=True) as mock_schedule:
        main = importlib.import_module("main")
        importlib.reload(main)
        client = TestClient(main.app)
        response = client.post("/run")

    assert response.json() == {"status": "completed"}
    assert call_order == ["scan", "fix", "commit", "schedule"]
    mock_scan.assert_called_once_with()
    mock_fix.assert_called_once_with("raw")
    mock_commit.assert_called_once_with("fixed")
    mock_schedule.assert_called_once_with()
