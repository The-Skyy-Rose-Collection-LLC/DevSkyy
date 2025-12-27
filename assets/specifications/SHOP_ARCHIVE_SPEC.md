# SKYYROSE SHOP ARCHIVE PAGE SPECIFICATION

# Version: 1.0.0

# Last Updated: 2024-12-11

# Platform: WordPress + WooCommerce + Elementor Pro

---

## PAGE METADATA

```yaml
page:
  name: "Shop / All Products"
  slug: "/shop/"
  template: "elementor_header_footer"
  type: "archive"

  seo:
    title: "Shop All | SkyyRose Luxury Streetwear"
    description: "Shop all SkyyRose collections. Premium luxury streetwear from Oakland. BLACK ROSE limited editions, LOVE HURTS emotional pieces, and SIGNATURE essentials."
    keywords: ["shop streetwear", "luxury clothing", "premium hoodies", "designer joggers"]

  og:
    image: "/assets/images/og-shop.jpg"
    type: "website"
```

---

## PAGE STRUCTURE

```yaml
page_structure:
  sections:
    - id: "shop_header"
      order: 1

    - id: "filter_bar"
      order: 2
      sticky: true

    - id: "product_grid"
      order: 3

    - id: "load_more"
      order: 4
```

---

## SECTION 1: SHOP HEADER

### Specification

```yaml
section:
  id: "shop_header"
  type: "page_header"
  background: "#0D0D0D"
  padding:
    desktop: "80px 24px"
    mobile: "48px 16px"
```

### Content

```yaml
content:
  headline:
    text: "THE SHOP"
    font: "Cormorant Garamond"
    size: "clamp(2rem, 6vw, 3rem)"
    weight: 400
    letter_spacing: "0.15em"
    color: "#FAFAFA"

  subheadline:
    text: "All Collections"
    font: "Inter"
    size: "0.875rem"
    letter_spacing: "0.1em"
    color: "rgba(250, 250, 250, 0.6)"
```

### Elementor Configuration

```json
{
  "elementor_widget": "container",
  "settings": {
    "content_width": "full",
    "background_color": "#0D0D0D",
    "padding": {"unit": "px", "top": 80, "right": 24, "bottom": 80, "left": 24},
    "padding_mobile": {"unit": "px", "top": 48, "right": 16, "bottom": 48, "left": 16},
    "flex_direction": "column",
    "flex_align_items": "center"
  },
  "children": [
    {
      "elementor_widget": "heading",
      "settings": {
        "title": "THE SHOP",
        "header_size": "h1",
        "align": "center",
        "typography_font_family": "Cormorant Garamond",
        "typography_font_size": {"unit": "rem", "size": 3},
        "typography_letter_spacing": {"unit": "em", "size": 0.15},
        "title_color": "#FAFAFA"
      }
    },
    {
      "elementor_widget": "text-editor",
      "settings": {
        "editor": "All Collections",
        "align": "center",
        "typography_font_family": "Inter",
        "typography_font_size": {"unit": "rem", "size": 0.875},
        "typography_letter_spacing": {"unit": "em", "size": 0.1},
        "text_color": "rgba(250, 250, 250, 0.6)"
      }
    }
  ]
}
```

---

## SECTION 2: FILTER BAR

### Specification

```yaml
section:
  id: "filter_bar"
  type: "sticky_filter"
  background: "#FFFFFF"
  border_bottom: "1px solid rgba(0,0,0,0.1)"
  padding: "16px 24px"
  sticky:
    enable: true
    offset: "header_height"
    z_index: 50
```

### Content

```yaml
filters:
  layout:
    desktop: "row"
    mobile: "collapsible"

  collection_filter:
    type: "pill_buttons"
    position: "left"
    options:
      - label: "All"
        value: "*"
        active_default: true
      - label: "BLACK ROSE"
        value: "black-rose"
        accent_color: "#C9A962"
      - label: "LOVE HURTS"
        value: "love-hurts"
        accent_color: "#8B3A3A"
      - label: "SIGNATURE"
        value: "signature"
        accent_color: "#6B6B6B"
    style:
      active:
        background: "#0D0D0D"
        color: "#FAFAFA"
      inactive:
        background: "transparent"
        border: "1px solid rgba(0,0,0,0.15)"
        color: "#4A4A4A"
      hover:
        border_color: "#0D0D0D"

  dropdowns:
    position: "right"
    items:
      - id: "size_filter"
        label: "Size"
        type: "multi_select"
        options: ["XS", "S", "M", "L", "XL", "XXL", "3XL"]

      - id: "color_filter"
        label: "Color"
        type: "multi_select"
        options: ["Black", "White", "Grey", "Cream", "Navy", "Burgundy"]

      - id: "sort"
        label: "Sort"
        type: "single_select"
        default: "Featured"
        options:
          - label: "Featured"
            value: "menu_order"
          - label: "Newest"
            value: "date"
          - label: "Price: Low to High"
            value: "price"
          - label: "Price: High to Low"
            value: "price-desc"

  mobile_toggle:
    text: "Filter & Sort"
    icon: "filter"
```

### CSS Styles

```css
/* Filter Bar */
.filter-bar {
  background: #FFFFFF;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  padding: 16px 24px;
  position: sticky;
  top: var(--header-height, 80px);
  z-index: 50;
  transition: box-shadow 0.3s ease;
}

.filter-bar.scrolled {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.filter-bar__inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
  gap: 16px;
}

/* Collection Pills */
.collection-pills {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.collection-pill {
  padding: 8px 20px;
  font-size: 0.75rem;
  font-family: 'Inter', sans-serif;
  letter-spacing: 0.05em;
  border-radius: 0;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid rgba(0, 0, 0, 0.15);
  background: transparent;
  color: #4A4A4A;
}

.collection-pill.active {
  background: #0D0D0D;
  color: #FAFAFA;
  border-color: #0D0D0D;
}

.collection-pill:hover:not(.active) {
  border-color: #0D0D0D;
}

/* Filter Dropdowns */
.filter-dropdowns {
  display: flex;
  gap: 8px;
}

.filter-dropdown {
  position: relative;
}

.filter-dropdown__trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 0.75rem;
  font-family: 'Inter', sans-serif;
  background: transparent;
  border: 1px solid rgba(0, 0, 0, 0.15);
  cursor: pointer;
}

.filter-dropdown__trigger::after {
  content: '▼';
  font-size: 0.5rem;
}

/* Mobile Filter Toggle */
.mobile-filter-toggle {
  display: none;
  padding: 12px 20px;
  font-size: 0.75rem;
  background: #0D0D0D;
  color: #FAFAFA;
  border: none;
  width: 100%;
}

@media (max-width: 768px) {
  .collection-pills,
  .filter-dropdowns {
    display: none;
  }

  .mobile-filter-toggle {
    display: block;
  }

  .filter-bar.expanded .collection-pills,
  .filter-bar.expanded .filter-dropdowns {
    display: flex;
    flex-direction: column;
    width: 100%;
    margin-top: 16px;
  }

  .filter-bar.expanded .collection-pills {
    flex-direction: row;
    flex-wrap: wrap;
  }
}
```

---

## SECTION 3: PRODUCT GRID WITH EDITORIAL CARDS

### Specification

```yaml
section:
  id: "product_grid"
  type: "mixed_content_grid"
  background: "#F5F3EF"
  padding:
    desktop: "40px 24px"
    mobile: "24px 16px"
```

### Content

```yaml
grid:
  source: "woocommerce"
  columns:
    desktop: 4
    tablet: 3
    mobile: 2
  gap: "16px"

  products_per_page: 16

  editorial_cards:
    enabled: true
    insert_positions: [4, 12, 20]
    cards:
      - type: "collection_promo"
        collection: "black-rose"
        background: "linear-gradient(135deg, #0D0D0D 0%, #1A1A1A 100%)"
        headline: "BLACK ROSE"
        subline: "Limited Edition Collection"
        accent_color: "#C9A962"
        cta: "EXPLORE"
        url: "/collection/black-rose/"

      - type: "collection_promo"
        collection: "love-hurts"
        background: "linear-gradient(135deg, #8B3A3A 0%, #5C2828 100%)"
        headline: "LOVE HURTS"
        subline: "Wear Your Heart"
        cta: "SHOP NOW"
        url: "/collection/love-hurts/"

      - type: "value_prop"
        background: "#0D0D0D"
        headline: "Free Shipping"
        subline: "On orders over $150"
        icon: "🚚"

  product_card:
    aspect_ratio: "3:4"
    background: "#FFFFFF"
    border: "1px solid rgba(0,0,0,0.05)"
    hover:
      border_color: "#0D0D0D"
      shadow: "0 8px 24px rgba(0,0,0,0.08)"
      image_effect: "secondary_image"

    badges:
      new:
        text: "NEW"
        background: "#0D0D0D"
        color: "#FAFAFA"
        position: "top-left"
      low_stock:
        text: "LOW STOCK"
        background: "#DC2626"
        color: "#FAFAFA"
        position: "top-left"
        threshold: 10
      sold_out:
        text: "SOLD OUT"
        overlay: true
        overlay_opacity: 0.6

    quick_view:
      enabled: true
      trigger: "hover_icon"
      position: "bottom-center"

    wishlist:
      enabled: true
      position: "top-right"
      icon: "heart"
```

### WooCommerce Product Card Structure

```yaml
product_card_html:
  structure: |
    <div class="product-card" data-product-id="{{id}}">
      <div class="product-card__image">
        {{#if badges}}
          <div class="product-card__badges">
            {{#each badges}}
              <span class="badge badge--{{type}}">{{text}}</span>
            {{/each}}
          </div>
        {{/if}}

        <a href="{{url}}">
          <img src="{{image}}" alt="{{title}}" class="product-card__img--primary" />
          {{#if secondary_image}}
            <img src="{{secondary_image}}" alt="{{title}}" class="product-card__img--secondary" />
          {{/if}}
        </a>

        <button class="product-card__wishlist" aria-label="Add to wishlist">
          <span class="heart-icon">♡</span>
        </button>

        <button class="product-card__quickview" aria-label="Quick view">
          Quick View
        </button>
      </div>

      <div class="product-card__info">
        <h3 class="product-card__title">
          <a href="{{url}}">{{title}}</a>
        </h3>
        <div class="product-card__meta">
          <span class="product-card__price">{{price}}</span>
          {{#if color_swatches}}
            <div class="product-card__swatches">
              {{#each color_swatches}}
                <span class="swatch" style="background-color: {{color}}" title="{{name}}"></span>
              {{/each}}
            </div>
          {{/if}}
        </div>
      </div>
    </div>
```

### CSS Styles

```css
/* Product Grid */
.product-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  max-width: 1200px;
  margin: 0 auto;
}

@media (max-width: 1024px) {
  .product-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .product-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Product Card */
.product-card {
  background: #FFFFFF;
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.product-card:hover {
  border-color: #0D0D0D;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.product-card__image {
  position: relative;
  aspect-ratio: 3 / 4;
  overflow: hidden;
  background: #F5F3EF;
}

.product-card__img--primary,
.product-card__img--secondary {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: opacity 0.3s ease;
}

.product-card__img--secondary {
  opacity: 0;
}

.product-card:hover .product-card__img--primary {
  opacity: 0;
}

.product-card:hover .product-card__img--secondary {
  opacity: 1;
}

/* Badges */
.product-card__badges {
  position: absolute;
  top: 8px;
  left: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 10;
}

.badge {
  padding: 4px 8px;
  font-size: 0.625rem;
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  letter-spacing: 0.05em;
}

.badge--new {
  background: #0D0D0D;
  color: #FAFAFA;
}

.badge--low-stock {
  background: #DC2626;
  color: #FAFAFA;
}

/* Wishlist */
.product-card__wishlist {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 32px;
  height: 32px;
  background: #FFFFFF;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: 10;
}

.product-card:hover .product-card__wishlist {
  opacity: 1;
}

.product-card__wishlist.active .heart-icon {
  color: #DC2626;
}

/* Quick View */
.product-card__quickview {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%) translateY(20px);
  padding: 10px 20px;
  background: #FFFFFF;
  border: none;
  font-size: 0.75rem;
  font-family: 'Inter', sans-serif;
  letter-spacing: 0.05em;
  cursor: pointer;
  opacity: 0;
  transition: all 0.3s ease;
  z-index: 10;
}

.product-card:hover .product-card__quickview {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

/* Product Info */
.product-card__info {
  padding: 16px;
}

.product-card__title {
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  font-weight: 500;
  color: #0D0D0D;
  margin: 0 0 8px;
}

.product-card__title a {
  color: inherit;
  text-decoration: none;
}

.product-card__meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-card__price {
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  color: #6B6B6B;
}

.product-card__swatches {
  display: flex;
  gap: 4px;
}

.swatch {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

/* Editorial Card */
.editorial-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 32px;
  aspect-ratio: 3 / 4;
}

.editorial-card__headline {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.25rem;
  color: #FAFAFA;
  margin-bottom: 8px;
}

.editorial-card__subline {
  font-family: 'Inter', sans-serif;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 16px;
}

.editorial-card__cta {
  padding: 10px 24px;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.5);
  color: #FAFAFA;
  font-size: 0.75rem;
  font-family: 'Inter', sans-serif;
  letter-spacing: 0.1em;
  cursor: pointer;
  transition: all 0.3s ease;
}

.editorial-card__cta:hover {
  background: #FAFAFA;
  color: #0D0D0D;
}
```

---

## SECTION 4: LOAD MORE / PAGINATION

### Specification

```yaml
section:
  id: "load_more"
  type: "pagination"
  background: "#F5F3EF"
  padding: "40px 24px 80px"
```

### Content

```yaml
pagination:
  type: "load_more"
  button:
    text: "LOAD MORE PRODUCTS"
    loading_text: "LOADING..."
    style:
      background: "transparent"
      border: "1px solid #0D0D0D"
      color: "#0D0D0D"
      padding: "16px 48px"
      font_size: "0.75rem"
      letter_spacing: "0.1em"
    hover:
      background: "#0D0D0D"
      color: "#FAFAFA"

  counter:
    show: true
    format: "Showing {{displayed}} of {{total}} products"
    font: "Inter"
    size: "0.75rem"
    color: "#6B6B6B"
```

---

## FULL PAGE ASSEMBLY

```yaml
page_sections:
  - section_id: "shop_header"
    order: 1
    visible: true

  - section_id: "filter_bar"
    order: 2
    visible: true
    sticky: true

  - section_id: "product_grid"
    order: 3
    visible: true

  - section_id: "load_more"
    order: 4
    visible: true
```

---

## AGENT EXECUTION CHECKLIST

```yaml
execution_checklist:
  phase_1_setup:
    - task: "Create Shop page in WordPress"
      status: "pending"

    - task: "Configure WooCommerce shop settings"
      status: "pending"

  phase_2_build:
    - task: "Build shop header section"
      status: "pending"

    - task: "Build filter bar with AJAX functionality"
      status: "pending"

    - task: "Build product grid with editorial cards"
      status: "pending"

    - task: "Implement load more pagination"
      status: "pending"

  phase_3_functionality:
    - task: "Implement AJAX filtering"
      status: "pending"

    - task: "Add quick view modal"
      status: "pending"

    - task: "Add wishlist functionality"
      status: "pending"
```

---

*End of Shop Archive Specification*
