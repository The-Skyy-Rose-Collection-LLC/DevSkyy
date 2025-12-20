# Authentication Bypass Response

**Severity Level**: CRITICAL
**Last Updated**: 2025-12-19
**Owner**: Security Operations Team
**Related**: [Security Incident Response Master Procedure](/Users/coreyfoster/DevSkyy/docs/runbooks/security-incident-response.md)

## Overview

Authentication bypass allows unauthorized access to protected resources by circumventing authentication mechanisms. This runbook covers detection, containment, and remediation of authentication bypass vulnerabilities.

## Detection

### Alert Triggers

**Automated Alerts:**

- Unauthorized access to protected endpoints (401/403 followed by 200)
- Session tokens used without prior authentication
- JWT token manipulation attempts
- Cookie tampering detection
- Access to admin endpoints from non-admin accounts
- Authentication decorator bypasses
- Direct object reference without auth check

### How to Identify

1. **Access Log Analysis**

   ```bash
   # Check for 401/403 followed by successful 200
   awk '
     NR==FNR { if ($9 ~ /^(401|403)$/) failed[$1,$7] = 1; next }
     ($1,$7) in failed && $9 == 200 { print }
   ' /var/log/nginx/access.log /var/log/nginx/access.log

   # Check for admin access from regular users
   grep "/api/admin/" /var/log/nginx/access.log | \
   awk '$9 == 200 {print $1, $7, $9}'
   ```

2. **Application Logs**

   ```bash
   # Check for authentication bypass attempts
   grep -E "bypass|unauthorized.*success|auth.*skip" /var/log/skyyrose/api.log

   # Look for role escalation
   grep -E "role.*admin|privilege.*escalation" /var/log/skyyrose/security.log
   ```

3. **Database Audit**

   ```bash
   # Check for suspicious access patterns
   psql $DATABASE_URL -c "
   SELECT
     al.created_at,
     al.user_id,
     al.action,
     al.resource,
     u.role
   FROM audit_log al
   JOIN users u ON al.user_id = u.id
   WHERE al.resource LIKE '/admin/%'
     AND u.role != 'admin'
     AND al.created_at > NOW() - INTERVAL '24 hours'
   ORDER BY al.created_at DESC;
   "
   ```

## Triage

### Severity Assessment

**CRITICAL:**

- Admin panel accessible without authentication
- Payment processing bypassed
- User data accessible without auth
- JWT secret compromised
- Session hijacking successful

**HIGH:**

- Partial authentication bypass
- Role-based access control (RBAC) bypass
- API endpoints accessible without token
- Session fixation vulnerability

### Initial Containment Steps

1. **Block Unauthorized Access**

   ```bash
   # Get IPs with suspicious access
   grep "/api/admin/" /var/log/nginx/access.log | \
   awk '$9 == 200 {print $1}' | sort | uniq > /tmp/suspicious_ips.txt

   # Block IPs
   while read ip; do
     ufw deny from $ip
   done < /tmp/suspicious_ips.txt
   ```

2. **Revoke All Sessions**

   ```bash
   # Invalidate all active sessions
   redis-cli FLUSHDB

   # Mark all sessions as invalid in DB
   psql $DATABASE_URL -c "UPDATE sessions SET valid = false, invalidated_at = NOW();"
   ```

3. **Enforce Authentication**

   ```python
   # Deploy emergency auth middleware
   @app.middleware("http")
   async def enforce_auth(request: Request, call_next):
       if request.url.path.startswith("/api/"):
           auth_header = request.headers.get("authorization")
           if not auth_header:
               return JSONResponse(
                   status_code=401,
                   content={"error": "Authentication required"}
               )
       return await call_next(request)
   ```

## Investigation

### Vulnerability Analysis

1. **Check Authentication Decorators**

   ```bash
   # Find endpoints without auth decorators
   grep -rn "@app\.\(get\|post\|put\|delete\)" apps/ --include="*.py" | \
   grep -v "@require_auth\|@login_required\|@authenticated"
   ```

2. **JWT Token Analysis**

   ```bash
   # Check if JWT secret is weak
   python scripts/check_jwt_strength.py

   # Test token manipulation
   python scripts/test_jwt_bypass.py --target https://api.skyyrose.com
   ```

## Remediation

### Fix Procedures

1. **Implement Mandatory Authentication**

   ```python
   from functools import wraps
   from fastapi import HTTPException, Depends
   from fastapi.security import HTTPBearer

   security = HTTPBearer()

   async def verify_token(credentials: str = Depends(security)):
       try:
           payload = jwt.decode(
               credentials.credentials,
               JWT_SECRET,
               algorithms=["HS256"]
           )
           return payload
       except jwt.InvalidTokenError:
           raise HTTPException(401, "Invalid token")

   # Apply to all routes
   @app.get("/api/protected", dependencies=[Depends(verify_token)])
   async def protected_endpoint():
       return {"data": "protected"}
   ```

2. **Implement RBAC**

   ```python
   def require_role(required_role: str):
       def decorator(func):
           @wraps(func)
           async def wrapper(*args, **kwargs):
               token = await verify_token()
               user_role = token.get("role")
               if user_role != required_role:
                   raise HTTPException(403, "Insufficient permissions")
               return await func(*args, **kwargs)
           return wrapper
       return decorator

   @app.get("/api/admin/users")
   @require_role("admin")
   async def get_users():
       return await db.fetch_all("SELECT * FROM users")
   ```

## Recovery

### Verification Steps

```bash
# Test that auth is required
curl -X GET https://api.skyyrose.com/api/protected
# Should return 401

# Test with valid token
curl -X GET https://api.skyyrose.com/api/protected \
  -H "Authorization: Bearer $VALID_TOKEN"
# Should return 200

# Test role enforcement
curl -X GET https://api.skyyrose.com/api/admin/users \
  -H "Authorization: Bearer $USER_TOKEN"
# Should return 403
```

## Post-Mortem

### Preventive Measures

- [ ] Implement authentication middleware on all routes
- [ ] Deploy RBAC framework
- [ ] Regular security audits of auth code
- [ ] Automated auth testing in CI/CD
- [ ] Security training on auth best practices

## Contact Information

| Role | Contact |
|------|---------|
| Security Lead | @security-lead |
| Backend Lead | @backend-lead |

## Slack Notification Template

```
:lock: **AUTHENTICATION BYPASS DETECTED** :lock:

**Incident ID**: INC-AUTHBYPASS-YYYYMMDD-HHmm
**Severity**: CRITICAL
**Status**: MITIGATING

**Details**:
- Vulnerable Endpoint: [ENDPOINT]
- Bypass Method: [JWT/Session/Cookie]
- Affected Resources: [LIST]

**ACTIONS TAKEN**:
- All sessions revoked
- Auth middleware enforced
- Suspicious IPs blocked

**Incident Commander**: @security-lead
```

## Related Runbooks

- [Security Incident Response Master Procedure](/Users/coreyfoster/DevSkyy/docs/runbooks/security-incident-response.md)
- [Brute Force Attack](/Users/coreyfoster/DevSkyy/docs/runbooks/brute-force-attack.md)
- [Data Breach](/Users/coreyfoster/DevSkyy/docs/runbooks/data-breach.md)
