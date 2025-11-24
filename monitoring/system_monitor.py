import asyncio
from collections import deque
import contextlib
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any

import psutil


"""
Advanced System Monitoring - Enterprise Grade
Comprehensive system health monitoring with metrics collection and alerting
"""

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System metrics data structure"""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int
    process_count: int
    load_average: list[float]


@dataclass
class AlertRule:
    """Alert rule configuration"""

    name: str
    metric: str
    threshold: float
    operator: str  # '>', '<', '>=', '<=', '=='
    duration: int  # seconds
    severity: str  # 'critical', 'warning', 'info'
    enabled: bool = True


class MetricsCollector:
    """System metrics collector"""

    def __init__(self, collection_interval: int = 30):
        self.collection_interval = collection_interval
        self.metrics_history = deque(maxlen=1000)  # Keep last 1000 metrics
        self.is_collecting = False
        self._collection_task = None

    async def start_collection(self):
        """Start metrics collection"""
        if self.is_collecting:
            return

        self.is_collecting = True
        self._collection_task = asyncio.create_task(self._collect_metrics())
        logger.info("Started system metrics collection")

    async def stop_collection(self):
        """Stop metrics collection"""
        self.is_collecting = False
        if self._collection_task:
            self._collection_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._collection_task
        logger.info("Stopped system metrics collection")

    async def _collect_metrics(self):
        """Collect system metrics periodically"""
        while self.is_collecting:
            try:
                metrics = self._get_current_metrics()
                self.metrics_history.append(metrics)

                # Log critical metrics
                if metrics.cpu_percent > 90:
                    logger.warning(f"High CPU usage: {metrics.cpu_percent:.1f}%")

                if metrics.memory_percent > 90:
                    logger.warning(f"High memory usage: {metrics.memory_percent:.1f}%")

                if metrics.disk_usage_percent > 90:
                    logger.warning(f"High disk usage: {metrics.disk_usage_percent:.1f}%")

                await asyncio.sleep(self.collection_interval)

            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(self.collection_interval)

    def _get_current_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024**3)

        # Disk metrics
        disk = psutil.disk_usage("/")
        disk_usage_percent = (disk.used / disk.total) * 100
        disk_free_gb = disk.free / (1024**3)

        # Network metrics
        network = psutil.net_io_counters()
        network_bytes_sent = network.bytes_sent
        network_bytes_recv = network.bytes_recv

        # Connection metrics
        connections = psutil.net_connections()
        active_connections = len([c for c in connections if c.status == "ESTABLISHED"])

        # Process metrics
        process_count = len(psutil.pids())

        # Load average (Unix-like systems)
        try:
            load_average = list(psutil.getloadavg())
        except AttributeError:
            # Windows doesn't have load average
            load_average = [0.0, 0.0, 0.0]

        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_gb=memory_available_gb,
            disk_usage_percent=disk_usage_percent,
            disk_free_gb=disk_free_gb,
            network_bytes_sent=network_bytes_sent,
            network_bytes_recv=network_bytes_recv,
            active_connections=active_connections,
            process_count=process_count,
            load_average=load_average,
        )

    def get_latest_metrics(self) -> SystemMetrics | None:
        """Get the latest metrics"""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_metrics_history(self, minutes: int = 60) -> list[SystemMetrics]:
        """Get metrics history for specified minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]

    def get_average_metrics(self, minutes: int = 60) -> dict[str, float]:
        """Get average metrics over specified time period"""
        history = self.get_metrics_history(minutes)

        if not history:
            return {}

        return {
            "cpu_percent": sum(m.cpu_percent for m in history) / len(history),
            "memory_percent": sum(m.memory_percent for m in history) / len(history),
            "disk_usage_percent": sum(m.disk_usage_percent for m in history) / len(history),
            "active_connections": sum(m.active_connections for m in history) / len(history),
            "process_count": sum(m.process_count for m in history) / len(history),
            "load_average_1m": sum(m.load_average[0] for m in history) / len(history),
        }


class AlertManager:
    """System alert manager"""

    def __init__(self):
        self.alert_rules: list[AlertRule] = []
        self.active_alerts: dict[str, dict] = {}
        self.alert_history: deque = deque(maxlen=1000)

        # Default alert rules
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Setup default alert rules"""
        default_rules = [
            AlertRule("High CPU Usage", "cpu_percent", 90.0, ">=", 300, "critical"),
            AlertRule("High Memory Usage", "memory_percent", 90.0, ">=", 300, "critical"),
            AlertRule("High Disk Usage", "disk_usage_percent", 90.0, ">=", 600, "warning"),
            AlertRule("Low Disk Space", "disk_free_gb", 1.0, "<=", 600, "critical"),
            AlertRule("High Load Average", "load_average_1m", 5.0, ">=", 300, "warning"),
            AlertRule("Too Many Processes", "process_count", 500, ">=", 300, "warning"),
        ]

        self.alert_rules.extend(default_rules)
        logger.info(f"Setup {len(default_rules)} default alert rules")

    def add_alert_rule(self, rule: AlertRule):
        """Add custom alert rule"""
        self.alert_rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")

    def check_alerts(self, metrics: SystemMetrics):
        """Check metrics against alert rules"""
        current_time = datetime.now()

        for rule in self.alert_rules:
            if not rule.enabled:
                continue

            # Get metric value
            metric_value = getattr(metrics, rule.metric, None)
            if metric_value is None:
                continue

            # Handle load average special case
            if rule.metric == "load_average_1m":
                metric_value = metrics.load_average[0]

            # Check threshold
            triggered = self._evaluate_condition(metric_value, rule.operator, rule.threshold)

            alert_key = f"{rule.name}_{rule.metric}"

            if triggered:
                if alert_key not in self.active_alerts:
                    # New alert
                    self.active_alerts[alert_key] = {
                        "rule": rule,
                        "first_triggered": current_time,
                        "last_triggered": current_time,
                        "trigger_count": 1,
                        "current_value": metric_value,
                    }
                else:
                    # Update existing alert
                    alert = self.active_alerts[alert_key]
                    alert["last_triggered"] = current_time
                    alert["trigger_count"] += 1
                    alert["current_value"] = metric_value

                    # Check if alert should fire (duration exceeded)
                    duration = (current_time - alert["first_triggered"]).total_seconds()
                    if duration >= rule.duration:
                        self._fire_alert(alert_key, alert)
            # Clear alert if it exists
            elif alert_key in self.active_alerts:
                self._clear_alert(alert_key)

    def _evaluate_condition(self, value: float, operator: str, threshold: float) -> bool:
        """Evaluate alert condition"""
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return value == threshold
        return False

    def _fire_alert(self, alert_key: str, alert_data: dict):
        """Fire an alert"""
        rule = alert_data["rule"]

        alert_event = {
            "timestamp": datetime.now().isoformat(),
            "alert_key": alert_key,
            "rule_name": rule.name,
            "severity": rule.severity,
            "metric": rule.metric,
            "threshold": rule.threshold,
            "current_value": alert_data["current_value"],
            "duration": rule.duration,
            "trigger_count": alert_data["trigger_count"],
            "status": "fired",
        }

        self.alert_history.append(alert_event)

        logger.error(
            f"ALERT FIRED: {rule.name} - {rule.metric}={alert_data['current_value']:.2f} "
            f"{rule.operator} {rule.threshold} (severity: {rule.severity})"
        )

    def _clear_alert(self, alert_key: str):
        """Clear an active alert"""
        if alert_key in self.active_alerts:
            alert_data = self.active_alerts[alert_key]
            rule = alert_data["rule"]

            alert_event = {
                "timestamp": datetime.now().isoformat(),
                "alert_key": alert_key,
                "rule_name": rule.name,
                "severity": rule.severity,
                "metric": rule.metric,
                "status": "cleared",
            }

            self.alert_history.append(alert_event)
            del self.active_alerts[alert_key]

            logger.info(f"ALERT CLEARED: {rule.name}")

    def get_active_alerts(self) -> list[dict]:
        """Get all active alerts"""
        return [
            {
                "alert_key": key,
                "rule_name": data["rule"].name,
                "severity": data["rule"].severity,
                "metric": data["rule"].metric,
                "threshold": data["rule"].threshold,
                "current_value": data["current_value"],
                "first_triggered": data["first_triggered"].isoformat(),
                "last_triggered": data["last_triggered"].isoformat(),
                "trigger_count": data["trigger_count"],
            }
            for key, data in self.active_alerts.items()
        ]

    def get_alert_history(self, hours: int = 24) -> list[dict]:
        """Get alert history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if datetime.fromisoformat(alert["timestamp"]) >= cutoff_time]


class SystemMonitor:
    """Main system monitor class"""

    def __init__(self, collection_interval: int = 30):
        self.metrics_collector = MetricsCollector(collection_interval)
        self.alert_manager = AlertManager()
        self.is_monitoring = False
        self._monitoring_task = None

    async def start_monitoring(self):
        """Start system monitoring"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        await self.metrics_collector.start_collection()
        self._monitoring_task = asyncio.create_task(self._monitor_loop())

        logger.info("System monitoring started")

    async def stop_monitoring(self):
        """Stop system monitoring"""
        self.is_monitoring = False
        await self.metrics_collector.stop_collection()

        if self._monitoring_task:
            self._monitoring_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitoring_task

        logger.info("System monitoring stopped")

    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                latest_metrics = self.metrics_collector.get_latest_metrics()
                if latest_metrics:
                    self.alert_manager.check_alerts(latest_metrics)

                await asyncio.sleep(10)  # TODO: Move to config  # Check alerts every 10 seconds

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)  # TODO: Move to config

    def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status"""
        latest_metrics = self.metrics_collector.get_latest_metrics()
        active_alerts = self.alert_manager.get_active_alerts()

        if not latest_metrics:
            return {"status": "no_data", "message": "No metrics available"}

        # Determine overall health
        critical_alerts = [a for a in active_alerts if a["severity"] == "critical"]
        warning_alerts = [a for a in active_alerts if a["severity"] == "warning"]

        if critical_alerts:
            overall_status = "critical"
        elif warning_alerts:
            overall_status = "warning"
        else:
            overall_status = "healthy"

        return {
            "status": overall_status,
            "timestamp": latest_metrics.timestamp.isoformat(),
            "metrics": {
                "cpu_percent": latest_metrics.cpu_percent,
                "memory_percent": latest_metrics.memory_percent,
                "memory_available_gb": latest_metrics.memory_available_gb,
                "disk_usage_percent": latest_metrics.disk_usage_percent,
                "disk_free_gb": latest_metrics.disk_free_gb,
                "active_connections": latest_metrics.active_connections,
                "process_count": latest_metrics.process_count,
                "load_average": latest_metrics.load_average,
            },
            "alerts": {
                "active_count": len(active_alerts),
                "critical_count": len(critical_alerts),
                "warning_count": len(warning_alerts),
                "active_alerts": active_alerts,
            },
            "averages_1h": self.metrics_collector.get_average_metrics(60),
        }


# Global instance
system_monitor = SystemMonitor()
