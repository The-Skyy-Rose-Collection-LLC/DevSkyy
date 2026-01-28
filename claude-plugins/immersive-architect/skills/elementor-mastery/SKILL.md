# Elementor Mastery

This skill provides comprehensive knowledge for building immersive themes with Elementor Pro. It activates when users mention "Elementor", "Elementor Pro", "Elementor widgets", "Theme Builder", or need to build pages and themes with Elementor.

---

## Theme Builder Setup

### Header Template
1. Templates → Theme Builder → Header
2. Add New → Choose template type
3. Design header with widgets
4. Set display conditions

### Key Header Widgets
- Site Logo
- Nav Menu
- Search Form
- Cart (for WooCommerce)
- Custom HTML for animations

### Dynamic Header
```css
/* Transparent header that changes on scroll */
.elementor-sticky--active {
    background: rgba(255, 255, 255, 0.95) !important;
    backdrop-filter: blur(10px);
    box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
}

.elementor-sticky--active .elementor-nav-menu a {
    color: #000 !important;
}
```

## Global Settings

### Global Colors
- Primary: Brand main color
- Secondary: Supporting color
- Text: Body text color
- Accent: CTAs and highlights

### Global Fonts
- Primary: Headings
- Secondary: Body text
- Text: Paragraphs
- Accent: Special elements

### Theme Style
```
Site Settings → Theme Style:
- Typography defaults
- Button styles
- Form field styles
- Image styles
```

## Custom Widgets

### Register Custom Widget
```php
// inc/elementor/widgets/product-showcase.php
class Product_Showcase_Widget extends \Elementor\Widget_Base {

    public function get_name() {
        return 'product_showcase';
    }

    public function get_title() {
        return 'Product Showcase';
    }

    public function get_icon() {
        return 'eicon-products';
    }

    public function get_categories() {
        return ['theme-elements'];
    }

    protected function register_controls() {
        // Content Section
        $this->start_controls_section(
            'content_section',
            [
                'label' => 'Content',
                'tab' => \Elementor\Controls_Manager::TAB_CONTENT,
            ]
        );

        $this->add_control(
            'product_id',
            [
                'label' => 'Select Product',
                'type' => \Elementor\Controls_Manager::SELECT2,
                'options' => $this->get_products(),
                'default' => '',
            ]
        );

        $this->add_control(
            'show_3d',
            [
                'label' => 'Show 3D Viewer',
                'type' => \Elementor\Controls_Manager::SWITCHER,
                'default' => 'yes',
            ]
        );

        $this->end_controls_section();

        // Style Section
        $this->start_controls_section(
            'style_section',
            [
                'label' => 'Style',
                'tab' => \Elementor\Controls_Manager::TAB_STYLE,
            ]
        );

        $this->add_group_control(
            \Elementor\Group_Control_Typography::get_type(),
            [
                'name' => 'title_typography',
                'selector' => '{{WRAPPER}} .product-title',
            ]
        );

        $this->end_controls_section();
    }

    protected function render() {
        $settings = $this->get_settings_for_display();
        $product = wc_get_product($settings['product_id']);

        if (!$product) return;

        include get_template_directory() . '/template-parts/elementor/product-showcase.php';
    }

    private function get_products() {
        $products = wc_get_products(['limit' => -1]);
        $options = [];
        foreach ($products as $product) {
            $options[$product->get_id()] = $product->get_name();
        }
        return $options;
    }
}

// Register widget
add_action('elementor/widgets/register', function($widgets_manager) {
    $widgets_manager->register(new Product_Showcase_Widget());
});
```

## Motion Effects

### Entrance Animations
- Fade In
- Slide In (from direction)
- Zoom In
- Bounce
- Custom CSS animation

### Scroll Effects
```
Widget → Advanced → Motion Effects:
- Scrolling Effects
  - Vertical/Horizontal scroll
  - Transparency
  - Blur
  - Scale
  - Rotate
- Mouse Effects
  - Mouse Track
  - 3D Tilt
```

### Custom Animation CSS
```css
/* Add to Elementor Custom CSS */
.animate-float {
    animation: float 3s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-20px); }
}

/* Staggered entrance */
.elementor-widget-wrap > .elementor-element:nth-child(1) { animation-delay: 0s; }
.elementor-widget-wrap > .elementor-element:nth-child(2) { animation-delay: 0.1s; }
.elementor-widget-wrap > .elementor-element:nth-child(3) { animation-delay: 0.2s; }
```

## WooCommerce Integration

### Product Archive Template
1. Theme Builder → Product Archive
2. Use Archive Products widget
3. Customize with:
   - Products per row
   - Pagination style
   - Filtering options

### Single Product Template
1. Theme Builder → Single Product
2. Key widgets:
   - Product Images
   - Product Title
   - Product Price
   - Product Rating
   - Add to Cart
   - Product Meta
   - Product Tabs
   - Related Products

### Custom Product Layout
```
Section 1: Full-width hero with product gallery
Section 2: Two columns - details left, add to cart right
Section 3: Tabs with description, reviews, etc.
Section 4: Related products slider
```

## Responsive Design

### Breakpoints
```
Desktop: 1025px+
Tablet: 768px - 1024px
Mobile: 0 - 767px

Custom breakpoints available in:
Site Settings → Layout → Breakpoints
```

### Per-Widget Responsive
- Hide on specific devices
- Different spacing/sizing
- Stack columns on mobile
- Adjust typography

## Performance Optimization

### Elementor Settings
```
Elementor → Settings → Advanced:
- CSS Print Method: External File
- Load Unminified CSS: No
- Improved Asset Loading: Yes
```

### Best Practices
- Use Flexbox containers (not sections)
- Minimize nested elements
- Optimize images before upload
- Use lazy loading
- Limit animations on mobile

## Custom CSS Locations

1. **Widget Level**: Advanced → Custom CSS
2. **Page Level**: Page Settings → Custom CSS
3. **Global**: Elementor → Custom Code
4. **Theme**: style.css or Customizer

## Useful Code Snippets

### Make Section Full Height
```css
.full-height-section {
    min-height: 100vh;
    display: flex;
    align-items: center;
}
```

### Smooth Scroll
```css
html {
    scroll-behavior: smooth;
}
```

### Hide Elementor Admin Bar
```php
add_filter('show_admin_bar', '__return_false');
```

### Load Custom Fonts
```php
add_action('elementor/controls/register', function($controls_manager) {
    $new_fonts = [
        'Custom Font' => 'sans-serif',
    ];
    $controls_manager->get_control('font')->add_fonts($new_fonts);
});
```
