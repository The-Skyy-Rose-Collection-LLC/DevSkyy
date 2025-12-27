# SKYYROSE HOMEPAGE SPECIFICATION

# Version: 1.0.0

# Last Updated: 2024-12-11

# Platform: WordPress + WooCommerce + Elementor Pro

# Theme: Shoptimizer 2.9.0

---

## PAGE METADATA

```yaml
page:
  name: "Homepage"
  slug: "/"
  template: "elementor_header_footer"
  seo:
    title: "SkyyRose | Where Love Meets Luxury - Oakland Streetwear"
    description: "Premium luxury streetwear born in Oakland. Shop BLACK ROSE limited editions, LOVE HURTS emotional pieces, and SIGNATURE essentials. Free shipping over $150."
    keywords: ["luxury streetwear", "oakland fashion", "premium hoodies", "limited edition clothing"]
  og:
    image: "/assets/images/og-homepage.jpg"
    type: "website"
  schema_type: "WebPage"
  priority: 1.0
  mobile_first: true
  target_load_time: "<3s"
```

---

## GLOBAL DESIGN TOKENS

```yaml
design_tokens:
  # ===========================================
  # HOMEPAGE MIXED PALETTE
  # Combines BLACK ROSE, LOVE HURTS & SIGNATURE
  # ===========================================
  colors:
    # Core Brand
    primary:
      black: "#0D0D0D"
      white: "#FAFAFA"
      cream: "#F5F3EF"

    # Metallic Accents (from all collections)
    metallics:
      gold: "#D4AF37"              # From SIGNATURE
      rose_gold: "#B76E79"         # From SIGNATURE
      soft_gold: "#C9A962"         # Soft Gold
      silver: "#C0C0C0"            # From BLACK ROSE
      chrome: "#E8E8E8"            # Bright Silver

    # Warm Tones (from LOVE HURTS)
    warm:
      deep_rose: "#8B3A3A"
      soft_rose: "#D4A5A5"
      warm_dark: "#2D1F1F"
      warm_cream: "#FDF8F8"

    # Collection-Specific Accents
    collections:
      black_rose:
        primary: "#0D0D0D"
        accent: "#C0C0C0"          # Metallic Silver
        secondary: "#1A1A1A"
      love_hurts:
        primary: "#8B3A3A"
        accent: "#D4A5A5"
        secondary: "#5C2828"
      signature:
        primary: "#0D0D0D"
        accent: "#D4AF37"          # Gold
        secondary: "#B76E79"       # Rose Gold

    # UI Feedback
    ui:
      success: "#059669"
      warning: "#D97706"
      error: "#DC2626"

    # Gradients (Mixed)
    gradients:
      hero: "linear-gradient(135deg, #0D0D0D 0%, #1A1A1A 40%, #2D1F1F 70%, #0D0D0D 100%)"
      metallic_shimmer: "linear-gradient(90deg, #C0C0C0 0%, #D4AF37 50%, #B76E79 100%)"
      gold: "linear-gradient(135deg, #D4AF37 0%, #F5D77A 50%, #D4AF37 100%)"
      rose: "linear-gradient(135deg, #8B3A3A 0%, #D4A5A5 50%, #8B3A3A 100%)"

  typography:
    headings:
      family: "'Cormorant Garamond', 'Playfair Display', serif"
      weights: [400, 500, 600, 700]
    body:
      family: "'Inter', 'Outfit', -apple-system, sans-serif"
      weights: [400, 500, 600]
    sizes:
      h1: "clamp(2rem, 5vw, 3.5rem)"
      h2: "clamp(1.5rem, 4vw, 2.5rem)"
      h3: "clamp(1.25rem, 3vw, 1.75rem)"
      body: "1rem"
      small: "0.875rem"
      xs: "0.75rem"

  spacing:
    base: "8px"
    section_padding:
      desktop: "80px"
      tablet: "60px"
      mobile: "48px"
    container_max: "1200px"

  breakpoints:
    mobile: "375px"
    tablet: "768px"
    desktop: "1024px"
    wide: "1440px"

  animations:
    duration:
      fast: "150ms"
      normal: "300ms"
      slow: "500ms"
    easing: "cubic-bezier(0.4, 0, 0.2, 1)"
```

---

## SECTION 1: HERO

### Specification

```yaml
section:
  id: "hero"
  name: "Hero Section"
  type: "full_width_video_hero"
  height:
    desktop: "100vh"
    mobile: "90vh"
  background:
    type: "video"
    fallback: "image"
    video_url: "/assets/videos/hero-oakland-sunset.mp4"
    fallback_image: "/assets/images/hero-fallback.jpg"
    overlay:
      type: "gradient"
      value: "linear-gradient(180deg, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0.5) 100%)"
```

### Content

```yaml
content:
  logo:
    type: "text"
    value: "SKYYROSE"
    font: "Cormorant Garamond"
    size: "clamp(2rem, 6vw, 4rem)"
    weight: 400
    letter_spacing: "0.3em"
    color: "#FAFAFA"

  tagline:
    type: "text"
    value: "WHERE LOVE MEETS LUXURY"
    font: "Inter"
    size: "clamp(0.75rem, 2vw, 1rem)"
    weight: 400
    letter_spacing: "0.2em"
    color: "rgba(250, 250, 250, 0.8)"
    margin_top: "16px"

  cta_primary:
    type: "button"
    text: "SHOP THE COLLECTIONS"
    url: "/shop/"
    style:
      background: "#FAFAFA"
      color: "#0D0D0D"
      padding: "16px 40px"
      font_size: "0.75rem"
      letter_spacing: "0.15em"
      font_weight: 500
      border: "none"
      hover:
        background: "#0D0D0D"
        color: "#FAFAFA"
        transition: "all 0.3s ease"
    margin_top: "32px"

  scroll_indicator:
    type: "icon"
    icon: "chevron-down"
    animation: "bounce"
    position: "bottom-center"
    margin_bottom: "24px"
    color: "rgba(250, 250, 250, 0.6)"
```

### Elementor Configuration

```json
{
  "elementor_widget": "container",
  "settings": {
    "content_width": "full",
    "min_height": {"unit": "vh", "size": 100},
    "min_height_mobile": {"unit": "vh", "size": 90},
    "flex_direction": "column",
    "flex_justify_content": "center",
    "flex_align_items": "center",
    "background_background": "video",
    "background_video_link": "{{video_url}}",
    "background_video_fallback": {"url": "{{fallback_image}}"},
    "background_overlay_background": "gradient",
    "background_overlay_gradient_angle": {"unit": "deg", "size": 180},
    "background_overlay_color_stop": {"unit": "%", "size": 0},
    "padding": {"unit": "px", "top": 0, "right": 0, "bottom": 0, "left": 0},
    "z_index": 1
  },
  "children": [
    {
      "elementor_widget": "heading",
      "settings": {
        "title": "SKYYROSE",
        "header_size": "h1",
        "align": "center",
        "typography_font_family": "Cormorant Garamond",
        "typography_font_size": {"unit": "rem", "size": 4},
        "typography_font_size_mobile": {"unit": "rem", "size": 2},
        "typography_letter_spacing": {"unit": "em", "size": 0.3},
        "title_color": "#FAFAFA",
        "_animation": "fadeIn",
        "_animation_delay": 300
      }
    },
    {
      "elementor_widget": "text-editor",
      "settings": {
        "editor": "WHERE LOVE MEETS LUXURY",
        "align": "center",
        "typography_font_family": "Inter",
        "typography_font_size": {"unit": "rem", "size": 1},
        "typography_letter_spacing": {"unit": "em", "size": 0.2},
        "text_color": "rgba(250, 250, 250, 0.8)",
        "_animation": "fadeIn",
        "_animation_delay": 500
      }
    },
    {
      "elementor_widget": "button",
      "settings": {
        "text": "SHOP THE COLLECTIONS",
        "link": {"url": "/shop/"},
        "align": "center",
        "typography_font_size": {"unit": "rem", "size": 0.75},
        "typography_letter_spacing": {"unit": "em", "size": 0.15},
        "button_text_color": "#0D0D0D",
        "background_color": "#FAFAFA",
        "button_text_color_hover": "#FAFAFA",
        "button_background_hover_color": "#0D0D0D",
        "border_radius": {"unit": "px", "size": 0},
        "button_padding": {"unit": "px", "top": 16, "right": 40, "bottom": 16, "left": 40},
        "_animation": "fadeInUp",
        "_animation_delay": 700
      }
    }
  ]
}
```

### Agent Tasks

```yaml
agent_tasks:
  - agent: "content_agent"
    task: "Generate hero video content brief for Oakland sunset/lifestyle shoot"
    priority: "high"

  - agent: "media_agent"
    task: "Source/create hero background video (15-30s loop, 4K, <10MB compressed)"
    priority: "high"
    specs:
      duration: "15-30s"
      resolution: "3840x2160"
      format: "MP4 (H.264)"
      max_size: "10MB"
      content: "Oakland cityscape, Lake Merritt, model in SkyyRose pieces"

  - agent: "seo_agent"
    task: "Optimize hero section for Core Web Vitals (LCP target <2.5s)"
    priority: "high"
```

---

## SECTION 2: COLLECTION TRIPTYCH

### Specification

```yaml
section:
  id: "collection_triptych"
  name: "Collection Cards"
  type: "three_column_grid"
  background: "#F5F3EF"
  padding:
    desktop: "80px 0"
    mobile: "48px 0"
  container_max_width: "1200px"
```

### Content

```yaml
collections:
  - id: "black_rose"
    name: "BLACK ROSE"
    tagline: "Dark Elegance. Limited Always."
    description: "Limited edition pieces for those who understand restraint."
    url: "/collection/black-rose/"
    image: "/assets/images/collections/black-rose-card.jpg"
    background_color: "#0D0D0D"
    text_color: "#FAFAFA"
    accent_color: "#C9A962"
    hover_effect: "zoom_overlay"
    badge: null

  - id: "love_hurts"
    name: "LOVE HURTS"
    tagline: "Wear Your Heart. Own Your Story."
    description: "Emotional pieces honoring our family legacy."
    url: "/collection/love-hurts/"
    image: "/assets/images/collections/love-hurts-card.jpg"
    background_color: "#8B3A3A"
    text_color: "#FAFAFA"
    accent_color: "#D4A5A5"
    hover_effect: "zoom_overlay"
    badge: null

  - id: "signature"
    name: "SIGNATURE"
    tagline: "The Foundation. Built to Last."
    description: "Premium essentials for your everyday wardrobe."
    url: "/collection/signature/"
    image: "/assets/images/collections/signature-card.jpg"
    background_color: "#6B6B6B"
    text_color: "#FAFAFA"
    accent_color: "#1A1A2E"
    hover_effect: "zoom_overlay"
    badge: null
```

### Elementor Configuration

```json
{
  "elementor_widget": "container",
  "settings": {
    "content_width": "boxed",
    "boxed_width": {"unit": "px", "size": 1200},
    "flex_direction": "row",
    "flex_direction_mobile": "column",
    "flex_gap": {"unit": "px", "size": 24},
    "flex_gap_mobile": {"unit": "px", "size": 16},
    "background_color": "#F5F3EF",
    "padding": {"unit": "px", "top": 80, "right": 24, "bottom": 80, "left": 24},
    "padding_mobile": {"unit": "px", "top": 48, "right": 16, "bottom": 48, "left": 16}
  },
  "children": [
    {
      "elementor_widget": "container",
      "settings": {
        "content_width": "full",
        "min_height": {"unit": "px", "size": 400},
        "min_height_mobile": {"unit": "px", "size": 280},
        "flex_direction": "column",
        "flex_justify_content": "center",
        "flex_align_items": "center",
        "background_background": "classic",
        "background_color": "#0D0D0D",
        "background_image": {"url": "{{black_rose_image}}"},
        "background_size": "cover",
        "background_position": "center center",
        "background_overlay_background": "classic",
        "background_overlay_color": "rgba(0,0,0,0.4)",
        "background_overlay_hover_color": "rgba(0,0,0,0.2)",
        "padding": {"unit": "px", "top": 40, "right": 24, "bottom": 40, "left": 24},
        "border_radius": {"unit": "px", "size": 0},
        "css_classes": "collection-card",
        "_element_width": "33.333%",
        "_element_width_mobile": "100%"
      },
      "children": [
        {
          "elementor_widget": "heading",
          "settings": {
            "title": "BLACK ROSE",
            "header_size": "h3",
            "align": "center",
            "typography_font_family": "Cormorant Garamond",
            "typography_font_size": {"unit": "rem", "size": 1.5},
            "typography_letter_spacing": {"unit": "em", "size": 0.2},
            "title_color": "#FAFAFA"
          }
        },
        {
          "elementor_widget": "text-editor",
          "settings": {
            "editor": "Dark Elegance. Limited Always.",
            "align": "center",
            "typography_font_family": "Inter",
            "typography_font_size": {"unit": "rem", "size": 0.875},
            "text_color": "rgba(250, 250, 250, 0.7)"
          }
        },
        {
          "elementor_widget": "button",
          "settings": {
            "text": "EXPLORE",
            "link": {"url": "/collection/black-rose/"},
            "align": "center",
            "button_type": "outline",
            "typography_font_size": {"unit": "rem", "size": 0.75},
            "typography_letter_spacing": {"unit": "em", "size": 0.1},
            "button_text_color": "#FAFAFA",
            "button_border_color": "rgba(250, 250, 250, 0.5)",
            "button_text_color_hover": "#0D0D0D",
            "button_background_hover_color": "#FAFAFA",
            "border_radius": {"unit": "px", "size": 0},
            "button_padding": {"unit": "px", "top": 12, "right": 32, "bottom": 12, "left": 32}
          }
        }
      ]
    }
  ]
}
```

### CSS Custom Styles

```css
/* Collection Card Hover Effects */
.collection-card {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  cursor: pointer;
}

.collection-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.collection-card:hover .elementor-background-overlay {
  opacity: 0.2;
}

.collection-card:hover img {
  transform: scale(1.05);
}

/* Responsive Grid */
@media (max-width: 768px) {
  .collection-card {
    min-height: 280px !important;
  }
}
```

### Agent Tasks

```yaml
agent_tasks:
  - agent: "media_agent"
    task: "Create collection card images (3 images, 800x1000px each)"
    priority: "high"
    specs:
      - file: "black-rose-card.jpg"
        content: "Dark, moody studio shot, model in black pieces, rose gold accents"
      - file: "love-hurts-card.jpg"
        content: "Warm, emotional portrait, Oakland backdrop, burgundy tones"
      - file: "signature-card.jpg"
        content: "Clean, minimal studio shot, neutral tones, essential pieces"

  - agent: "wordpress_agent"
    task: "Create WooCommerce product categories: BLACK ROSE, LOVE HURTS, SIGNATURE"
    priority: "high"
```

---

## SECTION 3: FEATURED PRODUCT

### Specification

```yaml
section:
  id: "featured_product"
  name: "Featured Product Highlight"
  type: "asymmetric_split"
  background: "#FFFFFF"
  padding:
    desktop: "0"
    mobile: "0"
  layout:
    desktop: "60% image / 40% content"
    mobile: "stacked (image first)"
```

### Content

```yaml
featured_product:
  dynamic: true
  source: "woocommerce_featured"
  fallback_product_id: 123

  display:
    badge:
      text: "NEW ARRIVAL"
      background: "#0D0D0D"
      color: "#FAFAFA"

    title:
      format: "{{product.name}}"
      font: "Cormorant Garamond"
      size: "clamp(1.5rem, 3vw, 2rem)"

    price:
      format: "${{product.price}}"
      font: "Inter"
      size: "1.25rem"
      color: "#6B6B6B"

    rating:
      show: true
      format: "stars"
      show_count: true

    description:
      source: "short_description"
      max_chars: 100

    trust_element:
      text: "✓ Free shipping over $150"
      color: "#059669"

    cta:
      text: "ADD TO BAG"
      style: "primary"
      action: "add_to_cart"
```

### Elementor Configuration

```json
{
  "elementor_widget": "container",
  "settings": {
    "content_width": "full",
    "flex_direction": "row",
    "flex_direction_mobile": "column",
    "background_color": "#FFFFFF"
  },
  "children": [
    {
      "elementor_widget": "container",
      "settings": {
        "_element_width": "60%",
        "_element_width_mobile": "100%",
        "min_height": {"unit": "px", "size": 500},
        "min_height_mobile": {"unit": "px", "size": 350},
        "background_background": "classic",
        "background_image": {"url": "{{featured_product.image}}"},
        "background_size": "cover",
        "background_position": "center center"
      }
    },
    {
      "elementor_widget": "container",
      "settings": {
        "_element_width": "40%",
        "_element_width_mobile": "100%",
        "flex_direction": "column",
        "flex_justify_content": "center",
        "padding": {"unit": "px", "top": 60, "right": 60, "bottom": 60, "left": 60},
        "padding_mobile": {"unit": "px", "top": 32, "right": 24, "bottom": 32, "left": 24}
      },
      "children": [
        {
          "elementor_widget": "text-editor",
          "settings": {
            "editor": "NEW ARRIVAL",
            "typography_font_family": "Inter",
            "typography_font_size": {"unit": "rem", "size": 0.75},
            "typography_letter_spacing": {"unit": "em", "size": 0.1},
            "text_color": "#6B6B6B"
          }
        },
        {
          "elementor_widget": "woocommerce-product-title",
          "settings": {
            "header_size": "h2",
            "typography_font_family": "Cormorant Garamond",
            "typography_font_size": {"unit": "rem", "size": 2},
            "title_color": "#0D0D0D"
          }
        },
        {
          "elementor_widget": "woocommerce-product-price",
          "settings": {
            "typography_font_family": "Inter",
            "typography_font_size": {"unit": "rem", "size": 1.25},
            "price_color": "#6B6B6B"
          }
        },
        {
          "elementor_widget": "woocommerce-product-rating",
          "settings": {
            "star_color": "#F59E0B",
            "show_count": true
          }
        },
        {
          "elementor_widget": "woocommerce-product-add-to-cart",
          "settings": {
            "button_text": "ADD TO BAG",
            "button_text_color": "#FAFAFA",
            "button_background_color": "#0D0D0D",
            "button_text_color_hover": "#0D0D0D",
            "button_background_hover_color": "#FAFAFA",
            "button_border_color_hover": "#0D0D0D",
            "typography_font_size": {"unit": "rem", "size": 0.875},
            "typography_letter_spacing": {"unit": "em", "size": 0.1}
          }
        },
        {
          "elementor_widget": "text-editor",
          "settings": {
            "editor": "✓ Free shipping over $150",
            "typography_font_size": {"unit": "rem", "size": 0.875},
            "text_color": "#059669"
          }
        }
      ]
    }
  ]
}
```

### WooCommerce Integration

```php
<?php
/**
 * Get Featured Product for Homepage
 * Add to theme functions.php or custom plugin
 */
function skyyrose_get_featured_product() {
    $args = array(
        'post_type' => 'product',
        'posts_per_page' => 1,
        'meta_key' => '_featured',
        'meta_value' => 'yes',
        'orderby' => 'date',
        'order' => 'DESC'
    );

    $featured = new WP_Query($args);

    if ($featured->have_posts()) {
        $featured->the_post();
        $product = wc_get_product(get_the_ID());

        return array(
            'id' => $product->get_id(),
            'name' => $product->get_name(),
            'price' => $product->get_price(),
            'image' => wp_get_attachment_url($product->get_image_id()),
            'rating' => $product->get_average_rating(),
            'review_count' => $product->get_review_count(),
            'short_description' => $product->get_short_description(),
            'url' => $product->get_permalink()
        );
    }

    wp_reset_postdata();
    return null;
}
```

### Agent Tasks

```yaml
agent_tasks:
  - agent: "wordpress_agent"
    task: "Set up featured product meta field and rotation logic"
    priority: "medium"

  - agent: "media_agent"
    task: "Create featured product lifestyle image (1200x800px, on-model shot)"
    priority: "high"
```

---

## SECTION 4: BRAND STORY STRIP

### Specification

```yaml
section:
  id: "brand_story"
  name: "Brand Story Strip"
  type: "parallax_text_overlay"
  background:
    type: "image"
    url: "/assets/images/oakland-skyline.jpg"
    parallax: true
    parallax_speed: 0.5
    overlay: "linear-gradient(180deg, rgba(13,13,13,0.7) 0%, rgba(13,13,13,0.85) 100%)"
  padding:
    desktop: "120px 24px"
    mobile: "80px 24px"
  text_align: "center"
  max_width: "800px"
```

### Content

```yaml
content:
  headline:
    text: "BORN IN THE TOWN"
    font: "Cormorant Garamond"
    size: "clamp(1.5rem, 4vw, 2.5rem)"
    color: "#FAFAFA"
    margin_bottom: "24px"

  body:
    text: "From Oakland to the world, SkyyRose blends Bay Area authenticity with luxury craftsmanship. This isn't fast fashion—it's forever fashion."
    font: "Inter"
    size: "1rem"
    line_height: "1.7"
    color: "rgba(250, 250, 250, 0.8)"
    max_chars: 200
    margin_bottom: "32px"

  cta:
    text: "OUR STORY"
    url: "/about/"
    style: "outline_white"
    padding: "14px 32px"
```

### Elementor Configuration

```json
{
  "elementor_widget": "container",
  "settings": {
    "content_width": "full",
    "min_height": {"unit": "px", "size": 400},
    "flex_direction": "column",
    "flex_justify_content": "center",
    "flex_align_items": "center",
    "background_background": "classic",
    "background_image": {"url": "{{oakland_skyline}}"},
    "background_size": "cover",
    "background_position": "center center",
    "background_attachment": "fixed",
    "background_overlay_background": "gradient",
    "background_overlay_color": "rgba(13,13,13,0.7)",
    "background_overlay_color_b": "rgba(13,13,13,0.85)",
    "background_overlay_gradient_angle": {"unit": "deg", "size": 180},
    "padding": {"unit": "px", "top": 120, "right": 24, "bottom": 120, "left": 24},
    "padding_mobile": {"unit": "px", "top": 80, "right": 24, "bottom": 80, "left": 24}
  },
  "children": [
    {
      "elementor_widget": "container",
      "settings": {
        "content_width": "boxed",
        "boxed_width": {"unit": "px", "size": 800},
        "flex_direction": "column",
        "flex_align_items": "center"
      },
      "children": [
        {
          "elementor_widget": "heading",
          "settings": {
            "title": "\"BORN IN THE TOWN\"",
            "header_size": "h2",
            "align": "center",
            "typography_font_family": "Cormorant Garamond",
            "typography_font_size": {"unit": "rem", "size": 2.5},
            "typography_font_size_mobile": {"unit": "rem", "size": 1.5},
            "title_color": "#FAFAFA",
            "_animation": "fadeIn"
          }
        },
        {
          "elementor_widget": "text-editor",
          "settings": {
            "editor": "From Oakland to the world, SkyyRose blends Bay Area authenticity with luxury craftsmanship. This isn't fast fashion—it's forever fashion.",
            "align": "center",
            "typography_font_family": "Inter",
            "typography_font_size": {"unit": "rem", "size": 1},
            "typography_line_height": {"unit": "em", "size": 1.7},
            "text_color": "rgba(250, 250, 250, 0.8)"
          }
        },
        {
          "elementor_widget": "button",
          "settings": {
            "text": "OUR STORY",
            "link": {"url": "/about/"},
            "align": "center",
            "button_type": "outline",
            "typography_font_size": {"unit": "rem", "size": 0.75},
            "typography_letter_spacing": {"unit": "em", "size": 0.1},
            "button_text_color": "#FAFAFA",
            "button_border_color": "rgba(250, 250, 250, 0.5)",
            "button_text_color_hover": "#0D0D0D",
            "button_background_hover_color": "#FAFAFA",
            "border_radius": {"unit": "px", "size": 0},
            "button_padding": {"unit": "px", "top": 14, "right": 32, "bottom": 14, "left": 32}
          }
        }
      ]
    }
  ]
}
```

### Agent Tasks

```yaml
agent_tasks:
  - agent: "media_agent"
    task: "Source/create Oakland skyline image (2400x1600px, muted tones)"
    priority: "medium"
    specs:
      location: "Oakland, CA"
      time: "Golden hour or blue hour"
      style: "Slightly desaturated, moody"
      landmarks: "Lake Merritt, downtown skyline optional"

  - agent: "content_agent"
    task: "Draft brand story page content (500-800 words)"
    priority: "medium"
```

---

## SECTION 5: UGC GALLERY

### Specification

```yaml
section:
  id: "ugc_gallery"
  name: "Social Proof / UGC Gallery"
  type: "instagram_grid"
  background: "#F5F3EF"
  padding:
    desktop: "80px 0"
    mobile: "48px 0"
```

### Content

```yaml
ugc:
  headline:
    text: "THE SKYYROSE COMMUNITY"
    font: "Cormorant Garamond"
    size: "clamp(1.25rem, 3vw, 1.75rem)"

  source:
    type: "instagram_feed"
    hashtag: "#SKYYROSE"
    fallback: "curated_images"

  grid:
    columns:
      desktop: 6
      tablet: 4
      mobile: 3
    images: 6
    aspect_ratio: "1:1"
    gap: "8px"

  footer:
    handle: "@skyyrose"
    hashtag: "#SKYYROSE"
    cta: "Share Your Look"
    url: "https://instagram.com/skyyrose"
```

### Elementor Configuration

```json
{
  "elementor_widget": "container",
  "settings": {
    "content_width": "full",
    "background_color": "#F5F3EF",
    "padding": {"unit": "px", "top": 80, "right": 0, "bottom": 80, "left": 0},
    "padding_mobile": {"unit": "px", "top": 48, "right": 0, "bottom": 48, "left": 0}
  },
  "children": [
    {
      "elementor_widget": "heading",
      "settings": {
        "title": "THE SKYYROSE COMMUNITY",
        "header_size": "h2",
        "align": "center",
        "typography_font_family": "Cormorant Garamond",
        "typography_font_size": {"unit": "rem", "size": 1.75},
        "title_color": "#0D0D0D"
      }
    },
    {
      "elementor_widget": "shortcode",
      "settings": {
        "shortcode": "[instagram-feed feed=1]"
      }
    },
    {
      "elementor_widget": "text-editor",
      "settings": {
        "editor": "<a href='https://instagram.com/skyyrose' target='_blank'>@skyyrose</a> · <a href='https://instagram.com/explore/tags/skyyrose' target='_blank'>#SKYYROSE</a>",
        "align": "center",
        "typography_font_size": {"unit": "rem", "size": 0.875},
        "text_color": "#6B6B6B"
      }
    }
  ]
}
```

### Plugin Requirements

```yaml
plugins:
  recommended:
    - name: "Smash Balloon Instagram Feed"
      slug: "instagram-feed"
      purpose: "Instagram integration"
      config:
        feed_type: "hashtag"
        hashtag: "skyyrose"
        num_posts: 6
        columns: 6
        columns_mobile: 3
        show_header: false
        show_follow_button: false

  alternative:
    - name: "Spotlight Social Media Feeds"
      slug: "developer/developer"
```

### Agent Tasks

```yaml
agent_tasks:
  - agent: "social_agent"
    task: "Set up Instagram Business account and API integration"
    priority: "medium"

  - agent: "wordpress_agent"
    task: "Install and configure Smash Balloon Instagram Feed plugin"
    priority: "medium"

  - agent: "media_agent"
    task: "Create 6 placeholder UGC-style images for pre-launch"
    priority: "low"
```

---

## SECTION 6: NEWSLETTER

### Specification

```yaml
section:
  id: "newsletter"
  name: "Newsletter Capture"
  type: "email_capture"
  background: "#0D0D0D"
  padding:
    desktop: "80px 24px"
    mobile: "60px 24px"
  text_align: "center"
```

### Content

```yaml
newsletter:
  headline:
    text: "JOIN THE INNER CIRCLE"
    font: "Cormorant Garamond"
    size: "clamp(1.25rem, 3vw, 1.5rem)"
    color: "#FAFAFA"

  subheadline:
    text: "First access to drops. Exclusive offers. No spam—just love."
    font: "Inter"
    size: "0.875rem"
    color: "rgba(250, 250, 250, 0.7)"

  form:
    provider: "klaviyo"
    list_id: "{{KLAVIYO_LIST_ID}}"
    fields:
      - type: "email"
        placeholder: "Email Address"
        required: true
    button:
      text: "JOIN"
      style: "primary_inverted"
    success_message: "Welcome to the inner circle! Check your inbox."

  privacy:
    text: "🔒 We respect your privacy"
    link: "/privacy-policy/"

  incentive:
    text: "Get 10% off your first order"
    show: true
```

### Elementor Configuration

```json
{
  "elementor_widget": "container",
  "settings": {
    "content_width": "full",
    "background_color": "#0D0D0D",
    "padding": {"unit": "px", "top": 80, "right": 24, "bottom": 80, "left": 24},
    "padding_mobile": {"unit": "px", "top": 60, "right": 24, "bottom": 60, "left": 24}
  },
  "children": [
    {
      "elementor_widget": "container",
      "settings": {
        "content_width": "boxed",
        "boxed_width": {"unit": "px", "size": 500},
        "flex_direction": "column",
        "flex_align_items": "center"
      },
      "children": [
        {
          "elementor_widget": "heading",
          "settings": {
            "title": "JOIN THE INNER CIRCLE",
            "header_size": "h2",
            "align": "center",
            "typography_font_family": "Cormorant Garamond",
            "typography_font_size": {"unit": "rem", "size": 1.5},
            "typography_letter_spacing": {"unit": "em", "size": 0.1},
            "title_color": "#FAFAFA"
          }
        },
        {
          "elementor_widget": "text-editor",
          "settings": {
            "editor": "First access to drops. Exclusive offers. No spam—just love.",
            "align": "center",
            "typography_font_family": "Inter",
            "typography_font_size": {"unit": "rem", "size": 0.875},
            "text_color": "rgba(250, 250, 250, 0.7)"
          }
        },
        {
          "elementor_widget": "shortcode",
          "settings": {
            "shortcode": "[klaviyo_form id=\"homepage_newsletter\"]"
          }
        },
        {
          "elementor_widget": "text-editor",
          "settings": {
            "editor": "🔒 We respect your privacy",
            "align": "center",
            "typography_font_size": {"unit": "rem", "size": 0.75},
            "text_color": "rgba(250, 250, 250, 0.5)"
          }
        }
      ]
    }
  ]
}
```

### Klaviyo Integration

```javascript
// Klaviyo Form Embed Code
<div class="klaviyo-form-container">
  <form id="skyyrose-newsletter" class="klaviyo-form">
    <div class="form-row">
      <input
        type="email"
        name="email"
        placeholder="Email Address"
        required
        class="klaviyo-email-input"
      />
      <button type="submit" class="klaviyo-submit">JOIN</button>
    </div>
  </form>
</div>

<script>
  // Klaviyo API Integration
  document.getElementById('skyyrose-newsletter').addEventListener('submit', function(e) {
    e.preventDefault();

    var email = this.querySelector('input[name="email"]').value;

    _learnq.push(['identify', {
      '$email': email,
      'Newsletter Source': 'Homepage'
    }]);

    _learnq.push(['track', 'Newsletter Signup', {
      'Source': 'Homepage Footer'
    }]);

    // Show success message
    this.innerHTML = '<p class="success">Welcome to the inner circle! ✓</p>';
  });
</script>
```

### CSS Styles

```css
/* Newsletter Form Styles */
.klaviyo-form-container {
  width: 100%;
  max-width: 400px;
  margin: 24px auto 0;
}

.klaviyo-form .form-row {
  display: flex;
  gap: 8px;
}

.klaviyo-email-input {
  flex: 1;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 14px 16px;
  color: #FAFAFA;
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
}

.klaviyo-email-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.klaviyo-email-input:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.5);
}

.klaviyo-submit {
  background: #FAFAFA;
  color: #0D0D0D;
  border: none;
  padding: 14px 24px;
  font-family: 'Inter', sans-serif;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  cursor: pointer;
  transition: all 0.3s ease;
}

.klaviyo-submit:hover {
  background: #C9A962;
  color: #0D0D0D;
}

.klaviyo-form .success {
  color: #059669;
  text-align: center;
  padding: 14px;
}

@media (max-width: 480px) {
  .klaviyo-form .form-row {
    flex-direction: column;
  }

  .klaviyo-submit {
    width: 100%;
  }
}
```

### Agent Tasks

```yaml
agent_tasks:
  - agent: "marketing_agent"
    task: "Set up Klaviyo account and create homepage newsletter list"
    priority: "high"

  - agent: "wordpress_agent"
    task: "Install Klaviyo plugin and configure API integration"
    priority: "high"
```

---

## SECTION 7: FOOTER

### Specification

```yaml
section:
  id: "footer"
  name: "Site Footer"
  type: "multi_column_footer"
  background: "#F5F3EF"
  padding:
    desktop: "60px 24px 40px"
    mobile: "48px 24px 32px"
  border_top: "1px solid rgba(0,0,0,0.1)"
```

### Content

```yaml
footer:
  columns:
    - title: "SHOP"
      links:
        - text: "All Products"
          url: "/shop/"
        - text: "BLACK ROSE"
          url: "/collection/black-rose/"
        - text: "LOVE HURTS"
          url: "/collection/love-hurts/"
        - text: "SIGNATURE"
          url: "/collection/signature/"
        - text: "New Arrivals"
          url: "/shop/?orderby=date"

    - title: "SUPPORT"
      links:
        - text: "Shipping & Delivery"
          url: "/shipping/"
        - text: "Returns & Exchanges"
          url: "/returns/"
        - text: "Size Guide"
          url: "/size-guide/"
        - text: "Contact Us"
          url: "/contact/"
        - text: "FAQ"
          url: "/faq/"

    - title: "COMPANY"
      links:
        - text: "Our Story"
          url: "/about/"
        - text: "Journal"
          url: "/journal/"
        - text: "Sustainability"
          url: "/sustainability/"
        - text: "Careers"
          url: "/careers/"

    - title: "CONNECT"
      links:
        - text: "Instagram"
          url: "https://instagram.com/skyyrose"
          external: true
          icon: "instagram"
        - text: "TikTok"
          url: "https://tiktok.com/@skyyrose"
          external: true
          icon: "tiktok"
        - text: "Pinterest"
          url: "https://pinterest.com/skyyrose"
          external: true
          icon: "pinterest"

  bottom_bar:
    copyright: "© {{year}} SkyyRose. All rights reserved."
    links:
      - text: "Privacy Policy"
        url: "/privacy-policy/"
      - text: "Terms of Service"
        url: "/terms/"
    payment_icons:
      - "visa"
      - "mastercard"
      - "amex"
      - "paypal"
      - "apple-pay"
      - "google-pay"
```

### Elementor Configuration

```json
{
  "elementor_widget": "container",
  "settings": {
    "content_width": "boxed",
    "boxed_width": {"unit": "px", "size": 1200},
    "background_color": "#F5F3EF",
    "border_border": "solid",
    "border_width": {"unit": "px", "top": 1, "right": 0, "bottom": 0, "left": 0},
    "border_color": "rgba(0,0,0,0.1)",
    "padding": {"unit": "px", "top": 60, "right": 24, "bottom": 40, "left": 24}
  },
  "children": [
    {
      "elementor_widget": "container",
      "settings": {
        "flex_direction": "row",
        "flex_direction_mobile": "column",
        "flex_gap": {"unit": "px", "size": 48},
        "flex_gap_mobile": {"unit": "px", "size": 32}
      },
      "children": [
        {
          "elementor_widget": "container",
          "settings": {
            "_element_width": "25%",
            "_element_width_mobile": "50%",
            "flex_direction": "column"
          },
          "children": [
            {
              "elementor_widget": "heading",
              "settings": {
                "title": "SHOP",
                "header_size": "h4",
                "typography_font_family": "Inter",
                "typography_font_size": {"unit": "rem", "size": 0.75},
                "typography_font_weight": "600",
                "typography_letter_spacing": {"unit": "em", "size": 0.1},
                "title_color": "#0D0D0D"
              }
            },
            {
              "elementor_widget": "icon-list",
              "settings": {
                "icon_list": [
                  {"text": "All Products", "link": {"url": "/shop/"}},
                  {"text": "BLACK ROSE", "link": {"url": "/collection/black-rose/"}},
                  {"text": "LOVE HURTS", "link": {"url": "/collection/love-hurts/"}},
                  {"text": "SIGNATURE", "link": {"url": "/collection/signature/"}}
                ],
                "view": "stacked",
                "typography_font_family": "Inter",
                "typography_font_size": {"unit": "rem", "size": 0.875},
                "text_color": "#6B6B6B",
                "text_color_hover": "#0D0D0D"
              }
            }
          ]
        }
      ]
    },
    {
      "elementor_widget": "divider",
      "settings": {
        "style": "solid",
        "color": "rgba(0,0,0,0.1)",
        "gap": {"unit": "px", "size": 40}
      }
    },
    {
      "elementor_widget": "container",
      "settings": {
        "flex_direction": "row",
        "flex_direction_mobile": "column",
        "flex_justify_content": "space-between",
        "flex_align_items": "center"
      },
      "children": [
        {
          "elementor_widget": "text-editor",
          "settings": {
            "editor": "© 2024 SkyyRose. All rights reserved.",
            "typography_font_size": {"unit": "rem", "size": 0.75},
            "text_color": "#6B6B6B"
          }
        },
        {
          "elementor_widget": "text-editor",
          "settings": {
            "editor": "<a href='/privacy-policy/'>Privacy</a> · <a href='/terms/'>Terms</a>",
            "typography_font_size": {"unit": "rem", "size": 0.75},
            "text_color": "#6B6B6B"
          }
        },
        {
          "elementor_widget": "image",
          "settings": {
            "image": {"url": "/assets/images/payment-icons.png"},
            "image_size": "custom",
            "image_custom_dimension": {"width": 200}
          }
        }
      ]
    }
  ]
}
```

---

## FULL PAGE ASSEMBLY

### Page Structure Order

```yaml
page_sections:
  - section_id: "hero"
    order: 1
    visible: true

  - section_id: "collection_triptych"
    order: 2
    visible: true

  - section_id: "featured_product"
    order: 3
    visible: true

  - section_id: "brand_story"
    order: 4
    visible: true

  - section_id: "ugc_gallery"
    order: 5
    visible: true

  - section_id: "newsletter"
    order: 6
    visible: true

  - section_id: "footer"
    order: 7
    visible: true
    template: "theme_builder"
```

### Performance Requirements

```yaml
performance:
  core_web_vitals:
    lcp: "<2.5s"
    fid: "<100ms"
    cls: "<0.1"

  optimization:
    - lazy_load_images: true
    - lazy_load_videos: true
    - preload_hero_image: true
    - defer_non_critical_css: true
    - minify_css: true
    - minify_js: true

  image_specs:
    hero_video:
      format: "MP4 (H.264)"
      max_size: "10MB"
      poster_image: true
    images:
      format: "WebP with JPG fallback"
      quality: 85
      sizes:
        - "400w"
        - "800w"
        - "1200w"
        - "1600w"
```

### Agent Execution Checklist

```yaml
execution_checklist:
  phase_1_setup:
    - task: "Install required plugins"
      plugins:
        - "elementor-pro"
        - "woocommerce"
        - "instagram-feed"
        - "klaviyo"
      status: "pending"

    - task: "Configure global design tokens in Elementor"
      status: "pending"

    - task: "Create page in WordPress"
      status: "pending"

  phase_2_content:
    - task: "Upload hero video/image"
      status: "pending"

    - task: "Upload collection card images"
      status: "pending"

    - task: "Set featured product"
      status: "pending"

    - task: "Upload brand story background"
      status: "pending"

  phase_3_build:
    - task: "Build Section 1: Hero"
      status: "pending"

    - task: "Build Section 2: Collection Triptych"
      status: "pending"

    - task: "Build Section 3: Featured Product"
      status: "pending"

    - task: "Build Section 4: Brand Story"
      status: "pending"

    - task: "Build Section 5: UGC Gallery"
      status: "pending"

    - task: "Build Section 6: Newsletter"
      status: "pending"

  phase_4_optimize:
    - task: "Mobile responsive testing"
      status: "pending"

    - task: "Page speed optimization"
      status: "pending"

    - task: "SEO meta configuration"
      status: "pending"
```

---

## API ENDPOINTS FOR AGENTS

```yaml
api_endpoints:
  wordpress:
    base_url: "{{SITE_URL}}/wp-json"

    pages:
      create: "POST /wp/v2/pages"
      update: "PUT /wp/v2/pages/{id}"
      get: "GET /wp/v2/pages/{id}"

    media:
      upload: "POST /wp/v2/media"
      get: "GET /wp/v2/media/{id}"

  woocommerce:
    base_url: "{{SITE_URL}}/wp-json/wc/v3"

    products:
      featured: "GET /products?featured=true"
      categories: "GET /products/categories"

  elementor:
    template_import: "POST /elementor/v1/template/import"

  klaviyo:
    base_url: "https://a.klaviyo.com/api"

    lists:
      subscribe: "POST /v2/list/{list_id}/subscribe"
```

---

*End of Homepage Specification*
