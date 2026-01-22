# WordPress REST API Authentication Fix

**Date**: 2026-01-15
**Status**: Fixed - Ready for Testing
**Issue**: Media upload returned HTML (200) instead of JSON (201)

---

## 🔍 Root Cause Analysis

### Problem Discovered
The `integrate_webp_wordpress.py` script was returning HTML responses (200 OK) instead of JSON (201 Created) when uploading images to WordPress Media Library.

### Investigation Process
Used **Context7** to query official WordPress REST API documentation:
- Library: `/wp-api/docs` (WordPress REST API documentation)
- Source: https://developer.wordpress.org/rest-api/reference/media/

### Root Causes Identified

1. **Incorrect Headers**
   - **Problem**: Script was sending both `Content-Disposition` AND `Content-Type` headers
   - **Expected**: WordPress REST API expects ONLY `Content-Disposition` header
   - **Impact**: WordPress may have rejected or redirected the request

2. **Poor Error Detection**
   - **Problem**: Script didn't check for HTML responses (authentication redirects)
   - **Expected**: Should detect `Content-Type: text/html` and report auth error
   - **Impact**: Confusing error messages, hard to diagnose

---

## ✅ Fixes Applied

### 1. Fixed Media Upload Headers

**Before** (scripts/integrate_webp_wordpress.py:50-64):
```python
# Determine content type
content_type = "image/webp" if filepath.suffix.lower() == ".webp" else "image/jpeg"

headers = {
    "Content-Disposition": f'attachment; filename="{filepath.name}"',
    "Content-Type": content_type,  # ❌ WRONG - causes issues
}
```

**After** (scripts/integrate_webp_wordpress.py:50-62):
```python
# WordPress REST API media upload format (official docs)
# Only Content-Disposition header required - WordPress detects MIME type automatically
headers = {
    "Content-Disposition": f'attachment; filename="{filepath.name}"',
}
```

**Reference**: Official WordPress REST API documentation
```bash
# Correct curl format (from WordPress docs)
curl --user "username:xxxx xxxx xxxx xxxx xxxx xxxx" \
  -X POST \
  -H "Content-Disposition: attachment; filename=image.jpg" \
  --data-binary @/path/to/image.jpg \
  https://example.com/wp-json/wp/v2/media
```

### 2. Enhanced Error Detection

**Added** (scripts/integrate_webp_wordpress.py:70-83):
```python
# Check for HTML response (authentication redirect)
content_type = resp.headers.get("Content-Type", "")

if resp.status == 201:
    result = await resp.json()
    print(f"  ✓ Uploaded: {filepath.name} (ID: {result['id']})")
    return result
elif "text/html" in content_type:
    # Got HTML instead of JSON - likely authentication issue
    print(f"  ✗ Failed: {filepath.name} - Authentication error (got HTML, expected JSON)")
    print(f"    Status: {resp.status}")
    print(f"    Hint: Verify WordPress Application Password is correct")
    print(f"    Run: python scripts/diagnose_wordpress_api.py")
    return None
```

### 3. Created Diagnostic Tool

**New File**: `scripts/diagnose_wordpress_api.py` (executable)

**Purpose**: Test WordPress REST API step-by-step before attempting uploads

**Tests Performed**:
1. ✅ Base URL accessibility (`https://skyyrose.co`)
2. ✅ REST API enabled (`/wp-json/`)
3. ✅ Credentials configured (`.env` file)
4. ✅ Authentication working (`/wp-json/wp/v2/users/me`)
5. ✅ Media endpoint accessible (`/wp-json/wp/v2/media`)
6. ✅ User has upload capability (`upload_files` permission)

**Usage**:
```bash
python scripts/diagnose_wordpress_api.py
```

**Example Output**:
```
======================================================================
WordPress REST API Diagnostic Tool
======================================================================

Test 1: Base URL Accessibility
URL: https://skyyrose.co
[PASS] Base URL accessible
       Status: 200

Test 2: REST API Enabled
[PASS] REST API enabled
       Namespace: ['oembed/1.0', 'wp/v2', 'wp-site-health/v1']

Test 3: Credentials Configuration
[PASS] Username configured
       Username: skyyroseco
[PASS] App Password configured
       Password: xxxx...xxxx

Test 4: Authentication Test
[PASS] Authentication
       Logged in as: Admin User (ID: 1)

Test 5: Media Endpoint Access
[PASS] Media endpoint
       Found 45 media items

Test 6: Media Upload Capability
[PASS] Upload capability
       User has 'upload_files' capability

======================================================================
Summary
======================================================================
Tests passed: 6/6

✓ All tests passed! WordPress REST API is ready for media uploads.

Next step: Run integrate_webp_wordpress.py
```

### 4. Improved Documentation

**Updated** (scripts/integrate_webp_wordpress.py:1-24):
- Added official WordPress REST API documentation link
- Added authentication instructions
- Added troubleshooting section
- Added diagnostic script reference

**Updated** (scripts/integrate_webp_wordpress.py:35-43):
- Enhanced error message when credentials missing
- Added `.env` configuration example
- Added Application Password generation instructions

---

## 📊 Technical Details

### WordPress REST API Media Upload Specification

**Endpoint**: `POST /wp-json/wp/v2/media`

**Authentication**: Basic Auth (Application Passwords, WordPress 5.6+)
```python
auth = HTTPBasicAuth(username, application_password)
```

**Headers** (REQUIRED):
```python
headers = {
    "Content-Disposition": 'attachment; filename="image.jpg"'
}
```

**Headers** (NOT ALLOWED):
- ❌ `Content-Type` - WordPress auto-detects MIME type from file content
- ❌ `Content-Length` - Automatically calculated
- ❌ Custom headers - May interfere with WordPress processing

**Request Body**: Raw binary file data (`--data-binary` in curl)

**Success Response**:
```json
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": 123,
  "date": "2026-01-15T10:30:00",
  "slug": "image-123",
  "type": "attachment",
  "mime_type": "image/webp",
  "source_url": "https://skyyrose.co/wp-content/uploads/2026/01/image.webp"
}
```

**Error Responses**:
- **401 Unauthorized**: Invalid Application Password or username
- **403 Forbidden**: User lacks `upload_files` capability
- **200 OK (HTML)**: Authentication redirect (not logged in)
- **413 Payload Too Large**: File exceeds upload limit
- **415 Unsupported Media Type**: MIME type not allowed
- **429 Too Many Requests**: Rate limit exceeded

---

## 🚀 Next Steps

### Step 1: Run Diagnostic Tool ⚠️ REQUIRED

**Before** uploading any images, verify WordPress REST API is working:

```bash
python scripts/diagnose_wordpress_api.py
```

**Expected**: All 6 tests should pass

**If tests fail**:
1. **Test 1 fails**: Check WordPress URL in `.env`
2. **Test 2 fails**: REST API disabled in WordPress (contact admin)
3. **Test 3 fails**: Add credentials to `.env` file
4. **Test 4 fails**: Verify Application Password is correct
5. **Test 5 fails**: Check WordPress user permissions
6. **Test 6 fails**: User needs Administrator or Editor role

### Step 2: Test Upload with 1 Image

Test with a single image first to verify the fix:

```bash
# Create test directory
mkdir -p /tmp/wordpress_test/{webp,fallback}

# Copy one test image (assuming you have processed images)
cp /tmp/wordpress_integration/webp_optimized/webp/product-001.webp /tmp/wordpress_test/webp/
cp /tmp/wordpress_integration/webp_optimized/fallback/product-001.jpg /tmp/wordpress_test/fallback/

# Test upload
python scripts/integrate_webp_wordpress.py \
  --webp-dir /tmp/wordpress_test/webp \
  --fallback-dir /tmp/wordpress_test/fallback \
  --limit 1
```

**Expected Output**:
```
============================================================
WordPress WebP Integration
============================================================
WebP directory:     /tmp/wordpress_test/webp
Fallback directory: /tmp/wordpress_test/fallback
Images to process:  1
WordPress URL:      https://skyyrose.co
============================================================

Processing: product-001
  ✓ Uploaded: product-001.webp (ID: 456)
  ✓ Uploaded: product-001.jpg (ID: 457)

============================================================
Upload Summary
============================================================
WebP uploaded:     1
Fallback uploaded: 1

Next Steps:
1. Add WebP helper function to theme (see below)
2. Update product templates to use helper
3. Test on live site
============================================================

✓ Generated PHP helper: wordpress/skyyrose-immersive/webp-helper.php
  Copy contents to wordpress/skyyrose-immersive/functions.php

✓ Generated mapping: wordpress/webp_image_mapping.json
  Use this to update product galleries programmatically
```

### Step 3: Process Full Catalog (150 products)

Once single-image test succeeds, process full catalog:

```bash
# Process all product images
./scripts/batch_product_processor.sh ~/products ./processed_all
./scripts/webp_converter.sh ./processed_all ./webp_all

# Upload all images
python scripts/integrate_webp_wordpress.py \
  --webp-dir ./webp_all/webp \
  --fallback-dir ./webp_all/fallback
```

**Performance Estimate**:
- 150 products = 300 uploads (150 WebP + 150 fallback)
- Rate limit: 0.5s delay = ~2.5 minutes total
- Network: Depends on connection speed

### Step 4: Integrate PHP Helper

Copy contents of `wordpress/skyyrose-immersive/webp-helper.php` to WordPress theme:

**Location**: `wordpress/skyyrose-immersive/functions.php`

**Add at bottom**:
```php
/**
 * SkyyRose WebP Image Helper
 */
function skyyrose_webp_image($webp_id, $fallback_id, $alt = '', $class = '') {
    $webp_url = wp_get_attachment_url($webp_id);
    $fallback_url = wp_get_attachment_url($fallback_id);

    if (!$webp_url || !$fallback_url) {
        return '';
    }

    ob_start();
    ?>
    <picture class="<?php echo esc_attr($class); ?>">
        <source srcset="<?php echo esc_url($webp_url); ?>" type="image/webp">
        <img src="<?php echo esc_url($fallback_url); ?>"
             alt="<?php echo esc_attr($alt); ?>"
             loading="lazy"
             class="<?php echo esc_attr($class); ?>">
    </picture>
    <?php
    return ob_get_clean();
}
```

### Step 5: Update Product Templates

**WooCommerce Product Gallery** (`woocommerce/content-single-product.php`):

**Before**:
```php
<img src="<?php echo esc_url($image_url); ?>" alt="<?php echo esc_attr($product->get_name()); ?>">
```

**After**:
```php
<?php
// Get WebP and fallback IDs from mapping
$mapping = json_decode(file_get_contents(get_template_directory() . '/webp_image_mapping.json'), true);
$product_slug = $product->get_slug();

if (isset($mapping[$product_slug])) {
    echo skyyrose_webp_image(
        $mapping[$product_slug]['webp_id'],
        $mapping[$product_slug]['fallback_id'],
        $product->get_name(),
        'woocommerce-product-gallery__image'
    );
}
?>
```

### Step 6: Verify & Test

1. **Check WordPress Media Library**
   - Verify images appear in Media Library
   - Check WebP images are recognized (not "application/octet-stream")
   - Verify image dimensions are correct

2. **Test on Product Pages**
   - View product in Chrome (should serve WebP)
   - View product in Safari 13 (should serve JPG fallback)
   - Check Network tab for correct MIME types

3. **Run Lighthouse Audit**
   - Check "Serve images in next-gen formats" metric
   - Verify Largest Contentful Paint (LCP) improvement
   - Check Core Web Vitals scores

---

## 🔒 Security Notes

### Application Password Best Practices

1. **Generate Unique Password**
   - WordPress Admin → Users → Profile → Application Passwords
   - Name: "DevSkyy Image Upload Script"
   - Copy password immediately (shown once)

2. **Store Securely**
   - Add to `.env` file (never commit to git)
   - Format: `WORDPRESS_APP_PASSWORD="xxxx xxxx xxxx xxxx xxxx xxxx"` # pragma: allowlist secret
   - Keep spaces in password (required format)

3. **Revoke When Done**
   - After bulk upload complete, revoke Application Password
   - Prevents unauthorized use if `.env` is compromised

4. **Audit Access**
   - Check WordPress admin logs for API access
   - Monitor for unexpected media uploads
   - Review Application Passwords regularly

### Rate Limiting

Current script includes **0.5s delay** between uploads:
```python
await asyncio.sleep(0.5)  # 2 requests/second
```

**Adjust if needed**:
- Faster: `0.1s` (10 req/s) - May trigger rate limits
- Safer: `1.0s` (1 req/s) - Lower server load
- Production: Keep at `0.5s` (good balance)

---

## 📚 Resources

### Official Documentation
- [WordPress REST API Handbook](https://developer.wordpress.org/rest-api/)
- [Media Endpoint Reference](https://developer.wordpress.org/rest-api/reference/media/)
- [Authentication Guide](https://developer.wordpress.org/rest-api/using-the-rest-api/authentication/)
- [Application Passwords](https://make.wordpress.org/core/2020/11/05/application-passwords-integration-guide/)

### Related Files
- `scripts/integrate_webp_wordpress.py` - Fixed upload script
- `scripts/diagnose_wordpress_api.py` - Diagnostic tool
- `wordpress/skyyrose-immersive/webp-helper.php` - PHP helper function
- `wordpress/webp_image_mapping.json` - WebP/fallback ID mapping
- `IMAGE_OPTIMIZATION_WORKFLOW_SUMMARY.md` - Full workflow documentation

---

## 🐛 Troubleshooting

### Issue: "Authentication error (got HTML, expected JSON)"

**Cause**: Application Password is incorrect or WordPress is redirecting to login

**Fix**:
1. Run diagnostic: `python scripts/diagnose_wordpress_api.py`
2. Check Test 4 (Authentication)
3. Verify Application Password in `.env` matches WordPress
4. Ensure password includes spaces (e.g., `xxxx xxxx xxxx xxxx`)
5. Check user has Administrator or Editor role

### Issue: "401 Unauthorized"

**Cause**: Invalid credentials or Application Password expired

**Fix**:
1. Verify username in `.env` matches WordPress login
2. Regenerate Application Password in WordPress admin
3. Update `.env` with new password
4. Test with diagnostic script

### Issue: "403 Forbidden"

**Cause**: User lacks `upload_files` capability

**Fix**:
1. Check user role (needs Administrator or Editor)
2. Contact WordPress admin to elevate permissions
3. Or use different user credentials

### Issue: "413 Payload Too Large"

**Cause**: Image file exceeds WordPress upload limit

**Fix**:
1. Check WordPress upload limit: `wp-admin → Media → Add New`
2. Increase limit in `php.ini`:
   ```ini
   upload_max_filesize = 64M
   post_max_size = 64M
   ```
3. Or reduce image quality in `webp_converter.sh`

### Issue: "429 Too Many Requests"

**Cause**: Rate limit exceeded

**Fix**:
1. Increase delay in script (line 142): `await asyncio.sleep(1.0)`
2. Or upload in smaller batches using `--limit` flag

---

**Version**: 1.0.0
**Last Updated**: 2026-01-15 22:45:00 PST
**Status**: Fixed - Ready for Testing

**Created by**: Claude Sonnet 4.5 using Context7 research
**For**: SkyyRose LLC
**Contact**: support@skyyrose.com
