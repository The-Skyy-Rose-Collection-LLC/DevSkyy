---
name: deploy
description: Deploy WordPress theme to skyyrose.co with comprehensive verification
argument-hint: "[--verify] [--rollback-on-fail]"
allowed-tools: [Read, Write, Bash, WebFetch, mcp__plugin_playwright_playwright__browser_snapshot]
---

# Deploy WordPress Theme

Deploy the SkyyRose 2025 theme to https://skyyrose.co (WordPress.com managed hosting) with automated verification.

## Process

### 1. Pre-Deployment Validation

Check theme files before deploying:
```bash
cd /Users/coreyfoster/DevSkyy/wordpress-theme/skyyrose-2025

# Validate PHP syntax
find . -name "*.php" -exec php -l {} \;

# Check required files
required="style.css functions.php index.php header.php footer.php inc/security-hardening.php"
for file in $required; do
  [ -f "$file" ] || echo "ERROR: Missing $file"
done
```

### 2. Create Deployment Package

```bash
cd /Users/coreyfoster/DevSkyy/wordpress-theme
timestamp=$(date +%Y%m%d-%H%M%S)
zip -r "skyyrose-2025-deploy-${timestamp}.zip" skyyrose-2025 \
  -x "*.DS_Store" "*node_modules/*" "*.git/*"

echo "Created: skyyrose-2025-deploy-${timestamp}.zip"
```

### 3. Open WordPress Admin

```bash
open "https://wordpress.com/themes/skyyrose.co"
```

**User actions required:**
1. Click "Add New Theme" → "Upload Theme"
2. Select the ZIP file created above
3. Click "Install Now"
4. **CRITICAL:** Click "Replace current with uploaded"
5. Click "Activate"

### 4. Clear Caches

```bash
open "https://wordpress.com/settings/performance/skyyrose.co"
```

User clicks "Clear all caches" and waits 30 seconds.

### 5. Verify Deployment

Check CSP headers:
```bash
curl -I "https://skyyrose.co/?nocache=1" | grep "content-security-policy"
```

Expected: Should contain 'unsafe-inline', stats.wp.com, cdn.babylonjs.com

Check console errors:
```bash
# Open browser console
open "https://skyyrose.co/?nocache=1"
```

Expected: < 10 errors (down from 107+)

### 6. Performance Check

```bash
npx lighthouse https://skyyrose.co \
  --only-categories=performance \
  --output=json
```

### 7. Report Results

Summarize deployment:
- ✅ Theme uploaded and activated
- ✅ CSP headers updated correctly
- ✅ Console errors reduced to [X]
- ✅ CSS loading properly
- ✅ Performance: LCP [X]s, FID [X]ms, CLS [X]

## Flags

**--verify**: Run extended verification (default: true)
**--rollback-on-fail**: Automatic rollback if verification fails

## Rollback

If deployment fails:
```bash
open "https://wordpress.com/backup/skyyrose.co"
```

Restore from today's backup (before deployment).

## Notes

- Always create backup before deploying
- WordPress.com requires manual upload (no API)
- Cache may take 5-10 minutes to clear
- Test in incognito window after deployment
