
import schedule
import time
import logging
from datetime import datetime
from typing import Callable, Dict, Any

logger = logging.getLogger(__name__)

def schedule_hourly_job(job_func: Callable = None) -> Dict[str, Any]:
    """Schedule a job to run every hour."""
    try:
        if job_func is None:
            # Default job function
            def default_job():
                logger.info(f"🕐 Hourly DevSkyy maintenance check: {datetime.now().isoformat()}")
                return {"status": "completed", "timestamp": datetime.now().isoformat()}
            job_func = default_job
        
        # Schedule the job
        schedule.every().hour.do(job_func)
        
        logger.info("⏰ Hourly job scheduled successfully")
        return {
            "status": "scheduled",
            "job_type": "hourly",
            "next_run": schedule.next_run().isoformat() if schedule.next_run() else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to schedule hourly job: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def schedule_daily_job(job_func: Callable, time_str: str = "02:00") -> Dict[str, Any]:
    """Schedule a job to run daily at specified time."""
    try:
        schedule.every().day.at(time_str).do(job_func)
        
        logger.info(f"⏰ Daily job scheduled for {time_str}")
        return {
            "status": "scheduled",
            "job_type": "daily",
            "scheduled_time": time_str,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to schedule daily job: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def run_pending_jobs() -> Dict[str, Any]:
    """Run all pending scheduled jobs."""
    try:
        schedule.run_pending()
        return {
            "status": "completed",
            "pending_jobs": len(schedule.jobs),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to run pending jobs: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def get_scheduled_jobs() -> Dict[str, Any]:
    """Get information about all scheduled jobs."""
    try:
        jobs_info = []
        for job in schedule.jobs:
            jobs_info.append({
                "job": str(job.job_func),
                "next_run": job.next_run.isoformat() if job.next_run else None,
                "interval": str(job.interval),
                "unit": job.unit
            })
        
        return {
            "total_jobs": len(schedule.jobs),
            "jobs": jobs_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get scheduled jobs: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def clear_all_jobs() -> Dict[str, Any]:
    """Clear all scheduled jobs."""
    try:
        schedule.clear()
        logger.info("🧹 All scheduled jobs cleared")
        return {
            "status": "cleared",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to clear jobs: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
