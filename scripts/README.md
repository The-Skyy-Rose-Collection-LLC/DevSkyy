# DevSkyy Scripts

This directory contains utility scripts for managing and validating the DevSkyy platform.

## Requirements Validation Scripts

### validate_requirements_fast.py (Recommended for CI/CD)

**Purpose:** Fast Python-based validation of all requirements files  
**Runtime:** ~2-5 seconds  
**Used in:** CI/CD pipelines

**Features:**
- ✅ Checks all requirements files exist
- ✅ Validates version pinning standards (== vs >= vs ~=)
- ✅ Detects duplicate package entries
- ✅ Verifies inheritance structure (-r requirements.txt)
- ✅ Fast execution (no package installation)

**Usage:**
```bash
python3 scripts/validate_requirements_fast.py
```

**Exit Codes:**
- `0`: All validations passed
- `1`: One or more validations failed

### validate_requirements.sh (Comprehensive Validation)

**Purpose:** Full validation with pip install --dry-run and security scanning  
**Runtime:** ~60-120 seconds  
**Used in:** Local development, pre-commit hooks

**Features:**
- ✅ All features from fast validation
- ✅ Runs `pip install --dry-run` on each file
- ✅ Security vulnerability scanning with `safety` and `pip-audit`
- ✅ Comprehensive syntax validation

**Usage:**
```bash
./scripts/validate_requirements.sh
```

**Requirements:**
```bash
pip install safety pip-audit
```

**Exit Codes:**
- `0`: All validations passed
- `1`: One or more validations failed

## When to Use Which Script

### Use `validate_requirements_fast.py` for:
- ✅ CI/CD pipelines (fast feedback)
- ✅ Pre-commit hooks (quick checks)
- ✅ Development workflow (rapid iteration)
- ✅ Automated testing

### Use `validate_requirements.sh` for:
- ✅ Pre-release validation (comprehensive)
- ✅ Security audits (vulnerability scanning)
- ✅ Manual reviews (detailed output)
- ✅ Release preparation

## Integration

### GitHub Actions (CI/CD)

Already integrated in `.github/workflows/ci-cd.yml`:

```yaml
jobs:
  validate-requirements:
    name: Validate Requirements Files
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11.9'
      - name: Run requirements validation
        run: python3 scripts/validate_requirements_fast.py
```

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: validate-requirements
        name: Validate Requirements Files
        entry: python3 scripts/validate_requirements_fast.py
        language: system
        pass_filenames: false
        files: 'requirements.*\.txt$'
```

### Manual Validation

Before committing changes to requirements files:

```bash
# Quick check
python3 scripts/validate_requirements_fast.py

# Full validation
./scripts/validate_requirements.sh

# Test installation
pip install --dry-run -r requirements.txt
```

## Troubleshooting

### Common Issues

#### "File not found" errors
```bash
# Ensure you're running from repository root
cd /path/to/DevSkyy
python3 scripts/validate_requirements_fast.py
```

#### Duplicate package errors
```
✗ requirements-dev.txt - duplicates found:
  Line 186: 'pytest-benchmark' already defined at line 56
```

**Solution:** Remove the duplicate line or add a comment referencing the original

#### Version pinning warnings
```
⚠ requirements-dev.txt - pinning issues:
  Line 68: httpx uses >= instead of ==
```

**Solution:** Change `>=` to `==` for reproducible builds (except for `setuptools`)

#### Inheritance errors
```
✗ requirements-dev.txt - inheritance issues:
  requirements-dev.txt should inherit from requirements.txt using '-r requirements.txt'
```

**Solution:** Add `-r requirements.txt` at the top of the file

## Validation Rules

### 1. Version Pinning
- **Production files** (requirements.txt, requirements-production.txt, etc.): Use `==` for all packages
- **Exception**: Build tools like `setuptools` can use `>=`
- **Development files**: Use `==` for reproducibility

### 2. No Duplicates
- Each package should appear only once per file
- Use comments to reference where packages are defined

### 3. Inheritance
- `requirements-dev.txt` must inherit from `requirements.txt`
- `requirements-test.txt` must inherit from `requirements.txt`
- Use `-r requirements.txt` at the top of the file

### 4. File Structure
All required files must exist:
- requirements.txt
- requirements-dev.txt
- requirements-test.txt
- requirements-production.txt
- requirements.minimal.txt
- requirements.vercel.txt
- requirements_mcp.txt
- requirements-luxury-automation.txt
- wordpress-mastery/docker/ai-services/requirements.txt

## Database Backup & Restore Scripts

### backup_database.sh

**Purpose:** Production-ready PostgreSQL backup with compression, encryption, and S3 upload
**Runtime:** 1-5 minutes (depending on database size)
**Used in:** GitHub Actions, Docker cron, manual backups

**Features:**
- ✅ PostgreSQL backup using pg_dump
- ✅ Automatic gzip compression
- ✅ Optional GPG encryption
- ✅ S3 upload for off-site storage
- ✅ Local retention management (7 days default)
- ✅ Backup verification
- ✅ Health checks
- ✅ Error ledger logging

**Usage:**
```bash
# Local backup only (development)
./scripts/backup_database.sh --local-only

# Full production backup (with S3 and encryption)
./scripts/backup_database.sh --verify

# Backup without encryption
./scripts/backup_database.sh --no-encryption

# Help
./scripts/backup_database.sh --help
```

**Environment Variables:**
```bash
# Database connection (required)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=devskyy
POSTGRES_USER=devskyy
POSTGRES_PASSWORD=your_password

# Backup configuration
BACKUP_DIR=/backups/devskyy
BACKUP_RETENTION_DAYS=7

# S3 configuration (optional)
S3_BACKUP_BUCKET=my-backup-bucket
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1

# GPG encryption (optional)
BACKUP_GPG_RECIPIENT=backup@example.com
```

### restore_database.sh

**Purpose:** Restore PostgreSQL database from backup with decryption and verification
**Runtime:** 2-10 minutes (depending on database size)
**Used in:** Disaster recovery, testing, database migrations

**Features:**
- ✅ Restore from local or S3 backups
- ✅ Automatic decryption (GPG)
- ✅ Automatic decompression (gzip)
- ✅ Test restore mode (restore to temporary database)
- ✅ Data verification
- ✅ Safety confirmations

**Usage:**
```bash
# Test restore (recommended first)
./scripts/restore_database.sh --test-only backup.sql.gz

# Production restore (requires confirmation)
./scripts/restore_database.sh backup.sql.gz

# Restore from S3
./scripts/restore_database.sh --from-s3 s3://bucket/path/backup.sql.gz.gpg

# Force restore without confirmation (DANGEROUS)
./scripts/restore_database.sh --force backup.sql.gz

# Help
./scripts/restore_database.sh --help
```

**WARNING:** Production restore will replace the current database. Always test restore first!

### test_backup.sh

**Purpose:** Automated testing of backup and restore functionality
**Runtime:** 3-10 minutes
**Used in:** CI/CD, development, validation

**Features:**
- ✅ Creates test database with sample data
- ✅ Runs backup script
- ✅ Verifies backup file integrity
- ✅ Tests restore to temporary database
- ✅ Validates data integrity
- ✅ Tests compression
- ✅ Automated cleanup

**Usage:**
```bash
# Run all tests
./scripts/test_backup.sh

# Run tests and cleanup
./scripts/test_backup.sh --cleanup

# Skip restore tests
./scripts/test_backup.sh --skip-restore

# Help
./scripts/test_backup.sh --help
```

**Test Results:**
```
=== Test Suite: Database Setup ===
✓ PASS: Create test database
✓ PASS: Populate test data

=== Test Suite: Backup Operations ===
✓ PASS: Backup creation
✓ PASS: Backup file exists (1 file(s) found)
✓ PASS: Backup file size (2.3M)
✓ PASS: Backup compression integrity

=== Test Suite: Restore Operations ===
✓ PASS: Restore to temporary database
✓ PASS: Data integrity verification

Total Tests:    8
Passed:         8
Failed:         0
Pass Rate:      100.0%
```

### monitor_backups.sh

**Purpose:** Monitor backup health and send alerts
**Runtime:** < 1 minute
**Used in:** Cron jobs, monitoring systems, health checks

**Features:**
- ✅ Check backup directory exists and is writable
- ✅ Find latest backup file
- ✅ Verify backup age (stale detection)
- ✅ Check backup file size
- ✅ Verify backup integrity
- ✅ Check disk space
- ✅ Optional S3 backup verification
- ✅ Email and webhook alerts
- ✅ JSON output for automation

**Usage:**
```bash
# Basic health check
./scripts/monitor_backups.sh

# Check with custom max age
./scripts/monitor_backups.sh --max-age 24

# Check S3 and send alerts
./scripts/monitor_backups.sh --check-s3 --alert

# JSON output
./scripts/monitor_backups.sh --json

# Help
./scripts/monitor_backups.sh --help
```

**Exit Codes:**
- `0`: All checks passed (HEALTHY)
- `1`: Warnings found
- `2`: Critical issues found

**Alerting:**
```bash
# Email alerts
export ALERT_EMAIL=admin@example.com

# Webhook alerts (Slack, Discord, etc.)
export ALERT_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK
```

## Backup System Integration

### Docker Cron (Production)

```bash
# Start backup container
docker-compose -f docker-compose.yml -f docker-compose.backup.yml up -d

# View logs
docker-compose -f docker-compose.backup.yml logs -f backup

# Manual backup
docker-compose -f docker-compose.backup.yml run --rm backup \
  /scripts/backup_database.sh --verify

# Monitor backups
docker-compose -f docker-compose.backup.yml exec backup \
  /scripts/monitor_backups.sh
```

**Cron Schedule:**
- Daily backup: 2:00 AM UTC
- Hourly monitoring: Every hour

### GitHub Actions

Automated backups run on:
- Daily schedule: 2:00 AM UTC
- Push to main branch
- Manual trigger

```bash
# Trigger manual backup
gh workflow run backup.yml

# View workflow runs
gh run list --workflow=backup.yml
```

### Local Development

```bash
# Quick local backup
POSTGRES_HOST=localhost \
POSTGRES_DB=devskyy \
POSTGRES_USER=devskyy \
POSTGRES_PASSWORD=changeme \
./scripts/backup_database.sh --local-only

# Test backup system
./scripts/test_backup.sh --cleanup
```

## Backup Best Practices

### Production Checklist

- [ ] Run backups daily at minimum
- [ ] Enable S3 upload for off-site storage
- [ ] Enable GPG encryption for sensitive data
- [ ] Monitor backup health hourly
- [ ] Test restore quarterly
- [ ] Maintain 30-day retention in S3
- [ ] Verify backup integrity automatically
- [ ] Set up alerting for failures
- [ ] Document restore procedures
- [ ] Practice disaster recovery drills

### Security Best Practices

- [ ] Use dedicated backup database user with read-only access
- [ ] Encrypt backups with GPG for production
- [ ] Use IAM roles instead of access keys (GitHub Actions)
- [ ] Enable S3 bucket encryption at rest
- [ ] Restrict S3 bucket access with bucket policies
- [ ] Rotate GPG keys every 2 years
- [ ] Store GPG private keys in secure vault
- [ ] Audit backup access regularly
- [ ] Use SSL/TLS for database connections

### Testing Best Practices

- [ ] Run automated tests in CI/CD
- [ ] Test restore to temporary database monthly
- [ ] Verify data integrity after restore
- [ ] Test disaster recovery procedures quarterly
- [ ] Document restore time objectives (RTO)
- [ ] Validate backup retention policies
- [ ] Test S3 download and restore
- [ ] Verify GPG decryption works

## Troubleshooting Backup Issues

### Backup fails with "connection refused"

```bash
# Check database is running
pg_isready -h localhost -p 5432 -U devskyy

# Verify environment variables
echo $POSTGRES_HOST
echo $POSTGRES_PASSWORD
```

### S3 upload fails

```bash
# Verify AWS credentials
aws sts get-caller-identity

# Test S3 access
aws s3 ls s3://your-bucket/

# Check bucket permissions
aws s3api get-bucket-policy --bucket your-bucket
```

### GPG encryption fails

```bash
# List available keys
gpg --list-keys

# Import public key
gpg --import backup-public-key.asc

# Trust the key
gpg --edit-key backup@example.com trust quit
```

### Backup file is empty

```bash
# Check disk space
df -h /backups

# Check permissions
ls -la /backups/devskyy

# Run with verbose logging
./scripts/backup_database.sh --local-only 2>&1 | tee backup.log
```

## See Also

- [BACKUP_RESTORE.md](../docs/BACKUP_RESTORE.md) - Comprehensive backup & restore guide
- [DEPENDENCIES.md](../DEPENDENCIES.md) - Comprehensive dependency management guide
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [.github/workflows/backup.yml](../.github/workflows/backup.yml) - Backup workflow configuration
- [.github/workflows/ci-cd.yml](../.github/workflows/ci-cd.yml) - CI/CD pipeline configuration
