# DevSkyy Database Backup & Restore Guide

Comprehensive guide for DevSkyy's production-ready database backup and restore system.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Manual Backup](#manual-backup)
- [Automated Backups](#automated-backups)
- [Restore Procedures](#restore-procedures)
- [Docker Integration](#docker-integration)
- [GitHub Actions](#github-actions)
- [Monitoring](#monitoring)
- [Disaster Recovery](#disaster-recovery)
- [Configuration](#configuration)
- [Security](#security)
- [Troubleshooting](#troubleshooting)

## Overview

The DevSkyy backup system provides:

- **Automated daily backups** via GitHub Actions and Docker cron
- **Compression** using gzip for efficient storage
- **Encryption** using GPG for data security
- **S3 upload** for off-site backup storage
- **Backup verification** with integrity checks
- **Monitoring & alerting** for backup health
- **Automated testing** of backup and restore functionality
- **Retention policies** for local and S3 backups

### Features

✓ PostgreSQL 15 native backup using `pg_dump`
✓ Automatic compression (gzip)
✓ Optional GPG encryption
✓ S3 upload for remote storage
✓ Local retention (7 days default)
✓ S3 retention (30 days default)
✓ Automated verification
✓ Health monitoring
✓ Docker containerized
✓ GitHub Actions automation
✓ Comprehensive error logging

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DevSkyy Backup System                     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐          ┌─────▼─────┐        ┌─────▼─────┐
   │  Manual │          │   Docker  │        │  GitHub   │
   │  Backup │          │   Cron    │        │  Actions  │
   └────┬────┘          └─────┬─────┘        └─────┬─────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  backup_database  │
                    │      .sh          │
                    └─────────┬─────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐          ┌─────▼─────┐        ┌─────▼─────┐
   │pg_dump  │          │   gzip    │        │    GPG    │
   │         │──────────►           │────────►           │
   └─────────┘          └───────────┘        └─────┬─────┘
                                                    │
                              ┌─────────────────────┤
                              │                     │
                        ┌─────▼─────┐         ┌─────▼─────┐
                        │   Local   │         │    S3     │
                        │  Storage  │         │  Storage  │
                        └───────────┘         └───────────┘
```

## Quick Start

### Prerequisites

```bash
# Install required tools
sudo apt-get update
sudo apt-get install -y postgresql-client gnupg awscli

# Verify installations
pg_dump --version
gpg --version
aws --version
```

### Environment Setup

Create a `.env` file or export environment variables:

```bash
# Database connection
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=devskyy
export POSTGRES_USER=devskyy
export POSTGRES_PASSWORD=your_password

# Backup configuration
export BACKUP_DIR=/backups/devskyy
export BACKUP_RETENTION_DAYS=7

# Optional: S3 configuration
export S3_BACKUP_BUCKET=my-backup-bucket
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1

# Optional: GPG encryption
export BACKUP_GPG_RECIPIENT=backup@devskyy.com
```

## Manual Backup

### Basic Backup (Local Only)

```bash
# Simple local backup
./scripts/backup_database.sh --local-only

# Backup with verification
./scripts/backup_database.sh --local-only --verify
```

### Production Backup (with S3 and Encryption)

```bash
# Full production backup
./scripts/backup_database.sh --verify

# Backup without encryption
./scripts/backup_database.sh --no-encryption

# Backup without S3 upload
./scripts/backup_database.sh --no-upload
```

### Backup Output

```
================================================================================
DevSkyy Database Backup Summary
================================================================================

Timestamp:          20250116T120000Z
Environment:        production
Database:           devskyy
Host:               localhost:5432

Backup File:        devskyy_backup_20250116T120000Z.sql.gz.gpg
Backup Size:        145M
Backup Location:    /backups/devskyy/devskyy_backup_20250116T120000Z.sql.gz.gpg

Encryption:         true
S3 Upload:          true
Verification:       true

Status:             SUCCESS
================================================================================
```

## Automated Backups

### Docker Cron (Recommended for Production)

The backup container runs automated backups via cron:

```bash
# Start backup container
docker-compose -f docker-compose.yml -f docker-compose.backup.yml up -d backup

# View logs
docker-compose -f docker-compose.backup.yml logs -f backup

# Check backup status
docker-compose -f docker-compose.backup.yml exec backup /scripts/monitor_backups.sh
```

**Default Schedule:**
- Daily backup: 2:00 AM UTC
- Hourly monitoring: Every hour

### GitHub Actions (Recommended for CI/CD)

Automated backups run on:
- **Daily schedule**: 2:00 AM UTC
- **On push to main**: After successful merge
- **Manual trigger**: Via workflow dispatch

```bash
# Manually trigger backup via GitHub CLI
gh workflow run backup.yml

# With custom parameters
gh workflow run backup.yml \
  -f environment=staging \
  -f upload_to_s3=true \
  -f enable_encryption=true
```

## Restore Procedures

### List Available Backups

```bash
# List local backups
ls -lh /backups/devskyy/

# List S3 backups
aws s3 ls s3://my-backup-bucket/production/
```

### Test Restore (Recommended)

**Always test restore to a temporary database first:**

```bash
# Test restore from local file
./scripts/restore_database.sh --test-only devskyy_backup_20250116T120000Z.sql.gz.gpg

# Test restore from S3
./scripts/restore_database.sh --test-only --from-s3 \
  s3://my-backup-bucket/production/2025-01-16/devskyy_backup_20250116T120000Z.sql.gz.gpg
```

### Production Restore

⚠️ **WARNING**: This will replace the current database!

```bash
# Interactive restore (requires confirmation)
./scripts/restore_database.sh devskyy_backup_20250116T120000Z.sql.gz.gpg

# Force restore without confirmation (DANGEROUS)
./scripts/restore_database.sh --force devskyy_backup_20250116T120000Z.sql.gz.gpg

# Restore from S3
./scripts/restore_database.sh --from-s3 \
  s3://my-backup-bucket/production/2025-01-16/devskyy_backup_20250116T120000Z.sql.gz.gpg
```

### Restore Output

```
================================================================================
WARNING: DATABASE RESTORE OPERATION
================================================================================

This operation will REPLACE the current database with the backup:

    Database:       devskyy
    Host:           localhost:5432
    Backup Source:  devskyy_backup_20250116T120000Z.sql.gz.gpg
    Environment:    production

ALL CURRENT DATA IN devskyy WILL BE LOST!

================================================================================

Are you sure you want to continue? (type 'yes' to confirm):
```

## Docker Integration

### Build Backup Container

```bash
# Build backup image
docker build -f Dockerfile.backup -t devskyy-backup:latest .

# Build with docker-compose
docker-compose -f docker-compose.backup.yml build
```

### Run Backup Container

```bash
# Start backup service
docker-compose -f docker-compose.yml -f docker-compose.backup.yml up -d

# Run one-time backup
docker-compose -f docker-compose.backup.yml run --rm backup \
  /scripts/backup_database.sh --verify

# Monitor backups
docker-compose -f docker-compose.backup.yml run --rm backup \
  /scripts/monitor_backups.sh

# Restore from backup
docker-compose -f docker-compose.backup.yml run --rm backup \
  /scripts/restore_database.sh --test-only /backups/devskyy/backup.sql.gz
```

### Access Backup Volumes

```bash
# List backup files
docker-compose -f docker-compose.backup.yml exec backup \
  ls -lh /backups/devskyy/

# Copy backup from container
docker cp devskyy-backup:/backups/devskyy/backup.sql.gz ./

# Copy backup to container
docker cp ./backup.sql.gz devskyy-backup:/backups/devskyy/
```

## GitHub Actions

### Workflow Configuration

The backup workflow is located at `.github/workflows/backup.yml`

**Required Secrets:**

```yaml
# Production Database
PROD_DB_HOST
PROD_DB_PORT
PROD_DB_NAME
PROD_DB_USER
PROD_DB_PASSWORD

# Staging Database (optional)
STAGING_DB_HOST
STAGING_DB_PORT
STAGING_DB_NAME
STAGING_DB_USER
STAGING_DB_PASSWORD

# AWS Configuration
AWS_BACKUP_ROLE_ARN  # For OIDC authentication
AWS_REGION
S3_BACKUP_BUCKET

# GPG Encryption (optional)
BACKUP_GPG_PUBLIC_KEY
BACKUP_GPG_RECIPIENT
```

### Set GitHub Secrets

```bash
# Using GitHub CLI
gh secret set PROD_DB_HOST -b "db.example.com"
gh secret set PROD_DB_PASSWORD -b "secure_password"
gh secret set S3_BACKUP_BUCKET -b "devskyy-backups"

# Import GPG public key
gh secret set BACKUP_GPG_PUBLIC_KEY < ~/.gnupg/backup-public-key.asc
```

### Workflow Jobs

1. **backup-database**: Creates and uploads backup
2. **verify-backup**: Verifies backup integrity
3. **cleanup-old-backups**: Removes backups older than 30 days
4. **monitor-backup-health**: Monitors backup health

### View Workflow Results

```bash
# List recent workflow runs
gh run list --workflow=backup.yml

# View specific run
gh run view <run-id>

# Download backup artifacts
gh run download <run-id>
```

## Monitoring

### Manual Health Check

```bash
# Check backup health
./scripts/monitor_backups.sh

# Check with S3 verification
./scripts/monitor_backups.sh --check-s3

# JSON output for automation
./scripts/monitor_backups.sh --json

# Send alerts on issues
./scripts/monitor_backups.sh --alert
```

### Monitoring Output

```
================================================================================
DevSkyy Backup Monitoring Summary
================================================================================

Timestamp:          20250116T120000Z
Environment:        production
Status:             HEALTHY

Backup Configuration:
    Backup Directory:       /backups/devskyy
    Max Backup Age:         48 hours
    S3 Bucket:              devskyy-backups

Latest Backup:
    File:                   devskyy_backup_20250116T100000Z.sql.gz.gpg

Issues Found: 0
Warnings Found: 0

Overall Status:     ✓ HEALTHY
================================================================================
```

### Exit Codes

- `0`: All checks passed
- `1`: Warnings found
- `2`: Critical issues found

### Automated Monitoring

The backup container runs hourly health checks via cron. Configure alerting:

```bash
# Email alerts
export ALERT_EMAIL=admin@devskyy.com

# Webhook alerts (Slack, Discord, etc.)
export ALERT_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## Disaster Recovery

### Full Database Loss Scenario

**Recovery Steps:**

1. **Identify Latest Backup**

```bash
# List S3 backups
aws s3 ls s3://devskyy-backups/production/ --recursive | sort -r | head -10

# Download latest backup
aws s3 cp s3://devskyy-backups/production/2025-01-16/backup.sql.gz.gpg ./
```

2. **Test Restore**

```bash
# Test restore to temporary database
./scripts/restore_database.sh --test-only ./backup.sql.gz.gpg
```

3. **Verify Data Integrity**

```bash
# Connect to test database and verify data
psql -h localhost -U devskyy -d devskyy_restore_test_TIMESTAMP

# Check critical tables
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM orders;
SELECT MAX(created_at) FROM audit_log;
```

4. **Restore to Production**

```bash
# Create final backup of current state (if database exists)
./scripts/backup_database.sh --local-only

# Restore from backup
./scripts/restore_database.sh --force ./backup.sql.gz.gpg
```

5. **Verify Production**

```bash
# Check database connectivity
psql -h localhost -U devskyy -d devskyy -c "SELECT version();"

# Verify application connectivity
curl http://localhost:8000/health
```

### Recovery Time Objectives (RTO)

- **Small databases** (< 1GB): 5-10 minutes
- **Medium databases** (1-10GB): 15-30 minutes
- **Large databases** (> 10GB): 30-60 minutes

### Recovery Point Objectives (RPO)

- **Daily backups**: Up to 24 hours of data loss
- **Hourly backups**: Up to 1 hour of data loss (custom cron)

## Configuration

### Environment Variables

#### Database Connection

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `POSTGRES_HOST` | Database host | localhost | Yes |
| `POSTGRES_PORT` | Database port | 5432 | Yes |
| `POSTGRES_DB` | Database name | devskyy | Yes |
| `POSTGRES_USER` | Database user | devskyy | Yes |
| `POSTGRES_PASSWORD` | Database password | - | Yes |

#### Backup Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `BACKUP_DIR` | Local backup directory | /backups/devskyy | No |
| `BACKUP_RETENTION_DAYS` | Days to keep local backups | 7 | No |
| `ENVIRONMENT` | Environment name | development | No |

#### S3 Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `S3_BACKUP_BUCKET` | S3 bucket name | - | No |
| `AWS_ACCESS_KEY_ID` | AWS access key | - | If using S3 |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | - | If using S3 |
| `AWS_REGION` | AWS region | us-east-1 | No |

#### GPG Encryption

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `BACKUP_GPG_RECIPIENT` | GPG recipient email | - | If using GPG |

#### Monitoring & Alerts

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MAX_BACKUP_AGE_HOURS` | Max backup age in hours | 48 | No |
| `ALERT_EMAIL` | Alert email address | - | No |
| `ALERT_WEBHOOK` | Alert webhook URL | - | No |

### S3 Bucket Setup

1. **Create S3 Bucket**

```bash
# Create bucket
aws s3 mb s3://devskyy-backups --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket devskyy-backups \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket devskyy-backups \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

2. **Configure Lifecycle Policy**

```bash
# Create lifecycle policy
cat > lifecycle.json <<'EOF'
{
  "Rules": [
    {
      "Id": "DeleteOldBackups",
      "Status": "Enabled",
      "Prefix": "",
      "Expiration": {
        "Days": 30
      }
    },
    {
      "Id": "TransitionToGlacier",
      "Status": "Enabled",
      "Prefix": "",
      "Transitions": [
        {
          "Days": 7,
          "StorageClass": "GLACIER"
        }
      ]
    }
  ]
}
EOF

# Apply lifecycle policy
aws s3api put-bucket-lifecycle-configuration \
  --bucket devskyy-backups \
  --lifecycle-configuration file://lifecycle.json
```

3. **Set Bucket Policy**

```bash
cat > bucket-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUnencryptedUploads",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::devskyy-backups/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": "AES256"
        }
      }
    }
  ]
}
EOF

aws s3api put-bucket-policy \
  --bucket devskyy-backups \
  --policy file://bucket-policy.json
```

### GPG Key Management

1. **Generate GPG Key**

```bash
# Generate new key pair
gpg --full-generate-key

# Use these settings:
# - Key type: RSA and RSA
# - Key size: 4096
# - Expiration: 2 years
# - Email: backup@devskyy.com
```

2. **Export Public Key**

```bash
# Export public key
gpg --armor --export backup@devskyy.com > backup-public-key.asc

# Import on backup server
gpg --import backup-public-key.asc

# Trust the key
gpg --edit-key backup@devskyy.com
# Type: trust
# Select: 5 (ultimate)
# Type: quit
```

3. **Export Private Key (for restore)**

```bash
# Export private key (KEEP SECURE!)
gpg --armor --export-secret-keys backup@devskyy.com > backup-private-key.asc

# Store in secure location (password manager, vault, etc.)
```

4. **Restore with GPG Key**

```bash
# Import private key on restore server
gpg --import backup-private-key.asc

# Decrypt backup
gpg --decrypt backup.sql.gz.gpg > backup.sql.gz
```

## Security

### Best Practices

✓ **Encrypt backups** with GPG for sensitive data
✓ **Use IAM roles** instead of access keys (GitHub Actions OIDC)
✓ **Enable S3 bucket encryption** at rest
✓ **Restrict S3 bucket access** with bucket policies
✓ **Rotate GPG keys** every 2 years
✓ **Store GPG private keys** in secure vault
✓ **Use read-only database user** for backups (if possible)
✓ **Audit backup access** regularly
✓ **Test restores** quarterly
✓ **Monitor backup health** continuously

### Database User Permissions

Create a dedicated backup user with minimal permissions:

```sql
-- Create backup user
CREATE USER backup_user WITH PASSWORD 'secure_password';

-- Grant necessary permissions
GRANT CONNECT ON DATABASE devskyy TO backup_user;
GRANT USAGE ON SCHEMA public TO backup_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO backup_user;

-- For future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO backup_user;
```

### S3 IAM Policy

Minimal IAM policy for backup uploads:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::devskyy-backups",
        "arn:aws:s3:::devskyy-backups/*"
      ]
    }
  ]
}
```

## Troubleshooting

### Common Issues

#### 1. pg_dump: connection failed

**Problem**: Cannot connect to database

**Solution**:
```bash
# Check database is running
pg_isready -h localhost -p 5432 -U devskyy

# Test connection
psql -h localhost -p 5432 -U devskyy -d devskyy -c "SELECT version();"

# Check environment variables
echo $POSTGRES_HOST
echo $POSTGRES_PORT
echo $POSTGRES_PASSWORD
```

#### 2. GPG encryption failed

**Problem**: GPG recipient not found

**Solution**:
```bash
# List available keys
gpg --list-keys

# Import public key
gpg --import backup-public-key.asc

# Trust the key
gpg --edit-key backup@devskyy.com trust quit
```

#### 3. S3 upload failed

**Problem**: Access denied or bucket not found

**Solution**:
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Test S3 access
aws s3 ls s3://devskyy-backups/

# Check bucket region
aws s3api get-bucket-location --bucket devskyy-backups
```

#### 4. Backup file is empty

**Problem**: Backup created but file is 0 bytes

**Solution**:
```bash
# Check disk space
df -h /backups/devskyy

# Check permissions
ls -la /backups/devskyy

# Run backup with verbose output
./scripts/backup_database.sh --local-only 2>&1 | tee backup.log
```

#### 5. Restore hangs or fails

**Problem**: Restore process stuck or errors

**Solution**:
```bash
# Check backup file integrity
gzip -t backup.sql.gz

# Decompress and inspect
gunzip -c backup.sql.gz | head -100

# Check PostgreSQL logs
tail -f /var/log/postgresql/postgresql-15-main.log

# Terminate hanging connections
psql -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'devskyy';"
```

### Error Ledgers

All errors are logged to error ledgers in JSON format:

```bash
# View error ledgers
ls -lh artifacts/error-ledger-*.json

# Parse error ledger
jq '.' artifacts/error-ledger-backup-20250116T120000Z.json
```

Example error ledger:
```json
{
  "timestamp": "2025-01-16T12:00:00Z",
  "script": "backup_database.sh",
  "error": "S3 upload failed",
  "error_code": 7,
  "context": "s3_upload",
  "environment": "production",
  "backup_file": "devskyy_backup_20250116T120000Z.sql"
}
```

### Debug Mode

Enable verbose logging:

```bash
# Bash debug mode
bash -x ./scripts/backup_database.sh

# PostgreSQL verbose mode
POSTGRES_VERBOSITY=verbose ./scripts/backup_database.sh
```

## Testing

### Run Automated Tests

```bash
# Run all backup tests
./scripts/test_backup.sh

# Run tests with cleanup
./scripts/test_backup.sh --cleanup

# Skip restore tests
./scripts/test_backup.sh --skip-restore
```

### Manual Testing Checklist

- [ ] Backup script creates backup file
- [ ] Backup file is compressed
- [ ] Backup file is encrypted (if enabled)
- [ ] Backup is uploaded to S3 (if enabled)
- [ ] Local backups are cleaned up after retention period
- [ ] Restore script can restore from local file
- [ ] Restore script can restore from S3
- [ ] Restore script can decrypt GPG files
- [ ] Monitoring script detects stale backups
- [ ] Monitoring script alerts on issues
- [ ] Docker container runs scheduled backups
- [ ] GitHub Actions workflow completes successfully

## Support

For issues or questions:

- **Documentation**: `/docs/BACKUP_RESTORE.md`
- **Scripts**: `/scripts/`
- **GitHub Issues**: https://github.com/DevSkyy/issues
- **Error Logs**: `/logs/backups/`
- **Error Ledgers**: `/artifacts/`

---

**Last Updated**: 2025-01-16
**Version**: 1.0.0
**Maintained By**: DevSkyy Team
