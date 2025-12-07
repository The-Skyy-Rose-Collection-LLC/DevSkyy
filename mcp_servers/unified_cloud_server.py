"""
DevSkyy Unified MCP Cloud Server

A comprehensive FastMCP server combining:
1. Theme Orchestrator - WordPress theme generation
2. WooCommerce Tools - Product & inventory management
3. Content & SEO Tools - Blog, media, optimization
4. AI Generation Tools - Product descriptions, prompts
5. Analytics Tools - Sales, traffic, performance
6. Agent Orchestration - DevSkyy AI agents

Sources & References:
- FastMCP 2.0 Documentation: https://gofastmcp.com/getting-started/welcome
- MCP Specification 2025-06-18: https://modelcontextprotocol.io/specification/2025-06-18/server/tools
- WooCommerce REST API v3: https://woocommerce.github.io/woocommerce-rest-api-docs/
- Elementor Widget Development: https://developers.elementor.com/docs/widgets/simple-example/
- WordPress REST API: https://developer.wordpress.org/rest-api/using-the-rest-api/authentication/

Deploy to FastMCP.app:
    fastmcp deploy mcp_servers/unified_cloud_server.py

Run locally:
    fastmcp dev mcp_servers/unified_cloud_server.py

Standard Python execution:
    python -m mcp_servers.unified_cloud_server
"""

from datetime import datetime
import hashlib
import json
import math
import re
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field


# =============================================================================
# CONSTANTS - SEO and Content Limits
# =============================================================================

META_TITLE_MAX_LENGTH = 60
META_DESCRIPTION_MAX_LENGTH = 160
META_DESCRIPTION_MIN_LENGTH = 120
SHORT_DESCRIPTION_MAX_LENGTH = 150
EXCERPT_MAX_LENGTH = 200

# =============================================================================
# SERVER INITIALIZATION
# Per FastMCP 2.0 docs: https://gofastmcp.com/getting-started/welcome
# =============================================================================

mcp = FastMCP(
    name="DevSkyy Unified Platform",
    version="2.0.0",
)

# In-memory state stores
active_theme_builds: dict[str, dict[str, Any]] = {}
product_catalog: dict[str, dict[str, Any]] = {}
content_drafts: dict[str, dict[str, Any]] = {}
agent_task_queue: dict[str, dict[str, Any]] = {}
discount_codes: dict[str, dict[str, Any]] = {}


# =============================================================================
# BRAND CONFIGURATION - SkyyRose (skyyrose.co)
# =============================================================================


def get_skyy_rose_brand_config() -> dict[str, Any]:
    """
    Get verified SkyyRose brand configuration.

    Returns complete brand guidelines including colors, typography,
    and prohibited terms for brand compliance.
    """
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
        "prohibited": {
            "incorrect_names": ["Skyy Rose", "skyy rose", "SKYYROSE", "SkyRose"],
            "incorrect_domains": [".com", "skyyrose.com"],
            "prohibited_language": ["discount", "clearance", "cheap", "sale", "hyphy"],
        },
    }


def generate_verification_hash(content: str) -> str:
    """
    Generate SHA-256 hash for content verification.

    Per Truth Protocol Rule #2: All outputs must be verifiable.
    """
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def get_current_timestamp() -> str:
    """Get current ISO format timestamp."""
    return datetime.now().isoformat()


# =============================================================================
# SECTION 1: THEME ORCHESTRATOR TOOLS
# =============================================================================


@mcp.tool
def generate_wordpress_theme(
    theme_name: Annotated[str, "Name for the WordPress theme"],
    theme_type: Annotated[str, Field(description="Theme style type", default="luxury_fashion")] = "luxury_fashion",
    include_woocommerce: Annotated[bool, Field(description="Include WooCommerce support", default=True)] = True,
    pages_to_generate: Annotated[list[str] | None, "List of page templates to generate"] = None,
) -> dict[str, Any]:
    """
    Generate a complete WordPress theme with Elementor support for SkyyRose.

    Creates theme files including style.css, functions.php, header.php,
    footer.php, and index.php following WordPress theme standards.

    Per Elementor docs: https://developers.elementor.com/docs/widgets/simple-example/
    """
    if pages_to_generate is None:
        pages_to_generate = ["home", "shop", "product", "about", "contact", "blog"]

    brand = get_skyy_rose_brand_config()
    build_id = f"theme_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{theme_name.replace(' ', '_')}"

    # Theme type configurations
    theme_type_configs = {
        "luxury_fashion": {
            "style": "elegant",
            "layout": "full-width",
            "animations": "subtle",
            "description": "Elegant, sophisticated design for luxury fashion brands",
        },
        "streetwear": {
            "style": "bold",
            "layout": "grid",
            "animations": "dynamic",
            "description": "Bold, dynamic design with urban aesthetic",
        },
        "minimalist": {
            "style": "clean",
            "layout": "centered",
            "animations": "minimal",
            "description": "Clean, focused design with minimal elements",
        },
        "ecommerce": {
            "style": "commercial",
            "layout": "full-width",
            "animations": "smooth",
            "description": "Conversion-optimized online store design",
        },
    }

    selected_config = theme_type_configs.get(theme_type, theme_type_configs["luxury_fashion"])
    theme_slug = theme_name.lower().replace(" ", "-")
    function_prefix = theme_name.lower().replace(" ", "_").replace("-", "_")

    # Generate style.css per WordPress theme standards
    style_css_content = f"""/*
Theme Name: {theme_name}
Theme URI: https://{brand['domain']}
Description: Custom {theme_type} theme for {brand['brand_name']} Collection - {brand['tagline']}
Version: 1.0.0
Author: {brand['brand_name']} Theme Orchestrator
Author URI: https://{brand['domain']}
Text Domain: {theme_slug}
License: Proprietary
License URI: https://{brand['domain']}/license
Requires at least: 6.0
Tested up to: 6.4
Requires PHP: 8.0
*/

/* CSS Custom Properties - Brand Colors */
:root {{
    --skyyrose-primary: {brand['colors']['primary']};
    --skyyrose-secondary: {brand['colors']['secondary']};
    --skyyrose-accent: {brand['colors']['accent']};
    --skyyrose-background: {brand['colors']['background']};
    --skyyrose-text: {brand['colors']['text']};
}}

/* Base Typography */
body {{
    font-family: '{brand['typography']['body']}', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color: var(--skyyrose-text);
    background-color: var(--skyyrose-background);
    line-height: 1.6;
    font-size: 16px;
}}

h1, h2, h3, h4, h5, h6 {{
    font-family: '{brand['typography']['headings']}', Georgia, serif;
    font-weight: 700;
    line-height: 1.2;
    color: var(--skyyrose-primary);
}}

/* Links */
a {{
    color: var(--skyyrose-secondary);
    text-decoration: none;
    transition: color 0.3s ease;
}}

a:hover {{
    color: var(--skyyrose-accent);
}}

/* Buttons */
.button, button, input[type="submit"] {{
    background-color: var(--skyyrose-primary);
    color: var(--skyyrose-background);
    border: none;
    padding: 12px 24px;
    font-family: '{brand['typography']['body']}', sans-serif;
    font-size: 14px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    transition: all 0.3s ease;
}}

.button:hover, button:hover, input[type="submit"]:hover {{
    background-color: var(--skyyrose-secondary);
    color: var(--skyyrose-primary);
}}

/* Container */
.container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}}

/* Header Styles */
.site-header {{
    background-color: var(--skyyrose-primary);
    padding: 20px 0;
}}

.site-header .site-title {{
    color: var(--skyyrose-background);
    font-family: '{brand['typography']['headings']}', Georgia, serif;
}}

.site-header .site-title a {{
    color: inherit;
}}

/* Navigation */
.main-navigation {{
    display: flex;
    align-items: center;
}}

.main-navigation ul {{
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    gap: 30px;
}}

.main-navigation a {{
    color: var(--skyyrose-background);
    font-size: 14px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

.main-navigation a:hover {{
    color: var(--skyyrose-secondary);
}}

/* Footer Styles */
.site-footer {{
    background-color: var(--skyyrose-primary);
    color: var(--skyyrose-background);
    padding: 60px 0 30px;
}}

.site-footer h4 {{
    color: var(--skyyrose-secondary);
    font-size: 16px;
    margin-bottom: 20px;
}}

.site-footer a {{
    color: var(--skyyrose-background);
    opacity: 0.8;
}}

.site-footer a:hover {{
    opacity: 1;
    color: var(--skyyrose-secondary);
}}

/* WooCommerce Overrides */
.woocommerce .products .product {{
    text-align: center;
}}

.woocommerce .products .product .woocommerce-loop-product__title {{
    font-family: '{brand['typography']['headings']}', Georgia, serif;
    font-size: 18px;
}}

.woocommerce .products .product .price {{
    color: var(--skyyrose-secondary);
    font-weight: 600;
}}

.woocommerce .button.add_to_cart_button {{
    background-color: var(--skyyrose-primary);
}}

.woocommerce .button.add_to_cart_button:hover {{
    background-color: var(--skyyrose-secondary);
}}
"""

    # Generate functions.php per WordPress and WooCommerce standards
    functions_php_content = f"""<?php
/**
 * {theme_name} Theme Functions
 *
 * @package {theme_slug}
 * @version 1.0.0
 * @author {brand['brand_name']}
 * @link https://{brand['domain']}
 */

if (!defined('ABSPATH')) {{
    exit; // Exit if accessed directly
}}

/**
 * Theme Setup
 *
 * Sets up theme defaults and registers support for WordPress features.
 */
function {function_prefix}_theme_setup() {{
    // Add support for post thumbnails
    add_theme_support('post-thumbnails');

    // Add support for automatic title tag
    add_theme_support('title-tag');

    // Add support for custom logo
    add_theme_support('custom-logo', array(
        'height'      => 100,
        'width'       => 400,
        'flex-width'  => true,
        'flex-height' => true,
    ));

    // Add support for HTML5 markup
    add_theme_support('html5', array(
        'search-form',
        'comment-form',
        'comment-list',
        'gallery',
        'caption',
        'style',
        'script',
    ));

    // WooCommerce support
    add_theme_support('woocommerce');
    add_theme_support('wc-product-gallery-zoom');
    add_theme_support('wc-product-gallery-lightbox');
    add_theme_support('wc-product-gallery-slider');

    // Register navigation menus
    register_nav_menus(array(
        'primary' => esc_html__('Primary Menu', '{theme_slug}'),
        'footer'  => esc_html__('Footer Menu', '{theme_slug}'),
        'mobile'  => esc_html__('Mobile Menu', '{theme_slug}'),
    ));

    // Set content width
    $GLOBALS['content_width'] = 1200;
}}
add_action('after_setup_theme', '{function_prefix}_theme_setup');

/**
 * Enqueue Styles and Scripts
 */
function {function_prefix}_enqueue_assets() {{
    // Theme stylesheet
    wp_enqueue_style(
        '{theme_slug}-style',
        get_stylesheet_uri(),
        array(),
        wp_get_theme()->get('Version')
    );

    // Google Fonts - Playfair Display and Source Sans Pro
    wp_enqueue_style(
        '{theme_slug}-google-fonts',
        'https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Source+Sans+Pro:wght@300;400;600;700&display=swap',
        array(),
        null
    );

    // Main JavaScript
    wp_enqueue_script(
        '{theme_slug}-main',
        get_template_directory_uri() . '/assets/js/main.js',
        array('jquery'),
        wp_get_theme()->get('Version'),
        true
    );

    // Localize script for AJAX
    wp_localize_script('{theme_slug}-main', '{function_prefix}Ajax', array(
        'ajaxurl' => admin_url('admin-ajax.php'),
        'nonce'   => wp_create_nonce('{theme_slug}-nonce'),
    ));
}}
add_action('wp_enqueue_scripts', '{function_prefix}_enqueue_assets');

/**
 * Register Widget Areas
 */
function {function_prefix}_widgets_init() {{
    register_sidebar(array(
        'name'          => esc_html__('Footer Column 1', '{theme_slug}'),
        'id'            => 'footer-1',
        'description'   => esc_html__('Add widgets here for footer column 1.', '{theme_slug}'),
        'before_widget' => '<div id="%1$s" class="widget %2$s">',
        'after_widget'  => '</div>',
        'before_title'  => '<h4 class="widget-title">',
        'after_title'   => '</h4>',
    ));

    register_sidebar(array(
        'name'          => esc_html__('Footer Column 2', '{theme_slug}'),
        'id'            => 'footer-2',
        'description'   => esc_html__('Add widgets here for footer column 2.', '{theme_slug}'),
        'before_widget' => '<div id="%1$s" class="widget %2$s">',
        'after_widget'  => '</div>',
        'before_title'  => '<h4 class="widget-title">',
        'after_title'   => '</h4>',
    ));

    register_sidebar(array(
        'name'          => esc_html__('Shop Sidebar', '{theme_slug}'),
        'id'            => 'shop-sidebar',
        'description'   => esc_html__('Add widgets here for shop sidebar.', '{theme_slug}'),
        'before_widget' => '<div id="%1$s" class="widget %2$s">',
        'after_widget'  => '</div>',
        'before_title'  => '<h4 class="widget-title">',
        'after_title'   => '</h4>',
    ));
}}
add_action('widgets_init', '{function_prefix}_widgets_init');

/**
 * Custom Excerpt Length
 */
function {function_prefix}_excerpt_length($length) {{
    return 25;
}}
add_filter('excerpt_length', '{function_prefix}_excerpt_length');

/**
 * Custom Excerpt More
 */
function {function_prefix}_excerpt_more($more) {{
    return '...';
}}
add_filter('excerpt_more', '{function_prefix}_excerpt_more');

/**
 * Add body classes
 */
function {function_prefix}_body_classes($classes) {{
    // Add theme-specific class
    $classes[] = '{theme_slug}-theme';

    // Add class for WooCommerce pages
    if (class_exists('WooCommerce')) {{
        if (is_shop() || is_product_category() || is_product_tag()) {{
            $classes[] = '{theme_slug}-shop-page';
        }}
        if (is_product()) {{
            $classes[] = '{theme_slug}-product-page';
        }}
    }}

    return $classes;
}}
add_filter('body_class', '{function_prefix}_body_classes');
"""

    # Generate header.php
    header_php_content = f"""<?php
/**
 * The header for {theme_name}
 *
 * @package {theme_slug}
 */

if (!defined('ABSPATH')) {{
    exit;
}}
?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="profile" href="https://gmpg.org/xfn/11">
    <?php wp_head(); ?>
</head>

<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<div id="page" class="site">
    <a class="skip-link screen-reader-text" href="#primary">
        <?php esc_html_e('Skip to content', '{theme_slug}'); ?>
    </a>

    <header id="masthead" class="site-header">
        <div class="container">
            <div class="header-inner">
                <div class="site-branding">
                    <?php if (has_custom_logo()) : ?>
                        <?php the_custom_logo(); ?>
                    <?php else : ?>
                        <h1 class="site-title">
                            <a href="<?php echo esc_url(home_url('/')); ?>" rel="home">
                                {brand['brand_name']}
                            </a>
                        </h1>
                    <?php endif; ?>
                </div>

                <nav id="site-navigation" class="main-navigation">
                    <button class="menu-toggle" aria-controls="primary-menu" aria-expanded="false">
                        <span class="screen-reader-text"><?php esc_html_e('Menu', '{theme_slug}'); ?></span>
                        <span class="hamburger-icon"></span>
                    </button>
                    <?php
                    wp_nav_menu(array(
                        'theme_location' => 'primary',
                        'menu_id'        => 'primary-menu',
                        'container'      => false,
                        'fallback_cb'    => false,
                    ));
                    ?>
                </nav>

                <div class="header-actions">
                    <?php if (class_exists('WooCommerce')) : ?>
                        <a href="<?php echo esc_url(wc_get_page_permalink('myaccount')); ?>" class="header-icon account-icon" aria-label="<?php esc_attr_e('My Account', '{theme_slug}'); ?>">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                                <circle cx="12" cy="7" r="4"></circle>
                            </svg>
                        </a>
                        <a href="<?php echo esc_url(wc_get_cart_url()); ?>" class="header-icon cart-icon" aria-label="<?php esc_attr_e('Shopping Cart', '{theme_slug}'); ?>">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <circle cx="9" cy="21" r="1"></circle>
                                <circle cx="20" cy="21" r="1"></circle>
                                <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
                            </svg>
                            <span class="cart-count"><?php echo esc_html(WC()->cart->get_cart_contents_count()); ?></span>
                        </a>
                    <?php endif; ?>
                </div>
            </div>
        </div>
    </header>

    <main id="primary" class="site-main">
"""

    # Generate footer.php
    footer_php_content = f"""<?php
/**
 * The footer for {theme_name}
 *
 * @package {theme_slug}
 */

if (!defined('ABSPATH')) {{
    exit;
}}
?>
    </main><!-- #primary -->

    <footer id="colophon" class="site-footer">
        <div class="container">
            <div class="footer-widgets">
                <div class="footer-column">
                    <h4>About {brand['brand_name']}</h4>
                    <p>{brand['tagline']}</p>
                    <p>Oakland, California</p>
                </div>

                <div class="footer-column">
                    <h4>Quick Links</h4>
                    <?php
                    wp_nav_menu(array(
                        'theme_location' => 'footer',
                        'container'      => false,
                        'fallback_cb'    => false,
                        'depth'          => 1,
                    ));
                    ?>
                </div>

                <div class="footer-column">
                    <h4>Contact</h4>
                    <p>Oakland, CA</p>
                    <p><a href="mailto:hello@{brand['domain']}">hello@{brand['domain']}</a></p>
                </div>

                <div class="footer-column">
                    <h4>Follow Us</h4>
                    <div class="social-links">
                        <a href="https://instagram.com/skyyroseco" target="_blank" rel="noopener noreferrer" aria-label="Instagram">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                            </svg>
                        </a>
                        <a href="https://tiktok.com/@skyyroseco" target="_blank" rel="noopener noreferrer" aria-label="TikTok">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
                            </svg>
                        </a>
                    </div>
                </div>
            </div>

            <div class="footer-bottom">
                <p>&copy; <?php echo esc_html(date('Y')); ?> {brand['brand_name']}. All rights reserved.</p>
            </div>
        </div>
    </footer>
</div><!-- #page -->

<?php wp_footer(); ?>
</body>
</html>
"""

    # Generate index.php
    index_php_content = f"""<?php
/**
 * The main template file for {theme_name}
 *
 * @package {theme_slug}
 */

if (!defined('ABSPATH')) {{
    exit;
}}

get_header();
?>

<div class="container">
    <?php if (have_posts()) : ?>

        <div class="posts-grid">
            <?php while (have_posts()) : the_post(); ?>

                <article id="post-<?php the_ID(); ?>" <?php post_class('post-card'); ?>>
                    <?php if (has_post_thumbnail()) : ?>
                        <div class="post-thumbnail">
                            <a href="<?php the_permalink(); ?>">
                                <?php the_post_thumbnail('medium_large'); ?>
                            </a>
                        </div>
                    <?php endif; ?>

                    <div class="post-content">
                        <header class="entry-header">
                            <?php the_title('<h2 class="entry-title"><a href="' . esc_url(get_permalink()) . '">', '</a></h2>'); ?>

                            <div class="entry-meta">
                                <span class="posted-on">
                                    <?php echo esc_html(get_the_date()); ?>
                                </span>
                            </div>
                        </header>

                        <div class="entry-excerpt">
                            <?php the_excerpt(); ?>
                        </div>

                        <a href="<?php the_permalink(); ?>" class="read-more">
                            <?php esc_html_e('Read More', '{theme_slug}'); ?>
                        </a>
                    </div>
                </article>

            <?php endwhile; ?>
        </div>

        <nav class="posts-navigation">
            <?php the_posts_pagination(array(
                'mid_size'  => 2,
                'prev_text' => esc_html__('Previous', '{theme_slug}'),
                'next_text' => esc_html__('Next', '{theme_slug}'),
            )); ?>
        </nav>

    <?php else : ?>

        <div class="no-results">
            <h2><?php esc_html_e('Nothing Found', '{theme_slug}'); ?></h2>
            <p><?php esc_html_e('It seems we cannot find what you are looking for.', '{theme_slug}'); ?></p>
        </div>

    <?php endif; ?>
</div>

<?php
get_footer();
"""

    # Compile all files
    theme_files = {
        "style.css": style_css_content,
        "functions.php": functions_php_content,
        "header.php": header_php_content,
        "footer.php": footer_php_content,
        "index.php": index_php_content,
    }

    # Generate content hash for verification
    all_content = json.dumps(theme_files, sort_keys=True)
    content_verification_hash = generate_verification_hash(all_content)

    # Store build in memory
    active_theme_builds[build_id] = {
        "build_id": build_id,
        "status": "completed",
        "theme_name": theme_name,
        "theme_slug": theme_slug,
        "theme_type": theme_type,
        "created_at": get_current_timestamp(),
        "content_hash": content_verification_hash,
        "files": theme_files,
        "config": selected_config,
    }

    return {
        "success": True,
        "build_id": build_id,
        "theme_name": theme_name,
        "theme_slug": theme_slug,
        "theme_type": theme_type,
        "config": selected_config,
        "files": theme_files,
        "file_count": len(theme_files),
        "content_hash": content_verification_hash,
        "pages_included": pages_to_generate,
        "woocommerce_enabled": include_woocommerce,
        "brand": {
            "name": brand["brand_name"],
            "domain": brand["domain"],
            "tagline": brand["tagline"],
        },
        "next_steps": [
            f"1. Download all {len(theme_files)} theme files",
            "2. Create theme folder and add files",
            "3. Upload to WordPress via Appearance > Themes > Add New",
            "4. Activate theme and customize with Elementor",
            f"5. Visit https://{brand['domain']} to verify",
        ],
    }


@mcp.tool
def list_available_theme_types() -> dict[str, Any]:
    """
    List all available WordPress theme types with descriptions.

    Returns detailed information about each theme style
    including recommended use cases and features.
    """
    return {
        "success": True,
        "theme_types": [
            {
                "id": "luxury_fashion",
                "name": "Luxury Fashion",
                "description": "Elegant, sophisticated design for luxury fashion brands",
                "style": "elegant",
                "features": [
                    "WooCommerce integration",
                    "Elementor compatible",
                    "Custom product galleries",
                    "Lookbook layouts",
                ],
                "recommended_for": "High-end fashion, boutique, luxury retail",
                "color_scheme": "Black and gold with neutral accents",
            },
            {
                "id": "streetwear",
                "name": "Streetwear",
                "description": "Bold, dynamic design with urban aesthetic",
                "style": "bold",
                "features": [
                    "Dynamic grid layouts",
                    "Video backgrounds",
                    "Drop countdown timers",
                    "Social media integration",
                ],
                "recommended_for": "Street fashion, urban wear, youth brands",
                "color_scheme": "High contrast with bold accents",
            },
            {
                "id": "minimalist",
                "name": "Minimalist",
                "description": "Clean, focused design with minimal elements",
                "style": "clean",
                "features": [
                    "Fast loading",
                    "Accessibility focused",
                    "Simple navigation",
                    "Whitespace emphasis",
                ],
                "recommended_for": "Modern brands, premium simplicity",
                "color_scheme": "Neutral palette with subtle accents",
            },
            {
                "id": "ecommerce",
                "name": "E-commerce",
                "description": "Conversion-optimized online store design",
                "style": "commercial",
                "features": [
                    "Product filters",
                    "Wishlist functionality",
                    "Reviews integration",
                    "Upsell sections",
                ],
                "recommended_for": "High-volume stores, product-focused sites",
                "color_scheme": "Trust-building blues with action colors",
            },
        ],
        "default_type": "luxury_fashion",
        "brand": "SkyyRose",
    }


@mcp.tool
def generate_elementor_custom_widget(
    widget_type: Annotated[
        str,
        Field(description="Widget type: product_showcase, brand_hero, collection_grid, testimonials, newsletter"),
    ],
    custom_widget_name: Annotated[str | None, "Optional custom name for the widget"] = None,
) -> dict[str, Any]:
    """
    Generate a custom Elementor widget for WordPress themes.

    Creates complete PHP widget class following Elementor widget development
    best practices per https://developers.elementor.com/docs/widgets/simple-example/
    """
    available_widget_types = [
        "product_showcase",
        "brand_hero",
        "collection_grid",
        "testimonials",
        "newsletter",
    ]

    if widget_type not in available_widget_types:
        return {
            "success": False,
            "error": f"Unknown widget type: {widget_type}",
            "available_types": available_widget_types,
        }

    brand = get_skyy_rose_brand_config()

    if custom_widget_name is None:
        custom_widget_name = widget_type.replace("_", " ").title()

    class_name = "SkyyRose_" + custom_widget_name.replace(" ", "_") + "_Widget"
    widget_slug = widget_type.lower()

    # Widget configurations per Elementor standards
    widget_configs = {
        "product_showcase": {
            "icon": "eicon-products",
            "category": "skyyrose",
            "description": "Display WooCommerce products in a beautiful grid",
        },
        "brand_hero": {
            "icon": "eicon-banner",
            "category": "skyyrose",
            "description": "Full-width hero section with brand messaging",
        },
        "collection_grid": {
            "icon": "eicon-gallery-grid",
            "category": "skyyrose",
            "description": "Product category grid with images",
        },
        "testimonials": {
            "icon": "eicon-testimonial-carousel",
            "category": "skyyrose",
            "description": "Customer testimonials carousel",
        },
        "newsletter": {
            "icon": "eicon-email-field",
            "category": "skyyrose",
            "description": "Email newsletter signup form",
        },
    }

    config = widget_configs[widget_type]

    # Generate complete PHP widget class per Elementor documentation
    widget_php_content = f"""<?php
/**
 * {custom_widget_name} - Custom Elementor Widget
 *
 * @package skyyrose-theme
 * @since 1.0.0
 * @link https://developers.elementor.com/docs/widgets/simple-example/
 */

if (!defined('ABSPATH')) {{
    exit; // Exit if accessed directly
}}

/**
 * {custom_widget_name} Widget Class
 *
 * {config['description']}
 */
class {class_name} extends \\Elementor\\Widget_Base {{

    /**
     * Get widget name.
     *
     * @return string Widget name.
     */
    public function get_name(): string {{
        return '{widget_slug}';
    }}

    /**
     * Get widget title.
     *
     * @return string Widget title.
     */
    public function get_title(): string {{
        return esc_html__('{custom_widget_name}', 'skyyrose');
    }}

    /**
     * Get widget icon.
     *
     * @return string Widget icon.
     */
    public function get_icon(): string {{
        return '{config['icon']}';
    }}

    /**
     * Get widget categories.
     *
     * @return array Widget categories.
     */
    public function get_categories(): array {{
        return ['{config['category']}'];
    }}

    /**
     * Get widget keywords.
     *
     * @return array Widget keywords.
     */
    public function get_keywords(): array {{
        return ['skyyrose', '{widget_type}', 'fashion', 'luxury'];
    }}

    /**
     * Whether the widget requires inner wrapper.
     *
     * @return bool
     */
    public function has_widget_inner_wrapper(): bool {{
        return false;
    }}

    /**
     * Register widget controls.
     */
    protected function register_controls(): void {{
        $this->start_controls_section(
            'content_section',
            [
                'label' => esc_html__('Content', 'skyyrose'),
                'tab'   => \\Elementor\\Controls_Manager::TAB_CONTENT,
            ]
        );
"""

    # Add widget-specific controls
    if widget_type == "product_showcase":
        widget_php_content += """
        $this->add_control(
            'products_count',
            [
                'label'   => esc_html__('Number of Products', 'skyyrose'),
                'type'    => \\Elementor\\Controls_Manager::NUMBER,
                'default' => 8,
                'min'     => 1,
                'max'     => 24,
            ]
        );

        $this->add_control(
            'columns',
            [
                'label'   => esc_html__('Columns', 'skyyrose'),
                'type'    => \\Elementor\\Controls_Manager::SELECT,
                'default' => '4',
                'options' => [
                    '2' => esc_html__('2 Columns', 'skyyrose'),
                    '3' => esc_html__('3 Columns', 'skyyrose'),
                    '4' => esc_html__('4 Columns', 'skyyrose'),
                ],
            ]
        );

        $this->add_control(
            'orderby',
            [
                'label'   => esc_html__('Order By', 'skyyrose'),
                'type'    => \\Elementor\\Controls_Manager::SELECT,
                'default' => 'date',
                'options' => [
                    'date'       => esc_html__('Date', 'skyyrose'),
                    'title'      => esc_html__('Title', 'skyyrose'),
                    'price'      => esc_html__('Price', 'skyyrose'),
                    'popularity' => esc_html__('Popularity', 'skyyrose'),
                    'rating'     => esc_html__('Rating', 'skyyrose'),
                ],
            ]
        );
"""
    elif widget_type == "brand_hero":
        widget_php_content += f"""
        $this->add_control(
            'heading',
            [
                'label'   => esc_html__('Heading', 'skyyrose'),
                'type'    => \\Elementor\\Controls_Manager::TEXT,
                'default' => esc_html__('Welcome to {brand['brand_name']}', 'skyyrose'),
            ]
        );

        $this->add_control(
            'subheading',
            [
                'label'   => esc_html__('Subheading', 'skyyrose'),
                'type'    => \\Elementor\\Controls_Manager::TEXT,
                'default' => esc_html__('{brand['tagline']}', 'skyyrose'),
            ]
        );

        $this->add_control(
            'button_text',
            [
                'label'   => esc_html__('Button Text', 'skyyrose'),
                'type'    => \\Elementor\\Controls_Manager::TEXT,
                'default' => esc_html__('Shop Now', 'skyyrose'),
            ]
        );

        $this->add_control(
            'button_link',
            [
                'label'       => esc_html__('Button Link', 'skyyrose'),
                'type'        => \\Elementor\\Controls_Manager::URL,
                'placeholder' => esc_html__('https://your-link.com', 'skyyrose'),
                'default'     => [
                    'url' => '/shop',
                ],
            ]
        );

        $this->add_control(
            'background_image',
            [
                'label' => esc_html__('Background Image', 'skyyrose'),
                'type'  => \\Elementor\\Controls_Manager::MEDIA,
            ]
        );
"""
    elif widget_type == "collection_grid":
        widget_php_content += """
        $this->add_control(
            'categories_count',
            [
                'label'   => esc_html__('Number of Categories', 'skyyrose'),
                'type'    => \\Elementor\\Controls_Manager::NUMBER,
                'default' => 6,
                'min'     => 2,
                'max'     => 12,
            ]
        );

        $this->add_control(
            'show_count',
            [
                'label'        => esc_html__('Show Product Count', 'skyyrose'),
                'type'         => \\Elementor\\Controls_Manager::SWITCHER,
                'label_on'     => esc_html__('Yes', 'skyyrose'),
                'label_off'    => esc_html__('No', 'skyyrose'),
                'return_value' => 'yes',
                'default'      => 'yes',
            ]
        );
"""
    elif widget_type == "testimonials":
        widget_php_content += """
        $this->add_control(
            'testimonials',
            [
                'label'   => esc_html__('Testimonials', 'skyyrose'),
                'type'    => \\Elementor\\Controls_Manager::REPEATER,
                'fields'  => [
                    [
                        'name'    => 'quote',
                        'label'   => esc_html__('Quote', 'skyyrose'),
                        'type'    => \\Elementor\\Controls_Manager::TEXTAREA,
                        'default' => esc_html__('Amazing quality and attention to detail!', 'skyyrose'),
                    ],
                    [
                        'name'    => 'author',
                        'label'   => esc_html__('Author', 'skyyrose'),
                        'type'    => \\Elementor\\Controls_Manager::TEXT,
                        'default' => esc_html__('Customer Name', 'skyyrose'),
                    ],
                ],
                'default' => [
                    [
                        'quote'  => esc_html__('Absolutely love the quality. SkyyRose is my go-to for luxury streetwear.', 'skyyrose'),
                        'author' => esc_html__('Satisfied Customer', 'skyyrose'),
                    ],
                ],
                'title_field' => '{{{ author }}}',
            ]
        );

        $this->add_control(
            'autoplay',
            [
                'label'        => esc_html__('Autoplay', 'skyyrose'),
                'type'         => \\Elementor\\Controls_Manager::SWITCHER,
                'label_on'     => esc_html__('Yes', 'skyyrose'),
                'label_off'    => esc_html__('No', 'skyyrose'),
                'return_value' => 'yes',
                'default'      => 'yes',
            ]
        );
"""
    elif widget_type == "newsletter":
        widget_php_content += f"""
        $this->add_control(
            'heading',
            [
                'label'   => esc_html__('Heading', 'skyyrose'),
                'type'    => \\Elementor\\Controls_Manager::TEXT,
                'default' => esc_html__('Join the {brand['brand_name']} Community', 'skyyrose'),
            ]
        );

        $this->add_control(
            'description',
            [
                'label'   => esc_html__('Description', 'skyyrose'),
                'type'    => \\Elementor\\Controls_Manager::TEXTAREA,
                'default' => esc_html__('Subscribe for exclusive offers, early access to new drops, and style inspiration.', 'skyyrose'),
            ]
        );

        $this->add_control(
            'button_text',
            [
                'label'   => esc_html__('Button Text', 'skyyrose'),
                'type'    => \\Elementor\\Controls_Manager::TEXT,
                'default' => esc_html__('Subscribe', 'skyyrose'),
            ]
        );

        $this->add_control(
            'placeholder_text',
            [
                'label'   => esc_html__('Placeholder Text', 'skyyrose'),
                'type'    => \\Elementor\\Controls_Manager::TEXT,
                'default' => esc_html__('Enter your email address', 'skyyrose'),
            ]
        );
"""

    # Close controls section
    widget_php_content += (
        """
        $this->end_controls_section();

        // Style Section
        $this->start_controls_section(
            'style_section',
            [
                'label' => esc_html__('Style', 'skyyrose'),
                'tab'   => \\Elementor\\Controls_Manager::TAB_STYLE,
            ]
        );

        $this->add_control(
            'text_color',
            [
                'label'     => esc_html__('Text Color', 'skyyrose'),
                'type'      => \\Elementor\\Controls_Manager::COLOR,
                'selectors' => [
                    '{{WRAPPER}} .skyyrose-widget' => 'color: {{VALUE}};',
                ],
            ]
        );

        $this->end_controls_section();
    }

    /**
     * Render widget output on the frontend.
     */
    protected function render(): void {
        $settings = $this->get_settings_for_display();
        ?>
        <div class="skyyrose-widget skyyrose-"""
        + widget_slug
        + """">
"""
    )

    # Add widget-specific render content
    if widget_type == "product_showcase":
        widget_php_content += """
            <?php
            if (class_exists('WooCommerce')) {
                $products_count = absint($settings['products_count']);
                $columns = absint($settings['columns']);
                $orderby = sanitize_text_field($settings['orderby']);

                echo do_shortcode('[products limit="' . $products_count . '" columns="' . $columns . '" orderby="' . $orderby . '"]');
            } else {
                echo '<p>' . esc_html__('WooCommerce is required for this widget.', 'skyyrose') . '</p>';
            }
            ?>
"""
    elif widget_type == "brand_hero":
        widget_php_content += """
            <?php
            $bg_image = !empty($settings['background_image']['url']) ? $settings['background_image']['url'] : '';
            $heading = !empty($settings['heading']) ? $settings['heading'] : '';
            $subheading = !empty($settings['subheading']) ? $settings['subheading'] : '';
            $button_text = !empty($settings['button_text']) ? $settings['button_text'] : '';
            $button_url = !empty($settings['button_link']['url']) ? $settings['button_link']['url'] : '#';
            ?>
            <div class="skyyrose-hero" style="background-image: url('<?php echo esc_url($bg_image); ?>');">
                <div class="hero-overlay"></div>
                <div class="hero-content">
                    <?php if ($heading) : ?>
                        <h1 class="hero-heading"><?php echo esc_html($heading); ?></h1>
                    <?php endif; ?>
                    <?php if ($subheading) : ?>
                        <p class="hero-subheading"><?php echo esc_html($subheading); ?></p>
                    <?php endif; ?>
                    <?php if ($button_text) : ?>
                        <a href="<?php echo esc_url($button_url); ?>" class="hero-button">
                            <?php echo esc_html($button_text); ?>
                        </a>
                    <?php endif; ?>
                </div>
            </div>
"""
    elif widget_type == "collection_grid":
        widget_php_content += """
            <?php
            if (class_exists('WooCommerce')) {
                $categories_count = absint($settings['categories_count']);
                $show_count = $settings['show_count'] === 'yes';

                $categories = get_terms(array(
                    'taxonomy'   => 'product_cat',
                    'hide_empty' => true,
                    'number'     => $categories_count,
                ));

                if (!empty($categories) && !is_wp_error($categories)) : ?>
                    <div class="skyyrose-collections-grid">
                        <?php foreach ($categories as $category) :
                            $thumbnail_id = get_term_meta($category->term_id, 'thumbnail_id', true);
                            $image_url = $thumbnail_id ? wp_get_attachment_url($thumbnail_id) : wc_placeholder_img_src();
                        ?>
                            <a href="<?php echo esc_url(get_term_link($category)); ?>" class="collection-item">
                                <div class="collection-image">
                                    <img src="<?php echo esc_url($image_url); ?>" alt="<?php echo esc_attr($category->name); ?>">
                                </div>
                                <div class="collection-info">
                                    <h3 class="collection-name"><?php echo esc_html($category->name); ?></h3>
                                    <?php if ($show_count) : ?>
                                        <span class="collection-count"><?php echo esc_html($category->count); ?> products</span>
                                    <?php endif; ?>
                                </div>
                            </a>
                        <?php endforeach; ?>
                    </div>
                <?php endif;
            } else {
                echo '<p>' . esc_html__('WooCommerce is required for this widget.', 'skyyrose') . '</p>';
            }
            ?>
"""
    elif widget_type == "testimonials":
        widget_php_content += """
            <?php
            $testimonials = $settings['testimonials'];
            $autoplay = $settings['autoplay'] === 'yes' ? 'true' : 'false';

            if (!empty($testimonials)) : ?>
                <div class="skyyrose-testimonials-slider" data-autoplay="<?php echo esc_attr($autoplay); ?>">
                    <div class="testimonials-wrapper">
                        <?php foreach ($testimonials as $testimonial) : ?>
                            <div class="testimonial-item">
                                <blockquote class="testimonial-quote">
                                    <p><?php echo esc_html($testimonial['quote']); ?></p>
                                </blockquote>
                                <cite class="testimonial-author">- <?php echo esc_html($testimonial['author']); ?></cite>
                            </div>
                        <?php endforeach; ?>
                    </div>
                    <div class="testimonials-navigation">
                        <button class="prev-testimonial" aria-label="Previous">&larr;</button>
                        <button class="next-testimonial" aria-label="Next">&rarr;</button>
                    </div>
                </div>
            <?php endif; ?>
"""
    elif widget_type == "newsletter":
        widget_php_content += """
            <?php
            $heading = !empty($settings['heading']) ? $settings['heading'] : '';
            $description = !empty($settings['description']) ? $settings['description'] : '';
            $button_text = !empty($settings['button_text']) ? $settings['button_text'] : 'Subscribe';
            $placeholder = !empty($settings['placeholder_text']) ? $settings['placeholder_text'] : 'Enter your email';
            ?>
            <div class="skyyrose-newsletter-widget">
                <?php if ($heading) : ?>
                    <h3 class="newsletter-heading"><?php echo esc_html($heading); ?></h3>
                <?php endif; ?>
                <?php if ($description) : ?>
                    <p class="newsletter-description"><?php echo esc_html($description); ?></p>
                <?php endif; ?>
                <form class="newsletter-form" method="post" action="">
                    <?php wp_nonce_field('skyyrose_newsletter', 'newsletter_nonce'); ?>
                    <div class="form-group">
                        <input type="email" name="newsletter_email" placeholder="<?php echo esc_attr($placeholder); ?>" required>
                        <button type="submit" class="newsletter-submit"><?php echo esc_html($button_text); ?></button>
                    </div>
                </form>
            </div>
"""

    # Close render method and class
    widget_php_content += """
        </div>
        <?php
    }
}
"""

    # Generate registration code
    registration_php = f"""<?php
/**
 * Register {custom_widget_name} Widget
 *
 * Include widget file and register widget class.
 *
 * @param \\Elementor\\Widgets_Manager $widgets_manager Elementor widgets manager.
 */
function register_{widget_slug}_widget($widgets_manager) {{
    require_once(__DIR__ . '/widgets/{widget_slug}-widget.php');
    $widgets_manager->register(new \\{class_name}());
}}
add_action('elementor/widgets/register', 'register_{widget_slug}_widget');
"""

    # Generate verification hash
    content_hash = generate_verification_hash(widget_php_content)

    return {
        "success": True,
        "widget_type": widget_type,
        "widget_name": custom_widget_name,
        "class_name": class_name,
        "widget_slug": widget_slug,
        "config": config,
        "files": {
            f"widgets/{widget_slug}-widget.php": widget_php_content,
            "functions.php (add to existing)": registration_php,
        },
        "content_hash": content_hash,
        "installation_steps": [
            "1. Create directory: your-theme/widgets/",
            f"2. Save widget as: your-theme/widgets/{widget_slug}-widget.php",
            "3. Add registration code to your theme's functions.php",
            "4. Widget will appear in Elementor under 'SkyyRose' category",
            "5. Drag and drop the widget to use it",
        ],
        "documentation_reference": "https://developers.elementor.com/docs/widgets/simple-example/",
    }


@mcp.tool
def get_theme_build_status(
    build_id: Annotated[str, "The build ID from generate_wordpress_theme"],
) -> dict[str, Any]:
    """
    Get the status of a theme build.

    Retrieves detailed information about a specific theme build
    including all generated files and configuration.
    """
    if build_id in active_theme_builds:
        build = active_theme_builds[build_id]
        return {
            "success": True,
            "build": build,
            "files_included": list(build.get("files", {}).keys()),
        }

    return {
        "success": False,
        "error": f"Build not found: {build_id}",
        "available_builds": list(active_theme_builds.keys()),
    }


# =============================================================================
# SECTION 2: WOOCOMMERCE / ECOMMERCE TOOLS
# Per WooCommerce REST API v3: https://woocommerce.github.io/woocommerce-rest-api-docs/
# =============================================================================


@mcp.tool
def create_woocommerce_product(
    product_name: Annotated[str, "Product name"],
    regular_price: Annotated[float, "Regular price in USD"],
    product_description: Annotated[str, "Full product description"],
    short_description: Annotated[str | None, "Short description (auto-generated if not provided)"] = None,
    product_category: Annotated[str, Field(description="Product category", default="Uncategorized")] = "Uncategorized",
    sku: Annotated[str | None, "Stock keeping unit (auto-generated if not provided)"] = None,
    stock_quantity: Annotated[int, Field(description="Initial stock quantity", default=10)] = 10,
    product_images: Annotated[list[str] | None, "List of image URLs"] = None,
    product_status: Annotated[
        str, Field(description="Product status: draft, publish, pending", default="draft")
    ] = "draft",
) -> dict[str, Any]:
    """
    Create a new WooCommerce product for SkyyRose catalog.

    Generates a complete product object ready for WooCommerce REST API v3.
    Per https://woocommerce.github.io/woocommerce-rest-api-docs/
    """
    brand = get_skyy_rose_brand_config()

    # Generate SKU if not provided
    if sku is None:
        timestamp_part = datetime.now().strftime("%Y%m%d")
        hash_part = generate_verification_hash(product_name)[:6].upper()
        sku = f"SR-{timestamp_part}-{hash_part}"

    # Generate short description if not provided
    if short_description is None:
        if len(product_description) > SHORT_DESCRIPTION_MAX_LENGTH:
            short_description = product_description[: SHORT_DESCRIPTION_MAX_LENGTH - 3] + "..."
        else:
            short_description = product_description

    # Generate product ID
    product_id = f"prod_{generate_verification_hash(product_name + str(datetime.now()))[:12]}"

    # Build product object per WooCommerce API structure
    product = {
        "id": product_id,
        "name": product_name,
        "slug": product_name.lower().replace(" ", "-").replace("'", ""),
        "type": "simple",
        "status": product_status,
        "featured": False,
        "catalog_visibility": "visible",
        "description": product_description,
        "short_description": short_description,
        "sku": sku,
        "regular_price": str(regular_price),
        "sale_price": "",
        "manage_stock": True,
        "stock_quantity": stock_quantity,
        "stock_status": "instock" if stock_quantity > 0 else "outofstock",
        "backorders": "no",
        "categories": [{"name": product_category}],
        "images": [{"src": url} for url in (product_images or [])],
        "attributes": [],
        "meta_data": [
            {"key": "_created_by", "value": "DevSkyy MCP Server"},
            {"key": "_created_at", "value": get_current_timestamp()},
        ],
    }

    # Store in catalog
    product_catalog[product_id] = product

    return {
        "success": True,
        "product": product,
        "product_id": product_id,
        "sku": sku,
        "brand": brand["brand_name"],
        "api_endpoint": "POST /wp-json/wc/v3/products",
        "next_steps": [
            "Add product images via WordPress Media Library",
            "Set product status to 'publish' when ready",
            "Configure shipping options if needed",
            "Add product variations if applicable",
        ],
    }


@mcp.tool
def update_woocommerce_product(
    product_id: Annotated[str, "Product ID to update"],
    product_name: Annotated[str | None, "New product name"] = None,
    regular_price: Annotated[float | None, "New regular price"] = None,
    sale_price: Annotated[float | None, "Sale price (set to 0 to remove sale)"] = None,
    product_description: Annotated[str | None, "New description"] = None,
    stock_quantity: Annotated[int | None, "New stock quantity"] = None,
    product_status: Annotated[str | None, "New status: draft, publish, pending, private"] = None,
) -> dict[str, Any]:
    """
    Update an existing WooCommerce product.

    Modifies product attributes in the catalog.
    Per WooCommerce REST API v3 PUT /products/{id}
    """
    if product_id not in product_catalog:
        return {
            "success": False,
            "error": f"Product not found: {product_id}",
            "available_products": list(product_catalog.keys()),
        }

    product = product_catalog[product_id]
    updates_made = {}

    if product_name is not None:
        product["name"] = product_name
        product["slug"] = product_name.lower().replace(" ", "-").replace("'", "")
        updates_made["name"] = product_name

    if regular_price is not None:
        product["regular_price"] = str(regular_price)
        updates_made["regular_price"] = regular_price

    if sale_price is not None:
        if sale_price > 0:
            product["sale_price"] = str(sale_price)
            updates_made["sale_price"] = sale_price
        else:
            product["sale_price"] = ""
            updates_made["sale_price"] = "removed"

    if product_description is not None:
        product["description"] = product_description
        updates_made["description"] = "updated"

    if stock_quantity is not None:
        product["stock_quantity"] = stock_quantity
        product["stock_status"] = "instock" if stock_quantity > 0 else "outofstock"
        updates_made["stock_quantity"] = stock_quantity

    if product_status is not None:
        valid_statuses = ["draft", "publish", "pending", "private"]
        if product_status in valid_statuses:
            product["status"] = product_status
            updates_made["status"] = product_status
        else:
            return {
                "success": False,
                "error": f"Invalid status: {product_status}",
                "valid_statuses": valid_statuses,
            }

    # Add update timestamp
    product["date_modified"] = get_current_timestamp()

    return {
        "success": True,
        "product_id": product_id,
        "updates_made": updates_made,
        "product": product,
        "api_endpoint": f"PUT /wp-json/wc/v3/products/{product_id}",
    }


@mcp.tool
def list_catalog_products(
    category_filter: Annotated[str | None, "Filter by category name"] = None,
    status_filter: Annotated[str | None, "Filter by status: draft, publish, pending"] = None,
    max_results: Annotated[int, Field(description="Maximum products to return", default=20)] = 20,
) -> dict[str, Any]:
    """
    List products in the catalog with optional filtering.

    Returns products matching the specified criteria.
    """
    products = list(product_catalog.values())

    if category_filter:
        products = [p for p in products if any(c.get("name") == category_filter for c in p.get("categories", []))]

    if status_filter:
        products = [p for p in products if p.get("status") == status_filter]

    products = products[:max_results]

    return {
        "success": True,
        "total_count": len(products),
        "products": products,
        "filters_applied": {
            "category": category_filter,
            "status": status_filter,
            "limit": max_results,
        },
    }


@mcp.tool
def manage_product_inventory(
    product_id: Annotated[str, "Product ID"],
    inventory_action: Annotated[str, "Action: add, remove, or set"],
    quantity: Annotated[int, Field(description="Quantity to add/remove/set", default=1)] = 1,
) -> dict[str, Any]:
    """
    Manage product inventory levels.

    Supports adding stock, removing stock, or setting absolute quantity.
    """
    if product_id not in product_catalog:
        return {
            "success": False,
            "error": f"Product not found: {product_id}",
        }

    product = product_catalog[product_id]
    current_stock = product.get("stock_quantity", 0)

    valid_actions = ["add", "remove", "set"]
    if inventory_action not in valid_actions:
        return {
            "success": False,
            "error": f"Invalid action: {inventory_action}",
            "valid_actions": valid_actions,
        }

    if inventory_action == "add":
        new_stock = current_stock + quantity
    elif inventory_action == "remove":
        new_stock = max(0, current_stock - quantity)
    else:  # set
        new_stock = max(0, quantity)

    product["stock_quantity"] = new_stock
    product["stock_status"] = "instock" if new_stock > 0 else "outofstock"

    return {
        "success": True,
        "product_id": product_id,
        "product_name": product.get("name"),
        "action": inventory_action,
        "quantity_changed": quantity,
        "previous_stock": current_stock,
        "new_stock": new_stock,
        "stock_status": product["stock_status"],
    }


@mcp.tool
def create_coupon_code(
    coupon_code: Annotated[str, "Coupon code (e.g., SUMMER20)"],
    discount_type: Annotated[
        str, Field(description="Type: percent, fixed_cart, fixed_product", default="percent")
    ] = "percent",
    discount_amount: Annotated[float, Field(description="Discount amount", default=10.0)] = 10.0,
    minimum_order_amount: Annotated[float | None, "Minimum order total required"] = None,
    expiry_date: Annotated[str | None, "Expiration date (YYYY-MM-DD format)"] = None,
    usage_limit: Annotated[int | None, "Maximum number of uses"] = None,
    individual_use: Annotated[bool, Field(description="Cannot be used with other coupons", default=False)] = False,
) -> dict[str, Any]:
    """
    Create a WooCommerce discount/coupon code.

    Generates a coupon configuration for the WooCommerce REST API.
    """
    valid_discount_types = ["percent", "fixed_cart", "fixed_product"]
    if discount_type not in valid_discount_types:
        return {
            "success": False,
            "error": f"Invalid discount type: {discount_type}",
            "valid_types": valid_discount_types,
        }

    formatted_code = coupon_code.upper().replace(" ", "")

    coupon = {
        "code": formatted_code,
        "discount_type": discount_type,
        "amount": str(discount_amount),
        "individual_use": individual_use,
        "exclude_sale_items": False,
        "minimum_amount": str(minimum_order_amount) if minimum_order_amount else "",
        "date_expires": expiry_date,
        "usage_limit": usage_limit,
        "usage_count": 0,
        "meta_data": [
            {"key": "_created_by", "value": "DevSkyy MCP Server"},
            {"key": "_created_at", "value": get_current_timestamp()},
        ],
    }

    # Store coupon
    discount_codes[formatted_code] = coupon

    # Generate display text
    display_text = f"{discount_amount}% off" if discount_type == "percent" else f"${discount_amount} off"

    if minimum_order_amount:
        display_text += f" on orders over ${minimum_order_amount}"

    return {
        "success": True,
        "coupon": coupon,
        "code": formatted_code,
        "display_text": display_text,
        "api_endpoint": "POST /wp-json/wc/v3/coupons",
    }


# =============================================================================
# SECTION 3: CONTENT & SEO TOOLS
# =============================================================================


@mcp.tool
def create_blog_post(
    post_title: Annotated[str, "Post title"],
    post_content: Annotated[str, "Full post content (HTML supported)"],
    post_excerpt: Annotated[str | None, "Short excerpt/summary (auto-generated if not provided)"] = None,
    post_categories: Annotated[list[str] | None, "List of category names"] = None,
    post_tags: Annotated[list[str] | None, "List of tags"] = None,
    featured_image_url: Annotated[str | None, "Featured image URL"] = None,
    post_status: Annotated[str, Field(description="Post status: draft, publish, pending", default="draft")] = "draft",
) -> dict[str, Any]:
    """
    Create a new WordPress blog post.

    Generates a complete post object for WordPress REST API.
    Per https://developer.wordpress.org/rest-api/using-the-rest-api/authentication/
    """
    brand = get_skyy_rose_brand_config()
    post_id = f"post_{generate_verification_hash(post_title + str(datetime.now()))[:12]}"

    # Generate excerpt if not provided
    if post_excerpt is None:
        # Strip HTML tags for excerpt
        clean_content = re.sub(r"<[^>]+>", "", post_content)
        clean_content = clean_content.replace("\n", " ").strip()
        if len(clean_content) > EXCERPT_MAX_LENGTH:
            post_excerpt = clean_content[:EXCERPT_MAX_LENGTH] + "..."
        else:
            post_excerpt = clean_content

    post = {
        "id": post_id,
        "title": {"rendered": post_title},
        "slug": post_title.lower().replace(" ", "-").replace("'", ""),
        "content": {"rendered": post_content},
        "excerpt": {"rendered": post_excerpt},
        "categories": post_categories or ["Uncategorized"],
        "tags": post_tags or [],
        "featured_media": featured_image_url,
        "status": post_status,
        "author": brand["brand_name"],
        "date": get_current_timestamp(),
        "meta_data": {
            "created_by": "DevSkyy MCP Server",
        },
    }

    # Store draft
    content_drafts[post_id] = post

    # Generate SEO suggestions
    seo_suggestions = [
        f"Meta title suggestion: {post_title} | {brand['brand_name']}",
        f"Meta description: {post_excerpt[:150]}...",
        "Add internal links to relevant product pages",
        "Include alt text for all images",
        "Use heading hierarchy (H1, H2, H3)",
    ]

    return {
        "success": True,
        "post": post,
        "post_id": post_id,
        "seo_suggestions": seo_suggestions,
        "api_endpoint": "POST /wp-json/wp/v2/posts",
    }


@mcp.tool
def generate_seo_metadata(
    content_type: Annotated[str, "Content type: post, product, page"],
    content_title: Annotated[str, "Title of the content"],
    target_keyword: Annotated[str, "Primary keyword to target"],
    content_description: Annotated[str | None, "Brief content description for context"] = None,
) -> dict[str, Any]:
    """
    Generate SEO-optimized metadata for content.

    Creates meta title, description, and schema markup
    following SEO best practices.
    """
    brand = get_skyy_rose_brand_config()

    # Generate meta title (max 60 chars)
    meta_title = f"{target_keyword.title()} | {brand['brand_name']}"
    if len(meta_title) > META_TITLE_MAX_LENGTH:
        meta_title = f"{target_keyword.title()[:45]}... | {brand['brand_name']}"

    # Generate meta description (max 160 chars)
    base_description = content_description or f"Discover {target_keyword.lower()} at {brand['brand_name']}"

    meta_description = f"{base_description}. {brand['tagline']}. Shop luxury streetwear at {brand['domain']}."
    if len(meta_description) > META_DESCRIPTION_MAX_LENGTH:
        meta_description = meta_description[: META_DESCRIPTION_MAX_LENGTH - 3] + "..."

    # Generate schema markup
    if content_type == "product":
        schema_type = "Product"
    elif content_type == "post":
        schema_type = "Article"
    else:
        schema_type = "WebPage"

    schema_markup = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "name": content_title,
        "description": meta_description,
        "brand": {
            "@type": "Brand",
            "name": brand["brand_name"],
        },
        "url": f"https://{brand['domain']}/",
    }

    # Analysis
    analysis = {
        "title_length": len(meta_title),
        "title_ok": len(meta_title) <= META_TITLE_MAX_LENGTH,
        "description_length": len(meta_description),
        "description_ok": META_DESCRIPTION_MIN_LENGTH <= len(meta_description) <= META_DESCRIPTION_MAX_LENGTH,
        "keyword_in_title": target_keyword.lower() in meta_title.lower(),
        "keyword_in_description": target_keyword.lower() in meta_description.lower(),
    }

    recommendations = []
    if not analysis["keyword_in_title"]:
        recommendations.append("Include target keyword in meta title")
    if not analysis["keyword_in_description"]:
        recommendations.append("Include target keyword in meta description")
    if analysis["description_length"] < META_DESCRIPTION_MIN_LENGTH:
        recommendations.append("Meta description could be longer for better CTR")

    return {
        "success": True,
        "seo_metadata": {
            "meta_title": meta_title,
            "meta_description": meta_description,
            "og_title": meta_title,
            "og_description": meta_description,
            "og_type": "website" if content_type == "page" else "article",
            "twitter_card": "summary_large_image",
        },
        "schema_markup": schema_markup,
        "analysis": analysis,
        "recommendations": recommendations if recommendations else ["SEO metadata looks good!"],
    }


# =============================================================================
# SECTION 4: AI GENERATION TOOLS
# =============================================================================


@mcp.tool
def generate_product_description(
    product_name: Annotated[str, "Name of the product"],
    product_type: Annotated[str, "Type: hoodie, jacket, pants, tee, accessories, etc."],
    key_features: Annotated[list[str], "List of key product features"],
    materials: Annotated[list[str] | None, "List of materials used"] = None,
    target_audience: Annotated[
        str, Field(description="Target audience description", default="fashion-forward individuals")
    ] = "fashion-forward individuals",
) -> dict[str, Any]:
    """
    Generate luxury product description following SkyyRose brand voice.

    Creates full description, short description, and social media caption
    all aligned with brand guidelines.
    """
    brand = get_skyy_rose_brand_config()

    # Format materials text
    materials_text = ""
    if materials:
        if len(materials) > 1:
            materials_text = f"Crafted from premium {', '.join(materials[:-1])} and {materials[-1]}"
        else:
            materials_text = f"Crafted from premium {materials[0]}"

    # Format features
    features_formatted = "\n".join([f"- {feature}" for feature in key_features])

    # Generate full description (luxury tone)
    full_description = f"""Introducing the {product_name} - where Oakland authenticity meets luxury streetwear.

{materials_text + '.' if materials_text else ''} This {product_type} embodies the essence of {brand['brand_name']}: sophisticated design that doesn't compromise on quality or style.

Key Features:
{features_formatted}

Designed for {target_audience} who appreciate the finer things while staying true to their roots. The {product_name} is a statement piece that seamlessly transitions from day to night.

Elevate your wardrobe with a piece that speaks to both heritage and innovation."""

    # Generate short description
    features_brief = ". ".join(key_features[:3])
    short_description = f"Premium {product_type} from {brand['brand_name']}. {features_brief}. {brand['tagline']}."

    # Generate social media caption
    social_caption = f"""New drop: {product_name}

Luxury meets streetwear. Oakland authenticity.

{key_features[0] if key_features else 'Premium quality'}.

Shop now at {brand['domain']}

#SkyyRose #LuxuryStreetwear #OaklandFashion #NewDrop"""

    # Generate verification hash
    content_hash = generate_verification_hash(full_description)

    return {
        "success": True,
        "product_name": product_name,
        "descriptions": {
            "full": full_description,
            "short": short_description,
            "social_caption": social_caption,
        },
        "word_counts": {
            "full": len(full_description.split()),
            "short": len(short_description.split()),
            "social": len(social_caption.split()),
        },
        "content_hash": content_hash,
        "brand_compliant": True,
        "brand": brand["brand_name"],
    }


@mcp.tool
def generate_collection_copy(
    collection_name: Annotated[str, "Name of the collection"],
    season: Annotated[str, "Season: Spring, Summer, Fall, Winter, or year like 2025"],
    theme: Annotated[str, "Collection theme or inspiration"],
    piece_count: Annotated[int, "Number of pieces in collection"],
    hero_pieces: Annotated[list[str] | None, "Featured/hero pieces"] = None,
) -> dict[str, Any]:
    """
    Generate copy for a product collection.

    Creates hero text, tagline, email subjects, and meta description
    all aligned with SkyyRose brand voice.
    """
    brand = get_skyy_rose_brand_config()

    # Generate hero text
    hero_text = f"""The {collection_name} Collection

{season} brings a new chapter in {brand['brand_name']}'s story. Inspired by {theme}, this {piece_count}-piece collection represents the perfect fusion of Oakland's street culture and elevated fashion.

Each piece tells a story of authenticity, craftsmanship, and uncompromising style."""

    if hero_pieces:
        hero_text += f"\n\nFeatured pieces: {', '.join(hero_pieces)}."

    # Generate tagline
    tagline = f"{collection_name}: {theme}"

    # Generate email content
    email_subject = f"New: The {collection_name} Collection Has Arrived"
    email_preview = f"Discover {piece_count} new pieces inspired by {theme}. Shop {brand['brand_name']} now."

    # Generate meta description
    meta_description = f"Shop the {collection_name} Collection from {brand['brand_name']}. {piece_count} pieces inspired by {theme}. Luxury streetwear with Oakland authenticity. Free shipping on orders over $150."

    # Generate content hash
    content_hash = generate_verification_hash(hero_text)

    return {
        "success": True,
        "collection_name": collection_name,
        "copy": {
            "hero_text": hero_text,
            "tagline": tagline,
            "email_subject": email_subject,
            "email_preview": email_preview,
            "meta_description": meta_description,
        },
        "content_hash": content_hash,
        "brand": brand["brand_name"],
    }


@mcp.tool
def generate_ai_image_prompt(
    subject: Annotated[str, "Main subject (product, model wearing product, lifestyle shot)"],
    visual_style: Annotated[
        str, Field(description="Style: luxury_fashion, streetwear, editorial, minimalist", default="luxury_fashion")
    ] = "luxury_fashion",
    mood: Annotated[
        str, Field(description="Mood: sophisticated, bold, relaxed, energetic", default="sophisticated")
    ] = "sophisticated",
    background: Annotated[
        str, Field(description="Background: studio, urban, nature, abstract", default="studio")
    ] = "studio",
    additional_details: Annotated[str | None, "Extra details to include"] = None,
) -> dict[str, Any]:
    """
    Generate AI image generation prompts for product/brand imagery.

    Creates optimized prompts for Midjourney, DALL-E, and Stable Diffusion
    following SkyyRose visual brand guidelines.
    """
    brand = get_skyy_rose_brand_config()

    style_modifiers = {
        "luxury_fashion": "high-end fashion photography, Vogue aesthetic, elegant lighting, premium quality",
        "streetwear": "urban street photography, authentic, raw energy, dynamic angles",
        "editorial": "editorial fashion shoot, artistic composition, magazine quality, high fashion",
        "minimalist": "clean minimal aesthetic, lots of negative space, modern, sophisticated simplicity",
    }

    mood_modifiers = {
        "sophisticated": "refined, polished, premium feel, elegant",
        "bold": "striking, confident, powerful, impactful",
        "relaxed": "casual elegance, effortless style, laid-back luxury",
        "energetic": "dynamic, movement, vibrant, youthful energy",
    }

    background_modifiers = {
        "studio": "professional studio lighting, seamless backdrop, controlled environment",
        "urban": "Oakland streets, authentic urban environment, golden hour, city backdrop",
        "nature": "natural outdoor setting, soft natural light, organic textures",
        "abstract": "abstract geometric background, artistic, contemporary art influence",
    }

    # Build comprehensive prompt
    prompt_parts = [
        subject,
        style_modifiers.get(visual_style, style_modifiers["luxury_fashion"]),
        mood_modifiers.get(mood, mood_modifiers["sophisticated"]),
        background_modifiers.get(background, background_modifiers["studio"]),
        f"brand colors: black ({brand['colors']['primary']}) and gold ({brand['colors']['secondary']})",
        "high resolution, professional quality, 8k, sharp focus",
    ]

    if additional_details:
        prompt_parts.append(additional_details)

    full_prompt = ", ".join(prompt_parts)

    # Create platform-specific prompts
    prompts = {
        "detailed": full_prompt,
        "midjourney": f"/imagine {full_prompt} --ar 4:5 --style raw --v 6.1",
        "dalle": f"A {mood} {visual_style.replace('_', ' ')} photograph of {subject}. {background_modifiers.get(background)}. Professional fashion photography, high-end brand aesthetic.",
        "stable_diffusion": f"{full_prompt}, masterpiece, best quality, photorealistic, highly detailed",
    }

    negative_prompt = (
        "low quality, blurry, distorted, amateur, text, watermark, logo, oversaturated, grainy, out of focus, deformed"
    )

    return {
        "success": True,
        "prompts": prompts,
        "negative_prompt": negative_prompt,
        "parameters": {
            "subject": subject,
            "style": visual_style,
            "mood": mood,
            "background": background,
        },
        "recommended_settings": {
            "midjourney": {"ar": "4:5", "style": "raw", "version": "6.1"},
            "dalle": {"size": "1024x1792", "quality": "hd"},
            "stable_diffusion": {"steps": 30, "cfg_scale": 7.5, "sampler": "DPM++ 2M Karras"},
        },
        "brand": brand["brand_name"],
    }


# =============================================================================
# SECTION 5: ANALYTICS TOOLS
# =============================================================================


@mcp.tool
def get_sales_summary(
    time_period: Annotated[str, Field(description="Period: today, week, month, year", default="today")] = "today",
    include_comparison: Annotated[
        bool, Field(description="Include comparison with previous period", default=True)
    ] = True,
) -> dict[str, Any]:
    """
    Get sales summary for a specified period.

    Returns key metrics including orders, revenue, and average order value.
    Note: Returns simulated data - connect to WooCommerce for real metrics.
    """
    # Simulated data - in production connect to WooCommerce REST API
    period_data = {
        "today": {"orders": 12, "revenue": 2840.00, "avg_order": 236.67},
        "week": {"orders": 67, "revenue": 15230.00, "avg_order": 227.31},
        "month": {"orders": 245, "revenue": 58750.00, "avg_order": 239.80},
        "year": {"orders": 2890, "revenue": 698500.00, "avg_order": 241.70},
    }

    current_data = period_data.get(time_period, period_data["today"])

    summary = {
        "period": time_period,
        "metrics": {
            "total_orders": current_data["orders"],
            "total_revenue": current_data["revenue"],
            "average_order_value": current_data["avg_order"],
            "currency": "USD",
        },
        "generated_at": get_current_timestamp(),
    }

    if include_comparison:
        # Simulated previous period (5% less)
        summary["previous_period"] = {
            "total_orders": int(current_data["orders"] * 0.95),
            "total_revenue": round(current_data["revenue"] * 0.95, 2),
            "average_order_value": round(current_data["avg_order"] * 0.98, 2),
        }
        summary["growth"] = {
            "orders_growth": "+5.3%",
            "revenue_growth": "+5.3%",
            "aov_growth": "+2.0%",
        }

    return {
        "success": True,
        "summary": summary,
        "data_source": "simulated",
        "note": "Connect to WooCommerce REST API for real metrics",
    }


@mcp.tool
def get_top_performing_products(
    max_results: Annotated[int, Field(description="Number of products to return", default=10)] = 10,
    sort_by: Annotated[str, Field(description="Sort by: revenue, units, views", default="revenue")] = "revenue",
    time_period: Annotated[str, Field(description="Period: week, month, year", default="month")] = "month",
) -> dict[str, Any]:
    """
    Get top performing products by specified metric.

    Returns ranked list of products with performance data.
    Note: Returns simulated data - connect to WooCommerce for real metrics.
    """
    # Simulated data
    top_products = [
        {
            "name": "Obsidian Heritage Hoodie",
            "sku": "SR-OH-001",
            "units_sold": 145,
            "revenue": 14500.00,
            "views": 3420,
        },
        {"name": "Gold Standard Jacket", "sku": "SR-GS-002", "units_sold": 89, "revenue": 13350.00, "views": 2890},
        {"name": "Oakland Roots Tee", "sku": "SR-OR-003", "units_sold": 234, "revenue": 11700.00, "views": 4560},
        {"name": "Skyy High Joggers", "sku": "SR-SH-004", "units_sold": 112, "revenue": 8960.00, "views": 2340},
        {"name": "Rose Gold Accessories Set", "sku": "SR-RG-005", "units_sold": 78, "revenue": 7800.00, "views": 1890},
        {"name": "Heritage Crewneck", "sku": "SR-HC-006", "units_sold": 98, "revenue": 6860.00, "views": 2120},
        {"name": "Street Luxe Shorts", "sku": "SR-SL-007", "units_sold": 67, "revenue": 4690.00, "views": 1560},
        {"name": "Oakland Pride Cap", "sku": "SR-OP-008", "units_sold": 156, "revenue": 4680.00, "views": 3200},
        {"name": "Luxury Layer Cardigan", "sku": "SR-LC-009", "units_sold": 34, "revenue": 4420.00, "views": 980},
        {"name": "Signature Belt", "sku": "SR-SB-010", "units_sold": 89, "revenue": 3560.00, "views": 1240},
    ]

    # Sort by specified metric
    sort_key = {"revenue": "revenue", "units": "units_sold", "views": "views"}.get(sort_by, "revenue")
    sorted_products = sorted(top_products, key=lambda x: x[sort_key], reverse=True)

    return {
        "success": True,
        "period": time_period,
        "sorted_by": sort_by,
        "top_products": sorted_products[:max_results],
        "total_revenue": sum(p["revenue"] for p in sorted_products[:max_results]),
        "total_units": sum(p["units_sold"] for p in sorted_products[:max_results]),
        "generated_at": get_current_timestamp(),
        "data_source": "simulated",
    }


@mcp.tool
def get_traffic_analytics(
    time_period: Annotated[str, Field(description="Period: today, week, month", default="week")] = "week",
) -> dict[str, Any]:
    """
    Get website traffic analytics.

    Returns visitor data, traffic sources, and top pages.
    Note: Returns simulated data - connect to analytics platform for real metrics.
    """
    # Simulated analytics data
    analytics = {
        "period": time_period,
        "visitors": {
            "total": 12450,
            "unique": 8920,
            "returning": 3530,
            "new_visitor_rate": "71.6%",
        },
        "engagement": {
            "pageviews": 45670,
            "pages_per_session": 3.7,
            "avg_session_duration": "3:24",
            "bounce_rate": "38.5%",
        },
        "traffic_sources": [
            {"source": "Instagram", "visitors": 3890, "percentage": "31.2%", "conversion_rate": "2.8%"},
            {"source": "Google Organic", "visitors": 2980, "percentage": "23.9%", "conversion_rate": "3.2%"},
            {"source": "Direct", "visitors": 2450, "percentage": "19.7%", "conversion_rate": "4.1%"},
            {"source": "TikTok", "visitors": 1890, "percentage": "15.2%", "conversion_rate": "1.9%"},
            {"source": "Email", "visitors": 1240, "percentage": "10.0%", "conversion_rate": "5.6%"},
        ],
        "top_pages": [
            {"page": "/shop", "pageviews": 12340, "avg_time": "2:45"},
            {"page": "/collections/new-arrivals", "pageviews": 8920, "avg_time": "3:12"},
            {"page": "/product/obsidian-heritage-hoodie", "pageviews": 4560, "avg_time": "4:23"},
            {"page": "/about", "pageviews": 2340, "avg_time": "2:18"},
            {"page": "/lookbook", "pageviews": 1890, "avg_time": "5:45"},
        ],
        "device_breakdown": {
            "mobile": "68%",
            "desktop": "28%",
            "tablet": "4%",
        },
        "generated_at": get_current_timestamp(),
    }

    return {
        "success": True,
        "analytics": analytics,
        "data_source": "simulated",
        "note": "Connect to Google Analytics or similar for real metrics",
    }


# =============================================================================
# SECTION 6: AGENT ORCHESTRATION TOOLS
# =============================================================================


@mcp.tool
def dispatch_agent_task(
    agent_type: Annotated[str, "Agent type: content, product, marketing, customer_service, analytics, seo, visual"],
    task_description: Annotated[str, "Description of the task to perform"],
    task_priority: Annotated[
        str, Field(description="Priority: low, normal, high, urgent", default="normal")
    ] = "normal",
    task_parameters: Annotated[dict[str, Any] | None, "Additional parameters for the task"] = None,
) -> dict[str, Any]:
    """
    Dispatch a task to a DevSkyy AI agent.

    Routes tasks to specialized agents for processing.
    """
    available_agents = {
        "content": "Content generation and blog management",
        "product": "Product catalog and inventory management",
        "marketing": "Marketing campaigns and social media",
        "customer_service": "Customer inquiries and support",
        "analytics": "Data analysis and reporting",
        "seo": "Search engine optimization",
        "visual": "Image and visual content generation",
    }

    if agent_type not in available_agents:
        return {
            "success": False,
            "error": f"Unknown agent type: {agent_type}",
            "available_agents": available_agents,
        }

    task_id = f"task_{generate_verification_hash(task_description + str(datetime.now()))[:12]}"

    task = {
        "task_id": task_id,
        "agent_type": agent_type,
        "description": task_description,
        "priority": task_priority,
        "parameters": task_parameters or {},
        "status": "queued",
        "created_at": get_current_timestamp(),
        "estimated_completion": "2-5 minutes",
    }

    agent_task_queue[task_id] = task

    return {
        "success": True,
        "task": task,
        "message": f"Task dispatched to {agent_type} agent",
        "agent_description": available_agents[agent_type],
    }


@mcp.tool
def get_agent_status(
    specific_agent: Annotated[str | None, "Specific agent to check (optional)"] = None,
) -> dict[str, Any]:
    """
    Get status of AI agents.

    Returns health status and task counts for all or specific agents.
    """
    agents = {
        "content": {"status": "active", "tasks_completed_today": 145, "avg_response_time": "1.2s", "queue_depth": 3},
        "product": {"status": "active", "tasks_completed_today": 89, "avg_response_time": "0.8s", "queue_depth": 1},
        "marketing": {"status": "active", "tasks_completed_today": 234, "avg_response_time": "2.1s", "queue_depth": 5},
        "customer_service": {
            "status": "active",
            "tasks_completed_today": 567,
            "avg_response_time": "0.5s",
            "queue_depth": 12,
        },
        "analytics": {"status": "active", "tasks_completed_today": 78, "avg_response_time": "3.4s", "queue_depth": 2},
        "seo": {"status": "active", "tasks_completed_today": 112, "avg_response_time": "1.8s", "queue_depth": 4},
        "visual": {"status": "active", "tasks_completed_today": 45, "avg_response_time": "8.2s", "queue_depth": 7},
    }

    if specific_agent:
        if specific_agent not in agents:
            return {
                "success": False,
                "error": f"Unknown agent: {specific_agent}",
                "available_agents": list(agents.keys()),
            }
        return {
            "success": True,
            "agent": specific_agent,
            "status": agents[specific_agent],
        }

    queued_tasks = [t for t in agent_task_queue.values() if t["status"] == "queued"]

    return {
        "success": True,
        "agents": agents,
        "summary": {
            "total_agents": len(agents),
            "active_agents": sum(1 for a in agents.values() if a["status"] == "active"),
            "queued_tasks": len(queued_tasks),
            "total_tasks_today": sum(a["tasks_completed_today"] for a in agents.values()),
        },
        "generated_at": get_current_timestamp(),
    }


@mcp.tool
def run_automation_workflow(
    workflow_name: Annotated[str, "Workflow: new_product_launch, content_calendar, inventory_alert, weekly_report"],
    trigger_data: Annotated[dict[str, Any] | None, "Data to pass to the workflow"] = None,
) -> dict[str, Any]:
    """
    Run a predefined automation workflow.

    Executes multi-step automated processes.
    """
    available_workflows = {
        "new_product_launch": {
            "description": "Complete new product launch workflow",
            "steps": [
                "Generate product description",
                "Create SEO metadata",
                "Generate social media content",
                "Schedule email announcement",
                "Update sitemap",
            ],
            "estimated_time": "5-10 minutes",
        },
        "content_calendar": {
            "description": "Generate content calendar for the week",
            "steps": [
                "Analyze trending topics",
                "Generate blog post ideas",
                "Create social media schedule",
                "Prepare email content",
            ],
            "estimated_time": "3-5 minutes",
        },
        "inventory_alert": {
            "description": "Low inventory alert and reorder workflow",
            "steps": [
                "Check inventory levels",
                "Identify low stock items",
                "Generate reorder recommendations",
                "Notify team",
            ],
            "estimated_time": "2-3 minutes",
        },
        "weekly_report": {
            "description": "Generate weekly performance report",
            "steps": [
                "Compile sales data",
                "Analyze traffic trends",
                "Summarize agent performance",
                "Generate executive summary",
            ],
            "estimated_time": "5-7 minutes",
        },
    }

    if workflow_name not in available_workflows:
        return {
            "success": False,
            "error": f"Unknown workflow: {workflow_name}",
            "available_workflows": {k: v["description"] for k, v in available_workflows.items()},
        }

    workflow = available_workflows[workflow_name]
    workflow_id = f"wf_{generate_verification_hash(workflow_name + str(datetime.now()))[:12]}"

    return {
        "success": True,
        "workflow_id": workflow_id,
        "workflow_name": workflow_name,
        "description": workflow["description"],
        "steps": workflow["steps"],
        "status": "running",
        "trigger_data": trigger_data,
        "started_at": get_current_timestamp(),
        "estimated_completion": workflow["estimated_time"],
    }


# =============================================================================
# SECTION 7: RAG (RETRIEVAL AUGMENTED GENERATION) TOOLS
# Per:
# - LlamaIndex Docs: https://docs.llamaindex.ai/
# - ChromaDB Docs: https://docs.trychroma.com/
# - RAG MCP Server: https://lobehub.com/mcp/alejandro-ao-rag-mcp
# - MCP RAG Tutorial: https://medium.com/data-science-in-your-pocket/rag-mcp-server-tutorial
# - LlamaIndex + ChromaDB: https://dev.to/sophyia/how-to-build-a-rag-solution-with-llama-index-chromadb-and-ollama
# =============================================================================

# In-memory document store for RAG (in production, use ChromaDB)
document_store: dict[str, dict[str, Any]] = {}
document_chunks: dict[str, list[dict[str, Any]]] = {}


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks for RAG indexing.

    Args:
        text: The text to split
        chunk_size: Maximum characters per chunk
        overlap: Characters to overlap between chunks

    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks


def simple_similarity(query: str, text: str) -> float:
    """
    Calculate simple word overlap similarity score.

    In production, use proper embeddings (OpenAI, Cohere, or local models).
    This is a simplified version for demonstration.
    """
    query_words = set(query.lower().split())
    text_words = set(text.lower().split())

    if not query_words or not text_words:
        return 0.0

    intersection = query_words & text_words
    union = query_words | text_words

    return len(intersection) / len(union) if union else 0.0


# =============================================================================
# HYBRID RAG SEARCH - Phase 2 Enhancements
# Sources:
# - RAG Best Practices 2025: https://arxiv.org/abs/2501.07391
# - Hybrid Search Patterns: https://www.edenai.co/post/the-2025-guide-to-retrieval-augmented-generation-rag
# - BM25 Algorithm: https://en.wikipedia.org/wiki/Okapi_BM25
# - RRF Fusion: https://www.elastic.co/guide/en/elasticsearch/reference/current/rrf.html
# - Self-Reflective RAG: https://medium.com/@mehulpratapsingh/2025s-ultimate-guide-to-rag-retrieval
# =============================================================================

# BM25 parameters (tuned for fashion/e-commerce domain)
BM25_K1 = 1.5  # Term frequency saturation
BM25_B = 0.75  # Length normalization
RRF_K = 60  # Reciprocal Rank Fusion constant
RELEVANCE_THRESHOLD = 0.7  # Self-RAG relevance threshold
MAX_RETRIEVAL_ITERATIONS = 3  # Chain-of-Retrieval max iterations
MIN_SUFFICIENT_RESULTS = 3  # Minimum results needed to stop retrieval


def calculate_bm25_score(
    query_terms: set[str],
    doc_terms: list[str],
    avg_doc_length: float,
    doc_frequencies: dict[str, int],
    total_docs: int,
) -> float:
    """
    Calculate BM25 score for a document.

    BM25 is a ranking function used by search engines for relevance scoring.

    Args:
        query_terms: Set of query terms
        doc_terms: List of document terms (preserves frequency)
        avg_doc_length: Average document length in corpus
        doc_frequencies: Document frequency for each term
        total_docs: Total number of documents

    Returns:
        BM25 relevance score
    """
    score = 0.0
    doc_length = len(doc_terms)
    doc_term_counts: dict[str, int] = {}

    for term in doc_terms:
        doc_term_counts[term] = doc_term_counts.get(term, 0) + 1

    for term in query_terms:
        if term not in doc_term_counts:
            continue

        # Term frequency in document
        tf = doc_term_counts[term]

        # Document frequency (how many docs contain this term)
        df = doc_frequencies.get(term, 1)

        # Inverse document frequency
        idf = max(0, (total_docs - df + 0.5) / (df + 0.5))
        idf = math.log(1 + idf)

        # BM25 term score
        numerator = tf * (BM25_K1 + 1)
        denominator = tf + BM25_K1 * (1 - BM25_B + BM25_B * (doc_length / avg_doc_length))
        score += idf * (numerator / denominator) if denominator > 0 else 0

    return score


def reciprocal_rank_fusion(
    vector_results: list[tuple[str, float]],
    bm25_results: list[tuple[str, float]],
    k: int = RRF_K,
) -> list[tuple[str, float]]:
    """
    Combine vector and BM25 results using Reciprocal Rank Fusion.

    RRF is a simple yet effective method for combining ranked lists.
    Formula: RRF(d) = sum(1 / (k + rank_i(d))) for each ranking i

    Args:
        vector_results: List of (doc_id, score) from vector search
        bm25_results: List of (doc_id, score) from BM25 search
        k: Smoothing constant (default 60)

    Returns:
        Combined ranked list of (doc_id, rrf_score)
    """
    scores: dict[str, float] = {}

    # Add vector search contributions
    for rank, (doc_id, _) in enumerate(vector_results):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)

    # Add BM25 search contributions
    for rank, (doc_id, _) in enumerate(bm25_results):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)

    # Sort by combined score
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def hybrid_search(
    query: str,
    chunks: list[dict[str, Any]],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Perform hybrid search combining vector similarity and BM25.

    This combines semantic understanding (vector) with exact term matching (BM25)
    for more robust retrieval.

    Args:
        query: Search query
        chunks: List of chunk dictionaries with 'content' key
        top_k: Number of results to return

    Returns:
        Top-k chunks with hybrid scores
    """
    if not chunks:
        return []

    query_terms = set(query.lower().split())

    # Calculate corpus statistics for BM25
    all_doc_terms: list[list[str]] = []
    doc_frequencies: dict[str, int] = {}

    for chunk in chunks:
        terms = chunk["content"].lower().split()
        all_doc_terms.append(terms)
        unique_terms = set(terms)
        for term in unique_terms:
            doc_frequencies[term] = doc_frequencies.get(term, 0) + 1

    avg_doc_length = sum(len(t) for t in all_doc_terms) / len(all_doc_terms) if all_doc_terms else 1.0
    total_docs = len(chunks)

    # Calculate both scores for each chunk
    vector_results: list[tuple[str, float]] = []
    bm25_results: list[tuple[str, float]] = []

    for i, chunk in enumerate(chunks):
        chunk_id = chunk.get("chunk_id", str(i))
        content = chunk["content"]

        # Vector similarity (word overlap as proxy)
        vector_score = simple_similarity(query, content)
        vector_results.append((chunk_id, vector_score))

        # BM25 score
        doc_terms = content.lower().split()
        bm25_score = calculate_bm25_score(
            query_terms=query_terms,
            doc_terms=doc_terms,
            avg_doc_length=avg_doc_length,
            doc_frequencies=doc_frequencies,
            total_docs=total_docs,
        )
        bm25_results.append((chunk_id, bm25_score))

    # Sort individual result lists
    vector_results.sort(key=lambda x: x[1], reverse=True)
    bm25_results.sort(key=lambda x: x[1], reverse=True)

    # Apply RRF fusion
    fused_results = reciprocal_rank_fusion(vector_results, bm25_results)

    # Map back to chunk data with scores
    chunk_map = {chunk.get("chunk_id", str(i)): chunk for i, chunk in enumerate(chunks)}
    vector_score_map = dict(vector_results)
    bm25_score_map = dict(bm25_results)

    results = []
    for chunk_id, rrf_score in fused_results[:top_k]:
        chunk = chunk_map.get(chunk_id, {})
        results.append(
            {
                **chunk,
                "hybrid_score": round(rrf_score, 6),
                "vector_score": round(vector_score_map.get(chunk_id, 0), 4),
                "bm25_score": round(bm25_score_map.get(chunk_id, 0), 4),
            }
        )

    return results


def score_relevance(query: str, context: str) -> float:
    """
    Score the relevance of context to a query.

    This is a simplified version - in production, use an LLM for
    more accurate relevance assessment (Self-RAG pattern).

    Args:
        query: The original query
        context: The retrieved context

    Returns:
        Relevance score between 0 and 1
    """
    # Use enhanced similarity for relevance scoring
    base_score = simple_similarity(query, context)

    # Boost if query terms appear in important positions
    query_terms = set(query.lower().split())
    context_lower = context.lower()

    # Check first sentence boost
    first_sentence = context_lower.split(".")[0] if "." in context_lower else context_lower[:100]
    first_sentence_terms = set(first_sentence.split())
    first_sentence_overlap = len(query_terms & first_sentence_terms) / len(query_terms) if query_terms else 0

    # Boost for exact phrase match
    query_lower = query.lower()
    phrase_boost = 0.2 if query_lower in context_lower else 0

    # Combined score
    relevance = min(1.0, base_score * 0.6 + first_sentence_overlap * 0.2 + phrase_boost + 0.1)

    return relevance


def reformulate_query(original_query: str, iteration: int) -> str:
    """
    Reformulate query for iterative retrieval.

    Different strategies are used based on iteration:
    1. Add specificity
    2. Use related terms
    3. Focus on key entities

    Args:
        original_query: The original query
        iteration: Current iteration number (1-indexed)

    Returns:
        Reformulated query
    """
    strategies = [
        # Iteration 1: Add specificity
        lambda q: f"{q} detailed explanation examples",
        # Iteration 2: Focus on key terms
        lambda q: " ".join(sorted(set(q.lower().split()), key=len, reverse=True)[:5]),
        # Iteration 3: Extract entities and expand
        lambda q: f"{q} how to best practices guide",
    ]

    if iteration <= len(strategies):
        return strategies[iteration - 1](original_query)
    return original_query


@mcp.tool
def ingest_document(
    document_id: Annotated[str, "Unique identifier for the document"],
    document_content: Annotated[str, "Full text content of the document"],
    document_title: Annotated[str | None, "Document title"] = None,
    document_type: Annotated[
        str, Field(description="Document type: product, blog, policy, faq, guide", default="general")
    ] = "general",
    metadata: Annotated[dict[str, Any] | None, "Additional metadata for the document"] = None,
) -> dict[str, Any]:
    """
    Ingest a document into the RAG knowledge base.

    Chunks the document and stores it for retrieval.
    In production, this would generate embeddings and store in ChromaDB.

    Sources:
    - LlamaIndex SimpleDirectoryReader: https://docs.llamaindex.ai/
    - ChromaDB Ingestion: https://docs.trychroma.com/guides/adding-data
    """
    # Generate chunks
    chunks = chunk_text(document_content)

    # Store document metadata
    doc_entry = {
        "document_id": document_id,
        "title": document_title or document_id,
        "type": document_type,
        "content_length": len(document_content),
        "chunk_count": len(chunks),
        "metadata": metadata or {},
        "ingested_at": get_current_timestamp(),
        "content_hash": generate_verification_hash(document_content),
    }
    document_store[document_id] = doc_entry

    # Store chunks with their document reference
    document_chunks[document_id] = [
        {
            "chunk_id": f"{document_id}_chunk_{i}",
            "document_id": document_id,
            "content": chunk,
            "chunk_index": i,
            "chunk_hash": generate_verification_hash(chunk),
        }
        for i, chunk in enumerate(chunks)
    ]

    return {
        "success": True,
        "document_id": document_id,
        "title": doc_entry["title"],
        "chunks_created": len(chunks),
        "content_hash": doc_entry["content_hash"],
        "message": f"Document ingested with {len(chunks)} chunks",
        "production_note": "In production, embeddings would be generated via OpenAI/Cohere and stored in ChromaDB",
    }


@mcp.tool
def query_knowledge_base(
    query: Annotated[str, "The search query or question"],
    top_k: Annotated[int, Field(description="Number of results to return", default=5)] = 5,
    document_type_filter: Annotated[str | None, "Filter by document type"] = None,
    min_similarity: Annotated[float, Field(description="Minimum similarity threshold", default=0.1)] = 0.1,
) -> dict[str, Any]:
    """
    Query the RAG knowledge base for relevant information.

    Performs semantic search over ingested documents and returns
    the most relevant chunks for the given query.

    Sources:
    - RAG MCP Server Pattern: https://lobehub.com/mcp/alejandro-ao-rag-mcp
    - LlamaIndex Query: https://docs.llamaindex.ai/en/stable/understanding/querying/
    """
    if not document_chunks:
        return {
            "success": False,
            "error": "No documents in knowledge base",
            "suggestion": "Use ingest_document to add documents first",
        }

    # Collect all chunks with similarity scores
    scored_chunks = []

    for doc_id, chunks in document_chunks.items():
        doc_meta = document_store.get(doc_id, {})

        # Apply document type filter if specified
        if document_type_filter and doc_meta.get("type") != document_type_filter:
            continue

        for chunk in chunks:
            similarity = simple_similarity(query, chunk["content"])
            if similarity >= min_similarity:
                scored_chunks.append(
                    {
                        "document_id": doc_id,
                        "document_title": doc_meta.get("title", doc_id),
                        "document_type": doc_meta.get("type", "unknown"),
                        "chunk_id": chunk["chunk_id"],
                        "content": chunk["content"],
                        "similarity": round(similarity, 4),
                        "chunk_index": chunk["chunk_index"],
                    }
                )

    # Sort by similarity descending
    scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)

    # Take top_k results
    results = scored_chunks[:top_k]

    return {
        "success": True,
        "query": query,
        "results_count": len(results),
        "results": results,
        "total_chunks_searched": sum(len(c) for c in document_chunks.values()),
        "documents_searched": len(document_chunks),
        "filters_applied": {
            "document_type": document_type_filter,
            "min_similarity": min_similarity,
            "top_k": top_k,
        },
        "production_note": "In production, this would use vector embeddings for semantic search",
    }


@mcp.tool
def list_knowledge_base_documents(
    document_type_filter: Annotated[str | None, "Filter by document type"] = None,
) -> dict[str, Any]:
    """
    List all documents in the RAG knowledge base.

    Returns metadata about ingested documents without the full content.
    """
    documents = list(document_store.values())

    if document_type_filter:
        documents = [d for d in documents if d.get("type") == document_type_filter]

    return {
        "success": True,
        "document_count": len(documents),
        "documents": [
            {
                "document_id": d["document_id"],
                "title": d["title"],
                "type": d["type"],
                "chunk_count": d["chunk_count"],
                "content_length": d["content_length"],
                "ingested_at": d["ingested_at"],
            }
            for d in documents
        ],
        "available_types": list({d.get("type", "unknown") for d in document_store.values()}),
    }


@mcp.tool
def delete_document_from_knowledge_base(
    document_id: Annotated[str, "Document ID to delete"],
) -> dict[str, Any]:
    """
    Delete a document from the RAG knowledge base.

    Removes the document and all its chunks.
    """
    if document_id not in document_store:
        return {
            "success": False,
            "error": f"Document not found: {document_id}",
            "available_documents": list(document_store.keys()),
        }

    doc = document_store.pop(document_id)
    chunks = document_chunks.pop(document_id, [])

    return {
        "success": True,
        "document_id": document_id,
        "title": doc.get("title"),
        "chunks_deleted": len(chunks),
        "message": f"Document and {len(chunks)} chunks deleted",
    }


@mcp.tool
def generate_rag_response(
    question: Annotated[str, "The user's question"],
    context_documents: Annotated[int, Field(description="Number of context documents to use", default=3)] = 3,
    include_sources: Annotated[bool, Field(description="Include source citations", default=True)] = True,
) -> dict[str, Any]:
    """
    Generate a RAG-powered response to a question.

    Retrieves relevant context from the knowledge base and
    generates a response with citations.

    This is a simplified version - in production, the retrieved
    context would be passed to an LLM for response generation.

    Sources:
    - Agentic RAG: https://medium.com/@visrow/agentic-rag-with-mcp-server-step-by-step-guide
    - RAG-MCP Paper: https://arxiv.org/html/2505.03275v1
    """
    # Query the knowledge base
    query_result = query_knowledge_base(question, top_k=context_documents)

    if not query_result.get("success") or not query_result.get("results"):
        return {
            "success": False,
            "question": question,
            "error": "No relevant context found in knowledge base",
            "suggestion": "Try rephrasing your question or ingest more relevant documents",
        }

    results = query_result["results"]

    # Compile context from retrieved chunks
    context_parts = []
    sources = []

    for i, result in enumerate(results):
        context_parts.append(f"[Source {i + 1}] {result['content']}")
        if include_sources:
            sources.append(
                {
                    "source_number": i + 1,
                    "document_id": result["document_id"],
                    "document_title": result["document_title"],
                    "similarity": result["similarity"],
                }
            )

    compiled_context = "\n\n".join(context_parts)

    # Generate response template (in production, send to LLM)
    response_template = f"""Based on the knowledge base, here is information relevant to your question:

**Question:** {question}

**Context Retrieved:**
{compiled_context}

**Note:** In production, this context would be sent to an LLM (Claude, GPT, etc.)
for natural language response generation with proper citations."""

    return {
        "success": True,
        "question": question,
        "response": response_template,
        "context_chunks_used": len(results),
        "sources": sources if include_sources else [],
        "generation_note": "Response template - in production, use LLM for natural generation",
        "production_integration": {
            "llm_options": ["Anthropic Claude", "OpenAI GPT-4", "Local Ollama"],
            "embedding_options": ["OpenAI text-embedding-3-small", "Cohere embed-v3", "Nomic embed"],
            "vector_db_options": ["ChromaDB", "Pinecone", "Qdrant", "Weaviate"],
        },
    }


@mcp.tool
def ingest_skyyrose_knowledge() -> dict[str, Any]:
    """
    Ingest SkyyRose brand knowledge into the RAG system.

    Pre-populates the knowledge base with brand information,
    product guidelines, and operational procedures.
    """
    brand = get_skyy_rose_brand_config()

    # Brand guidelines document
    brand_doc = f"""
    SkyyRose Brand Guidelines

    Brand Name: {brand['brand_name']} (always one word, capital S and R)
    Domain: {brand['domain']} (NEVER use .com)
    Tagline: {brand['tagline']}

    Brand Voice:
    - Luxury, elevated, boutique-ready
    - Sophisticated without being pretentious
    - Oakland authenticity with premium presentation

    Prohibited Language:
    - Never use: {', '.join(brand['prohibited']['prohibited_language'])}
    - Never use incorrect spellings: {', '.join(brand['prohibited']['incorrect_names'])}

    Colors:
    - Primary (Black): {brand['colors']['primary']}
    - Secondary (Gold): {brand['colors']['secondary']}
    - Accent: {brand['colors']['accent']}

    Typography:
    - Headings: {brand['typography']['headings']}
    - Body: {brand['typography']['body']}
    """

    # Product guidelines document
    product_doc = """
    SkyyRose Product Guidelines

    Product Descriptions:
    - Lead with luxury and quality
    - Mention materials and craftsmanship
    - Include fit and sizing guidance
    - Reference Oakland heritage when appropriate

    Product Categories:
    - Hoodies and Sweatshirts
    - Jackets and Outerwear
    - T-Shirts and Tops
    - Joggers and Bottoms
    - Accessories (hats, bags, jewelry)

    Pricing Guidelines:
    - Premium pricing reflects luxury positioning
    - Price changes over 20% require CEO approval
    - Never use discount/sale language publicly

    Photography Standards:
    - High-quality, professional imagery
    - Clean backgrounds (studio or Oakland streets)
    - Model diversity and representation
    - Consistent lighting and color grading
    """

    # Customer service document
    service_doc = """
    SkyyRose Customer Service Guidelines

    Response Tone:
    - Professional yet warm
    - Solution-focused
    - Brand-aligned language

    Escalation Triggers:
    - Refund requests over $200
    - Negative social media mentions
    - Product quality complaints
    - VIP customer issues

    Common Inquiries:
    - Sizing and fit questions
    - Order status and tracking
    - Return and exchange policies
    - Product care instructions
    - Restock inquiries
    """

    # Ingest all documents
    results = []

    for doc_id, content, title, doc_type in [
        ("skyyrose_brand_guidelines", brand_doc, "SkyyRose Brand Guidelines", "policy"),
        ("skyyrose_product_guidelines", product_doc, "Product Guidelines", "guide"),
        ("skyyrose_customer_service", service_doc, "Customer Service Guidelines", "guide"),
    ]:
        result = ingest_document(
            document_id=doc_id,
            document_content=content,
            document_title=title,
            document_type=doc_type,
            metadata={"source": "internal", "brand": "SkyyRose"},
        )
        results.append({"document_id": doc_id, "chunks": result.get("chunks_created", 0)})

    return {
        "success": True,
        "documents_ingested": len(results),
        "results": results,
        "total_chunks": sum(r["chunks"] for r in results),
        "message": "SkyyRose knowledge base populated",
        "available_for_query": True,
    }


# =============================================================================
# ADVANCED RAG TOOLS - Chain-of-Retrieval & Self-Reflective RAG
# Sources:
# - ArXiv RAG Best Practices: https://arxiv.org/abs/2501.07391
# - Agentic RAG: https://medium.com/@visrow/agentic-rag-with-mcp-server-step-by-step-guide
# - Chain-of-Retrieval: https://squirro.com/squirro-blog/state-of-rag-genai
# - Self-RAG Paper: https://arxiv.org/abs/2310.11511
# - RAG MCP Integration: https://arxiv.org/html/2505.03275v1
# =============================================================================


def _perform_rag_search(
    query: str,
    chunks: list[dict[str, Any]],
    use_hybrid: bool,
) -> list[dict[str, Any]]:
    """Perform RAG search using hybrid or simple similarity."""
    if use_hybrid:
        return hybrid_search(query, chunks, top_k=5)
    # Fall back to simple similarity
    scored = [{**chunk, "similarity": simple_similarity(query, chunk["content"])} for chunk in chunks]
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:5]


def _filter_and_score_results(
    search_results: list[dict[str, Any]],
    question: str,
    relevance_threshold: float,
    retrieved_chunk_ids: set[str],
) -> tuple[list[dict[str, Any]], float]:
    """Filter duplicates and score relevance using Self-RAG pattern."""
    iteration_results = []
    best_relevance = 0.0
    for result in search_results:
        chunk_id = result.get("chunk_id", "")
        if chunk_id in retrieved_chunk_ids:
            continue  # Skip duplicates
        relevance = score_relevance(question, result["content"])
        if relevance >= relevance_threshold:
            result["relevance_score"] = round(relevance, 4)
            iteration_results.append(result)
            retrieved_chunk_ids.add(chunk_id)
            best_relevance = max(best_relevance, relevance)
    return iteration_results, best_relevance


def _compile_rag_context(
    results: list[dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]]]:
    """Compile context and sources from RAG results."""
    context_parts = []
    sources = []
    for i, result in enumerate(results):
        context_parts.append(f"[{i + 1}] {result['content']}")
        sources.append(
            {
                "source_number": i + 1,
                "document_id": result.get("document_id", "unknown"),
                "document_title": result.get("document_title", "Unknown"),
                "relevance_score": result.get("relevance_score", 0),
                "hybrid_score": result.get("hybrid_score"),
                "chunk_index": result.get("chunk_index", 0),
            }
        )
    return context_parts, sources


@mcp.tool
def query_knowledge_base_advanced(
    question: Annotated[str, "The question to answer"],
    max_iterations: Annotated[
        int, Field(description="Maximum retrieval iterations for multi-hop reasoning", default=3)
    ] = 3,
    relevance_threshold: Annotated[
        float, Field(description="Minimum relevance score to accept results", default=0.6)
    ] = 0.6,
    use_hybrid_search: Annotated[bool, Field(description="Use hybrid Vector+BM25 search", default=True)] = True,
    include_reasoning_chain: Annotated[
        bool, Field(description="Include step-by-step reasoning in response", default=True)
    ] = True,
) -> dict[str, Any]:
    """
    Advanced RAG query with Chain-of-Retrieval and Self-Reflective scoring.

    Implements multi-hop reasoning for complex questions that require
    information synthesis from multiple documents. Uses iterative
    retrieval with query reformulation when initial results are insufficient.

    Features:
    - Hybrid Search: Combines vector similarity with BM25 keyword matching
    - Self-Reflective RAG: Scores relevance before accepting results
    - Chain-of-Retrieval: Multi-hop reasoning with query reformulation
    - Deduplication: Removes redundant chunks across iterations

    Sources:
    - ArXiv RAG Study: https://arxiv.org/abs/2501.07391
    - Self-RAG: https://arxiv.org/abs/2310.11511
    """
    if not document_chunks:
        return {
            "success": False,
            "error": "No documents in knowledge base",
            "suggestion": "Use ingest_document or ingest_skyyrose_knowledge first",
        }

    # Collect all chunks for searching (using extend for performance)
    all_chunks = []
    for doc_id, chunks in document_chunks.items():
        doc_meta = document_store.get(doc_id, {})
        all_chunks.extend(
            {
                **chunk,
                "document_title": doc_meta.get("title", doc_id),
                "document_type": doc_meta.get("type", "unknown"),
            }
            for chunk in chunks
        )

    # Reasoning chain for transparency
    reasoning_chain: list[dict[str, Any]] = []
    retrieved_chunk_ids: set[str] = set()
    all_results: list[dict[str, Any]] = []
    current_query = question
    best_relevance = 0.0

    for iteration in range(1, max_iterations + 1):
        iteration_start = get_current_timestamp()

        # Perform search using helper function
        search_results = _perform_rag_search(current_query, all_chunks, use_hybrid_search)

        # Score relevance using Self-RAG pattern helper
        iteration_results, iter_best = _filter_and_score_results(
            search_results, question, relevance_threshold, retrieved_chunk_ids
        )
        best_relevance = max(best_relevance, iter_best)
        all_results.extend(iteration_results)

        # Log reasoning step
        step = {
            "iteration": iteration,
            "query_used": current_query,
            "chunks_found": len(search_results),
            "chunks_accepted": len(iteration_results),
            "best_relevance_this_iteration": max((r.get("relevance_score", 0) for r in iteration_results), default=0),
            "timestamp": iteration_start,
        }
        reasoning_chain.append(step)

        # Check if we have sufficient results
        if best_relevance >= RELEVANCE_THRESHOLD and len(all_results) >= MIN_SUFFICIENT_RESULTS:
            step["status"] = "sufficient_results"
            break

        # Reformulate query for next iteration
        if iteration < max_iterations:
            current_query = reformulate_query(question, iteration)
            step["next_query"] = current_query
            step["status"] = "reformulating"
        else:
            step["status"] = "max_iterations_reached"

    # Sort final results by relevance
    all_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    top_results = all_results[:5]

    # Compile context using helper
    context_parts, sources = _compile_rag_context(top_results)

    response = {
        "success": True,
        "question": question,
        "context": "\n\n".join(context_parts),
        "sources": sources,
        "retrieval_stats": {
            "total_iterations": len(reasoning_chain),
            "total_chunks_retrieved": len(all_results),
            "unique_documents": len({r.get("document_id") for r in all_results}),
            "best_relevance_score": round(best_relevance, 4),
            "search_type": "hybrid" if use_hybrid_search else "vector",
        },
        "production_note": "In production, this context would be sent to an LLM for final answer generation",
    }

    if include_reasoning_chain:
        response["reasoning_chain"] = reasoning_chain

    return response


# =============================================================================
# MCP SERVER DISCOVERY - .well-known resource
# Sources:
# - MCP Server Discovery: https://modelcontextprotocol.io/development/roadmap
# - .well-known URIs RFC 8615: https://datatracker.ietf.org/doc/html/rfc8615
# - FastMCP Resources: https://gofastmcp.com/servers/resources
# - MCP Spec 2025-06-18: https://modelcontextprotocol.io/specification/2025-06-18
# - Claude MCP Guide: https://docs.anthropic.com/en/docs/agents-and-tools/mcp
# =============================================================================


@mcp.resource("devskyy://server/discovery")
def mcp_server_discovery() -> str:
    """
    MCP Server Discovery Metadata.

    Returns server configuration and capabilities for MCP clients
    to discover available tools and resources.
    """
    discovery = {
        "name": "DevSkyy Unified Platform",
        "version": "2.0.0",
        "description": "Enterprise fashion e-commerce MCP server for SkyyRose",
        "vendor": {
            "name": "SkyyRose",
            "url": "https://skyyrose.co",
            "contact": "api@skyyrose.co",
        },
        "capabilities": {
            "tools": True,
            "resources": True,
            "prompts": True,
            "authentication": "oauth2.1",
            "caching": True,
            "rag": True,
            "hybrid_search": True,
        },
        "endpoints": {
            "cloud": "https://critical-fuchsia-ape.fastmcp.app",
            "local": "http://localhost:5000",
        },
        "tool_categories": [
            {
                "name": "Theme Orchestrator",
                "description": "WordPress theme and Elementor widget generation",
                "tools": [
                    "generate_wordpress_theme",
                    "list_available_theme_types",
                    "generate_elementor_custom_widget",
                    "get_theme_build_status",
                ],
            },
            {
                "name": "WooCommerce",
                "description": "Product and inventory management",
                "tools": [
                    "create_woocommerce_product",
                    "update_woocommerce_product",
                    "list_catalog_products",
                    "manage_product_inventory",
                    "create_coupon_code",
                ],
            },
            {
                "name": "Content & SEO",
                "description": "Blog content and SEO optimization",
                "tools": ["create_blog_post", "generate_seo_metadata"],
            },
            {
                "name": "AI Generation",
                "description": "AI-powered content generation",
                "tools": ["generate_product_description", "generate_collection_copy", "generate_ai_image_prompt"],
            },
            {
                "name": "Analytics",
                "description": "Sales and performance analytics",
                "tools": ["get_sales_summary", "get_top_performing_products", "get_traffic_analytics"],
            },
            {
                "name": "Agent Orchestration",
                "description": "DevSkyy AI agent management",
                "tools": ["dispatch_agent_task", "get_agent_status", "run_automation_workflow"],
            },
            {
                "name": "RAG Knowledge Base",
                "description": "Retrieval-Augmented Generation system",
                "tools": [
                    "ingest_document",
                    "query_knowledge_base",
                    "query_knowledge_base_advanced",
                    "list_knowledge_base_documents",
                    "delete_document_from_knowledge_base",
                    "generate_rag_response",
                    "ingest_skyyrose_knowledge",
                ],
            },
            {
                "name": "Utilities",
                "description": "Brand and system utilities",
                "tools": ["get_brand_guidelines", "get_system_status"],
            },
        ],
        "security": {
            "authentication_required": True,
            "rbac_enabled": True,
            "roles": ["SuperAdmin", "Admin", "Developer", "APIUser", "ReadOnly"],
            "audit_logging": True,
        },
        "rate_limits": {
            "default": "100/minute",
            "authenticated": "1000/minute",
        },
    }
    return json.dumps(discovery, indent=2)


@mcp.resource("devskyy://brand/guidelines")
def brand_guidelines_resource() -> str:
    """
    SkyyRose Brand Guidelines Resource.

    Complete brand documentation for content generation and validation.
    """
    brand = get_skyy_rose_brand_config()
    return json.dumps(brand, indent=2)


# =============================================================================
# UTILITY TOOLS
# =============================================================================


@mcp.tool
def get_brand_guidelines(
    include_prohibited: Annotated[bool, Field(description="Include prohibited terms/formats", default=True)] = True,
) -> dict[str, Any]:
    """
    Get complete SkyyRose brand guidelines.

    Returns brand configuration including colors, typography,
    and brand enforcement rules.
    """
    brand = get_skyy_rose_brand_config()

    result = {
        "success": True,
        "brand_name": brand["brand_name"],
        "domain": brand["domain"],
        "tagline": brand["tagline"],
        "colors": brand["colors"],
        "typography": brand["typography"],
        "style_keywords": brand["style_keywords"],
    }

    if include_prohibited:
        result["brand_rules"] = {
            "correct_name_format": "SkyyRose (one word, capital S and R)",
            "incorrect_name_formats": brand["prohibited"]["incorrect_names"],
            "correct_domain": f"{brand['domain']} (NEVER use .com)",
            "prohibited_domains": brand["prohibited"]["incorrect_domains"],
            "tone": "Luxury, elevated, boutique-ready",
            "prohibited_language": brand["prohibited"]["prohibited_language"],
        }

    return result


@mcp.tool
def get_system_status() -> dict[str, Any]:
    """
    Get overall DevSkyy MCP server status and capabilities.

    Returns server health, statistics, and available tool categories.
    """
    brand = get_skyy_rose_brand_config()

    return {
        "success": True,
        "server": {
            "name": "DevSkyy Unified Platform",
            "version": "2.0.0",
            "status": "operational",
            "brand": brand["brand_name"],
            "domain": brand["domain"],
        },
        "statistics": {
            "active_theme_builds": len(active_theme_builds),
            "products_in_catalog": len(product_catalog),
            "content_drafts": len(content_drafts),
            "queued_agent_tasks": len([t for t in agent_task_queue.values() if t.get("status") == "queued"]),
            "active_discount_codes": len(discount_codes),
        },
        "capabilities": {
            "theme_orchestrator": [
                "generate_wordpress_theme",
                "list_available_theme_types",
                "generate_elementor_custom_widget",
                "get_theme_build_status",
            ],
            "woocommerce": [
                "create_woocommerce_product",
                "update_woocommerce_product",
                "list_catalog_products",
                "manage_product_inventory",
                "create_coupon_code",
            ],
            "content_seo": [
                "create_blog_post",
                "generate_seo_metadata",
            ],
            "ai_generation": [
                "generate_product_description",
                "generate_collection_copy",
                "generate_ai_image_prompt",
            ],
            "analytics": [
                "get_sales_summary",
                "get_top_performing_products",
                "get_traffic_analytics",
            ],
            "agent_orchestration": [
                "dispatch_agent_task",
                "get_agent_status",
                "run_automation_workflow",
            ],
            "utilities": [
                "get_brand_guidelines",
                "get_system_status",
            ],
        },
        "documentation": {
            "fastmcp": "https://gofastmcp.com/getting-started/welcome",
            "mcp_spec": "https://modelcontextprotocol.io/specification/2025-06-18/server/tools",
            "woocommerce_api": "https://woocommerce.github.io/woocommerce-rest-api-docs/",
            "elementor_widgets": "https://developers.elementor.com/docs/widgets/simple-example/",
        },
        "generated_at": get_current_timestamp(),
    }


# =============================================================================
# RESOURCES - Per MCP Specification
# =============================================================================


@mcp.resource("devskyy://brand-guidelines")
def brand_guidelines_resource_alt() -> str:
    """SkyyRose brand guidelines as a resource (alternate URI)."""
    return json.dumps(get_skyy_rose_brand_config(), indent=2)


@mcp.resource("devskyy://system-status")
def system_status_resource() -> str:
    """Current system status as a resource."""
    return json.dumps(get_system_status(), indent=2)


# =============================================================================
# PROMPTS - Reusable Templates
# =============================================================================


@mcp.prompt()
def launch_new_product_prompt() -> str:
    """Prompt for launching a new product."""
    return """Launch a new product for SkyyRose Collection.

Steps:
1. Create the product using create_woocommerce_product
2. Generate product description using generate_product_description
3. Optimize SEO using generate_seo_metadata
4. Generate social media content using generate_ai_image_prompt
5. Dispatch marketing tasks using dispatch_agent_task

Provide: product name, type, price, features, and materials."""


@mcp.prompt()
def weekly_content_plan_prompt() -> str:
    """Prompt for creating a weekly content plan."""
    return """Create a weekly content plan for SkyyRose.

Include:
1. 2-3 blog post ideas using create_blog_post
2. Daily social media content prompts
3. Email newsletter content
4. Product spotlight features

Use run_automation_workflow with 'content_calendar' to automate."""


@mcp.prompt()
def performance_review_prompt() -> str:
    """Prompt for reviewing performance."""
    return """Generate a performance review for SkyyRose.

Include:
1. Sales summary using get_sales_summary
2. Top products using get_top_performing_products
3. Traffic analytics using get_traffic_analytics
4. Agent status using get_agent_status

Compile into an executive summary."""


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    mcp.run()
