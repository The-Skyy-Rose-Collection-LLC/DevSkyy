# SQL Injection Attack Response

**Severity Level**: CRITICAL
**Last Updated**: 2025-12-19
**Owner**: Security Operations Team
**Related**: [Security Incident Response Master Procedure](/Users/coreyfoster/DevSkyy/docs/runbooks/security-incident-response.md)

## Overview

SQL Injection (SQLi) attacks exploit vulnerabilities in database queries to execute unauthorized SQL commands, potentially leading to data breaches, data manipulation, or complete system compromise. This runbook covers detection, containment, and remediation of SQL injection attacks.

## Detection

### Alert Triggers

**Automated Alerts:**

- WAF rules detecting SQL injection patterns
- Database query errors (syntax errors, unexpected failures)
- Unusual SQL commands in query logs (UNION, DROP, UPDATE WHERE 1=1)
- Database access from application with elevated privileges
- Query execution time anomalies
- Multiple failed queries from same IP
- SQL pattern matching in application logs

**SQL Injection Patterns:**

```regex
# Common SQLi patterns to detect
' OR '1'='1
' OR 1=1--
'; DROP TABLE
UNION SELECT
EXEC(\s|%20)
CAST\(
CONCAT\(
WAITFOR DELAY
pg_sleep\(
information_schema
```

### How to Identify

1. **Check WAF Logs**

   ```bash
   # Search for SQL injection attempts in Cloudflare WAF
   curl -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/firewall/events?action=block" \
     -H "X-Auth-Email: $CF_EMAIL" \
     -H "X-Auth-Key: $CF_API_KEY" | \
     jq '.result[] | select(.ruleId | contains("sqli"))'

   # Check nginx WAF logs (ModSecurity)
   grep -E "SQL Injection|SQLi" /var/log/modsec_audit.log
   ```

2. **Analyze Database Query Logs**

   ```bash
   # Check PostgreSQL logs for suspicious queries
   grep -E "(UNION SELECT|DROP TABLE|'; DELETE|1=1)" /var/log/postgresql/postgresql.log

   # Check for unexpected queries on sensitive tables
   psql $DATABASE_URL -c "
   SELECT
     query_start,
     usename,
     client_addr,
     state,
     query
   FROM pg_stat_activity
   WHERE query ILIKE '%UNION%'
      OR query ILIKE '%DROP%'
      OR query ILIKE '%DELETE FROM%'
      OR query ILIKE '%UPDATE % SET%'
   ORDER BY query_start DESC;
   "

   # Check slow query log for anomalies
   tail -100 /var/log/postgresql/slow-queries.log
   ```

3. **Application Error Logs**

   ```bash
   # Search for SQL syntax errors
   grep -E "SQL.*error|syntax error|pg_query|QueryException" /var/log/skyyrose/api.log

   # Check for exposed database errors
   grep -E "postgresql|psycopg2|SQLAlchemy.*Error" /var/log/nginx/error.log | tail -50

   # Look for parameter tampering attempts
   grep -E "(\?|&)(id|user|order)=.*('|--|UNION)" /var/log/nginx/access.log
   ```

4. **Monitor Database Activity**

   ```bash
   # Check for unauthorized data access
   psql $DATABASE_URL -c "
   SELECT
     schemaname,
     tablename,
     seq_scan,
     seq_tup_read,
     idx_scan,
     idx_tup_fetch
   FROM pg_stat_user_tables
   WHERE seq_tup_read > 100000
   ORDER BY seq_tup_read DESC;
   "

   # Look for suspicious joins or aggregations
   psql $DATABASE_URL -c "
   SELECT
     query,
     calls,
     total_time,
     mean_time
   FROM pg_stat_statements
   WHERE query ILIKE '%users%'
     AND query ILIKE '%password%'
   ORDER BY total_time DESC
   LIMIT 20;
   "
   ```

5. **Check for Data Exfiltration**

   ```bash
   # Look for UNION-based exfiltration
   psql $DATABASE_URL -c "
   SELECT
     event_time,
     user_name,
     query,
     rows_returned
   FROM pgaudit.audit_log
   WHERE query ILIKE '%UNION SELECT%'
      OR rows_returned > 1000
   ORDER BY event_time DESC
   LIMIT 50;
   "
   ```

## Triage

### Severity Assessment

**CRITICAL - Immediate Response:**

- Successful SQL injection confirmed
- Data exfiltration detected
- Database modifications (DELETE, UPDATE, DROP)
- Admin account compromise
- Sensitive data accessed (passwords, payment info)
- Multiple tables affected

**HIGH - Urgent Response (< 30 min):**

- SQL injection attempts blocked by WAF
- Repeated injection attempts from same source
- Injection on authentication endpoints
- Error messages exposing database structure
- Read-only data access via injection

**MEDIUM - Response within 2 hours:**

- Single failed injection attempt
- Injection attempt on non-sensitive endpoint
- WAF successfully blocking all attempts
- No data accessed or modified

### Initial Containment Steps

**IMMEDIATE ACTIONS (within 5 minutes):**

1. **Block Attacking Sources**

   ```bash
   # Identify attacking IPs
   grep -E "(UNION SELECT|'; DROP|1=1)" /var/log/nginx/access.log | \
   awk '{print $1}' | sort | uniq > /tmp/sqli_attackers.txt

   # Block IPs immediately
   while read ip; do
     ufw deny from $ip
     echo "deny $ip;" >> /etc/nginx/conf.d/blocked-ips.conf
   done < /tmp/sqli_attackers.txt

   nginx -s reload
   ```

2. **Enable Prepared Statements Everywhere**

   ```bash
   # Emergency patch: force parameterized queries
   # Deploy hotfix immediately
   git checkout -b hotfix/sqli-emergency
   # Apply prepared statement patches
   git apply patches/force-prepared-statements.patch
   make deploy-hotfix
   ```

3. **Restrict Database Permissions**

   ```sql
   -- Revoke dangerous permissions from application user
   REVOKE DROP ON DATABASE skyyrose FROM skyyrose_api;
   REVOKE DELETE ON ALL TABLES IN SCHEMA public FROM skyyrose_api;
   REVOKE UPDATE ON ALL TABLES IN SCHEMA public FROM skyyrose_api;

   -- Grant only necessary permissions
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO skyyrose_api;
   GRANT INSERT ON orders, order_items TO skyyrose_api;
   GRANT UPDATE ON users (last_login_at) TO skyyrose_api;

   -- Enable row-level security
   ALTER TABLE users ENABLE ROW LEVEL SECURITY;
   ```

4. **Enable Query Logging**

   ```bash
   # Enable full query logging temporarily
   psql $DATABASE_URL -c "ALTER SYSTEM SET log_statement = 'all';"
   psql $DATABASE_URL -c "ALTER SYSTEM SET log_duration = on;"
   psql $DATABASE_URL -c "SELECT pg_reload_conf();"
   ```

5. **Isolate Affected Endpoints**

   ```bash
   # If specific endpoint is vulnerable, disable it
   # Update nginx to return 503 for vulnerable endpoint
   cat >> /etc/nginx/conf.d/emergency-blocks.conf << 'EOF'
   location /api/vulnerable-endpoint {
     return 503 "Temporarily unavailable for maintenance";
   }
   EOF

   nginx -s reload
   ```

### Escalation Procedures

**CRITICAL SQLi:**

1. **Call** Security Lead: [PHONE]
2. **Call** CTO: [PHONE]
3. **Call** Database Administrator: [PHONE]
4. **Notify** Legal team (if data accessed)
5. **Create** war room: `#incident-sqli-YYYYMMDD`
6. **Assess** if this is part of data breach (escalate to data breach runbook)

## Investigation

### Vulnerability Analysis

1. **Identify Vulnerable Code**

   ```bash
   # Search for string concatenation in SQL queries
   grep -rn "f\"SELECT.*{" apps/ --include="*.py"
   grep -rn '"SELECT.*" + ' apps/ --include="*.py"
   grep -rn 'execute.*%' apps/ --include="*.py"

   # Check for raw SQL without parameters
   grep -rn "cursor.execute.*format\|%" apps/ --include="*.py"

   # Look for ORM bypasses
   grep -rn "\.raw\(|\.extra\(" apps/ --include="*.py"
   ```

2. **Reproduce the Vulnerability**

   ```bash
   # Test injection on identified endpoint (in dev environment!)
   curl -X GET "http://localhost:8000/api/products?id=1' OR '1'='1" \
     -H "Authorization: Bearer $DEV_TOKEN"

   # Try UNION-based injection
   curl -X GET "http://localhost:8000/api/products?id=1 UNION SELECT id,email,password FROM users--" \
     -H "Authorization: Bearer $DEV_TOKEN"

   # Test blind injection
   curl -X GET "http://localhost:8000/api/products?id=1 AND pg_sleep(5)--" \
     -H "Authorization: Bearer $DEV_TOKEN"
   ```

3. **Assess Data Impact**

   ```bash
   # Check what data was accessed
   psql $DATABASE_URL -c "
   SELECT
     event_time,
     user_name,
     client_addr,
     object_name,
     command_tag,
     rows_returned
   FROM pgaudit.audit_log
   WHERE client_addr = '<ATTACKER_IP>'
     OR query ILIKE '%UNION SELECT%'
   ORDER BY event_time;
   "

   # Check for data modifications
   psql $DATABASE_URL -c "
   SELECT
     event_time,
     user_name,
     command_tag,
     object_name,
     rows_affected
   FROM pgaudit.audit_log
   WHERE command_tag IN ('UPDATE', 'DELETE', 'DROP')
     AND event_time > '<ATTACK_START_TIME>'
   ORDER BY event_time;
   "
   ```

### Data Collection Checklist

- [ ] Vulnerable endpoint(s) identified
- [ ] Vulnerable code location (file, line number)
- [ ] Type of SQL injection (UNION, blind, error-based, etc.)
- [ ] Attack timeline (first attempt to last)
- [ ] Attacking IP addresses
- [ ] SQL commands executed
- [ ] Tables accessed
- [ ] Data exfiltrated (row count, sensitive fields)
- [ ] Data modified or deleted
- [ ] Application errors generated
- [ ] WAF logs showing block/allow decisions

### Root Cause Analysis

**Common Causes:**

1. **String Concatenation in Queries**

   ```python
   # VULNERABLE
   query = f"SELECT * FROM products WHERE id = {product_id}"
   cursor.execute(query)
   ```

2. **Unsafe ORM Usage**

   ```python
   # VULNERABLE
   User.objects.raw(f"SELECT * FROM users WHERE username = '{username}'")
   ```

3. **Improper Input Validation**

   ```python
   # VULNERABLE - no validation
   product_id = request.args.get('id')
   query = f"SELECT * FROM products WHERE id = {product_id}"
   ```

4. **Dynamic Query Building**

   ```python
   # VULNERABLE
   filters = request.args.get('filters')  # "1=1 OR"
   query = f"SELECT * FROM products WHERE {filters}"
   ```

## Remediation

### Step-by-Step Fix Procedures

**1. Fix Vulnerable Code - Use Parameterized Queries**

```python
# BEFORE (VULNERABLE)
def get_product(product_id):
    query = f"SELECT * FROM products WHERE id = {product_id}"
    cursor.execute(query)
    return cursor.fetchone()

# AFTER (SECURE)
def get_product(product_id):
    query = "SELECT * FROM products WHERE id = %s"
    cursor.execute(query, (product_id,))
    return cursor.fetchone()

# Using ORM (SECURE)
def get_product(product_id):
    return Product.objects.get(id=product_id)
```

**2. Implement Input Validation**

```python
from pydantic import BaseModel, validator, Field

class ProductQuery(BaseModel):
    id: int = Field(..., gt=0)

    @validator('id')
    def validate_id(cls, v):
        if not isinstance(v, int):
            raise ValueError('Product ID must be an integer')
        if v < 1 or v > 999999:
            raise ValueError('Invalid product ID range')
        return v

@app.get("/api/products")
async def get_product(query: ProductQuery):
    product = await db.fetch_one(
        "SELECT * FROM products WHERE id = :id",
        values={"id": query.id}
    )
    return product
```

**3. Enable Database-Level Protection**

```sql
-- Create read-only user for most operations
CREATE ROLE skyyrose_readonly;
GRANT CONNECT ON DATABASE skyyrose TO skyyrose_readonly;
GRANT USAGE ON SCHEMA public TO skyyrose_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO skyyrose_readonly;

-- Create limited write user
CREATE ROLE skyyrose_writer;
GRANT skyyrose_readonly TO skyyrose_writer;
GRANT INSERT ON orders, order_items, users TO skyyrose_writer;
GRANT UPDATE ON users (last_login_at, updated_at) TO skyyrose_writer;

-- Enable query length limit
ALTER DATABASE skyyrose SET max_statement_length = '1MB';

-- Enable statement timeout
ALTER DATABASE skyyrose SET statement_timeout = '30s';
```

**4. Deploy WAF Rules**

```nginx
# ModSecurity rules for SQL injection
SecRule ARGS "@detectSQLi" \
    "id:1001,phase:2,block,log,msg:'SQL Injection Attack Detected'"

SecRule ARGS "@rx (?i:(\bunion\b.+\bselect\b|\bselect\b.+\bunion\b))" \
    "id:1002,phase:2,block,log,msg:'SQL Injection UNION Attack'"

SecRule ARGS "@rx (?i:(exec\s*\(|execute\s*\(|waitfor\s+delay|pg_sleep))" \
    "id:1003,phase:2,block,log,msg:'SQL Injection Time-Based Attack'"

# Cloudflare WAF custom rule
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/firewall/rules" \
  -H "X-Auth-Email: $CF_EMAIL" \
  -H "X-Auth-Key: $CF_API_KEY" \
  -H "Content-Type: application/json" \
  --data '{
    "filter": {
      "expression": "(http.request.uri.query contains \"UNION SELECT\") or (http.request.uri.query contains \"DROP TABLE\") or (http.request.uri.query contains \"1=1\")"
    },
    "action": "block",
    "description": "Block SQL Injection Attempts"
  }'
```

**5. Implement Prepared Statements Framework-Wide**

```python
# Create database wrapper that enforces prepared statements
class SecureDatabase:
    def __init__(self, connection_string):
        self.engine = create_engine(connection_string)

    def execute(self, query: str, params: dict = None):
        """Only allows parameterized queries"""
        if not params and any(char in query for char in ['%s', '%d', 'f"', "f'"]):
            raise ValueError("Direct string interpolation not allowed. Use parameterized queries.")

        # Use SQLAlchemy text() for safe parameterization
        from sqlalchemy import text
        stmt = text(query)

        with self.engine.connect() as conn:
            return conn.execute(stmt, params or {})

# Usage
db = SecureDatabase(DATABASE_URL)
result = db.execute(
    "SELECT * FROM products WHERE id = :id AND category = :category",
    {"id": product_id, "category": category}
)
```

**6. Code Review All Queries**

```bash
# Audit all database queries in codebase
python scripts/sql_security_audit.py \
  --path apps/ \
  --output security-audit-report.json

# Generate list of files to review
grep -rn "execute\|cursor\|raw" apps/ --include="*.py" > files_to_review.txt

# Create security review tickets
python scripts/create_security_tickets.py --input files_to_review.txt
```

### Verification Steps

```bash
# 1. Test that injection is blocked
curl -X GET "https://api.skyyrose.com/api/products?id=1' OR '1'='1" \
  -H "Authorization: Bearer $TEST_TOKEN"
# Should return 400 Bad Request or 403 Forbidden

# 2. Verify WAF blocks injection attempts
curl -X GET "https://api.skyyrose.com/api/products?id=1 UNION SELECT * FROM users--" \
  -H "Authorization: Bearer $TEST_TOKEN"
# Should return 403 Forbidden with WAF block message

# 3. Test prepared statements are in use
psql $DATABASE_URL -c "
SELECT
  query,
  calls,
  total_time
FROM pg_stat_statements
WHERE query LIKE 'SELECT * FROM products%'
LIMIT 5;
"
# Should show parameterized queries with $1, $2 placeholders

# 4. Verify database permissions
psql $DATABASE_URL -c "
SELECT grantee, privilege_type
FROM information_schema.role_table_grants
WHERE grantee = 'skyyrose_api'
  AND table_name = 'users';
"
# Should only show necessary permissions (no DROP, DELETE on sensitive tables)

# 5. Run automated security scan
sqlmap -u "https://api.skyyrose.com/api/products?id=1" \
  --headers="Authorization: Bearer $TEST_TOKEN" \
  --batch --level=5 --risk=3
# Should find no vulnerabilities
```

## Recovery

### Service Restoration Process

**Phase 1: Immediate Patching (0-2 hours)**

1. Deploy hotfix with parameterized queries
2. Enable WAF rules
3. Verify all injection attempts blocked
4. Monitor application errors
5. Restore vulnerable endpoints

**Phase 2: Data Integrity Check (2-24 hours)**

1. Review all data modifications during attack window
2. Restore from backup if data corrupted
3. Validate data integrity
4. Re-index database if needed

```bash
# Check for data corruption
psql $DATABASE_URL -c "
SELECT
  schemaname,
  tablename,
  n_tup_ins,
  n_tup_upd,
  n_tup_del
FROM pg_stat_user_tables
WHERE last_autovacuum > '<ATTACK_TIME>'
   OR last_autoanalyze > '<ATTACK_TIME>';
"

# Restore from backup if needed
pg_restore --dbname=skyyrose \
  --clean \
  --if-exists \
  --verbose \
  /backups/skyyrose-<BEFORE_ATTACK_TIME>.dump
```

**Phase 3: Security Hardening (24-72 hours)**

1. Complete code audit
2. Implement all security recommendations
3. Deploy enhanced monitoring
4. Conduct penetration test
5. Update security documentation

### Monitoring During Recovery

```bash
# Monitor for continued injection attempts
watch -n 30 'grep -c "SQL Injection" /var/log/modsec_audit.log | tail -1'

# Monitor query patterns
watch -n 60 "psql $DATABASE_URL -c \"
SELECT
  substring(query, 1, 50) as query_preview,
  calls,
  total_time
FROM pg_stat_statements
ORDER BY calls DESC
LIMIT 10;
\""

# Monitor application errors
tail -f /var/log/skyyrose/api.log | grep -E "SQL|Database|Query"
```

### Communication Plan

**Internal Communication:**

```
#security-alerts

:syringe: **SQL Injection Vulnerability Patched**

**Incident**: SQL injection vulnerability in product search endpoint
**Status**: RESOLVED
**Severity**: CRITICAL

**Timeline**:
- [TIME]: Vulnerability detected via WAF alerts
- [TIME]: Vulnerable code identified
- [TIME]: Hotfix deployed with parameterized queries
- [TIME]: WAF rules enabled
- [TIME]: Security testing completed

**Impact**:
- No data exfiltration detected
- No unauthorized modifications
- All attempts blocked by WAF

**Remediation**:
- Deployed prepared statements
- Enhanced input validation
- Restricted database permissions
- Enabled query logging

**Follow-up**:
- Full code audit in progress
- Security training scheduled: [DATE]
- Penetration test scheduled: [DATE]

**Incident Commander**: @security-lead
```

**Customer Communication (if data accessed):**

```
Subject: Security Update - No Action Required

Dear Customer,

We want to inform you of a security vulnerability that was recently detected and immediately resolved.

What Happened:
Our security team identified a SQL injection vulnerability in one of our API endpoints. We immediately patched the vulnerability and verified that no customer data was accessed or compromised.

What We Did:
- Patched the vulnerability within 2 hours of detection
- Enhanced our web application firewall
- Conducted a full security audit
- Implemented additional safeguards

Impact to You:
None. Our investigation confirmed no customer data was accessed or compromised.

Our Commitment:
We take security seriously and continuously monitor, test, and improve our systems to protect your data.

Questions? Contact: security@skyyrose.com

Best regards,
SkyyRose Security Team
```

## Post-Mortem

### Key Metrics

- Time to detection: [X minutes]
- Time to patch: [X hours]
- Number of injection attempts: [X]
- Successful injections: [X]
- Data accessed: [NONE / PII / etc.]
- Data modified: [NONE / X records]
- Endpoints affected: [X]

### Preventive Measures

**Immediate (within 7 days):**

- [ ] Audit all SQL queries for parameterization
- [ ] Deploy WAF rules for SQL injection
- [ ] Implement strict input validation
- [ ] Restrict database user permissions
- [ ] Enable query logging and monitoring

**Short-term (within 30 days):**

- [ ] Implement ORM usage guidelines
- [ ] Deploy automated SQLi scanning in CI/CD
- [ ] Create secure coding standards
- [ ] Conduct developer security training
- [ ] Implement code review checklist for database queries
- [ ] Deploy database activity monitoring

**Long-term (within 90 days):**

- [ ] Implement runtime application self-protection (RASP)
- [ ] Deploy database firewall
- [ ] Conduct annual penetration testing
- [ ] Implement security champions program
- [ ] Create automated security regression tests
- [ ] Implement bug bounty program

### Secure Coding Standards

Create `docs/SECURE_SQL_CODING.md`:

```markdown
# Secure SQL Coding Standards

## Always Use Parameterized Queries

✅ CORRECT:
```python
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

❌ WRONG:

```python
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

## Use ORM Query Builders

✅ CORRECT:

```python
User.objects.filter(id=user_id).first()
```

❌ WRONG:

```python
User.objects.raw(f"SELECT * FROM users WHERE id = {user_id}")
```

## Validate All Input

```python
from pydantic import BaseModel, validator

class UserQuery(BaseModel):
    id: int

    @validator('id')
    def validate_id(cls, v):
        if not 0 < v < 999999:
            raise ValueError('Invalid ID')
        return v
```

## Never Trust User Input

All user input is potentially malicious. Always validate, sanitize, and parameterize.

```

## Contact Information

### Incident Response Team

| Role | Contact | Email |
|------|---------|-------|
| Security Lead | @security-lead | security-lead@skyyrose.com |
| Database Admin | @dba | dba@skyyrose.com |
| DevOps Lead | @devops-lead | devops@skyyrose.com |

## Slack Notification Template

```

:syringe: **SQL INJECTION ATTACK DETECTED** :syringe:

**Incident ID**: INC-SQLI-YYYYMMDD-HHmm
**Severity**: CRITICAL
**Status**: INVESTIGATING

**Attack Details**:

- Endpoint: [VULNERABLE_ENDPOINT]
- Attack Type: [UNION-based / Blind / Error-based]
- Source IP: [ATTACKER_IP]
- Detection: [WAF / Error logs / Manual]

**Initial Assessment**:

- Data Accessed: [INVESTIGATING / CONFIRMED: X records]
- Data Modified: [INVESTIGATING / NO / YES: X records]
- Attack Success: [BLOCKED / PARTIALLY SUCCESSFUL / SUCCESSFUL]

**IMMEDIATE ACTIONS**:

- Blocked attacking IP
- Isolated vulnerable endpoint
- Enabled query logging
- Security team investigating

**Incident Commander**: @security-lead
**War Room**: #incident-sqli-YYYYMMDD

**CRITICAL**: All hands to review database queries in your codebase NOW.

**Next Update**: [TIME]

```

## Related Runbooks

- [Security Incident Response Master Procedure](/Users/coreyfoster/DevSkyy/docs/runbooks/security-incident-response.md)
- [Data Breach](/Users/coreyfoster/DevSkyy/docs/runbooks/data-breach.md)
- [Authentication Bypass](/Users/coreyfoster/DevSkyy/docs/runbooks/authentication-bypass.md)
