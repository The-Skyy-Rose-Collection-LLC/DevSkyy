# WordPress.com Page Cleanup Guide

## Status

This is a **WordPress.com hosted site** (not self-hosted), which requires **OAuth token authentication** for REST API access, not basic auth.

**Current Pages to Delete**:
- /home-2/ (ID varies)
- /signature/ (ID varies)
- /black-rose/ (ID varies)
- /love-hurts/ (ID varies)
- /about-2/ (ID varies)

## Option 1: Manual Deletion (Fastest)

1. **Go to WordPress Admin**: https://skyyrose.co/wp-admin
2. **Pages → All Pages**
3. **Select pages** (checkbox on left):
   - home-2
   - signature
   - black-rose
   - love-hurts
   - about-2
4. **Bulk Actions**: "Delete Permanently"
5. **Apply**

## Option 2: OAuth Token Setup (For Scripted Automation)

### Step 1: Create WordPress.com OAuth App

1. Go to: https://developer.wordpress.com/apps/
2. Sign in with your WordPress.com account
3. Click **"Create New App"**
4. Fill in:
   - **App Name**: `DevSkyy WordPress Cleanup`
   - **Redirect URL**: `https://localhost:3000/oauth-callback` (or your app URL)
   - **Type**: `Web`
5. Click **"Create App"**
6. Copy:
   - **Client ID** → `WORDPRESS_COM_CLIENT_ID` in `.env`
   - **Client Secret** → `WORDPRESS_COM_CLIENT_SECRET` in `.env` (already added as `VERCEL_CLIENT_SECRET`?)

### Step 2: Generate Access Token

```bash
# Request authorization
open "https://public-api.wordpress.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=https://localhost:3000/oauth-callback&response_type=code"

# User grants access, receives code
# Exchange code for token:
curl -X POST https://public-api.wordpress.com/oauth2/token \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "code=AUTH_CODE" \
  -d "grant_type=authorization_code"

# Response contains: "access_token"
# Add to .env as: WORDPRESS_COM_ACCESS_TOKEN
```

### Step 3: Use Token with REST API

```bash
# List pages
curl -H "Authorization: Bearer ACCESS_TOKEN" \
  https://public-api.wordpress.com/rest/v1.1/sites/skyyrose.co/posts/?type=page

# Delete page
curl -X DELETE \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  https://public-api.wordpress.com/rest/v1.1/sites/skyyrose.co/posts/PAGE_ID
```

## Option 3: Use the Cleanup Script (Post-OAuth Setup)

Once you have `WORDPRESS_COM_ACCESS_TOKEN` in `.env`:

```bash
cd /Users/coreyfoster/DevSkyy
python scripts/wordpress_com_cleanup.py
```

See: `scripts/wordpress_com_cleanup.py` (to be created)

---

## Production Pages to Create After Cleanup

After deleting old pages, create these production pages:

| Slug | Title | Type | Parent |
|------|-------|------|--------|
| / | Home | Page | - |
| /shop | Shop | Page | - |
| /experiences/signature | Signature Collection | Page | - |
| /experiences/black-rose | Black Rose Collection | Page | - |
| /experiences/love-hurts | Love Hurts Collection | Page | - |
| /about | About SkyyRose | Page | - |
| /contact | Contact | Page | - |

**Template for Each**:
```html
[collection_logo collection="COLLECTION_NAME" size="hero"]

<!-- Featured 3D Models Grid -->
<div class="collection-3d-viewer">
  [skyyrose_collection_experience collection="COLLECTION_NAME" enable_ar="true"]
</div>

<!-- Product Showcase -->
<div class="collection-products">
  [products category="CATEGORY_ID" columns="3" orderby="popularity"]
</div>
```

---

## Resources

- **WordPress.com REST API Docs**: https://developer.wordpress.com/docs/api/
- **OAuth Flow**: https://developer.wordpress.com/docs/oauth/
- **Sites Endpoint**: https://developer.wordpress.com/docs/api/1.1/get/sites/%24site/
- **Posts Endpoint**: https://developer.wordpress.com/docs/api/1.1/get/sites/%24site/posts/
