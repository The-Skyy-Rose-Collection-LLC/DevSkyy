# DDoS Attack Response

**Severity Level**: HIGH
**Last Updated**: 2025-12-19
**Owner**: DevOps Team, Network Operations
**Related**: [Security Incident Response Master Procedure](/Users/coreyfoster/DevSkyy/docs/runbooks/security-incident-response.md)

## Overview

Distributed Denial of Service (DDoS) attacks overwhelm systems with traffic to make services unavailable. This runbook covers detection, traffic analysis, mitigation through rate limiting and CDN protection, and service restoration.

## Detection

### Alert Triggers

**Automated Alerts:**

- Traffic spike > 10x normal baseline
- HTTP 5xx error rate > 20%
- Response time > 5000ms (p95)
- Connection pool exhaustion
- CPU/Memory usage > 90%
- Cloudflare DDoS alerts
- AWS Shield notifications
- Nginx/Load balancer connection limits reached

**Monitoring Thresholds:**

```yaml
ddos_detection:
  traffic_spike:
    threshold: 1000%  # 10x normal traffic
    window: 5m
  error_rate:
    threshold: 20%
    window: 5m
  response_time:
    threshold: 5000ms
    percentile: p95
    window: 5m
  connections:
    threshold: 10000
    window: 1m
```

### How to Identify

1. **Traffic Analysis**

   ```bash
   # Check current request rate
   tail -10000 /var/log/nginx/access.log | \
   awk '{print $4}' | cut -d: -f1-2 | sort | uniq -c | sort -rn

   # Analyze requests per IP
   awk '{print $1}' /var/log/nginx/access.log | \
   sort | uniq -c | sort -rn | head -20

   # Check for specific attack patterns
   grep -E "(POST|GET)" /var/log/nginx/access.log | \
   awk '{print $1, $7}' | sort | uniq -c | sort -rn | head -20
   ```

2. **System Resource Monitoring**

   ```bash
   # CPU and memory usage
   top -bn1 | head -20

   # Network connections
   netstat -an | grep ESTABLISHED | wc -l

   # Connection states
   netstat -tan | awk '{print $6}' | sort | uniq -c

   # Check for SYN flood
   netstat -an | grep SYN_RECV | wc -l
   ```

3. **Application Metrics**

   ```bash
   # Check API response times
   curl -w "@curl-format.txt" -o /dev/null -s https://api.skyyrose.com/health

   # Database connection pool
   psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

   # Redis memory usage
   redis-cli INFO memory | grep used_memory_human
   ```

4. **Geographic Analysis**

   ```bash
   # Identify attacking countries
   awk '{print $1}' /var/log/nginx/access.log | \
   while read ip; do geoiplookup $ip; done | \
   cut -d: -f2 | sort | uniq -c | sort -rn | head -10
   ```

5. **Attack Pattern Recognition**

   **Common DDoS Attack Types:**
   - **HTTP Flood**: High volume of legitimate-looking HTTP requests
   - **SYN Flood**: Exploits TCP handshake, exhausts connection table
   - **UDP Flood**: High volume of UDP packets
   - **Slowloris**: Holds connections open with slow requests
   - **DNS Amplification**: Exploits DNS servers to amplify traffic
   - **NTP Amplification**: Exploits NTP servers
   - **Application Layer**: Targets specific endpoints (e.g., search, login)

   ```bash
   # Detect HTTP flood
   awk '{print $7}' /var/log/nginx/access.log | sort | uniq -c | sort -rn

   # Detect slow requests (Slowloris)
   awk '{print $NF}' /var/log/nginx/access.log | awk '{sum+=$1; count++} END {print sum/count}'

   # Check request methods
   awk '{print $6}' /var/log/nginx/access.log | sort | uniq -c
   ```

## Triage

### Severity Assessment

**CRITICAL - Immediate Response:**

- Complete service outage (0% availability)
- Traffic > 100x normal baseline
- All servers unreachable
- Database connections exhausted
- CDN/DDoS protection overwhelmed

**HIGH - Urgent Response (< 15 min):**

- Partial service degradation (< 50% availability)
- Traffic 10-100x normal baseline
- Error rate > 50%
- Response times > 10s
- Specific endpoints down

**MEDIUM - Response within 1 hour:**

- Service slowdown but functional
- Traffic 5-10x normal baseline
- Error rate 20-50%
- Response times 5-10s
- Auto-scaling keeping up

### Initial Containment Steps

**IMMEDIATE ACTIONS (0-5 minutes):**

1. **Enable DDoS Protection**

   ```bash
   # Enable Cloudflare Under Attack Mode
   curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/security_level" \
     -H "X-Auth-Email: $CF_EMAIL" \
     -H "X-Auth-Key: $CF_API_KEY" \
     -H "Content-Type: application/json" \
     --data '{"value":"under_attack"}'

   # Enable AWS Shield Advanced (if configured)
   aws shield create-protection \
     --name skyyrose-api-ddos-protection \
     --resource-arn arn:aws:elasticloadbalancing:us-east-1:ACCOUNT:loadbalancer/app/skyyrose-api
   ```

2. **Activate Rate Limiting**

   ```bash
   # Enable aggressive rate limiting in nginx
   cat > /etc/nginx/conf.d/ddos-rate-limit.conf << 'EOF'
   limit_req_zone $binary_remote_addr zone=ddos_limit:50m rate=10r/s;
   limit_conn_zone $binary_remote_addr zone=ddos_conn:50m;

   limit_req zone=ddos_limit burst=20 nodelay;
   limit_conn ddos_conn 10;
   limit_req_status 429;
   limit_conn_status 429;
   EOF

   nginx -t && nginx -s reload
   ```

3. **Block Attacking IPs**

   ```bash
   # Get top attacking IPs
   awk '{print $1}' /var/log/nginx/access.log | \
   sort | uniq -c | sort -rn | head -100 | \
   awk '$1 > 1000 {print $2}' > /tmp/attacking_ips.txt

   # Block in firewall
   while read ip; do
     ufw deny from $ip
   done < /tmp/attacking_ips.txt

   # Block in nginx
   while read ip; do
     echo "deny $ip;" >> /etc/nginx/conf.d/blocked-ips.conf
   done < /tmp/attacking_ips.txt
   nginx -s reload
   ```

4. **Scale Infrastructure**

   ```bash
   # Auto-scale application servers (AWS)
   aws autoscaling set-desired-capacity \
     --auto-scaling-group-name skyyrose-api-asg \
     --desired-capacity 20

   # Scale database read replicas
   aws rds create-db-instance-read-replica \
     --db-instance-identifier skyyrose-db-replica-emergency

   # Scale Redis cluster
   aws elasticache modify-replication-group \
     --replication-group-id skyyrose-cache \
     --apply-immediately \
     --num-cache-clusters 5
   ```

### Escalation Procedures

**CRITICAL DDoS:**

1. Alert DevOps Lead immediately: [PHONE]
2. Alert CTO: [PHONE]
3. Contact Cloudflare Enterprise Support: 1-888-99-FLARE
4. Contact AWS Support (Enterprise): Create P1 ticket
5. Create war room: `#incident-ddos-YYYYMMDD`
6. Notify customer support team (prepare status updates)

**HIGH Severity:**

1. Post in `#devops-alerts` channel
2. Alert DevOps Lead via Slack
3. Create incident ticket
4. Monitor and prepare escalation

## Investigation

### Traffic Analysis

1. **Analyze Attack Vectors**

   ```bash
   # Request distribution by endpoint
   awk '{print $7}' /var/log/nginx/access.log | \
   cut -d? -f1 | sort | uniq -c | sort -rn | head -20

   # Request methods
   awk '{print $6}' /var/log/nginx/access.log | \
   tr -d '"' | sort | uniq -c | sort -rn

   # User agents (identify bots)
   awk -F'"' '{print $6}' /var/log/nginx/access.log | \
   sort | uniq -c | sort -rn | head -20

   # HTTP status codes
   awk '{print $9}' /var/log/nginx/access.log | \
   sort | uniq -c | sort -rn
   ```

2. **Network Layer Analysis**

   ```bash
   # Capture network traffic for analysis
   tcpdump -i any -s 65535 -w /tmp/ddos-capture.pcap port 80 or port 443

   # Analyze with tshark
   tshark -r /tmp/ddos-capture.pcap -q -z conv,ip

   # Check for SYN flood
   tcpdump -r /tmp/ddos-capture.pcap 'tcp[tcpflags] & (tcp-syn) != 0' | wc -l
   ```

3. **CDN Analytics**

   ```bash
   # Get Cloudflare analytics
   curl "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/analytics/dashboard?since=-30" \
     -H "X-Auth-Email: $CF_EMAIL" \
     -H "X-Auth-Key: $CF_API_KEY" | jq .

   # Get top attacking countries
   curl "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/analytics/colos" \
     -H "X-Auth-Email: $CF_EMAIL" \
     -H "X-Auth-Key: $CF_API_KEY"
   ```

### Data Collection Checklist

- [ ] Peak traffic volume (requests/second)
- [ ] Attack duration (start and end times)
- [ ] Attack vectors (HTTP flood, SYN flood, etc.)
- [ ] Targeted endpoints/services
- [ ] Source IP addresses (top 100)
- [ ] Geographic distribution of attack traffic
- [ ] User agent patterns
- [ ] Request patterns (size, frequency, headers)
- [ ] Network packet captures
- [ ] CDN analytics and logs
- [ ] Impact metrics (downtime, error rate, response time)
- [ ] Business impact (orders lost, revenue impact)

### Root Cause Analysis

**Why was the system vulnerable?**

1. **Insufficient DDoS Protection**
   - No CDN or CDN misconfigured
   - No rate limiting enabled
   - No connection limits
   - No request size limits

2. **Infrastructure Scaling Issues**
   - Fixed capacity, no auto-scaling
   - Single point of failure
   - Inadequate bandwidth provisioning

3. **Application Vulnerabilities**
   - Expensive endpoints without caching
   - No request validation
   - Database queries not optimized
   - No circuit breakers

```bash
# Check current protections
nginx -T | grep -E "(limit_req|limit_conn)"

# Check auto-scaling configuration
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names skyyrose-api-asg

# Check Cloudflare settings
curl "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings" \
  -H "X-Auth-Email: $CF_EMAIL" \
  -H "X-Auth-Key: $CF_API_KEY" | jq .
```

## Remediation

### Step-by-Step Fix Procedures

**1. Implement CDN and DDoS Protection**

```bash
# Configure Cloudflare (if not already)
# DNS changes to route traffic through Cloudflare

# Enable Cloudflare features
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/security_level" \
  -H "X-Auth-Email: $CF_EMAIL" \
  -H "X-Auth-Key: $CF_API_KEY" \
  --data '{"value":"high"}'

# Enable Browser Integrity Check
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/browser_check" \
  -H "X-Auth-Email: $CF_EMAIL" \
  -H "X-Auth-Key: $CF_API_KEY" \
  --data '{"value":"on"}'

# Enable Challenge Passage
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/challenge_ttl" \
  -H "X-Auth-Email: $CF_EMAIL" \
  -H "X-Auth-Key: $CF_API_KEY" \
  --data '{"value":1800}'
```

**2. Deploy Multi-Layer Rate Limiting**

```nginx
# /etc/nginx/conf.d/rate-limiting.conf
# Connection limiting
limit_conn_zone $binary_remote_addr zone=conn_limit_per_ip:10m;
limit_conn_zone $server_name zone=conn_limit_per_server:10m;

# Request rate limiting
limit_req_zone $binary_remote_addr zone=req_limit_per_ip:10m rate=100r/s;
limit_req_zone $request_uri zone=req_limit_per_uri:10m rate=50r/s;

# Slow attack prevention
client_body_timeout 10s;
client_header_timeout 10s;
keepalive_timeout 30s;

server {
    # Apply limits
    limit_conn conn_limit_per_ip 10;
    limit_conn conn_limit_per_server 1000;
    limit_req zone=req_limit_per_ip burst=50 nodelay;

    # Request size limits
    client_max_body_size 10m;
    client_body_buffer_size 128k;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 16k;
}
```

**3. Implement Application-Level Protection**

```python
# security/ddos_protection.py
from fastapi import Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.middleware("http")
async def ddos_protection_middleware(request: Request, call_next):
    # Request size validation
    if request.headers.get("content-length"):
        if int(request.headers["content-length"]) > 10_000_000:  # 10MB
            raise HTTPException(413, "Request too large")

    # User agent validation
    user_agent = request.headers.get("user-agent", "")
    if not user_agent or user_agent in BLOCKED_USER_AGENTS:
        raise HTTPException(403, "Forbidden")

    # Geographic blocking (if needed)
    country = request.headers.get("cf-ipcountry")
    if country in BLOCKED_COUNTRIES:
        raise HTTPException(403, "Geographic restriction")

    response = await call_next(request)
    return response

@app.get("/api/expensive-endpoint")
@limiter.limit("10/minute")
async def expensive_operation(request: Request):
    # Cached response
    cache_key = f"expensive:{request.query_params}"
    if cached := await redis.get(cache_key):
        return cached

    result = await perform_expensive_operation()
    await redis.setex(cache_key, 300, result)
    return result
```

**4. Configure Auto-Scaling**

```yaml
# aws/autoscaling-policy.yml
AutoScalingGroup:
  MinSize: 3
  MaxSize: 50
  DesiredCapacity: 5

  TargetTrackingScaling:
    - MetricType: ASGAverageCPUUtilization
      TargetValue: 70
    - MetricType: ALBRequestCountPerTarget
      TargetValue: 1000

  StepScaling:
    - MetricName: RequestCount
      Threshold: 10000
      ScalingAdjustment: +10
    - MetricName: RequestCount
      Threshold: 50000
      ScalingAdjustment: +20
```

**5. Implement Circuit Breakers**

```python
# Add circuit breakers for external dependencies
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_external_api():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://external-api.com/data")
        return response.json()
```

**6. Database Protection**

```python
# Implement connection pooling limits
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 40,
    "pool_timeout": 30,
    "pool_recycle": 3600,
}

# Add query timeouts
@app.middleware("http")
async def query_timeout_middleware(request: Request, call_next):
    # Set statement timeout for this request
    async with db.session() as session:
        await session.execute("SET LOCAL statement_timeout = '5s'")
    return await call_next(request)
```

### Verification Steps

```bash
# 1. Test rate limiting
ab -n 1000 -c 100 https://api.skyyrose.com/health
# Should see 429 responses

# 2. Verify auto-scaling configuration
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names skyyrose-api-asg | \
  jq '.AutoScalingGroups[0].DesiredCapacity'

# 3. Test Cloudflare protection
curl -I https://api.skyyrose.com/
# Should see: cf-ray, cf-cache-status headers

# 4. Verify connection limits
for i in {1..100}; do
  curl https://api.skyyrose.com/ &
done
# Should see some connection refused

# 5. Load test to verify resilience
k6 run load-tests/ddos-simulation.js
```

## Recovery

### Service Restoration Process

**Phase 1: Stabilization (0-1 hour)**

1. Verify attack traffic has subsided
2. Monitor error rates and response times
3. Gradually relax rate limits if too restrictive
4. Check for any data corruption or loss
5. Verify all services are healthy

```bash
# Check traffic levels
tail -1000 /var/log/nginx/access.log | \
awk '{print $4}' | cut -d: -f1-2 | sort | uniq -c

# Monitor error rate
watch -n 10 'tail -100 /var/log/nginx/access.log | awk "{print \$9}" | grep -c "^5"'
```

**Phase 2: Optimization (1-6 hours)**

1. Analyze attack patterns
2. Update WAF rules based on patterns
3. Fine-tune rate limiting thresholds
4. Scale down infrastructure if over-provisioned
5. Clear blocked IPs if legitimate traffic affected

```bash
# Gradually remove IP blocks (review first)
tail -100 /etc/nginx/conf.d/blocked-ips.conf

# Adjust rate limits to normal levels
vim /etc/nginx/conf.d/rate-limiting.conf
nginx -s reload
```

**Phase 3: Return to Normal (6-24 hours)**

1. Disable "Under Attack" mode (if enabled)
2. Scale infrastructure to normal levels
3. Resume normal monitoring
4. Complete post-incident analysis

```bash
# Disable Cloudflare Under Attack Mode
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/security_level" \
  -H "X-Auth-Email: $CF_EMAIL" \
  -H "X-Auth-Key: $CF_API_KEY" \
  --data '{"value":"medium"}'

# Scale down to normal capacity
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name skyyrose-api-asg \
  --desired-capacity 5
```

### Monitoring During Recovery

```bash
# Real-time traffic monitoring
watch -n 5 'tail -100 /var/log/nginx/access.log | wc -l'

# Response time monitoring
while true; do
  curl -w "%{time_total}\n" -o /dev/null -s https://api.skyyrose.com/health
  sleep 5
done

# Database performance
watch -n 10 "psql $DATABASE_URL -c 'SELECT count(*), state FROM pg_stat_activity GROUP BY state;'"

# Application health
watch -n 30 'curl -s https://api.skyyrose.com/health | jq .'
```

### Communication Plan

**Customer Communication (Status Page):**

```
INVESTIGATING: We are currently experiencing higher than normal traffic levels that may impact performance.
Update at [TIME]: We have implemented additional protections and are monitoring the situation.
Update at [TIME]: Service performance is returning to normal. We continue to monitor.
RESOLVED: All services are operating normally. We apologize for any inconvenience.
```

**Internal Communication:**

```
#devops-alerts

:chart_with_upwards_trend: DDoS Attack Update - [TIME]

**Status**: MITIGATED / RECOVERING / RESOLVED

**Current Metrics**:
- Traffic: [X] req/s (normal: [Y] req/s)
- Error Rate: [X]%
- Response Time: [X]ms (p95)
- Active Servers: [X]

**Actions Taken**:
- Enabled Cloudflare DDoS protection
- Implemented rate limiting
- Scaled to [X] servers
- Blocked [X] attacking IPs

**Next Steps**:
- Continue monitoring for [X] hours
- Review attack patterns
- Schedule post-mortem for [DATE/TIME]
```

## Post-Mortem

### Key Metrics

- Peak attack traffic: [X] requests/second
- Attack duration: [X] hours
- Service downtime: [X] minutes
- Error rate during attack: [X]%
- Response time during attack: [X]ms
- Number of attacking IPs: [X]
- Attack vectors identified: [LIST]
- Financial impact: $[X] (lost revenue, mitigation costs)

### Preventive Measures

**Infrastructure:**

- [ ] Enable AWS Shield Standard/Advanced
- [ ] Configure Cloudflare DDoS protection
- [ ] Implement multi-region failover
- [ ] Deploy anycast network
- [ ] Increase bandwidth capacity
- [ ] Implement auto-scaling policies

**Application:**

- [ ] Add comprehensive rate limiting
- [ ] Implement request validation
- [ ] Deploy caching layers (CDN, Redis)
- [ ] Optimize expensive endpoints
- [ ] Add circuit breakers
- [ ] Implement graceful degradation

**Monitoring:**

- [ ] Set up traffic anomaly detection
- [ ] Configure DDoS alerting
- [ ] Deploy real-time dashboards
- [ ] Implement automated response playbooks
- [ ] Create runbooks for common attack types

**Process:**

- [ ] Establish DDoS response team
- [ ] Conduct quarterly DDoS drills
- [ ] Maintain relationships with ISP/CDN
- [ ] Document attack patterns
- [ ] Update incident response plan

## Contact Information

### Incident Response Team

| Role | Contact | Phone | Email |
|------|---------|-------|-------|
| DevOps Lead | @devops-lead | [PHONE] | <devops@skyyrose.com> |
| Network Engineer | @network-eng | [PHONE] | <network@skyyrose.com> |
| CTO | @cto | [PHONE] | <cto@skyyrose.com> |

### External Support

| Provider | Purpose | Contact |
|----------|---------|---------|
| Cloudflare | Enterprise DDoS protection | 1-888-99-FLARE |
| AWS Support | Shield Advanced, infrastructure | AWS Console Support (P1) |
| ISP Support | Network-level mitigation | [ISP CONTACT] |

## Slack Notification Template

```
:warning: **DDoS ATTACK DETECTED** :warning:

**Incident ID**: INC-DDOS-YYYYMMDD-HHmm
**Severity**: HIGH
**Status**: MITIGATING

**Attack Metrics**:
- Traffic Volume: [X] req/s (baseline: [Y] req/s)
- Attack Type: [HTTP Flood / SYN Flood / etc.]
- Source: [X] unique IPs from [COUNTRIES]
- Targeted Service: [API / Website / etc.]

**Impact**:
- Current Error Rate: [X]%
- Response Time: [X]ms (normal: [Y]ms)
- Service Status: DEGRADED / PARTIAL OUTAGE

**Actions Taken**:
- Enabled Cloudflare Under Attack Mode
- Implemented aggressive rate limiting
- Blocked [X] attacking IPs
- Scaled to [X] servers

**Incident Commander**: @devops-lead
**War Room**: #incident-ddos-YYYYMMDD

**Status Page**: https://status.skyyrose.com
**Next Update**: [TIME]
```

## Related Runbooks

- [Security Incident Response Master Procedure](/Users/coreyfoster/DevSkyy/docs/runbooks/security-incident-response.md)
- [Brute Force Attack](/Users/coreyfoster/DevSkyy/docs/runbooks/brute-force-attack.md)
