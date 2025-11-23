#!/usr/bin/env python3
"""
WordPress Infrastructure Setup for DevSkyy Deployment System

This script registers WordPress capabilities with the automated deployment system,
enabling infrastructure validation and multi-agent approval workflows for WordPress tasks.

Per Truth Protocol:
- Rule #1: Never guess - Validate all credentials
- Rule #5: No secrets in code - Environment variables only
- Rule #7: Input validation - Schema enforcement

Usage:
    python scripts/wordpress/setup_wordpress_infrastructure.py
"""

import asyncio
import logging
import os
from pathlib import Path
import sys


# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

from config.wordpress_credentials import validate_environment_setup
from ml.agent_deployment_system import ResourceType, get_deployment_orchestrator


# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WordPressInfrastructureSetup:
    """Register WordPress tools and resources with deployment system."""

    def __init__(self):
        self.orchestrator = get_deployment_orchestrator()
        self.validator = self.orchestrator.validator

    def check_oauth_credentials(self) -> bool:
        """Check if WordPress OAuth credentials are configured."""
        required_oauth = [
            "WORDPRESS_CLIENT_ID",
            "WORDPRESS_CLIENT_SECRET",
            "WORDPRESS_REDIRECT_URI",
            "WORDPRESS_TOKEN_URL",
            "WORDPRESS_API_BASE"
        ]

        all_configured = all(os.getenv(var) for var in required_oauth)

        if all_configured:
            logger.info("✅ WordPress OAuth 2.0 credentials configured")
        else:
            missing = [var for var in required_oauth if not os.getenv(var)]
            logger.warning("⚠️  Missing one or more required WordPress OAuth credentials.")

        return all_configured

    def check_basic_auth_credentials(self) -> bool:
        """Check if WordPress basic auth credentials are configured."""
        env_check = validate_environment_setup()

        if env_check["valid"]:
            logger.info("✅ WordPress basic auth credentials configured")
            logger.info(f"   Site URL: {os.getenv('SKYY_ROSE_SITE_URL')}")
            logger.info(f"   Username: {os.getenv('SKYY_ROSE_USERNAME')}")
        else:
            logger.warning(f"⚠️  Missing basic auth credentials: {', '.join(env_check['missing_required'])}")

        return env_check["valid"]

    def register_wordpress_tools(self):
        """Register all WordPress-specific tools with the deployment system."""

        logger.info("\n🔧 Registering WordPress Tools...")

        # WordPress REST API Tools
        wordpress_tools = [
            # Content Management
            {
                "tool_name": "wordpress_create_post",
                "tool_type": "api",
                "rate_limit": 60,  # 60 requests per minute
                "metadata": {
                    "description": "Create WordPress blog posts",
                    "auth_type": "oauth2",
                    "scope": "posts",
                    "category": "WORDPRESS_CMS"
                }
            },
            {
                "tool_name": "wordpress_update_post",
                "tool_type": "api",
                "rate_limit": 60,
                "metadata": {
                    "description": "Update existing WordPress posts",
                    "auth_type": "oauth2",
                    "scope": "posts",
                    "category": "WORDPRESS_CMS"
                }
            },
            {
                "tool_name": "wordpress_create_page",
                "tool_type": "api",
                "rate_limit": 60,
                "metadata": {
                    "description": "Create WordPress pages",
                    "auth_type": "oauth2",
                    "scope": "posts",
                    "category": "WORDPRESS_CMS"
                }
            },
            {
                "tool_name": "wordpress_get_posts",
                "tool_type": "api",
                "rate_limit": 120,
                "metadata": {
                    "description": "Retrieve WordPress posts",
                    "auth_type": "oauth2",
                    "scope": "posts",
                    "category": "WORDPRESS_CMS"
                }
            },

            # Media Management
            {
                "tool_name": "wordpress_upload_media",
                "tool_type": "api",
                "rate_limit": 30,
                "metadata": {
                    "description": "Upload media to WordPress",
                    "auth_type": "oauth2",
                    "scope": "media",
                    "category": "WORDPRESS_CMS"
                }
            },
            {
                "tool_name": "wordpress_get_media",
                "tool_type": "api",
                "rate_limit": 120,
                "metadata": {
                    "description": "Retrieve WordPress media",
                    "auth_type": "oauth2",
                    "scope": "media",
                    "category": "WORDPRESS_CMS"
                }
            },

            # Theme & Customization
            {
                "tool_name": "wordpress_get_theme_info",
                "tool_type": "api",
                "rate_limit": 60,
                "metadata": {
                    "description": "Get WordPress theme information",
                    "auth_type": "oauth2",
                    "scope": "sites",
                    "category": "WORDPRESS_CMS"
                }
            },
            {
                "tool_name": "wordpress_customize_theme",
                "tool_type": "api",
                "rate_limit": 30,
                "metadata": {
                    "description": "Customize WordPress theme",
                    "auth_type": "oauth2",
                    "scope": "sites",
                    "category": "WORDPRESS_CMS"
                }
            },

            # Site Management
            {
                "tool_name": "wordpress_get_site_info",
                "tool_type": "api",
                "rate_limit": 120,
                "metadata": {
                    "description": "Get WordPress site information",
                    "auth_type": "oauth2",
                    "scope": "sites",
                    "category": "WORDPRESS_CMS"
                }
            },
            {
                "tool_name": "wordpress_get_site_stats",
                "tool_type": "api",
                "rate_limit": 60,
                "metadata": {
                    "description": "Get WordPress site statistics",
                    "auth_type": "oauth2",
                    "scope": "stats",
                    "category": "WORDPRESS_CMS"
                }
            },

            # WooCommerce Integration
            {
                "tool_name": "wordpress_woocommerce_products",
                "tool_type": "api",
                "rate_limit": 60,
                "metadata": {
                    "description": "Manage WooCommerce products",
                    "auth_type": "application_password",
                    "scope": "woocommerce",
                    "category": "ECOMMERCE"
                }
            },
            {
                "tool_name": "wordpress_woocommerce_orders",
                "tool_type": "api",
                "rate_limit": 60,
                "metadata": {
                    "description": "Manage WooCommerce orders",
                    "auth_type": "application_password",
                    "scope": "woocommerce",
                    "category": "ECOMMERCE"
                }
            },

            # SEO & Optimization
            {
                "tool_name": "wordpress_yoast_seo",
                "tool_type": "api",
                "rate_limit": 60,
                "metadata": {
                    "description": "Manage Yoast SEO settings",
                    "auth_type": "application_password",
                    "scope": "seo",
                    "category": "MARKETING_BRAND"
                }
            },

            # Divi Builder
            {
                "tool_name": "wordpress_divi_builder",
                "tool_type": "api",
                "rate_limit": 30,
                "metadata": {
                    "description": "Manage Divi Builder layouts",
                    "auth_type": "application_password",
                    "scope": "divi",
                    "category": "WORDPRESS_CMS"
                }
            }
        ]

        # Register each tool
        for tool in wordpress_tools:
            self.validator.register_tool(
                tool_name=tool["tool_name"],
                tool_type=tool["tool_type"],
                rate_limit=tool["rate_limit"],
                metadata=tool["metadata"]
            )
            logger.info(f"   ✓ Registered: {tool['tool_name']}")

        logger.info(f"✅ Registered {len(wordpress_tools)} WordPress tools")

    def register_wordpress_resources(self):
        """Register WordPress API resources with the deployment system."""

        logger.info("\n💾 Registering WordPress Resources...")

        # WordPress API rate limits and quotas
        resources = [
            {
                "resource_type": ResourceType.API_QUOTA,
                "amount": 10000.0,  # 10k requests per hour
                "unit": "requests/hour"
            },
            {
                "resource_type": ResourceType.STORAGE,
                "amount": 50.0,  # 50 GB media storage
                "unit": "GB"
            },
            {
                "resource_type": ResourceType.MEMORY,
                "amount": 2.0,  # 2 GB for WordPress operations
                "unit": "GB"
            }
        ]

        for resource in resources:
            self.validator.register_resource(
                resource_type=resource["resource_type"],
                amount=resource["amount"]
            )
            logger.info(f"   ✓ Registered: {resource['resource_type'].value} ({resource['amount']} {resource['unit']})")

        logger.info(f"✅ Registered {len(resources)} WordPress resources")

    def register_api_keys(self):
        """Register WordPress API key availability."""

        logger.info("\n🔑 Checking WordPress API Keys...")

        # Check OAuth
        has_oauth = self.check_oauth_credentials()
        self.validator.register_api_key("wordpress_oauth", has_oauth)

        # Check Basic Auth
        has_basic = self.check_basic_auth_credentials()
        self.validator.register_api_key("wordpress_basic", has_basic)

        # Check specific integrations
        has_woocommerce = bool(os.getenv("SKYY_ROSE_APP_PASSWORD"))
        self.validator.register_api_key("wordpress_woocommerce", has_woocommerce)

        logger.info("\n📊 API Key Status:")
        logger.info(f"   WordPress OAuth: {'✅' if has_oauth else '❌'}")
        logger.info(f"   WordPress Basic Auth: {'✅' if has_basic else '❌'}")
        logger.info(f"   WooCommerce: {'✅' if has_woocommerce else '❌'}")

        return has_oauth or has_basic

    def generate_example_jobs(self):
        """Generate example WordPress deployment jobs."""

        logger.info("\n📝 Example WordPress Deployment Jobs...")

        examples = {
            "create_luxury_collection_page": {
                "job_name": "Create Luxury Collection Page",
                "job_description": "Create a new luxury product collection page with Divi builder, SEO optimization, and conversion-focused design",
                "category": "WORDPRESS_CMS",
                "primary_agent": "wordpress_fullstack_theme_builder",
                "supporting_agents": ["brand_intelligence", "seo_optimizer"],
                "required_tools": [
                    {"tool_name": "wordpress_create_page", "tool_type": "api", "estimated_calls": 1, "required": True},
                    {"tool_name": "wordpress_divi_builder", "tool_type": "api", "estimated_calls": 3, "required": True},
                    {"tool_name": "wordpress_upload_media", "tool_type": "api", "estimated_calls": 5, "required": False},
                    {"tool_name": "wordpress_yoast_seo", "tool_type": "api", "estimated_calls": 1, "required": True}
                ],
                "required_resources": [
                    {"resource_type": "API_QUOTA", "amount": 20.0, "unit": "requests"},
                    {"resource_type": "STORAGE", "amount": 0.5, "unit": "GB"}
                ],
                "max_budget_usd": 2.0,
                "estimated_tokens": 15000
            },

            "optimize_woocommerce_products": {
                "job_name": "Optimize WooCommerce Products",
                "job_description": "Audit and optimize all WooCommerce products for SEO, descriptions, images, and conversion",
                "category": "ECOMMERCE",
                "primary_agent": "ecommerce_agent",
                "supporting_agents": ["seo_optimizer", "brand_intelligence"],
                "required_tools": [
                    {"tool_name": "wordpress_woocommerce_products", "tool_type": "api", "estimated_calls": 50, "required": True},
                    {"tool_name": "wordpress_get_media", "tool_type": "api", "estimated_calls": 100, "required": True},
                    {"tool_name": "wordpress_yoast_seo", "tool_type": "api", "estimated_calls": 50, "required": True}
                ],
                "required_resources": [
                    {"resource_type": "API_QUOTA", "amount": 300.0, "unit": "requests"},
                    {"resource_type": "MEMORY", "amount": 1.0, "unit": "GB"}
                ],
                "max_budget_usd": 5.0,
                "estimated_tokens": 50000
            },

            "update_blog_content": {
                "job_name": "Update Blog Content for SEO",
                "job_description": "Audit and update existing blog posts for SEO optimization, readability, and brand consistency",
                "category": "MARKETING_BRAND",
                "primary_agent": "seo_optimizer",
                "supporting_agents": ["brand_intelligence", "content_writer"],
                "required_tools": [
                    {"tool_name": "wordpress_get_posts", "tool_type": "api", "estimated_calls": 1, "required": True},
                    {"tool_name": "wordpress_update_post", "tool_type": "api", "estimated_calls": 20, "required": True},
                    {"tool_name": "wordpress_yoast_seo", "tool_type": "api", "estimated_calls": 20, "required": True}
                ],
                "required_resources": [
                    {"resource_type": "API_QUOTA", "amount": 100.0, "unit": "requests"}
                ],
                "max_budget_usd": 3.0,
                "estimated_tokens": 35000
            },

            "monitor_site_performance": {
                "job_name": "WordPress Site Performance Monitoring",
                "job_description": "Monitor WordPress site performance, analyze metrics, and generate optimization recommendations",
                "category": "CORE_SECURITY",
                "primary_agent": "performance_monitor",
                "supporting_agents": ["security_compliance", "wordpress_specialist"],
                "required_tools": [
                    {"tool_name": "wordpress_get_site_stats", "tool_type": "api", "estimated_calls": 1, "required": True},
                    {"tool_name": "wordpress_get_site_info", "tool_type": "api", "estimated_calls": 1, "required": True}
                ],
                "required_resources": [
                    {"resource_type": "API_QUOTA", "amount": 10.0, "unit": "requests"}
                ],
                "max_budget_usd": 1.0,
                "estimated_tokens": 8000
            }
        }

        for job_key, job_data in examples.items():
            logger.info(f"\n   📌 {job_data['job_name']}")
            logger.info(f"      Category: {job_data['category']}")
            logger.info(f"      Tools: {len(job_data['required_tools'])}")
            logger.info(f"      Estimated Tokens: {job_data['estimated_tokens']:,}")
            logger.info(f"      Budget: ${job_data['max_budget_usd']:.2f}")

        # Save examples to file
        import json
        examples_file = project_root / "docs" / "wordpress_deployment_examples.json"
        with open(examples_file, "w") as f:
            json.dump(examples, f, indent=2)

        logger.info(f"\n✅ Saved examples to: {examples_file}")

        return examples

    def run_infrastructure_validation(self):
        """Run complete infrastructure validation."""

        logger.info("\n🔍 Running Infrastructure Validation...\n")

        # Check infrastructure status
        available_tools = self.validator.available_tools
        available_resources = self.validator.available_resources
        api_keys = self.validator.api_keys

        # Calculate readiness
        wordpress_tools = [t for t in available_tools if t.startswith("wordpress_")]
        total_tools = len(wordpress_tools)
        available_tool_count = sum(1 for t in wordpress_tools if available_tools[t].get("available", True))

        readiness_score = available_tool_count / max(total_tools, 1)

        logger.info("📊 Infrastructure Readiness Report:")
        logger.info(f"   Total WordPress Tools: {total_tools}")
        logger.info(f"   Available Tools: {available_tool_count}")
        logger.info(f"   Resources: {len(available_resources)}")
        logger.info(f"   API Keys Configured: {sum(1 for v in api_keys.values() if v)}/{len(api_keys)}")
        logger.info(f"   Readiness Score: {readiness_score:.1%}")

        if readiness_score >= 0.8:
            logger.info("\n✅ WordPress infrastructure is READY for deployment!")
        elif readiness_score >= 0.5:
            logger.info("\n⚠️  WordPress infrastructure is PARTIALLY ready")
        else:
            logger.info("\n❌ WordPress infrastructure needs configuration")

        return readiness_score

    def setup_complete(self):
        """Run complete WordPress infrastructure setup."""

        logger.info("=" * 80)
        logger.info("🚀 WordPress Infrastructure Setup for DevSkyy Deployment System")
        logger.info("=" * 80)

        # Step 1: Register tools
        self.register_wordpress_tools()

        # Step 2: Register resources
        self.register_wordpress_resources()

        # Step 3: Check and register API keys
        has_credentials = self.register_api_keys()

        # Step 4: Generate examples
        examples = self.generate_example_jobs()

        # Step 5: Validate infrastructure
        readiness = self.run_infrastructure_validation()

        # Final summary
        logger.info("\n" + "=" * 80)
        logger.info("📋 Setup Summary")
        logger.info("=" * 80)

        if has_credentials and readiness >= 0.8:
            logger.info("✅ WordPress infrastructure setup COMPLETE!")
            logger.info("✅ Ready to submit deployment jobs")
            logger.info("\n📖 Next Steps:")
            logger.info("   1. Update .env file with your actual WordPress credentials")
            logger.info("   2. Review example jobs in docs/wordpress_deployment_examples.json")
            logger.info("   3. Submit a job via API: POST /api/v1/deployment/jobs")
            logger.info("   4. Monitor approval workflow and deployment status")
        elif has_credentials:
            logger.info("⚠️  WordPress credentials found, but infrastructure incomplete")
            logger.info("   Run this script again after registering all tools")
        else:
            logger.info("❌ WordPress credentials NOT configured")
            logger.info("\n📖 Configuration Steps:")
            logger.info("   1. Edit .env file with your credentials:")
            logger.info("      - Add WORDPRESS_CLIENT_ID and WORDPRESS_CLIENT_SECRET")
            logger.info("      - OR add SKYY_ROSE_SITE_URL, SKYY_ROSE_USERNAME, SKYY_ROSE_PASSWORD")
            logger.info("   2. Run this script again: python scripts/wordpress/setup_wordpress_infrastructure.py")

        logger.info("=" * 80)

        return {
            "has_credentials": has_credentials,
            "readiness_score": readiness,
            "total_tools_registered": len([t for t in self.validator.available_tools if t.startswith("wordpress_")]),
            "example_jobs_created": len(examples)
        }


async def main():
    """Main entry point."""
    setup = WordPressInfrastructureSetup()
    result = setup.setup_complete()

    # Return exit code based on readiness
    if result["has_credentials"] and result["readiness_score"] >= 0.8:
        sys.exit(0)  # Success
    elif result["has_credentials"]:
        sys.exit(1)  # Credentials OK, but incomplete
    else:
        sys.exit(2)  # No credentials


if __name__ == "__main__":
    asyncio.run(main())
