# SKYYROSE PRODUCT PAGE (PDP) SPECIFICATION

# Version: 1.0.0

# Last Updated: 2024-12-11

# Platform: WordPress + WooCommerce + Elementor Pro Theme Builder

---

## PAGE METADATA

```yaml
page:
  name: "Single Product Template"
  type: "theme_builder_template"
  template_type: "single_product"
  applies_to: "all_products"

  seo:
    title_format: "{{product.name}} | SkyyRose"
    description_format: "Shop {{product.name}} from {{product.collection}}. {{product.short_description}} Free shipping over $150."

  schema_type: "Product"

  conversion_elements:
    - "star_rating_above_fold"
    - "free_shipping_badge"
    - "trust_badges"
    - "size_guide_link"
    - "sticky_mobile_cta"
```

---

## PAGE STRUCTURE

```yaml
page_structure:
  sections:
    - id: "breadcrumbs"
      order: 1

    - id: "product_hero"
      order: 2

    - id: "product_tabs"
      order: 3

    - id: "related_products"
      order: 4

    - id: "ugc_section"
      order: 5

    - id: "mobile_sticky_cta"
      order: 6
      mobile_only: true
```

---

## SECTION 1: BREADCRUMBS

### Specification

```yaml
section:
  id: "breadcrumbs"
  type: "navigation_breadcrumbs"
  background: "#F5F3EF"
  padding: "12px 24px"
```

### Content

```yaml
content:
  format: "Home / {{collection}} / {{product.name}}"
  separator: " / "

  style:
    font: "Inter"
    size: "0.75rem"
    color: "#6B6B6B"
    link_color: "#6B6B6B"
    link_hover: "#0D0D0D"
    current_color: "#0D0D0D"
```

### Elementor Configuration

```json
{
  "elementor_widget": "container",
  "settings": {
    "content_width": "boxed",
    "background_color": "#F5F3EF",
    "padding": {"unit": "px", "top": 12, "right": 24, "bottom": 12, "left": 24}
  },
  "children": [
    {
      "elementor_widget": "woocommerce-breadcrumb",
      "settings": {
        "typography_font_family": "Inter",
        "typography_font_size": {"unit": "rem", "size": 0.75},
        "text_color": "#6B6B6B",
        "link_color": "#6B6B6B",
        "link_hover_color": "#0D0D0D"
      }
    }
  ]
}
```

---

## SECTION 2: PRODUCT HERO

### Specification

```yaml
section:
  id: "product_hero"
  type: "split_product_display"
  background: "#FFFFFF"
  padding:
    desktop: "0"
    mobile: "0"
  layout:
    desktop: "60% gallery / 40% info"
    mobile: "stacked (gallery first)"
```

### Left Column: Image Gallery

```yaml
image_gallery:
  layout:
    desktop: "main_image_with_thumbnails"
    mobile: "swipeable_carousel"

  main_image:
    aspect_ratio: "1:1"
    background: "#F5F3EF"
    zoom_on_hover: true
    lightbox_on_click: true

  thumbnails:
    position: "below"
    count: 5
    active_indicator: "border"
    gap: "8px"

  badges:
    edition_badge:
      position: "top-left"
      show_for: "black-rose"
      format: "#{{edition}}/50"
      style:
        background: "#0D0D0D"
        color: "#C9A962"
        border: "1px solid rgba(201, 169, 98, 0.3)"

    new_badge:
      position: "top-left"
      show_for: "new_products"
      text: "NEW"
      style:
        background: "#0D0D0D"
        color: "#FAFAFA"

    sale_badge:
      position: "top-left"
      show_for: "on_sale"
      text: "SALE"
      style:
        background: "#DC2626"
        color: "#FAFAFA"
```

### Right Column: Product Info

```yaml
product_info:
  padding:
    desktop: "40px 48px"
    mobile: "24px 16px"

  elements:
    - type: "collection_label"
      order: 1
      config:
        font: "Inter"
        size: "0.75rem"
        letter_spacing: "0.1em"
        color: "#6B6B6B"
        text_transform: "uppercase"

    - type: "product_title"
      order: 2
      config:
        font: "Cormorant Garamond"
        size: "clamp(1.5rem, 4vw, 2rem)"
        weight: 400
        color: "#0D0D0D"

    - type: "rating_stars"
      order: 3
      config:
        star_color: "#F59E0B"
        show_count: true
        count_format: "({{count}} reviews)"
        count_color: "#6B6B6B"
        link_to_reviews: true

    - type: "price"
      order: 4
      config:
        font: "Inter"
        size: "1.5rem"
        weight: 600
        color: "#0D0D0D"
        sale_price_color: "#DC2626"
        original_price_style: "line-through"
        original_price_color: "#6B6B6B"

    - type: "shipping_badge"
      order: 5
      config:
        text: "✓ Free shipping over $150"
        color: "#059669"
        font_size: "0.875rem"

    - type: "divider"
      order: 6
      config:
        color: "rgba(0,0,0,0.1)"
        margin: "24px 0"

    - type: "size_selector"
      order: 7
      config:
        label: "Size"
        label_font: "Inter"
        label_size: "0.875rem"
        size_guide_link: true
        size_guide_text: "Size Guide"
        buttons:
          style: "bordered"
          selected:
            background: "#0D0D0D"
            color: "#FAFAFA"
          default:
            background: "transparent"
            border: "1px solid rgba(0,0,0,0.2)"
          hover:
            border_color: "#0D0D0D"
          out_of_stock:
            opacity: 0.3
            strikethrough: true
        gap: "8px"

    - type: "color_selector"
      order: 8
      config:
        label: "Color"
        label_with_value: "Color: {{selected}}"
        swatches:
          size: "32px"
          border_radius: "50%"
          selected_indicator: "ring"
          ring_color: "#0D0D0D"
          ring_offset: "2px"
        gap: "8px"

    - type: "add_to_cart"
      order: 9
      config:
        text: "ADD TO BAG"
        text_with_price: "ADD TO BAG — ${{price}}"
        style:
          background: "#0D0D0D"
          color: "#FAFAFA"
          padding: "18px 0"
          width: "100%"
          font_size: "0.875rem"
          letter_spacing: "0.1em"
          font_weight: 500
        hover:
          background: "#4A4A4A"
        loading:
          text: "ADDING..."
        success:
          text: "ADDED ✓"
          background: "#059669"

    - type: "wishlist_button"
      order: 10
      config:
        text: "♡ Add to Wishlist"
        style:
          background: "transparent"
          border: "1px solid rgba(0,0,0,0.2)"
          color: "#6B6B6B"
          padding: "14px 0"
          width: "100%"
        active:
          text: "♥ In Wishlist"
          color: "#DC2626"

    - type: "divider"
      order: 11
      config:
        color: "rgba(0,0,0,0.1)"
        margin: "24px 0"

    - type: "trust_badges"
      order: 12
      config:
        layout: "3_column"
        badges:
          - icon: "🚚"
            text: "Free Shipping"
            subtext: "Over $150"
          - icon: "↩️"
            text: "100-Day Returns"
            subtext: "No questions"
          - icon: "🔒"
            text: "Secure Checkout"
            subtext: "SSL encrypted"
        style:
          icon_size: "1.5rem"
          text_font: "Inter"
          text_size: "0.75rem"
          text_color: "#6B6B6B"
```

### Elementor Configuration

```json
{
  "elementor_widget": "container",
  "settings": {
    "content_width": "full",
    "background_color": "#FFFFFF"
  },
  "children": [
    {
      "elementor_widget": "container",
      "settings": {
        "content_width": "boxed",
        "boxed_width": {"unit": "px", "size": 1400},
        "flex_direction": "row",
        "flex_direction_mobile": "column"
      },
      "children": [
        {
          "elementor_widget": "container",
          "settings": {
            "_element_width": "60%",
            "_element_width_mobile": "100%",
            "padding": {"unit": "px", "top": 24, "right": 24, "bottom": 24, "left": 24}
          },
          "children": [
            {
              "elementor_widget": "woocommerce-product-images",
              "settings": {
                "sale_flash": "yes",
                "image_size": "full"
              }
            }
          ]
        },
        {
          "elementor_widget": "container",
          "settings": {
            "_element_width": "40%",
            "_element_width_mobile": "100%",
            "padding": {"unit": "px", "top": 40, "right": 48, "bottom": 40, "left": 48},
            "padding_mobile": {"unit": "px", "top": 24, "right": 16, "bottom": 24, "left": 16},
            "border_border": "solid",
            "border_width": {"unit": "px", "top": 0, "right": 0, "bottom": 0, "left": 1},
            "border_color": "rgba(0,0,0,0.1)"
          },
          "children": [
            {
              "elementor_widget": "shortcode",
              "settings": {
                "shortcode": "[skyyrose_collection_label]"
              }
            },
            {
              "elementor_widget": "woocommerce-product-title",
              "settings": {
                "header_size": "h1",
                "typography_font_family": "Cormorant Garamond",
                "typography_font_size": {"unit": "rem", "size": 2},
                "title_color": "#0D0D0D"
              }
            },
            {
              "elementor_widget": "woocommerce-product-rating",
              "settings": {
                "star_color": "#F59E0B",
                "link_color": "#6B6B6B"
              }
            },
            {
              "elementor_widget": "woocommerce-product-price",
              "settings": {
                "typography_font_family": "Inter",
                "typography_font_size": {"unit": "rem", "size": 1.5},
                "typography_font_weight": "600",
                "price_color": "#0D0D0D"
              }
            },
            {
              "elementor_widget": "text-editor",
              "settings": {
                "editor": "✓ Free shipping over $150",
                "typography_font_size": {"unit": "rem", "size": 0.875},
                "text_color": "#059669"
              }
            },
            {
              "elementor_widget": "divider",
              "settings": {
                "color": "rgba(0,0,0,0.1)"
              }
            },
            {
              "elementor_widget": "woocommerce-product-add-to-cart",
              "settings": {
                "button_text_color": "#FAFAFA",
                "button_background_color": "#0D0D0D",
                "button_text_color_hover": "#FAFAFA",
                "button_background_hover_color": "#4A4A4A",
                "typography_font_size": {"unit": "rem", "size": 0.875},
                "typography_letter_spacing": {"unit": "em", "size": 0.1}
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

## SECTION 3: PRODUCT TABS

### Specification

```yaml
section:
  id: "product_tabs"
  type: "tabbed_content"
  background: "#FFFFFF"
  padding:
    desktop: "40px 24px 80px"
    mobile: "24px 16px 48px"
```

### Content

```yaml
tabs:
  style: "underline"
  active_indicator: "border-bottom"

  items:
    - id: "description"
      label: "Description"
      content_source: "product.description"

    - id: "size_guide"
      label: "Size Guide"
      content_source: "custom"
      custom_content:
        type: "size_chart"
        measurements: ["Chest", "Length", "Sleeve"]
        sizes: ["XS", "S", "M", "L", "XL", "XXL", "3XL"]

    - id: "reviews"
      label: "Reviews ({{count}})"
      content_source: "woocommerce_reviews"
      review_style:
        show_images: true
        show_verified_badge: true
        pagination: true

  tab_style:
    font: "Inter"
    size: "0.875rem"
    weight: 500
    inactive_color: "#6B6B6B"
    active_color: "#0D0D0D"
    border_active: "2px solid #0D0D0D"
    gap: "32px"
```

### Size Guide Table

```yaml
size_guide_config:
  measurement_unit: "inches"
  toggle_to_cm: true

  data:
    tops:
      - size: "XS"
        chest: "34-36"
        length: "26"
        sleeve: "32"
      - size: "S"
        chest: "36-38"
        length: "27"
        sleeve: "33"
      - size: "M"
        chest: "38-40"
        length: "28"
        sleeve: "34"
      - size: "L"
        chest: "40-42"
        length: "29"
        sleeve: "35"
      - size: "XL"
        chest: "42-44"
        length: "30"
        sleeve: "36"
      - size: "XXL"
        chest: "44-46"
        length: "31"
        sleeve: "37"
      - size: "3XL"
        chest: "46-48"
        length: "32"
        sleeve: "38"

  fit_note: "Our pieces are designed for a relaxed, comfortable fit. If you prefer a more fitted look, we recommend sizing down."
```

---

## SECTION 4: RELATED PRODUCTS

### Specification

```yaml
section:
  id: "related_products"
  type: "product_carousel"
  background: "#F5F3EF"
  padding:
    desktop: "80px 24px"
    mobile: "48px 16px"
```

### Content

```yaml
content:
  headline:
    text: "YOU MAY ALSO LIKE"
    font: "Cormorant Garamond"
    size: "clamp(1.25rem, 3vw, 1.5rem)"
    color: "#0D0D0D"

  products:
    source: "related"
    fallback: "same_collection"
    count: 4
    columns:
      desktop: 4
      tablet: 3
      mobile: 2

  carousel:
    enable_mobile: true
    show_navigation: false
    show_pagination: true
```

---

## SECTION 5: UGC SECTION

### Specification

```yaml
section:
  id: "product_ugc"
  type: "ugc_gallery"
  background: "#FFFFFF"
  padding:
    desktop: "80px 24px"
    mobile: "48px 16px"
```

### Content

```yaml
content:
  headline:
    text: "WORN BY THE COMMUNITY"
    font: "Cormorant Garamond"
    size: "clamp(1.25rem, 3vw, 1.5rem)"
    color: "#0D0D0D"

  gallery:
    source: "product_tagged_ugc"
    fallback: "collection_ugc"
    columns:
      desktop: 6
      tablet: 4
      mobile: 3
    max_images: 6
    aspect_ratio: "1:1"
    gap: "8px"

  cta:
    text: "Tag us @skyyrose to be featured"
    color: "#6B6B6B"
```

---

## SECTION 6: MOBILE STICKY CTA

### Specification

```yaml
section:
  id: "mobile_sticky_cta"
  type: "sticky_bottom_bar"
  visibility: "mobile_only"
  trigger: "scroll_past_add_to_cart"
  background: "#FFFFFF"
  border_top: "1px solid rgba(0,0,0,0.1)"
  box_shadow: "0 -4px 12px rgba(0,0,0,0.1)"
  padding: "12px 16px"
  z_index: 100
```

### Content

```yaml
content:
  layout: "flex_row"

  elements:
    - type: "product_info"
      width: "flex-1"
      config:
        title:
          max_chars: 20
          truncate: "..."
          font: "Inter"
          size: "0.75rem"
          color: "#6B6B6B"
        price:
          font: "Inter"
          size: "1rem"
          weight: 600
          color: "#0D0D0D"

    - type: "add_to_cart_button"
      width: "auto"
      config:
        text: "ADD TO BAG"
        style:
          background: "#0D0D0D"
          color: "#FAFAFA"
          padding: "14px 24px"
          font_size: "0.75rem"
          letter_spacing: "0.1em"
```

### CSS Implementation

```css
/* Mobile Sticky CTA */
.mobile-sticky-cta {
  display: none;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #FFFFFF;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.1);
  padding: 12px 16px;
  z-index: 100;
  transform: translateY(100%);
  transition: transform 0.3s ease;
}

.mobile-sticky-cta.visible {
  transform: translateY(0);
}

@media (max-width: 768px) {
  .mobile-sticky-cta {
    display: flex;
    align-items: center;
    gap: 16px;
  }
}

.mobile-sticky-cta .product-info {
  flex: 1;
}

.mobile-sticky-cta .product-title {
  font-size: 0.75rem;
  color: #6B6B6B;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mobile-sticky-cta .product-price {
  font-size: 1rem;
  font-weight: 600;
  color: #0D0D0D;
}

.mobile-sticky-cta .add-to-bag {
  background: #0D0D0D;
  color: #FAFAFA;
  padding: 14px 24px;
  font-size: 0.75rem;
  letter-spacing: 0.1em;
  border: none;
  white-space: nowrap;
}
```

### JavaScript Implementation

```javascript
// Mobile Sticky CTA Trigger
document.addEventListener('DOMContentLoaded', function() {
  const addToCartButton = document.querySelector('.single_add_to_cart_button');
  const stickyBar = document.querySelector('.mobile-sticky-cta');

  if (!addToCartButton || !stickyBar) return;

  const observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        stickyBar.classList.remove('visible');
      } else {
        stickyBar.classList.add('visible');
      }
    },
    { threshold: 0, rootMargin: '-100px 0px 0px 0px' }
  );

  observer.observe(addToCartButton);
});
```

---

## COLLECTION-SPECIFIC VARIATIONS

### BLACK ROSE Products

```yaml
black_rose_variations:
  badges:
    edition_badge:
      show: true
      format: "#{{edition}}/50"

  stock_display:
    show_remaining: true
    format: "Only {{remaining}} left"
    threshold: 10

  urgency_messaging:
    enabled: true
    messages:
      - condition: "stock < 5"
        text: "Almost gone"
        color: "#DC2626"
      - condition: "stock < 10"
        text: "Low stock"
        color: "#D97706"
```

### LOVE HURTS Products

```yaml
love_hurts_variations:
  color_scheme:
    accent_color: "#8B3A3A"

  add_to_cart:
    hover_color: "#5C2828"
```

### SIGNATURE Products

```yaml
signature_variations:
  bundles:
    show_bundle_upsell: true
    upsell_position: "below_add_to_cart"
    message: "Complete the look with The Starter Bundle and save 20%"
```

---

## AGENT EXECUTION CHECKLIST

```yaml
execution_checklist:
  phase_1_setup:
    - task: "Create Theme Builder Single Product template"
      status: "pending"

    - task: "Install required widgets: YITH Wishlist, variation swatches"
      status: "pending"

  phase_2_build:
    - task: "Build breadcrumbs section"
      status: "pending"

    - task: "Build product hero (gallery + info)"
      status: "pending"

    - task: "Build product tabs"
      status: "pending"

    - task: "Build related products section"
      status: "pending"

    - task: "Build UGC section"
      status: "pending"

    - task: "Build mobile sticky CTA"
      status: "pending"

  phase_3_customize:
    - task: "Add collection-specific CSS classes"
      status: "pending"

    - task: "Implement edition badge for BLACK ROSE"
      status: "pending"

    - task: "Add size guide modal"
      status: "pending"

  phase_4_test:
    - task: "Test on all device sizes"
      status: "pending"

    - task: "Test add to cart functionality"
      status: "pending"

    - task: "Test variation selectors"
      status: "pending"
```

---

*End of Product Page Specification*
