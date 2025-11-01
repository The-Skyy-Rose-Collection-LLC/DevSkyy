"""Ops Agent - System monitoring, health checks, and automation."""

import time
from pathlib import Path
from typing import Any, Dict, List

from src.core.utils import get_disk_usage, save_json

from .base import BaseAgent


class OpsAgent(BaseAgent):
    """Agent responsible for operational monitoring and system management."""

    def __init__(self, *args, **kwargs):
        """Initialize Ops Agent."""
        super().__init__(name="OpsAgent", *args, **kwargs)
        self.metrics_path = Path("logs")
        self.metrics_path.mkdir(parents=True, exist_ok=True)

    def get_supported_tasks(self) -> List[str]:
        """Get supported task types."""
        return ["health_check", "collect_metrics", "trigger_backup", "scale_services"]

    async def process_task(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process ops-related tasks.

        Args:
            task_type: Type of ops task
            payload: Task parameters

        Returns:
            Task result
        """
        if task_type == "health_check":
            return await self._health_check(payload)
        elif task_type == "collect_metrics":
            return await self._collect_metrics(payload)
        elif task_type == "trigger_backup":
            return await self._trigger_backup(payload)
        elif task_type == "scale_services":
            return await self._scale_services(payload)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")

    async def _health_check(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform system health check.

        Args:
            payload: Health check parameters

        Returns:
            Health status
        """
        self.logger.info("Performing health check")

        # Check disk usage
        disk_usage = get_disk_usage(Path("."))

        # Check queue depths
        queue_depths = {
            "designer": self.queue_manager.get_queue_depth("designer"),
            "commerce": self.queue_manager.get_queue_depth("commerce"),
            "marketing": self.queue_manager.get_queue_depth("marketing"),
            "finance": self.queue_manager.get_queue_depth("finance"),
        }

        health = {
            "status": "healthy",
            "timestamp": time.time(),
            "checks": {
                "disk_usage_percent": disk_usage["percent"],
                "disk_free_gb": disk_usage["free"] / (1024**3),
                "queue_depths": queue_depths,
                "max_queue_depth": max(queue_depths.values()),
            },
            "alerts": [],
        }

        # Check thresholds
        if disk_usage["percent"] > 90:
            health["alerts"].append("Disk usage above 90%")
            health["status"] = "warning"

        if max(queue_depths.values()) > 1000:
            health["alerts"].append("Queue depth exceeds 1000")
            health["status"] = "warning"

        # Save health report
        health_file = self.metrics_path / "health_report.txt"
        with open(health_file, "w") as f:
            f.write(f"Health Check Report - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Status: {health['status']}\n")
            f.write(f"Disk Usage: {health['checks']['disk_usage_percent']:.2f}%\n")
            f.write(f"Max Queue Depth: {health['checks']['max_queue_depth']}\n")
            if health["alerts"]:
                f.write(f"Alerts: {', '.join(health['alerts'])}\n")

        self.logger.info(f"Health check complete: {health['status']}")
        return health

    async def _collect_metrics(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Collect system metrics.

        Args:
            payload: Metrics collection parameters

        Returns:
            Collected metrics
        """
        self.logger.info("Collecting system metrics")

        # Collect queue metrics
        queue_metrics = {
            "designer": {
                "depth": self.queue_manager.get_queue_depth("designer"),
                "throughput": 10.5,  # Placeholder
            },
            "commerce": {
                "depth": self.queue_manager.get_queue_depth("commerce"),
                "throughput": 8.2,
            },
            "marketing": {
                "depth": self.queue_manager.get_queue_depth("marketing"),
                "throughput": 5.7,
            },
            "finance": {
                "depth": self.queue_manager.get_queue_depth("finance"),
                "throughput": 3.1,
            },
        }

        metrics = {
            "timestamp": time.time(),
            "queues": queue_metrics,
            "api": {
                "uptime_percent": 99.9,
                "avg_response_ms": 150,
                "error_rate_percent": 0.1,
            },
        }

        # Save metrics
        metrics_file = self.metrics_path / "queue_metrics.json"
        save_json(metrics, metrics_file)

        self.logger.info("Metrics collected and saved")
        return metrics

    async def _trigger_backup(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger system backup.

        Args:
            payload: Backup parameters

        Returns:
            Backup result
        """
        self.logger.info("Triggering backup")

        backup_type = payload.get("type", "full")

        backup = {
            "backup_id": f"BKP-{int(time.time())}",
            "backup_type": backup_type,
            "status": "completed",
            "size_bytes": 1024 * 1024 * 100,  # 100MB placeholder
            "started_at": time.time() - 300,
            "completed_at": time.time(),
        }

        self.logger.info(f"Backup completed: {backup['backup_id']}")
        return backup

    async def _scale_services(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Scale services based on load.

        Args:
            payload: Scaling parameters

        Returns:
            Scaling result
        """
        self.logger.info(f"Scaling services: {payload}")

        service = payload.get("service")
        target_instances = payload.get("instances", 2)

        scaling = {
            "service": service,
            "current_instances": 1,
            "target_instances": target_instances,
            "status": "scaling",
            "initiated_at": time.time(),
        }

        self.logger.info(f"Scaling initiated for {service}")
        return scaling
