# WordPress Access Methods - Complete Guide

Access the WordPress.com site at **https://skyyrose.co** via multiple methods:

---

## 1. WordPress Admin Dashboard (Fastest)

**URL**: https://skyyrose.co/wp-admin/

**Login**:
- Username: `skyyroseco`
- Password: (in .env as `WORDPRESS_PASSWORD`)

**What You Can Do**:
- ✅ Create/Edit/Delete pages
- ✅ Manage products (WooCommerce)
- ✅ Upload media
- ✅ Configure theme settings
- ✅ Install plugins
- ✅ View analytics

---

## 2. WordPress.com REST API (OAuth Token)

**Endpoint**: `https://public-api.wordpress.com/rest/v1.1/sites/skyyrose.co/`

**Authentication**: Bearer token (OAuth)

### Get OAuth Token

```bash
# 1. Create app at https://developer.wordpress.com/apps/
# 2. Get Client ID & Secret
# 3. Request authorization
open "https://public-api.wordpress.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=https://localhost:3000&response_type=code"
# 4. Copy authorization code from redirect URL
# 5. Exchange for token
curl -X POST https://public-api.wordpress.com/oauth2/token \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "code=AUTHORIZATION_CODE" \
  -d "grant_type=authorization_code"
# 6. Copy "access_token" → .env as WORDPRESS_COM_ACCESS_TOKEN
```

### API Methods

```bash
# List pages
curl -H "Authorization: Bearer TOKEN" \
  "https://public-api.wordpress.com/rest/v1.1/sites/skyyrose.co/posts/?type=page"

# Create page
curl -X POST -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"My Page","content":"Content","type":"page"}' \
  "https://public-api.wordpress.com/rest/v1.1/sites/skyyrose.co/posts/"

# Update page
curl -X POST -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Updated","content":"New Content"}' \
  "https://public-api.wordpress.com/rest/v1.1/sites/skyyrose.co/posts/PAGE_ID"

# Delete page
curl -X POST -H "Authorization: Bearer TOKEN" \
  "https://public-api.wordpress.com/rest/v1.1/sites/skyyrose.co/posts/PAGE_ID?status=delete"
```

### Use Scripts

```bash
# List pages
python scripts/wordpress_com_cleanup.py --list-only

# Delete pages (with confirmation)
python scripts/wordpress_com_cleanup.py

# Dry-run (see what would be deleted)
python scripts/wordpress_com_cleanup.py --dry-run
```

---

## 3. WooCommerce REST API (Basic Auth)

**Endpoint**: `https://skyyrose.co/wp-json/wc/v3/`

**Authentication**: Consumer Key & Secret

### Setup WooCommerce Credentials

```bash
# Already in .env:
WOOCOMMERCE_KEY=ck_f2c49886126f8ec0626a2ec6082ef44d7105ae7c
WOOCOMMERCE_SECRET=cs_58bbf671bdbdd7fdab8a70c3460290dd63dff839
```

### API Methods

```bash
WC_KEY="ck_f2c49886126f8ec0626a2ec6082ef44d7105ae7c"
WC_SECRET="cs_58bbf671bdbdd7fdab8a70c3460290dd63dff839"
SITE="https://skyyrose.co"

# List products
curl -u "$WC_KEY:$WC_SECRET" \
  "${SITE}/wp-json/wc/v3/products"

# List categories
curl -u "$WC_KEY:$WC_SECRET" \
  "${SITE}/wp-json/wc/v3/products/categories"

# Get specific product
curl -u "$WC_KEY:$WC_SECRET" \
  "${SITE}/wp-json/wc/v3/products/123"

# Create product
curl -X POST -u "$WC_KEY:$WC_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"name":"Product","type":"simple","status":"publish"}' \
  "${SITE}/wp-json/wc/v3/products"

# Update product
curl -X PUT -u "$WC_KEY:$WC_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"name":"Updated Name"}' \
  "${SITE}/wp-json/wc/v3/products/123"
```

---

## 4. Python Client (HTTP + Auth)

### WordPress.com (OAuth)

```python
import requests

TOKEN = "YOUR_ACCESS_TOKEN"
SITE = "skyyrose.co"
BASE_URL = "https://public-api.wordpress.com/rest/v1.1/sites"

headers = {"Authorization": f"Bearer {TOKEN}"}

# List pages
response = requests.get(
    f"{BASE_URL}/{SITE}/posts/?type=page",
    headers=headers
)
pages = response.json()["posts"]
for page in pages:
    print(f"{page['ID']}: {page['title']}")

# Create page
response = requests.post(
    f"{BASE_URL}/{SITE}/posts/",
    headers=headers,
    json={
        "title": "New Page",
        "content": "Page content",
        "type": "page",
        "status": "publish"
    }
)
new_page = response.json()
print(f"Created: {new_page['URL']}")

# Delete page
response = requests.post(
    f"{BASE_URL}/{SITE}/posts/PAGE_ID?status=delete",
    headers=headers
)
```

### WooCommerce (Basic Auth)

```python
import requests
from requests.auth import HTTPBasicAuth

KEY = "ck_f2c49886126f8ec0626a2ec6082ef44d7105ae7c"
SECRET = "cs_58bbf671bdbdd7fdab8a70c3460290dd63dff839"
SITE = "https://skyyrose.co"

auth = HTTPBasicAuth(KEY, SECRET)

# List products
response = requests.get(
    f"{SITE}/wp-json/wc/v3/products",
    auth=auth
)
products = response.json()
for product in products:
    print(f"{product['id']}: {product['name']} - ${product['price']}")

# Create product
response = requests.post(
    f"{SITE}/wp-json/wc/v3/products",
    auth=auth,
    json={
        "name": "New Product",
        "type": "simple",
        "regular_price": "29.99",
        "status": "publish"
    }
)
```

---

## 5. XML-RPC Interface (Legacy)

**Endpoint**: `https://skyyrose.co/xmlrpc.php`

**Authentication**: Username & password

### Using Python xmlrpc

```python
import xmlrpc.client

USERNAME = "skyyroseco"
PASSWORD = "YOUR_PASSWORD"  # From .env WORDPRESS_PASSWORD
SITE = "https://skyyrose.co"

client = xmlrpc.client.ServerProxy(f"{SITE}/xmlrpc.php")

# Authenticate
try:
    blogs = client.blogger.getUsersBlogs(USERNAME, PASSWORD)
    blog_id = blogs[0]["blogid"]
    print(f"Authenticated to blog {blog_id}")
except Exception as e:
    print(f"Auth failed: {e}")

# Get pages
pages = client.wp.getPages(blog_id, USERNAME, PASSWORD)
for page in pages:
    print(f"{page['page_id']}: {page['title']}")

# Create page
page_id = client.wp.newPage(
    blog_id,
    USERNAME,
    PASSWORD,
    {
        "title": "New Page",
        "description": "Page content",
        "post_type": "page",
        "post_status": "publish"
    }
)
print(f"Created page: {page_id}")

# Delete page
deleted = client.wp.deletePage(blog_id, USERNAME, PASSWORD, page_id)
print(f"Deleted: {deleted}")
```

---

## 6. WP-CLI (Command Line Interface)

**Note**: WP-CLI requires SSH/server access. For WordPress.com, use:

```bash
# Check if available
wp --version

# List pages
wp post list --post_type=page

# Create page
wp post create --post_type=page --post_title="New Page" --post_content="Content"

# Delete page
wp post delete PAGE_ID --force

# Export database
wp db export backup.sql
```

---

## 7. FTP/SFTP File Access

**For WordPress.com**: Limited, use SSH instead

**For Self-Hosted**:
- Host: `sftp.skyyrose.co` (check in hosting panel)
- Username: (hosting panel)
- Password: (hosting panel)

Navigate to: `/wp-content/plugins/` or `/wp-content/themes/`

---

## 8. Direct Database Access (WordPress.com)

**WordPress.com doesn't provide direct database access**, but you can:

1. **Export database via admin**:
   - WP Admin → Tools → Export
   - Select all content
   - Download XML

2. **Import to local copy**:
   ```bash
   # Restore locally for analysis/testing
   wp import exported.xml --authors=create
   ```

---

## 9. Mobile App Access

**WordPress.com Mobile App**:
- iOS: [App Store](https://apps.apple.com/app/wordpress/id335703880)
- Android: [Play Store](https://play.google.com/store/apps/details?id=org.wordpress.android)

**What You Can Do**:
- ✅ Manage pages/posts
- ✅ View analytics
- ✅ Respond to comments
- ✅ Upload media
- ⚠️ Limited plugin management

---

## 10. Third-Party Tools

### Zapier (No-Code Automation)

Connect WordPress.com to:
- Google Sheets
- Slack
- Email
- Discord
- etc.

[Create Zap](https://zapier.com/apps/wordpress-com/integrations)

### Integromat/Make

Create workflows like:
- Auto-create pages from forms
- Sync products to Shopify
- Send notifications

[Make Integration](https://www.make.com/en/integrations/wordpress)

### Airtable

```bash
# Sync WordPress pages to Airtable
# Use: Zapier or Make for automation
```

---

## 11. Programmatic Access (DevSkyy Scripts)

### Available Scripts

```bash
# List pages (no auth needed, uses OAuth token from .env)
python scripts/wordpress_com_cleanup.py --list-only

# Create pages from template
python scripts/create_wordpress_pages.py

# Bulk update pages
python scripts/bulk_update_pages.py

# Sync 3D models to WordPress
python wordpress/upload_3d_models_to_wordpress.py

# Manage WooCommerce products
python wordpress/products.py
```

---

## 12. GitHub Integration

**Pages deployment via GitHub**:
1. Store page templates in Git
2. Use GitHub Actions to sync to WordPress
3. Auto-deploy on `main` branch push

See: `.github/workflows/wordpress-sync.yml` (to be created)

---

## Quick Access Cheatsheet

| Task | Method | Command |
|------|--------|---------|
| **Delete pages** | Admin Dashboard | WP Admin → Pages → Select → Delete |
| **Delete pages** | Python + OAuth | `python scripts/wordpress_com_cleanup.py` |
| **Delete pages** | cURL | `curl -X POST -H "Authorization: Bearer TOKEN" ...` |
| **Create pages** | Admin Dashboard | Pages → Add New → Publish |
| **Create pages** | Python + OAuth | `python scripts/create_wordpress_pages.py` |
| **Manage products** | Admin Dashboard | Products → Add/Edit |
| **Manage products** | WooCommerce API | `curl -u KEY:SECRET ...` |
| **View analytics** | Mobile App | Open app → View stats |
| **Backup site** | Admin Dashboard | Tools → Export |

---

## Environment Variables Required

Add to `.env`:

```bash
# WordPress.com Login
WORDPRESS_URL=https://skyyrose.co
WORDPRESS_USERNAME=skyyroseco
WORDPRESS_PASSWORD=IQb3KFqFA76vhMJmsyT1tCTC
WORDPRESS_APP_PASSWORD=IQb3KFqFA76vhMJmsyT1tCTC

# WooCommerce (for product management)
WOOCOMMERCE_KEY=ck_f2c49886126f8ec0626a2ec6082ef44d7105ae7c
WOOCOMMERCE_SECRET=cs_58bbf671bdbdd7fdab8a70c3460290dd63dff839

# WordPress.com OAuth (for REST API automation)
WORDPRESS_COM_CLIENT_ID=YOUR_CLIENT_ID
WORDPRESS_COM_CLIENT_SECRET=YOUR_CLIENT_SECRET (add as VERCEL_CLIENT_SECRET)
WORDPRESS_COM_ACCESS_TOKEN=YOUR_ACCESS_TOKEN
```

---

## Troubleshooting

### "401 Unauthorized"
- Check credentials in .env
- OAuth token may be expired → refresh
- Basic auth not supported on WordPress.com → use OAuth

### "404 Page Not Found"
- Check URL format: `/sites/domain.com/` not `/sites/domain/`
- Verify site URL doesn't include protocol

### "429 Too Many Requests"
- Rate limited by WordPress.com
- Wait 60 seconds before retrying
- Use exponential backoff in scripts

### API Endpoint Confusion
- **WordPress.com REST**: `/public-api.wordpress.com/rest/v1.1/`
- **WooCommerce REST**: `/wp-json/wc/v3/`
- **Self-hosted WordPress**: `/wp-json/wp/v2/`

---

## Resources

- [WordPress.com REST API Docs](https://developer.wordpress.com/docs/api/)
- [WordPress.com OAuth Docs](https://developer.wordpress.com/docs/oauth/)
- [WooCommerce REST API Docs](https://woocommerce.com/document/woocommerce-rest-api/)
- [XML-RPC Reference](https://wordpress.com/support/xmlrpc/)
- [WP-CLI Handbook](https://developer.wordpress.org/cli/commands/)
