#!/usr/bin/env python3
"""
Automated WordPress Site Builder from Brand Config
Reads brand configuration and automatically builds complete WordPress site
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from agent.wordpress.theme_builder import ElementorThemeBuilder
from agent.wordpress.automated_theme_uploader import (
    AutomatedThemeUploader,
    WordPressCredentials,
    UploadMethod,
)
from agent.wordpress.content_generator import ContentGenerator
from agent.wordpress.seo_optimizer import SEOOptimizer


class BrandConfigBuilder:
    """
    Automated WordPress builder using brand configuration files
    """

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.output_dir = Path("staging/themes/deployed")
        self.assets_dir = Path("assets/brand")

    def _load_config(self) -> dict[str, Any]:
        """Load brand configuration from JSON file"""
        try:
            with open(self.config_path) as f:
                config = json.load(f)
            print(f"✓ Loaded configuration: {self.config_path}")
            return config
        except FileNotFoundError:
            print(f"✗ Configuration file not found: {self.config_path}")
            print("\nCreate a config file using:")
            print("  cp config/brand-config.example.json config/my-brand.json")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON in config file: {e}")
            sys.exit(1)

    def _validate_config(self) -> bool:
        """Validate required configuration fields"""
        required_fields = [
            ("brand", "name"),
            ("colors", "primary"),
            ("theme", "type"),
        ]

        missing = []
        for section, field in required_fields:
            if section not in self.config:
                missing.append(f"{section}")
            elif field not in self.config[section]:
                missing.append(f"{section}.{field}")

        if missing:
            print(f"✗ Missing required config fields: {', '.join(missing)}")
            return False

        return True

    def _check_assets(self) -> dict[str, bool]:
        """Check which brand assets are available"""
        assets = self.config.get("assets", {})
        status = {}

        for key, path in assets.items():
            if isinstance(path, list):
                # Multiple assets (like hero images)
                status[key] = all(Path(p).exists() for p in path)
            else:
                status[key] = Path(path).exists()

        return status

    async def build_theme(self) -> dict[str, Any]:
        """
        Build WordPress theme from configuration
        """
        print("\n" + "=" * 60)
        print(f"Building WordPress Site: {self.config['brand']['name']}")
        print("=" * 60)
        print()

        # Validate config
        if not self._validate_config():
            sys.exit(1)

        # Check assets
        print("Checking brand assets...")
        asset_status = self._check_assets()
        for asset, exists in asset_status.items():
            status = "✓" if exists else "⚠"
            print(f"  {status} {asset}")
        print()

        # Initialize builder
        api_key = os.getenv("ANTHROPIC_API_KEY")
        builder = ElementorThemeBuilder(api_key=api_key)

        # Prepare brand info
        brand_info = {
            "name": self.config["brand"]["name"],
            "tagline": self.config["brand"].get("tagline", ""),
            "description": self.config["brand"].get("description", ""),
            "primary_color": self.config["colors"]["primary"],
            "secondary_color": self.config["colors"]["secondary"],
            "accent_color": self.config["colors"]["accent"],
            "font_heading": self.config["typography"]["heading_font"],
            "font_body": self.config["typography"]["body_font"],
            "logo_url": self.config["assets"].get("logo", ""),
            "industry": self.config["brand"].get("industry", "fashion"),
        }

        # Generate theme
        print("🎨 Generating theme with AI...")
        theme = await builder.generate_theme(
            brand_info=brand_info,
            theme_type=self.config["theme"]["type"],
            pages=self.config.get("pages", ["home", "shop", "about", "contact"]),
            include_woocommerce=self.config["features"].get("woocommerce", True),
            include_seo=True,
            responsive=True,
        )

        print(f"✓ Theme generated: {theme['name']}")
        print(f"  - Pages: {len(theme['pages'])}")
        print()

        # Inject assets into theme
        print("📦 Adding brand assets to theme...")
        theme = self._inject_assets(theme)
        print("✓ Assets integrated")
        print()

        # Optimize colors and typography
        print("🎨 Optimizing design with AI...")
        theme = await self._optimize_design(builder, theme)
        print("✓ Design optimized")
        print()

        # Generate SEO metadata
        print("🔍 Generating SEO metadata...")
        theme = await self._generate_seo(builder, theme)
        print("✓ SEO metadata generated")
        print()

        # Generate content
        if api_key:
            print("✍️  Generating page content with AI...")
            theme = await self._generate_content(theme)
            print("✓ Content generated")
            print()

        # Export theme
        print("💾 Exporting theme files...")
        export_result = await builder.export_theme(
            theme=theme,
            format="elementor_json",
            output_dir=str(self.output_dir),
        )

        print(f"✓ Theme exported: {export_result['path']}")
        print(f"  - Format: {export_result['format']}")
        print(f"  - Size: {export_result.get('size_mb', 0):.2f} MB")
        print()

        return {
            "theme": theme,
            "export_path": export_result["path"],
            "export_result": export_result,
        }

    def _inject_assets(self, theme: dict[str, Any]) -> dict[str, Any]:
        """Inject brand assets (logo, images) into theme"""
        assets = self.config.get("assets", {})

        # Add logo
        if "logo" in assets and Path(assets["logo"]).exists():
            theme["logo"] = assets["logo"]

        # Add hero images
        if "hero_images" in assets:
            theme["hero_images"] = [
                img for img in assets["hero_images"] if Path(img).exists()
            ]

        # Add to each page's data
        for page in theme.get("pages", []):
            if page["type"] == "home" and "hero_images" in theme:
                page["hero_images"] = theme["hero_images"]

        return theme

    async def _optimize_design(
        self, builder: ElementorThemeBuilder, theme: dict[str, Any]
    ) -> dict[str, Any]:
        """Optimize colors and typography with AI"""
        # Optimize color palette
        optimized_colors = await builder.optimize_color_palette(
            theme=theme,
            target_audience=self.config["brand"].get(
                "target_audience", "fashion consumers"
            ),
            conversion_goal="increase engagement and sales",
        )

        # Optimize typography
        optimized_fonts = await builder.optimize_typography(
            theme=theme,
            readability_score_target=85,
            brand_personality=self.config["theme"].get("layout_style", "elegant"),
        )

        return theme

    async def _generate_seo(
        self, builder: ElementorThemeBuilder, theme: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate SEO metadata for all pages"""
        seo_config = self.config.get("seo", {})

        seo_data = await builder.generate_seo_metadata(
            theme=theme,
            target_keywords=seo_config.get("keywords", []),
            site_title=seo_config.get("site_title", self.config["brand"]["name"]),
            meta_description=seo_config.get(
                "meta_description", self.config["brand"].get("description", "")
            ),
        )

        theme["seo"] = seo_data
        return theme

    async def _generate_content(self, theme: dict[str, Any]) -> dict[str, Any]:
        """Generate page content with AI"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return theme

        generator = ContentGenerator(api_key=api_key)

        brand_context = {
            "name": self.config["brand"]["name"],
            "description": self.config["brand"].get("description", ""),
            "industry": self.config["brand"].get("industry", "fashion"),
        }

        # Generate content for each page
        for page in theme.get("pages", []):
            content = await generator.generate_page_content(
                page_type=page["type"], brand_context=brand_context
            )
            page["ai_generated_content"] = content

        return theme

    async def deploy_theme(self, theme_path: str) -> dict[str, Any]:
        """
        Deploy theme to WordPress site
        """
        deployment_config = self.config.get("deployment", {})

        wp_url = deployment_config.get("wordpress_url") or os.getenv("WP_SITE_URL")
        if not wp_url:
            print("⚠ No WordPress URL configured. Skipping deployment.")
            print("  Set 'deployment.wordpress_url' in config or WP_SITE_URL env var")
            return {"deployed": False, "reason": "no_url"}

        print("\n" + "=" * 60)
        print("Deploying to WordPress")
        print("=" * 60)
        print()

        # Get credentials
        credentials = WordPressCredentials(
            site_url=wp_url,
            username=os.getenv("WP_USERNAME", "admin"),
            password=os.getenv("WP_PASSWORD", ""),
            application_password=os.getenv("WP_APP_PASSWORD"),
        )

        # Deploy method
        deploy_method_name = deployment_config.get(
            "deploy_method", "wordpress_rest_api"
        )
        deploy_method = UploadMethod[deploy_method_name.upper()]

        # Upload
        uploader = AutomatedThemeUploader()

        print(f"📤 Uploading to {wp_url}...")
        print(f"   Method: {deploy_method.value}")
        print()

        result = await uploader.deploy_theme(
            theme_path=theme_path,
            credentials=credentials,
            upload_method=deploy_method,
            activate_after_upload=deployment_config.get("auto_activate", False),
            backup_existing=deployment_config.get("backup_before_deploy", True),
            validate_before_activate=True,
        )

        if result.success:
            print("✓ Theme deployed successfully!")
            print(f"  - Deployment ID: {result.deployment_id}")
            print(f"  - Status: {result.status.value}")
            print()
            if not deployment_config.get("auto_activate", False):
                print("⚠ Theme uploaded but not activated (manual activation required)")
                print("  Go to WordPress admin → Appearance → Themes")
        else:
            print(f"✗ Deployment failed: {result.error_message}")

        return {"deployed": result.success, "result": result}

    def generate_summary(self, build_result: dict[str, Any]) -> str:
        """Generate summary report"""
        theme = build_result["theme"]
        export_path = build_result["export_path"]

        summary = f"""
{'=' * 60}
Build Summary: {self.config['brand']['name']}
{'=' * 60}

Theme Details:
  - Name: {theme['name']}
  - Type: {self.config['theme']['type']}
  - Pages: {len(theme.get('pages', []))}
  - WooCommerce: {'Yes' if self.config['features'].get('woocommerce') else 'No'}

Export Location:
  - Path: {export_path}
  - Size: {build_result['export_result'].get('size_mb', 0):.2f} MB

Next Steps:
  1. Review theme files in: {export_path}
  2. Test theme on staging WordPress site
  3. Deploy to production when ready

Deploy Command:
  python3 scripts/auto_build_wp.py --config {self.config_path} --deploy
"""
        return summary


async def main():
    """
    Main function
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Build WordPress site from brand configuration"
    )
    parser.add_argument(
        "--config",
        "-c",
        default="config/brand-config.json",
        help="Path to brand configuration JSON file",
    )
    parser.add_argument(
        "--deploy", "-d", action="store_true", help="Deploy to WordPress after build"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output directory for theme files (default: staging/themes/deployed)",
    )

    args = parser.parse_args()

    # Build theme
    builder = BrandConfigBuilder(args.config)
    build_result = await builder.build_theme()

    # Print summary
    print(builder.generate_summary(build_result))

    # Deploy if requested
    if args.deploy:
        await builder.deploy_theme(build_result["export_path"])

    print("\n✓ Done!")


if __name__ == "__main__":
    asyncio.run(main())
