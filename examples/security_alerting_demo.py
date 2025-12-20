#!/usr/bin/env python3
"""
Security Alerting System Demo
==============================

Demonstrates the comprehensive security alerting system with:
- Slack notifications
- Multi-channel alerting
- Alert deduplication
- Severity-based routing
"""

import asyncio
import os

from security.alerting import AlertChannel, AlertingConfig, AlertingIntegration, send_slack_alert
from security.security_monitoring import AlertSeverity, SecurityAlert, SecurityEventType


async def demo_basic_slack_alert():
    """Demo 1: Basic Slack alert"""
    print("\n" + "=" * 60)
    print("Demo 1: Basic Slack Alert")
    print("=" * 60)

    alert = SecurityAlert(
        alert_id="demo_001",
        title="Brute Force Attack Detected",
        description="Multiple failed login attempts detected from IP 192.168.1.100",
        severity=AlertSeverity.CRITICAL,
        event_type=SecurityEventType.BRUTE_FORCE_DETECTED,
        source_events=["evt_001", "evt_002", "evt_003"],
        recommended_action="Block IP address 192.168.1.100 immediately",
    )

    # Note: Set SLACK_WEBHOOK_URL in environment to actually send
    if os.getenv("SLACK_WEBHOOK_URL"):
        result = await send_slack_alert(alert)
        print(f"Slack alert sent: {result}")
    else:
        print("Slack webhook not configured (set SLACK_WEBHOOK_URL)")
        print(f"Would send alert: {alert.title}")
        print(f"Severity: {alert.severity.value}")
        print("Color: #FF0000 (CRITICAL)")


async def demo_multi_channel_alerting():
    """Demo 2: Multi-channel alerting with auto-routing"""
    print("\n" + "=" * 60)
    print("Demo 2: Multi-Channel Alerting")
    print("=" * 60)

    # Configure alerting system
    config = AlertingConfig(
        slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL"),
        email_enabled=True,
        email_to=["security@devskyy.com", "ops@devskyy.com"],
        pagerduty_key=os.getenv("PAGERDUTY_INTEGRATION_KEY"),
    )

    alerting = AlertingIntegration(config)

    # Create different severity alerts
    alerts = [
        SecurityAlert(
            alert_id="demo_critical",
            title="SQL Injection Attack",
            description="Critical SQL injection attempt detected",
            severity=AlertSeverity.CRITICAL,
            event_type=SecurityEventType.INJECTION_ATTEMPT,
            recommended_action="Block IP and investigate database logs",
        ),
        SecurityAlert(
            alert_id="demo_high",
            title="Unusual API Access Pattern",
            description="Suspicious API access from new location",
            severity=AlertSeverity.HIGH,
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            recommended_action="Review access logs and verify user identity",
        ),
        SecurityAlert(
            alert_id="demo_medium",
            title="Rate Limit Exceeded",
            description="User exceeded API rate limit",
            severity=AlertSeverity.MEDIUM,
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            recommended_action="Monitor for continued abuse",
        ),
    ]

    for alert in alerts:
        print(f"\nSending {alert.severity.value} alert: {alert.title}")
        results = await alerting.send_alert(alert)
        print(f"Delivery results: {results}")

    # Show statistics
    print("\nAlerting Statistics:")
    stats = alerting.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


async def demo_manual_channel_selection():
    """Demo 3: Manual channel selection"""
    print("\n" + "=" * 60)
    print("Demo 3: Manual Channel Selection")
    print("=" * 60)

    alerting = AlertingIntegration()

    alert = SecurityAlert(
        alert_id="demo_manual",
        title="Security Audit Required",
        description="Quarterly security audit due in 7 days",
        severity=AlertSeverity.LOW,
        event_type=SecurityEventType.SYSTEM_ERROR,
        recommended_action="Schedule security audit meeting",
    )

    # Send only to Slack and Email
    channels = [AlertChannel.SLACK, AlertChannel.EMAIL]
    print(f"Sending alert to specific channels: {[c.value for c in channels]}")

    results = await alerting.send_alert(alert, channels=channels)
    print(f"Delivery results: {results}")


async def demo_alert_deduplication():
    """Demo 4: Alert deduplication"""
    print("\n" + "=" * 60)
    print("Demo 4: Alert Deduplication")
    print("=" * 60)

    alerting = AlertingIntegration()

    # Same alert sent multiple times
    alert = SecurityAlert(
        alert_id="demo_dedup_1",
        title="Failed Login Attempt",
        description="Failed login from user john@example.com",
        severity=AlertSeverity.MEDIUM,
        event_type=SecurityEventType.LOGIN_FAILED,
        recommended_action="Monitor user account",
    )

    print("Sending same alert 3 times (should deduplicate):")
    for i in range(3):
        results = await alerting.send_alert(alert)
        print(f"  Attempt {i+1}: {results}")
        await asyncio.sleep(1)

    stats = alerting.get_stats()
    print(f"\nDeduplicated alerts: {stats['deduplicated']}")


async def demo_severity_based_routing():
    """Demo 5: Severity-based routing"""
    print("\n" + "=" * 60)
    print("Demo 5: Severity-Based Routing")
    print("=" * 60)

    config = AlertingConfig(
        slack_webhook_url="https://hooks.slack.com/...",
        email_enabled=True,
        pagerduty_key="pd_key_123",
        min_severity_slack=AlertSeverity.MEDIUM,
        min_severity_email=AlertSeverity.HIGH,
        min_severity_pagerduty=AlertSeverity.CRITICAL,
    )

    alerting = AlertingIntegration(config)

    severities = [
        AlertSeverity.INFO,
        AlertSeverity.LOW,
        AlertSeverity.MEDIUM,
        AlertSeverity.HIGH,
        AlertSeverity.CRITICAL,
    ]

    for severity in severities:
        SecurityAlert(
            alert_id=f"demo_severity_{severity.value}",
            title=f"{severity.value.upper()} Security Event",
            description=f"This is a {severity.value} severity alert",
            severity=severity,
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            recommended_action="Review and take appropriate action",
        )

        channels = alerting._select_channels_by_severity(severity)
        print(f"\n{severity.value.upper()} → Channels: {[c.value for c in channels]}")


async def demo_slack_color_coding():
    """Demo 6: Slack color coding"""
    print("\n" + "=" * 60)
    print("Demo 6: Slack Color Coding")
    print("=" * 60)

    from security.alerting import get_severity_color, get_severity_emoji

    print("\nSeverity Color Mapping:")
    for severity in AlertSeverity:
        color = get_severity_color(severity)
        emoji = get_severity_emoji(severity)
        print(f"  {severity.value.upper()}: {emoji} → {color}")


async def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("DevSkyy Security Alerting System - Comprehensive Demo")
    print("=" * 70)

    demos = [
        demo_basic_slack_alert,
        demo_multi_channel_alerting,
        demo_manual_channel_selection,
        demo_alert_deduplication,
        demo_severity_based_routing,
        demo_slack_color_coding,
    ]

    for demo in demos:
        try:
            await demo()
        except Exception as e:
            print(f"Error in demo: {e}")

    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print("\nConfiguration Instructions:")
    print("1. Set SLACK_WEBHOOK_URL environment variable")
    print("2. Set PAGERDUTY_INTEGRATION_KEY for critical alerts")
    print("3. Configure email settings for notifications")
    print("4. Set CUSTOM_WEBHOOK_URL for custom integrations")
    print("\nExample:")
    print("  export SLACK_WEBHOOK_URL='https://hooks.slack.com/services/YOUR/WEBHOOK/URL'")
    print("  python examples/security_alerting_demo.py")


if __name__ == "__main__":
    asyncio.run(main())
