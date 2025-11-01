from datetime import datetime
import time

from pydantic import BaseModel

from collections import defaultdict, deque
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import asyncio
import logging
import psutil

"""
Enterprise Observability & Monitoring System
Metrics, traces, logs, and health checks for production systems
"""

logger = logging.getLogger(__name__)

# ============================================================================
# MODELS
# ============================================================================

class MetricType(str, Enum):
    """Metric type enumeration"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class Metric(BaseModel):
    """Metric data model"""

    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = {}
    timestamp: datetime

class HealthStatus(str, Enum):
    """Health status enumeration"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class HealthCheck(BaseModel):
    """Health check result"""

    component: str
    status: HealthStatus
    message: str
    latency_ms: float
    timestamp: datetime
    metadata: Dict[str, Any] = {}

# ============================================================================
# METRICS COLLECTOR
# ============================================================================

class MetricsCollector:
    """
    Collect and aggregate metrics
    """

    def __init__(self, retention_minutes: int = 60):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)

        self.retention_minutes = retention_minutes
        self.start_time = time.time()

        logger.info("📊 Metrics Collector initialized")

    # ========================================================================
    # METRIC RECORDING
    # ========================================================================

    def increment_counter(
        self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None
    ):
        """Increment a counter metric"""
        key = self._make_key(name, labels)
        self.counters[key] += value

        self._record_metric(name, MetricType.COUNTER, self.counters[key], labels or {})

    def set_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """Set a gauge metric"""
        key = self._make_key(name, labels)
        self.gauges[key] = value

        self._record_metric(name, MetricType.GAUGE, value, labels or {})

    def record_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """Record a histogram value"""
        key = self._make_key(name, labels)
        self.histograms[key].append(value)

        # Keep only recent values
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-1000:]

        self._record_metric(name, MetricType.HISTOGRAM, value, labels or {})

    def _record_metric(
        self, name: str, metric_type: MetricType, value: float, labels: Dict[str, str]
    ):
        """Record a metric data point"""
        metric = Metric(
            name=name,
            type=metric_type,
            value=value,
            labels=labels,
            timestamp=datetime.now(),
        )

        self.metrics[name].append(metric)

    @staticmethod
    def _make_key(name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create a unique key for a metric with labels"""
        if not labels:
            return name

        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    # ========================================================================
    # METRIC QUERIES
    # ========================================================================

    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current counter value"""
        key = self._make_key(name, labels)
        return self.counters.get(key, 0.0)

    def get_gauge(
        self, name: str, labels: Optional[Dict[str, str]] = None
    ) -> Optional[float]:
        """Get current gauge value"""
        key = self._make_key(name, labels)
        return self.gauges.get(key)

    def get_histogram_stats(
        self, name: str, labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """Get histogram statistics"""
        key = self._make_key(name, labels)
        values = self.histograms.get(key, [])

        if not values:
            return {"count": 0}

        sorted_values = sorted(values)
        count = len(sorted_values)

        return {
            "count": count,
            "sum": sum(sorted_values),
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "mean": sum(sorted_values) / count,
            "p50": sorted_values[int(count * 0.5)],
            "p95": sorted_values[int(count * 0.95)],
            "p99": sorted_values[int(count * 0.99)],
        }

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics"""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {
                k: self.get_histogram_stats(k) for k in self.histograms.keys()
            },
            "uptime_seconds": time.time() - self.start_time,
        }

    # ========================================================================
    # SYSTEM METRICS
    # ========================================================================

    def collect_system_metrics(self):
        """Collect system-level metrics"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        self.set_gauge("system_cpu_percent", cpu_percent)

        # Memory
        memory = psutil.virtual_memory()
        self.set_gauge("system_memory_percent", memory.percent)
        self.set_gauge("system_memory_available_mb", memory.available / 1024 / 1024)

        # Disk
        disk = psutil.disk_usage("/")
        self.set_gauge("system_disk_percent", disk.percent)
        self.set_gauge("system_disk_free_gb", disk.free / 1024 / 1024 / 1024)

        # Network (if available)
        try:
            net_io = psutil.net_io_counters()
            self.set_gauge("system_network_sent_mb", net_io.bytes_sent / 1024 / 1024)
            self.set_gauge("system_network_recv_mb", net_io.bytes_recv / 1024 / 1024)
        except Exception as e:
    logger.warning(f"Handled exception: {e}")

# ============================================================================
# HEALTH MONITOR
# ============================================================================

class HealthMonitor:
    """
    Monitor system health
    """

    def __init__(self):
        self.health_checks: Dict[str, Callable] = {}
        self.last_results: Dict[str, HealthCheck] = {}

        logger.info("🏥 Health Monitor initialized")

    def register_check(self, name: str, check_func: Callable):
        """
        Register a health check

        Args:
            name: Check name
            check_func: Async function that returns (status, message)
        """
        self.health_checks[name] = check_func
        logger.info(f"Registered health check: {name}")

    async def run_check(self, name: str) -> HealthCheck:
        """Run a single health check"""
        if name not in self.health_checks:
            return HealthCheck(
                component=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check '{name}' not found",
                latency_ms=0,
                timestamp=datetime.now(),
            )

        start = time.time()

        try:
            check_func = self.health_checks[name]
            status, message, metadata = await check_func()

            latency_ms = (time.time() - start) * 1000

            result = HealthCheck(
                component=name,
                status=status,
                message=message,
                latency_ms=latency_ms,
                timestamp=datetime.now(),
                metadata=metadata or {},
            )

        except Exception as e:
            latency_ms = (time.time() - start) * 1000

            result = HealthCheck(
                component=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {str(e)}",
                latency_ms=latency_ms,
                timestamp=datetime.now(),
            )

        self.last_results[name] = result
        return result

    async def run_all_checks(self) -> Dict[str, HealthCheck]:
        """Run all health checks"""
        tasks = [self.run_check(name) for name in self.health_checks.keys()]
        results = await asyncio.gather(*tasks)

        return {result.component: result for result in results}

    def get_overall_status(self) -> Tuple[HealthStatus, str]:
        """Get overall system health status"""
        if not self.last_results:
            return HealthStatus.UNHEALTHY, "No health checks configured"

        statuses = [check.status for check in self.last_results.values()]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY, "All systems operational"

        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            unhealthy = [
                name
                for name, check in self.last_results.items()
                if check.status == HealthStatus.UNHEALTHY
            ]
            return (
                HealthStatus.UNHEALTHY,
                f"Unhealthy components: {', '.join(unhealthy)}",
            )

        degraded = [
            name
            for name, check in self.last_results.items()
            if check.status == HealthStatus.DEGRADED
        ]
        return HealthStatus.DEGRADED, f"Degraded components: {', '.join(degraded)}"

# ============================================================================
# PERFORMANCE TRACKER
# ============================================================================

class PerformanceTracker:
    """
    Track API endpoint performance
    """

    def __init__(self):
        self.endpoint_metrics: Dict[str, List[float]] = defaultdict(list)
        self.request_count: Dict[str, int] = defaultdict(int)
        self.error_count: Dict[str, int] = defaultdict(int)

        logger.info("⚡ Performance Tracker initialized")

    def record_request(self, endpoint: str, duration_ms: float, status_code: int):
        """Record API request"""
        self.endpoint_metrics[endpoint].append(duration_ms)
        self.request_count[endpoint] += 1

        if status_code >= 400:
            self.error_count[endpoint] += 1

        # Keep only last 1000 requests per endpoint
        if len(self.endpoint_metrics[endpoint]) > 1000:
            self.endpoint_metrics[endpoint] = self.endpoint_metrics[endpoint][-1000:]

    def get_endpoint_stats(self, endpoint: str) -> Dict[str, Any]:
        """Get statistics for an endpoint"""
        durations = self.endpoint_metrics.get(endpoint, [])

        if not durations:
            return {"requests": 0}

        sorted_durations = sorted(durations)
        count = len(sorted_durations)

        return {
            "requests": self.request_count[endpoint],
            "errors": self.error_count[endpoint],
            "error_rate": (
                (self.error_count[endpoint] / self.request_count[endpoint] * 100)
                if self.request_count[endpoint] > 0
                else 0
            ),
            "latency_ms": {
                "min": sorted_durations[0],
                "max": sorted_durations[-1],
                "mean": sum(sorted_durations) / count,
                "p50": sorted_durations[int(count * 0.5)],
                "p95": sorted_durations[int(count * 0.95)],
                "p99": sorted_durations[int(count * 0.99)],
            },
        }

    def get_all_stats(self) -> Dict[str, Any]:
        """Get all endpoint statistics"""
        return {
            endpoint: self.get_endpoint_stats(endpoint)
            for endpoint in self.endpoint_metrics.keys()
        }

# ============================================================================
# DISTRIBUTED TRACING
# ============================================================================

class Span:
    """Trace span"""

    def __init__(
        self,
        trace_id: str,
        span_id: str,
        operation: str,
        parent_id: Optional[str] = None,
    ):
        self.trace_id = trace_id
        self.span_id = span_id
        self.operation = operation
        self.parent_id = parent_id
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.tags: Dict[str, Any] = {}
        self.logs: List[Dict[str, Any]] = []

    def set_tag(self, key: str, value: Any):
        """Add a tag to the span"""
        self.tags[key] = value

    def log(self, message: str, **fields):
        """Add a log to the span"""
        self.logs.append({"timestamp": time.time(), "message": message, **fields})

    def finish(self):
        """Finish the span"""
        self.end_time = time.time()

    def duration_ms(self) -> float:
        """Get span duration in milliseconds"""
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000

# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

metrics_collector = MetricsCollector()
health_monitor = HealthMonitor()
performance_tracker = PerformanceTracker()

logger.info("📊 Enterprise Observability System initialized")
