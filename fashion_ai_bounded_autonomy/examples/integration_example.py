#!/usr/bin/env python3
"""
Complete Integration Example
Demonstrates how to integrate existing DevSkyy agents with Bounded Autonomy System
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fashion_ai_bounded_autonomy import (
    BoundedOrchestrator,
    ApprovalSystem,
    DataPipeline,
    PerformanceTracker,
    ReportGenerator
)
from agent.orchestrator import ExecutionPriority
from agent.modules.base_agent import BaseAgent


# Example: Create a simple fashion agent
class SimpleFashionAgent(BaseAgent):
    """Simple fashion agent for demonstration"""

    async def initialize(self) -> bool:
        """Initialize agent"""
        self.status = self.status.HEALTHY if self.status != self.status.FAILED else self.status
        return True

    async def execute_core_function(self, **kwargs) -> dict:
        """Core agent functionality"""
        task = kwargs.get("task", "unknown")

        if task == "analyze_trend":
            return {
                "status": "success",
                "trend": "sustainable_fashion",
                "confidence": 0.92,
                "data_points": 1500
            }
        elif task == "generate_design":
            return {
                "status": "success",
                "design_id": "design_001",
                "style": kwargs.get("style", "modern"),
                "season": kwargs.get("season", "spring")
            }
        else:
            return {"status": "error", "message": f"Unknown task: {task}"}


async def main():
    """Main integration example"""
    print("=" * 70)
    print("FASHION AI BOUNDED AUTONOMY - INTEGRATION EXAMPLE")
    print("=" * 70)
    print()

    # ========================================
    # 1. Create Bounded Orchestrator
    # ========================================
    print("1️⃣  Creating Bounded Orchestrator...")
    orchestrator = BoundedOrchestrator(
        local_only=True,
        auto_approve_low_risk=True
    )
    print("   ✅ Orchestrator created\n")

    # ========================================
    # 2. Initialize Supporting Systems
    # ========================================
    print("2️⃣  Initializing supporting systems...")
    approval_system = ApprovalSystem()
    data_pipeline = DataPipeline()
    performance_tracker = PerformanceTracker()
    report_generator = ReportGenerator()
    print("   ✅ Systems initialized\n")

    # ========================================
    # 3. Register Agents with Bounded Controls
    # ========================================
    print("3️⃣  Registering agents with bounded controls...")

    # Create and register designer agent
    designer_agent = SimpleFashionAgent("designer_agent", version="1.0.0")
    await orchestrator.register_agent(
        agent=designer_agent,
        capabilities=["trend_analysis", "design_generation"],
        priority=ExecutionPriority.MEDIUM
    )
    print("   ✅ Designer agent registered")

    # Create and register commerce agent
    commerce_agent = SimpleFashionAgent("commerce_agent", version="1.0.0")
    await orchestrator.register_agent(
        agent=commerce_agent,
        capabilities=["product_management", "inventory_optimization"],
        priority=ExecutionPriority.HIGH
    )
    print("   ✅ Commerce agent registered\n")

    # ========================================
    # 4. Execute Low-Risk Task (Auto-Approved)
    # ========================================
    print("4️⃣  Executing low-risk task (auto-approved)...")
    result = await orchestrator.execute_task(
        task_type="analyze_trend",
        parameters={"task": "analyze_trend", "category": "sustainable"},
        required_capabilities=["trend_analysis"],
        priority=ExecutionPriority.MEDIUM
    )

    if result.get("status") == "completed":
        print("   ✅ Task completed automatically")
        print(f"   Result: {result.get('results', {})}\n")
    else:
        print(f"   ⚠️  Unexpected status: {result.get('status')}\n")

    # ========================================
    # 5. Execute High-Risk Task (Requires Approval)
    # ========================================
    print("5️⃣  Executing high-risk task (requires approval)...")
    result = await orchestrator.execute_task(
        task_type="generate_design",
        parameters={"task": "generate_design", "style": "luxury", "season": "fall"},
        required_capabilities=["design_generation"],
        priority=ExecutionPriority.HIGH,
        require_approval=True  # Force approval for demo
    )

    if result.get("status") == "pending_approval":
        action_id = result.get("action_id")
        print(f"   ⏳ Task pending approval: {action_id}")
        print(f"   Review command: {result.get('review_command')}\n")

        # Simulate operator approval
        print("6️⃣  Simulating operator approval...")
        approval_result = await approval_system.approve(
            action_id=action_id,
            operator="demo_operator",
            notes="Approved for demonstration"
        )
        print(f"   ✅ Approved: {approval_result}\n")

        # Execute the approved task
        print("7️⃣  Executing approved task...")
        execution_result = await orchestrator.execute_approved_task(
            task_id=action_id,
            approved_by="demo_operator"
        )
        print(f"   ✅ Execution result: {execution_result.get('status')}\n")
    else:
        print(f"   ⚠️  Unexpected status: {result.get('status')}\n")

    # ========================================
    # 8. Data Pipeline Example
    # ========================================
    print("8️⃣  Data Pipeline Example...")
    print("   (Would process approved data files)")
    print("   Supported: CSV, JSON, Parquet, Images")
    print("   All data validated against schemas\n")

    # ========================================
    # 9. Performance Tracking
    # ========================================
    print("9️⃣  Performance Tracking...")

    # Log some metrics
    performance_tracker.log_metric("designer_agent", "execution_time", 1.2)
    performance_tracker.log_metric("designer_agent", "success_rate", 1.0)
    performance_tracker.log_metric("commerce_agent", "execution_time", 0.8)

    print("   ✅ Metrics logged\n")

    # Generate weekly report
    weekly_report = await performance_tracker.compute_weekly_report()
    print(f"   📊 Weekly report generated")
    print(f"   Agent performance data points: {len(weekly_report.get('agent_performance', {}))}\n")

    # ========================================
    # 10. System Status
    # ========================================
    print("🔟 System Status...")
    status = await orchestrator.get_bounded_status()

    print(f"   System Status: {status.get('system_status')}")
    print(f"   Registered Agents: {status.get('registered_agents')}")
    print(f"   Pending Approvals: {status.get('bounded_autonomy', {}).get('pending_approvals', 0)}")
    print(f"   Emergency Stop: {status.get('bounded_autonomy', {}).get('system_controls', {}).get('emergency_stop')}")
    print(f"   Local Only: {status.get('bounded_autonomy', {}).get('system_controls', {}).get('local_only')}")
    print()

    # ========================================
    # 11. Generate Reports
    # ========================================
    print("1️⃣1️⃣  Generating Reports...")

    # Daily summary
    approval_stats = {
        "pending": len(await approval_system.get_pending_actions()),
        "approved_today": 1,
        "rejected_today": 0
    }

    daily_report = await report_generator.generate_daily_summary(
        orchestrator_status=status,
        performance_data=weekly_report,
        approval_stats=approval_stats
    )
    print(f"   ✅ Daily summary: {daily_report}\n")

    # ========================================
    # Final Summary
    # ========================================
    print("=" * 70)
    print("✅ INTEGRATION EXAMPLE COMPLETE")
    print("=" * 70)
    print()
    print("Next Steps:")
    print("1. Review approval queue: python -m fashion_ai_bounded_autonomy.approval_cli list")
    print("2. Check logs: ls -la logs/")
    print("3. Review reports: ls -la fashion_ai_bounded_autonomy/output/summaries/")
    print("4. Integrate your own agents following this pattern")
    print()


if __name__ == "__main__":
    asyncio.run(main())
