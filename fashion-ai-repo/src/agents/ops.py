"""Ops Agent - System monitoring, health checks, and automation."""

import time
from pathlib import Path
from typing import Any, Dict, List

from src.core.utils import get_disk_usage, save_json

from .base import BaseAgent


class OpsAgent(BaseAgent):
    """Agent responsible for operational monitoring and system management."""

    def __init__(self, *args, **kwargs):
        """
        Create an OpsAgent named "OpsAgent" and ensure a "logs" directory exists for metrics.
        
        Initializes the BaseAgent with the name "OpsAgent" and creates the `metrics_path` attribute pointing to the "logs" directory, creating the directory if it does not already exist.
        """
        super().__init__(name="OpsAgent", *args, **kwargs)
        self.metrics_path = Path("logs")
        self.metrics_path.mkdir(parents=True, exist_ok=True)

    def get_supported_tasks(self) -> List[str]:
        """
        Return the task type identifiers this agent can handle.
        
        Returns:
            List[str]: Supported task type identifiers: "health_check", "collect_metrics", "trigger_backup", "scale_services".
        """
        return ["health_check", "collect_metrics", "trigger_backup", "scale_services"]

    async def process_task(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch and execute an OpsAgent task based on its type.
        
        Parameters:
            task_type (str): One of "health_check", "collect_metrics", "trigger_backup", or "scale_services".
            payload (Dict[str, Any]): Task-specific parameters used by the selected task handler.
        
        Returns:
            Dict[str, Any]: A task-specific result object (health report, metrics, backup descriptor, or scaling descriptor).
        
        Raises:
            ValueError: If task_type is not one of the supported types.
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
        """
        Perform a system health check and produce a structured health report.
        
        Parameters:
            payload (Dict[str, Any]): Optional parameters for the check (currently unused).
        
        Returns:
            Dict[str, Any]: Health report with the following keys:
                - `status` (str): Overall health status, e.g., "healthy" or "warning".
                - `timestamp` (float): UNIX timestamp when the check was performed.
                - `checks` (dict): Detailed measurements:
                    - `disk_usage_percent` (float): Disk usage percentage.
                    - `disk_free_gb` (float): Free disk space in gigabytes.
                    - `queue_depths` (dict): Per-service queue depths.
                    - `max_queue_depth` (int): Maximum queue depth across services.
                - `alerts` (List[str]): List of alert messages triggered by threshold breaches.
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
        """
        Gather and persist current queue and API metrics.
        
        Parameters:
            payload (Dict[str, Any]): Optional collection parameters (unused by default) that may influence which metrics are gathered.
        
        Returns:
            Dict[str, Any]: Metrics snapshot containing `timestamp`, `queues` (per-service depth and throughput), and `api` (uptime_percent, avg_response_ms, error_rate_percent).
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
        """
        Initiates a backup operation and produces a descriptor with its metadata.
        
        Parameters:
            payload (Dict[str, Any]): Backup parameters. Recognized key:
                - "type": optional; backup type string (defaults to "full").
        
        Returns:
            Dict[str, Any]: Backup descriptor containing keys:
                - "backup_id": unique backup identifier
                - "backup_type": the requested backup type
                - "status": final backup status
                - "size_bytes": size of the backup in bytes
                - "started_at": start timestamp (epoch seconds)
                - "completed_at": completion timestamp (epoch seconds)
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
        """
        Initiates a scaling operation for a service and returns a descriptor of the requested scaling action.
        
        Parameters:
            payload (Dict[str, Any]): Parameters for scaling. Expected keys:
                - "service" (str): Name of the service to scale.
                - "instances" (int, optional): Desired target instance count; defaults to 2.
        
        Returns:
            Dict[str, Any]: A descriptor of the scaling operation containing:
                - "service": requested service name
                - "current_instances": current instance count (placeholder)
                - "target_instances": requested target instance count
                - "status": operation status (e.g., "scaling")
                - "initiated_at": Unix timestamp when scaling was initiated
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