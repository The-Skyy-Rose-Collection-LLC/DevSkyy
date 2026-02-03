# AI Image Enhancement - Quick Start Guide

## Installation

### 1. WordPress Theme Setup

Files already integrated into SkyyRose 2025 theme:

```
wordpress-theme/skyyrose-2025/
├── inc/ai-image-enhancement.php      ✓ Core integration
├── admin/ai-enhancement-settings.php ✓ Settings page
├── assets/
│   ├── js/admin-ai-enhancement.js   ✓ AJAX handlers
│   └── css/admin-ai-enhancement.css ✓ Admin styles
└── functions.php                     ✓ Loads ai-image-enhancement.php
```

### 2. FastAPI Backend Setup

Ensure backend is running:

```bash
cd /Users/coreyfoster/DevSkyy
uvicorn main_enterprise:app --host 0.0.0.0 --port 8000 --reload
```

Test health endpoint:
```bash
curl http://localhost:8000/health
```

### 3. Configure API Keys

**Option A: WordPress Admin (Recommended)**

1. Go to **WordPress Admin > Media > AI Enhancement**
2. Scroll to "API Configuration"
3. Enter API keys:
   - Replicate: `r8_...`
   - FAL: `...`
   - Stability AI: `...`
   - Together AI: `...`
   - RunwayML: `...`
4. Click "Test API Connection"
5. Save Settings

**Option B: Environment Variables**

```bash
# In .env or environment
export REPLICATE_API_KEY="r8_..."
export FAL_API_KEY="..."
export STABILITY_API_KEY="..."
export TOGETHER_API_KEY="..."
export RUNWAY_API_KEY="..."
```

## Basic Usage

### Enable Auto-Enhancement

1. Go to **Media > AI Enhancement**
2. Check "Enable AI Enhancement"
3. Check "Auto-Enhance Uploads"
4. Check "Luxury Color Grading"
5. Check "Blurhash Placeholders"
6. Check "Responsive Images"
7. Save Settings

### Upload Test Image

1. Go to **Media > Add New**
2. Upload a product image
3. Wait ~5-10 seconds
4. Go to **Media > Library**
5. Check status column shows "✓ Enhanced"

### Manual Enhancement

1. Go to **Media > Library**
2. Find unenhanced image
3. Click "Enhance" button
4. Wait for processing
5. Status updates to "Enhanced"

### Bulk Enhancement

1. Go to **Media > Library**
2. Select multiple images (checkboxes)
3. Choose "Enhance with AI" from bulk actions dropdown
4. Click "Apply"
5. Watch progress bar

## Testing

### 1. Upload Test

```bash
# Upload image via WordPress admin
# Check logs:
tail -f /path/to/wordpress/debug.log
```

### 2. API Test

```bash
# Test FastAPI endpoint directly
curl -X POST http://localhost:8000/api/v1/ai/enhance-image \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test-product.jpg" \
  -F "apply_luxury_filter=true" \
  -F "generate_blurhash=true"
```

### 3. WordPress AJAX Test

```javascript
// Run in browser console on WordPress admin
jQuery.post(ajaxurl, {
    action: 'skyyrose_test_api',
    nonce: '<?php echo wp_create_nonce("skyyrose_enhance_nonce"); ?>'
}, function(response) {
    console.log(response);
});
```

## Batch Processing

Process all existing WordPress media:

```bash
cd /Users/coreyfoster/DevSkyy

python scripts/wordpress-media-pipeline.py \
  --wp-url https://skyyrose.co \
  --wp-username admin \
  --wp-password "YOUR_APP_PASSWORD" \
  --fal-key "YOUR_FAL_KEY" \
  --replicate-key "YOUR_REPLICATE_KEY" \
  --output-dir ./enhanced_media
```

## Verification

### Check Enhancement Status

```php
// In WordPress template
$attachment_id = 123;
$status = get_post_meta($attachment_id, '_skyyrose_enhancement_status', true);
$blurhash = get_post_meta($attachment_id, '_skyyrose_blurhash', true);

echo "Status: $status<br>";
echo "Blurhash: $blurhash<br>";
```

### View Enhanced Image

```php
// Get enhanced image URL
$image_url = wp_get_attachment_image_src($attachment_id, 'full')[0];
echo '<img src="' . $image_url . '" alt="Enhanced Product">';
```

### Compare Before/After

1. Download original from WordPress
2. Upload to test environment
3. Enable enhancement
4. Download enhanced version
5. Compare side-by-side

## Common Settings

### For Product Photography

```
✓ Enable AI Enhancement
✓ Auto-Enhance Uploads
✓ Luxury Color Grading
✓ Blurhash Placeholders
✓ Responsive Images
☐ Background Removal (test first)
☐ 4x Upscaling (slow)
```

### For Editorial Content

```
✓ Enable AI Enhancement
☐ Auto-Enhance Uploads (manual only)
✓ Luxury Color Grading
✓ Blurhash Placeholders
✓ Responsive Images
☐ Background Removal
☐ 4x Upscaling
```

### For Hero Images

```
✓ Enable AI Enhancement
☐ Auto-Enhance Uploads
✓ Luxury Color Grading
✓ Blurhash Placeholders
✓ Responsive Images
☐ Background Removal
✓ 4x Upscaling (use selectively)
```

## Troubleshooting

### "API connection failed"

**Check:**
1. FastAPI backend running: `curl http://localhost:8000/health`
2. Firewall allows connection from WordPress to FastAPI
3. SKYYROSE_API_URL defined correctly

### "Enhancement takes too long"

**Solutions:**
1. Disable "4x Upscaling" (slowest operation)
2. Increase PHP max_execution_time
3. Process in smaller batches
4. Use background queue (WP Cron)

### "Enhanced image looks wrong"

**Try:**
1. Disable "Background Removal" (can affect quality)
2. Adjust luxury filter intensity (contact developer)
3. Use manual enhancement with preview
4. Check original image quality

### "No enhancement button in media library"

**Check:**
1. Theme is SkyyRose 2025
2. inc/ai-image-enhancement.php loaded
3. JavaScript enqueued correctly
4. Browser console for errors

## Quick Commands

```bash
# Start FastAPI backend
uvicorn main_enterprise:app --reload

# Test health endpoint
curl http://localhost:8000/health

# Test enhancement endpoint
curl -X POST http://localhost:8000/api/v1/ai/enhance-image \
  -F "file=@test.jpg" \
  -F "apply_luxury_filter=true"

# Batch process media
python scripts/wordpress-media-pipeline.py \
  --wp-url https://skyyrose.co \
  --wp-username admin \
  --wp-password "APP_PASSWORD" \
  --fal-key "KEY"

# Check WordPress logs
tail -f wp-content/debug.log

# Check FastAPI logs
tail -f /path/to/fastapi.log
```

## Next Steps

1. ✓ Configure API keys
2. ✓ Test with single image
3. ✓ Enable auto-enhancement
4. ✓ Process existing media (batch script)
5. ✓ Monitor enhancement quality
6. ✓ Adjust settings as needed
7. ✓ Set up monitoring/alerts
8. ✓ Document internal workflows

## Support

- **Documentation:** [AI_ENHANCEMENT_INTEGRATION.md](AI_ENHANCEMENT_INTEGRATION.md)
- **Backend Code:** [services/ai_image_enhancement.py](../services/ai_image_enhancement.py)
- **WordPress Code:** [inc/ai-image-enhancement.php](skyyrose-2025/inc/ai-image-enhancement.php)
- **API Endpoints:** [api/v1/ai_enhancement.py](../api/v1/ai_enhancement.py)

---

**Status:** Ready for Testing ✓
**Version:** 2.0.0
