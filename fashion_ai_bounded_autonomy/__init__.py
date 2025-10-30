"""
Fashion AI Bounded Autonomy System
===================================

Local, Python-based bounded autonomous fashion AI infrastructure.
Full operator control with deterministic, logged, and human-reviewed operations.

Components:
-----------
- BoundedOrchestrator: Extends AgentOrchestrator with bounded autonomy controls
- BoundedAutonomyWrapper: Wraps agents with approval workflows
- ApprovalSystem: Human review queue management
- DataPipeline: Validated data ingestion and processing
- Watchdog: Health monitoring and recovery
- PerformanceTracker: KPI tracking and improvement proposals
- ReportGenerator: Comprehensive reporting

Quick Start:
------------
```python
from fashion_ai_bounded_autonomy import BoundedOrchestrator
from agent.modules.your_agent import YourAgent

# Create bounded orchestrator
orchestrator = BoundedOrchestrator(
    local_only=True,
    auto_approve_low_risk=True
)

# Register agent with bounded controls
agent = YourAgent("your_agent", version="1.0.0")
await orchestrator.register_agent(
    agent=agent,
    capabilities=["your_capability"],
    priority=ExecutionPriority.MEDIUM
)

# Execute task (requires approval for high-risk)
result = await orchestrator.execute_task(
    task_type="your_task",
    parameters={"param": "value"},
    required_capabilities=["your_capability"]
)
```

CLI Tools:
----------
- Approval CLI: `python -m fashion_ai_bounded_autonomy.approval_cli list`
- Recovery: `./fashion_ai_bounded_autonomy/recovery.sh`

Documentation:
--------------
See README.md for complete integration guide and examples.

License: Proprietary
Copyright © 2025 The Skyy Rose Collection LLC
"""

__version__ = "1.0.0"
__author__ = "The Skyy Rose Collection LLC"

from .approval_system import ApprovalSystem, ApprovalWorkflowType
from .bounded_autonomy_wrapper import ActionRiskLevel, BoundedAutonomyWrapper
from .bounded_orchestrator import BoundedOrchestrator
from .data_pipeline import DataPipeline
from .performance_tracker import PerformanceTracker
from .report_generator import ReportGenerator
from .watchdog import Watchdog


__all__ = [
    "ActionRiskLevel",
    "ApprovalSystem",
    "ApprovalWorkflowType",
    "BoundedAutonomyWrapper",
    "BoundedOrchestrator",
    "DataPipeline",
    "PerformanceTracker",
    "ReportGenerator",
    "Watchdog",
]
