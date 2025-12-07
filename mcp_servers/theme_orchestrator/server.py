"""
WordPress Theme Orchestrator MCP Server

Full-featured MCP server for WordPress theme orchestration:
- Generate complete WordPress themes with Elementor support
- Apply SkyyRose brand guidelines automatically
- Validate theme structure and WordPress compliance
- Package themes for deployment
- Deploy to WordPress sites via REST API or SFTP
- Coordinate with WordPress MCP for site operations

Usage:
    # Run standalone
    python -m mcp_servers.theme_orchestrator

    # Or import and use
    from mcp_servers.theme_orchestrator import create_mcp_server
    server = create_mcp_server()
"""

import asyncio
from datetime import datetime
import json
import logging
from pathlib import Path
import tempfile
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool


# Import theme building components
try:
    from agent.wordpress.automated_theme_uploader import UploadMethod
    from agent.wordpress.theme_builder import ElementorThemeBuilder
    from agent.wordpress.theme_builder_orchestrator import (
        BuildStatus,
        ThemeBuilderOrchestrator,
        ThemeBuildRequest,
        ThemeType,
    )

    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False

try:
    from config.wordpress_credentials import (
        WordPressCredentials,
        wordpress_credentials_manager,
    )

    CREDENTIALS_AVAILABLE = True
except ImportError:
    CREDENTIALS_AVAILABLE = False

try:
    from core.logging import LogCategory, enterprise_logger

    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


class ThemeOrchestratorMCP:
    """
    MCP Server for WordPress Theme Orchestration

    Exposes theme building tools via standard MCP protocol:
    - generate_theme: Create complete WordPress themes
    - validate_theme: Check theme structure and compliance
    - package_theme: Create deployable ZIP packages
    - deploy_theme: Upload and activate on WordPress sites
    - get_build_status: Check ongoing build progress
    - list_theme_types: Available theme templates
    - get_brand_guidelines: SkyyRose brand configuration
    """

    def __init__(self):
        """Initialize Theme Orchestrator MCP Server."""
        self.server = Server("theme-orchestrator")

        # Initialize orchestrator if available
        if ORCHESTRATOR_AVAILABLE:
            self.orchestrator = ThemeBuilderOrchestrator()
            self.elementor_builder = ElementorThemeBuilder()
        else:
            self.orchestrator = None
            self.elementor_builder = None

        # Track active builds
        self.active_builds: dict[str, dict[str, Any]] = {}

        self._register_handlers()
        logger.info("Theme Orchestrator MCP Server initialized")

    def _register_handlers(self) -> None:
        """Register all MCP tool handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List all theme orchestration tools."""
            return [
                # Core Theme Generation
                Tool(
                    name="generate_theme",
                    description="Generate a complete WordPress theme with Elementor support based on brand guidelines and theme type",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "theme_name": {
                                "type": "string",
                                "description": "Name for the generated theme (e.g., 'SkyyRose Luxury 2025')",
                            },
                            "theme_type": {
                                "type": "string",
                                "enum": [
                                    "luxury_fashion",
                                    "streetwear",
                                    "minimalist",
                                    "ecommerce",
                                    "blog",
                                    "portfolio",
                                    "corporate",
                                ],
                                "default": "luxury_fashion",
                                "description": "Type of theme template to use",
                            },
                            "brand_guidelines": {
                                "type": "object",
                                "description": "Optional custom brand guidelines (uses SkyyRose defaults if not provided)",
                                "properties": {
                                    "colors": {
                                        "type": "object",
                                        "properties": {
                                            "primary": {"type": "string"},
                                            "secondary": {"type": "string"},
                                            "accent": {"type": "string"},
                                            "background": {"type": "string"},
                                            "text": {"type": "string"},
                                        },
                                    },
                                    "typography": {
                                        "type": "object",
                                        "properties": {
                                            "headings": {"type": "string"},
                                            "body": {"type": "string"},
                                            "accent": {"type": "string"},
                                        },
                                    },
                                    "brand_name": {"type": "string"},
                                    "tagline": {"type": "string"},
                                },
                            },
                            "pages": {
                                "type": "array",
                                "items": {"type": "string"},
                                "default": ["home", "shop", "product", "about", "contact", "blog"],
                                "description": "Pages to generate layouts for",
                            },
                            "include_elementor_widgets": {
                                "type": "boolean",
                                "default": True,
                                "description": "Include custom Elementor widgets",
                            },
                            "include_woocommerce": {
                                "type": "boolean",
                                "default": True,
                                "description": "Include WooCommerce integration",
                            },
                        },
                        "required": ["theme_name"],
                    },
                ),
                # Theme Validation
                Tool(
                    name="validate_theme",
                    description="Validate a generated theme for WordPress compliance, file structure, and best practices",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "theme_path": {
                                "type": "string",
                                "description": "Path to the theme directory to validate",
                            },
                            "strict_mode": {
                                "type": "boolean",
                                "default": False,
                                "description": "Enable strict validation (fails on warnings)",
                            },
                        },
                        "required": ["theme_path"],
                    },
                ),
                # Theme Packaging
                Tool(
                    name="package_theme",
                    description="Package a validated theme into a deployable ZIP file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "theme_path": {
                                "type": "string",
                                "description": "Path to the theme directory",
                            },
                            "output_path": {
                                "type": "string",
                                "description": "Path for the output ZIP file (optional)",
                            },
                            "include_readme": {
                                "type": "boolean",
                                "default": True,
                                "description": "Include installation README",
                            },
                        },
                        "required": ["theme_path"],
                    },
                ),
                # Theme Deployment
                Tool(
                    name="deploy_theme",
                    description="Deploy a packaged theme to a WordPress site",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "theme_package": {
                                "type": "string",
                                "description": "Path to the theme ZIP package",
                            },
                            "site_key": {
                                "type": "string",
                                "default": "skyy_rose",
                                "description": "Site configuration key (e.g., 'skyy_rose')",
                            },
                            "upload_method": {
                                "type": "string",
                                "enum": ["rest_api", "sftp", "ssh"],
                                "default": "rest_api",
                                "description": "Method to upload the theme",
                            },
                            "activate_after_deploy": {
                                "type": "boolean",
                                "default": False,
                                "description": "Activate theme immediately after deployment",
                            },
                        },
                        "required": ["theme_package"],
                    },
                ),
                # Full Pipeline
                Tool(
                    name="build_and_deploy",
                    description="Complete pipeline: generate, validate, package, and deploy a theme in one operation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "theme_name": {
                                "type": "string",
                                "description": "Name for the theme",
                            },
                            "theme_type": {
                                "type": "string",
                                "enum": [
                                    "luxury_fashion",
                                    "streetwear",
                                    "minimalist",
                                    "ecommerce",
                                ],
                                "default": "luxury_fashion",
                            },
                            "site_key": {
                                "type": "string",
                                "default": "skyy_rose",
                            },
                            "activate_after_deploy": {
                                "type": "boolean",
                                "default": False,
                            },
                            "customizations": {
                                "type": "object",
                                "description": "Custom overrides for theme generation",
                            },
                        },
                        "required": ["theme_name"],
                    },
                ),
                # Build Status
                Tool(
                    name="get_build_status",
                    description="Get the status of an ongoing or completed theme build",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "build_id": {
                                "type": "string",
                                "description": "Build ID returned from generate_theme or build_and_deploy",
                            },
                        },
                        "required": ["build_id"],
                    },
                ),
                # Theme Types
                Tool(
                    name="list_theme_types",
                    description="List all available theme types with their descriptions and features",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                # Brand Guidelines
                Tool(
                    name="get_brand_guidelines",
                    description="Get the default SkyyRose brand guidelines (colors, typography, style)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_full_config": {
                                "type": "boolean",
                                "default": False,
                                "description": "Include full configuration details",
                            },
                        },
                    },
                ),
                # System Status
                Tool(
                    name="get_system_status",
                    description="Get the current status of the theme orchestration system",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                # Elementor Widgets
                Tool(
                    name="generate_elementor_widget",
                    description="Generate a custom Elementor widget for the theme",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "widget_type": {
                                "type": "string",
                                "enum": [
                                    "product_showcase",
                                    "brand_hero",
                                    "collection_grid",
                                    "testimonial_slider",
                                    "newsletter_signup",
                                    "instagram_feed",
                                ],
                                "description": "Type of Elementor widget to generate",
                            },
                            "widget_name": {
                                "type": "string",
                                "description": "Custom name for the widget",
                            },
                            "styling": {
                                "type": "object",
                                "description": "Custom styling options",
                            },
                        },
                        "required": ["widget_type"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Route tool calls to appropriate handlers."""
            try:
                if name == "generate_theme":
                    result = await self._handle_generate_theme(arguments)
                elif name == "validate_theme":
                    result = await self._handle_validate_theme(arguments)
                elif name == "package_theme":
                    result = await self._handle_package_theme(arguments)
                elif name == "deploy_theme":
                    result = await self._handle_deploy_theme(arguments)
                elif name == "build_and_deploy":
                    result = await self._handle_build_and_deploy(arguments)
                elif name == "get_build_status":
                    result = await self._handle_get_build_status(arguments)
                elif name == "list_theme_types":
                    result = await self._handle_list_theme_types(arguments)
                elif name == "get_brand_guidelines":
                    result = await self._handle_get_brand_guidelines(arguments)
                elif name == "get_system_status":
                    result = await self._handle_get_system_status(arguments)
                elif name == "generate_elementor_widget":
                    result = await self._handle_generate_elementor_widget(arguments)
                else:
                    result = {"error": f"Unknown tool: {name}"}

                return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({"error": str(e), "tool": name}, indent=2),
                    )
                ]

    async def _handle_generate_theme(self, args: dict[str, Any]) -> dict[str, Any]:
        """Generate a complete WordPress theme."""
        theme_name = args["theme_name"]
        theme_type = args.get("theme_type", "luxury_fashion")
        brand_guidelines = args.get("brand_guidelines", self._get_skyy_rose_defaults())
        pages = args.get("pages", ["home", "shop", "product", "about", "contact", "blog"])
        include_elementor = args.get("include_elementor_widgets", True)
        include_woocommerce = args.get("include_woocommerce", True)

        build_id = f"build_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{theme_name.replace(' ', '_')}"

        # Track build
        self.active_builds[build_id] = {
            "status": "generating",
            "theme_name": theme_name,
            "started_at": datetime.now().isoformat(),
            "progress": [],
        }

        try:
            if self.elementor_builder:
                # Use full orchestrator
                brand_info = {
                    "name": brand_guidelines.get("brand_name", "SkyyRose"),
                    "tagline": brand_guidelines.get("tagline", "Luxury Streetwear"),
                    "primary_color": brand_guidelines.get("colors", {}).get("primary", "#1a1a1a"),
                    "secondary_color": brand_guidelines.get("colors", {}).get("secondary", "#d4af37"),
                    **brand_guidelines,
                }

                result = await self.elementor_builder.generate_theme(
                    brand_info=brand_info,
                    theme_type=theme_type,
                    pages=pages,
                )

                if result.get("success"):
                    # Create theme directory
                    theme_dir = Path(tempfile.mkdtemp(prefix=f"theme_{theme_name.replace(' ', '_')}_"))

                    self.active_builds[build_id]["status"] = "completed"
                    self.active_builds[build_id]["theme_path"] = str(theme_dir)
                    self.active_builds[build_id]["completed_at"] = datetime.now().isoformat()

                    return {
                        "success": True,
                        "build_id": build_id,
                        "theme_name": theme_name,
                        "theme_type": theme_type,
                        "theme_path": str(theme_dir),
                        "theme_config": result.get("theme", {}),
                        "pages_generated": pages,
                        "features": {
                            "elementor_widgets": include_elementor,
                            "woocommerce": include_woocommerce,
                        },
                        "next_steps": [
                            "Use validate_theme to check the generated theme",
                            "Use package_theme to create a ZIP for deployment",
                            "Use deploy_theme to upload to WordPress",
                        ],
                    }
                else:
                    self.active_builds[build_id]["status"] = "failed"
                    self.active_builds[build_id]["error"] = result.get("error", "Unknown error")
                    return {"success": False, "error": result.get("error", "Theme generation failed")}
            else:
                # Fallback: Generate basic theme structure
                return await self._generate_basic_theme(theme_name, theme_type, brand_guidelines, build_id)

        except Exception as e:
            self.active_builds[build_id]["status"] = "failed"
            self.active_builds[build_id]["error"] = str(e)
            raise

    async def _generate_basic_theme(
        self, theme_name: str, theme_type: str, brand_guidelines: dict, build_id: str
    ) -> dict[str, Any]:
        """Generate a basic theme when full orchestrator is not available."""
        theme_dir = Path(tempfile.mkdtemp(prefix=f"theme_{theme_name.replace(' ', '_')}_"))

        # Generate style.css
        style_content = f"""/*
Theme Name: {theme_name}
Description: Custom {theme_type} theme generated by SkyyRose Theme Orchestrator
Version: 1.0.0
Author: DevSkyy Platform
Text Domain: {theme_name.lower().replace(' ', '-')}
*/
"""
        (theme_dir / "style.css").write_text(style_content)

        # Generate functions.php
        functions_content = self._generate_functions_php(theme_name, brand_guidelines)
        (theme_dir / "functions.php").write_text(functions_content)

        # Generate index.php
        index_content = self._generate_index_php()
        (theme_dir / "index.php").write_text(index_content)

        self.active_builds[build_id]["status"] = "completed"
        self.active_builds[build_id]["theme_path"] = str(theme_dir)

        return {
            "success": True,
            "build_id": build_id,
            "theme_name": theme_name,
            "theme_path": str(theme_dir),
            "mode": "basic",
            "note": "Generated basic theme structure (full orchestrator not available)",
        }

    def _generate_functions_php(self, theme_name: str, brand_guidelines: dict) -> str:
        """Generate WordPress functions.php."""
        slug = theme_name.lower().replace(" ", "_")
        return f"""<?php
/**
 * {theme_name} functions and definitions
 * Generated by SkyyRose Theme Orchestrator
 */

if (!defined('ABSPATH')) {{
    exit;
}}

// Theme setup
function {slug}_setup() {{
    add_theme_support('post-thumbnails');
    add_theme_support('title-tag');
    add_theme_support('custom-logo');
    add_theme_support('woocommerce');
    add_theme_support('wc-product-gallery-zoom');
    add_theme_support('wc-product-gallery-lightbox');
    add_theme_support('wc-product-gallery-slider');

    register_nav_menus(array(
        'primary' => __('Primary Menu', '{slug}'),
        'footer' => __('Footer Menu', '{slug}'),
    ));
}}
add_action('after_setup_theme', '{slug}_setup');

// Enqueue scripts and styles
function {slug}_scripts() {{
    wp_enqueue_style('{slug}-style', get_stylesheet_uri(), array(), '1.0.0');
}}
add_action('wp_enqueue_scripts', '{slug}_scripts');
"""

    def _generate_index_php(self) -> str:
        """Generate WordPress index.php."""
        return """<?php get_header(); ?>

<main id="main" class="site-main">
    <?php if (have_posts()) : ?>
        <?php while (have_posts()) : the_post(); ?>
            <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
                <header class="entry-header">
                    <?php the_title('<h1 class="entry-title">', '</h1>'); ?>
                </header>
                <div class="entry-content">
                    <?php the_content(); ?>
                </div>
            </article>
        <?php endwhile; ?>
    <?php endif; ?>
</main>

<?php get_footer(); ?>
"""

    async def _handle_validate_theme(self, args: dict[str, Any]) -> dict[str, Any]:
        """Validate a theme directory."""
        theme_path = Path(args["theme_path"])
        strict_mode = args.get("strict_mode", False)

        if not theme_path.exists():
            return {"valid": False, "error": f"Theme path does not exist: {theme_path}"}

        issues = []
        warnings = []

        # Required files check
        required_files = ["style.css", "index.php"]
        for file in required_files:
            if not (theme_path / file).exists():
                issues.append(f"Missing required file: {file}")

        # Recommended files check
        recommended_files = ["functions.php", "header.php", "footer.php", "screenshot.png"]
        for file in recommended_files:
            if not (theme_path / file).exists():
                warnings.append(f"Missing recommended file: {file}")

        # Validate style.css header
        style_css = theme_path / "style.css"
        if style_css.exists():
            content = style_css.read_text()[:500]
            if "Theme Name:" not in content:
                issues.append("style.css missing 'Theme Name:' header")

        is_valid = len(issues) == 0
        if strict_mode and warnings:
            is_valid = False

        return {
            "valid": is_valid,
            "theme_path": str(theme_path),
            "issues": issues,
            "warnings": warnings,
            "files_checked": required_files + recommended_files,
        }

    async def _handle_package_theme(self, args: dict[str, Any]) -> dict[str, Any]:
        """Package theme into a ZIP file."""
        import shutil

        theme_path = Path(args["theme_path"])
        output_path = args.get("output_path")

        if not theme_path.exists():
            return {"success": False, "error": f"Theme path does not exist: {theme_path}"}

        # Determine output path
        if output_path:
            zip_path = Path(output_path)
        else:
            zip_path = theme_path.parent / f"{theme_path.name}.zip"

        # Create ZIP
        try:
            shutil.make_archive(str(zip_path.with_suffix("")), "zip", theme_path.parent, theme_path.name)

            return {
                "success": True,
                "package_path": str(zip_path),
                "size_bytes": zip_path.stat().st_size if zip_path.exists() else 0,
                "theme_name": theme_path.name,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_deploy_theme(self, args: dict[str, Any]) -> dict[str, Any]:
        """Deploy theme to WordPress site."""
        theme_package = args["theme_package"]
        site_key = args.get("site_key", "skyy_rose")
        upload_method = args.get("upload_method", "rest_api")
        activate = args.get("activate_after_deploy", False)

        if not CREDENTIALS_AVAILABLE:
            return {
                "success": False,
                "error": "WordPress credentials not configured",
                "hint": "Set up credentials in config/wordpress_credentials.py",
            }

        if not Path(theme_package).exists():
            return {"success": False, "error": f"Theme package not found: {theme_package}"}

        try:
            credentials = wordpress_credentials_manager.get_credentials(site_key)
            if not credentials:
                return {"success": False, "error": f"No credentials found for site: {site_key}"}

            if self.orchestrator:
                # Use full orchestrator deployment
                result = await self.orchestrator.theme_uploader.deploy_theme(
                    theme_package=theme_package,
                    credentials=credentials,
                    upload_method=UploadMethod(upload_method.upper()),
                    activate_after_deploy=activate,
                )
                return {
                    "success": result.success,
                    "site_url": credentials.site_url,
                    "theme_activated": activate and result.success,
                    "message": result.message if hasattr(result, "message") else "Deployment completed",
                }
            else:
                return {
                    "success": False,
                    "error": "Full orchestrator not available",
                    "credentials_found": True,
                    "site_url": credentials.site_url,
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_build_and_deploy(self, args: dict[str, Any]) -> dict[str, Any]:
        """Complete build and deploy pipeline."""
        theme_name = args["theme_name"]
        theme_type = args.get("theme_type", "luxury_fashion")
        site_key = args.get("site_key", "skyy_rose")
        activate = args.get("activate_after_deploy", False)
        customizations = args.get("customizations", {})

        steps = []

        # Step 1: Generate
        generate_result = await self._handle_generate_theme({
            "theme_name": theme_name,
            "theme_type": theme_type,
            "brand_guidelines": {**self._get_skyy_rose_defaults(), **customizations},
        })
        steps.append({"step": "generate", "result": generate_result})

        if not generate_result.get("success"):
            return {"success": False, "failed_at": "generate", "steps": steps}

        theme_path = generate_result["theme_path"]

        # Step 2: Validate
        validate_result = await self._handle_validate_theme({"theme_path": theme_path})
        steps.append({"step": "validate", "result": validate_result})

        if not validate_result.get("valid"):
            return {"success": False, "failed_at": "validate", "steps": steps}

        # Step 3: Package
        package_result = await self._handle_package_theme({"theme_path": theme_path})
        steps.append({"step": "package", "result": package_result})

        if not package_result.get("success"):
            return {"success": False, "failed_at": "package", "steps": steps}

        # Step 4: Deploy
        deploy_result = await self._handle_deploy_theme({
            "theme_package": package_result["package_path"],
            "site_key": site_key,
            "activate_after_deploy": activate,
        })
        steps.append({"step": "deploy", "result": deploy_result})

        return {
            "success": deploy_result.get("success", False),
            "build_id": generate_result.get("build_id"),
            "theme_name": theme_name,
            "steps": steps,
        }

    async def _handle_get_build_status(self, args: dict[str, Any]) -> dict[str, Any]:
        """Get build status."""
        build_id = args["build_id"]

        if build_id in self.active_builds:
            return self.active_builds[build_id]

        if self.orchestrator:
            result = self.orchestrator.get_build_status(build_id)
            if result:
                return {
                    "build_id": result.build_id,
                    "status": result.status.value,
                    "theme_name": result.request.theme_name,
                    "theme_path": result.theme_path,
                    "build_log": result.build_log[-10:],  # Last 10 entries
                    "error_message": result.error_message,
                }

        return {"error": f"Build not found: {build_id}"}

    async def _handle_list_theme_types(self, args: dict[str, Any]) -> dict[str, Any]:
        """List available theme types."""
        return {
            "theme_types": [
                {
                    "id": "luxury_fashion",
                    "name": "Luxury Fashion",
                    "description": "Elegant, sophisticated design for luxury brands",
                    "features": ["woocommerce", "elementor", "custom-header", "gallery"],
                    "colors": {"primary": "#1a1a1a", "secondary": "#d4af37"},
                },
                {
                    "id": "streetwear",
                    "name": "Streetwear",
                    "description": "Bold, dynamic design for streetwear brands",
                    "features": ["woocommerce", "social-media", "video-backgrounds"],
                    "colors": {"primary": "#000000", "secondary": "#ff6b35"},
                },
                {
                    "id": "minimalist",
                    "name": "Minimalist",
                    "description": "Clean, focused design with minimal elements",
                    "features": ["responsive", "fast-loading", "accessibility"],
                    "colors": {"primary": "#2c3e50", "secondary": "#ecf0f1"},
                },
                {
                    "id": "ecommerce",
                    "name": "E-commerce",
                    "description": "Conversion-optimized online store design",
                    "features": ["woocommerce", "product-filters", "wishlist", "reviews"],
                    "colors": {"primary": "#e74c3c", "secondary": "#34495e"},
                },
            ]
        }

    async def _handle_get_brand_guidelines(self, args: dict[str, Any]) -> dict[str, Any]:
        """Get SkyyRose brand guidelines."""
        include_full = args.get("include_full_config", False)

        guidelines = self._get_skyy_rose_defaults()

        if include_full:
            guidelines["brand_rules"] = {
                "name_format": "SkyyRose (one word, capital S and R)",
                "incorrect_formats": ["Skyy Rose", "skyy rose", "SKYYROSE", "SkyRose"],
                "domain": "skyyrose.co (never .com)",
                "tone": "Luxury, elevated, boutique-ready",
                "prohibited": ["hyphy slang", "discount language", ".com URLs"],
            }

        return guidelines

    async def _handle_get_system_status(self, args: dict[str, Any]) -> dict[str, Any]:
        """Get system status."""
        status = {
            "orchestrator_available": self.orchestrator is not None,
            "elementor_builder_available": self.elementor_builder is not None,
            "credentials_available": CREDENTIALS_AVAILABLE,
            "active_builds": len(self.active_builds),
            "active_build_ids": list(self.active_builds.keys()),
        }

        if self.orchestrator:
            status["orchestrator_status"] = self.orchestrator.get_system_status()

        return status

    async def _handle_generate_elementor_widget(self, args: dict[str, Any]) -> dict[str, Any]:
        """Generate a custom Elementor widget."""
        widget_type = args["widget_type"]
        widget_name = args.get("widget_name", widget_type.replace("_", " ").title())
        styling = args.get("styling", {})

        widget_templates = {
            "product_showcase": self._generate_product_showcase_widget,
            "brand_hero": self._generate_brand_hero_widget,
            "collection_grid": self._generate_collection_grid_widget,
            "testimonial_slider": self._generate_testimonial_slider_widget,
            "newsletter_signup": self._generate_newsletter_widget,
            "instagram_feed": self._generate_instagram_widget,
        }

        if widget_type not in widget_templates:
            return {"error": f"Unknown widget type: {widget_type}"}

        widget_code = widget_templates[widget_type](widget_name, styling)

        return {
            "success": True,
            "widget_type": widget_type,
            "widget_name": widget_name,
            "php_code": widget_code,
            "installation": "Add to your theme's functions.php or create a custom plugin",
        }

    def _generate_product_showcase_widget(self, name: str, styling: dict) -> str:
        """Generate product showcase Elementor widget."""
        return f"""<?php
/**
 * {name} - Custom Elementor Widget
 * Generated by SkyyRose Theme Orchestrator
 */

class {name.replace(' ', '_')}_Widget extends \\Elementor\\Widget_Base {{
    public function get_name() {{ return '{name.lower().replace(' ', '_')}'; }}
    public function get_title() {{ return __('{name}', 'skyyrose'); }}
    public function get_icon() {{ return 'eicon-products'; }}
    public function get_categories() {{ return ['general']; }}

    protected function render() {{
        $settings = $this->get_settings_for_display();
        echo '<div class="skyyrose-product-showcase">';
        echo do_shortcode('[products limit="8" columns="4"]');
        echo '</div>';
    }}
}}
"""

    def _generate_brand_hero_widget(self, name: str, styling: dict) -> str:
        """Generate brand hero Elementor widget."""
        return f"""<?php
/**
 * {name} - Custom Elementor Widget
 */

class {name.replace(' ', '_')}_Widget extends \\Elementor\\Widget_Base {{
    public function get_name() {{ return '{name.lower().replace(' ', '_')}'; }}
    public function get_title() {{ return __('{name}', 'skyyrose'); }}
    public function get_icon() {{ return 'eicon-banner'; }}
    public function get_categories() {{ return ['general']; }}

    protected function render() {{
        ?>
        <div class="skyyrose-hero">
            <h1>Welcome to SkyyRose</h1>
            <p>Luxury Streetwear, Oakland Authenticity</p>
            <a href="/shop" class="btn-primary">Shop Now</a>
        </div>
        <?php
    }}
}}
"""

    def _generate_collection_grid_widget(self, name: str, styling: dict) -> str:
        """Generate collection grid widget."""
        return f"""<?php
class {name.replace(' ', '_')}_Widget extends \\Elementor\\Widget_Base {{
    public function get_name() {{ return '{name.lower().replace(' ', '_')}'; }}
    public function get_title() {{ return __('{name}', 'skyyrose'); }}
    public function get_icon() {{ return 'eicon-gallery-grid'; }}
    public function get_categories() {{ return ['general']; }}

    protected function render() {{
        $categories = get_terms('product_cat', ['hide_empty' => true, 'number' => 6]);
        echo '<div class="skyyrose-collection-grid">';
        foreach ($categories as $cat) {{
            echo '<div class="collection-item"><a href="' . get_term_link($cat) . '">' . $cat->name . '</a></div>';
        }}
        echo '</div>';
    }}
}}
"""

    def _generate_testimonial_slider_widget(self, name: str, styling: dict) -> str:
        """Generate testimonial slider widget."""
        return f"""<?php
class {name.replace(' ', '_')}_Widget extends \\Elementor\\Widget_Base {{
    public function get_name() {{ return '{name.lower().replace(' ', '_')}'; }}
    public function get_title() {{ return __('{name}', 'skyyrose'); }}
    public function get_icon() {{ return 'eicon-testimonial-carousel'; }}
    public function get_categories() {{ return ['general']; }}

    protected function render() {{
        echo '<div class="skyyrose-testimonials swiper">';
        echo '<div class="swiper-wrapper"></div>';
        echo '<div class="swiper-pagination"></div>';
        echo '</div>';
    }}
}}
"""

    def _generate_newsletter_widget(self, name: str, styling: dict) -> str:
        """Generate newsletter signup widget."""
        return f"""<?php
class {name.replace(' ', '_')}_Widget extends \\Elementor\\Widget_Base {{
    public function get_name() {{ return '{name.lower().replace(' ', '_')}'; }}
    public function get_title() {{ return __('{name}', 'skyyrose'); }}
    public function get_icon() {{ return 'eicon-email-field'; }}
    public function get_categories() {{ return ['general']; }}

    protected function render() {{
        ?>
        <div class="skyyrose-newsletter">
            <h3>Join Our Community</h3>
            <form class="newsletter-form">
                <input type="email" placeholder="Your email" required>
                <button type="submit">Subscribe</button>
            </form>
        </div>
        <?php
    }}
}}
"""

    def _generate_instagram_widget(self, name: str, styling: dict) -> str:
        """Generate Instagram feed widget."""
        return f"""<?php
class {name.replace(' ', '_')}_Widget extends \\Elementor\\Widget_Base {{
    public function get_name() {{ return '{name.lower().replace(' ', '_')}'; }}
    public function get_title() {{ return __('{name}', 'skyyrose'); }}
    public function get_icon() {{ return 'eicon-instagram-gallery'; }}
    public function get_categories() {{ return ['general']; }}

    protected function render() {{
        echo '<div class="skyyrose-instagram">';
        echo '<h3>Follow @SkyyRose</h3>';
        echo '<div class="instagram-grid"></div>';
        echo '</div>';
    }}
}}
"""

    def _get_skyy_rose_defaults(self) -> dict[str, Any]:
        """Get default SkyyRose brand guidelines."""
        return {
            "brand_name": "SkyyRose",
            "tagline": "Luxury Streetwear, Oakland Authenticity",
            "domain": "skyyrose.co",
            "colors": {
                "primary": "#1a1a1a",
                "secondary": "#d4af37",
                "accent": "#8b7355",
                "background": "#ffffff",
                "text": "#333333",
            },
            "typography": {
                "headings": "Playfair Display",
                "body": "Source Sans Pro",
                "accent": "Dancing Script",
            },
            "style_keywords": ["luxury", "elegant", "sophisticated", "modern", "fashion"],
            "target_audience": "luxury fashion enthusiasts",
        }

    def get_server(self) -> Server:
        """Get the MCP server instance."""
        return self.server


def create_mcp_server() -> ThemeOrchestratorMCP:
    """Create and return the MCP server instance."""
    return ThemeOrchestratorMCP()


# Lazy-loaded server instance
_server_instance: ThemeOrchestratorMCP | None = None


def get_server_instance() -> ThemeOrchestratorMCP:
    """Get or create the server instance."""
    global _server_instance
    if _server_instance is None:
        _server_instance = create_mcp_server()
    return _server_instance


# Lazy proxy for mcp to avoid import-time initialization
class _MCPProxy:
    """Lazy proxy for the MCP server instance."""

    def __getattr__(self, name: str):
        return getattr(get_server_instance().server, name)


# Export mcp instance for Claude Code compatibility
mcp = _MCPProxy()


async def run_server() -> None:
    """Run the MCP server via stdio."""
    server = get_server_instance()
    async with stdio_server() as (read_stream, write_stream):
        await server.get_server().run(read_stream, write_stream, server.get_server().create_initialization_options())


def main() -> None:
    """Main entry point for running the server."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
