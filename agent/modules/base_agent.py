"""
Base Agent Class with Advanced ML and Self-Healing Capabilities
Enterprise-grade foundation for all DevSkyy AI agents

Features:
- Self-healing and auto-recovery mechanisms
- ML-powered anomaly detection
- Performance monitoring and optimization
- Comprehensive error handling and logging
- Health checks and diagnostics
- Metrics collection and reporting
- Circuit breaker pattern for resilience
- Adaptive learning and improvement
"""

import asyncio
import inspect
import logging
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set

import numpy as np

# Configure logging
logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent operational status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    RECOVERING = "recovering"
    FAILED = "failed"
    INITIALIZING = "initializing"


class SeverityLevel(Enum):
    """Issue severity classification"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class HealthMetrics:
    """Agent health and performance metrics"""

    success_rate: float = 100.0
    average_response_time: float = 0.0
    error_count: int = 0
    warning_count: int = 0
    total_operations: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    uptime_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0


@dataclass
class AgentMetrics:
    """Comprehensive agent metrics"""

    operations_per_minute: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    recovery_count: int = 0
    ml_predictions_made: int = 0
    anomalies_detected: int = 0
    self_healings_performed: int = 0
    performance_score: float = 100.0


@dataclass
class Issue:
    """Detected issue with metadata"""

    severity: SeverityLevel
    description: str
    detected_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution_attempted: bool = False
    resolution_strategy: Optional[str] = None


class CircuitBreaker:
    """Circuit breaker pattern for resilient operations"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is OPEN - too many failures")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return True
        return (datetime.now() - self.last_failure_time).seconds > self.timeout

    def _on_success(self):
        """Handle successful operation"""
        self.failure_count = 0
        self.state = "closed"

    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )


class BaseAgent(ABC):
    """
    Base class for all DevSkyy AI agents with ML and self-healing capabilities.

    All agents should inherit from this class to get:
    - Self-healing and error recovery
    - ML-powered anomaly detection
    - Performance monitoring
    - Health checks
    - Circuit breaker protection
    - Comprehensive logging
    """

    def __init__(self, agent_name: str, version: str = "1.0.0"):
        self.agent_name = agent_name
        self.version = version
        self.status = AgentStatus.INITIALIZING
        self.initialized_at = datetime.now()

        # Health and metrics
        self.health_metrics = HealthMetrics()
        self.agent_metrics = AgentMetrics()

        # Issue tracking
        self.detected_issues: List[Issue] = []
        self.known_errors: Set[str] = set()

        # Circuit breaker for resilience
        self.circuit_breaker = CircuitBreaker()

        # ML components
        self.anomaly_baseline: Dict[str, List[float]] = {}
        self.performance_history: List[float] = []

        # Configuration
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        self.health_check_interval = 60  # seconds
        self.auto_heal_enabled = True

        logger.info(f"🤖 {self.agent_name} v{self.version} initializing...")

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the agent. Must be implemented by subclasses.
        Returns True if initialization successful, False otherwise.
        """

    @abstractmethod
    async def execute_core_function(self, **kwargs) -> Dict[str, Any]:
        """
        Core agent functionality. Must be implemented by subclasses.
        """

    # === Self-Healing Methods ===

    def with_healing(self, func: Callable) -> Callable:
        """
        Decorator to add self-healing capabilities to any function.

        Usage:
            @agent.with_healing
            async def my_function(self, param):
                # function code
        """

        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(self.max_retries):
                try:
                    # Record start time
                    start_time = datetime.now()

                    # Execute function with circuit breaker
                    result = await self._execute_with_circuit_breaker(
                        func, *args, **kwargs
                    )

                    # Record success metrics
                    elapsed = (datetime.now() - start_time).total_seconds()
                    self._record_success(elapsed)

                    return result

                except Exception as e:
                    self._record_failure(e)

                    if attempt < self.max_retries - 1:
                        # Attempt self-healing
                        if self.auto_heal_enabled:
                            healing_result = await self._attempt_self_healing(
                                e, func.__name__
                            )
                            if healing_result["healed"]:
                                logger.info(
                                    f"✨ Self-healing successful for {func.__name__}"
                                )
                                self.agent_metrics.self_healings_performed += 1
                                await asyncio.sleep(self.retry_delay)
                                continue

                        logger.warning(
                            f"⚠️ Attempt {attempt + 1}/{self.max_retries} failed for {func.__name__}: {str(e)}"
                        )
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                    else:
                        logger.error(
                            f"❌ All retry attempts exhausted for {func.__name__}"
                        )
                        self.status = AgentStatus.FAILED
                        raise

            return {"error": "Max retries exceeded", "status": "failed"}

        return wrapper

    async def _execute_with_circuit_breaker(
        self, func: Callable, *args, **kwargs
    ) -> Any:
        """Execute function with circuit breaker protection"""
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return self.circuit_breaker.call(func, *args, **kwargs)

    async def _attempt_self_healing(
        self, error: Exception, function_name: str
    ) -> Dict[str, Any]:
        """
        Attempt to heal from an error automatically.

        Strategies:
        1. Clear caches and reset state
        2. Reinitialize connections
        3. Apply known fixes for common errors
        4. Adjust configuration based on error type
        """
        try:
            error_signature = f"{type(error).__name__}:{str(error)[:50]}"

            # Check if we've seen this error before and have a solution
            if error_signature in self.known_errors:
                logger.info(f"🔧 Applying known fix for: {error_signature}")
                await self._apply_known_fix(error_signature)
                return {"healed": True, "strategy": "known_fix"}

            # Strategy 1: Connection/Resource issues
            if any(
                keyword in str(error).lower()
                for keyword in [
                    "connection",
                    "timeout",
                    "unavailable",
                    "refused",
                    "reset",
                ]
            ):
                logger.info("🔧 Healing strategy: Reinitialize connections")
                await self._reinitialize_connections()
                return {"healed": True, "strategy": "reinit_connections"}

            # Strategy 2: Memory/Resource exhaustion
            if any(
                keyword in str(error).lower()
                for keyword in ["memory", "resource", "limit"]
            ):
                logger.info("🔧 Healing strategy: Clear caches and optimize resources")
                await self._optimize_resources()
                return {"healed": True, "strategy": "optimize_resources"}

            # Strategy 3: API rate limiting
            if any(
                keyword in str(error).lower()
                for keyword in ["rate limit", "too many requests", "quota"]
            ):
                logger.info("🔧 Healing strategy: Backoff and retry")
                await asyncio.sleep(5)  # Longer backoff for rate limits
                return {"healed": True, "strategy": "rate_limit_backoff"}

            # Strategy 4: Data validation errors
            if any(
                keyword in str(error).lower()
                for keyword in ["validation", "invalid", "malformed"]
            ):
                logger.info("🔧 Healing strategy: Reset to defaults")
                await self._reset_to_safe_defaults()
                return {"healed": True, "strategy": "reset_defaults"}

            # If no strategy worked, mark as unresolved
            self.detected_issues.append(
                Issue(
                    severity=SeverityLevel.HIGH,
                    description=f"Unresolved error in {function_name}: {str(error)}",
                )
            )

            return {"healed": False, "strategy": "none"}

        except Exception as healing_error:
            logger.error(f"Self-healing failed: {str(healing_error)}")
            return {"healed": False, "error": str(healing_error)}

    async def _reinitialize_connections(self):
        """Reinitialize all connections and external resources"""
        logger.info(f"Reinitializing {self.agent_name} connections...")
        await self.initialize()

    async def _optimize_resources(self):
        """Clear caches and optimize resource usage"""
        logger.info(f"Optimizing {self.agent_name} resources...")
        # Subclasses can override to implement specific optimization

    async def _reset_to_safe_defaults(self):
        """Reset configuration to safe default values"""
        logger.info(f"Resetting {self.agent_name} to safe defaults...")
        # Subclasses can override to implement specific resets

    async def _apply_known_fix(self, error_signature: str):
        """Apply a known fix for a specific error"""
        # Subclasses can override to implement specific fixes

    # === ML-Powered Anomaly Detection ===

    def detect_anomalies(
        self, metric_name: str, value: float, threshold: float = 2.0
    ) -> bool:
        """
        Detect anomalies using statistical methods (Z-score).

        Args:
            metric_name: Name of the metric to check
            value: Current value
            threshold: Z-score threshold for anomaly (default 2.0 = ~95% confidence)

        Returns:
            True if anomaly detected, False otherwise
        """
        if metric_name not in self.anomaly_baseline:
            self.anomaly_baseline[metric_name] = []

        baseline = self.anomaly_baseline[metric_name]
        baseline.append(value)

        # Keep only recent history (last 100 values)
        if len(baseline) > 100:
            baseline.pop(0)

        # Need at least 10 samples for meaningful analysis
        if len(baseline) < 10:
            return False

        mean = np.mean(baseline)
        std = np.std(baseline)

        if std == 0:
            return False

        z_score = abs((value - mean) / std)

        if z_score > threshold:
            logger.warning(
                f"🚨 Anomaly detected in {metric_name}: value={value}, z-score={z_score:.2f}"
            )
            self.agent_metrics.anomalies_detected += 1
            self.detected_issues.append(
                Issue(
                    severity=SeverityLevel.MEDIUM,
                    description=f"Anomaly in {metric_name}: {value} (z-score: {z_score:.2f})",
                )
            )
            return True

        return False

    def predict_performance(self) -> Dict[str, Any]:
        """
        Predict future performance based on historical data using simple linear regression.

        Returns:
            Prediction dict with forecast and confidence
        """
        if len(self.performance_history) < 10:
            return {"forecast": "insufficient_data", "confidence": 0.0}

        # Simple linear regression on recent performance
        recent_history = self.performance_history[-50:]  # Last 50 data points
        x = np.arange(len(recent_history))
        y = np.array(recent_history)

        # Calculate trend
        slope, intercept = np.polyfit(x, y, 1)
        next_value = slope * len(recent_history) + intercept

        # Calculate confidence based on variance
        variance = np.var(recent_history)
        confidence = max(0, min(100, 100 - (variance * 10)))

        trend = "improving" if slope > 0 else "declining" if slope < 0 else "stable"

        return {
            "forecast": next_value,
            "trend": trend,
            "confidence": confidence,
            "slope": slope,
        }

    # === Health Checks and Diagnostics ===

    async def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check of the agent.

        Returns detailed health status and metrics.
        """
        try:
            # Calculate uptime
            uptime = (datetime.now() - self.initialized_at).total_seconds()
            self.health_metrics.uptime_seconds = uptime

            # Calculate success rate
            total_ops = (
                self.agent_metrics.success_count + self.agent_metrics.failure_count
            )
            if total_ops > 0:
                self.health_metrics.success_rate = (
                    self.agent_metrics.success_count / total_ops
                ) * 100
            else:
                self.health_metrics.success_rate = 100.0

            # Update status based on health
            if self.health_metrics.success_rate < 50:
                self.status = AgentStatus.FAILED
            elif self.health_metrics.success_rate < 80:
                self.status = AgentStatus.DEGRADED
            elif (
                self.status == AgentStatus.FAILED or self.status == AgentStatus.DEGRADED
            ):
                self.status = AgentStatus.RECOVERING
            else:
                self.status = AgentStatus.HEALTHY

            # Collect unresolved issues
            unresolved_issues = [
                issue for issue in self.detected_issues if not issue.resolved
            ]

            return {
                "agent_name": self.agent_name,
                "version": self.version,
                "status": self.status.value,
                "health_metrics": {
                    "success_rate": round(self.health_metrics.success_rate, 2),
                    "average_response_time_ms": round(
                        self.health_metrics.average_response_time * 1000, 2
                    ),
                    "error_count": self.health_metrics.error_count,
                    "total_operations": total_ops,
                    "uptime_hours": round(uptime / 3600, 2),
                },
                "agent_metrics": {
                    "operations_per_minute": round(
                        self.agent_metrics.operations_per_minute, 2
                    ),
                    "ml_predictions_made": self.agent_metrics.ml_predictions_made,
                    "anomalies_detected": self.agent_metrics.anomalies_detected,
                    "self_healings_performed": self.agent_metrics.self_healings_performed,
                    "performance_score": round(self.agent_metrics.performance_score, 2),
                },
                "circuit_breaker": {
                    "state": self.circuit_breaker.state,
                    "failure_count": self.circuit_breaker.failure_count,
                },
                "issues": {
                    "total": len(self.detected_issues),
                    "unresolved": len(unresolved_issues),
                    "critical": len(
                        [
                            i
                            for i in unresolved_issues
                            if i.severity == SeverityLevel.CRITICAL
                        ]
                    ),
                },
                "performance_prediction": self.predict_performance(),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def diagnose_issues(self) -> Dict[str, Any]:
        """
        Diagnose current issues and recommend solutions.

        Returns detailed diagnostic report with recommendations.
        """
        unresolved = [issue for issue in self.detected_issues if not issue.resolved]

        diagnostics = {
            "agent_name": self.agent_name,
            "diagnostic_time": datetime.now().isoformat(),
            "overall_health": self.status.value,
            "issues_found": len(unresolved),
            "issues": [],
            "recommendations": [],
        }

        for issue in unresolved:
            diagnostics["issues"].append(
                {
                    "severity": issue.severity.value,
                    "description": issue.description,
                    "detected_at": issue.detected_at.isoformat(),
                    "resolution_attempted": issue.resolution_attempted,
                }
            )

        # Generate recommendations
        if self.health_metrics.success_rate < 80:
            diagnostics["recommendations"].append(
                "Consider restarting the agent to clear accumulated errors"
            )

        if self.agent_metrics.anomalies_detected > 10:
            diagnostics["recommendations"].append(
                "High number of anomalies detected - review configuration"
            )

        if self.circuit_breaker.state == "open":
            diagnostics["recommendations"].append(
                "Circuit breaker is open - external dependencies may be unavailable"
            )

        if len(diagnostics["recommendations"]) == 0:
            diagnostics["recommendations"].append("Agent is operating normally")

        return diagnostics

    # === Metrics and Monitoring ===

    def _record_success(self, elapsed_time: float):
        """Record successful operation"""
        self.agent_metrics.success_count += 1
        self.agent_metrics.operations_per_minute = self._calculate_ops_per_minute()

        # Update average response time
        total = self.agent_metrics.success_count + self.agent_metrics.failure_count
        self.health_metrics.average_response_time = (
            self.health_metrics.average_response_time * (total - 1) + elapsed_time
        ) / total

        # Record performance
        self.performance_history.append(elapsed_time)
        if len(self.performance_history) > 1000:
            self.performance_history.pop(0)

        # Detect anomalies in response time
        self.detect_anomalies("response_time", elapsed_time)

    def _record_failure(self, error: Exception):
        """Record failed operation"""
        self.agent_metrics.failure_count += 1
        self.health_metrics.error_count += 1
        self.health_metrics.last_error = str(error)
        self.health_metrics.last_error_time = datetime.now()

        # Log the error with stack trace
        logger.error(
            f"Agent {self.agent_name} error: {str(error)}\n{traceback.format_exc()}"
        )

    def _calculate_ops_per_minute(self) -> float:
        """Calculate operations per minute"""
        uptime_minutes = (datetime.now() - self.initialized_at).total_seconds() / 60
        if uptime_minutes < 1:
            return 0.0
        total_ops = self.agent_metrics.success_count + self.agent_metrics.failure_count
        return total_ops / uptime_minutes

    # === Utility Methods ===

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_name": self.agent_name,
            "version": self.version,
            "status": self.status.value,
            "initialized_at": self.initialized_at.isoformat(),
            "uptime_seconds": (datetime.now() - self.initialized_at).total_seconds(),
        }

    async def shutdown(self):
        """Graceful shutdown of the agent"""
        logger.info(f"🛑 Shutting down {self.agent_name}...")
        self.status = AgentStatus.FAILED
        # Subclasses can override to add cleanup logic
