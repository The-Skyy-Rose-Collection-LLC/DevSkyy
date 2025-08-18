
import schedule
import time
import threading
from datetime import datetime
from typing import Callable, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DevSkyyScheduler:
    """Enhanced scheduler for DevSkyy operations."""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.jobs = {}
    
    def schedule_hourly_job(self, job_func: Callable = None, job_name: str = "default"):
        """Schedule a job to run every hour."""
        if job_func is None:
            job_func = self._default_hourly_task
        
        schedule.every().hour.do(job_func)
        self.jobs[job_name] = {
            "function": job_func,
            "frequency": "hourly",
            "last_run": None
        }
        
        logger.info(f"Scheduled hourly job: {job_name}")
        return True
    
    def schedule_daily_job(self, job_func: Callable, job_name: str, time_str: str = "02:00"):
        """Schedule a job to run daily at specified time."""
        schedule.every().day.at(time_str).do(job_func)
        self.jobs[job_name] = {
            "function": job_func,
            "frequency": "daily",
            "time": time_str,
            "last_run": None
        }
        
        logger.info(f"Scheduled daily job: {job_name} at {time_str}")
        return True
    
    def start_scheduler(self):
        """Start the scheduler in a background thread."""
        if self.running:
            logger.warning("Scheduler already running")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        logger.info("DevSkyy scheduler started")
        return True
    
    def stop_scheduler(self):
        """Stop the scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("DevSkyy scheduler stopped")
        return True
    
    def _run_scheduler(self):
        """Main scheduler loop."""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)
    
    def _default_hourly_task(self):
        """Default hourly maintenance task."""
        try:
            from agent.modules.scanner import scan_site
            from agent.modules.fixer import fix_code
            
            # Run basic site scan
            scan_results = scan_site()
            
            # Apply any necessary fixes
            if scan_results.get("issues_found"):
                fix_code(scan_results)
            
            logger.info("Hourly maintenance completed")
            
            # Update job status
            for job_name, job_info in self.jobs.items():
                if job_info["function"] == self._default_hourly_task:
                    job_info["last_run"] = datetime.now().isoformat()
                    
        except Exception as e:
            logger.error(f"Hourly task error: {e}")
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get status of all scheduled jobs."""
        return {
            "scheduler_running": self.running,
            "total_jobs": len(self.jobs),
            "jobs": self.jobs,
            "next_run": str(schedule.next_run()) if schedule.jobs else None
        }

# Global scheduler instance
scheduler = DevSkyyScheduler()

def schedule_hourly_job(job_func: Callable = None) -> bool:
    """Convenience function to schedule hourly job."""
    return scheduler.schedule_hourly_job(job_func)

def start_scheduler() -> bool:
    """Start the global scheduler."""
    return scheduler.start_scheduler()

def get_scheduler_status() -> Dict[str, Any]:
    """Get scheduler status."""
    return scheduler.get_job_status()
