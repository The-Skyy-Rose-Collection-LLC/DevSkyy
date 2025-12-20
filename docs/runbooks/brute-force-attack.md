# Brute Force Attack Response

**Severity Level**: HIGH
**Last Updated**: 2025-12-19
**Owner**: Security Operations Team
**Related**: [Security Incident Response Master Procedure](/Users/coreyfoster/DevSkyy/docs/runbooks/security-incident-response.md)

## Overview

Brute force attacks attempt to gain unauthorized access by systematically trying multiple password combinations or API keys. This runbook covers detection, containment, and mitigation of brute force attacks against authentication endpoints.

## Detection

### Alert Triggers

**Automated Alerts:**

- Failed login attempts > 5 from single IP within 5 minutes
- Failed login attempts > 10 from single user account within 10 minutes
- Failed API authentication > 20 from single IP within 1 minute
- Pattern matching for credential stuffing (testing known breached passwords)
- Geographic anomalies (login attempts from unusual countries)

**Security Monitoring Rules:**

```python
# Example monitoring rule in security/monitoring.py
BRUTE_FORCE_THRESHOLDS = {
    "failed_login_per_ip": (5, 300),      # 5 attempts in 300 seconds
    "failed_login_per_user": (10, 600),   # 10 attempts in 600 seconds
    "failed_api_auth": (20, 60),          # 20 attempts in 60 seconds
    "password_spray": (50, 3600),         # 50 different users in 1 hour
}
```

### How to Identify

1. **Check Security Dashboard**

   ```bash
   # Query failed authentication attempts
   psql $DATABASE_URL -c "
   SELECT
     ip_address,
     user_id,
     COUNT(*) as attempts,
     MIN(created_at) as first_attempt,
     MAX(created_at) as last_attempt
   FROM security_events
   WHERE event_type = 'failed_login'
     AND created_at > NOW() - INTERVAL '1 hour'
   GROUP BY ip_address, user_id
   HAVING COUNT(*) > 5
   ORDER BY attempts DESC;
   "
   ```

2. **Analyze Attack Patterns**

   ```bash
   # Check for password spray attacks (many users, few attempts each)
   psql $DATABASE_URL -c "
   SELECT
     ip_address,
     COUNT(DISTINCT user_id) as unique_users,
     COUNT(*) as total_attempts
   FROM security_events
   WHERE event_type = 'failed_login'
     AND created_at > NOW() - INTERVAL '1 hour'
   GROUP BY ip_address
   HAVING COUNT(DISTINCT user_id) > 10;
   "
   ```

3. **Check Application Logs**

   ```bash
   # Grep for failed authentication
   grep "authentication failed" /var/log/skyyrose/api.log | tail -100

   # Check nginx access logs for auth endpoints
   awk '$7 ~ /\/api\/auth\/login/ && $9 == 401' /var/log/nginx/access.log | wc -l
   ```

4. **Geographic Analysis**

   ```bash
   # Check for unusual countries (requires GeoIP database)
   grep "failed_login" /var/log/skyyrose/security.log | \
   geoiplookup -f /usr/share/GeoIP/GeoIP.dat | \
   sort | uniq -c | sort -rn
   ```

## Triage

### Severity Assessment

**HIGH Severity - Immediate Response Required:**

- Successful authentication followed by suspicious activity
- Brute force attack on admin/privileged accounts
- Coordinated attack from multiple IPs (distributed brute force)
- Credential stuffing using known breach data
- > 1000 failed attempts in 1 hour

**MEDIUM Severity - Response within 1 hour:**

- Standard brute force on regular user accounts
- Failed attempts from single IP address
- < 1000 failed attempts in 1 hour
- Automated bot activity (user agent patterns)

**LOW Severity - Monitor:**

- Isolated failed login attempts
- User legitimately forgetting password
- < 10 failed attempts per IP

### Initial Containment Steps

1. **Block Attacking IP Addresses**

   ```bash
   # Block IP at firewall level
   ufw deny from <ATTACKER_IP>

   # Block IP in nginx (add to /etc/nginx/blocked-ips.conf)
   echo "deny <ATTACKER_IP>;" >> /etc/nginx/blocked-ips.conf
   nginx -s reload

   # Block IP range if distributed attack
   ufw deny from <ATTACKER_IP_RANGE>/24
   ```

2. **Enable Rate Limiting**

   ```python
   # Update rate limits in security/rate_limiter.py
   RATE_LIMITS = {
       "login": "3 per 5 minutes",
       "api_auth": "10 per 1 minute"
   }
   ```

3. **Lock Compromised Accounts**

   ```bash
   # Disable targeted user accounts
   psql $DATABASE_URL -c "
   UPDATE users
   SET locked = true, locked_reason = 'Brute force attack detected'
   WHERE id IN (
     SELECT DISTINCT user_id
     FROM security_events
     WHERE event_type = 'failed_login'
       AND created_at > NOW() - INTERVAL '1 hour'
     GROUP BY user_id
     HAVING COUNT(*) > 10
   );
   "
   ```

4. **Alert Affected Users**

   ```python
   # Send security notification
   python scripts/send_security_alert.py \
     --template brute_force_warning \
     --user-ids <AFFECTED_USER_IDS>
   ```

### Escalation Procedures

**Immediate Escalation (HIGH Severity):**

1. Notify Security Lead via phone: [PHONE]
2. Create incident war room: `#incident-brute-force-YYYYMMDD`
3. Page on-call DevOps engineer
4. Alert executive team if admin accounts targeted

**Standard Escalation (MEDIUM Severity):**

1. Post in `#security-alerts` channel
2. Notify Security Lead via Slack
3. Create incident ticket in JIRA

## Investigation

### Log Queries

1. **Identify Attack Source**

   ```bash
   # Get detailed attack timeline
   psql $DATABASE_URL -c "
   SELECT
     created_at,
     ip_address,
     user_agent,
     username_attempted,
     failure_reason
   FROM security_events
   WHERE event_type = 'failed_login'
     AND ip_address = '<ATTACKER_IP>'
   ORDER BY created_at DESC
   LIMIT 100;
   "
   ```

2. **Check for Successful Breaches**

   ```bash
   # Find successful logins from attacking IPs
   psql $DATABASE_URL -c "
   SELECT
     sl.created_at,
     sl.ip_address,
     sl.user_id,
     u.email,
     sl.session_id
   FROM successful_logins sl
   JOIN users u ON sl.user_id = u.id
   WHERE sl.ip_address IN (
     SELECT DISTINCT ip_address
     FROM security_events
     WHERE event_type = 'failed_login'
       AND created_at > NOW() - INTERVAL '1 hour'
     GROUP BY ip_address
     HAVING COUNT(*) > 10
   )
   AND sl.created_at > NOW() - INTERVAL '1 hour';
   "
   ```

3. **Analyze User Agent Patterns**

   ```bash
   # Identify bot signatures
   psql $DATABASE_URL -c "
   SELECT user_agent, COUNT(*) as count
   FROM security_events
   WHERE event_type = 'failed_login'
     AND created_at > NOW() - INTERVAL '1 hour'
   GROUP BY user_agent
   ORDER BY count DESC;
   "
   ```

### Data Collection Checklist

- [ ] Complete list of attacking IP addresses
- [ ] Targeted user accounts (usernames/emails)
- [ ] Attack timeframe (start and end times)
- [ ] Total number of failed attempts
- [ ] User agents (identify bots vs. legitimate browsers)
- [ ] Geographic origin (GeoIP lookup)
- [ ] Attack pattern (single IP, distributed, password spray)
- [ ] Any successful authentications during attack window
- [ ] Session data for successful logins (if any)

### Root Cause Analysis

**Common Root Causes:**

1. **Weak Password Policy**: Users choosing easily guessable passwords
2. **No Rate Limiting**: Unlimited authentication attempts allowed
3. **Lack of Account Lockout**: No automatic account locking after failed attempts
4. **No CAPTCHA**: Missing human verification on login forms
5. **Exposed User Enumeration**: Login page reveals if username exists
6. **No MFA**: Multi-factor authentication not enforced
7. **Credential Database Breach**: Attackers using previously leaked credentials

**Investigation Steps:**

```bash
# Check if targeted accounts have weak passwords
python scripts/password_strength_audit.py --user-ids <AFFECTED_USER_IDS>

# Verify rate limiting configuration
grep "rate_limit" /etc/nginx/nginx.conf

# Check if MFA is enabled for targeted accounts
psql $DATABASE_URL -c "SELECT id, email, mfa_enabled FROM users WHERE id IN (<AFFECTED_USER_IDS>);"
```

## Remediation

### Step-by-Step Fix Procedures

**1. Block Attack Sources**

```bash
# Get list of attacking IPs
psql $DATABASE_URL -c "
COPY (
  SELECT DISTINCT ip_address
  FROM security_events
  WHERE event_type = 'failed_login'
    AND created_at > NOW() - INTERVAL '1 hour'
  GROUP BY ip_address
  HAVING COUNT(*) > 10
) TO STDOUT;" > attacking_ips.txt

# Block all attacking IPs
while read ip; do
  ufw deny from $ip
  echo "deny $ip;" >> /etc/nginx/blocked-ips.conf
done < attacking_ips.txt

# Reload nginx
nginx -s reload
```

**2. Implement Enhanced Rate Limiting**

```nginx
# Add to /etc/nginx/conf.d/rate-limiting.conf
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=3r/m;

location /api/auth/login {
    limit_req zone=login_limit burst=5 nodelay;
    limit_req_status 429;
}
```

**3. Enable Account Lockout**

```python
# Update security/authentication.py
ACCOUNT_LOCKOUT_CONFIG = {
    "max_failed_attempts": 5,
    "lockout_duration_minutes": 30,
    "notify_user": True
}
```

**4. Deploy CAPTCHA**

```javascript
// Add to frontend/src/components/LoginForm.tsx
import { ReCAPTCHA } from "react-google-recaptcha";

<ReCAPTCHA
  sitekey={process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY}
  onChange={handleRecaptchaChange}
/>
```

**5. Force MFA for Targeted Accounts**

```bash
# Enable MFA for all admin accounts
psql $DATABASE_URL -c "
UPDATE users
SET mfa_required = true
WHERE role IN ('admin', 'superadmin');
"

# Send MFA setup instructions to affected users
python scripts/send_mfa_setup_email.py --role admin
```

**6. Invalidate Suspicious Sessions**

```bash
# Revoke all sessions from attacking IPs
psql $DATABASE_URL -c "
DELETE FROM sessions
WHERE ip_address IN (
  SELECT DISTINCT ip_address
  FROM security_events
  WHERE event_type = 'failed_login'
  GROUP BY ip_address
  HAVING COUNT(*) > 10
);
"

# Force re-authentication
redis-cli KEYS "session:*" | xargs redis-cli DEL
```

**7. Reset Passwords for Compromised Accounts**

```bash
# Force password reset for targeted accounts
psql $DATABASE_URL -c "
UPDATE users
SET password_reset_required = true,
    password_reset_token = gen_random_uuid(),
    password_reset_expires = NOW() + INTERVAL '24 hours'
WHERE id IN (
  SELECT DISTINCT user_id
  FROM security_events
  WHERE event_type = 'failed_login'
  GROUP BY user_id
  HAVING COUNT(*) > 10
);
"

# Send password reset emails
python scripts/send_password_reset.py --reason brute_force_attack
```

### Verification Steps

```bash
# 1. Verify IPs are blocked
nmap -Pn <ATTACKER_IP> | grep "filtered"

# 2. Test rate limiting
ab -n 100 -c 10 https://api.skyyrose.com/api/auth/login
# Should return 429 Too Many Requests after 3 attempts

# 3. Verify account lockouts
psql $DATABASE_URL -c "SELECT id, email, locked FROM users WHERE locked = true;"

# 4. Test CAPTCHA
curl -X POST https://api.skyyrose.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "test"}'
# Should require recaptcha_token

# 5. Verify suspicious sessions invalidated
redis-cli KEYS "session:*" | wc -l
# Should be significantly reduced
```

## Recovery

### Service Restoration Process

1. **Gradual IP Unblocking (if false positives)**

   ```bash
   # Review blocked IPs after 24 hours
   cat /etc/nginx/blocked-ips.conf

   # Unblock legitimate IPs
   sed -i '/deny <LEGITIMATE_IP>/d' /etc/nginx/blocked-ips.conf
   nginx -s reload
   ```

2. **Unlock Legitimate User Accounts**

   ```bash
   # Review locked accounts
   psql $DATABASE_URL -c "SELECT id, email, locked_reason FROM users WHERE locked = true;"

   # Unlock after verification
   psql $DATABASE_URL -c "UPDATE users SET locked = false WHERE id = '<USER_ID>';"
   ```

3. **Restore Normal Rate Limits**

   ```nginx
   # Gradually relax rate limits if necessary
   limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
   ```

### Monitoring During Recovery

```bash
# Monitor failed login rate
watch -n 30 "psql $DATABASE_URL -c \"SELECT COUNT(*) FROM security_events WHERE event_type = 'failed_login' AND created_at > NOW() - INTERVAL '5 minutes';\""

# Monitor successful login rate
watch -n 30 "psql $DATABASE_URL -c \"SELECT COUNT(*) FROM successful_logins WHERE created_at > NOW() - INTERVAL '5 minutes';\""

# Monitor blocked requests
tail -f /var/log/nginx/error.log | grep "429"

# Monitor user complaints
# Check support tickets for login issues
```

### Communication Plan

**Internal:**

1. Update `#security-alerts` with resolution status
2. Brief engineering team on new security controls
3. Document incident in post-mortem

**External (Affected Users):**

```
Subject: Security Notice - Your Account Was Protected

Dear [User],

We detected unusual login activity on your account and took immediate action to protect your security. Your account was temporarily locked and we've reset your password as a precaution.

What happened:
We identified a brute force attack attempting to access multiple accounts, including yours.

What we did:
- Blocked the attacking IPs
- Locked your account temporarily
- Invalidated all active sessions
- Enabled additional security measures

What you need to do:
1. Reset your password using the link below
2. Enable two-factor authentication (highly recommended)
3. Review recent account activity

Reset Password: [LINK]

If you didn't attempt to log in recently, please contact security@skyyrose.com immediately.

Thank you,
SkyyRose Security Team
```

## Post-Mortem

### Key Metrics to Track

- Total failed login attempts during attack
- Number of unique attacking IPs
- Number of targeted user accounts
- Time to detection
- Time to containment
- Number of compromised accounts (if any)
- Attack duration

### Preventive Measures

- [ ] Enforce strong password policy (minimum 12 characters, complexity requirements)
- [ ] Implement progressive delays (increase delay after each failed attempt)
- [ ] Deploy bot detection (fingerprinting, behavioral analysis)
- [ ] Enable MFA for all accounts (mandatory for admins, optional for users)
- [ ] Implement IP reputation scoring
- [ ] Add honeypot fields to login forms (detect bots)
- [ ] Monitor HaveIBeenPwned for credential leaks
- [ ] Conduct security awareness training
- [ ] Implement WebAuthn/FIDO2 for passwordless authentication
- [ ] Deploy advanced WAF rules for brute force detection

### Follow-Up Actions

1. Review and strengthen password policy
2. Mandate MFA for all admin accounts within 7 days
3. Deploy improved rate limiting across all auth endpoints
4. Implement account lockout with exponential backoff
5. Add CAPTCHA to login form after 3 failed attempts
6. Set up automated IP blocking in Cloudflare
7. Conduct penetration test on authentication system
8. Schedule quarterly security training for all engineers

## Contact Information

### Incident Response Team

| Role | Slack | Email |
|------|-------|-------|
| Security Lead | @security-lead | <security-lead@skyyrose.com> |
| DevOps Lead | @devops-lead | <devops-lead@skyyrose.com> |
| On-Call Engineer | @oncall | <oncall@skyyrose.com> |

## Slack Notification Template

```
:shield: **BRUTE FORCE ATTACK DETECTED** :shield:

**Incident ID**: INC-BF-YYYYMMDD-HHmm
**Severity**: HIGH
**Status**: INVESTIGATING

**Attack Details**:
- Attacking IP(s): <IP_ADDRESSES>
- Targeted Account(s): <AFFECTED_ACCOUNTS>
- Failed Attempts: <COUNT>
- Attack Duration: <START_TIME> to <END_TIME>

**Immediate Actions Taken**:
- Blocked <X> attacking IP addresses
- Locked <Y> targeted user accounts
- Enabled enhanced rate limiting
- Invalidated suspicious sessions

**Incident Commander**: @[name]
**War Room**: #incident-bf-YYYYMMDD-HHmm

**Next Steps**:
- RCA in progress
- User notifications pending
- Post-mortem scheduled for [DATE/TIME]

**Next Update**: [TIMESTAMP]
```

## Related Runbooks

- [Security Incident Response Master Procedure](/Users/coreyfoster/DevSkyy/docs/runbooks/security-incident-response.md)
- [Authentication Bypass](/Users/coreyfoster/DevSkyy/docs/runbooks/authentication-bypass.md)
- [Data Breach](/Users/coreyfoster/DevSkyy/docs/runbooks/data-breach.md)
- [API Key Leak](/Users/coreyfoster/DevSkyy/docs/runbooks/api-key-leak.md)
