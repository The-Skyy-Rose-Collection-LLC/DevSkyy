# Grafana Security Monitoring Dashboard

Comprehensive security monitoring and alerting for DevSkyy Platform.

## Overview

This directory contains Grafana dashboard configurations and provisioning files for real-time security monitoring, threat detection, and incident response.

## Directory Structure

```
config/grafana/
├── dashboards/
│   └── security-dashboard.json       # Main security dashboard
├── provisioning/
│   ├── dashboards/
│   │   └── dashboard.yml             # Dashboard provisioning config
│   └── datasources/
│       └── prometheus.yml            # Prometheus datasource config
└── README.md                         # This file
```

## Security Dashboard Panels

The `security-dashboard.json` includes the following panels:

### 1. Real-time Security Events (Time Series)

- **Type**: Time series chart
- **Metric**: `rate(security_events_total[5m])`
- **Description**: Live stream of security events by type
- **Refresh**: 5 seconds

### 2. Threat Score (Gauge)

- **Type**: Gauge
- **Metric**: `security_threat_score`
- **Range**: 0-100
- **Thresholds**:
  - Green: 0-49 (Normal)
  - Yellow: 50-69 (Elevated)
  - Orange: 70-84 (High)
  - Red: 85-100 (Critical)

### 3. Alert Status (Stat Panel)

- **Type**: Stat
- **Metric**: `sum(security_alerts_active)`
- **Description**: Count of active, unacknowledged alerts

### 4. Top Blocked IPs (Bar Chart)

- **Type**: Horizontal bar chart
- **Metric**: `topk(10, sum by (ip_address) (increase(security_blocked_ips_total[24h])))`
- **Description**: Top 10 IP addresses blocked in last 24 hours

### 5. Failed Login Attempts by Endpoint (Heatmap)

- **Type**: Heatmap
- **Metric**: `sum by (endpoint) (increase(security_failed_login_attempts[1h]))`
- **Description**: Heat visualization of login failures across endpoints
- **Color Scheme**: Oranges (higher = more failures)

### 6. Security Alerts by Severity (Time Series)

- **Type**: Time series
- **Metric**: `sum by (severity) (security_alerts_total)`
- **Description**: Alert trend breakdown by severity level

### 7. Top Security Event Types (Bar Gauge)

- **Type**: Bar gauge
- **Metric**: `topk(10, sum by (event_type) (increase(security_events_total[1h])))`
- **Description**: Most common security events in the last hour

## Metrics Reference

### Security Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `security_events_total` | Counter | Total security events by type |
| `security_threat_score` | Gauge | Current threat score (0-100) |
| `security_alerts_total` | Counter | Total alerts by severity |
| `security_alerts_active` | Gauge | Currently active alerts |
| `security_blocked_ips_total` | Counter | IPs blocked by security system |
| `security_failed_login_attempts` | Counter | Failed authentication attempts |
| `security_injection_attempts_total` | Counter | SQL/Command injection attempts |
| `security_rate_limit_exceeded_total` | Counter | Rate limit violations |
| `security_suspicious_activity_total` | Counter | Suspicious activity detections |
| `security_access_denied_total` | Counter | Access denied events |
| `security_alerts_unacknowledged` | Gauge | Unacknowledged alerts |

## Setup Instructions

### 1. Start Services

```bash
docker-compose up -d grafana prometheus
```

### 2. Access Grafana

Open browser to: <http://localhost:3000>

**Default Credentials:**

- Username: `admin`
- Password: `admin` (or value from `GRAFANA_PASSWORD` env var)

### 3. Verify Dashboard

1. Navigate to "Dashboards" → "Browse"
2. Look for "DevSkyy Security Dashboard"
3. Dashboard auto-loads from provisioning

### 4. Configure Data Source

Prometheus data source is auto-provisioned at: `http://prometheus:9090`

To verify:

1. Go to Configuration → Data Sources
2. Check "Prometheus" is listed and working
3. Click "Test" to verify connection

## Alert Configuration

Grafana integrates with Prometheus Alertmanager for alerting.

### Alert Rules Location

```
config/prometheus/alerts/security_alerts.yml
```

### Alert Channels

- **Slack**: Critical, High, Medium alerts
- **Email**: High and Critical alerts
- **PagerDuty**: Critical alerts only
- **Webhook**: All alerts to custom endpoint

### Configure Slack Alerts

1. Create Slack incoming webhook
2. Set environment variable:

```bash
export SLACK_WEBHOOK_URL='https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
```

3. Restart Alertmanager:

```bash
docker-compose restart alertmanager
```

## Customization

### Add New Panels

1. Edit dashboard in Grafana UI
2. Export dashboard JSON
3. Replace `dashboards/security-dashboard.json`
4. Restart Grafana:

```bash
docker-compose restart grafana
```

### Modify Refresh Rate

Edit `security-dashboard.json`:

```json
{
  "refresh": "5s",  // Change to "10s", "30s", "1m", etc.
  ...
}
```

### Add Custom Variables

Add to `templating.list` in dashboard JSON:

```json
{
  "templating": {
    "list": [
      {
        "name": "severity",
        "type": "custom",
        "query": "critical,high,medium,low",
        "current": {
          "text": "All",
          "value": "$__all"
        }
      }
    ]
  }
}
```

## Troubleshooting

### Dashboard Not Loading

1. Check Grafana logs:

```bash
docker-compose logs grafana
```

2. Verify provisioning path:

```bash
docker-compose exec grafana ls -la /etc/grafana/dashboards
```

3. Check JSON syntax:

```bash
python3 -m json.tool config/grafana/dashboards/security-dashboard.json
```

### No Data Showing

1. Verify Prometheus connection:
   - Go to Explore → Select Prometheus
   - Run query: `up`
   - Should see services

2. Check metrics are being exported:

```bash
curl http://localhost:8000/metrics | grep security_
```

3. Verify scrape targets:
   - Open <http://localhost:9090/targets>
   - All targets should be "UP"

### Alerts Not Firing

1. Check alert rules:

```bash
docker-compose exec prometheus cat /etc/prometheus/alerts/security_alerts.yml
```

2. Verify Alertmanager:
   - Open <http://localhost:9093>
   - Check alert status

3. Test Slack webhook:

```bash
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test alert from DevSkyy"}'
```

## Performance Tuning

### For High-Traffic Systems

1. Increase scrape interval in `prometheus.yml`:

```yaml
global:
  scrape_interval: 30s  # Default: 15s
```

2. Reduce dashboard refresh rate:

```json
{
  "refresh": "30s"  // Default: "5s"
}
```

3. Limit time range:

```json
{
  "time": {
    "from": "now-1h",  // Default: "now-6h"
    "to": "now"
  }
}
```

## Security Best Practices

1. **Change Default Password**

   ```bash
   export GRAFANA_PASSWORD='strong-secure-password'
   ```

2. **Enable HTTPS**
   - Configure TLS in Grafana settings
   - Use reverse proxy (nginx) with SSL

3. **Restrict Access**
   - Set `GF_USERS_ALLOW_SIGN_UP=false`
   - Configure authentication (LDAP, OAuth)

4. **Regular Updates**

   ```bash
   docker-compose pull grafana
   docker-compose up -d grafana
   ```

## Integration with Security System

The dashboard integrates with:

### Security Monitoring

```python
from security.security_monitoring import security_monitor, SecurityEvent

# Events automatically generate metrics
event = SecurityEvent(...)
security_monitor.log_event(event)
```

### Alerting System

```python
from security.alerting import alerting, SecurityAlert

# Alerts trigger notifications
alert = SecurityAlert(...)
await alerting.send_alert(alert)
```

### Metrics Export

Application exports Prometheus metrics at:

- `/metrics` endpoint
- Port 8000 (default)

## Support

For issues or questions:

1. Check logs: `docker-compose logs grafana prometheus alertmanager`
2. Review Grafana docs: <https://grafana.com/docs/>
3. Review Prometheus docs: <https://prometheus.io/docs/>

## License

Copyright (c) 2025 DevSkyy Platform
