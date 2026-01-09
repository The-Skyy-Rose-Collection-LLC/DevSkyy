"""
Prometheus Metrics Exporter for DevSkyy Security Monitoring
Provides security event tracking, threat scoring, and API performance metrics.
"""

import time
from typing import Any

from prometheus_client import Counter, Gauge, Histogram, generate_latest
from prometheus_client.core import CollectorRegistry

# Custom registry for DevSkyy metrics
devskyy_registry = CollectorRegistry()

# Counter: Security Events Total
# Tracks all security-related events with labels for event type and severity
security_events_total = Counter(
    "security_events_total",
    "Total count of security events",
    ["event_type", "severity", "source_ip", "endpoint"],
    registry=devskyy_registry,
)

# Gauge: Current Threat Score
# Tracks the current threat score for different sources
threat_score = Gauge(
    "threat_score",
    "Current threat score (0-100)",
    ["source_ip", "user_id"],
    registry=devskyy_registry,
)

# Histogram: API Request Duration
# Tracks API request processing time in seconds
api_request_duration_seconds = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint", "status_code"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
    registry=devskyy_registry,
)

# Counter: Authentication Events
# Tracks login attempts, successes, and failures
auth_events_total = Counter(
    "auth_events_total",
    "Total count of authentication events",
    ["event_type", "method", "result"],
    registry=devskyy_registry,
)

# Counter: Input Validation Failures
# Tracks failed input validation attempts (potential attacks)
input_validation_failures_total = Counter(
    "input_validation_failures_total",
    "Total count of input validation failures",
    ["validation_type", "field", "endpoint"],
    registry=devskyy_registry,
)

# Gauge: Active Sessions
# Tracks number of active user sessions
active_sessions = Gauge(
    "active_sessions", "Number of active user sessions", ["session_type"], registry=devskyy_registry
)

# Counter: Rate Limit Events
# Tracks rate limiting events
rate_limit_events_total = Counter(
    "rate_limit_events_total",
    "Total count of rate limiting events",
    ["action", "limit_type", "source_ip"],
    registry=devskyy_registry,
)

# Histogram: Database Query Duration
# Tracks database query execution time
db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type", "table"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=devskyy_registry,
)

# Gauge: Cache Hit Rate
# Tracks cache performance
cache_hit_rate = Gauge(
    "cache_hit_rate", "Cache hit rate percentage (0-100)", ["cache_type"], registry=devskyy_registry
)

# =============================================================================
# LLM Round Table Metrics
# =============================================================================

# Counter: Round Table Competitions
round_table_competitions_total = Counter(
    "round_table_competitions_total",
    "Total number of LLM Round Table competitions",
    ["winner_provider", "use_production"],
    registry=devskyy_registry,
)

# Counter: Round Table Provider Participations
round_table_provider_participations = Counter(
    "round_table_provider_participations_total",
    "Total provider participations in Round Table",
    ["provider", "outcome"],  # outcome: winner, finalist, participant
    registry=devskyy_registry,
)

# Histogram: Round Table Competition Duration
round_table_duration_seconds = Histogram(
    "round_table_duration_seconds",
    "Round Table competition duration in seconds",
    ["use_production"],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0),
    registry=devskyy_registry,
)

# Histogram: Round Table Provider Latency
round_table_provider_latency_ms = Histogram(
    "round_table_provider_latency_ms",
    "Individual provider response latency in milliseconds",
    ["provider"],
    buckets=(100, 250, 500, 1000, 2000, 5000, 10000, 20000),
    registry=devskyy_registry,
)

# Gauge: Round Table Provider Win Rate
round_table_provider_win_rate = Gauge(
    "round_table_provider_win_rate",
    "Provider win rate in Round Table (0-1)",
    ["provider"],
    registry=devskyy_registry,
)

# Counter: Round Table Errors
round_table_errors_total = Counter(
    "round_table_errors_total",
    "Total Round Table errors",
    ["error_type", "provider"],
    registry=devskyy_registry,
)


class PrometheusExporter:
    """
    Prometheus metrics exporter for DevSkyy security and performance monitoring.
    """

    def __init__(self) -> None:
        """Initialize the Prometheus exporter."""
        self.registry = devskyy_registry
        self._request_start_times: dict[str, float] = {}

    def record_security_event(
        self,
        event_type: str,
        severity: str = "info",
        source_ip: str = "unknown",
        endpoint: str = "unknown",
    ) -> None:
        """
        Record a security event.

        Args:
            event_type: Type of security event (e.g., 'failed_login', 'sql_injection_attempt')
            severity: Severity level ('info', 'warning', 'critical')
            source_ip: Source IP address
            endpoint: API endpoint involved
        """
        security_events_total.labels(
            event_type=event_type, severity=severity, source_ip=source_ip, endpoint=endpoint
        ).inc()

    def update_threat_score(
        self, score: float, source_ip: str = "unknown", user_id: str = "anonymous"
    ) -> None:
        """
        Update the threat score for a source.

        Args:
            score: Threat score (0-100)
            source_ip: Source IP address
            user_id: User identifier
        """
        threat_score.labels(source_ip=source_ip, user_id=user_id).set(score)

    def record_api_request(
        self, duration: float, method: str, endpoint: str, status_code: int
    ) -> None:
        """
        Record an API request duration.

        Args:
            duration: Request duration in seconds
            method: HTTP method
            endpoint: API endpoint
            status_code: HTTP status code
        """
        api_request_duration_seconds.labels(
            method=method, endpoint=endpoint, status_code=str(status_code)
        ).observe(duration)

    def start_api_request(self, request_id: str) -> None:
        """
        Mark the start time of an API request.

        Args:
            request_id: Unique identifier for the request
        """
        self._request_start_times[request_id] = time.time()

    def finish_api_request(
        self, request_id: str, method: str, endpoint: str, status_code: int
    ) -> float | None:
        """
        Mark the end time of an API request and record duration.

        Args:
            request_id: Unique identifier for the request
            method: HTTP method
            endpoint: API endpoint
            status_code: HTTP status code

        Returns:
            Request duration in seconds, or None if request_id not found
        """
        start_time = self._request_start_times.pop(request_id, None)
        if start_time is None:
            return None

        duration = time.time() - start_time
        self.record_api_request(duration, method, endpoint, status_code)
        return duration

    def record_auth_event(
        self, event_type: str, method: str = "password", result: str = "success"
    ) -> None:
        """
        Record an authentication event.

        Args:
            event_type: Type of auth event ('login', 'logout', 'token_refresh')
            method: Auth method ('password', 'oauth', 'api_key')
            result: Result ('success', 'failure', 'blocked')
        """
        auth_events_total.labels(event_type=event_type, method=method, result=result).inc()

    def record_validation_failure(self, validation_type: str, field: str, endpoint: str) -> None:
        """
        Record an input validation failure.

        Args:
            validation_type: Type of validation that failed
            field: Field that failed validation
            endpoint: API endpoint
        """
        input_validation_failures_total.labels(
            validation_type=validation_type, field=field, endpoint=endpoint
        ).inc()

    def set_active_sessions(self, count: int, session_type: str = "user") -> None:
        """
        Set the number of active sessions.

        Args:
            count: Number of active sessions
            session_type: Type of session ('user', 'admin', 'api')
        """
        active_sessions.labels(session_type=session_type).set(count)

    def record_rate_limit_event(
        self, action: str, limit_type: str, source_ip: str = "unknown"
    ) -> None:
        """
        Record a rate limiting event.

        Args:
            action: Action taken ('allowed', 'throttled', 'blocked')
            limit_type: Type of rate limit ('api', 'login', 'signup')
            source_ip: Source IP address
        """
        rate_limit_events_total.labels(
            action=action, limit_type=limit_type, source_ip=source_ip
        ).inc()

    def record_db_query(self, duration: float, query_type: str, table: str = "unknown") -> None:
        """
        Record a database query duration.

        Args:
            duration: Query duration in seconds
            query_type: Type of query ('select', 'insert', 'update', 'delete')
            table: Database table name
        """
        db_query_duration_seconds.labels(query_type=query_type, table=table).observe(duration)

    def update_cache_hit_rate(self, hit_rate: float, cache_type: str = "redis") -> None:
        """
        Update the cache hit rate.

        Args:
            hit_rate: Hit rate percentage (0-100)
            cache_type: Type of cache ('redis', 'memory', 'cdn')
        """
        cache_hit_rate.labels(cache_type=cache_type).set(hit_rate)

    # =========================================================================
    # LLM Round Table Metrics
    # =========================================================================

    def record_round_table_competition(
        self,
        winner_provider: str,
        duration_seconds: float,
        use_production: bool = True,
    ) -> None:
        """
        Record a Round Table competition result.

        Args:
            winner_provider: The winning LLM provider
            duration_seconds: Total competition duration
            use_production: Whether production Round Table was used
        """
        round_table_competitions_total.labels(
            winner_provider=winner_provider,
            use_production=str(use_production).lower(),
        ).inc()
        round_table_duration_seconds.labels(use_production=str(use_production).lower()).observe(
            duration_seconds
        )

    def record_round_table_provider(
        self,
        provider: str,
        outcome: str,
        latency_ms: float,
    ) -> None:
        """
        Record a provider's participation in Round Table.

        Args:
            provider: LLM provider name
            outcome: 'winner', 'finalist', or 'participant'
            latency_ms: Provider response latency in milliseconds
        """
        round_table_provider_participations.labels(
            provider=provider,
            outcome=outcome,
        ).inc()
        round_table_provider_latency_ms.labels(provider=provider).observe(latency_ms)

    def update_round_table_win_rate(self, provider: str, win_rate: float) -> None:
        """
        Update a provider's win rate.

        Args:
            provider: LLM provider name
            win_rate: Win rate (0-1)
        """
        round_table_provider_win_rate.labels(provider=provider).set(win_rate)

    def record_round_table_error(self, error_type: str, provider: str = "unknown") -> None:
        """
        Record a Round Table error.

        Args:
            error_type: Type of error (e.g., 'timeout', 'api_error', 'parse_error')
            provider: Provider that caused the error
        """
        round_table_errors_total.labels(error_type=error_type, provider=provider).inc()

    def generate_metrics(self) -> bytes:
        """
        Generate Prometheus metrics in text format.

        Returns:
            Metrics in Prometheus text format
        """
        return generate_latest(self.registry)

    def get_metrics_dict(self) -> dict[str, Any]:
        """
        Get current metrics as a dictionary (for debugging/monitoring).

        Returns:
            Dictionary of current metric values
        """
        metrics = {}
        for metric in self.registry.collect():
            metrics[metric.name] = {
                "type": metric.type,
                "documentation": metric.documentation,
                "samples": [
                    {"name": sample.name, "labels": dict(sample.labels), "value": sample.value}
                    for sample in metric.samples
                ],
            }
        return metrics


# Global exporter instance
exporter = PrometheusExporter()


def get_metrics() -> bytes:
    """
    Get Prometheus metrics in text format.

    Returns:
        Metrics in Prometheus text format
    """
    return exporter.generate_metrics()


def record_security_event(
    event_type: str, severity: str = "info", source_ip: str = "unknown", endpoint: str = "unknown"
) -> None:
    """
    Convenience function to record a security event.

    Args:
        event_type: Type of security event
        severity: Severity level
        source_ip: Source IP address
        endpoint: API endpoint involved
    """
    exporter.record_security_event(event_type, severity, source_ip, endpoint)


def update_threat_score(
    score: float, source_ip: str = "unknown", user_id: str = "anonymous"
) -> None:
    """
    Convenience function to update threat score.

    Args:
        score: Threat score (0-100)
        source_ip: Source IP address
        user_id: User identifier
    """
    exporter.update_threat_score(score, source_ip, user_id)
