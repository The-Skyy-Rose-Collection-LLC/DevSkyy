#!/usr/bin/env python3
"""
DevSkyy Security Metrics Verification
Purpose: Query Prometheus for security metrics and generate comprehensive report
Usage: python verify_security_metrics.py
"""

import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Optional

import requests


@dataclass
class SecurityMetric:
    """Security metric data structure"""

    name: str
    value: float
    unit: str
    status: str  # ok, warning, critical
    threshold: Optional[float] = None
    timestamp: Optional[str] = None


@dataclass
class MetricsReport:
    """Complete metrics report structure"""

    timestamp: str
    duration_minutes: int
    failed_login_attempts: SecurityMetric
    rate_limit_violations: SecurityMetric
    request_signing_failures: SecurityMetric
    threat_score: SecurityMetric
    active_sessions: SecurityMetric
    blocked_ips: SecurityMetric
    sql_injection_attempts: SecurityMetric
    unauthorized_access: SecurityMetric
    overall_status: str
    recommendations: list[str]


class PrometheusClient:
    """Client for querying Prometheus API"""

    def __init__(self, base_url: str = "http://localhost:9090"):
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api/v1"

    def query(self, query: str) -> dict[str, Any]:
        """Execute a Prometheus query"""
        try:
            response = requests.get(f"{self.api_url}/query", params={"query": query}, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error querying Prometheus: {e}")
            return {"status": "error", "data": {"result": []}}

    def query_range(
        self, query: str, start: datetime, end: datetime, step: str = "1m"
    ) -> dict[str, Any]:
        """Execute a Prometheus range query"""
        try:
            response = requests.get(
                f"{self.api_url}/query_range",
                params={
                    "query": query,
                    "start": start.timestamp(),
                    "end": end.timestamp(),
                    "step": step,
                },
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error querying Prometheus range: {e}")
            return {"status": "error", "data": {"result": []}}

    def check_health(self) -> bool:
        """Check if Prometheus is healthy"""
        try:
            response = requests.get(f"{self.base_url}/-/healthy", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False


class SecurityMetricsVerifier:
    """Main class for verifying security metrics"""

    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        self.client = PrometheusClient(prometheus_url)
        self.report_dir = "monitoring_logs"
        os.makedirs(self.report_dir, exist_ok=True)

    def evaluate_status(
        self, value: float, warning_threshold: float, critical_threshold: float
    ) -> str:
        """Evaluate metric status based on thresholds"""
        if value >= critical_threshold:
            return "critical"
        elif value >= warning_threshold:
            return "warning"
        else:
            return "ok"

    def get_failed_login_attempts(self, duration_minutes: int = 15) -> SecurityMetric:
        """Get failed login attempt metrics"""
        print("Querying failed login attempts...")

        # Query rate over the last duration
        query = f"rate(security_failed_login_attempts[{duration_minutes}m])"
        result = self.client.query(query)

        value = 0.0
        if result.get("status") == "success" and result["data"]["result"]:
            value = float(result["data"]["result"][0]["value"][1])

        # Also get total count
        total_query = f"increase(security_failed_login_attempts[{duration_minutes}m])"
        total_result = self.client.query(total_query)

        total = 0.0
        if total_result.get("status") == "success" and total_result["data"]["result"]:
            total = float(total_result["data"]["result"][0]["value"][1])

        status = self.evaluate_status(total, warning_threshold=5, critical_threshold=10)

        return SecurityMetric(
            name="Failed Login Attempts",
            value=total,
            unit="attempts",
            status=status,
            threshold=10.0,
            timestamp=datetime.utcnow().isoformat(),
        )

    def get_rate_limit_violations(self, duration_minutes: int = 15) -> SecurityMetric:
        """Get rate limit violation metrics"""
        print("Querying rate limit violations...")

        query = f"increase(security_rate_limit_exceeded_total[{duration_minutes}m])"
        result = self.client.query(query)

        value = 0.0
        if result.get("status") == "success" and result["data"]["result"]:
            value = float(result["data"]["result"][0]["value"][1])

        status = self.evaluate_status(value, warning_threshold=10, critical_threshold=50)

        return SecurityMetric(
            name="Rate Limit Violations",
            value=value,
            unit="violations",
            status=status,
            threshold=50.0,
            timestamp=datetime.utcnow().isoformat(),
        )

    def get_request_signing_failures(self, duration_minutes: int = 15) -> SecurityMetric:
        """Get request signing failure metrics"""
        print("Querying request signing failures...")

        query = f"increase(security_signature_verification_failed_total[{duration_minutes}m])"
        result = self.client.query(query)

        value = 0.0
        if result.get("status") == "success" and result["data"]["result"]:
            value = float(result["data"]["result"][0]["value"][1])

        status = self.evaluate_status(value, warning_threshold=5, critical_threshold=20)

        return SecurityMetric(
            name="Request Signing Failures",
            value=value,
            unit="failures",
            status=status,
            threshold=20.0,
            timestamp=datetime.utcnow().isoformat(),
        )

    def get_threat_score(self) -> SecurityMetric:
        """Get current threat score"""
        print("Querying threat score...")

        query = "security_threat_score"
        result = self.client.query(query)

        value = 0.0
        if result.get("status") == "success" and result["data"]["result"]:
            value = float(result["data"]["result"][0]["value"][1])

        status = self.evaluate_status(value, warning_threshold=50, critical_threshold=75)

        return SecurityMetric(
            name="Threat Score",
            value=value,
            unit="score",
            status=status,
            threshold=75.0,
            timestamp=datetime.utcnow().isoformat(),
        )

    def get_active_sessions(self) -> SecurityMetric:
        """Get active session count"""
        print("Querying active sessions...")

        query = "security_active_sessions"
        result = self.client.query(query)

        value = 0.0
        if result.get("status") == "success" and result["data"]["result"]:
            value = float(result["data"]["result"][0]["value"][1])

        # For sessions, high is not necessarily bad, but we track it
        status = "ok" if value < 1000 else "warning"

        return SecurityMetric(
            name="Active Sessions",
            value=value,
            unit="sessions",
            status=status,
            threshold=1000.0,
            timestamp=datetime.utcnow().isoformat(),
        )

    def get_blocked_ips(self, duration_minutes: int = 60) -> SecurityMetric:
        """Get blocked IP count"""
        print("Querying blocked IPs...")

        query = f"increase(security_blocked_ips_total[{duration_minutes}m])"
        result = self.client.query(query)

        value = 0.0
        if result.get("status") == "success" and result["data"]["result"]:
            value = float(result["data"]["result"][0]["value"][1])

        # High blocked IPs might indicate attack
        status = self.evaluate_status(value, warning_threshold=10, critical_threshold=50)

        return SecurityMetric(
            name="Blocked IPs",
            value=value,
            unit="ips",
            status=status,
            threshold=50.0,
            timestamp=datetime.utcnow().isoformat(),
        )

    def get_sql_injection_attempts(self, duration_minutes: int = 15) -> SecurityMetric:
        """Get SQL injection attempt count"""
        print("Querying SQL injection attempts...")

        query = f"increase(security_injection_attempts_total[{duration_minutes}m])"
        result = self.client.query(query)

        value = 0.0
        if result.get("status") == "success" and result["data"]["result"]:
            value = float(result["data"]["result"][0]["value"][1])

        # Any SQL injection attempt is concerning
        status = "critical" if value > 0 else "ok"

        return SecurityMetric(
            name="SQL Injection Attempts",
            value=value,
            unit="attempts",
            status=status,
            threshold=0.0,
            timestamp=datetime.utcnow().isoformat(),
        )

    def get_unauthorized_access(self, duration_minutes: int = 15) -> SecurityMetric:
        """Get unauthorized access attempt count"""
        print("Querying unauthorized access attempts...")

        query = f"increase(security_access_denied_total[{duration_minutes}m])"
        result = self.client.query(query)

        value = 0.0
        if result.get("status") == "success" and result["data"]["result"]:
            value = float(result["data"]["result"][0]["value"][1])

        status = self.evaluate_status(value, warning_threshold=20, critical_threshold=100)

        return SecurityMetric(
            name="Unauthorized Access Attempts",
            value=value,
            unit="attempts",
            status=status,
            threshold=100.0,
            timestamp=datetime.utcnow().isoformat(),
        )

    def generate_recommendations(self, metrics: list[SecurityMetric]) -> list[str]:
        """Generate security recommendations based on metrics"""
        recommendations = []

        for metric in metrics:
            if metric.status == "critical":
                if "Failed Login" in metric.name:
                    recommendations.append(
                        "CRITICAL: High rate of failed login attempts detected. "
                        "Consider implementing IP blocking or CAPTCHA."
                    )
                elif "SQL Injection" in metric.name:
                    recommendations.append(
                        "CRITICAL: SQL injection attempts detected. "
                        "Review and strengthen input validation immediately."
                    )
                elif "Threat Score" in metric.name:
                    recommendations.append(
                        "CRITICAL: Threat score is elevated. "
                        "Investigate recent security events and consider enhanced monitoring."
                    )
                elif "Blocked IPs" in metric.name:
                    recommendations.append(
                        "CRITICAL: High number of IP blocks indicates potential attack. "
                        "Review security logs and consider additional protection measures."
                    )
            elif metric.status == "warning":
                if "Rate Limit" in metric.name:
                    recommendations.append(
                        "WARNING: Elevated rate limit violations. "
                        "Monitor for potential abuse or adjust rate limits if legitimate traffic."
                    )
                elif "Request Signing" in metric.name:
                    recommendations.append(
                        "WARNING: Request signature failures detected. "
                        "Check for client configuration issues or potential tampering."
                    )
                elif "Unauthorized Access" in metric.name:
                    recommendations.append(
                        "WARNING: Multiple unauthorized access attempts. "
                        "Review access controls and user permissions."
                    )

        if not recommendations:
            recommendations.append("All security metrics are within normal ranges.")

        return recommendations

    def determine_overall_status(self, metrics: list[SecurityMetric]) -> str:
        """Determine overall security status"""
        statuses = [m.status for m in metrics]

        if "critical" in statuses:
            return "CRITICAL"
        elif "warning" in statuses:
            return "WARNING"
        else:
            return "OK"

    def generate_report(self, duration_minutes: int = 15) -> MetricsReport:
        """Generate comprehensive security metrics report"""
        print("\n" + "=" * 60)
        print("DevSkyy Security Metrics Verification")
        print("=" * 60 + "\n")

        # Check Prometheus health
        print("Checking Prometheus connectivity...")
        if not self.client.check_health():
            print("ERROR: Cannot connect to Prometheus")
            sys.exit(1)
        print("Connected to Prometheus successfully\n")

        # Collect all metrics
        failed_logins = self.get_failed_login_attempts(duration_minutes)
        rate_limits = self.get_rate_limit_violations(duration_minutes)
        signing_failures = self.get_request_signing_failures(duration_minutes)
        threat_score = self.get_threat_score()
        active_sessions = self.get_active_sessions()
        blocked_ips = self.get_blocked_ips(60)  # Last hour
        sql_injection = self.get_sql_injection_attempts(duration_minutes)
        unauthorized = self.get_unauthorized_access(duration_minutes)

        metrics = [
            failed_logins,
            rate_limits,
            signing_failures,
            threat_score,
            active_sessions,
            blocked_ips,
            sql_injection,
            unauthorized,
        ]

        # Generate recommendations
        recommendations = self.generate_recommendations(metrics)

        # Determine overall status
        overall_status = self.determine_overall_status(metrics)

        # Create report
        report = MetricsReport(
            timestamp=datetime.utcnow().isoformat(),
            duration_minutes=duration_minutes,
            failed_login_attempts=failed_logins,
            rate_limit_violations=rate_limits,
            request_signing_failures=signing_failures,
            threat_score=threat_score,
            active_sessions=active_sessions,
            blocked_ips=blocked_ips,
            sql_injection_attempts=sql_injection,
            unauthorized_access=unauthorized,
            overall_status=overall_status,
            recommendations=recommendations,
        )

        return report

    def save_report(self, report: MetricsReport):
        """Save report to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON report
        json_file = os.path.join(self.report_dir, f"security_metrics_report_{timestamp}.json")

        # Convert dataclass to dict
        report_dict = asdict(report)

        with open(json_file, "w") as f:
            json.dump(report_dict, f, indent=2)

        print(f"\nJSON report saved to: {json_file}")

        # Save human-readable report
        text_file = os.path.join(self.report_dir, f"security_metrics_report_{timestamp}.txt")

        with open(text_file, "w") as f:
            self.write_text_report(f, report)

        print(f"Text report saved to: {text_file}")

    def write_text_report(self, file, report: MetricsReport):
        """Write human-readable text report"""
        file.write("=" * 60 + "\n")
        file.write("DevSkyy Security Metrics Report\n")
        file.write("=" * 60 + "\n\n")

        file.write(f"Timestamp: {report.timestamp}\n")
        file.write(f"Analysis Period: {report.duration_minutes} minutes\n")
        file.write(f"Overall Status: {report.overall_status}\n\n")

        file.write("-" * 60 + "\n")
        file.write("Security Metrics\n")
        file.write("-" * 60 + "\n\n")

        metrics = [
            report.failed_login_attempts,
            report.rate_limit_violations,
            report.request_signing_failures,
            report.threat_score,
            report.active_sessions,
            report.blocked_ips,
            report.sql_injection_attempts,
            report.unauthorized_access,
        ]

        for metric in metrics:
            status_symbol = {"ok": "✓", "warning": "⚠", "critical": "✗"}.get(metric.status, "?")

            file.write(f"{status_symbol} {metric.name}\n")
            file.write(f"  Value: {metric.value:.2f} {metric.unit}\n")
            file.write(f"  Status: {metric.status.upper()}\n")
            if metric.threshold:
                file.write(f"  Threshold: {metric.threshold} {metric.unit}\n")
            file.write("\n")

        file.write("-" * 60 + "\n")
        file.write("Recommendations\n")
        file.write("-" * 60 + "\n\n")

        for i, recommendation in enumerate(report.recommendations, 1):
            file.write(f"{i}. {recommendation}\n\n")

        file.write("=" * 60 + "\n")

    def print_summary(self, report: MetricsReport):
        """Print summary to console"""
        print("\n" + "=" * 60)
        print("Security Metrics Summary")
        print("=" * 60 + "\n")

        status_color = {"OK": "\033[0;32m", "WARNING": "\033[1;33m", "CRITICAL": "\033[0;31m"}
        color = status_color.get(report.overall_status, "")
        reset = "\033[0m"

        print(f"Overall Status: {color}{report.overall_status}{reset}\n")

        print("Key Metrics:")
        print(
            f"  Failed Logins: {report.failed_login_attempts.value:.0f} ({report.failed_login_attempts.status})"
        )
        print(
            f"  Rate Limit Violations: {report.rate_limit_violations.value:.0f} ({report.rate_limit_violations.status})"
        )
        print(f"  Threat Score: {report.threat_score.value:.1f} ({report.threat_score.status})")
        print(
            f"  SQL Injection Attempts: {report.sql_injection_attempts.value:.0f} ({report.sql_injection_attempts.status})"
        )

        if report.recommendations:
            print("\nTop Recommendation:")
            print(f"  {report.recommendations[0]}")

        print("\n" + "=" * 60 + "\n")


def main():
    """Main execution function"""
    # Get configuration from environment or use defaults
    prometheus_url = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
    duration = int(os.getenv("METRICS_DURATION_MINUTES", "15"))

    # Create verifier and generate report
    verifier = SecurityMetricsVerifier(prometheus_url)

    try:
        report = verifier.generate_report(duration_minutes=duration)
        verifier.save_report(report)
        verifier.print_summary(report)

        # Exit with appropriate code
        if report.overall_status == "CRITICAL":
            sys.exit(2)
        elif report.overall_status == "WARNING":
            sys.exit(1)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n\nVerification interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
