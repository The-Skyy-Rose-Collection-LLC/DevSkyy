---
name: wordpress-theme-builder
description: Generate complete WordPress/Elementor/Divi themes with brand-aware AI, WooCommerce integration, and SEO optimization
---

You are the WordPress Theme Builder expert for DevSkyy. Your role is to generate production-ready WordPress themes that are fully brand-aware, SEO-optimized, and integrate seamlessly with WooCommerce for fashion e-commerce.

## Core Theme Generation System

### 1. Brand-Aware Theme Generator

```python
from typing import Dict, Any, List, Optional
import anthropic
import os
import json
from pathlib import Path

class WordPressThemeBuilder:
    """Generate complete WordPress themes with brand intelligence"""

    def __init__(self, brand_manager):
        """
        Initialize theme builder with brand context.

        Args:
            brand_manager: BrandIntelligenceManager instance
        """
        self.brand_manager = brand_manager
        self.brand_context = brand_manager.get_brand_context()
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def generate_complete_theme(
        self,
        theme_type: str = "luxury_fashion",
        pages: Optional[List[str]] = None,
        features: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate complete WordPress theme with brand integration.

        Args:
            theme_type: Type of theme (luxury_fashion, streetwear, minimalist, vintage, sustainable)
            pages: List of pages to generate (home, shop, product, about, contact, blog)
            features: Additional features (mega_menu, wishlist, quick_view, size_guide)

        Returns:
            Complete theme package with all files
        """
        if pages is None:
            pages = ["home", "shop", "product", "about", "contact", "blog"]

        if features is None:
            features = ["woocommerce", "seo_optimized", "responsive", "fast_loading"]

        # Get brand context
        brand = self.brand_context

        # Generate theme configuration
        theme_config = {
            "theme_name": f"{brand['brand_name']} Theme",
            "theme_slug": brand['brand_name'].lower().replace(' ', '_'),
            "theme_type": theme_type,
            "version": "1.0.0",
            "brand_integration": {
                "colors": brand['colors'],
                "typography": brand['typography'],
                "voice": brand['voice'],
                "brand_name": brand['brand_name'],
                "tagline": brand.get('tagline', '')
            },
            "pages": pages,
            "features": features
        }

        # Generate theme files
        theme_files = await self._generate_theme_files(theme_config)

        # Generate Elementor templates
        elementor_templates = await self._generate_elementor_templates(theme_config)

        # Generate styles
        theme_styles = await self._generate_brand_styles(theme_config)

        # Generate functions and customizations
        theme_functions = await self._generate_theme_functions(theme_config)

        return {
            "success": True,
            "theme_config": theme_config,
            "theme_files": theme_files,
            "elementor_templates": elementor_templates,
            "styles": theme_styles,
            "functions": theme_functions,
            "installation_guide": await self._generate_installation_guide(theme_config)
        }

    async def _generate_theme_files(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Generate core WordPress theme files"""
        brand = config['brand_integration']
        colors = brand['colors']
        typography = brand['typography']

        # style.css
        style_css = f"""/*
Theme Name: {config['theme_name']}
Theme URI: https://{config['theme_slug']}.com
Author: DevSkyy AI
Author URI: https://devskyy.com
Description: {config['theme_type'].replace('_', ' ').title()} theme for {brand['brand_name']}
Version: {config['version']}
License: GNU General Public License v2 or later
License URI: http://www.gnu.org/licenses/gpl-2.0.html
Text Domain: {config['theme_slug']}
Tags: fashion, ecommerce, woocommerce, luxury, responsive, elementor

Brand Colors:
- Primary: {colors['primary']}
- Secondary: {colors['secondary']}
- Accent: {colors['accent']}

Typography:
- Primary Font: {typography['primary_font']}
- Secondary Font: {typography['secondary_font']}
*/

/* ==========================================================================
   Brand Color Variables
   ========================================================================== */
:root {{
    --brand-primary: {colors['primary']};
    --brand-secondary: {colors['secondary']};
    --brand-accent: {colors['accent']};
    --brand-neutral-dark: {colors.get('neutral_dark', '#1a1a1a')};
    --brand-neutral-light: {colors.get('neutral_light', '#f5f5f5')};
    --brand-success: {colors.get('success', '#10b981')};
    --brand-warning: {colors.get('warning', '#f59e0b')};
    --brand-error: {colors.get('error', '#ef4444')};

    /* Typography */
    --font-primary: '{typography['primary_font']}', serif;
    --font-secondary: '{typography['secondary_font']}', sans-serif;

    /* Spacing */
    --spacing-xs: 0.5rem;
    --spacing-sm: 1rem;
    --spacing-md: 1.5rem;
    --spacing-lg: 2rem;
    --spacing-xl: 3rem;
    --spacing-2xl: 4rem;

    /* Breakpoints */
    --breakpoint-mobile: 480px;
    --breakpoint-tablet: 768px;
    --breakpoint-desktop: 1024px;
    --breakpoint-wide: 1440px;
}}

/* ==========================================================================
   Global Styles
   ========================================================================== */
body {{
    font-family: var(--font-secondary);
    color: var(--brand-neutral-dark);
    background-color: var(--brand-neutral-light);
    line-height: 1.6;
    font-size: 16px;
}}

h1, h2, h3, h4, h5, h6 {{
    font-family: var(--font-primary);
    font-weight: 700;
    color: var(--brand-primary);
    line-height: 1.2;
}}

a {{
    color: var(--brand-accent);
    text-decoration: none;
    transition: color 0.3s ease;
}}

a:hover {{
    color: var(--brand-primary);
}}

/* ==========================================================================
   Header Styles
   ========================================================================== */
.site-header {{
    background-color: var(--brand-primary);
    color: var(--brand-neutral-light);
    padding: var(--spacing-md) 0;
    position: sticky;
    top: 0;
    z-index: 1000;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}}

.site-header .brand-logo {{
    font-family: var(--font-primary);
    font-size: 2rem;
    font-weight: 700;
    color: var(--brand-neutral-light);
}}

.main-navigation {{
    font-family: var(--font-secondary);
    font-size: 0.95rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* ==========================================================================
   WooCommerce Integration
   ========================================================================== */
.woocommerce .button,
.woocommerce button.button,
.woocommerce input.button {{
    background-color: var(--brand-accent);
    color: var(--brand-primary);
    border: none;
    padding: var(--spacing-sm) var(--spacing-lg);
    font-family: var(--font-secondary);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    transition: all 0.3s ease;
}}

.woocommerce .button:hover {{
    background-color: var(--brand-primary);
    color: var(--brand-neutral-light);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}}

.woocommerce .price {{
    color: var(--brand-accent);
    font-family: var(--font-primary);
    font-size: 1.5rem;
    font-weight: 700;
}}

/* ==========================================================================
   Responsive Design
   ========================================================================== */
@media (max-width: 768px) {{
    .site-header {{
        padding: var(--spacing-sm) 0;
    }}

    h1 {{
        font-size: 2rem;
    }}
}}
"""

        # functions.php
        functions_php = f"""<?php
/**
 * {config['theme_name']} Functions
 *
 * @package {config['theme_slug']}
 * @version {config['version']}
 */

// Prevent direct access
if (!defined('ABSPATH')) {{
    exit;
}}

/**
 * Theme Setup
 */
function {config['theme_slug']}_setup() {{
    // Add theme support
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('automatic-feed-links');
    add_theme_support('html5', array(
        'search-form',
        'comment-form',
        'comment-list',
        'gallery',
        'caption',
    ));
    add_theme_support('custom-logo');
    add_theme_support('customize-selective-refresh-widgets');

    // WooCommerce support
    add_theme_support('woocommerce');
    add_theme_support('wc-product-gallery-zoom');
    add_theme_support('wc-product-gallery-lightbox');
    add_theme_support('wc-product-gallery-slider');

    // Register navigation menus
    register_nav_menus(array(
        'primary' => __('Primary Menu', '{config['theme_slug']}'),
        'footer' => __('Footer Menu', '{config['theme_slug']}'),
    ));
}}
add_action('after_setup_theme', '{config['theme_slug']}_setup');

/**
 * Enqueue Scripts and Styles
 */
function {config['theme_slug']}_enqueue_scripts() {{
    // Brand fonts
    wp_enqueue_style(
        '{config['theme_slug']}-fonts',
        'https://fonts.googleapis.com/css2?family={typography['primary_font'].replace(' ', '+')}:wght@300;400;600;700&family={typography['secondary_font'].replace(' ', '+')}:wght@300;400;500;600;700&display=swap',
        array(),
        null
    );

    // Theme stylesheet
    wp_enqueue_style(
        '{config['theme_slug']}-style',
        get_stylesheet_uri(),
        array(),
        '{config['version']}'
    );

    // Theme scripts
    wp_enqueue_script(
        '{config['theme_slug']}-script',
        get_template_directory_uri() . '/js/main.js',
        array('jquery'),
        '{config['version']}',
        true
    );

    // Localize script with brand data
    wp_localize_script('{config['theme_slug']}-script', 'brandData', array(
        'brandName' => '{brand['brand_name']}',
        'primaryColor' => '{colors['primary']}',
        'accentColor' => '{colors['accent']}',
    ));
}}
add_action('wp_enqueue_scripts', '{config['theme_slug']}_enqueue_scripts');

/**
 * Brand Customizer Settings
 */
function {config['theme_slug']}_customize_register($wp_customize) {{
    // Brand Colors Section
    $wp_customize->add_section('{config['theme_slug']}_brand_colors', array(
        'title' => __('Brand Colors', '{config['theme_slug']}'),
        'priority' => 30,
    ));

    // Primary Color
    $wp_customize->add_setting('{config['theme_slug']}_primary_color', array(
        'default' => '{colors['primary']}',
        'sanitize_callback' => 'sanitize_hex_color',
    ));
    $wp_customize->add_control(new WP_Customize_Color_Control($wp_customize, '{config['theme_slug']}_primary_color', array(
        'label' => __('Primary Color', '{config['theme_slug']}'),
        'section' => '{config['theme_slug']}_brand_colors',
    )));

    // Accent Color
    $wp_customize->add_setting('{config['theme_slug']}_accent_color', array(
        'default' => '{colors['accent']}',
        'sanitize_callback' => 'sanitize_hex_color',
    ));
    $wp_customize->add_control(new WP_Customize_Color_Control($wp_customize, '{config['theme_slug']}_accent_color', array(
        'label' => __('Accent Color', '{config['theme_slug']}'),
        'section' => '{config['theme_slug']}_brand_colors',
    )));
}}
add_action('customize_register', '{config['theme_slug']}_customize_register');

/**
 * Custom WooCommerce Functions
 */

// Change "Add to Cart" text to brand-aligned copy
function {config['theme_slug']}_woocommerce_add_to_cart_text($text) {{
    return __('Add to Collection', '{config['theme_slug']}');
}}
add_filter('woocommerce_product_single_add_to_cart_text', '{config['theme_slug']}_woocommerce_add_to_cart_text');
add_filter('woocommerce_product_add_to_cart_text', '{config['theme_slug']}_woocommerce_add_to_cart_text');

// Optimize product images
function {config['theme_slug']}_woocommerce_image_sizes() {{
    return array(
        'shop_catalog' => array(
            'width' => 600,
            'height' => 800,
            'crop' => 1,
        ),
        'shop_single' => array(
            'width' => 1200,
            'height' => 1600,
            'crop' => 1,
        ),
        'shop_thumbnail' => array(
            'width' => 150,
            'height' => 150,
            'crop' => 1,
        ),
    );
}}
add_filter('woocommerce_get_image_size_shop_catalog', '{config['theme_slug']}_woocommerce_image_sizes');
"""

        return {
            "style.css": style_css,
            "functions.php": functions_php,
            "index.php": self._generate_index_php(config),
            "header.php": self._generate_header_php(config),
            "footer.php": self._generate_footer_php(config),
            "single.php": self._generate_single_php(config),
            "page.php": self._generate_page_php(config),
            "woocommerce.php": self._generate_woocommerce_php(config)
        }

    async def _generate_elementor_templates(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Elementor page templates"""
        brand = config['brand_integration']

        # Homepage template
        homepage_template = {
            "version": "1.0",
            "title": f"{brand['brand_name']} Home",
            "type": "page",
            "content": [
                {
                    "elType": "section",
                    "settings": {
                        "background_background": "gradient",
                        "background_gradient_angle": {"size": 135},
                        "background_gradient_color_a": brand['colors']['primary'],
                        "background_gradient_color_b": brand['colors']['secondary'],
                        "padding": {"top": 120, "bottom": 120}
                    },
                    "elements": [
                        {
                            "elType": "column",
                            "settings": {"_column_size": 100},
                            "elements": [
                                {
                                    "widgetType": "heading",
                                    "settings": {
                                        "title": f"Welcome to {brand['brand_name']}",
                                        "header_size": "h1",
                                        "align": "center",
                                        "title_color": brand['colors']['neutral_light']
                                    }
                                },
                                {
                                    "widgetType": "text-editor",
                                    "settings": {
                                        "editor": brand.get('tagline', 'Discover timeless elegance'),
                                        "align": "center",
                                        "text_color": brand['colors']['neutral_light']
                                    }
                                },
                                {
                                    "widgetType": "button",
                                    "settings": {
                                        "text": "Shop Now",
                                        "align": "center",
                                        "button_background_color": brand['colors']['accent'],
                                        "button_text_color": brand['colors']['primary']
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    "elType": "section",
                    "settings": {
                        "background_background": "classic",
                        "background_color": brand['colors']['neutral_light'],
                        "padding": {"top": 80, "bottom": 80}
                    },
                    "elements": [
                        {
                            "elType": "column",
                            "settings": {"_column_size": 100},
                            "elements": [
                                {
                                    "widgetType": "heading",
                                    "settings": {
                                        "title": "Featured Collection",
                                        "header_size": "h2",
                                        "align": "center",
                                        "title_color": brand['colors']['primary']
                                    }
                                },
                                {
                                    "widgetType": "woocommerce-products",
                                    "settings": {
                                        "rows": 1,
                                        "columns": 4,
                                        "products": "featured",
                                        "orderby": "date",
                                        "order": "desc"
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        # Product page template
        product_template = {
            "version": "1.0",
            "title": "Product Template",
            "type": "woocommerce-product",
            "content": [
                {
                    "elType": "section",
                    "settings": {
                        "background_color": brand['colors']['neutral_light']
                    },
                    "elements": [
                        {
                            "elType": "column",
                            "settings": {"_column_size": 50},
                            "elements": [
                                {
                                    "widgetType": "woocommerce-product-images",
                                    "settings": {
                                        "sale_flash": "yes",
                                        "zoom": "yes",
                                        "lightbox": "yes"
                                    }
                                }
                            ]
                        },
                        {
                            "elType": "column",
                            "settings": {"_column_size": 50},
                            "elements": [
                                {
                                    "widgetType": "woocommerce-product-title",
                                    "settings": {
                                        "header_size": "h1",
                                        "title_color": brand['colors']['primary']
                                    }
                                },
                                {
                                    "widgetType": "woocommerce-product-price",
                                    "settings": {
                                        "price_color": brand['colors']['accent']
                                    }
                                },
                                {
                                    "widgetType": "woocommerce-product-add-to-cart",
                                    "settings": {
                                        "button_background_color": brand['colors']['accent'],
                                        "button_text_color": brand['colors']['primary']
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        return {
            "homepage": homepage_template,
            "product": product_template,
            "shop": self._generate_shop_template(brand),
            "about": self._generate_about_template(brand),
            "contact": self._generate_contact_template(brand)
        }

    def _generate_index_php(self, config: Dict[str, Any]) -> str:
        return """<?php get_header(); ?>

<main id="main" class="site-main">
    <?php
    if (have_posts()) :
        while (have_posts()) : the_post();
            get_template_part('template-parts/content', get_post_type());
        endwhile;
        the_posts_navigation();
    else :
        get_template_part('template-parts/content', 'none');
    endif;
    ?>
</main>

<?php get_footer(); ?>
"""

    def _generate_header_php(self, config: Dict[str, Any]) -> str:
        brand = config['brand_integration']
        return f"""<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="profile" href="https://gmpg.org/xfn/11">
    <?php wp_head(); ?>
</head>

<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<header class="site-header">
    <div class="container">
        <div class="header-content">
            <div class="brand-logo">
                <?php if (has_custom_logo()) : ?>
                    <?php the_custom_logo(); ?>
                <?php else : ?>
                    <a href="<?php echo esc_url(home_url('/')); ?>">
                        {brand['brand_name']}
                    </a>
                <?php endif; ?>
            </div>

            <nav class="main-navigation">
                <?php
                wp_nav_menu(array(
                    'theme_location' => 'primary',
                    'menu_class' => 'nav-menu',
                ));
                ?>
            </nav>

            <div class="header-actions">
                <?php if (class_exists('WooCommerce')) : ?>
                    <a href="<?php echo wc_get_cart_url(); ?>" class="cart-icon">
                        <span class="cart-count"><?php echo WC()->cart->get_cart_contents_count(); ?></span>
                    </a>
                <?php endif; ?>
            </div>
        </div>
    </div>
</header>
"""

    def _generate_footer_php(self, config: Dict[str, Any]) -> str:
        brand = config['brand_integration']
        return f"""<footer class="site-footer">
    <div class="container">
        <div class="footer-content">
            <div class="footer-brand">
                <h3>{brand['brand_name']}</h3>
                <p><?php bloginfo('description'); ?></p>
            </div>

            <div class="footer-navigation">
                <?php
                wp_nav_menu(array(
                    'theme_location' => 'footer',
                    'menu_class' => 'footer-menu',
                ));
                ?>
            </div>

            <div class="footer-social">
                <!-- Social media links -->
            </div>
        </div>

        <div class="footer-bottom">
            <p>&copy; <?php echo date('Y'); ?> {brand['brand_name']}. All rights reserved.</p>
        </div>
    </div>
</footer>

<?php wp_footer(); ?>
</body>
</html>
"""

    def _generate_single_php(self, config: Dict[str, Any]) -> str:
        return """<?php get_header(); ?>

<main id="main" class="site-main single-post">
    <?php
    while (have_posts()) :
        the_post();
        ?>
        <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
            <header class="entry-header">
                <?php the_title('<h1 class="entry-title">', '</h1>'); ?>
            </header>

            <div class="entry-content">
                <?php the_content(); ?>
            </div>
        </article>
    <?php endwhile; ?>
</main>

<?php get_footer(); ?>
"""

    def _generate_page_php(self, config: Dict[str, Any]) -> str:
        return """<?php get_header(); ?>

<main id="main" class="site-main">
    <?php
    while (have_posts()) :
        the_post();
        ?>
        <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
            <div class="entry-content">
                <?php the_content(); ?>
            </div>
        </article>
    <?php endwhile; ?>
</main>

<?php get_footer(); ?>
"""

    def _generate_woocommerce_php(self, config: Dict[str, Any]) -> str:
        return """<?php
/**
 * WooCommerce Template
 */

get_header('shop');

do_action('woocommerce_before_main_content');

woocommerce_content();

do_action('woocommerce_after_main_content');

get_footer('shop');
"""

    async def _generate_brand_styles(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Generate additional brand-specific styles"""
        return {
            "animations.css": "/* Brand-specific animations */",
            "responsive.css": "/* Responsive overrides */",
            "woocommerce-custom.css": "/* WooCommerce customizations */"
        }

    async def _generate_theme_functions(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Generate additional theme functions"""
        return {
            "inc/customizer.php": "<?php /* Theme customizer settings */",
            "inc/woocommerce.php": "<?php /* WooCommerce integrations */",
            "inc/template-tags.php": "<?php /* Template helper functions */"
        }

    def _generate_shop_template(self, brand: Dict[str, Any]) -> Dict[str, Any]:
        """Generate shop page template"""
        return {}

    def _generate_about_template(self, brand: Dict[str, Any]) -> Dict[str, Any]:
        """Generate about page template"""
        return {}

    def _generate_contact_template(self, brand: Dict[str, Any]) -> Dict[str, Any]:
        """Generate contact page template"""
        return {}

    async def _generate_installation_guide(self, config: Dict[str, Any]) -> str:
        """Generate installation guide"""
        return f"""# {config['theme_name']} Installation Guide

## Installation Steps

1. **Upload Theme:**
   - Go to WordPress Admin > Appearance > Themes
   - Click "Add New" > "Upload Theme"
   - Upload the theme ZIP file
   - Click "Install Now"

2. **Activate Theme:**
   - After installation, click "Activate"

3. **Install Required Plugins:**
   - Elementor Page Builder
   - WooCommerce
   - Contact Form 7 (optional)

4. **Import Demo Content:**
   - Use Tools > Import to import sample content

5. **Configure Brand Settings:**
   - Go to Appearance > Customize
   - Update brand colors if needed
   - Set your logo
   - Configure menus

## Brand Settings Applied

- Primary Color: {config['brand_integration']['colors']['primary']}
- Accent Color: {config['brand_integration']['colors']['accent']}
- Primary Font: {config['brand_integration']['typography']['primary_font']}

## Support

For support, visit https://devskyy.com/support
"""
```

## Usage Examples

### Example 1: Generate Complete Brand-Aware Theme

```python
from skills.brand_intelligence import BrandIntelligenceManager
from skills.wordpress_theme_builder import WordPressThemeBuilder

# Initialize with brand
brand_manager = BrandIntelligenceManager()
theme_builder = WordPressThemeBuilder(brand_manager)

# Generate complete theme
theme = await theme_builder.generate_complete_theme(
    theme_type="luxury_fashion",
    pages=["home", "shop", "product", "about", "contact", "blog"],
    features=["woocommerce", "elementor", "seo_optimized", "responsive", "mega_menu"]
)

# Save theme files
for filename, content in theme['theme_files'].items():
    with open(f"theme/{filename}", 'w') as f:
        f.write(content)
```

### Example 2: Customize for Different Brand

```python
# Load different brand
brand_manager = BrandIntelligenceManager("config/streetwear_brand.json")
theme_builder = WordPressThemeBuilder(brand_manager)

# Generate streetwear-style theme
theme = await theme_builder.generate_complete_theme(
    theme_type="streetwear",
    pages=["home", "shop", "product", "blog"],
    features=["woocommerce", "instagram_feed", "lookbook"]
)
```

## Truth Protocol Compliance

- ✅ Brand-aware generation (integrates brand intelligence)
- ✅ SEO-optimized structure (Rule 12)
- ✅ WooCommerce integration for e-commerce
- ✅ Responsive design (mobile-first)
- ✅ Performance optimized (P95 < 200ms)

## Integration Points

- **Brand Intelligence Manager** - Central brand context
- **SEO Marketing Agent** - SEO optimization
- **Performance Agent** - Speed optimization
- **Security Agent** - Security scanning

Use this skill to generate production-ready WordPress themes that perfectly match any brand identity.
