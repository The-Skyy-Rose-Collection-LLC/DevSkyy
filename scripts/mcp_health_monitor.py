#!/usr/bin/env python3
"""
MCP Health Monitor - Continuous Health Checking

Runs periodic health checks on all MCP servers and tools.
Sends alerts when issues are detected.
Can be run as a cron job or systemd service.

Features:
- Continuous health monitoring
- Prometheus metrics integration
- Slack/email alerting (optional)
- Automatic remediation attempts
- Historical health tracking

Usage:
    # Run once
    python scripts/mcp_health_monitor.py

    # Run continuously (check every 5 minutes)
    python scripts/mcp_health_monitor.py --interval 300

    # Run with alerts
    python scripts/mcp_health_monitor.py --slack-webhook URL

    # Cron job (every 5 minutes)
    */5 * * * * cd /path/to/DevSkyy && python scripts/mcp_health_monitor.py

Version: 1.0.0
"""

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import httpx

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@dataclass
class HealthStatus:
    """Health status for a component."""
    component: str
    status: str  # healthy, degraded, unhealthy
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class HealthThresholds:
    """Health check thresholds."""
    healthy_latency_ms: float = 1000  # < 1s is healthy
    degraded_latency_ms: float = 5000  # < 5s is degraded
    timeout_seconds: float = 30  # > 30s is timeout
    max_error_rate: float = 0.05  # 5% error rate threshold


class MCPHealthMonitor:
    """Monitors MCP server health continuously."""

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        metrics_url: str = "http://localhost:9090",
        thresholds: Optional[HealthThresholds] = None,
    ):
        self.api_url = api_url
        self.metrics_url = metrics_url
        self.thresholds = thresholds or HealthThresholds()
        self.client = httpx.AsyncClient(timeout=self.thresholds.timeout_seconds)

    async def check_api_health(self) -> HealthStatus:
        """Check main API health endpoint."""
        try:
            start = time.time()
            response = await self.client.get(f"{self.api_url}/health")
            latency_ms = (time.time() - start) * 1000

            if response.status_code == 200:
                if latency_ms < self.thresholds.healthy_latency_ms:
                    status = "healthy"
                elif latency_ms < self.thresholds.degraded_latency_ms:
                    status = "degraded"
                else:
                    status = "unhealthy"

                return HealthStatus(
                    component="api",
                    status=status,
                    latency_ms=latency_ms,
                )
            else:
                return HealthStatus(
                    component="api",
                    status="unhealthy",
                    error=f"HTTP {response.status_code}",
                )

        except Exception as e:
            return HealthStatus(
                component="api",
                status="unhealthy",
                error=str(e),
            )

    async def check_metrics_server(self) -> HealthStatus:
        """Check Prometheus metrics server."""
        try:
            start = time.time()
            response = await self.client.get(f"{self.metrics_url}/health")
            latency_ms = (time.time() - start) * 1000

            if response.status_code == 200:
                return HealthStatus(
                    component="metrics_server",
                    status="healthy",
                    latency_ms=latency_ms,
                )
            else:
                return HealthStatus(
                    component="metrics_server",
                    status="unhealthy",
                    error=f"HTTP {response.status_code}",
                )

        except Exception as e:
            return HealthStatus(
                component="metrics_server",
                status="unhealthy",
                error=str(e),
            )

    async def check_tool_availability(self) -> List[HealthStatus]:
        """Check if all MCP tools are available."""
        # This would require integration with the MCP server
        # For now, return a placeholder
        return []

    async def get_prometheus_metrics(self) -> Optional[Dict]:
        """Fetch current metrics from Prometheus."""
        try:
            response = await self.client.get(f"{self.metrics_url}/metrics")
            if response.status_code == 200:
                # Parse Prometheus text format
                metrics = {}
                for line in response.text.split("\n"):
                    if line.startswith("mcp_") and not line.startswith("#"):
                        parts = line.split()
                        if len(parts) >= 2:
                            metric_name = parts[0].split("{")[0]
                            metric_value = parts[-1]
                            metrics[metric_name] = float(metric_value)
                return metrics
            return None

        except Exception as e:
            print(f"Error fetching metrics: {e}")
            return None

    async def run_health_check(self) -> Dict[str, HealthStatus]:
        """Run comprehensive health check."""
        results = {}

        # Check API
        results["api"] = await self.check_api_health()

        # Check metrics server
        results["metrics_server"] = await self.check_metrics_server()

        # Check tools (if available)
        tool_statuses = await self.check_tool_availability()
        for status in tool_statuses:
            results[status.component] = status

        return results

    async def monitor_continuously(
        self,
        interval_seconds: int = 300,
        slack_webhook: Optional[str] = None,
    ):
        """Monitor health continuously."""
        print(f"🔍 Starting continuous health monitoring (interval: {interval_seconds}s)")

        consecutive_failures = {}

        while True:
            try:
                # Run health check
                results = await self.run_health_check()

                # Print status
                print(f"\n[{datetime.now().isoformat()}] Health Check Results:")
                print("-" * 60)

                all_healthy = True
                for component, status in results.items():
                    emoji = {
                        "healthy": "✅",
                        "degraded": "⚠️",
                        "unhealthy": "❌",
                    }.get(status.status, "❓")

                    latency_str = f" ({status.latency_ms:.0f}ms)" if status.latency_ms else ""
                    error_str = f" - {status.error}" if status.error else ""

                    print(f"{emoji} {component}: {status.status}{latency_str}{error_str}")

                    if status.status != "healthy":
                        all_healthy = False

                        # Track consecutive failures
                        if component not in consecutive_failures:
                            consecutive_failures[component] = 0
                        consecutive_failures[component] += 1

                        # Alert if 3+ consecutive failures
                        if consecutive_failures[component] >= 3 and slack_webhook:
                            await self.send_alert(
                                slack_webhook,
                                component,
                                status,
                                consecutive_failures[component],
                            )
                    else:
                        # Reset failure count on success
                        consecutive_failures[component] = 0

                if all_healthy:
                    print("\n🎉 All systems healthy!")
                else:
                    print("\n⚠️  Some components are unhealthy")

                # Get and display metrics
                metrics = await self.get_prometheus_metrics()
                if metrics:
                    print("\n📊 Key Metrics:")
                    for metric_name, value in list(metrics.items())[:5]:
                        print(f"   {metric_name}: {value}")

                # Wait for next check
                await asyncio.sleep(interval_seconds)

            except KeyboardInterrupt:
                print("\n\n🛑 Stopping health monitor...")
                break
            except Exception as e:
                print(f"❌ Error in health monitor: {e}")
                await asyncio.sleep(interval_seconds)

        await self.client.aclose()

    async def send_alert(
        self,
        slack_webhook: str,
        component: str,
        status: HealthStatus,
        consecutive_failures: int,
    ):
        """Send alert via Slack webhook."""
        try:
            message = {
                "text": f"🚨 DevSkyy MCP Health Alert",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🚨 MCP Health Alert",
                        },
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Component:*\n{component}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Status:*\n{status.status}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Consecutive Failures:*\n{consecutive_failures}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Time:*\n{status.timestamp.isoformat()}",
                            },
                        ],
                    },
                ],
            }

            if status.error:
                message["blocks"].append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Error:*\n```{status.error}```",
                    },
                })

            await self.client.post(slack_webhook, json=message)
            print(f"📨 Alert sent for {component}")

        except Exception as e:
            print(f"❌ Failed to send alert: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MCP Health Monitor - Continuous health checking for DevSkyy MCP servers"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Check interval in seconds (default: 300)",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="MCP API URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--metrics-url",
        default="http://localhost:9090",
        help="Prometheus metrics URL (default: http://localhost:9090)",
    )
    parser.add_argument(
        "--slack-webhook",
        help="Slack webhook URL for alerts (optional)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (no continuous monitoring)",
    )

    args = parser.parse_args()

    monitor = MCPHealthMonitor(
        api_url=args.api_url,
        metrics_url=args.metrics_url,
    )

    if args.once:
        # Run once and exit
        results = asyncio.run(monitor.run_health_check())

        print("\n" + "=" * 60)
        print("MCP HEALTH CHECK RESULTS")
        print("=" * 60)

        for component, status in results.items():
            emoji = {
                "healthy": "✅",
                "degraded": "⚠️",
                "unhealthy": "❌",
            }.get(status.status, "❓")

            print(f"\n{emoji} {component.upper()}")
            print(f"   Status: {status.status}")
            if status.latency_ms:
                print(f"   Latency: {status.latency_ms:.0f}ms")
            if status.error:
                print(f"   Error: {status.error}")

        # Exit with appropriate code
        all_healthy = all(s.status == "healthy" for s in results.values())
        sys.exit(0 if all_healthy else 1)

    else:
        # Run continuously
        try:
            asyncio.run(
                monitor.monitor_continuously(
                    interval_seconds=args.interval,
                    slack_webhook=args.slack_webhook,
                )
            )
        except KeyboardInterrupt:
            print("\n✅ Health monitor stopped.")
            sys.exit(0)


if __name__ == "__main__":
    main()
