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
        """
        Handle a task failure by logging a localized error message that includes the task name, task id, and the error.
        
        Parameters:
            exc (Exception): The exception instance raised by the task.
            task_id (str): Identifier of the failed task execution.
            args (tuple): Positional arguments originally passed to the task.
            kwargs (dict): Keyword arguments originally passed to the task.
            einfo (traceback): Traceback/info object for the failure.
        """
        logger.error(f"❌ {t('tasks.failure', name=self.name, task_id=task_id, error=str(exc))}")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """
        Log a retry event for the task, including a localized message with the task name, task id, and error.
        
        Parameters:
            exc (Exception): The exception that triggered the retry.
            task_id (str): Identifier of the task execution.
            args (tuple): Positional arguments originally passed to the task.
            kwargs (dict): Keyword arguments originally passed to the task.
            einfo: Exception traceback/info provided by Celery.
        """
        logger.warning(f"🔄 {t('tasks.retry', name=self.name, task_id=task_id, error=str(exc))}")


# ============================================================================
# APPROVAL NOTIFICATION TASKS
# ============================================================================

@celery_app.task(base=BoundedAutonomyTask, bind=True, max_retries=3)
def send_approval_notification_task(self, action_id: str, agent_name: str, risk_level: str):
    """
    Notify an operator that a specific action requires approval.
    
    Returns:
        dict: {"status": "sent", "action_id": <action_id>} when the notification is successfully enqueued.
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
    """
    Remove expired approval requests from the approval system.
    
    Runs the approval system cleanup and returns a summary of the operation.
    
    Returns:
        result (dict): Operation result. On success: {"status": "completed", "cleaned_count": int} with the number of approvals removed. On failure: {"status": "failed", "error": str} with an error description.
    """
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
    Ingest data from a file into the data pipeline.
    
    Parameters:
        file_path (str): Filesystem path to the input data file.
        source_type (str): Format or source type of the file (e.g., "csv", "json").
    
    Returns:
        dict: Ingestion result returned by the data pipeline, typically containing status and processed metadata.
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
def validate_data_task(data: Dict[str, Any], source_type: str = "json"):
    """
    Validate and preprocess incoming data.
    
    Runs the data pipeline's preprocessing step and returns the pipeline's result. If preprocessing fails, returns a dict with keys `"status": "failed"` and `"error"` containing the error message.
    
    Parameters:
        data (Dict[str, Any]): Input payload to validate and preprocess.
        source_type (str, optional): Format or source type of the input data (e.g., "csv", "json"). Defaults to "json".
    
    Returns:
        The processed data returned by the pipeline on success; on failure, a dict `{"status": "failed", "error": "<message>"}`.
    """
    try:
        from fashion_ai_bounded_autonomy.data_pipeline import DataPipeline

        pipeline = DataPipeline()
        result = asyncio.run(pipeline.preprocess(data, source_type))

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
    """
    Generate the daily summary report.
    
    Returns:
        result (dict): On success: {"status": "completed", "report": <summary>} where `<summary>` is the generated report object.
                       On failure: {"status": "failed", "error": "<error message>"} with the error description.
    """
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
    """
    Generate the weekly summary report.
    
    Returns:
        dict: On success, {"status": "completed", "report": <report>} where <report> is the generated weekly summary.
              On failure, {"status": "failed", "error": "<error message>"} with a string describing the error.
    """
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
    """
    Generate a data validation report.
    
    On success returns a dictionary with "status" set to "completed" and "report" containing the generated validation report; on failure returns a dictionary with "status" set to "failed" and "error" containing the error message.
    
    Returns:
        dict: Success: {"status": "completed", "report": <report>}. Failure: {"status": "failed", "error": "<error message>"}.
    """
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
    Export performance metrics in the specified format.
    
    Parameters:
        format (str): Desired export format, typically "csv" or "json".
    
    Returns:
        dict: Result object with one of the following shapes:
            - {"status": "completed", "file_path": "<path>"} when export succeeds.
            - {"status": "failed", "error": "<error message>"} when an error occurs.
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
    """
    Check health of all registered agents and report any that are unhealthy.
    
    Performs health checks for each agent registered with the Watchdog and returns a summary of the results.
    
    Returns:
        result (dict): If successful, a dictionary with:
            - "status": "completed"
            - "unhealthy_agents": list of agent names that failed health checks (empty list if none)
            - "timestamp": ISO 8601 timestamp of when the check completed.
        If an error occurs, a dictionary with:
            - "status": "failed"
            - "error": string representation of the error that occurred.
    """
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
    """
    Retrieve a comprehensive snapshot of the system's current status.
    
    Returns:
        result (dict): On success, a dictionary with:
            - "status": "completed"
            - "system_status": the structured system status payload.
        On failure, a dictionary with:
            - "status": "failed"
            - "error": a string describing the failure.
    """
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
    """
    Take a snapshot of current performance metrics.
    
    Returns:
        dict: A result object with keys:
            - "status" (str): "completed" if snapshot succeeded, "failed" otherwise.
            - "metrics" (Any): KPI summary when status is "completed".
            - "error" (str): Error message when status is "failed".
    """
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
    """
    Generate performance improvement proposals for the system.
    
    Returns:
        dict: On success, {"status": "completed", "proposals": [...]} containing the generated proposals; on failure, {"status": "failed", "error": "<error message>"}.
    """
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
    Execute a task that has been approved and return its execution result.
    
    Parameters:
        task_id (str): Identifier of the approved task to execute.
        approved_by (str): Identifier or name of the operator who approved the task.
    
    Returns:
        Any: The result produced by executing the approved task.
    
    Raises:
        celery.exceptions.Retry: Re-queues the task for retry with a countdown when execution fails.
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
    Submit a named task to the Celery queue for execution.
    
    Parameters:
        task_name (str): Key identifying the task to enqueue. Supported keys:
            'send_approval_notification', 'process_data_ingestion',
            'validate_data', 'generate_daily_reports', 'generate_weekly_report',
            'export_metrics', 'monitor_agent_health', 'execute_approved_task'.
        *args: Positional arguments passed to the task.
        **kwargs: Keyword arguments passed to the task.
    
    Returns:
        Celery AsyncResult: Object representing the enqueued task.
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