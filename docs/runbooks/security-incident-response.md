# Security Incident Response - Master Procedure

**Severity Level**: CRITICAL/HIGH/MEDIUM (context-dependent)
**Last Updated**: 2025-12-19
**Owner**: Security Operations Team

## Overview

This is the master incident response procedure that governs all security incidents. All specific runbooks reference this procedure as the foundational framework.

## Detection

### Alert Triggers

- Security monitoring system alerts (SIEM, IDS/IPS)
- Automated threat detection from security scanners
- User reports of suspicious activity
- Third-party security notifications (e.g., AWS GuardDuty, GitHub security alerts)
- Anomaly detection from log analysis
- Breach notifications from external parties

### How to Identify

1. Monitor security dashboard for critical alerts
2. Review automated security notifications in Slack `#security-alerts` channel
3. Check email for external breach notifications
4. Analyze logs for unusual patterns:

   ```bash
   # Check recent security events
   tail -f /var/log/security/incidents.log

   # Query PostgreSQL for failed auth attempts
   psql $DATABASE_URL -c "SELECT * FROM security_events WHERE severity = 'CRITICAL' AND created_at > NOW() - INTERVAL '1 hour';"
   ```

## Triage

### Severity Assessment Matrix

| Severity | Criteria | Response Time |
|----------|----------|---------------|
| **CRITICAL** | Active data breach, system compromise, ransomware | Immediate (< 15 min) |
| **HIGH** | Attempted breach, credential leak, DDoS attack | < 1 hour |
| **MEDIUM** | Brute force attempt, XSS/SQLi detected and blocked | < 4 hours |
| **LOW** | Anomalous but non-threatening behavior | < 24 hours |

### Initial Containment Steps

1. **STOP** - Do not panic, follow the runbook
2. **ASSESS** - Determine severity using matrix above
3. **NOTIFY** - Alert incident response team immediately
4. **ISOLATE** - Contain the threat (block IPs, revoke tokens, disable accounts)
5. **DOCUMENT** - Start incident log immediately

### Escalation Procedures

**CRITICAL Incidents:**

1. Notify Security Lead immediately via phone
2. Page on-call DevOps engineer
3. Alert executive team (CTO, CEO)
4. Create incident war room (Slack channel: `#incident-YYYYMMDD-HHmm`)

**HIGH Incidents:**

1. Notify Security Lead via Slack
2. Alert DevOps team
3. Create incident thread in `#security-alerts`

**MEDIUM/LOW Incidents:**

1. Log in incident tracking system
2. Notify Security Lead via Slack
3. Schedule post-incident review

## Investigation

### Log Collection

```bash
# Collect application logs
docker logs skyyrose-api --since 2h > incident-app-logs.txt

# Collect nginx access logs
grep "suspicious-pattern" /var/log/nginx/access.log > incident-nginx-logs.txt

# Collect security events from PostgreSQL
psql $DATABASE_URL -c "\COPY (SELECT * FROM security_events WHERE created_at > NOW() - INTERVAL '24 hours') TO 'incident-security-events.csv' CSV HEADER;"

# Collect Redis cache data (if relevant)
redis-cli --scan --pattern "session:*" > incident-sessions.txt

# AWS CloudWatch logs (if using AWS)
aws logs tail /aws/lambda/skyyrose-api --since 2h --format short > incident-cloudwatch.txt
```

### Data Collection Checklist

- [ ] Timeline of events (first detection, actions taken)
- [ ] Affected systems and services
- [ ] Compromised accounts or credentials
- [ ] IP addresses involved (attacker and victim)
- [ ] Network traffic captures (if applicable)
- [ ] Database query logs
- [ ] Application logs
- [ ] System logs (syslog, auth.log)
- [ ] File integrity reports
- [ ] Memory dumps (for malware analysis)

### Root Cause Analysis (RCA)

#### 5 Whys Technique

1. **Why did the incident occur?** (e.g., API key was leaked)
2. **Why was the API key leaked?** (e.g., committed to public GitHub repo)
3. **Why was it committed?** (e.g., developer error, no pre-commit hooks)
4. **Why were there no pre-commit hooks?** (e.g., not part of dev onboarding)
5. **Why wasn't it part of onboarding?** (e.g., no formal security training)

**Root Cause**: Lack of security training and automated secret scanning in development workflow

#### Evidence Preservation

1. Create forensic copies of affected systems
2. Do NOT modify original evidence
3. Maintain chain of custody documentation
4. Store evidence in secure, encrypted location
5. Restrict access to authorized incident response team only

## Remediation

### Step-by-Step Fix Procedures

1. **Eliminate Threat**

   ```bash
   # Block malicious IP addresses
   ufw deny from <ATTACKER_IP>

   # Revoke compromised API keys
   python scripts/revoke_api_key.py --key <COMPROMISED_KEY>

   # Disable compromised user accounts
   psql $DATABASE_URL -c "UPDATE users SET active = false WHERE id = '<USER_ID>';"
   ```

2. **Patch Vulnerabilities**

   ```bash
   # Update dependencies
   pip install --upgrade -r requirements.txt
   npm audit fix

   # Apply security patches
   make security-patch
   ```

3. **Restore Security Posture**
   - Reset all passwords for affected accounts
   - Rotate all API keys and secrets
   - Review and update firewall rules
   - Update WAF rules to block attack patterns
   - Deploy security patches

4. **Implement Additional Controls**
   - Add rate limiting
   - Enable MFA for all admin accounts
   - Deploy additional monitoring
   - Update IDS/IPS signatures

### Verification Steps

```bash
# Verify threat is eliminated
nmap -sV <SYSTEM_IP> | grep "open"

# Verify patches applied
pip list | grep <VULNERABLE_PACKAGE>

# Verify API keys revoked
curl -H "Authorization: Bearer <OLD_KEY>" https://api.skyyrose.com/health
# Should return 401 Unauthorized

# Verify firewall rules
ufw status numbered
```

## Recovery

### Service Restoration Process

1. **Pre-Restoration Checklist**
   - [ ] Threat fully eliminated and verified
   - [ ] All vulnerabilities patched
   - [ ] Security controls strengthened
   - [ ] Backups verified and tested
   - [ ] Stakeholders notified of restoration plan

2. **Phased Restoration**

   ```bash
   # Phase 1: Restore internal services
   docker-compose up -d api database redis

   # Phase 2: Restore non-critical public services
   docker-compose up -d marketing-site

   # Phase 3: Restore critical public services
   docker-compose up -d ecommerce-api payment-gateway
   ```

3. **Verify Service Health**

   ```bash
   # Health checks
   curl https://api.skyyrose.com/health

   # Database connectivity
   psql $DATABASE_URL -c "SELECT 1;"

   # Redis connectivity
   redis-cli ping
   ```

### Monitoring During Recovery

```bash
# Monitor error rates
watch -n 5 'curl -s https://api.skyyrose.com/metrics | grep error_rate'

# Monitor response times
ab -n 100 -c 10 https://api.skyyrose.com/health

# Monitor logs for anomalies
tail -f /var/log/skyyrose/api.log | grep -i "error\|warning"
```

### Communication Plan

**Internal Communications:**

1. Update incident war room with restoration status
2. Notify all engineering teams of service restoration
3. Brief executive team on incident resolution

**External Communications (if applicable):**

1. Notify affected customers via email
2. Post status update to status page
3. Issue public statement (if data breach)
4. Notify regulatory bodies (if required by GDPR, HIPAA, etc.)

## Post-Mortem

### Incident Report Timeline

Within 24 hours of resolution, complete the [Post-Mortem Template](/Users/coreyfoster/DevSkyy/docs/POST_MORTEM_TEMPLATE.md)

### Post-Mortem Meeting

**Attendees:** Incident response team, engineering leads, security team, executives

**Agenda:**

1. Incident timeline review (15 min)
2. What went well (10 min)
3. What went wrong (15 min)
4. Action items and ownership (15 min)
5. Preventive measures (10 min)

### Follow-Up Actions

- [ ] Document lessons learned
- [ ] Update runbooks with new procedures
- [ ] Implement preventive controls
- [ ] Schedule security training (if needed)
- [ ] Review and update incident response plan
- [ ] Conduct tabletop exercise to test improvements

## Contact Information

### Incident Response Team

| Role | Name | Phone | Email | Slack |
|------|------|-------|-------|-------|
| Security Lead | [NAME] | [PHONE] | <security-lead@skyyrose.com> | @security-lead |
| DevOps Lead | [NAME] | [PHONE] | <devops-lead@skyyrose.com> | @devops-lead |
| CTO | [NAME] | [PHONE] | <cto@skyyrose.com> | @cto |
| Legal Counsel | [NAME] | [PHONE] | <legal@skyyrose.com> | @legal |

### External Contacts

| Organization | Purpose | Contact |
|--------------|---------|---------|
| AWS Support | Infrastructure issues | AWS Console > Support |
| Cloudflare | DDoS mitigation | 1-888-99-FLARE |
| FBI Cyber Division | Critical incidents | IC3.gov |
| Local Law Enforcement | Physical threats | 911 |

## Slack Notification Template

```
:rotating_light: **SECURITY INCIDENT DETECTED** :rotating_light:

**Incident ID**: INC-YYYYMMDD-HHmm
**Severity**: [CRITICAL/HIGH/MEDIUM/LOW]
**Type**: [Incident Type]
**Detected At**: [Timestamp]
**Status**: INVESTIGATING

**Initial Assessment**:
[Brief description of the incident]

**Immediate Actions Taken**:
- [Action 1]
- [Action 2]

**Incident Commander**: @[name]
**War Room**: #incident-YYYYMMDD-HHmm

**Next Update**: [Timestamp]
```

## Appendix

### Related Runbooks

- [Brute Force Attack](/Users/coreyfoster/DevSkyy/docs/runbooks/brute-force-attack.md)
- [Data Breach](/Users/coreyfoster/DevSkyy/docs/runbooks/data-breach.md)
- [DDoS Attack](/Users/coreyfoster/DevSkyy/docs/runbooks/ddos-attack.md)
- [API Key Leak](/Users/coreyfoster/DevSkyy/docs/runbooks/api-key-leak.md)
- [SQL Injection](/Users/coreyfoster/DevSkyy/docs/runbooks/sql-injection.md)
- [XSS Attack](/Users/coreyfoster/DevSkyy/docs/runbooks/xss-attack.md)
- [Authentication Bypass](/Users/coreyfoster/DevSkyy/docs/runbooks/authentication-bypass.md)
- [Zero-Day Vulnerability](/Users/coreyfoster/DevSkyy/docs/runbooks/zero-day-vulnerability.md)
- [Ransomware Attack](/Users/coreyfoster/DevSkyy/docs/runbooks/ransomware-attack.md)

### Reference Materials

- NIST Cybersecurity Framework
- SANS Incident Handler's Handbook
- OWASP Incident Response Guide
- CIS Critical Security Controls
