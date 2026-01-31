#!/usr/bin/env python3
"""
WordPress.com OAuth Theme Deployment Script
Uploads SkyyRose theme using OAuth credentials
"""

import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load OAuth credentials
load_dotenv('.env.wordpress')

CLIENT_ID = os.getenv('WORDPRESS_CLIENT_ID')
CLIENT_SECRET = os.getenv('WORDPRESS_CLIENT_SECRET')

if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ Error: WordPress OAuth credentials not found in .env.wordpress")
    sys.exit(1)

# Get site URL from user
site_url = input("Enter your WordPress.com site URL (e.g., mysite.wordpress.com): ").strip()
if not site_url:
    print("❌ Error: Site URL required")
    sys.exit(1)

# Remove protocol if present
site_url = site_url.replace('https://', '').replace('http://', '').rstrip('/')

print(f"\n🚀 Deploying SkyyRose theme to {site_url}")
print("=" * 60)

# Step 1: Get OAuth token
print("\n1️⃣  Authenticating with WordPress.com...")
print(f"   Please visit this URL to authorize:")
print(f"   https://public-api.wordpress.com/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri=urn:ietf:wg:oauth:2.0:oob&response_type=code")
print()

auth_code = input("   Enter authorization code: ").strip()

if not auth_code:
    print("❌ Error: Authorization code required")
    sys.exit(1)

# Exchange code for token
token_response = requests.post(
    'https://public-api.wordpress.com/oauth2/token',
    data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob'
    }
)

if token_response.status_code != 200:
    print(f"❌ Error getting access token: {token_response.text}")
    sys.exit(1)

token_data = token_response.json()
access_token = token_data.get('access_token')

print("✅ Authentication successful!")

# Step 2: Upload theme
print("\n2️⃣  Uploading theme package...")

theme_zip = Path("/Users/coreyfoster/DevSkyy/wordpress-theme/skyyrose-2025-theme.zip")

if not theme_zip.exists():
    print(f"❌ Error: Theme ZIP not found at {theme_zip}")
    sys.exit(1)

headers = {
    'Authorization': f'Bearer {access_token}'
}

# Upload theme using WordPress.com REST API
# Note: WordPress.com uses index.php?rest_route= format
base_url = f"https://public-api.wordpress.com/rest/v1.2/sites/{site_url}"

# First, get site info to verify access
site_response = requests.get(f"{base_url}", headers=headers)

if site_response.status_code != 200:
    print(f"❌ Error accessing site: {site_response.text}")
    sys.exit(1)

print(f"✅ Connected to site: {site_response.json().get('name', site_url)}")

# WordPress.com API doesn't support direct theme upload via REST API
# We need to use FTP or manual upload
print("\n⚠️  WordPress.com doesn't support theme upload via API")
print("   Please upload the theme manually:")
print()
print(f"   1. Go to: https://{site_url}/wp-admin/theme-install.php")
print(f"   2. Click 'Upload Theme'")
print(f"   3. Choose file: {theme_zip}")
print(f"   4. Click 'Install Now'")
print(f"   5. Click 'Activate'")
print()

# However, we can create pages via API
create_pages = input("Would you like to create pages automatically? (y/n): ").strip().lower()

if create_pages == 'y':
    print("\n3️⃣  Creating WordPress pages...")

    pages_to_create = [
        {
            'title': 'Home',
            'status': 'publish',
            'type': 'page',
            'slug': 'home'
        },
        {
            'title': 'The Vault',
            'status': 'publish',
            'type': 'page',
            'slug': 'vault'
        },
        {
            'title': 'Black Rose',
            'status': 'publish',
            'type': 'page',
            'slug': 'black-rose'
        },
        {
            'title': 'Black Rose Experience',
            'status': 'publish',
            'type': 'page',
            'slug': 'black-rose-experience'
        },
        {
            'title': 'Love Hurts',
            'status': 'publish',
            'type': 'page',
            'slug': 'love-hurts'
        },
        {
            'title': 'Love Hurts Experience',
            'status': 'publish',
            'type': 'page',
            'slug': 'love-hurts-experience'
        },
        {
            'title': 'Signature',
            'status': 'publish',
            'type': 'page',
            'slug': 'signature'
        },
        {
            'title': 'Signature Experience',
            'status': 'publish',
            'type': 'page',
            'slug': 'signature-experience'
        },
        {
            'title': 'About',
            'status': 'publish',
            'type': 'page',
            'slug': 'about'
        },
        {
            'title': 'Contact',
            'status': 'publish',
            'type': 'page',
            'slug': 'contact'
        }
    ]

    created_count = 0
    for page_data in pages_to_create:
        response = requests.post(
            f"{base_url}/posts/new",
            headers=headers,
            json=page_data
        )

        if response.status_code in [200, 201]:
            print(f"   ✅ Created: {page_data['title']}")
            created_count += 1
        else:
            print(f"   ⚠️  {page_data['title']}: {response.json().get('message', 'May already exist')}")

    print(f"\n✅ Created {created_count} pages")

    # Set homepage
    if created_count > 0:
        print("\n4️⃣  Setting homepage...")
        print(f"   Please go to: https://{site_url}/wp-admin/options-reading.php")
        print("   And set 'Home' as your homepage")

print("\n🎉 Deployment complete!")
print()
print("📋 Next steps:")
print("   1. Upload theme ZIP manually (instructions above)")
print("   2. Activate theme")
print("   3. Assign templates to pages")
print("   4. Import products from CSV")
print("   5. Set up navigation menu")
print()
print(f"📖 Full guide: /Users/coreyfoster/DevSkyy/wordpress-theme/skyyrose-2025/DEPLOYMENT_READY.md")
