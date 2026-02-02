# DevSkyy MCP Monitoring

> Comprehensive observability for all MCP servers, tools, and system health

## 🎯 Overview

The DevSkyy monitoring system provides:

- **Prometheus Metrics** - Request rates, latencies, errors, business metrics
- **Health Checks** - Continuous monitoring with alerting
- **Grafana Dashboards** - Real-time visualization
- **Auto-Remediation** - Automatic recovery from common failures

---

## 🚀 Quick Start

### 1. Install Dependencies

All dependencies are already installed:

```bash
✅ chromadb 1.4.1
✅ sentence-transformers 3.3.1
✅ pypdf 6.6.2
✅ woocommerce 3.0.0
✅ prometheus-client
✅ redis 7.1.0
```

### 2. Start Metrics Server

```bash
# Terminal 1: Start Prometheus metrics server
python monitoring/metrics_server.py

# Server will start on http://localhost:9090
# Metrics available at: http://localhost:9090/metrics
# Health check at: http://localhost:9090/health
# Status page at: http://localhost:9090/
```

### 3. Start Main MCP Server

```bash
# Terminal 2: Start DevSkyy MCP server with monitoring
python devskyy_mcp.py

# Or with environment variables
DEVSKYY_API_URL=http://localhost:8000 \
DEVSKYY_API_KEY=your-key \
python devskyy_mcp.py
```

### 4. Start Health Monitor

```bash
# Terminal 3: Start continuous health monitoring
python scripts/mcp_health_monitor.py --interval 300

# Or run once
python scripts/mcp_health_monitor.py --once

# With Slack alerts
python scripts/mcp_health_monitor.py \
  --interval 300 \
  --slack-webhook https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## 📊 Metrics Collected

### Request Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `mcp_tool_calls_total` | Counter | Total tool calls by name and status |
| `mcp_request_duration_seconds` | Histogram | Request latency distribution |
| `mcp_request_size_bytes` | Summary | Request payload size |
| `mcp_response_size_bytes` | Summary | Response payload size |

### Error Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `mcp_errors_total` | Counter | Errors by type, tool, and reason |
| `mcp_rate_limit_hits_total` | Counter | Rate limit violations |
| `mcp_timeouts_total` | Counter | Request timeouts by tool |

### System Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `mcp_active_connections` | Gauge | Current active connections |
| `mcp_queue_depth` | Gauge | Pending tool executions |
| `mcp_server_uptime_seconds` | Gauge | Server uptime |
| `mcp_tool_availability` | Gauge | Tool availability (1=available) |

### Business Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `mcp_agent_usage_total` | Counter | Agent usage by category |
| `mcp_llm_tokens_total` | Counter | LLM token usage (cost tracking) |
| `mcp_3d_generations_total` | Counter | 3D generation requests |

### Security Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `mcp_auth_failures_total` | Counter | Authentication failures |
| `mcp_validation_failures_total` | Counter | Input validation failures |
| `mcp_security_events_total` | Counter | Security-related events |

---

## 🔧 Integration with MCP Server

### Add Monitoring to Tools

```python
from monitoring.prometheus_metrics import (
    monitored_tool,
    record_tool_call,
    record_error,
    record_llm_tokens,
)

# Automatic monitoring with decorator
@mcp.tool()
@monitored_tool
async def my_tool(param: str) -> str:
    """Your tool implementation."""
    return result

# Manual monitoring with context manager
@mcp.tool()
async def my_tool(param: str) -> str:
    with record_tool_call("my_tool"):
        # Your implementation
        return result

# Record errors
try:
    result = await risky_operation()
except Exception as e:
    record_error("api_error", "my_tool", str(e))
    raise

# Track LLM usage
record_llm_tokens(
    provider="anthropic",
    model="claude-3-7-sonnet",
    input_tokens=1000,
    output_tokens=500,
)
```

### Start Metrics Server in Background

```python
from monitoring.metrics_server import start_metrics_server_background

# In your main MCP server
if __name__ == "__main__":
    # Start metrics server in background
    metrics_thread = start_metrics_server_background(port=9090)

    # Start your MCP server
    mcp.run()
```

---

## 📈 Prometheus Setup

### 1. Install Prometheus

```bash
# macOS
brew install prometheus

# Linux
wget https://github.com/prometheus/prometheus/releases/download/v2.47.0/prometheus-2.47.0.linux-amd64.tar.gz
tar xvfz prometheus-2.47.0.linux-amd64.tar.gz
cd prometheus-2.47.0.linux-amd64
```

### 2. Configure Prometheus

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'devskyy_mcp'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:9090']
        labels:
          service: 'devskyy_mcp'
          environment: 'production'
```

### 3. Start Prometheus

```bash
prometheus --config.file=prometheus.yml
```

Prometheus UI: http://localhost:9090

---

## 📊 Grafana Setup

### 1. Install Grafana

```bash
# macOS
brew install grafana

# Linux
sudo apt-get install -y grafana
```

### 2. Start Grafana

```bash
# macOS
brew services start grafana

# Linux
sudo systemctl start grafana-server
```

Grafana UI: http://localhost:3000 (admin/admin)

### 3. Add Prometheus Data Source

1. Go to **Configuration** → **Data Sources**
2. Click **Add data source**
3. Select **Prometheus**
4. Set URL: `http://localhost:9090`
5. Click **Save & Test**

### 4. Import DevSkyy Dashboard

1. Go to **Dashboards** → **Import**
2. Upload `monitoring/grafana/devskyy_dashboard.json`
3. Select Prometheus data source
4. Click **Import**

Your dashboard is now ready! 🎉

---

## 🔍 Health Monitoring

### Run Health Check Once

```bash
python scripts/mcp_health_monitor.py --once
```

Output:
```
============================================================
MCP HEALTH CHECK RESULTS
============================================================

✅ API
   Status: healthy
   Latency: 45ms

✅ METRICS_SERVER
   Status: healthy
   Latency: 12ms
```

### Continuous Monitoring

```bash
# Check every 5 minutes
python scripts/mcp_health_monitor.py --interval 300
```

### With Slack Alerts

```bash
# Set up Slack incoming webhook first
# https://api.slack.com/messaging/webhooks

python scripts/mcp_health_monitor.py \
  --interval 300 \
  --slack-webhook https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

Alerts are sent after 3 consecutive failures.

### Cron Job Setup

```bash
# Edit crontab
crontab -e

# Add this line (check every 5 minutes)
*/5 * * * * cd /path/to/DevSkyy && python scripts/mcp_health_monitor.py --once >> /var/log/mcp-health.log 2>&1
```

---

## 🚨 Alerting Rules

### Prometheus Alert Rules

Create `alerts.yml`:

```yaml
groups:
  - name: devskyy_mcp
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(mcp_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} (threshold: 0.05)"

      - alert: HighLatency
        expr: histogram_quantile(0.95, sum(rate(mcp_request_duration_seconds_bucket[5m])) by (le)) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "P95 latency is {{ $value }}s (threshold: 5s)"

      - alert: ToolUnavailable
        expr: mcp_tool_availability == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Tool unavailable"
          description: "Tool {{ $labels.tool_name }} is unavailable"

      - alert: ServerDown
        expr: up{job="devskyy_mcp"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "MCP server is down"
          description: "DevSkyy MCP server is not responding"
```

Add to `prometheus.yml`:

```yaml
rule_files:
  - "alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']
```

---

## 🎛️ Monitoring Best Practices

### 1. **Set Appropriate Thresholds**

- **Healthy**: Latency < 1s, Error rate < 1%
- **Degraded**: Latency < 5s, Error rate < 5%
- **Unhealthy**: Latency > 5s, Error rate > 5%

### 2. **Monitor Key Metrics**

- Request rate and throughput
- Latency percentiles (p50, p95, p99)
- Error rate by type and tool
- Tool availability
- LLM token usage (cost tracking)

### 3. **Alert on Trends**

- Rate of change in error rate
- Sustained high latency
- Increasing queue depth
- Repeated authentication failures

### 4. **Regular Health Checks**

- Run health checks every 5 minutes
- Alert after 3 consecutive failures
- Implement automatic remediation when possible

### 5. **Capacity Planning**

- Monitor request rate trends
- Track LLM token usage for cost forecasting
- Watch queue depth for scaling decisions

---

## 🔄 Automatic Remediation

The health monitor can attempt automatic fixes:

```python
# In scripts/mcp_health_monitor.py

async def attempt_remediation(component: str, status: HealthStatus):
    """Attempt to fix common issues automatically."""
    if component == "api" and "connection refused" in status.error:
        # Attempt to restart API server
        subprocess.run(["systemctl", "restart", "devskyy-mcp"])

    elif component == "metrics_server":
        # Restart metrics server
        start_metrics_server_background()
```

---

## 📋 Health Status Criteria

### 🟢 GREEN (Production Ready)

- ✅ All MCP servers running
- ✅ All tools accessible
- ✅ Error rate < 1%
- ✅ Latency p95 < 1s
- ✅ No critical alerts

### 🟡 YELLOW (Degraded - Acceptable)

- ⚠️ 80%+ tools accessible
- ⚠️ Error rate < 5%
- ⚠️ Latency p95 < 5s
- ⚠️ No critical alerts

### 🔴 RED (Critical - Requires Action)

- ❌ < 80% tools accessible
- ❌ Error rate > 5%
- ❌ Latency p95 > 5s
- ❌ Critical alerts active

---

## 🛠️ Troubleshooting

### Metrics Server Won't Start

```bash
# Check if port 9090 is in use
lsof -i :9090

# Kill existing process
kill -9 <PID>

# Or use different port
METRICS_PORT=9091 python monitoring/metrics_server.py
```

### No Metrics Showing Up

```bash
# Check metrics server is running
curl http://localhost:9090/metrics

# Check Prometheus is scraping
curl http://localhost:9090/api/v1/targets

# Check firewall rules
sudo ufw status
```

### Grafana Dashboard Empty

1. Verify Prometheus data source is configured
2. Check query in panel edit mode
3. Adjust time range (top right)
4. Verify metrics are being collected: `curl http://localhost:9090/metrics | grep mcp_`

---

## 📚 Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [DevSkyy MCP Server](../devskyy_mcp.py)

---

## 🎯 Next Steps

1. ✅ **Complete**: Dependencies installed
2. ✅ **Complete**: Monitoring modules created
3. ✅ **Complete**: Health check script ready
4. ✅ **Complete**: Grafana dashboard template
5. ⏭️ **TODO**: Set up Prometheus locally
6. ⏭️ **TODO**: Set up Grafana locally
7. ⏭️ **TODO**: Configure Slack webhook for alerts
8. ⏭️ **TODO**: Set up cron job for health checks

---

**Version:** 1.0.0
**Last Updated:** 2026-02-02
**Maintained By:** DevSkyy Team
