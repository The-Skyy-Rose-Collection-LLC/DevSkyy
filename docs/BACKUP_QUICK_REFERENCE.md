# DevSkyy Database Backup - Quick Reference

Quick reference card for common backup and restore operations.

## Daily Commands

### Create Backup

```bash
# Local backup (development)
./scripts/backup_database.sh --local-only

# Production backup (S3 + encryption)
./scripts/backup_database.sh --verify
```

### Check Backup Health

```bash
# Quick health check
./scripts/monitor_backups.sh

# With S3 verification
./scripts/monitor_backups.sh --check-s3
```

### List Backups

```bash
# Local backups
ls -lh /backups/devskyy/

# S3 backups
aws s3 ls s3://your-bucket/production/
```

## Emergency Restore

### 1. Test Restore First (ALWAYS)

```bash
./scripts/restore_database.sh --test-only <backup-file>
```

### 2. Production Restore

```bash
# Interactive (requires confirmation)
./scripts/restore_database.sh <backup-file>

# From S3
./scripts/restore_database.sh --from-s3 s3://bucket/path/backup.sql.gz.gpg
```

## Docker Commands

```bash
# Start backup service
docker-compose -f docker-compose.yml -f docker-compose.backup.yml up -d

# Manual backup
docker-compose -f docker-compose.backup.yml run --rm backup \
  /scripts/backup_database.sh --verify

# View logs
docker-compose -f docker-compose.backup.yml logs -f backup

# Monitor backups
docker-compose -f docker-compose.backup.yml exec backup \
  /scripts/monitor_backups.sh
```

## GitHub Actions

```bash
# Trigger manual backup
gh workflow run backup.yml

# View workflow runs
gh run list --workflow=backup.yml

# Download backup artifacts
gh run download <run-id>
```

## Environment Variables

```bash
# Database
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=devskyy
export POSTGRES_USER=devskyy
export POSTGRES_PASSWORD=your_password

# Backup
export BACKUP_DIR=/backups/devskyy
export BACKUP_RETENTION_DAYS=7

# S3 (optional)
export S3_BACKUP_BUCKET=my-bucket
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# GPG (optional)
export BACKUP_GPG_RECIPIENT=backup@example.com
```

## Troubleshooting

### Database not accessible

```bash
pg_isready -h localhost -p 5432 -U devskyy
```

### Backup file empty

```bash
# Check disk space
df -h /backups

# Check permissions
ls -la /backups/devskyy
```

### S3 upload fails

```bash
# Verify credentials
aws sts get-caller-identity

# Test S3 access
aws s3 ls s3://your-bucket/
```

### GPG encryption fails

```bash
# List keys
gpg --list-keys

# Import public key
gpg --import backup-public-key.asc
```

## Testing

```bash
# Run automated tests
./scripts/test_backup.sh --cleanup
```

## File Locations

| Item | Path |
|------|------|
| Backup script | `/home/user/DevSkyy/scripts/backup_database.sh` |
| Restore script | `/home/user/DevSkyy/scripts/restore_database.sh` |
| Test script | `/home/user/DevSkyy/scripts/test_backup.sh` |
| Monitor script | `/home/user/DevSkyy/scripts/monitor_backups.sh` |
| Documentation | `/home/user/DevSkyy/docs/BACKUP_RESTORE.md` |
| Workflow | `/home/user/DevSkyy/.github/workflows/backup.yml` |
| Docker config | `/home/user/DevSkyy/docker-compose.backup.yml` |
| Backup dir | `/backups/devskyy/` |
| Logs | `/home/user/DevSkyy/logs/backups/` |
| Error ledgers | `/home/user/DevSkyy/artifacts/` |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Warnings found |
| 2 | Critical issues |

## Support

- Full docs: `/home/user/DevSkyy/docs/BACKUP_RESTORE.md`
- Scripts README: `/home/user/DevSkyy/scripts/README.md`
- GitHub Issues: Create issue with `backup` label

## Emergency Contacts

**For critical production issues:**
1. Check monitoring dashboard
2. Review error ledgers in `/home/user/DevSkyy/artifacts/`
3. Check workflow logs in GitHub Actions
4. Create incident issue with `critical` label

---

**Remember:**
- ✓ Always test restore before production restore
- ✓ Verify backup health daily
- ✓ Test disaster recovery quarterly
- ✓ Keep GPG keys secure
- ✓ Monitor S3 costs
