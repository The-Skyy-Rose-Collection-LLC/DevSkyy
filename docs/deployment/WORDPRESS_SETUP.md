# WordPress API Configuration for DevSkyy

**Time Required**: ~20 minutes
**Prerequisites**: WordPress admin access to skyyrose.com

---

## Step 1: Install WooCommerce (if not already installed)

1. Log in to WordPress admin: `https://skyyrose.com/wp-admin`
2. Navigate to **Plugins → Add New**
3. Search for "WooCommerce"
4. Click **Install Now** → **Activate**
5. Skip the WooCommerce setup wizard (we'll configure manually)

---

## Step 2: Generate WooCommerce API Keys

1. Go to **WooCommerce → Settings → Advanced → REST API**
2. Click **Add Key**
3. Configure:
   - **Description**: `DevSkyy Integration`
   - **User**: Select your admin user
   - **Permissions**: **Read/Write**
4. Click **Generate API Key**
5. **IMPORTANT**: Copy both keys immediately (they won't be shown again):
   - **Consumer Key**: `ck_...` (64 characters)
   - **Consumer Secret**: `cs_...` (64 characters)
6. Save these in a secure location

---

## Step 3: Create WordPress Application Password

**Option A**: WordPress 5.6+ (Built-in Application Passwords)

1. Go to **Users → Profile** (or **Users → Your Profile**)
2. Scroll to **Application Passwords** section
3. Enter application name: `DevSkyy`
4. Click **Add New Application Password**
5. **IMPORTANT**: Copy the generated password immediately (spaces don't matter)
   - Example: `abcd 1234 EFGH 5678 ijkl 9012 mnop 3456`
6. Save this password securely

**Option B**: WordPress < 5.6 (Use Plugin)

1. Install **Application Passwords** plugin
2. Activate plugin
3. Follow Option A steps above

---

## Step 4: Enable WordPress REST API

1. Go to **Settings → Permalinks**
2. Ensure **NOT** set to "Plain"
   - Recommended: **Post name** (`https://skyyrose.com/sample-post/`)
3. Click **Save Changes**
4. Test REST API:
   ```bash
   curl https://skyyrose.com/wp-json/
   ```
   Should return JSON with API routes

---

## Step 5: Update DevSkyy Environment Variables

Add these to `/Users/coreyfoster/DevSkyy/.env.production`:

```bash
# WordPress Configuration
WORDPRESS_URL=https://skyyrose.com
WOOCOMMERCE_KEY=ck_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
WOOCOMMERCE_SECRET=cs_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

**Also update on Render**:
1. Go to Render Dashboard → DevSkyy Service → Environment
2. Add the same 4 environment variables
3. Click **Save Changes** (triggers redeploy)

---

## Step 6: Verify WordPress Integration

Run this test command:

```bash
python -c "
from integrations.wordpress.client import WordPressClient
client = WordPressClient()
print(client.test_connection())
"
```

**Expected output**: `✅ WordPress connection successful`

**Alternative test** (WooCommerce products):

```bash
curl -X GET https://skyyrose.com/wp-json/wc/v3/products \
  -u "ck_...:cs_..."
```

Should return JSON array of products.

---

## Security Best Practices

1. **Rotate API keys every 90 days**
2. **Use HTTPS only** (already configured: skyyrose.com)
3. **Limit API key permissions**:
   - Use Read/Write only for DevSkyy integration
   - Create separate Read-Only keys for monitoring
4. **Monitor API usage**:
   - WooCommerce → Status → Logs
   - Check for unauthorized access attempts
5. **Store secrets securely**:
   - Use environment variables (never commit to git)
   - Use secrets manager for production (Render secrets)

---

## Troubleshooting

### "REST API disabled" error

**Fix**: Install "Disable REST API" plugin and ensure it's NOT blocking `/wp-json/wc/v3/` routes

### "Consumer key invalid" error

**Fix**:
1. Regenerate API keys in WooCommerce settings
2. Ensure keys are copied correctly (no extra spaces)
3. Check that WooCommerce is activated

### "Application password not working" error

**Fix**:
1. Ensure WordPress is 5.6+ OR Application Passwords plugin is installed
2. Copy password exactly as shown (spaces can be removed)
3. Use username (not email) for authentication

### "Permalink structure" error

**Fix**: Change permalink structure from "Plain" to any other option (Post name recommended)

---

## Integration Features Enabled

Once configured, DevSkyy can:

✅ **Product Sync**: Bi-directional sync between DevSkyy and WooCommerce
✅ **Content Publishing**: Marketing agent can publish blog posts/pages
✅ **Theme Deployment**: Deploy generated WordPress themes
✅ **Order Processing**: Webhook-based order automation

---

## Next Steps

After WordPress configuration:

1. **Test WordPress webhook** (optional):
   ```bash
   POST https://devskyy.onrender.com/api/v1/wordpress/webhooks/product-updated
   ```

2. **Verify product sync**:
   - Create product in WooCommerce
   - Check DevSkyy database for synced product

3. **Configure webhooks** in WooCommerce:
   - WooCommerce → Settings → Advanced → Webhooks
   - Add webhook: `Product updated` → `https://devskyy.onrender.com/api/v1/wordpress/webhooks/product-updated`

---

**Status**: Ready for Phase 1 verification ✅
