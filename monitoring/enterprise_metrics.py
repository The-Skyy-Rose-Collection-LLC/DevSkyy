#!/usr/bin/env python3
"""
Enterprise Metrics and Alerting System for DevSkyy Platform
Comprehensive metrics collection, alerting, and dashboard integration
"""

from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import time
from typing import Any


# Prometheus imports (optional)
try:
    from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, Summary, generate_latest

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from core.logging import LogCategory, enterprise_logger


class MetricType(Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertSeverity(Enum):
    """Alert severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MetricDefinition:
    """Metric definition with metadata."""

    name: str
    metric_type: MetricType
    description: str
    labels: list[str] = field(default_factory=list)
    unit: str = ""
    help_text: str = ""


@dataclass
class AlertRule:
    """Alert rule definition."""

    name: str
    metric_name: str
    condition: str  # e.g., "> 100", "< 0.95"
    threshold: float
    severity: AlertSeverity
    duration: int = 60  # seconds
    description: str = ""
    runbook_url: str = ""


@dataclass
class Alert:
    """Active alert."""

    rule_name: str
    metric_name: str
    current_value: float
    threshold: float
    severity: AlertSeverity
    triggered_at: datetime
    description: str
    labels: dict[str, str] = field(default_factory=dict)
    resolved_at: datetime | None = None


class MetricsCollector:
    """
    Enterprise metrics collector with Prometheus integration,
    custom alerting, and dashboard support.
    """

    def __init__(self):
        self.metrics = {}
        self.alert_rules = {}
        self.active_alerts = {}
        self.metric_history = defaultdict(lambda: deque(maxlen=1000))
        self.alert_callbacks = []

        # Prometheus registry if available
        if PROMETHEUS_AVAILABLE:
            self.registry = CollectorRegistry()
            self.prometheus_metrics = {}

        # Background monitoring
        self._monitoring_active = False
        self._monitoring_thread = None

        self._initialize_core_metrics()
        self._initialize_alert_rules()

        enterprise_logger.info(
            "Metrics collector initialized",
            category=LogCategory.SYSTEM,
            metadata={"prometheus_available": PROMETHEUS_AVAILABLE},
        )

    def _initialize_core_metrics(self):
        """Initialize core application metrics."""
        core_metrics = [
            MetricDefinition(
                name="http_requests_total",
                metric_type=MetricType.COUNTER,
                description="Total HTTP requests",
                labels=["method", "endpoint", "status_code"],
                help_text="Total number of HTTP requests processed",
            ),
            MetricDefinition(
                name="http_request_duration_seconds",
                metric_type=MetricType.HISTOGRAM,
                description="HTTP request duration",
                labels=["method", "endpoint"],
                unit="seconds",
                help_text="Time spent processing HTTP requests",
            ),
            MetricDefinition(
                name="active_connections",
                metric_type=MetricType.GAUGE,
                description="Active connections",
                help_text="Number of active connections",
            ),
            MetricDefinition(
                name="memory_usage_bytes",
                metric_type=MetricType.GAUGE,
                description="Memory usage",
                unit="bytes",
                help_text="Current memory usage in bytes",
            ),
            MetricDefinition(
                name="cpu_usage_percent",
                metric_type=MetricType.GAUGE,
                description="CPU usage percentage",
                unit="percent",
                help_text="Current CPU usage percentage",
            ),
            MetricDefinition(
                name="ai_model_requests_total",
                metric_type=MetricType.COUNTER,
                description="AI model requests",
                labels=["model", "provider", "status"],
                help_text="Total AI model requests processed",
            ),
            MetricDefinition(
                name="ai_model_response_time_seconds",
                metric_type=MetricType.HISTOGRAM,
                description="AI model response time",
                labels=["model", "provider"],
                unit="seconds",
                help_text="Time spent processing AI model requests",
            ),
            MetricDefinition(
                name="database_connections_active",
                metric_type=MetricType.GAUGE,
                description="Active database connections",
                help_text="Number of active database connections",
            ),
            MetricDefinition(
                name="cache_hit_rate",
                metric_type=MetricType.GAUGE,
                description="Cache hit rate",
                unit="percent",
                help_text="Cache hit rate percentage",
            ),
            MetricDefinition(
                name="security_events_total",
                metric_type=MetricType.COUNTER,
                description="Security events",
                labels=["event_type", "severity"],
                help_text="Total security events detected",
            ),
        ]

        for metric_def in core_metrics:
            self.register_metric(metric_def)

    def _initialize_alert_rules(self):
        """Initialize default alert rules."""
        default_rules = [
            AlertRule(
                name="high_response_time",
                metric_name="http_request_duration_seconds",
                condition="> 2.0",
                threshold=2.0,
                severity=AlertSeverity.HIGH,
                duration=120,
                description="HTTP response time is too high",
                runbook_url="https://docs.devskyy.com/runbooks/high-response-time",
            ),
            AlertRule(
                name="high_error_rate",
                metric_name="http_requests_total",
                condition="> 0.05",  # 5% error rate
                threshold=0.05,
                severity=AlertSeverity.CRITICAL,
                duration=60,
                description="HTTP error rate is too high",
            ),
            AlertRule(
                name="low_memory",
                metric_name="memory_usage_bytes",
                condition="> 0.9",  # 90% memory usage
                threshold=0.9,
                severity=AlertSeverity.HIGH,
                duration=300,
                description="Memory usage is critically high",
            ),
            AlertRule(
                name="high_cpu",
                metric_name="cpu_usage_percent",
                condition="> 80",
                threshold=80,
                severity=AlertSeverity.MEDIUM,
                duration=300,
                description="CPU usage is high",
            ),
            AlertRule(
                name="ai_model_failures",
                metric_name="ai_model_requests_total",
                condition="> 0.1",  # 10% failure rate
                threshold=0.1,
                severity=AlertSeverity.HIGH,
                duration=180,
                description="AI model failure rate is too high",
            ),
            AlertRule(
                name="security_events",
                metric_name="security_events_total",
                condition="> 10",  # More than 10 security events per minute
                threshold=10,
                severity=AlertSeverity.CRITICAL,
                duration=60,
                description="High number of security events detected",
            ),
        ]

        for rule in default_rules:
            self.add_alert_rule(rule)

    def register_metric(self, metric_def: MetricDefinition):
        """Register a new metric."""
        self.metrics[metric_def.name] = metric_def

        # Create Prometheus metric if available
        if PROMETHEUS_AVAILABLE:
            self._create_prometheus_metric(metric_def)

        enterprise_logger.debug(
            f"Registered metric: {metric_def.name}",
            category=LogCategory.SYSTEM,
            metadata={"metric_type": metric_def.metric_type.value},
        )

    def _create_prometheus_metric(self, metric_def: MetricDefinition):
        """Create Prometheus metric."""
        if metric_def.metric_type == MetricType.COUNTER:
            self.prometheus_metrics[metric_def.name] = Counter(
                metric_def.name, metric_def.description, metric_def.labels, registry=self.registry
            )
        elif metric_def.metric_type == MetricType.GAUGE:
            self.prometheus_metrics[metric_def.name] = Gauge(
                metric_def.name, metric_def.description, metric_def.labels, registry=self.registry
            )
        elif metric_def.metric_type == MetricType.HISTOGRAM:
            self.prometheus_metrics[metric_def.name] = Histogram(
                metric_def.name, metric_def.description, metric_def.labels, registry=self.registry
            )
        elif metric_def.metric_type == MetricType.SUMMARY:
            self.prometheus_metrics[metric_def.name] = Summary(
                metric_def.name, metric_def.description, metric_def.labels, registry=self.registry
            )

    def increment_counter(self, metric_name: str, value: float = 1, labels: dict[str, str] | None = None):
        """Increment a counter metric."""
        if metric_name not in self.metrics:
            enterprise_logger.warning(f"Unknown metric: {metric_name}", category=LogCategory.SYSTEM)
            return

        # Store in history
        self.metric_history[metric_name].append(
            {"timestamp": datetime.utcnow(), "value": value, "labels": labels or {}}
        )

        # Update Prometheus metric
        if PROMETHEUS_AVAILABLE and metric_name in self.prometheus_metrics:
            if labels:
                self.prometheus_metrics[metric_name].labels(**labels).inc(value)
            else:
                self.prometheus_metrics[metric_name].inc(value)

    def set_gauge(self, metric_name: str, value: float, labels: dict[str, str] | None = None):
        """Set a gauge metric value."""
        if metric_name not in self.metrics:
            enterprise_logger.warning(f"Unknown metric: {metric_name}", category=LogCategory.SYSTEM)
            return

        # Store in history
        self.metric_history[metric_name].append(
            {"timestamp": datetime.utcnow(), "value": value, "labels": labels or {}}
        )

        # Update Prometheus metric
        if PROMETHEUS_AVAILABLE and metric_name in self.prometheus_metrics:
            if labels:
                self.prometheus_metrics[metric_name].labels(**labels).set(value)
            else:
                self.prometheus_metrics[metric_name].set(value)

        # Check alert rules
        self._check_alert_rules(metric_name, value, labels or {})

    def observe_histogram(self, metric_name: str, value: float, labels: dict[str, str] | None = None):
        """Observe a histogram metric."""
        if metric_name not in self.metrics:
            enterprise_logger.warning(f"Unknown metric: {metric_name}", category=LogCategory.SYSTEM)
            return

        # Store in history
        self.metric_history[metric_name].append(
            {"timestamp": datetime.utcnow(), "value": value, "labels": labels or {}}
        )

        # Update Prometheus metric
        if PROMETHEUS_AVAILABLE and metric_name in self.prometheus_metrics:
            if labels:
                self.prometheus_metrics[metric_name].labels(**labels).observe(value)
            else:
                self.prometheus_metrics[metric_name].observe(value)

        # Check alert rules
        self._check_alert_rules(metric_name, value, labels or {})

    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.alert_rules[rule.name] = rule
        enterprise_logger.info(
            f"Added alert rule: {rule.name}",
            category=LogCategory.SYSTEM,
            metadata={"metric": rule.metric_name, "threshold": rule.threshold, "severity": rule.severity.value},
        )

    def _check_alert_rules(self, metric_name: str, value: float, labels: dict[str, str]):
        """Check if any alert rules are triggered."""
        for rule_name, rule in self.alert_rules.items():
            if rule.metric_name != metric_name:
                continue

            # Simple condition checking (could be more sophisticated)
            triggered = False
            if rule.condition.startswith(">"):
                triggered = value > rule.threshold
            elif rule.condition.startswith("<"):
                triggered = value < rule.threshold
            elif rule.condition.startswith(">="):
                triggered = value >= rule.threshold
            elif rule.condition.startswith("<="):
                triggered = value <= rule.threshold

            if triggered:
                self._trigger_alert(rule, value, labels)
            else:
                self._resolve_alert(rule_name)

    def _trigger_alert(self, rule: AlertRule, current_value: float, labels: dict[str, str]):
        """Trigger an alert."""
        alert_key = f"{rule.name}_{hash(frozenset(labels.items()))}"

        if alert_key not in self.active_alerts:
            alert = Alert(
                rule_name=rule.name,
                metric_name=rule.metric_name,
                current_value=current_value,
                threshold=rule.threshold,
                severity=rule.severity,
                triggered_at=datetime.utcnow(),
                description=rule.description,
                labels=labels,
            )

            self.active_alerts[alert_key] = alert

            # Log alert
            enterprise_logger.error(
                f"Alert triggered: {rule.name}",
                category=LogCategory.SYSTEM,
                metadata={
                    "metric": rule.metric_name,
                    "current_value": current_value,
                    "threshold": rule.threshold,
                    "severity": rule.severity.value,
                    "labels": labels,
                },
            )

            # Notify callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    enterprise_logger.error(f"Alert callback failed: {e}", category=LogCategory.SYSTEM, error=e)

    def _resolve_alert(self, rule_name: str):
        """Resolve an alert."""
        alerts_to_resolve = [key for key in self.active_alerts if self.active_alerts[key].rule_name == rule_name]

        for alert_key in alerts_to_resolve:
            alert = self.active_alerts[alert_key]
            alert.resolved_at = datetime.utcnow()

            enterprise_logger.info(
                f"Alert resolved: {rule_name}",
                category=LogCategory.SYSTEM,
                metadata={"duration": (alert.resolved_at - alert.triggered_at).total_seconds()},
            )

            del self.active_alerts[alert_key]

    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add alert notification callback."""
        self.alert_callbacks.append(callback)

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get metrics summary."""
        return {
            "registered_metrics": len(self.metrics),
            "alert_rules": len(self.alert_rules),
            "active_alerts": len(self.active_alerts),
            "prometheus_available": PROMETHEUS_AVAILABLE,
            "metrics": list(self.metrics.keys()),
            "active_alert_names": [alert.rule_name for alert in self.active_alerts.values()],
        }

    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in text format."""
        if PROMETHEUS_AVAILABLE:
            return generate_latest(self.registry).decode("utf-8")
        return "# Prometheus not available\n"

    def start_monitoring(self):
        """Start background monitoring."""
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()

        enterprise_logger.info("Background monitoring started", category=LogCategory.SYSTEM)

    def stop_monitoring(self):
        """Stop background monitoring."""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)

        enterprise_logger.info("Background monitoring stopped", category=LogCategory.SYSTEM)

    def _monitoring_loop(self):
        """Background monitoring loop."""
        while self._monitoring_active:
            try:
                # Collect system metrics
                self._collect_system_metrics()
                time.sleep(30)  # Collect every 30 seconds
            except Exception as e:
                enterprise_logger.error(f"Monitoring loop error: {e}", category=LogCategory.SYSTEM, error=e)
                time.sleep(60)  # Wait longer on error

    def _collect_system_metrics(self):
        """Collect system metrics."""
        try:
            import psutil

            # Memory usage
            memory = psutil.virtual_memory()
            self.set_gauge("memory_usage_bytes", memory.used)

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.set_gauge("cpu_usage_percent", cpu_percent)

        except ImportError:
            # psutil not available
            pass
        except Exception as e:
            enterprise_logger.error(f"System metrics collection failed: {e}", category=LogCategory.SYSTEM, error=e)


# Global metrics collector instance
metrics_collector = MetricsCollector()


# Convenience functions
def increment_counter(metric_name: str, value: float = 1, **labels):
    """Increment counter metric."""
    metrics_collector.increment_counter(metric_name, value, labels)


def set_gauge(metric_name: str, value: float, **labels):
    """Set gauge metric."""
    metrics_collector.set_gauge(metric_name, value, labels)


def observe_histogram(metric_name: str, value: float, **labels):
    """Observe histogram metric."""
    metrics_collector.observe_histogram(metric_name, value, labels)


# Start monitoring on import
metrics_collector.start_monitoring()
