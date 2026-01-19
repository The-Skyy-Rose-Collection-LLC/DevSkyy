# Divi Mastery

This skill provides comprehensive knowledge for building immersive themes with Divi Builder. It activates when users mention "Divi", "Divi Builder", "Divi modules", "Divi Theme Builder", or need to build pages and themes with Divi.

---

## Divi Theme Setup

### Child Theme Structure
```
divi-child/
├── style.css
├── functions.php
├── custom.css
├── js/
│   └── custom.js
└── includes/
    ├── modules/
    └── shortcodes/
```

### Child Theme Setup
```php
// functions.php
function divi_child_enqueue_styles() {
    wp_enqueue_style('parent-style', get_template_directory_uri() . '/style.css');
    wp_enqueue_style('child-style', get_stylesheet_uri(), ['parent-style']);
}
add_action('wp_enqueue_scripts', 'divi_child_enqueue_styles');

// Enqueue custom scripts
function divi_child_enqueue_scripts() {
    wp_enqueue_script(
        'child-custom',
        get_stylesheet_directory_uri() . '/js/custom.js',
        ['jquery', 'divi-custom-script'],
        '1.0.0',
        true
    );
}
add_action('wp_enqueue_scripts', 'divi_child_enqueue_scripts');
```

## Divi Theme Builder

### Global Header
1. Divi → Theme Builder → Add Global Header
2. Build Header Template
3. Key modules:
   - Logo Module
   - Menu Module
   - Search Module
   - Button Module
   - Social Media Follow

### Transparent Header
```css
/* Transparent header on specific pages */
.et_header_style_split .et-fixed-header#main-header,
.et_header_style_split #main-header {
    background-color: transparent !important;
}

/* Solid on scroll */
.et_header_style_split .et-fixed-header#main-header.et-fixed-header {
    background-color: rgba(255, 255, 255, 0.95) !important;
    backdrop-filter: blur(10px);
}
```

### Sticky Header Animation
```css
#main-header {
    transition: all 0.3s ease;
}

.et-fixed-header#main-header {
    box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
}

.et-fixed-header .logo_container img {
    max-height: 60px !important;
    transition: max-height 0.3s ease;
}
```

## Custom Divi Modules

### Creating a Custom Module
```php
// includes/modules/ProductShowcase.php
class Custom_Product_Showcase extends ET_Builder_Module {
    public $slug       = 'custom_product_showcase';
    public $vb_support = 'on';

    protected $module_credits = [
        'module_uri' => '',
        'author'     => 'Theme Author',
        'author_uri' => '',
    ];

    public function init() {
        $this->name = esc_html__('Product Showcase', 'theme-textdomain');
        $this->icon_path = get_stylesheet_directory() . '/includes/modules/icons/product.svg';
    }

    public function get_fields() {
        return [
            'product_id' => [
                'label'           => esc_html__('Select Product', 'theme-textdomain'),
                'type'            => 'select',
                'option_category' => 'basic_option',
                'options'         => $this->get_products(),
                'default'         => '',
            ],
            'show_price' => [
                'label'           => esc_html__('Show Price', 'theme-textdomain'),
                'type'            => 'yes_no_button',
                'option_category' => 'configuration',
                'options'         => [
                    'on'  => esc_html__('Yes', 'theme-textdomain'),
                    'off' => esc_html__('No', 'theme-textdomain'),
                ],
                'default'         => 'on',
            ],
            'layout' => [
                'label'           => esc_html__('Layout', 'theme-textdomain'),
                'type'            => 'select',
                'option_category' => 'layout',
                'options'         => [
                    'standard' => esc_html__('Standard', 'theme-textdomain'),
                    'featured' => esc_html__('Featured', 'theme-textdomain'),
                    'minimal'  => esc_html__('Minimal', 'theme-textdomain'),
                ],
                'default'         => 'standard',
            ],
        ];
    }

    private function get_products() {
        $products = wc_get_products(['limit' => -1]);
        $options = ['' => esc_html__('Select Product', 'theme-textdomain')];
        foreach ($products as $product) {
            $options[$product->get_id()] = $product->get_name();
        }
        return $options;
    }

    public function render($attrs, $content = null, $render_slug) {
        $product_id = $this->props['product_id'];
        $show_price = $this->props['show_price'];
        $layout = $this->props['layout'];

        if (empty($product_id)) {
            return '';
        }

        $product = wc_get_product($product_id);
        if (!$product) {
            return '';
        }

        ob_start();
        include get_stylesheet_directory() . '/template-parts/divi/product-showcase.php';
        return ob_get_clean();
    }
}

new Custom_Product_Showcase();
```

### Register Custom Module
```php
// functions.php
function divi_child_register_modules() {
    if (class_exists('ET_Builder_Module')) {
        require_once get_stylesheet_directory() . '/includes/modules/ProductShowcase.php';
    }
}
add_action('et_builder_ready', 'divi_child_register_modules');
```

## Divi Customizations

### Global Colors
```css
/* Define Divi color palette */
:root {
    --divi-primary: #2b87da;
    --divi-secondary: #23272a;
    --divi-accent: #ff6b6b;
    --divi-text: #333333;
    --divi-light: #f5f5f5;
}
```

### Global Presets
Theme Customizer → General Settings:
- Logo, Favicon
- Layout Settings
- Typography
- Color Palette
- Background

### Custom Module Styles
```css
/* Product Grid Module */
.et_pb_shop .woocommerce ul.products {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 30px;
}

.et_pb_shop .woocommerce ul.products li.product {
    margin: 0;
    padding: 0;
    width: 100% !important;
}

/* Product Card Styling */
.et_pb_shop .woocommerce ul.products li.product .woocommerce-loop-product__link {
    display: block;
    position: relative;
}

.et_pb_shop .woocommerce ul.products li.product img {
    transition: transform 0.4s ease;
}

.et_pb_shop .woocommerce ul.products li.product:hover img {
    transform: scale(1.05);
}
```

## Scroll Effects

### Divi Built-in Effects
Section/Row/Module Settings → Design → Scroll Effects:
- Vertical Motion
- Horizontal Motion
- Fading
- Scaling
- Rotating
- Blur

### Custom Scroll Animations
```javascript
// Custom GSAP integration with Divi
(function($) {
    $(window).on('load', function() {
        if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
            gsap.registerPlugin(ScrollTrigger);

            // Animate Divi modules on scroll
            gsap.utils.toArray('.et_pb_module').forEach(function(module) {
                gsap.from(module, {
                    y: 50,
                    opacity: 0,
                    duration: 0.8,
                    ease: 'power3.out',
                    scrollTrigger: {
                        trigger: module,
                        start: 'top 85%',
                        toggleActions: 'play none none none'
                    }
                });
            });
        }
    });
})(jQuery);
```

## WooCommerce + Divi

### Product Page Layout
Theme Builder → Add Product Template:
1. Post Title Module
2. Woo Product Images
3. Woo Product Price
4. Woo Add to Cart
5. Woo Product Description
6. Woo Product Meta
7. Woo Product Tabs
8. Woo Related Products

### Shop Page Layout
Theme Builder → Add Archive Template:
1. Shop Module with custom layout
2. Sidebar with filters
3. Pagination styling

### Custom Shop Styling
```css
/* Shop page grid */
.woocommerce .products {
    display: grid !important;
    grid-template-columns: repeat(3, 1fr);
    gap: 40px;
}

@media (max-width: 980px) {
    .woocommerce .products {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 767px) {
    .woocommerce .products {
        grid-template-columns: 1fr;
    }
}

/* Product card */
.woocommerce ul.products li.product {
    background: #fff;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.woocommerce ul.products li.product:hover {
    transform: translateY(-8px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
}
```

## Performance Optimization

### Divi Settings
Divi → Theme Options → Builder → Advanced:
- Enable Dynamic CSS
- Enable Dynamic Icons
- Enable Critical CSS
- Defer jQuery and jQuery Migrate

### Custom Optimization
```php
// Disable Divi built-in Google Fonts
function disable_divi_google_fonts() {
    return true;
}
add_filter('et_builder_load_fonts', 'disable_divi_google_fonts');

// Remove Divi's default emoji
remove_action('wp_head', 'print_emoji_detection_script', 7);
remove_action('admin_print_scripts', 'print_emoji_detection_script');
remove_action('wp_print_styles', 'print_emoji_styles');

// Async load non-critical CSS
function divi_child_defer_css($html, $handle, $href, $media) {
    if (is_admin()) {
        return $html;
    }

    $handles_to_defer = ['et-builder-modules-style', 'et-builder-modules-style-defer'];

    if (in_array($handle, $handles_to_defer)) {
        return '<link rel="preload" href="' . $href . '" as="style" onload="this.onload=null;this.rel=\'stylesheet\'">' .
               '<noscript>' . $html . '</noscript>';
    }

    return $html;
}
add_filter('style_loader_tag', 'divi_child_defer_css', 10, 4);
```

## Responsive Design

### Breakpoints
```
Desktop: 981px+
Tablet: 768px - 980px
Phone: 0 - 767px
```

### Per-Module Responsive
- Different content per device
- Hidden on specific devices
- Different spacing/sizing
- Responsive typography

### Custom Breakpoints
```css
/* Extra large screens */
@media (min-width: 1400px) {
    .et_pb_section {
        padding: 100px 8%;
    }
}

/* Tablet landscape */
@media (min-width: 768px) and (max-width: 980px) and (orientation: landscape) {
    .et_pb_row {
        max-width: 90%;
    }
}
```

## Useful Code Snippets

### Full-Width Sections
```css
.et_pb_section.full-width {
    width: 100vw;
    margin-left: calc(-50vw + 50%);
    padding-left: calc(50vw - 50%);
    padding-right: calc(50vw - 50%);
}
```

### Smooth Scroll
```css
html {
    scroll-behavior: smooth;
}
```

### Parallax Fix for Mobile
```php
// Disable parallax on mobile
function disable_mobile_parallax() {
    if (wp_is_mobile()) {
        return true;
    }
    return false;
}
add_filter('et_pb_parallax_enabled', 'disable_mobile_parallax');
```

### Custom Fonts
```php
function add_custom_fonts($fonts) {
    $fonts['Custom Font'] = [
        'styles' => '300,400,500,600,700',
        'character_set' => 'latin',
        'type' => 'serif'
    ];
    return $fonts;
}
add_filter('et_websafe_fonts', 'add_custom_fonts');
```
