# Data Breach Response

**Severity Level**: CRITICAL
**Last Updated**: 2025-12-19
**Owner**: Security Operations Team, Legal Team
**Related**: [Security Incident Response Master Procedure](/Users/coreyfoster/DevSkyy/docs/runbooks/security-incident-response.md)

## Overview

A data breach involves unauthorized access to sensitive data, including customer PII, payment information, credentials, or proprietary business data. This runbook covers immediate containment, forensic investigation, regulatory compliance, and customer notification procedures.

## Detection

### Alert Triggers

**Automated Alerts:**

- Unusual database queries (SELECT * on sensitive tables)
- Large data exports or downloads
- Database access from unauthorized IPs
- Anomalous data transfer volumes
- Access to sensitive tables outside business hours
- Privilege escalation events
- Backup file access by unauthorized users
- Cloud storage bucket permission changes
- AWS GuardDuty alerts (data exfiltration)

**Manual Detection:**

- Third-party breach notification (HaveIBeenPwned, security researcher)
- Customer reports of unauthorized account access
- Suspicious activity in user accounts
- Unexplained charges on customer payment methods
- Dark web monitoring alerts

### How to Identify

1. **Database Access Monitoring**

   ```bash
   # Check for unusual SELECT queries on sensitive tables
   psql $DATABASE_URL -c "
   SELECT
     query_start,
     usename,
     application_name,
     client_addr,
     LEFT(query, 100) as query_preview
   FROM pg_stat_activity
   WHERE query ILIKE '%users%'
      OR query ILIKE '%payment_methods%'
      OR query ILIKE '%orders%'
   ORDER BY query_start DESC
   LIMIT 50;
   "

   # Check database audit logs
   psql $DATABASE_URL -c "
   SELECT
     event_time,
     user_name,
     client_addr,
     command_tag,
     object_name
   FROM pgaudit.audit_log
   WHERE object_name IN ('users', 'payment_methods', 'api_keys')
     AND event_time > NOW() - INTERVAL '24 hours'
   ORDER BY event_time DESC;
   "
   ```

2. **Monitor Data Exfiltration**

   ```bash
   # Check for large data transfers
   awk '$10 > 10000000' /var/log/nginx/access.log | tail -100

   # Monitor S3 bucket access
   aws s3api get-bucket-logging --bucket skyyrose-data

   # Check CloudWatch for unusual data transfer
   aws cloudwatch get-metric-statistics \
     --namespace AWS/S3 \
     --metric-name BytesDownloaded \
     --dimensions Name=BucketName,Value=skyyrose-data \
     --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
     --period 300 \
     --statistics Sum
   ```

3. **Check for Compromised Credentials**

   ```bash
   # Search for credentials in public repositories
   python scripts/github_secret_scanner.py --org skyyrose

   # Check HaveIBeenPwned API
   curl -H "hibp-api-key: $HIBP_API_KEY" \
     https://haveibeenpwned.com/api/v3/breach/skyyrose.com

   # Monitor Pastebin/dark web
   python scripts/darkweb_monitor.py --domain skyyrose.com
   ```

4. **Application Log Analysis**

   ```bash
   # Check for unauthorized API access
   grep "unauthorized" /var/log/skyyrose/api.log | grep -E "(users|payment|orders)"

   # Look for data dump attempts
   grep -E "SELECT \* FROM (users|orders|payment_methods)" /var/log/postgresql/postgresql.log
   ```

## Triage

### Severity Assessment

**CRITICAL - Immediate Executive Notification:**

- Customer PII exposed (names, emails, addresses, SSN)
- Payment card data (PCI DSS breach)
- Authentication credentials (passwords, API keys)
- Health records (HIPAA violation)
- > 1000 customer records affected
- Publicly disclosed breach

**HIGH - Notify Security & Legal Teams:**

- Internal business data exposed
- Encrypted data accessed (but not decrypted)
- 100-1000 customer records affected
- Potential regulatory reporting required

**MEDIUM - Security Team Response:**

- Limited non-sensitive data accessed
- < 100 customer records affected
- Attempted but blocked data access

### Initial Containment Steps

**IMMEDIATE ACTIONS (within 15 minutes):**

1. **Preserve Evidence**

   ```bash
   # DO NOT shut down systems - preserve forensic evidence
   # Take memory dump (if malware suspected)
   sudo dd if=/dev/mem of=/forensics/memory-dump-$(date +%Y%m%d-%H%M%S).raw

   # Create disk image
   sudo dd if=/dev/sda of=/forensics/disk-image-$(date +%Y%m%d-%H%M%S).img bs=4M
   ```

2. **Isolate Compromised Systems**

   ```bash
   # Disconnect from network (but keep running for forensics)
   ip link set eth0 down

   # Revoke database access
   psql $DATABASE_URL -c "REVOKE ALL ON ALL TABLES IN SCHEMA public FROM compromised_user;"

   # Block compromised API keys
   python scripts/revoke_api_key.py --key <COMPROMISED_KEY>
   ```

3. **Stop Data Exfiltration**

   ```bash
   # Block attacker IP addresses
   ufw deny from <ATTACKER_IP>

   # Disable S3 bucket public access
   aws s3api put-public-access-block \
     --bucket skyyrose-data \
     --public-access-block-configuration \
     "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

   # Revoke IAM credentials
   aws iam delete-access-key --access-key-id <COMPROMISED_KEY>
   ```

4. **Lock Affected User Accounts**

   ```bash
   # Identify and lock compromised accounts
   psql $DATABASE_URL -c "
   UPDATE users
   SET locked = true,
       locked_reason = 'Data breach investigation - unauthorized access detected',
       all_sessions_invalidated = true
   WHERE id IN (<AFFECTED_USER_IDS>);
   "
   ```

### Escalation Procedures

**CRITICAL Breach - Immediate Escalation:**

1. **Call** Security Lead immediately: [PHONE]
2. **Call** CTO: [PHONE]
3. **Call** CEO: [PHONE]
4. **Notify** Legal Counsel: [PHONE]
5. **Notify** PR/Communications team
6. **Create** War Room: `#incident-breach-YYYYMMDD`
7. **Conference Call**: Set up bridge immediately

**Regulatory Notifications (if required):**

- GDPR: 72 hours to notify supervisory authority
- HIPAA: 60 days to notify HHS and affected individuals
- PCI DSS: Notify payment brands and acquiring bank immediately
- State breach laws: Varies by state (e.g., California: without unreasonable delay)

## Investigation

### Forensic Data Collection

**DO NOT contaminate evidence. Follow proper chain of custody.**

1. **Database Forensics**

   ```bash
   # Export database access logs
   psql $DATABASE_URL -c "\COPY (
     SELECT * FROM pgaudit.audit_log
     WHERE event_time > '<SUSPECTED_BREACH_TIME>'
     ORDER BY event_time
   ) TO '/forensics/db-audit-logs.csv' CSV HEADER;"

   # Identify accessed records
   psql $DATABASE_URL -c "
   SELECT
     table_name,
     COUNT(*) as records_accessed,
     MIN(event_time) as first_access,
     MAX(event_time) as last_access
   FROM pgaudit.audit_log
   WHERE user_name = '<ATTACKER_USERNAME>'
     AND command_tag = 'SELECT'
   GROUP BY table_name;
   "

   # Identify data exfiltration
   psql $DATABASE_URL -c "
   SELECT
     event_time,
     query,
     rows_returned
   FROM query_logs
   WHERE rows_returned > 100
     AND event_time BETWEEN '<START_TIME>' AND '<END_TIME>'
   ORDER BY rows_returned DESC;
   "
   ```

2. **Application Log Forensics**

   ```bash
   # Extract all activity from attacker IP
   grep "<ATTACKER_IP>" /var/log/nginx/access.log > /forensics/attacker-access.log

   # Extract API calls during breach window
   awk -v start="<START_TIME>" -v end="<END_TIME>" \
     '$4 >= start && $4 <= end' /var/log/skyyrose/api.log > /forensics/breach-api-calls.log

   # Check for data download endpoints
   grep -E "(export|download|csv|json)" /forensics/attacker-access.log
   ```

3. **Network Traffic Analysis**

   ```bash
   # Analyze packet captures (if available)
   tcpdump -r /var/log/tcpdump/capture.pcap -A | grep -E "(user|password|email|ssn)"

   # Check firewall logs
   tail -1000 /var/log/ufw.log | grep "<ATTACKER_IP>"
   ```

4. **Cloud Audit Logs**

   ```bash
   # AWS CloudTrail logs
   aws cloudtrail lookup-events \
     --lookup-attributes AttributeKey=Username,AttributeValue=<ATTACKER_USERNAME> \
     --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
     --max-items 1000 > /forensics/cloudtrail-events.json

   # S3 access logs
   aws s3 cp s3://skyyrose-logs/s3-access/ /forensics/s3-access-logs/ --recursive
   ```

### Data Collection Checklist

- [ ] Complete timeline of unauthorized access
- [ ] List of all affected customer records (IDs, not actual data)
- [ ] Types of data accessed (PII, payment, health, etc.)
- [ ] Attacker information (IPs, user accounts, methods)
- [ ] Entry point and attack vector
- [ ] Data exfiltration method and destination
- [ ] Database query logs
- [ ] Application logs
- [ ] Network traffic captures
- [ ] Cloud audit logs (AWS CloudTrail, etc.)
- [ ] System snapshots and memory dumps
- [ ] Chain of custody documentation

### Root Cause Analysis

**Common Attack Vectors:**

1. **SQL Injection**: Exploited vulnerable query leading to data dump
2. **Compromised Credentials**: Stolen admin password or API key
3. **Insider Threat**: Malicious employee or contractor
4. **Third-Party Breach**: Compromised vendor or partner with access
5. **Misconfigured S3 Bucket**: Public read permissions on sensitive data
6. **API Vulnerability**: Insecure direct object reference (IDOR) or broken access control
7. **Phishing**: Social engineering to obtain credentials

**RCA Investigation:**

```bash
# Check for SQL injection attempts
grep -E "(UNION SELECT|'; DROP|1=1)" /var/log/nginx/access.log

# Verify API authentication
psql $DATABASE_URL -c "SELECT * FROM api_key_usage WHERE key_id = '<COMPROMISED_KEY>';"

# Check S3 bucket policies
aws s3api get-bucket-policy --bucket skyyrose-data

# Review IAM access
aws iam get-user --user-name <SUSPECTED_USER>
aws iam list-attached-user-policies --user-name <SUSPECTED_USER>
```

## Remediation

### Step-by-Step Fix Procedures

**1. Close Attack Vector**

```bash
# Patch SQL injection vulnerability
git apply security-patches/sqli-fix.patch
make deploy-hotfix

# Revoke all compromised credentials
python scripts/mass_credential_rotation.py --scope all

# Fix S3 bucket permissions
aws s3api put-bucket-acl --bucket skyyrose-data --acl private

# Update IAM policies
aws iam put-user-policy --user-name <USER> --policy-name MinimumPrivilege --policy-document file://iam-policy.json
```

**2. Encrypt Exposed Data**

```bash
# If unencrypted data was accessed, enable encryption
psql $DATABASE_URL -c "
ALTER TABLE users
ALTER COLUMN email TYPE bytea
USING pgp_sym_encrypt(email::text, '<ENCRYPTION_KEY>');
"

# Enable RDS encryption (requires recreation)
aws rds create-db-instance --db-instance-identifier skyyrose-db-encrypted \
  --storage-encrypted --kms-key-id alias/aws/rds
```

**3. Force Password Resets**

```bash
# Force password reset for ALL affected users
psql $DATABASE_URL -c "
UPDATE users
SET password_reset_required = true,
    password_reset_token = gen_random_uuid(),
    password_reset_expires = NOW() + INTERVAL '7 days',
    password = NULL
WHERE id IN (SELECT id FROM affected_users);
"

# Invalidate all sessions
redis-cli FLUSHDB
```

**4. Notify Payment Processors (if payment data affected)**

```bash
# Contact Stripe
curl -X POST https://api.stripe.com/v1/security/incidents \
  -u "$STRIPE_SECRET_KEY:" \
  -d "description=Data breach affecting payment methods" \
  -d "severity=critical"

# Notify acquiring bank
# Manual process - call immediately
```

**5. Enable Enhanced Monitoring**

```bash
# Enable database query logging
psql $DATABASE_URL -c "ALTER SYSTEM SET log_statement = 'all';"
psql $DATABASE_URL -c "SELECT pg_reload_conf();"

# Enable AWS GuardDuty
aws guardduty create-detector --enable

# Deploy SIEM agent
ansible-playbook playbooks/deploy-siem-agent.yml
```

### Verification Steps

```bash
# 1. Verify attack vector is closed
python security/vulnerability-scanner.py --target https://api.skyyrose.com

# 2. Verify all compromised credentials revoked
psql $DATABASE_URL -c "SELECT COUNT(*) FROM api_keys WHERE revoked = false AND created_at < '<BREACH_TIME>';"
# Should be 0

# 3. Verify encryption enabled
psql $DATABASE_URL -c "SELECT pg_typeof(email) FROM users LIMIT 1;"
# Should return 'bytea'

# 4. Verify sessions invalidated
redis-cli KEYS "session:*" | wc -l
# Should be 0 immediately after reset

# 5. Verify monitoring enabled
aws guardduty get-detector --detector-id <DETECTOR_ID>
# Should show "Status": "ENABLED"
```

## Recovery

### Service Restoration Process

**Phase 1: Internal Systems (0-4 hours)**

1. Restore database from pre-breach backup (if data modified)
2. Deploy security patches
3. Verify all attack vectors closed
4. Re-enable database access with new credentials
5. Restart application servers

**Phase 2: User Access (4-24 hours)**

1. Begin user notification process
2. Enable password reset portal
3. Provide user support via dedicated hotline
4. Monitor for account takeover attempts

**Phase 3: Full Restoration (24-72 hours)**

1. Complete user password resets
2. Re-enable all services
3. Restore normal monitoring levels
4. Conduct security audit
5. Resume normal operations

### Monitoring During Recovery

```bash
# Monitor password reset activity
watch -n 60 "psql $DATABASE_URL -c \"SELECT COUNT(*) FROM users WHERE password_reset_required = true;\""

# Monitor support ticket volume
watch -n 300 "psql $DATABASE_URL -c \"SELECT COUNT(*) FROM support_tickets WHERE created_at > NOW() - INTERVAL '1 hour';\""

# Monitor for follow-up attacks
tail -f /var/log/skyyrose/security.log | grep -E "(unauthorized|breach|attack)"
```

### Communication Plan

**Legal & Regulatory (IMMEDIATE):**

1. Notify Legal Counsel within 1 hour
2. Prepare regulatory notifications (GDPR, HIPAA, PCI DSS)
3. File breach reports with supervisory authorities
4. Notify law enforcement (FBI IC3) if criminal activity

**Customer Notification (within 72 hours):**

```
Subject: Important Security Notice Regarding Your SkyyRose Account

Dear [Customer Name],

We are writing to inform you of a data security incident that may have affected your personal information.

WHAT HAPPENED:
On [DATE], we discovered unauthorized access to our systems that resulted in exposure of customer data. We immediately launched an investigation and took steps to secure our systems.

WHAT INFORMATION WAS INVOLVED:
[Specific data types: name, email, address, payment information, etc.]

WHAT WE ARE DOING:
- Secured our systems and closed the vulnerability
- Launched a forensic investigation
- Notified law enforcement and regulatory authorities
- Enhanced our security measures
- Offering [12 months of free credit monitoring]

WHAT YOU SHOULD DO:
1. Reset your password immediately: [LINK]
2. Enable two-factor authentication
3. Monitor your credit reports and account statements
4. Watch for phishing attempts
5. Enroll in free credit monitoring: [LINK]

We take this matter extremely seriously and sincerely apologize for this incident. We are committed to protecting your information and have implemented additional safeguards to prevent future incidents.

For questions, please contact our dedicated support line:
Phone: 1-800-XXX-XXXX
Email: databreach@skyyrose.com
Hours: 24/7

Sincerely,
[CEO Name]
CEO, SkyyRose

ADDITIONAL RESOURCES:
- FTC Identity Theft: identitytheft.gov
- Credit Bureau Contact Info: [LINKS]
- State Attorney General: [LINK]
```

**Public Statement (if publicly disclosed):**
Work with PR team and legal counsel. Key points:

- Acknowledge the breach transparently
- Explain what happened (without technical details that could aid attackers)
- Detail steps taken to secure systems
- Explain what customers should do
- Demonstrate commitment to security

**Internal Communication:**

```
ALL HANDS MEETING - MANDATORY

Subject: Data Breach - All Staff Briefing

All staff must attend emergency meeting:
Date: [TODAY]
Time: [ASAP]
Location: Main Conference Room / Zoom

Agenda:
- Breach overview (CTO)
- Legal implications (General Counsel)
- Customer support procedures (Support Lead)
- Q&A

DO NOT discuss this incident on social media or with press.
All media inquiries must be directed to PR@skyyrose.com.
```

## Post-Mortem

### Critical Metrics

- Total records exposed: [NUMBER]
- Data types compromised: [LIST]
- Customers affected: [NUMBER]
- Time from breach to detection: [HOURS/DAYS]
- Time from detection to containment: [HOURS]
- Estimated financial impact: $[AMOUNT]
- Regulatory fines: $[AMOUNT]
- Remediation costs: $[AMOUNT]

### Regulatory Compliance Checklist

**GDPR (if EU customers affected):**

- [ ] Notify supervisory authority within 72 hours
- [ ] Document breach in internal records
- [ ] Notify affected individuals "without undue delay"
- [ ] Assess need for Data Protection Impact Assessment (DPIA)

**HIPAA (if health data affected):**

- [ ] Notify HHS within 60 days (if > 500 individuals)
- [ ] Notify affected individuals within 60 days
- [ ] Notify media (if > 500 individuals in same state/jurisdiction)

**PCI DSS (if payment data affected):**

- [ ] Notify payment brands immediately
- [ ] Notify acquiring bank
- [ ] Engage PCI Forensic Investigator (PFI)
- [ ] Prepare for potential compliance audit

**State Laws (e.g., California CCPA):**

- [ ] Notify California Attorney General (if > 500 CA residents)
- [ ] Notify affected individuals "without unreasonable delay"

### Preventive Measures

- [ ] Implement database activity monitoring (DAM)
- [ ] Enable row-level security (RLS) in PostgreSQL
- [ ] Deploy data loss prevention (DLP) solution
- [ ] Implement data classification and tagging
- [ ] Enable encryption at rest and in transit
- [ ] Deploy runtime application self-protection (RASP)
- [ ] Conduct regular penetration testing
- [ ] Implement zero-trust network architecture
- [ ] Enable multi-factor authentication (MFA) for all access
- [ ] Conduct employee security awareness training
- [ ] Implement privileged access management (PAM)
- [ ] Deploy security information and event management (SIEM)
- [ ] Establish data retention and disposal policies
- [ ] Conduct vendor security assessments
- [ ] Implement incident response drills (tabletop exercises)

### Legal Follow-Up Actions

- [ ] Retain forensic investigation firm
- [ ] Retain breach notification service
- [ ] Obtain cyber insurance claim
- [ ] Prepare for class action lawsuits
- [ ] Engage external legal counsel
- [ ] Prepare for regulatory audits
- [ ] Document all remediation efforts

## Contact Information

### Internal Emergency Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| Security Lead | [NAME] | [PHONE] | <security-lead@skyyrose.com> |
| CTO | [NAME] | [PHONE] | <cto@skyyrose.com> |
| CEO | [NAME] | [PHONE] | <ceo@skyyrose.com> |
| General Counsel | [NAME] | [PHONE] | <legal@skyyrose.com> |
| PR Director | [NAME] | [PHONE] | <pr@skyyrose.com> |

### External Emergency Contacts

| Organization | Purpose | Contact |
|--------------|---------|---------|
| FBI Cyber Division | Report criminal activity | IC3.gov, [LOCAL FIELD OFFICE] |
| Mandiant/CrowdStrike | Forensic investigation | [CONTACT] |
| Experian/Equifax | Credit monitoring services | [CONTACT] |
| Cyber Insurance | File claim | [POLICY NUMBER], [PHONE] |
| External Legal Counsel | Regulatory compliance | [LAW FIRM], [PHONE] |

### Regulatory Authorities

| Authority | Jurisdiction | Contact |
|-----------|--------------|---------|
| EU DPA | GDPR | <https://edpb.europa.eu/about-edpb/board/members_en> |
| HHS OCR | HIPAA | <https://ocrportal.hhs.gov/ocr/breach/wizard_breach.jsf> |
| State Attorney General | State breach laws | [STATE-SPECIFIC] |
| FTC | Consumer protection | <https://www.ftccomplaintassistant.gov> |

## Slack Notification Template

```
:rotating_light::rotating_light: **CRITICAL - DATA BREACH DETECTED** :rotating_light::rotating_light:

@channel @here

**Incident ID**: INC-BREACH-YYYYMMDD-HHmm
**Severity**: CRITICAL
**Status**: ACTIVE INCIDENT

**Breach Details**:
- Data Accessed: [PII/Payment/Health/Other]
- Records Affected: [ESTIMATED COUNT]
- Breach Window: [START TIME] to [END TIME]
- Attack Vector: [SQL Injection/Compromised Creds/Other]

**IMMEDIATE ACTIONS TAKEN**:
- Systems isolated
- Attack vector closed
- Law enforcement notified
- Legal counsel engaged

**WAR ROOM**: #incident-breach-YYYYMMDD
**CONFERENCE BRIDGE**: [ZOOM LINK]

**ALL HANDS MEETING**: [TIME] - ATTENDANCE MANDATORY

**CRITICAL**: Do NOT discuss publicly. All media inquiries to PR@skyyrose.com.

**Incident Commander**: @security-lead
**Legal Lead**: @general-counsel
**Technical Lead**: @cto

**Next Update**: Every 30 minutes
```

## Related Runbooks

- [Security Incident Response Master Procedure](/Users/coreyfoster/DevSkyy/docs/runbooks/security-incident-response.md)
- [SQL Injection](/Users/coreyfoster/DevSkyy/docs/runbooks/sql-injection.md)
- [Authentication Bypass](/Users/coreyfoster/DevSkyy/docs/runbooks/authentication-bypass.md)
- [API Key Leak](/Users/coreyfoster/DevSkyy/docs/runbooks/api-key-leak.md)
