# SKYYROSE BLACK ROSE COLLECTION PAGE SPECIFICATION
# Version: 1.0.0
# Last Updated: 2024-12-11
# Platform: WordPress + WooCommerce + Elementor Pro

---

## PAGE METADATA

```yaml
page:
  name: "BLACK ROSE Collection"
  slug: "/collection/black-rose/"
  template: "elementor_header_footer"
  collection_id: "black_rose"
  woocommerce_category: "black-rose"
  
  seo:
    title: "BLACK ROSE | Limited Edition Dark Elegance | SkyyRose"
    description: "Discover BLACK ROSE - limited edition luxury streetwear. Only 50 pieces per style. When they're gone, they're gone. Shop the current drop now."
    keywords: ["limited edition streetwear", "luxury hoodies", "exclusive fashion", "numbered edition clothing"]
    
  og:
    image: "/assets/images/og-black-rose.jpg"
    type: "product.group"
    
  schema_type: "CollectionPage"
  
  brand_essence:
    mood: "Dark, mysterious, exclusive"
    tagline: "Dark Elegance. Limited Always."
    voice: "Confident, restrained, never desperate"
    scarcity_model: "numbered_editions"
    edition_limit: 50
```

---

## COLLECTION DESIGN TOKENS

```yaml
collection_tokens:
  colors:
    # BLACK ROSE: Dark, Mysterious, Icy, Exclusive
    primary: "#0D0D0D"           # Pure Black
    secondary: "#1A1A1A"         # Soft Black
    accent: "#C0C0C0"            # Metallic Silver
    accent_bright: "#E8E8E8"     # Bright Silver/Chrome
    white: "#FAFAFA"             # Pure White
    chrome: "#A8A8A8"            # Chrome/Steel
    text_primary: "#FAFAFA"
    text_secondary: "rgba(250, 250, 250, 0.7)"
    text_muted: "rgba(250, 250, 250, 0.5)"
    
  gradients:
    hero: "linear-gradient(180deg, #000000 0%, #1A1A1A 50%, #0D0D0D 100%)"
    overlay: "linear-gradient(180deg, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0.7) 100%)"
    metallic: "linear-gradient(135deg, #A8A8A8 0%, #E8E8E8 50%, #C0C0C0 100%)"
    
  typography:
    headings:
      color: "#C0C0C0"           # Metallic Silver headings
      family: "Cormorant Garamond"
    body:
      color: "rgba(250, 250, 250, 0.8)"
      family: "Inter"
      
  ui_elements:
    badge_low_stock:
      background: "#C0C0C0"      # Silver
      color: "#0D0D0D"
      text: "LOW STOCK"
    badge_sold_out:
      background: "transparent"
      color: "#C0C0C0"           # Silver
      text: "SOLD OUT"
    badge_edition:
      background: "#0D0D0D"
      color: "#C0C0C0"           # Silver
      border: "1px solid rgba(192, 192, 192, 0.3)"
```

---

## SECTION 1: CINEMATIC HERO

### Specification

```yaml
section:
  id: "br_hero"
  name: "Cinematic Hero"
  type: "full_screen_video_hero"
  height:
    desktop: "100vh"
    mobile: "90vh"
  background:
    type: "video"
    video_url: "/assets/videos/black-rose-hero.mp4"
    fallback_image: "/assets/images/black-rose-hero-fallback.jpg"
    overlay: "linear-gradient(180deg, rgba(0,0,0,0.4) 0%, rgba(0,0,0,0.6) 100%)"
    
  video_specs:
    content: "Slow-motion: dark studio, single dramatic light source, model in BLACK ROSE pieces, rose petals falling"
    duration: "15-20s loop"
    resolution: "4K"
    framerate: "24fps for cinematic feel"
    color_grade: "High contrast, deep blacks, gold highlights"
```

### Content

```yaml
content:
  collection_name:
    text: "BLACK ROSE"
    font: "Cormorant Garamond"
    size: "clamp(2.5rem, 8vw, 5rem)"
    weight: 400
    letter_spacing: "0.3em"
    color: "#C9A962"
    text_shadow: "0 4px 20px rgba(0,0,0,0.5)"
    
  tagline:
    text: "Dark Elegance. Limited Always."
    font: "Inter"
    size: "clamp(0.875rem, 2vw, 1.125rem)"
    weight: 300
    letter_spacing: "0.2em"
    color: "rgba(250, 250, 250, 0.7)"
    margin_top: "16px"
    
  cta_primary:
    text: "ENTER THE COLLECTION"
    url: "#current-drop"
    style:
      background: "#C9A962"
      color: "#0D0D0D"
      padding: "18px 48px"
      font_size: "0.75rem"
      letter_spacing: "0.15em"
      font_weight: 500
      hover:
        background: "#FAFAFA"
        color: "#0D0D0D"
    margin_top: "40px"
    
  scarcity_badge:
    type: "bordered_box"
    content:
      line1: "LIMITED EDITION"
      line2: "Only 50 Pieces Per Style"
    style:
      border: "1px solid rgba(201, 169, 98, 0.3)"
      padding: "16px 32px"
      background: "rgba(0,0,0,0.3)"
    margin_top: "24px"
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
    "background_video_link": "/assets/videos/black-rose-hero.mp4",
    "background_video_fallback": {"url": "/assets/images/black-rose-hero-fallback.jpg"},
    "background_overlay_background": "gradient",
    "background_overlay_color": "rgba(0,0,0,0.4)",
    "background_overlay_color_b": "rgba(0,0,0,0.6)",
    "z_index": 1
  },
  "children": [
    {
      "elementor_widget": "heading",
      "settings": {
        "title": "BLACK ROSE",
        "header_size": "h1",
        "align": "center",
        "typography_font_family": "Cormorant Garamond",
        "typography_font_size": {"unit": "rem", "size": 5},
        "typography_font_size_mobile": {"unit": "rem", "size": 2.5},
        "typography_letter_spacing": {"unit": "em", "size": 0.3},
        "typography_font_weight": "400",
        "title_color": "#C9A962",
        "text_shadow_text_shadow": {"horizontal": 0, "vertical": 4, "blur": 20, "color": "rgba(0,0,0,0.5)"},
        "_animation": "fadeIn",
        "_animation_delay": 300
      }
    },
    {
      "elementor_widget": "text-editor",
      "settings": {
        "editor": "Dark Elegance. Limited Always.",
        "align": "center",
        "typography_font_family": "Inter",
        "typography_font_size": {"unit": "rem", "size": 1.125},
        "typography_font_weight": "300",
        "typography_letter_spacing": {"unit": "em", "size": 0.2},
        "text_color": "rgba(250, 250, 250, 0.7)",
        "_animation": "fadeIn",
        "_animation_delay": 500
      }
    },
    {
      "elementor_widget": "button",
      "settings": {
        "text": "ENTER THE COLLECTION",
        "link": {"url": "#current-drop"},
        "align": "center",
        "typography_font_size": {"unit": "rem", "size": 0.75},
        "typography_letter_spacing": {"unit": "em", "size": 0.15},
        "button_text_color": "#0D0D0D",
        "background_color": "#C9A962",
        "button_text_color_hover": "#0D0D0D",
        "button_background_hover_color": "#FAFAFA",
        "border_radius": {"unit": "px", "size": 0},
        "button_padding": {"unit": "px", "top": 18, "right": 48, "bottom": 18, "left": 48},
        "_animation": "fadeInUp",
        "_animation_delay": 700
      }
    },
    {
      "elementor_widget": "container",
      "settings": {
        "content_width": "full",
        "border_border": "solid",
        "border_width": {"unit": "px", "top": 1, "right": 1, "bottom": 1, "left": 1},
        "border_color": "rgba(201, 169, 98, 0.3)",
        "background_color": "rgba(0,0,0,0.3)",
        "padding": {"unit": "px", "top": 16, "right": 32, "bottom": 16, "left": 32},
        "margin": {"unit": "px", "top": 24},
        "_animation": "fadeIn",
        "_animation_delay": 900
      },
      "children": [
        {
          "elementor_widget": "text-editor",
          "settings": {
            "editor": "<div style='text-align:center'><span style='color:#C9A962;font-size:0.75rem;letter-spacing:0.15em'>LIMITED EDITION</span><br><span style='color:rgba(250,250,250,0.8);font-size:0.875rem'>Only 50 Pieces Per Style</span></div>"
          }
        }
      ]
    }
  ]
}
```

---

## SECTION 2: PHILOSOPHY

### Specification

```yaml
section:
  id: "br_philosophy"
  name: "Collection Philosophy"
  type: "split_content"
  background: "#0A0A0A"
  padding:
    desktop: "100px 0"
    mobile: "60px 0"
  layout:
    desktop: "50% image / 50% content"
    mobile: "stacked"
```

### Content

```yaml
content:
  image:
    url: "/assets/images/black-rose-detail.jpg"
    alt: "BLACK ROSE fabric detail showing quality stitching"
    type: "extreme_closeup"
    content: "Macro shot of fabric texture, stitching detail, or embroidery"
    
  headline:
    text: "NOT EVERYTHING BEAUTIFUL IS MEANT FOR EVERYONE."
    font: "Cormorant Garamond"
    size: "clamp(1.25rem, 3vw, 1.75rem)"
    color: "#C9A962"
    style: "italic"
    
  body_copy:
    paragraphs:
      - text: "The BLACK ROSE collection exists for those who understand that true luxury is restraint."
        style: "primary"
        
      - text: "Each piece is numbered. Each drop is final. When they're gone, they're gone."
        style: "italic"
        color: "rgba(250, 250, 250, 0.6)"
        
  details:
    show: true
    items:
      - label: "Edition Size"
        value: "50 per style"
      - label: "Materials"
        value: "Premium French Terry, Italian hardware"
      - label: "Production"
        value: "Single-run, never restocked"
```

### Elementor Configuration

```json
{
  "elementor_widget": "container",
  "settings": {
    "content_width": "full",
    "background_color": "#0A0A0A",
    "padding": {"unit": "px", "top": 100, "right": 0, "bottom": 100, "left": 0},
    "padding_mobile": {"unit": "px", "top": 60, "right": 0, "bottom": 60, "left": 0}
  },
  "children": [
    {
      "elementor_widget": "container",
      "settings": {
        "content_width": "boxed",
        "boxed_width": {"unit": "px", "size": 1200},
        "flex_direction": "row",
        "flex_direction_mobile": "column",
        "flex_gap": {"unit": "px", "size": 60}
      },
      "children": [
        {
          "elementor_widget": "container",
          "settings": {
            "_element_width": "50%",
            "_element_width_mobile": "100%",
            "min_height": {"unit": "px", "size": 400},
            "min_height_mobile": {"unit": "px", "size": 300}
          },
          "children": [
            {
              "elementor_widget": "image",
              "settings": {
                "image": {"url": "/assets/images/black-rose-detail.jpg"},
                "image_size": "full",
                "width": {"unit": "%", "size": 100},
                "height": {"unit": "%", "size": 100},
                "object-fit": "cover"
              }
            }
          ]
        },
        {
          "elementor_widget": "container",
          "settings": {
            "_element_width": "50%",
            "_element_width_mobile": "100%",
            "flex_direction": "column",
            "flex_justify_content": "center",
            "padding": {"unit": "px", "top": 0, "right": 40, "bottom": 0, "left": 40},
            "padding_mobile": {"unit": "px", "top": 32, "right": 24, "bottom": 0, "left": 24}
          },
          "children": [
            {
              "elementor_widget": "heading",
              "settings": {
                "title": "\"NOT EVERYTHING BEAUTIFUL IS MEANT FOR EVERYONE.\"",
                "header_size": "h2",
                "typography_font_family": "Cormorant Garamond",
                "typography_font_size": {"unit": "rem", "size": 1.75},
                "typography_font_style": "italic",
                "title_color": "#C9A962",
                "_animation": "fadeIn"
              }
            },
            {
              "elementor_widget": "text-editor",
              "settings": {
                "editor": "The BLACK ROSE collection exists for those who understand that true luxury is restraint.",
                "typography_font_family": "Inter",
                "typography_font_size": {"unit": "rem", "size": 1},
                "typography_line_height": {"unit": "em", "size": 1.7},
                "text_color": "rgba(250, 250, 250, 0.8)"
              }
            },
            {
              "elementor_widget": "text-editor",
              "settings": {
                "editor": "Each piece is numbered. Each drop is final.<br>When they're gone, they're gone.",
                "typography_font_family": "Inter",
                "typography_font_size": {"unit": "rem", "size": 0.9375},
                "typography_font_style": "italic",
                "typography_line_height": {"unit": "em", "size": 1.7},
                "text_color": "rgba(250, 250, 250, 0.6)"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

---

## SECTION 3: CURRENT DROP (Product Showcase)

### Specification

```yaml
section:
  id: "br_current_drop"
  name: "The Current Drop"
  type: "product_grid"
  anchor: "current-drop"
  background: "#0D0D0D"
  padding:
    desktop: "100px 24px"
    mobile: "60px 16px"
```

### Content

```yaml
content:
  header:
    pretitle: "THE CURRENT DROP"
    title: "Drop 004"
    subtitle: "December 2024"
    style:
      pretitle:
        font: "Cormorant Garamond"
        size: "1.5rem"
        color: "#C9A962"
      title:
        font: "Inter"
        size: "0.875rem"
        color: "rgba(250, 250, 250, 0.5)"
        
  product_grid:
    source: "woocommerce"
    category: "black-rose"
    tag: "current-drop"
    columns:
      desktop: 4
      tablet: 3
      mobile: 2
    gap: "16px"
    max_products: 8
    
  product_card:
    show_edition_number: true
    edition_format: "#{{number}}/50"
    show_stock_badge: true
    stock_threshold: 10
    badges:
      low_stock:
        text: "LOW STOCK"
        background: "#C9A962"
        color: "#0D0D0D"
      sold_out:
        text: "SOLD OUT"
        overlay: true
        overlay_color: "rgba(0,0,0,0.7)"
        
  cta:
    text: "VIEW ALL {{count}} PIECES"
    url: "/shop/?collection=black-rose&drop=current"
    style: "outline_gold"
```

### Product Card Structure

```yaml
product_card_spec:
  container:
    border: "1px solid rgba(250, 250, 250, 0.1)"
    background: "transparent"
    padding: "0"
    hover:
      border_color: "rgba(201, 169, 98, 0.3)"
      
  image:
    aspect_ratio: "1:1"
    background: "#1A1A1A"
    hover_effect: "subtle_zoom"
    
  badges:
    position: "top-left"
    margin: "8px"
    
  edition_badge:
    position: "top-right"
    margin: "8px"
    background: "#0D0D0D"
    color: "#C9A962"
    border: "1px solid rgba(201, 169, 98, 0.3)"
    padding: "4px 8px"
    font_size: "0.625rem"
    
  content:
    padding: "16px"
    
  title:
    font: "Inter"
    size: "0.875rem"
    weight: 500
    color: "#C9A962"
    
  price:
    font: "Inter"
    size: "0.875rem"
    color: "rgba(250, 250, 250, 0.6)"
    
  stock_remaining:
    show: true
    format: "{{remaining}} left"
    color: "rgba(250, 250, 250, 0.4)"
    font_size: "0.75rem"
```

### WooCommerce Integration

```php
<?php
/**
 * BLACK ROSE Product Display with Edition Numbers
 * Add to theme functions.php
 */

// Add edition number meta field
function skyyrose_add_edition_meta() {
    add_meta_box(
        'edition_number',
        'BLACK ROSE Edition',
        'skyyrose_edition_meta_callback',
        'product',
        'side',
        'high'
    );
}
add_action('add_meta_boxes', 'skyyrose_add_edition_meta');

function skyyrose_edition_meta_callback($post) {
    $edition_total = get_post_meta($post->ID, '_edition_total', true) ?: 50;
    $edition_sold = get_post_meta($post->ID, '_edition_sold', true) ?: 0;
    
    echo '<p><label>Edition Total: <input type="number" name="edition_total" value="' . esc_attr($edition_total) . '" /></label></p>';
    echo '<p><label>Edition Sold: <input type="number" name="edition_sold" value="' . esc_attr($edition_sold) . '" /></label></p>';
    echo '<p>Next Edition: #' . ($edition_sold + 1) . '/' . $edition_total . '</p>';
}

// Display edition number on product
function skyyrose_display_edition_badge() {
    global $product;
    
    if (!has_term('black-rose', 'product_cat', $product->get_id())) {
        return;
    }
    
    $edition_total = get_post_meta($product->get_id(), '_edition_total', true) ?: 50;
    $edition_sold = get_post_meta($product->get_id(), '_edition_sold', true) ?: 0;
    $next_edition = $edition_sold + 1;
    
    if ($next_edition <= $edition_total) {
        echo '<div class="edition-badge">#' . $next_edition . '/' . $edition_total . '</div>';
    } else {
        echo '<div class="edition-badge sold-out">SOLD OUT</div>';
    }
}
add_action('woocommerce_before_shop_loop_item_title', 'skyyrose_display_edition_badge', 15);

// Low stock badge
function skyyrose_low_stock_badge() {
    global $product;
    
    $stock = $product->get_stock_quantity();
    
    if ($stock !== null && $stock <= 10 && $stock > 0) {
        echo '<span class="low-stock-badge">LOW STOCK</span>';
    }
}
add_action('woocommerce_before_shop_loop_item_title', 'skyyrose_low_stock_badge', 12);
```

### CSS Styles

```css
/* BLACK ROSE Product Grid */
.black-rose-grid {
  background: #0D0D0D;
}

.black-rose-grid .product {
  border: 1px solid rgba(250, 250, 250, 0.1);
  transition: border-color 0.3s ease;
}

.black-rose-grid .product:hover {
  border-color: rgba(201, 169, 98, 0.3);
}

.black-rose-grid .product .woocommerce-loop-product__title {
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  font-weight: 500;
  color: #C9A962;
}

.black-rose-grid .product .price {
  color: rgba(250, 250, 250, 0.6);
}

/* Edition Badge */
.edition-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: #0D0D0D;
  color: #C9A962;
  border: 1px solid rgba(201, 169, 98, 0.3);
  padding: 4px 8px;
  font-size: 0.625rem;
  font-family: 'Inter', sans-serif;
  letter-spacing: 0.05em;
  z-index: 10;
}

/* Low Stock Badge */
.low-stock-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  background: #C9A962;
  color: #0D0D0D;
  padding: 4px 8px;
  font-size: 0.625rem;
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  letter-spacing: 0.05em;
  z-index: 10;
}

/* Sold Out Overlay */
.product.outofstock .woocommerce-loop-product__link::after {
  content: 'SOLD OUT';
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #C9A962;
  font-family: 'Cormorant Garamond', serif;
  font-size: 1rem;
  letter-spacing: 0.2em;
}
```

---

## SECTION 4: THE ARCHIVE (FOMO Section)

### Specification

```yaml
section:
  id: "br_archive"
  name: "The Archive"
  type: "fomo_gallery"
  purpose: "Create urgency by showing sold-out past drops"
  background: "#0A0A0A"
  padding:
    desktop: "100px 24px"
    mobile: "60px 16px"
```

### Content

```yaml
content:
  header:
    title: "THE ARCHIVE"
    subtitle: "Previous BLACK ROSE Drops"
    style:
      title:
        font: "Cormorant Garamond"
        size: "1.5rem"
        color: "rgba(250, 250, 250, 0.4)"
      subtitle:
        font: "Inter"
        size: "0.75rem"
        color: "rgba(250, 250, 250, 0.3)"
        
  archive_grid:
    source: "woocommerce"
    category: "black-rose"
    tag: "archive"
    status: "outofstock"
    columns:
      desktop: 6
      tablet: 4
      mobile: 3
    gap: "8px"
    max_products: 12
    
  overlay:
    apply_to_all: true
    style:
      background: "rgba(0,0,0,0.6)"
      text: "SOLD OUT"
      text_color: "rgba(250, 250, 250, 0.5)"
      
  fomo_message:
    text: "You can't have these anymore.\nBut you can be first for the next."
    font: "Inter"
    size: "0.9375rem"
    style: "italic"
    color: "rgba(250, 250, 250, 0.5)"
    
  cta:
    text: "JOIN EARLY ACCESS LIST"
    url: "#early-access"
    style:
      background: "#C9A962"
      color: "#0D0D0D"
      padding: "16px 40px"
      hover:
        background: "#FAFAFA"
```

### Elementor Configuration

```json
{
  "elementor_widget": "container",
  "settings": {
    "content_width": "full",
    "background_color": "#0A0A0A",
    "padding": {"unit": "px", "top": 100, "right": 24, "bottom": 100, "left": 24}
  },
  "children": [
    {
      "elementor_widget": "container",
      "settings": {
        "content_width": "boxed",
        "boxed_width": {"unit": "px", "size": 1200},
        "flex_direction": "column",
        "flex_align_items": "center"
      },
      "children": [
        {
          "elementor_widget": "heading",
          "settings": {
            "title": "THE ARCHIVE",
            "header_size": "h2",
            "align": "center",
            "typography_font_family": "Cormorant Garamond",
            "typography_font_size": {"unit": "rem", "size": 1.5},
            "title_color": "rgba(250, 250, 250, 0.4)"
          }
        },
        {
          "elementor_widget": "text-editor",
          "settings": {
            "editor": "Previous BLACK ROSE Drops",
            "align": "center",
            "typography_font_size": {"unit": "rem", "size": 0.75},
            "text_color": "rgba(250, 250, 250, 0.3)"
          }
        },
        {
          "elementor_widget": "woocommerce-products",
          "settings": {
            "rows": 2,
            "columns": 6,
            "columns_mobile": 3,
            "query_post_type": "product",
            "query_include": "terms",
            "query_include_term_ids": ["black-rose-archive"],
            "css_classes": "archive-grid sold-out-overlay"
          }
        },
        {
          "elementor_widget": "text-editor",
          "settings": {
            "editor": "<em>You can't have these anymore.<br>But you can be first for the next.</em>",
            "align": "center",
            "typography_font_family": "Inter",
            "typography_font_size": {"unit": "rem", "size": 0.9375},
            "text_color": "rgba(250, 250, 250, 0.5)"
          }
        },
        {
          "elementor_widget": "button",
          "settings": {
            "text": "JOIN EARLY ACCESS LIST",
            "link": {"url": "#early-access"},
            "align": "center",
            "typography_font_size": {"unit": "rem", "size": 0.75},
            "typography_letter_spacing": {"unit": "em", "size": 0.1},
            "button_text_color": "#0D0D0D",
            "background_color": "#C9A962",
            "button_text_color_hover": "#0D0D0D",
            "button_background_hover_color": "#FAFAFA",
            "button_padding": {"unit": "px", "top": 16, "right": 40, "bottom": 16, "left": 40}
          }
        }
      ]
    }
  ]
}
```

---

## SECTION 5: EXCLUSIVE NEWSLETTER

### Specification

```yaml
section:
  id: "br_newsletter"
  name: "Inner Circle Newsletter"
  type: "email_capture"
  anchor: "early-access"
  background:
    type: "gradient"
    value: "linear-gradient(180deg, #1A1A1A 0%, #0D0D0D 100%)"
  border_top: "1px solid rgba(201, 169, 98, 0.1)"
  padding:
    desktop: "100px 24px"
    mobile: "60px 24px"
```

### Content

```yaml
content:
  headline:
    text: "THE INNER CIRCLE"
    font: "Cormorant Garamond"
    size: "clamp(1.5rem, 4vw, 2rem)"
    color: "#C9A962"
    
  subheadline:
    text: "BLACK ROSE drops announce to members first.\nOften, they sell out before going public."
    font: "Inter"
    size: "0.9375rem"
    line_height: "1.7"
    color: "rgba(250, 250, 250, 0.6)"
    
  form:
    provider: "klaviyo"
    list_id: "{{KLAVIYO_BLACK_ROSE_LIST}}"
    fields:
      - type: "email"
        placeholder: "Email Address"
        required: true
    button:
      text: "REQUEST ACCESS"
      style:
        background: "#C9A962"
        color: "#0D0D0D"
        hover:
          background: "#FAFAFA"
    success_message: "You're on the list. We'll be in touch."
    
  note:
    text: "We'll notify you 24 hours before the next drop."
    font_size: "0.75rem"
    color: "rgba(250, 250, 250, 0.4)"
```

### Klaviyo Segment

```yaml
klaviyo_segment:
  name: "BLACK ROSE Early Access"
  list_id: "{{KLAVIYO_BLACK_ROSE_LIST}}"
  
  triggers:
    - event: "signup"
      flow: "black_rose_welcome"
      
    - event: "new_drop"
      flow: "black_rose_drop_notification"
      timing: "24h_before_public"
      
  properties:
    collection: "black_rose"
    tier: "early_access"
    signup_source: "collection_page"
```

---

## FULL PAGE ASSEMBLY

### Section Order

```yaml
page_sections:
  - section_id: "br_hero"
    order: 1
    visible: true
    
  - section_id: "br_philosophy"
    order: 2
    visible: true
    
  - section_id: "br_current_drop"
    order: 3
    visible: true
    anchor: "current-drop"
    
  - section_id: "br_archive"
    order: 4
    visible: true
    
  - section_id: "br_newsletter"
    order: 5
    visible: true
    anchor: "early-access"
```

### Agent Execution Checklist

```yaml
execution_checklist:
  phase_1_setup:
    - task: "Create 'black-rose' WooCommerce category"
      status: "pending"
      
    - task: "Create 'current-drop' and 'archive' product tags"
      status: "pending"
      
    - task: "Set up edition number custom fields"
      status: "pending"
      
  phase_2_content:
    - task: "Create hero video (15-20s, dark studio, rose petals)"
      specs:
        duration: "15-20s"
        style: "Slow-motion, cinematic 24fps"
        lighting: "Single dramatic light source"
        subject: "Model in BLACK ROSE pieces"
        elements: "Rose petals falling"
      status: "pending"
      
    - task: "Create philosophy detail image"
      specs:
        type: "Extreme close-up"
        subject: "Fabric texture, stitching detail"
        size: "1200x800px"
      status: "pending"
      
    - task: "Upload products with edition metadata"
      status: "pending"
      
  phase_3_build:
    - task: "Build Section 1: Cinematic Hero"
      status: "pending"
      
    - task: "Build Section 2: Philosophy"
      status: "pending"
      
    - task: "Build Section 3: Current Drop Grid"
      status: "pending"
      
    - task: "Build Section 4: Archive"
      status: "pending"
      
    - task: "Build Section 5: Newsletter"
      status: "pending"
      
  phase_4_integration:
    - task: "Set up Klaviyo BLACK ROSE list"
      status: "pending"
      
    - task: "Create drop notification flow"
      status: "pending"
      
    - task: "Test edition number display"
      status: "pending"
```

---

*End of BLACK ROSE Collection Specification*
