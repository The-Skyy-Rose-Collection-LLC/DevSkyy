# Security Monitoring Quick Start Guide

Get DevSkyy's security monitoring and alerting stack running in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- Ports available: 3000 (Grafana), 9090 (Prometheus), 9093 (AlertManager)
- Optional: Slack webhook URL for alerts

## Quick Start

### 1. Set Environment Variables (Optional)

```bash
# For Slack alerts (recommended)
export SLACK_WEBHOOK_URL='https://hooks.slack.com/services/YOUR/WEBHOOK/URL'

# Grafana admin password (default: admin)
export GRAFANA_PASSWORD='your-secure-password'

# For PagerDuty critical alerts (optional)
export PAGERDUTY_INTEGRATION_KEY='your-key'
```

### 2. Start Monitoring Stack

```bash
# Start all monitoring services
docker-compose up -d prometheus grafana alertmanager postgres-exporter redis-exporter node-exporter

# Verify all services are running
docker-compose ps
```

Expected output:

```
NAME                    STATUS              PORTS
grafana                 Up (healthy)        0.0.0.0:3000->3000/tcp
prometheus              Up (healthy)        0.0.0.0:9090->9090/tcp
alertmanager            Up (healthy)        0.0.0.0:9093->9093/tcp
postgres-exporter       Up                  0.0.0.0:9187->9187/tcp
redis-exporter          Up                  0.0.0.0:9121->9121/tcp
node-exporter           Up                  0.0.0.0:9100->9100/tcp
```

### 3. Access Grafana Dashboard

1. Open browser to: <http://localhost:3000>
2. Login:
   - Username: `admin`
   - Password: `admin` (or your GRAFANA_PASSWORD)
3. Navigate to: Dashboards → Browse → "DevSkyy Security Dashboard"

You should see:

- Real-time security events chart
- Threat score gauge
- Alert status panel
- Top blocked IPs
- Failed login heatmap
- Security alerts by severity
- Top event types

### 4. Verify Prometheus

1. Open: <http://localhost:9090>
2. Go to Status → Targets
3. All targets should be "UP":
   - prometheus
   - devskyy-api
   - postgres-exporter
   - redis-exporter
   - node-exporter

### 5. Test Slack Alerting (If Configured)

```bash
# Run the demo
python examples/security_alerting_demo.py
```

Check your Slack channel for test alerts.

## Dashboard Panels Explained

### Real-time Security Events

Shows live security event stream. Look for spikes in:

- `login_failed` - Potential brute force
- `injection_attempt` - SQL/Command injection
- `rate_limit_exceeded` - API abuse
- `suspicious_activity` - Anomalies

### Threat Score Gauge

Overall security threat level (0-100):

- **0-49 (Green)**: Normal operations
- **50-69 (Yellow)**: Elevated threat level
- **70-84 (Orange)**: High threat - investigate
- **85-100 (Red)**: Critical threat - immediate action

### Alert Status

Number of unacknowledged security alerts. Click to see details.

### Top Blocked IPs

Shows most frequently blocked IP addresses. Review for:

- Persistent attackers
- Distributed attacks
- False positives needing whitelist

### Failed Login Heatmap

Visualizes authentication failures across endpoints:

- Darker orange = more failures
- Helps identify attack patterns
- Shows which endpoints are targeted

## Common Tasks

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f grafana
docker-compose logs -f prometheus
docker-compose logs -f alertmanager
```

### Restart Services

```bash
# Restart all monitoring
docker-compose restart prometheus grafana alertmanager

# Restart specific service
docker-compose restart grafana
```

### Stop Monitoring Stack

```bash
# Stop all monitoring services
docker-compose stop prometheus grafana alertmanager postgres-exporter redis-exporter node-exporter
```

### Update Dashboard

1. Edit dashboard in Grafana UI
2. Click "Save dashboard" → "Save"
3. Export JSON: Click "Share" → "Export" → "Save to file"
4. Replace `config/grafana/dashboards/security-dashboard.json`
5. Restart Grafana: `docker-compose restart grafana`

## Alerting Quick Reference

### Alert Severities

| Severity | Color | Channels | Use Case |
|----------|-------|----------|----------|
| CRITICAL | Red (#FF0000) | Slack, Email, PagerDuty | Immediate threat, active attack |
| HIGH | Orange (#FF6B00) | Slack, Email | Significant risk, needs attention |
| MEDIUM | Gold (#FFD700) | Slack | Worth investigating |
| LOW | Green (#00FF00) | Webhook only | Informational |

### Send Test Alert

```python
import asyncio
from security.alerting import send_slack_alert
from security.security_monitoring import SecurityAlert, AlertSeverity, SecurityEventType

alert = SecurityAlert(
    alert_id="test_001",
    title="Test Alert",
    description="Testing Slack integration",
    severity=AlertSeverity.INFO,
    event_type=SecurityEventType.SYSTEM_ERROR,
    recommended_action="No action needed - this is a test"
)

asyncio.run(send_slack_alert(alert))
```

### View Active Alerts

1. Open AlertManager: <http://localhost:9093>
2. See all firing alerts
3. Silence or acknowledge alerts

## Troubleshooting

### Dashboard Shows "No Data"

1. Check Prometheus connection:

   ```bash
   curl http://localhost:9090/api/v1/query?query=up
   ```

2. Verify metrics are exported:

   ```bash
   curl http://localhost:8000/metrics | grep security_
   ```

3. Check Grafana datasource:
   - Go to Configuration → Data Sources → Prometheus
   - Click "Test" button

### Alerts Not Firing

1. Check Prometheus alert rules:

   ```bash
   docker-compose exec prometheus cat /etc/prometheus/alerts/security_alerts.yml
   ```

2. Verify AlertManager config:

   ```bash
   docker-compose exec alertmanager cat /etc/alertmanager/alertmanager.yml
   ```

3. Test alert manually in Prometheus:
   - Open <http://localhost:9090/alerts>
   - See rule evaluation

### Slack Alerts Not Sending

1. Verify webhook URL is set:

   ```bash
   echo $SLACK_WEBHOOK_URL
   ```

2. Test webhook directly:

   ```bash
   curl -X POST $SLACK_WEBHOOK_URL \
     -H 'Content-Type: application/json' \
     -d '{"text":"Test from DevSkyy"}'
   ```

3. Check AlertManager logs:

   ```bash
   docker-compose logs alertmanager | grep -i slack
   ```

### Grafana Won't Start

1. Check logs:

   ```bash
   docker-compose logs grafana
   ```

2. Verify volume permissions:

   ```bash
   ls -la docker-compose.yml
   ```

3. Remove and recreate:

   ```bash
   docker-compose down -v grafana
   docker-compose up -d grafana
   ```

## Default Metrics

The system automatically tracks:

- **Security Events**: All authentication, authorization, and threat events
- **System Health**: CPU, memory, disk usage
- **Database**: PostgreSQL connections, queries, performance
- **Cache**: Redis hit rate, memory usage
- **API**: Response times, error rates

No additional configuration needed.

## Advanced Configuration

### Customize Alert Thresholds

Edit `config/prometheus/alerts/security_alerts.yml`:

```yaml
- alert: BruteForceAttackDetected
  expr: rate(security_failed_login_attempts[5m]) > 10  # Change threshold
  for: 2m  # Change duration
```

### Add Custom Panel

1. Open Grafana
2. Edit "DevSkyy Security Dashboard"
3. Click "Add" → "Visualization"
4. Select Prometheus datasource
5. Enter metric query
6. Configure panel settings
7. Save dashboard

### Configure Email Alerts

Update AlertManager config with SMTP settings:

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@devskyy.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'

receivers:
  - name: 'email-alerts'
    email_configs:
      - to: 'security@devskyy.com'
```

## Resources

- **Full Documentation**: `config/grafana/README.md`
- **Alert Rules**: `config/prometheus/alerts/security_alerts.yml`
- **Test Suite**: `tests/test_alerting_integration.py`
- **Demo Script**: `examples/security_alerting_demo.py`
- **Implementation Details**: `GRAFANA_ALERTING_IMPLEMENTATION.md`

## Production Checklist

Before deploying to production:

- [ ] Set strong GRAFANA_PASSWORD
- [ ] Configure Slack webhook URL
- [ ] Set up PagerDuty integration
- [ ] Configure email SMTP
- [ ] Enable HTTPS/TLS
- [ ] Review alert thresholds
- [ ] Set up alert acknowledgment workflow
- [ ] Configure data retention
- [ ] Set up backup for Grafana dashboards
- [ ] Document alert response procedures

## Support

For issues:

1. Check logs: `docker-compose logs [service]`
2. Review documentation: `config/grafana/README.md`
3. Run tests: `pytest tests/test_alerting_integration.py -v`
4. Check service health: `docker-compose ps`

---

**You're ready!** The security monitoring stack is now running and protecting your application.
