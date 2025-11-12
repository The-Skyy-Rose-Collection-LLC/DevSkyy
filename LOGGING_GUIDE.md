# DevSkyy Logging Guide

## 📍 Where to Find Error Logs

### Quick Answer

All error logs are located in the **`logs/`** directory at the root of the project:

```bash
cd /path/to/DevSkyy
ls -la logs/
```

### Log File Locations

| Log File | Location | Purpose | Content |
|----------|----------|---------|---------|
| **Application Log** | `logs/devskyy.log` | General application logs | All INFO, WARNING, ERROR, CRITICAL messages |
| **Error Log** | `logs/error.log` | Error-only logs | Only ERROR and CRITICAL messages |
| **Security Log** | `logs/security.log` | Security events | Authentication, authorization, violations |
| **Access Log** | `logs/access.log` | HTTP requests | Gunicorn/Uvicorn access logs (production) |

---

## 🚀 Quick Start - View Logs

### Method 1: Using the Log Viewer Script (Recommended)

```bash
# View all logs interactively
python scripts/view_logs.py

# View specific log file
python scripts/view_logs.py --file error

# Follow logs in real-time
python scripts/view_logs.py --follow

# View last 100 lines
python scripts/view_logs.py --lines 100

# Filter by log level
python scripts/view_logs.py --level ERROR
```

### Method 2: Using Standard Unix Commands

```bash
# View entire error log
cat logs/error.log

# View last 50 lines
tail -n 50 logs/error.log

# Follow logs in real-time
tail -f logs/devskyy.log

# View last 100 lines with live updates
tail -n 100 -f logs/error.log

# Search for specific error
grep "Exception" logs/error.log

# Search with context (3 lines before/after)
grep -C 3 "ValueError" logs/error.log
```

### Method 3: Using Python

```python
# Quick script to read error logs
with open('logs/error.log', 'r') as f:
    print(f.read())

# Read last 50 lines
with open('logs/error.log', 'r') as f:
    lines = f.readlines()
    print(''.join(lines[-50:]))
```

---

## 📊 Log File Details

### Application Log (`logs/devskyy.log`)

**Purpose:** General application activity and all log levels

**Contains:**
- Application startup/shutdown
- API requests and responses
- Agent execution logs
- Database operations
- Cache operations
- Background tasks
- Performance metrics

**Example Entry:**
```
2025-11-12 06:25:40 - devskyy.main - INFO - ✅ Logging configured - Level: INFO, Environment: development
2025-11-12 06:26:15 - devskyy.ecommerce - INFO - Product created: PROD-12345
2025-11-12 06:26:45 - devskyy.pricing - WARNING - Low inventory detected for SKU-789
```

**Format:**
```
TIMESTAMP - LOGGER_NAME - LEVEL - MESSAGE
```

### Error Log (`logs/error.log`)

**Purpose:** Error and critical issues only (ERROR and CRITICAL levels)

**Contains:**
- Application errors and exceptions
- API errors (4xx, 5xx)
- Database errors
- Integration failures
- Stack traces
- Critical system issues

**Example Entry:**
```json
{
  "timestamp": "2025-11-12T06:30:15.123456Z",
  "level": "ERROR",
  "logger": "devskyy.error",
  "message": "API error: POST /api/products - 500",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "error_type": "DatabaseError",
  "endpoint": "/api/products",
  "method": "POST",
  "status_code": 500,
  "exception": "Traceback (most recent call last):\n..."
}
```

**Format:** JSON structured logging (production) or plain text (development)

### Security Log (`logs/security.log`)

**Purpose:** Security-related events for audit and compliance

**Contains:**
- Authentication attempts (success/failure)
- Authorization checks
- API key usage
- Security violations
- Data access events
- Suspicious activity
- Rate limiting events

**Example Entry:**
```json
{
  "timestamp": "2025-11-12T06:35:22.789012Z",
  "event_type": "security",
  "level": "INFO",
  "security_category": "authentication",
  "message": "Authentication login: SUCCESS",
  "user_id": "user-123",
  "client_ip": "192.168.1.100",
  "threat_level": "low"
}
```

### Access Log (`logs/access.log`)

**Purpose:** HTTP access logs (production only)

**Contains:**
- HTTP method and URL
- Status codes
- Response time
- User agent
- IP address

**Example Entry:**
```
192.168.1.100 - - [12/Nov/2025:06:40:30 +0000] "POST /api/products HTTP/1.1" 200 1234 "-" "Mozilla/5.0"
```

---

## 🔍 Common Scenarios

### Scenario 1: Application Won't Start

```bash
# Check for startup errors
tail -n 100 logs/devskyy.log | grep -i error

# Check for import errors
grep "ImportError\|ModuleNotFoundError" logs/devskyy.log

# Check for configuration errors
grep "ValueError\|KeyError" logs/devskyy.log
```

### Scenario 2: API Endpoint Returning 500 Error

```bash
# Find recent API errors
grep "API error" logs/error.log | tail -n 20

# Search by endpoint
grep "/api/products" logs/devskyy.log | grep ERROR

# Get full stack trace
grep -A 20 "status_code.*500" logs/error.log
```

### Scenario 3: Authentication Issues

```bash
# Check security log
tail -n 50 logs/security.log

# Find failed login attempts
grep "FAILED" logs/security.log

# Check JWT/OAuth errors
grep "authentication" logs/error.log
```

### Scenario 4: Database Connection Issues

```bash
# Search for database errors
grep -i "database\|sqlalchemy" logs/error.log

# Check connection pool errors
grep "connection" logs/devskyy.log | grep -i error
```

### Scenario 5: Performance Issues

```bash
# Find slow requests
grep "duration.*[0-9]\{4,\}" logs/devskyy.log

# Check memory warnings
grep -i "memory" logs/devskyy.log

# Find timeout errors
grep -i "timeout" logs/error.log
```

### Scenario 6: Agent Execution Failures

```bash
# Find agent errors
grep "agent" logs/error.log -i

# Check specific agent
grep "EcommerceAgent\|PricingEngine" logs/devskyy.log | grep ERROR

# View agent execution timeline
grep "agent.*execute" logs/devskyy.log
```

---

## 🛠️ Log Management

### Log Rotation

Logs are automatically rotated when they reach **10MB** in size. The system keeps **5 backup files** for each log.

**Files you'll see:**
```
logs/devskyy.log         # Current log
logs/devskyy.log.1       # First rotation (most recent backup)
logs/devskyy.log.2       # Second rotation
logs/devskyy.log.3       # Third rotation
logs/devskyy.log.4       # Fourth rotation
logs/devskyy.log.5       # Fifth rotation (oldest)
```

### Clearing Logs

```bash
# Clear specific log file
> logs/devskyy.log

# Clear all logs
rm -f logs/*.log

# Clear old rotated logs only
rm -f logs/*.log.[1-9]

# Archive logs before clearing
tar -czf logs-archive-$(date +%Y%m%d).tar.gz logs/*.log
rm -f logs/*.log
```

### Log Levels

Control log verbosity with the `LOG_LEVEL` environment variable:

```bash
# Show everything (development)
export LOG_LEVEL=DEBUG

# Standard logging (default)
export LOG_LEVEL=INFO

# Warnings and errors only
export LOG_LEVEL=WARNING

# Errors only
export LOG_LEVEL=ERROR

# Critical issues only
export LOG_LEVEL=CRITICAL
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Set log level
export LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Set log file location (optional)
export LOG_FILE=logs/app.log       # Default: logs/devskyy.log

# Set environment
export ENVIRONMENT=production      # development, staging, production
```

### Structured Logging (JSON)

In production, logs use JSON format for better parsing:

```json
{
  "timestamp": "2025-11-12T06:45:00.000000Z",
  "level": "ERROR",
  "logger": "devskyy.ecommerce",
  "message": "Product creation failed",
  "correlation_id": "req-abc123",
  "service": "devskyy-enterprise",
  "version": "5.1.0",
  "environment": "production",
  "error_type": "ValidationError",
  "exception": "Traceback..."
}
```

### Correlation IDs

Each request gets a unique correlation ID to track it across logs:

```bash
# Find all logs for a specific request
grep "correlation_id.*abc-123-def" logs/devskyy.log
```

---

## 📱 Log Monitoring Tools

### Real-Time Log Monitoring

```bash
# Monitor all logs
tail -f logs/devskyy.log

# Monitor errors only
tail -f logs/error.log

# Monitor multiple logs
tail -f logs/*.log

# Monitor with color highlighting (requires ccze)
tail -f logs/devskyy.log | ccze -A
```

### Log Analysis

```bash
# Count errors by type
grep ERROR logs/devskyy.log | cut -d'-' -f4 | sort | uniq -c | sort -rn

# Find most common errors
grep -o "error_type.*" logs/error.log | sort | uniq -c | sort -rn

# Timeline of errors (hourly)
grep ERROR logs/devskyy.log | cut -d' ' -f1-2 | cut -d':' -f1 | uniq -c

# Count log entries by level
grep -oP '(?<=- )\w+(?= -)' logs/devskyy.log | sort | uniq -c
```

### Log Aggregation (Production)

For production deployments, consider using:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Grafana Loki** (lightweight log aggregation)
- **CloudWatch Logs** (AWS)
- **Google Cloud Logging** (GCP)
- **Azure Monitor** (Azure)

---

## 🚨 Troubleshooting

### "logs directory not found"

**Solution:**
```bash
# Create logs directory manually
mkdir -p logs

# Or run the application once (it will create it)
python main.py
```

### "Permission denied" when accessing logs

**Solution:**
```bash
# Fix permissions
chmod 755 logs
chmod 644 logs/*.log

# Or run with sudo (not recommended)
sudo tail logs/devskyy.log
```

### "Log file is empty"

**Possible causes:**
1. Application hasn't started yet
2. Log level is too high (set to ERROR but only INFO messages)
3. Logging not configured

**Solution:**
```bash
# Check if application is running
ps aux | grep python | grep devskyy

# Lower log level
export LOG_LEVEL=DEBUG

# Check logger configuration
python -c "import logging; print(logging.getLogger().level)"
```

### "Too many log files"

Log rotation is creating too many backups.

**Solution:**
Edit logging configuration in `logging_config.py`:
```python
# Reduce backup count
"maxBytes": 10485760,   # 10MB
"backupCount": 3,       # Keep only 3 backups (was 5)
```

---

## 💡 Best Practices

### Development

- Use `LOG_LEVEL=DEBUG` to see everything
- Monitor logs with `tail -f logs/devskyy.log`
- Keep logs open in a separate terminal
- Use correlation IDs to track requests

### Production

- Use `LOG_LEVEL=INFO` or `WARNING`
- Enable JSON structured logging
- Set up log aggregation (ELK, Loki)
- Configure log rotation (10MB, 5 backups)
- Monitor error rate alerts
- Archive logs regularly

### Security

- Never log sensitive data (passwords, API keys, tokens)
- Review `logs/security.log` regularly
- Set up alerts for failed authentication attempts
- Monitor for suspicious patterns
- Comply with data retention policies (GDPR)

---

## 📚 Additional Resources

### Related Documentation
- [README.md](README.md) - Main documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [DEPLOYMENT_RUNBOOK.md](DEPLOYMENT_RUNBOOK.md) - Production deployment
- [SECURITY.md](SECURITY.md) - Security documentation

### Code References
- `logging_config.py` - Main logging configuration
- `logger_config.py` - Alternative logging setup
- `main.py` - Application entry point with logging setup

### Tools
- `scripts/view_logs.py` - Interactive log viewer
- `scripts/health_check.sh` - System health check including logs

---

## 🆘 Need Help?

### Quick Commands Reference

```bash
# View error logs
tail -n 50 logs/error.log

# Follow logs live
tail -f logs/devskyy.log

# Search for errors
grep ERROR logs/devskyy.log

# View security events
cat logs/security.log

# Check log size
du -h logs/*.log

# Interactive log viewer
python scripts/view_logs.py
```

### Still Having Issues?

1. Check this guide: `LOGGING_GUIDE.md`
2. Run health check: `bash scripts/health_check.sh`
3. Check application status: `ps aux | grep devskyy`
4. View startup logs: `head -n 100 logs/devskyy.log`
5. Check for Python errors: `grep Traceback logs/error.log`

### Contact Support

- GitHub Issues: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues
- Documentation: See [README.md](README.md)

---

**Last Updated:** 2025-11-12  
**Version:** 5.1.0 Enterprise  
**Maintained by:** DevSkyy Team
