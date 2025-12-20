# API Key Leak Response

**Severity Level**: CRITICAL
**Last Updated**: 2025-12-19
**Owner**: Security Operations Team
**Related**: [Security Incident Response Master Procedure](/Users/coreyfoster/DevSkyy/docs/runbooks/security-incident-response.md)

## Overview

API key leaks occur when credentials are exposed in public repositories, logs, error messages, or intercepted in transit. This runbook covers immediate key revocation, credential rotation, and preventing future leaks.

## Detection

### Alert Triggers

**Automated Alerts:**

- GitHub secret scanning alerts
- GitGuardian detections
- TruffleHog findings
- Pre-commit hook violations
- API key usage from unexpected IP addresses
- API key usage spike (> 1000x normal)
- API calls from blacklisted user agents
- HaveIBeenPwned credential exposure notifications

**Manual Detection:**

- Security researcher disclosure
- Customer reports of unauthorized API usage
- Unusual billing charges
- Third-party vulnerability reports

### How to Identify

1. **GitHub Secret Scanning**

   ```bash
   # Check GitHub secret scanning alerts
   gh api /repos/skyyrose/backend/secret-scanning/alerts | jq .

   # Search public repositories for exposed keys
   python scripts/github_secret_scanner.py \
     --org skyyrose \
     --keywords "SKYYROSE_API_KEY,sk_live_,sk_test_"
   ```

2. **Scan Git History**

   ```bash
   # Use trufflehog to scan entire git history
   docker run --rm -v $(pwd):/repo trufflesecurity/trufflehog:latest \
     git file:///repo --since-commit HEAD~100 --json

   # Use gitleaks
   gitleaks detect --source . --verbose --report-path gitleaks-report.json

   # Search for common secret patterns
   git grep -E "(api[_-]?key|secret|password|token)" $(git rev-list --all)
   ```

3. **Check Application Logs**

   ```bash
   # Search for API keys in logs (should never happen!)
   grep -rE "sk_live_[a-zA-Z0-9]{32}" /var/log/skyyrose/

   # Check error logs for accidental exposure
   grep -i "api.key\|apikey" /var/log/nginx/error.log

   # Check for keys in exception messages
   grep -E "(Exception|Error).*[a-zA-Z0-9]{32}" /var/log/skyyrose/api.log
   ```

4. **Monitor API Usage**

   ```bash
   # Check for unusual API key usage patterns
   psql $DATABASE_URL -c "
   SELECT
     api_key_id,
     COUNT(*) as request_count,
     COUNT(DISTINCT ip_address) as unique_ips,
     array_agg(DISTINCT ip_address) as ips,
     MIN(created_at) as first_request,
     MAX(created_at) as last_request
   FROM api_requests
   WHERE created_at > NOW() - INTERVAL '24 hours'
   GROUP BY api_key_id
   HAVING COUNT(*) > 10000 OR COUNT(DISTINCT ip_address) > 10
   ORDER BY request_count DESC;
   "

   # Check for keys used from suspicious locations
   psql $DATABASE_URL -c "
   SELECT
     ak.key_prefix,
     ak.user_id,
     ar.ip_address,
     ar.country,
     COUNT(*) as requests
   FROM api_requests ar
   JOIN api_keys ak ON ar.api_key_id = ak.id
   WHERE ar.country NOT IN ('US', 'CA', 'GB')  -- Expected countries
     AND ar.created_at > NOW() - INTERVAL '24 hours'
   GROUP BY ak.key_prefix, ak.user_id, ar.ip_address, ar.country;
   "
   ```

5. **Check Public Paste Sites**

   ```bash
   # Monitor Pastebin
   python scripts/pastebin_monitor.py --keywords "skyyrose,sk_live_"

   # Check Gist
   gh gist list --public | grep -i "skyyrose\|api.key"
   ```

## Triage

### Severity Assessment

**CRITICAL - Immediate Action Required:**

- Production API keys exposed in public repository
- Payment gateway keys (Stripe, PayPal) leaked
- Database credentials exposed
- Admin/root API keys compromised
- Keys already being used maliciously
- AWS/Cloud provider credentials leaked

**HIGH - Urgent Response (< 1 hour):**

- Development/staging keys exposed (but production safe)
- Read-only API keys leaked
- Third-party service keys (non-financial)
- Keys exposed but not yet used
- Keys in private repository but accessible to untrusted users

**MEDIUM - Response within 4 hours:**

- Deprecated/unused keys found in old commits
- Test keys with no production access
- Keys with very limited scope/permissions

### Initial Containment Steps

**IMMEDIATE ACTIONS (within 5 minutes):**

1. **Revoke Compromised Keys**

   ```bash
   # Revoke API key immediately
   python scripts/revoke_api_key.py --key-prefix "sk_live_abc123"

   # Database update
   psql $DATABASE_URL -c "
   UPDATE api_keys
   SET revoked = true,
       revoked_at = NOW(),
       revoked_reason = 'Key leaked in GitHub commit abc123',
       revoked_by = 'security-team'
   WHERE key_hash = '<KEY_HASH>';
   "

   # Invalidate all active sessions using this key
   redis-cli KEYS "session:apikey:sk_live_abc123*" | xargs redis-cli DEL
   ```

2. **Block Unauthorized Usage**

   ```bash
   # Get IPs that used the compromised key
   psql $DATABASE_URL -c "
   SELECT DISTINCT ip_address
   FROM api_requests
   WHERE api_key_id = '<COMPROMISED_KEY_ID>'
     AND created_at > NOW() - INTERVAL '24 hours';
   " | tail -n +3 > /tmp/unauthorized_ips.txt

   # Block all IPs
   while read ip; do
     ufw deny from $ip
     echo "deny $ip;" >> /etc/nginx/conf.d/blocked-ips.conf
   done < /tmp/unauthorized_ips.txt

   nginx -s reload
   ```

3. **Rotate Related Credentials**

   ```bash
   # If database credentials leaked, rotate immediately
   # Generate new password
   NEW_DB_PASSWORD=$(openssl rand -base64 32)

   # Update PostgreSQL user
   psql $DATABASE_URL -c "ALTER USER skyyrose_api PASSWORD '$NEW_DB_PASSWORD';"

   # Update application configuration
   # (Requires deployment)

   # If AWS keys leaked
   aws iam delete-access-key \
     --access-key-id <COMPROMISED_KEY> \
     --user-name skyyrose-api

   aws iam create-access-key \
     --user-name skyyrose-api
   ```

4. **Remove from Source**

   ```bash
   # If key is in current branch
   git rm .env
   echo ".env" >> .gitignore
   git add .gitignore
   git commit -m "Remove exposed credentials and update gitignore"

   # If key is in git history, use BFG Repo-Cleaner
   bfg --replace-text secrets.txt --no-blob-protection
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive

   # Force push (coordinate with team!)
   git push --force --all
   ```

### Escalation Procedures

**CRITICAL Leaks:**

1. **Call** Security Lead immediately: [PHONE]
2. **Call** CTO: [PHONE]
3. **Notify** affected service providers (Stripe, AWS, etc.)
4. **Create** incident war room: `#incident-keyleak-YYYYMMDD`
5. **Notify** Legal (if customer data accessed)

**HIGH Severity:**

1. Post in `#security-alerts` channel
2. Notify Security Lead via Slack
3. Create incident ticket
4. Coordinate key rotation

## Investigation

### Forensic Analysis

1. **Determine Exposure Timeline**

   ```bash
   # Find when key was first committed
   git log -S "sk_live_abc123" --all --source --full-history

   # Check if commit was pushed to remote
   git log origin/main --grep="<COMMIT_HASH>"

   # Estimate public exposure duration
   # Commit date to revocation time

   # Check GitHub to see if commit is public
   gh api /repos/skyyrose/backend/commits/<COMMIT_HASH>
   ```

2. **Analyze Unauthorized Usage**

   ```bash
   # Get complete audit trail
   psql $DATABASE_URL -c "
   SELECT
     created_at,
     ip_address,
     endpoint,
     http_method,
     status_code,
     response_time_ms,
     user_agent,
     country,
     request_body_hash
   FROM api_requests
   WHERE api_key_id = '<COMPROMISED_KEY_ID>'
   ORDER BY created_at;
   " > /forensics/compromised-key-usage.csv

   # Identify what data was accessed
   psql $DATABASE_URL -c "
   SELECT
     endpoint,
     COUNT(*) as request_count,
     COUNT(DISTINCT ip_address) as unique_ips
   FROM api_requests
   WHERE api_key_id = '<COMPROMISED_KEY_ID>'
     AND status_code = 200
   GROUP BY endpoint
   ORDER BY request_count DESC;
   "

   # Check if sensitive data was accessed
   psql $DATABASE_URL -c "
   SELECT COUNT(*)
   FROM api_requests
   WHERE api_key_id = '<COMPROMISED_KEY_ID>'
     AND endpoint IN ('/api/users', '/api/orders', '/api/payment-methods')
     AND status_code = 200;
   "
   ```

3. **Check for Data Exfiltration**

   ```bash
   # Check for large data exports
   psql $DATABASE_URL -c "
   SELECT
     created_at,
     endpoint,
     ip_address,
     response_size_bytes
   FROM api_requests
   WHERE api_key_id = '<COMPROMISED_KEY_ID>'
     AND response_size_bytes > 1000000  -- 1MB
   ORDER BY response_size_bytes DESC;
   "

   # Check application logs for data access
   grep "api_key_id: <COMPROMISED_KEY_ID>" /var/log/skyyrose/api.log | \
   grep -E "(users|orders|payment)" > /forensics/sensitive-access.log
   ```

4. **Determine Impact**

   ```bash
   # Count affected users
   psql $DATABASE_URL -c "
   SELECT COUNT(DISTINCT user_id)
   FROM api_requests
   WHERE api_key_id = '<COMPROMISED_KEY_ID>'
     AND endpoint LIKE '%/users/%'
     AND status_code = 200;
   "

   # Check for financial impact
   psql $DATABASE_URL -c "
   SELECT
     SUM(amount) as total_unauthorized_charges,
     COUNT(*) as transaction_count
   FROM transactions
   WHERE api_key_id = '<COMPROMISED_KEY_ID>'
     AND created_at > '<LEAK_TIME>';
   "
   ```

### Data Collection Checklist

- [ ] When key was created
- [ ] When key was leaked (committed to git)
- [ ] When leak was discovered
- [ ] Exposure duration (leak to revocation)
- [ ] Key permissions and scope
- [ ] All IPs that used the key
- [ ] All endpoints accessed
- [ ] Data accessed/exfiltrated
- [ ] Unauthorized transactions (if any)
- [ ] Affected users/customers
- [ ] How the leak was discovered
- [ ] Git commit history

### Root Cause Analysis

**Why did the leak occur?**

1. **Developer Error**: Hardcoded credentials
2. **No Pre-Commit Hooks**: Secrets not caught before commit
3. **Inadequate Training**: Developers not aware of security practices
4. **No Secret Management**: Using .env files instead of vault
5. **Code Review Failure**: Reviewers didn't catch the secret
6. **CI/CD Misconfiguration**: Secrets exposed in build logs

```bash
# Check if pre-commit hooks are installed
git config --get core.hooksPath

# Check if secret scanning is enabled
gh api /repos/skyyrose/backend/secret-scanning | jq .status

# Review developer onboarding checklist
cat docs/DEVELOPER_ONBOARDING.md | grep -i "secret\|credential"
```

## Remediation

### Step-by-Step Fix Procedures

**1. Generate New API Keys**

```bash
# Generate new API key for user
python scripts/generate_api_key.py \
  --user-id <USER_ID> \
  --scope "read,write" \
  --description "Replacement for leaked key"

# Generate new service credentials
python scripts/rotate_service_credentials.py \
  --service stripe \
  --environment production
```

**2. Update Application Configuration**

```bash
# Update secrets in AWS Secrets Manager
aws secretsmanager update-secret \
  --secret-id skyyrose/api/stripe-key \
  --secret-string "sk_live_NEW_KEY_HERE"

# Update secrets in Kubernetes
kubectl create secret generic api-keys \
  --from-literal=stripe-key=sk_live_NEW_KEY_HERE \
  --dry-run=client -o yaml | kubectl apply -f -

# Trigger rolling deployment to pick up new secrets
kubectl rollout restart deployment/skyyrose-api
```

**3. Install Secret Scanning**

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Add secret detection
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
EOF

pre-commit run --all-files
```

**4. Enable GitHub Secret Scanning**

```bash
# Enable secret scanning (requires admin access)
gh api --method PATCH /repos/skyyrose/backend \
  --field security_and_analysis[secret_scanning][status]=enabled \
  --field security_and_analysis[secret_scanning_push_protection][status]=enabled

# Add custom patterns
gh api --method PUT /orgs/skyyrose/secret-scanning/custom-patterns \
  --field name="SkyyRose API Key" \
  --field regex="sk_live_[a-zA-Z0-9]{32}"
```

**5. Implement Secret Management**

```python
# Replace hardcoded secrets with vault access
# Before:
STRIPE_KEY = "sk_live_abc123..."

# After:
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name='us-east-1'
    )
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except ClientError as e:
        raise e

STRIPE_KEY = get_secret('skyyrose/api/stripe-key')
```

**6. Audit All Credentials**

```bash
# List all API keys and check creation dates
psql $DATABASE_URL -c "
SELECT
  id,
  user_id,
  key_prefix,
  created_at,
  last_used_at,
  scope
FROM api_keys
WHERE revoked = false
ORDER BY created_at DESC;
"

# Rotate all keys created before the leak
python scripts/mass_key_rotation.py \
  --created-before "2025-12-19" \
  --notify-users
```

**7. Clean Git History**

```bash
# Use BFG Repo-Cleaner to remove secrets from history
# Backup repository first!
git clone --mirror git@github.com:skyyrose/backend.git

# Create file with secrets to remove
cat > secrets.txt << EOF
sk_live_OLD_KEY_1
sk_live_OLD_KEY_2
DB_PASSWORD=oldpassword
EOF

# Remove secrets
bfg --replace-text secrets.txt backend.git

# Clean up
cd backend.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (WARNING: coordinate with team!)
git push
```

### Verification Steps

```bash
# 1. Verify old key is revoked
psql $DATABASE_URL -c "
SELECT revoked, revoked_at
FROM api_keys
WHERE key_prefix = 'sk_live_abc123';
"
# Should show revoked = true

# 2. Test old key returns 401
curl -X GET https://api.skyyrose.com/v1/products \
  -H "Authorization: Bearer sk_live_OLD_KEY"
# Should return 401 Unauthorized

# 3. Verify new key works
curl -X GET https://api.skyyrose.com/v1/products \
  -H "Authorization: Bearer sk_live_NEW_KEY"
# Should return 200 OK

# 4. Verify pre-commit hooks active
echo "sk_live_test123" > test.txt
git add test.txt
git commit -m "test"
# Should be blocked by pre-commit hook

# 5. Verify secrets removed from git history
git log --all --source --full-history -S "sk_live_OLD_KEY"
# Should return no results

# 6. Verify GitHub secret scanning enabled
gh api /repos/skyyrose/backend/secret-scanning | jq .status
# Should return "enabled"
```

## Recovery

### Service Restoration Process

**Phase 1: Immediate Key Rotation (0-1 hour)**

1. Revoke compromised keys
2. Generate new keys
3. Update secrets in secret manager
4. Deploy applications with new keys
5. Verify services operational

**Phase 2: Security Hardening (1-24 hours)**

1. Install secret scanning tools
2. Enable GitHub protections
3. Audit all credentials
4. Implement secret management
5. Update developer documentation

**Phase 3: User Notification (24-72 hours)**

1. Notify affected users of new API keys
2. Provide key rotation instructions
3. Update API documentation
4. Schedule security training

### Monitoring During Recovery

```bash
# Monitor API key usage
watch -n 30 "psql $DATABASE_URL -c \"
SELECT
  key_prefix,
  COUNT(*) as requests_last_5min
FROM api_requests
WHERE created_at > NOW() - INTERVAL '5 minutes'
GROUP BY key_prefix
ORDER BY requests_last_5min DESC
LIMIT 10;
\""

# Monitor for continued use of old keys
watch -n 60 "psql $DATABASE_URL -c \"
SELECT COUNT(*)
FROM api_requests
WHERE api_key_id IN (
  SELECT id FROM api_keys WHERE revoked = true
)
AND created_at > NOW() - INTERVAL '5 minutes';
\""

# Monitor application errors
tail -f /var/log/skyyrose/api.log | grep -i "authentication\|unauthorized"
```

### Communication Plan

**Internal Communication:**

```
#security-alerts

:key: **API Key Leak Resolved**

**Incident**: Production Stripe API key found in public GitHub commit
**Status**: RESOLVED
**Actions Taken**:
- Old key revoked at [TIME]
- New key generated and deployed
- All affected systems updated
- Pre-commit hooks installed
- Git history cleaned

**Impact**: No unauthorized usage detected
**Affected Services**: None (caught before exploitation)

**Follow-up**:
- Security training scheduled for [DATE]
- All developers to install pre-commit hooks by EOD
- Mandatory code review for .env changes

**Incident Commander**: @security-lead
```

**User Notification (if customer API keys affected):**

```
Subject: Important: API Key Security Update

Dear [Customer],

We are writing to inform you that we have rotated your API key as a security precaution.

What Happened:
During a routine security audit, we discovered that API keys may have been temporarily exposed. Out of an abundance of caution, we have proactively rotated all affected keys.

Action Required:
Please update your application to use the new API key:

Old Key: sk_live_abc123... (REVOKED)
New Key: sk_live_xyz789... (view in dashboard)

Get your new key: https://dashboard.skyyrose.com/settings/api-keys

Timeline:
- Your old key will stop working on [DATE]
- Please update by [DATE] to avoid service interruption

We apologize for any inconvenience. This precautionary measure ensures the security of your account and data.

Questions? Contact: security@skyyrose.com

Best regards,
SkyyRose Security Team
```

## Post-Mortem

### Key Metrics

- Time to detection: [X hours/days]
- Time to revocation: [X minutes]
- Exposure duration: [X hours/days]
- Number of compromised keys: [X]
- Unauthorized API calls: [X]
- Affected users: [X]
- Financial impact: $[X]

### Preventive Measures

**Immediate (within 7 days):**

- [ ] Install pre-commit hooks on all developer machines
- [ ] Enable GitHub secret scanning and push protection
- [ ] Rotate all existing API keys
- [ ] Implement secret management (AWS Secrets Manager/Vault)
- [ ] Update .gitignore to exclude all credential files
- [ ] Clean git history of all secrets

**Short-term (within 30 days):**

- [ ] Deploy automated secret scanning in CI/CD
- [ ] Implement API key rotation policy (90-day max)
- [ ] Add API key usage monitoring and alerting
- [ ] Create developer security training program
- [ ] Implement least-privilege API key scopes
- [ ] Add API key IP allowlisting

**Long-term (within 90 days):**

- [ ] Migrate to short-lived tokens (OAuth 2.0)
- [ ] Implement key management service (KMS)
- [ ] Deploy runtime secret detection
- [ ] Conduct regular security audits
- [ ] Implement automated key rotation
- [ ] Create incident response drill for key leaks

### Code Review Checklist Update

Add to `docs/CODE_REVIEW_CHECKLIST.md`:

```markdown
## Security Review
- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] All sensitive config in environment variables
- [ ] .env files in .gitignore
- [ ] No secrets in error messages or logs
- [ ] API keys have appropriate scope/permissions
- [ ] Credentials retrieved from secret manager
```

## Contact Information

### Incident Response Team

| Role | Contact | Email |
|------|---------|-------|
| Security Lead | @security-lead | <security-lead@skyyrose.com> |
| DevOps Lead | @devops-lead | <devops@skyyrose.com> |
| CTO | @cto | <cto@skyyrose.com> |

### External Services

| Service | Purpose | Contact |
|---------|---------|---------|
| GitHub Support | Secret scanning issues | support.github.com |
| AWS Support | Secrets Manager, IAM | AWS Console Support |
| Stripe Support | Payment key rotation | support.stripe.com |

## Slack Notification Template

```
:rotating_light: **API KEY LEAK DETECTED** :rotating_light:

**Incident ID**: INC-KEYLEAK-YYYYMMDD-HHmm
**Severity**: CRITICAL
**Status**: MITIGATING

**Leak Details**:
- Key Type: [Stripe API Key / AWS Access Key / etc.]
- Location: [GitHub commit abc123 / logs / etc.]
- Exposure: [Public / Private repo / etc.]
- Discovered: [How it was found]

**IMMEDIATE ACTIONS TAKEN**:
- Key revoked at [TIME]
- Unauthorized IPs blocked: [COUNT]
- New key generated and deployed
- Services verified operational

**Impact Assessment**:
- Unauthorized Usage: [YES/NO]
- Data Accessed: [NONE / PII / etc.]
- Financial Impact: $[AMOUNT]

**Incident Commander**: @security-lead
**War Room**: #incident-keyleak-YYYYMMDD

**Next Steps**:
- Git history cleanup in progress
- Pre-commit hooks deployment
- User notifications (if needed)

**Next Update**: [TIME]
```

## Related Runbooks

- [Security Incident Response Master Procedure](/Users/coreyfoster/DevSkyy/docs/runbooks/security-incident-response.md)
- [Data Breach](/Users/coreyfoster/DevSkyy/docs/runbooks/data-breach.md)
- [Authentication Bypass](/Users/coreyfoster/DevSkyy/docs/runbooks/authentication-bypass.md)
