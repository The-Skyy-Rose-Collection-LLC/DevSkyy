from datetime import datetime
import threading
import time

        from ..git_commit import commit_fixes
        from ..modules.fixer import fix_code
        from ..modules.scanner import scan_site
from typing import Any, Callable, Dict
import logging
import schedule

logger = logging.getLogger(__name__)

class CronScheduler:
    """
    Production-level cron scheduler for automated tasks.
    Manages recurring jobs with error handling and monitoring.
    """

    def __init__(self):
        self.jobs = {}
        self.running = False
        self.scheduler_thread = None

    def schedule_job(self, job_func: Callable, interval: str, **kwargs) -> str:
        """Schedule a job with specified interval."""
        job_id = f"job_{len(self.jobs)}_{int(time.time())}"

        try:
            if interval == "hourly":
                job = schedule.every().hour.do(job_func, **kwargs)
            elif interval == "daily":
                job = schedule.every().day.do(job_func, **kwargs)
            elif interval == "weekly":
                job = schedule.every().week.do(job_func, **kwargs)
            elif interval.endswith("minutes"):
                minutes = int(interval.split()[0])
                job = schedule.every(minutes).minutes.do(job_func, **kwargs)
            elif interval.endswith("hours"):
                hours = int(interval.split()[0])
                job = schedule.every(hours).hours.do(job_func, **kwargs)
            else:
                raise ValueError(f"Unsupported interval: {interval}")

            self.jobs[job_id] = {
                "job": job,
                "function": job_func,
                "interval": interval,
                "created": datetime.now().isoformat(),
                "last_run": None,
                "run_count": 0,
                "errors": 0,
            }

            logger.info(f"✅ Scheduled job {job_id} with interval: {interval}")
            return job_id

        except Exception as e:
            logger.error(f"❌ Failed to schedule job: {str(e)}")
            raise

    def start_scheduler(self):
        """Start the scheduler in a background thread."""
        if self.running:
            logger.info("Scheduler is already running")
            return

        self.running = True
        self.scheduler_thread = threading.Thread(
            target=self._run_scheduler, daemon=True
        )
        self.scheduler_thread.start()

        logger.info("🚀 Cron scheduler started")

    def _run_scheduler(self):
        """Run the scheduler loop."""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(30)  # TODO: Move to config  # Check every 30 seconds
            except Exception as e:
                logger.error(f"❌ Scheduler error: {str(e)}")
                time.sleep(60)  # TODO: Move to config  # Wait longer on error

    def stop_scheduler(self):
        """Stop the scheduler."""
        self.running = False
        schedule.clear()

        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)

        logger.info("⏹️ Cron scheduler stopped")

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a specific job."""
        if job_id not in self.jobs:
            return {"error": "Job not found"}

        job_info = self.jobs[job_id]
        return {
            "job_id": job_id,
            "interval": job_info["interval"],
            "created": job_info["created"],
            "last_run": job_info["last_run"],
            "run_count": job_info["run_count"],
            "errors": job_info["errors"],
            "next_run": (
                str(job_info["job"].next_run) if job_info["job"].next_run else None
            ),
        }

    def list_all_jobs(self) -> Dict[str, Any]:
        """List all scheduled jobs."""
        return {
            "total_jobs": len(self.jobs),
            "running": self.running,
            "jobs": {job_id: self.get_job_status(job_id) for job_id in self.jobs},
        }

# Global scheduler instance
_global_scheduler = CronScheduler()

def schedule_hourly_job() -> Dict[str, Any]:
    """
    Schedule the main DevSkyy agent workflow to run hourly.
    Production-level implementation with comprehensive monitoring.
    """
    try:
        logger.info("⏰ Setting up hourly DevSkyy agent workflow...")

        # Import the main functions

        def automated_workflow():
            """The automated workflow that runs every hour."""
            try:
                logger.info("🤖 Starting automated DevSkyy workflow...")

                # Step 1: Scan the site
                scan_results = scan_site()
                logger.info(
                    f"📊 Scan completed: {scan_results.get('files_scanned', 0)} files scanned"
                )

                # Step 2: Fix any issues found
                if scan_results.get("errors_found") or scan_results.get("warnings"):
                    fix_results = fix_code(scan_results)
                    logger.info(
                        f"🔧 Fixes applied: {fix_results.get('files_fixed', 0)} files fixed"
                    )

                    # Step 3: Commit fixes if any were made
                    if fix_results.get("files_fixed", 0) > 0:
                        commit_result = commit_fixes(fix_results)
                        logger.info(f"📝 Commit status: {commit_result.get('status')}")
                else:
                    logger.info("✅ No issues found, system is healthy")

                # Update job statistics
                job_id = getattr(automated_workflow, "job_id", None)
                if job_id and job_id in _global_scheduler.jobs:
                    _global_scheduler.jobs[job_id][
                        "last_run"
                    ] = datetime.now().isoformat()
                    _global_scheduler.jobs[job_id]["run_count"] += 1

                logger.info("✅ Automated workflow completed successfully")

            except Exception as e:
                logger.error(f"❌ Automated workflow failed: {str(e)}")

                # Update error count
                job_id = getattr(automated_workflow, "job_id", None)
                if job_id and job_id in _global_scheduler.jobs:
                    _global_scheduler.jobs[job_id]["errors"] += 1

        # Schedule the job
        job_id = _global_scheduler.schedule_job(automated_workflow, "hourly")
        automated_workflow.job_id = job_id

        # Start the scheduler if not already running
        if not _global_scheduler.running:
            _global_scheduler.start_scheduler()

        return {
            "status": "scheduled",
            "job_id": job_id,
            "interval": "hourly",
            "next_run": (
                str(schedule.jobs[0].next_run) if schedule.jobs else "within 1 hour"
            ),
            "scheduler_running": _global_scheduler.running,
            "message": "DevSkyy agent workflow scheduled successfully",
        }

    except Exception as e:
        logger.error(f"❌ Failed to schedule hourly job: {str(e)}")
        return {"status": "failed", "error": str(e)}

def schedule_custom_job(job_func: Callable, interval: str, **kwargs) -> Dict[str, Any]:
    """Schedule a custom job with specified interval."""
    try:
        job_id = _global_scheduler.schedule_job(job_func, interval, **kwargs)

        if not _global_scheduler.running:
            _global_scheduler.start_scheduler()

        return {"status": "scheduled", "job_id": job_id, "interval": interval}

    except Exception as e:
        return {"status": "failed", "error": str(e)}

def get_scheduler_status() -> Dict[str, Any]:
    """Get comprehensive scheduler status."""
    return _global_scheduler.list_all_jobs()

def stop_scheduler() -> Dict[str, Any]:
    """Stop the scheduler."""
    _global_scheduler.stop_scheduler()
    return {"status": "stopped"}
