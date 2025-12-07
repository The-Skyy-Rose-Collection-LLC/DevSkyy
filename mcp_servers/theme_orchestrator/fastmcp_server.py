"""
FastMCP Cloud-Compatible Theme Orchestrator

This version is designed to run on FastMCP.app (like critical-fuchsia-ape).
It's a streamlined version that can be deployed to the cloud.

To deploy to FastMCP:
1. Go to https://fastmcp.app
2. Create a new server or update existing
3. Paste this code or upload this file
4. Get the endpoint URL

Usage locally:
    fastmcp dev mcp_servers/theme_orchestrator/fastmcp_server.py
"""

from datetime import datetime
import json
from typing import Any

from fastmcp import FastMCP


# Create FastMCP server
mcp = FastMCP(
    name="SkyyRose Theme Orchestrator",
    version="1.0.0",
    description="WordPress theme orchestration for SkyyRose luxury fashion brand",
)

# In-memory state for builds
active_builds: dict[str, dict[str, Any]] = {}


def get_skyy_rose_defaults() -> dict[str, Any]:
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
    }


# =============================================================================
# THEME GENERATION TOOLS
# =============================================================================


@mcp.tool()
def generate_theme(
    theme_name: str,
    theme_type: str = "luxury_fashion",
    pages: list[str] | None = None,
    include_woocommerce: bool = True,
) -> dict[str, Any]:
    """
    Generate a complete WordPress theme with Elementor support.

    Args:
        theme_name: Name for the generated theme
        theme_type: Type of theme (luxury_fashion, streetwear, minimalist, ecommerce)
        pages: Pages to generate layouts for
        include_woocommerce: Include WooCommerce integration

    Returns:
        Theme configuration and file contents
    """
    if pages is None:
        pages = ["home", "shop", "product", "about", "contact", "blog"]

    build_id = f"build_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{theme_name.replace(' ', '_')}"
    brand = get_skyy_rose_defaults()

    # Generate theme structure
    theme_config = generate_theme_config(theme_name, theme_type, brand, pages, include_woocommerce)

    # Store build
    active_builds[build_id] = {
        "status": "completed",
        "theme_name": theme_name,
        "started_at": datetime.now().isoformat(),
        "config": theme_config,
    }

    return {
        "success": True,
        "build_id": build_id,
        "theme_name": theme_name,
        "theme_type": theme_type,
        "theme_config": theme_config,
        "files": generate_theme_files(theme_name, theme_type, brand),
        "next_steps": [
            "Download the generated files",
            "Upload to WordPress via Appearance > Themes > Add New",
            "Activate and customize with Elementor",
        ],
    }


def generate_theme_config(
    name: str, theme_type: str, brand: dict, pages: list, woocommerce: bool
) -> dict[str, Any]:
    """Generate theme configuration."""
    theme_templates = {
        "luxury_fashion": {
            "style": "elegant",
            "layout": "full-width",
            "animations": "subtle",
        },
        "streetwear": {
            "style": "bold",
            "layout": "grid",
            "animations": "dynamic",
        },
        "minimalist": {
            "style": "clean",
            "layout": "centered",
            "animations": "minimal",
        },
        "ecommerce": {
            "style": "commercial",
            "layout": "full-width",
            "animations": "smooth",
        },
    }

    template = theme_templates.get(theme_type, theme_templates["luxury_fashion"])

    return {
        "metadata": {
            "name": name,
            "version": "1.0.0",
            "author": "SkyyRose Theme Orchestrator",
            "theme_type": theme_type,
        },
        "template": template,
        "brand": brand,
        "pages": pages,
        "features": {
            "woocommerce": woocommerce,
            "elementor": True,
            "responsive": True,
        },
    }


def generate_theme_files(name: str, theme_type: str, brand: dict) -> dict[str, str]:
    """Generate actual theme file contents."""
    slug = name.lower().replace(" ", "-")
    func_slug = name.lower().replace(" ", "_")

    files = {
        "style.css": f"""/*
Theme Name: {name}
Theme URI: https://skyyrose.co
Description: Custom {theme_type} theme for SkyyRose Collection
Version: 1.0.0
Author: SkyyRose Theme Orchestrator
Author URI: https://skyyrose.co
Text Domain: {slug}
License: Proprietary
*/

:root {{
    --primary-color: {brand['colors']['primary']};
    --secondary-color: {brand['colors']['secondary']};
    --accent-color: {brand['colors']['accent']};
    --background-color: {brand['colors']['background']};
    --text-color: {brand['colors']['text']};
}}

body {{
    font-family: '{brand['typography']['body']}', sans-serif;
    color: var(--text-color);
    background-color: var(--background-color);
}}

h1, h2, h3, h4, h5, h6 {{
    font-family: '{brand['typography']['headings']}', serif;
}}
""",
        "functions.php": f"""<?php
/**
 * {name} Theme Functions
 * Generated by SkyyRose Theme Orchestrator
 */

if (!defined('ABSPATH')) exit;

// Theme setup
function {func_slug}_setup() {{
    add_theme_support('post-thumbnails');
    add_theme_support('title-tag');
    add_theme_support('custom-logo', array(
        'height' => 100,
        'width' => 400,
        'flex-width' => true,
        'flex-height' => true,
    ));
    add_theme_support('html5', array('search-form', 'comment-form', 'gallery', 'caption'));

    // WooCommerce support
    add_theme_support('woocommerce');
    add_theme_support('wc-product-gallery-zoom');
    add_theme_support('wc-product-gallery-lightbox');
    add_theme_support('wc-product-gallery-slider');

    // Navigation menus
    register_nav_menus(array(
        'primary' => __('Primary Menu', '{slug}'),
        'footer' => __('Footer Menu', '{slug}'),
    ));
}}
add_action('after_setup_theme', '{func_slug}_setup');

// Enqueue styles and scripts
function {func_slug}_scripts() {{
    wp_enqueue_style('{slug}-style', get_stylesheet_uri(), array(), '1.0.0');
    wp_enqueue_style('{slug}-main', get_template_directory_uri() . '/assets/css/main.css', array(), '1.0.0');
    wp_enqueue_script('{slug}-main', get_template_directory_uri() . '/assets/js/main.js', array('jquery'), '1.0.0', true);
}}
add_action('wp_enqueue_scripts', '{func_slug}_scripts');

// Google Fonts
function {func_slug}_google_fonts() {{
    wp_enqueue_style('{slug}-google-fonts',
        'https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Source+Sans+Pro:wght@300;400;600&display=swap',
        array(), null
    );
}}
add_action('wp_enqueue_scripts', '{func_slug}_google_fonts');
""",
        "index.php": """<?php get_header(); ?>

<main id="main" class="site-main">
    <?php if (have_posts()) : ?>
        <div class="posts-grid">
            <?php while (have_posts()) : the_post(); ?>
                <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
                    <?php if (has_post_thumbnail()) : ?>
                        <div class="post-thumbnail">
                            <a href="<?php the_permalink(); ?>">
                                <?php the_post_thumbnail('medium_large'); ?>
                            </a>
                        </div>
                    <?php endif; ?>

                    <header class="entry-header">
                        <?php the_title('<h2 class="entry-title"><a href="' . esc_url(get_permalink()) . '">', '</a></h2>'); ?>
                    </header>

                    <div class="entry-excerpt">
                        <?php the_excerpt(); ?>
                    </div>
                </article>
            <?php endwhile; ?>
        </div>

        <?php the_posts_navigation(); ?>
    <?php else : ?>
        <p><?php _e('No posts found.', 'skyyrose'); ?></p>
    <?php endif; ?>
</main>

<?php get_footer(); ?>
""",
        "header.php": f"""<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="profile" href="https://gmpg.org/xfn/11">
    <?php wp_head(); ?>
</head>

<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<div id="page" class="site">
    <header id="masthead" class="site-header">
        <div class="header-container">
            <div class="site-branding">
                <?php if (has_custom_logo()) : ?>
                    <?php the_custom_logo(); ?>
                <?php else : ?>
                    <h1 class="site-title">
                        <a href="<?php echo esc_url(home_url('/')); ?>">{brand['brand_name']}</a>
                    </h1>
                <?php endif; ?>
            </div>

            <nav id="site-navigation" class="main-navigation">
                <button class="menu-toggle" aria-controls="primary-menu" aria-expanded="false">
                    <span class="hamburger"></span>
                </button>
                <?php wp_nav_menu(array(
                    'theme_location' => 'primary',
                    'menu_id' => 'primary-menu',
                    'container_class' => 'menu-container',
                )); ?>
            </nav>

            <div class="header-icons">
                <?php if (class_exists('WooCommerce')) : ?>
                    <a href="<?php echo wc_get_page_permalink('myaccount'); ?>" class="account-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="8" r="4"/>
                            <path d="M6 21v-2a4 4 0 014-4h4a4 4 0 014 4v2"/>
                        </svg>
                    </a>
                    <a href="<?php echo wc_get_cart_url(); ?>" class="cart-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="9" cy="21" r="1"/>
                            <circle cx="20" cy="21" r="1"/>
                            <path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 002-1.61L23 6H6"/>
                        </svg>
                        <span class="cart-count"><?php echo WC()->cart->get_cart_contents_count(); ?></span>
                    </a>
                <?php endif; ?>
            </div>
        </div>
    </header>
""",
        "footer.php": f"""    <footer id="colophon" class="site-footer">
        <div class="footer-container">
            <div class="footer-widgets">
                <div class="footer-column">
                    <h4>About {brand['brand_name']}</h4>
                    <p>{brand['tagline']}</p>
                </div>

                <div class="footer-column">
                    <h4>Quick Links</h4>
                    <?php wp_nav_menu(array('theme_location' => 'footer')); ?>
                </div>

                <div class="footer-column">
                    <h4>Contact</h4>
                    <p>Oakland, CA</p>
                    <p>hello@{brand['domain']}</p>
                </div>

                <div class="footer-column">
                    <h4>Follow Us</h4>
                    <div class="social-links">
                        <a href="#" aria-label="Instagram">Instagram</a>
                        <a href="#" aria-label="TikTok">TikTok</a>
                    </div>
                </div>
            </div>

            <div class="footer-bottom">
                <p>&copy; <?php echo date('Y'); ?> {brand['brand_name']}. All rights reserved.</p>
            </div>
        </div>
    </footer>
</div>

<?php wp_footer(); ?>
</body>
</html>
""",
    }

    return files


@mcp.tool()
def list_theme_types() -> dict[str, Any]:
    """
    List all available theme types with descriptions and features.

    Returns:
        Dictionary of available theme types
    """
    return {
        "theme_types": [
            {
                "id": "luxury_fashion",
                "name": "Luxury Fashion",
                "description": "Elegant, sophisticated design for luxury fashion brands like SkyyRose",
                "style": "elegant",
                "features": ["woocommerce", "elementor", "custom-header", "gallery", "lookbook"],
                "recommended_for": "High-end fashion, boutique, luxury retail",
            },
            {
                "id": "streetwear",
                "name": "Streetwear",
                "description": "Bold, dynamic design with urban aesthetic",
                "style": "bold",
                "features": ["woocommerce", "social-media", "video-backgrounds", "drops-countdown"],
                "recommended_for": "Street fashion, urban wear, youth brands",
            },
            {
                "id": "minimalist",
                "name": "Minimalist",
                "description": "Clean, focused design with minimal elements",
                "style": "clean",
                "features": ["responsive", "fast-loading", "accessibility", "simple-navigation"],
                "recommended_for": "Modern brands, premium simplicity",
            },
            {
                "id": "ecommerce",
                "name": "E-commerce",
                "description": "Conversion-optimized online store design",
                "style": "commercial",
                "features": ["woocommerce", "product-filters", "wishlist", "reviews", "upsells"],
                "recommended_for": "High-volume stores, product-focused sites",
            },
        ]
    }


@mcp.tool()
def get_brand_guidelines(include_rules: bool = False) -> dict[str, Any]:
    """
    Get SkyyRose brand guidelines for theme generation.

    Args:
        include_rules: Include brand enforcement rules

    Returns:
        Complete brand guidelines
    """
    guidelines = get_skyy_rose_defaults()

    if include_rules:
        guidelines["brand_rules"] = {
            "name_format": "SkyyRose (one word, capital S and R)",
            "incorrect_formats": ["Skyy Rose", "skyy rose", "SKYYROSE", "SkyRose"],
            "domain": "skyyrose.co (NEVER use .com)",
            "tone": "Luxury, elevated, boutique-ready",
            "prohibited_language": [
                "hyphy slang",
                "discount language",
                "clearance terms",
                ".com URLs",
            ],
            "visual_style": [
                "Sophisticated black and gold palette",
                "Clean typography with Playfair Display headings",
                "High-quality imagery",
                "Generous whitespace",
            ],
        }

    return guidelines


@mcp.tool()
def validate_theme_structure(files: dict[str, str]) -> dict[str, Any]:
    """
    Validate a theme's file structure and contents.

    Args:
        files: Dictionary of filename -> content

    Returns:
        Validation result with issues and warnings
    """
    issues = []
    warnings = []

    # Required files
    required = ["style.css", "index.php"]
    for req in required:
        if req not in files:
            issues.append(f"Missing required file: {req}")

    # Recommended files
    recommended = ["functions.php", "header.php", "footer.php"]
    for rec in recommended:
        if rec not in files:
            warnings.append(f"Missing recommended file: {rec}")

    # Validate style.css header
    if "style.css" in files:
        style_content = files["style.css"]
        if "Theme Name:" not in style_content:
            issues.append("style.css missing 'Theme Name:' in header")
        if "Text Domain:" not in style_content:
            warnings.append("style.css missing 'Text Domain:' (recommended)")

    # Check for WooCommerce support in functions.php
    if "functions.php" in files:
        funcs = files["functions.php"]
        if "add_theme_support('woocommerce')" not in funcs:
            warnings.append("WooCommerce support not declared in functions.php")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "files_checked": list(files.keys()),
        "summary": f"{len(issues)} issues, {len(warnings)} warnings",
    }


@mcp.tool()
def generate_elementor_widget(
    widget_type: str,
    widget_name: str | None = None,
) -> dict[str, Any]:
    """
    Generate a custom Elementor widget for the theme.

    Args:
        widget_type: Type of widget (product_showcase, brand_hero, collection_grid, testimonials, newsletter)
        widget_name: Custom name for the widget

    Returns:
        Widget PHP code and installation instructions
    """
    if widget_name is None:
        widget_name = widget_type.replace("_", " ").title()

    class_name = widget_name.replace(" ", "_") + "_Widget"
    slug = widget_name.lower().replace(" ", "_")

    widget_templates = {
        "product_showcase": {
            "icon": "eicon-products",
            "render": """
        $settings = $this->get_settings_for_display();
        ?>
        <div class="skyyrose-product-showcase">
            <?php echo do_shortcode('[products limit="' . $settings['products_count'] . '" columns="' . $settings['columns'] . '"]'); ?>
        </div>
        <?php
""",
            "controls": """
        $this->add_control('products_count', [
            'label' => __('Products Count', 'skyyrose'),
            'type' => \\Elementor\\Controls_Manager::NUMBER,
            'default' => 8,
            'min' => 1,
            'max' => 24,
        ]);

        $this->add_control('columns', [
            'label' => __('Columns', 'skyyrose'),
            'type' => \\Elementor\\Controls_Manager::SELECT,
            'default' => '4',
            'options' => ['2' => '2', '3' => '3', '4' => '4'],
        ]);
""",
        },
        "brand_hero": {
            "icon": "eicon-banner",
            "render": """
        $settings = $this->get_settings_for_display();
        ?>
        <div class="skyyrose-hero" style="background-image: url('<?php echo $settings['background_image']['url']; ?>');">
            <div class="hero-overlay"></div>
            <div class="hero-content">
                <h1><?php echo $settings['heading']; ?></h1>
                <p><?php echo $settings['subheading']; ?></p>
                <a href="<?php echo $settings['button_link']['url']; ?>" class="hero-button">
                    <?php echo $settings['button_text']; ?>
                </a>
            </div>
        </div>
        <?php
""",
            "controls": """
        $this->add_control('heading', [
            'label' => __('Heading', 'skyyrose'),
            'type' => \\Elementor\\Controls_Manager::TEXT,
            'default' => 'Welcome to SkyyRose',
        ]);

        $this->add_control('subheading', [
            'label' => __('Subheading', 'skyyrose'),
            'type' => \\Elementor\\Controls_Manager::TEXT,
            'default' => 'Luxury Streetwear, Oakland Authenticity',
        ]);

        $this->add_control('button_text', [
            'label' => __('Button Text', 'skyyrose'),
            'type' => \\Elementor\\Controls_Manager::TEXT,
            'default' => 'Shop Now',
        ]);

        $this->add_control('button_link', [
            'label' => __('Button Link', 'skyyrose'),
            'type' => \\Elementor\\Controls_Manager::URL,
            'default' => ['url' => '/shop'],
        ]);

        $this->add_control('background_image', [
            'label' => __('Background Image', 'skyyrose'),
            'type' => \\Elementor\\Controls_Manager::MEDIA,
        ]);
""",
        },
        "collection_grid": {
            "icon": "eicon-gallery-grid",
            "render": """
        $categories = get_terms('product_cat', ['hide_empty' => true, 'number' => 6]);
        ?>
        <div class="skyyrose-collections">
            <?php foreach ($categories as $cat) :
                $thumbnail_id = get_term_meta($cat->term_id, 'thumbnail_id', true);
                $image = wp_get_attachment_url($thumbnail_id);
            ?>
                <a href="<?php echo get_term_link($cat); ?>" class="collection-item">
                    <?php if ($image) : ?>
                        <img src="<?php echo $image; ?>" alt="<?php echo $cat->name; ?>">
                    <?php endif; ?>
                    <span class="collection-name"><?php echo $cat->name; ?></span>
                </a>
            <?php endforeach; ?>
        </div>
        <?php
""",
            "controls": "",
        },
        "testimonials": {
            "icon": "eicon-testimonial-carousel",
            "render": """
        ?>
        <div class="skyyrose-testimonials swiper">
            <div class="swiper-wrapper">
                <div class="swiper-slide">
                    <blockquote>
                        <p>"Absolutely love the quality and attention to detail. SkyyRose is my go-to for luxury streetwear."</p>
                        <cite>- Satisfied Customer</cite>
                    </blockquote>
                </div>
            </div>
            <div class="swiper-pagination"></div>
        </div>
        <?php
""",
            "controls": "",
        },
        "newsletter": {
            "icon": "eicon-email-field",
            "render": """
        $settings = $this->get_settings_for_display();
        ?>
        <div class="skyyrose-newsletter">
            <h3><?php echo $settings['heading']; ?></h3>
            <p><?php echo $settings['description']; ?></p>
            <form class="newsletter-form" action="" method="post">
                <input type="email" name="email" placeholder="Enter your email" required>
                <button type="submit"><?php echo $settings['button_text']; ?></button>
            </form>
        </div>
        <?php
""",
            "controls": """
        $this->add_control('heading', [
            'label' => __('Heading', 'skyyrose'),
            'type' => \\Elementor\\Controls_Manager::TEXT,
            'default' => 'Join Our Community',
        ]);

        $this->add_control('description', [
            'label' => __('Description', 'skyyrose'),
            'type' => \\Elementor\\Controls_Manager::TEXTAREA,
            'default' => 'Subscribe for exclusive offers and updates',
        ]);

        $this->add_control('button_text', [
            'label' => __('Button Text', 'skyyrose'),
            'type' => \\Elementor\\Controls_Manager::TEXT,
            'default' => 'Subscribe',
        ]);
""",
        },
    }

    if widget_type not in widget_templates:
        return {
            "error": f"Unknown widget type: {widget_type}",
            "available_types": list(widget_templates.keys()),
        }

    template = widget_templates[widget_type]

    php_code = f"""<?php
/**
 * {widget_name} - Custom Elementor Widget
 * Generated by SkyyRose Theme Orchestrator
 */

if (!defined('ABSPATH')) exit;

class {class_name} extends \\Elementor\\Widget_Base {{

    public function get_name() {{
        return '{slug}';
    }}

    public function get_title() {{
        return __('{widget_name}', 'skyyrose');
    }}

    public function get_icon() {{
        return '{template['icon']}';
    }}

    public function get_categories() {{
        return ['skyyrose'];
    }}

    protected function register_controls() {{
        $this->start_controls_section(
            'content_section',
            [
                'label' => __('Content', 'skyyrose'),
                'tab' => \\Elementor\\Controls_Manager::TAB_CONTENT,
            ]
        );
        {template['controls']}
        $this->end_controls_section();
    }}

    protected function render() {{
        {template['render']}
    }}
}}

// Register widget
add_action('elementor/widgets/register', function($widgets_manager) {{
    $widgets_manager->register(new {class_name}());
}});
"""

    return {
        "success": True,
        "widget_type": widget_type,
        "widget_name": widget_name,
        "class_name": class_name,
        "php_code": php_code,
        "installation": [
            "1. Create file: your-theme/widgets/{slug}.php",
            "2. Add to functions.php: require_once get_template_directory() . '/widgets/{slug}.php';",
            "3. Widget will appear in Elementor under 'SkyyRose' category",
        ],
    }


@mcp.tool()
def get_build_status(build_id: str) -> dict[str, Any]:
    """
    Get the status of a theme build.

    Args:
        build_id: The build ID from generate_theme

    Returns:
        Build status and details
    """
    if build_id in active_builds:
        return active_builds[build_id]

    return {
        "error": f"Build not found: {build_id}",
        "available_builds": list(active_builds.keys()),
    }


@mcp.tool()
def get_system_status() -> dict[str, Any]:
    """
    Get the current system status.

    Returns:
        System status information
    """
    return {
        "server": "SkyyRose Theme Orchestrator",
        "version": "1.0.0",
        "status": "running",
        "active_builds": len(active_builds),
        "build_ids": list(active_builds.keys())[-5:],  # Last 5
        "capabilities": [
            "generate_theme",
            "validate_theme_structure",
            "generate_elementor_widget",
            "list_theme_types",
            "get_brand_guidelines",
        ],
    }


# =============================================================================
# RESOURCES
# =============================================================================


@mcp.resource("theme://brand-guidelines")
def brand_guidelines_resource() -> str:
    """Get SkyyRose brand guidelines as a resource."""
    return json.dumps(get_skyy_rose_defaults(), indent=2)


@mcp.resource("theme://theme-types")
def theme_types_resource() -> str:
    """Get available theme types as a resource."""
    return json.dumps(list_theme_types(), indent=2)


# =============================================================================
# PROMPTS
# =============================================================================


@mcp.prompt()
def create_luxury_theme() -> str:
    """Prompt for creating a luxury fashion theme."""
    return """Create a luxury fashion WordPress theme for SkyyRose Collection.

Requirements:
- Theme type: luxury_fashion
- Include WooCommerce integration
- Include Elementor widgets for:
  - Brand hero section
  - Product showcase grid
  - Collection navigation
  - Newsletter signup
- Follow SkyyRose brand guidelines:
  - Colors: Black (#1a1a1a) and Gold (#d4af37)
  - Typography: Playfair Display for headings, Source Sans Pro for body
  - Style: Elegant, sophisticated, boutique-ready

Please generate the complete theme using the generate_theme tool."""


@mcp.prompt()
def create_elementor_widgets() -> str:
    """Prompt for creating custom Elementor widgets."""
    return """Generate custom Elementor widgets for SkyyRose theme.

Create the following widgets:
1. Brand Hero - Full-width hero section with overlay
2. Product Showcase - Featured products grid
3. Collection Grid - Category navigation with images
4. Testimonials - Customer reviews carousel
5. Newsletter - Email signup form

Use the generate_elementor_widget tool for each widget type."""
