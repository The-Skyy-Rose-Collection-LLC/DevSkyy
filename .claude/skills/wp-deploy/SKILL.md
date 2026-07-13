---
name: wp-deploy
description: Deploy WordPress theme changes to skyyrose.co via SFTP. Handles pre-flight checks, file sync, and post-deploy verification.
disable-model-invocation: true
---

# WordPress Theme Deploy

Deploy the `wordpress-theme/skyyrose-flagship/` theme to the live SkyyRose site.

## Pre-flight Checks

Before deploying, verify:

1. **No uncommitted changes** to theme files:
   ```bash
   git status wordpress-theme/skyyrose-flagship/
   ```

2. **PHP syntax validation** on all modified PHP files:
   ```bash
   find wordpress-theme/skyyrose-flagship/ -name "*.php" -newer .git/refs/heads/main -exec php -l {} \;
   ```

3. **Confirm which files changed** since last deploy:
   ```bash
   git diff --name-only HEAD~5 -- wordpress-theme/skyyrose-flagship/
   ```

## Deploy Steps

### Option A: SFTP Upload (requires sshpass)

SFTP requires `sshpass` for password auth. The credentials should be in environment variables:
- `SFTP_HOST` - WordPress server hostname
- `SFTP_USER` - SFTP username
- `SFTP_PASS` - SFTP password
- `SFTP_PATH` - Remote theme path (e.g., `/wp-content/themes/skyyrose-flagship/`)

```bash
# Sync changed files via sftp batch mode
sshpass -p "$SFTP_PASS" sftp -oBatchMode=no "$SFTP_USER@$SFTP_HOST" <<BATCH
cd $SFTP_PATH
put -r wordpress-theme/skyyrose-flagship/*
BATCH
```

### Option B: rsync over SSH

```bash
rsync -avz --delete \
  wordpress-theme/skyyrose-flagship/ \
  "$SFTP_USER@$SFTP_HOST:$SFTP_PATH"
```

## Post-Deploy Verification

After upload completes:

1. **Check site is live**:
   ```bash
   curl -sI https://skyyrose.co | head -5
   ```

2. **Verify CSP headers**:
   ```bash
   curl -sI https://skyyrose.co | grep -i content-security-policy
   ```

3. **Check for PHP errors** (if WP debug log is accessible):
   ```bash
   curl -s https://skyyrose.co/wp-content/debug.log | tail -20
   ```

4. **Visual spot-check**: Open homepage, a collection page, and the pre-order page in a browser.

## Rollback

If something breaks:
```bash
# Revert to previous commit's theme files
git checkout HEAD~1 -- wordpress-theme/skyyrose-flagship/
# Re-deploy with the same steps above
```

## Important Notes

- **Never deploy** without running PHP syntax checks first
- **Always commit** theme changes before deploying (preserves rollback path)
- The theme version is in `style.css` header — update it for major changes
- Scene assets (large images) should be uploaded separately to avoid timeout
