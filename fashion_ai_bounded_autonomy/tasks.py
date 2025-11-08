"""
Celery Tasks for Bounded Autonomy System

All async tasks for the bounded autonomy system.
Tasks are organized by functional area:
- Approval notifications
- Data processing
- Report generation
- Monitoring and health checks
- Performance tracking
- Cleanup operations
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from celery import Task

from fashion_ai_bounded_autonomy.celery_app import celery_app
from fashion_ai_bounded_autonomy.i18n_loader import t


logger = logging.getLogger(__name__)


class BoundedAutonomyTask(Task):
    """Base task class with audit logging"""

    def on_success(self, retval, task_id, args, kwargs):
        """Log successful task execution"""
        logger.info(f"✅ {t('tasks.success', name=self.name, task_id=task_id)}")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log failed task execution"""
        logger.error(f"❌ {t('tasks.failure', name=self.name, task_id=task_id, error=str(exc))}")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Log task retry"""
        logger.warning(f"🔄 {t('tasks.retry', name=self.name, task_id=task_id, error=str(exc))}")


# ============================================================================
# APPROVAL NOTIFICATION TASKS
# ============================================================================

@celery_app.task(base=BoundedAutonomyTask, bind=True, max_retries=3)
def send_approval_notification_task(self, action_id: str, agent_name: str, risk_level: str):
    """
    Send notification to operator for pending approval.

    Args:
        action_id: Action ID requiring approval
        agent_name: Name of the agent requesting approval
        risk_level: Risk level of the action
    """
    try:
        from fashion_ai_bounded_autonomy.watchdog import Watchdog

        watchdog = Watchdog()
        notification = {
            "type": "approval_required",
            "action_id": action_id,
            "agent_name": agent_name,
            "risk_level": risk_level,
            "timestamp": datetime.now().isoformat(),
            "review_command": f"python -m fashion_ai_bounded_autonomy.approval_cli review {action_id}"
        }

        # Use asyncio to run async watchdog method
        asyncio.run(watchdog._send_notification("operator", "approval_required", notification))

        logger.info(f"📬 {t('tasks.approval_notification_sent', action_id=action_id)}")
        return {"status": "sent", "action_id": action_id}

    except Exception as exc:
        logger.error(f"{t('approval.notification_failed', error=str(exc))}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(base=BoundedAutonomyTask)
def cleanup_expired_approvals_task():
    """Clean up expired approval requests (runs hourly)"""
    try:
        from fashion_ai_bounded_autonomy.approval_system import ApprovalSystem

        approval_system = ApprovalSystem()
        count = asyncio.run(approval_system.cleanup_expired())

        logger.info(f"🧹 {t('approval.cleanup_expired', count=count)}")
        return {"status": "completed", "cleaned_count": count}

    except Exception as exc:
        logger.error(f"{t('errors.generic', error=str(exc))}")
        return {"status": "failed", "error": str(exc)}


# ============================================================================
# DATA PROCESSING TASKS
# ============================================================================

@celery_app.task(base=BoundedAutonomyTask, bind=True, max_retries=3)
def process_data_ingestion_task(self, file_path: str, source_type: str):
    """
    Process data ingestion asynchronously.

    Args:
        file_path: Path to data file
        source_type: Type of data source (csv, json, etc.)
    """
    try:
        from fashion_ai_bounded_autonomy.data_pipeline import DataPipeline

        pipeline = DataPipeline()
        result = asyncio.run(pipeline.ingest(file_path, source_type))

        logger.info(f"📊 Processed data ingestion: {file_path}")
        return result

    except Exception as exc:
        logger.error(f"Data ingestion failed: {exc}")
        raise self.retry(exc=exc, countdown=120)


@celery_app.task(base=BoundedAutonomyTask)
def validate_data_task(data: Dict[str, Any]):
    """
    Validate and preprocess data asynchronously.

    Args:
        data: Data to validate
    """
    try:
        from fashion_ai_bounded_autonomy.data_pipeline import DataPipeline

        pipeline = DataPipeline()
        result = asyncio.run(pipeline.preprocess(data))

        logger.info("✅ Data validation completed")
        return result

    except Exception as exc:
        logger.error(f"Data validation failed: {exc}")
        return {"status": "failed", "error": str(exc)}


# ============================================================================
# REPORT GENERATION TASKS
# ============================================================================

@celery_app.task(base=BoundedAutonomyTask)
def generate_daily_reports_task():
    """Generate daily summary reports (runs daily)"""
    try:
        from fashion_ai_bounded_autonomy.report_generator import ReportGenerator

        report_gen = ReportGenerator()
        summary = asyncio.run(report_gen.generate_daily_summary())

        logger.info("📈 Generated daily summary report")
        return {"status": "completed", "report": summary}

    except Exception as exc:
        logger.error(f"Daily report generation failed: {exc}")
        return {"status": "failed", "error": str(exc)}


@celery_app.task(base=BoundedAutonomyTask)
def generate_weekly_report_task():
    """Generate weekly summary report"""
    try:
        from fashion_ai_bounded_autonomy.report_generator import ReportGenerator

        report_gen = ReportGenerator()
        report = asyncio.run(report_gen.generate_weekly_report())

        logger.info("📊 Generated weekly summary report")
        return {"status": "completed", "report": report}

    except Exception as exc:
        logger.error(f"Weekly report generation failed: {exc}")
        return {"status": "failed", "error": str(exc)}


@celery_app.task(base=BoundedAutonomyTask)
def generate_validation_report_task():
    """Generate data validation report"""
    try:
        from fashion_ai_bounded_autonomy.report_generator import ReportGenerator

        report_gen = ReportGenerator()
        report = asyncio.run(report_gen.generate_validation_report())

        logger.info("✅ Generated validation report")
        return {"status": "completed", "report": report}

    except Exception as exc:
        logger.error(f"Validation report generation failed: {exc}")
        return {"status": "failed", "error": str(exc)}


@celery_app.task(base=BoundedAutonomyTask)
def export_metrics_task(format: str = "csv"):
    """
    Export performance metrics.

    Args:
        format: Export format (csv, json)
    """
    try:
        from fashion_ai_bounded_autonomy.report_generator import ReportGenerator

        report_gen = ReportGenerator()
        file_path = asyncio.run(report_gen.export_metrics(format))

        logger.info(f"📤 Exported metrics to {file_path}")
        return {"status": "completed", "file_path": str(file_path)}

    except Exception as exc:
        logger.error(f"Metrics export failed: {exc}")
        return {"status": "failed", "error": str(exc)}


# ============================================================================
# MONITORING AND HEALTH CHECK TASKS
# ============================================================================

@celery_app.task(base=BoundedAutonomyTask)
def monitor_agent_health_task():
    """Monitor health of all registered agents (runs every 5 minutes)"""
    try:
        from fashion_ai_bounded_autonomy.watchdog import Watchdog

        watchdog = Watchdog()
        unhealthy_agents = []

        # Check health of registered agents
        for agent_name in watchdog.agents.keys():
            is_healthy = asyncio.run(watchdog.check_health(agent_name))
            if not is_healthy:
                unhealthy_agents.append(agent_name)

        if unhealthy_agents:
            logger.warning(f"⚠️  Unhealthy agents detected: {unhealthy_agents}")
        else:
            logger.info("✅ All agents healthy")

        return {
            "status": "completed",
            "unhealthy_agents": unhealthy_agents,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as exc:
        logger.error(f"Health monitoring failed: {exc}")
        return {"status": "failed", "error": str(exc)}


@celery_app.task(base=BoundedAutonomyTask)
def check_system_status_task():
    """Get comprehensive system status"""
    try:
        from fashion_ai_bounded_autonomy.watchdog import Watchdog

        watchdog = Watchdog()
        status = asyncio.run(watchdog.get_status())

        logger.info("📊 Retrieved system status")
        return {"status": "completed", "system_status": status}

    except Exception as exc:
        logger.error(f"System status check failed: {exc}")
        return {"status": "failed", "error": str(exc)}


# ============================================================================
# PERFORMANCE TRACKING TASKS
# ============================================================================

@celery_app.task(base=BoundedAutonomyTask)
def performance_snapshot_task():
    """Take performance metrics snapshot (runs every 15 minutes)"""
    try:
        from fashion_ai_bounded_autonomy.performance_tracker import PerformanceTracker

        tracker = PerformanceTracker()

        # Get current KPIs
        summary = tracker.get_kpi_summary()

        logger.info("📸 Captured performance snapshot")
        return {"status": "completed", "metrics": summary}

    except Exception as exc:
        logger.error(f"Performance snapshot failed: {exc}")
        return {"status": "failed", "error": str(exc)}


@celery_app.task(base=BoundedAutonomyTask)
def generate_performance_proposals_task():
    """Generate performance improvement proposals"""
    try:
        from fashion_ai_bounded_autonomy.performance_tracker import PerformanceTracker

        tracker = PerformanceTracker()
        proposals = tracker.get_proposals()

        logger.info(f"💡 Generated {len(proposals)} performance proposals")
        return {"status": "completed", "proposals": proposals}

    except Exception as exc:
        logger.error(f"Performance proposal generation failed: {exc}")
        return {"status": "failed", "error": str(exc)}


# ============================================================================
# TASK EXECUTION TASKS
# ============================================================================

@celery_app.task(base=BoundedAutonomyTask, bind=True, max_retries=3)
def execute_approved_task_async(self, task_id: str, approved_by: str):
    """
    Execute an approved task asynchronously.

    Args:
        task_id: Task ID to execute
        approved_by: Operator who approved
    """
    try:
        from fashion_ai_bounded_autonomy.bounded_orchestrator import BoundedOrchestrator

        orchestrator = BoundedOrchestrator()
        result = asyncio.run(orchestrator.execute_approved_task(task_id, approved_by))

        logger.info(f"✅ Executed approved task {task_id}")
        return result

    except Exception as exc:
        logger.error(f"Task execution failed: {exc}")
        raise self.retry(exc=exc, countdown=180)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def submit_task_async(task_name: str, *args, **kwargs):
    """
    Submit a task for async execution.

    Args:
        task_name: Name of the task to execute
        *args: Positional arguments for the task
        **kwargs: Keyword arguments for the task

    Returns:
        AsyncResult object
    """
    task_map = {
        'send_approval_notification': send_approval_notification_task,
        'process_data_ingestion': process_data_ingestion_task,
        'validate_data': validate_data_task,
        'generate_daily_reports': generate_daily_reports_task,
        'generate_weekly_report': generate_weekly_report_task,
        'export_metrics': export_metrics_task,
        'monitor_agent_health': monitor_agent_health_task,
        'execute_approved_task': execute_approved_task_async,
    }

    task = task_map.get(task_name)
    if not task:
        raise ValueError(f"Unknown task: {task_name}")

    return task.delay(*args, **kwargs)


logger.info("✅ Celery tasks loaded for bounded autonomy system")
