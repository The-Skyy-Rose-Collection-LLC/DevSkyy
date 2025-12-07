#!/usr/bin/env python3
"""
Quick WordPress Configuration Status Check

Shows what was configured for WordPress deployment system integration.
This is a simplified status checker that doesn't require full DevSkyy dependencies.
"""

import os


# Load .env if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed, checking environment variables directly")

print("=" * 80)
print("🔍 WordPress Configuration Status for DevSkyy Deployment System")
print("=" * 80)

# Check OAuth credentials
print("\n📊 WordPress OAuth 2.0 Credentials:")
oauth_vars = {
    "WORDPRESS_CLIENT_ID": os.getenv("WORDPRESS_CLIENT_ID"),
    "WORDPRESS_CLIENT_SECRET": os.getenv("WORDPRESS_CLIENT_SECRET"),
    "WORDPRESS_REDIRECT_URI": os.getenv("WORDPRESS_REDIRECT_URI", "http://localhost:8000/api/v1/wordpress/oauth/callback"),
    "WORDPRESS_TOKEN_URL": os.getenv("WORDPRESS_TOKEN_URL", "https://public-api.wordpress.com/oauth2/token"),
    "WORDPRESS_API_BASE": os.getenv("WORDPRESS_API_BASE", "https://public-api.wordpress.com/rest/v1.1")
}

oauth_configured = bool(oauth_vars["WORDPRESS_CLIENT_ID"] and oauth_vars["WORDPRESS_CLIENT_SECRET"])

for key, value in oauth_vars.items():
    if value:
        # Mask sensitive values - never log passwords or secrets
        if "SECRET" in key or "PASSWORD" in key:
            display_value = "***REDACTED***"
        elif "CLIENT_ID" in key:
            display_value = value[:12] + "..." if len(value) > 12 else value
        else:
            display_value = value

        print(f"   ✅ {key}: {display_value}")
    elif "SECRET" not in key and "PASSWORD" not in key:
        print(f"   ❌ {key}: Not configured")

# Check Basic Auth credentials
print("\n📊 WordPress Basic Auth Credentials (Skyy Rose Collection):")
basic_vars = {
    "SKYY_ROSE_SITE_URL": os.getenv("SKYY_ROSE_SITE_URL"),
    "SKYY_ROSE_USERNAME": os.getenv("SKYY_ROSE_USERNAME"),
    "SKYY_ROSE_PASSWORD": os.getenv("SKYY_ROSE_PASSWORD"),
    "SKYY_ROSE_APP_PASSWORD": os.getenv("SKYY_ROSE_APP_PASSWORD")
}

basic_configured = bool(basic_vars["SKYY_ROSE_SITE_URL"] and basic_vars["SKYY_ROSE_USERNAME"])

for key, value in basic_vars.items():
    if value:
        # Mask sensitive values - never log passwords
        if "PASSWORD" in key:
            display_value = "***REDACTED***"
        else:
            display_value = value

        print(f"   ✅ {key}: {display_value}")
    elif "PASSWORD" not in key:
        print(f"   ❌ {key}: Not configured")

# Summary
print("\n" + "=" * 80)
print("📋 Configuration Summary")
print("=" * 80)

if oauth_configured:
    print("✅ WordPress OAuth 2.0: CONFIGURED")
    print("   → Can use WordPress.com API for:")
    print("      • Posts and Pages management")
    print("      • Media uploads")
    print("      • Site statistics")
    print("      • Theme customization")
else:
    print("❌ WordPress OAuth 2.0: NOT CONFIGURED")

if basic_configured:
    print("✅ WordPress Basic Auth: CONFIGURED")
    print("   → Can use self-hosted WordPress API for:")
    print("      • WooCommerce integration")
    print("      • Divi Builder customization")
    print("      • Yoast SEO optimization")
    print("      • Direct site management")
else:
    print("❌ WordPress Basic Auth: NOT CONFIGURED")

# WordPress Tools Registered (14 total)
print("\n🔧 WordPress Tools Available in Deployment System:")
wordpress_tools = [
    "wordpress_create_post",
    "wordpress_update_post",
    "wordpress_create_page",
    "wordpress_get_posts",
    "wordpress_upload_media",
    "wordpress_get_media",
    "wordpress_get_theme_info",
    "wordpress_customize_theme",
    "wordpress_get_site_info",
    "wordpress_get_site_stats",
    "wordpress_woocommerce_products",
    "wordpress_woocommerce_orders",
    "wordpress_yoast_seo",
    "wordpress_divi_builder"
]

for i, tool in enumerate(wordpress_tools, 1):
    print(f"   {i:2d}. {tool}")

print(f"\n   Total: {len(wordpress_tools)} WordPress tools registered")

# Resources
print("\n💾 WordPress Resources Allocated:")
print("   • API Quota: 10,000 requests/hour")
print("   • Storage: 50 GB")
print("   • Memory: 2 GB")

# Example Jobs
print("\n📝 Example WordPress Deployment Jobs:")
example_jobs = [
    {
        "name": "Create Luxury Collection Page",
        "category": "WORDPRESS_CMS",
        "tools": 4,
        "tokens": "~15,000",
        "cost": "$0.15"
    },
    {
        "name": "Optimize WooCommerce Products",
        "category": "ECOMMERCE",
        "tools": 3,
        "tokens": "~50,000",
        "cost": "$0.50"
    },
    {
        "name": "Update Blog Content for SEO",
        "category": "MARKETING_BRAND",
        "tools": 3,
        "tokens": "~35,000",
        "cost": "$0.35"
    },
    {
        "name": "WordPress Site Performance Monitoring",
        "category": "CORE_SECURITY",
        "tools": 2,
        "tokens": "~8,000",
        "cost": "$0.08"
    }
]

for i, job in enumerate(example_jobs, 1):
    print(f"\n   {i}. {job['name']}")
    print(f"      Category: {job['category']}")
    print(f"      Tools: {job['tools']} WordPress APIs")
    print(f"      Estimated Tokens: {job['tokens']}")
    print(f"      Estimated Cost: {job['cost']}")

# Next Steps
print("\n" + "=" * 80)
print("📖 Next Steps")
print("=" * 80)

if oauth_configured or basic_configured:
    print("✅ You can now:")
    print("   1. Submit WordPress deployment jobs via API")
    print("   2. Jobs will be validated for infrastructure readiness")
    print("   3. 2 category-head agents will review and approve")
    print("   4. Approved jobs will deploy and execute")
    print("   5. Token usage and costs will be tracked")

    print("\n📚 Documentation:")
    print("   • Setup Guide: docs/WORDPRESS_DEPLOYMENT_SETUP.md")
    print("   • Examples: docs/wordpress_deployment_examples.json")
    print("   • API Docs: http://localhost:8000/docs#/deployment")

    print("\n🚀 Quick Start:")
    print("   # Validate a job (dry-run)")
    print("   curl -X POST http://localhost:8000/api/v1/deployment/validate \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d @docs/wordpress_deployment_examples.json")

    print("\n   # Submit a deployment job")
    print("   curl -X POST http://localhost:8000/api/v1/deployment/jobs \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{...job definition...}'")
else:
    print("❌ WordPress credentials not configured")
    print("\n📝 To configure:")
    print("   1. Edit .env file and add your credentials:")
    print("      • For WordPress.com: Add WORDPRESS_CLIENT_ID and WORDPRESS_CLIENT_SECRET")
    print("      • For self-hosted: Add SKYY_ROSE_SITE_URL, SKYY_ROSE_USERNAME, SKYY_ROSE_PASSWORD")
    print("   2. Get credentials:")
    print("      • WordPress.com OAuth: https://developer.wordpress.com/apps/")
    print("      • Self-hosted: Settings → Users → Application Passwords")
    print("   3. Re-run this script to verify")

print("=" * 80)

# Exit code
if oauth_configured or basic_configured:
    exit(0)
else:
    exit(1)
