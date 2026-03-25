# Key Rotation Guide

**Automatic rotation of encryption and JWT keys for DevSkyy platform**

## Overview

DevSkyy uses two critical security keys:
- **ENCRYPTION_MASTER_KEY** (256-bit): For AES-256-GCM encryption of sensitive data
- **JWT_SECRET_KEY** (512-bit): For signing and verifying JWT authentication tokens

These keys MUST be rotated regularly to maintain security.

## Rotation Schedule

| Environment | Rotation Frequency | Automated |
|-------------|-------------------|-----------|
| Development | Every 90 days | Manual |
| Staging | Every 60 days | Recommended |
| Production | Every 30 days | **REQUIRED** |

## Manual Rotation

### Quick Start

```bash
# 1. Dry run to preview changes
python scripts/security/rotate_keys.py --dry-run

# 2. Actually rotate the keys
python scripts/security/rotate_keys.py

# 3. Restart services
docker-compose restart app worker

# 4. Verify services are healthy
curl http://localhost:8000/health
```

### Step-by-Step Process

1. **Backup Current State**
   ```bash
   # Automatic backup is created by script
   # Manual backup (optional):
   cp .env .env.backup.$(date +%Y%m%d)
   ```

2. **Rotate Keys**
   ```bash
   python scripts/security/rotate_keys.py
   ```

3. **Update Production Secrets** (if deploying to cloud)
   ```bash
   # AWS Secrets Manager
   aws secretsmanager update-secret \
     --secret-id devskyy/encryption-key \
     --secret-string "$(grep ENCRYPTION_MASTER_KEY .env | cut -d= -f2)"

   aws secretsmanager update-secret \
     --secret-id devskyy/jwt-secret \
     --secret-string "$(grep JWT_SECRET_KEY .env | cut -d= -f2)"

   # Vercel (for frontend)
   vercel env add ENCRYPTION_MASTER_KEY < .env
   vercel env add JWT_SECRET_KEY < .env
   ```

4. **Restart All Services**
   ```bash
   # Docker Compose
   docker-compose down
   docker-compose up -d

   # Kubernetes
   kubectl rollout restart deployment/devskyy-app
   kubectl rollout restart deployment/devskyy-worker

   # Systemd
   sudo systemctl restart devskyy-app
   sudo systemctl restart devskyy-worker
   ```

5. **Verify Health**
   ```bash
   # Check health endpoints
   curl http://localhost:8000/health
   curl http://localhost:8000/health/ready

   # Check logs for errors
   docker-compose logs app | grep -i error
   docker-compose logs worker | grep -i error
   ```

6. **Invalidate Old JWT Tokens**
   ```sql
   -- All users must re-login after JWT rotation
   -- Optional: Clear active sessions table
   DELETE FROM active_sessions WHERE created_at < NOW();
   ```

## Automated Rotation (Recommended for Production)

### Using GitHub Actions

Create `.github/workflows/rotate-keys.yml`:

```yaml
name: Rotate Security Keys

on:
  schedule:
    # Run on 1st of every month at 2 AM UTC
    - cron: '0 2 1 * *'
  workflow_dispatch:  # Allow manual trigger

jobs:
  rotate-keys:
    runs-on: ubuntu-latest
    env:
      ENVIRONMENT: production

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Rotate Keys (Dry Run)
        run: |
          python scripts/security/rotate_keys.py --dry-run

      - name: Rotate Keys (Live)
        if: github.event_name == 'schedule'
        run: |
          python scripts/security/rotate_keys.py

      - name: Upload Backup
        uses: actions/upload-artifact@v3
        with:
          name: key-backup-${{ github.run_number }}
          path: secrets/key_backups/
          retention-days: 90

      - name: Update Cloud Secrets
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          # Extract new keys
          ENCRYPTION_KEY=$(grep ENCRYPTION_MASTER_KEY .env | cut -d= -f2)
          JWT_SECRET=$(grep JWT_SECRET_KEY .env | cut -d= -f2)

          # Update AWS Secrets Manager
          aws secretsmanager update-secret \
            --secret-id devskyy/encryption-key \
            --secret-string "$ENCRYPTION_KEY"

          aws secretsmanager update-secret \
            --secret-id devskyy/jwt-secret \
            --secret-string "$JWT_SECRET"

      - name: Trigger Deployment
        run: |
          # Trigger rolling update to pick up new secrets
          kubectl rollout restart deployment/devskyy-app
          kubectl rollout restart deployment/devskyy-worker

      - name: Notify Team
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: '🔐 Security keys rotated successfully'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Using Cron Job

```bash
# Add to crontab (runs 1st of every month at 2 AM)
0 2 1 * * cd /path/to/devskyy && python scripts/security/rotate_keys.py && docker-compose restart app worker
```

### Using AWS Lambda + EventBridge

```python
# lambda_function.py
import boto3
import secrets

def lambda_handler(event, context):
    """Rotate keys monthly via Lambda."""
    ssm = boto3.client('secretsmanager')
    ecs = boto3.client('ecs')

    # Generate new keys
    encryption_key = secrets.token_hex(32)
    jwt_secret = secrets.token_urlsafe(64)

    # Update secrets
    ssm.update_secret(
        SecretId='devskyy/encryption-key',
        SecretString=encryption_key
    )
    ssm.update_secret(
        SecretId='devskyy/jwt-secret',
        SecretString=jwt_secret
    )

    # Force service restart
    ecs.update_service(
        cluster='devskyy-cluster',
        service='devskyy-app',
        forceNewDeployment=True
    )

    return {'statusCode': 200, 'body': 'Keys rotated'}
```

## Rollback Procedure

If rotation causes issues:

```bash
# 1. Stop services
docker-compose down

# 2. Restore backup
cp secrets/key_backups/.env.backup.YYYYMMDD_HHMMSS .env

# 3. Restart services
docker-compose up -d

# 4. Verify
curl http://localhost:8000/health
```

## Monitoring

### Key Rotation Metrics

Track in Prometheus:
```python
# In security/prometheus_exporter.py
KEY_ROTATION_TIMESTAMP = Gauge(
    'devskyy_key_rotation_timestamp',
    'Unix timestamp of last key rotation'
)

KEY_AGE_DAYS = Gauge(
    'devskyy_key_age_days',
    'Days since last key rotation'
)
```

### Alerts

```yaml
# prometheus/alerts.yml
groups:
  - name: security
    rules:
      - alert: KeyRotationOverdue
        expr: devskyy_key_age_days > 35
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Security keys overdue for rotation"
          description: "Keys are {{ $value }} days old. Rotate within 30 days."

      - alert: KeyRotationCritical
        expr: devskyy_key_age_days > 60
        for: 15m
        labels:
          severity: critical
        annotations:
          summary: "Security keys critically overdue"
          description: "Keys are {{ $value }} days old. Immediate rotation required."
```

## Impact Assessment

| Component | Impact | Mitigation |
|-----------|--------|------------|
| Active JWT tokens | Invalidated | Users must re-login |
| Encrypted data | None | Old data decrypted with old key backup |
| Database sessions | Cleared | Session table cleanup recommended |
| API rate limits | Reset | Temporarily relaxed for re-auth surge |
| Stateless services | None | Auto-pickup on restart |

## Security Best Practices

1. **Never commit keys to git**
   - Use `.gitignore` for `.env`
   - Use AWS Secrets Manager / Vault in production

2. **Store backups securely**
   - Encrypt backup files
   - Limit retention to 90 days
   - Restrict access to security team

3. **Test rotation in staging first**
   - Verify zero-downtime deployment
   - Check for authentication errors
   - Validate data encryption/decryption

4. **Audit rotation events**
   - Review `secrets/key_backups/rotation_log.txt`
   - Track who initiated rotation
   - Log access to backup files

5. **Emergency rotation**
   - If keys are compromised, rotate immediately
   - Invalidate all sessions
   - Force password resets if needed

## Troubleshooting

### "Encryption key mismatch" errors

```bash
# Old data was encrypted with previous key
# Keep backups for 90 days to decrypt legacy data
python scripts/security/decrypt_with_backup.py --backup-key <old_key>
```

### "Invalid JWT signature" errors

```bash
# Expected after rotation - users must re-login
# Clear browser cookies and session storage
# Verify JWT_SECRET_KEY loaded correctly:
python -c "import os; print(os.getenv('JWT_SECRET_KEY')[:16])"
```

### Services fail to start

```bash
# Check if .env file is malformed
cat .env | grep -E "ENCRYPTION_MASTER_KEY|JWT_SECRET_KEY"

# Verify key format (hex for encryption, base64 for JWT)
# Restore from backup if needed
```

## References

- [OWASP Key Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html)
- [NIST SP 800-57: Key Management](https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final)
- [AWS Secrets Manager Rotation](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html)
