# SKYYROSE SIGNATURE COLLECTION PAGE SPECIFICATION

# Version: 1.0.0

# Last Updated: 2024-12-11

# Platform: WordPress + WooCommerce + Elementor Pro

---

## PAGE METADATA

```yaml
page:
  name: "SIGNATURE Collection"
  slug: "/collection/signature/"
  template: "elementor_header_footer"
  collection_id: "signature"
  woocommerce_category: "signature"

  seo:
    title: "SIGNATURE | Premium Essentials Built to Last | SkyyRose"
    description: "SIGNATURE - elevated essentials for your everyday wardrobe. Premium Pima cotton, reinforced construction, inclusive sizing. The foundation of luxury streetwear."
    keywords: ["premium basics", "luxury essentials", "quality streetwear", "elevated basics", "wardrobe staples"]

  og:
    image: "/assets/images/og-signature.jpg"
    type: "product.group"

  brand_essence:
    mood: "Clean, minimal, confident, timeless"
    tagline: "The Foundation. Built to Last."
    voice: "Assured, quality-focused, unpretentious"
    value_prop: "Premium basics that justify the price through quality, not hype"
```

---

## COLLECTION DESIGN TOKENS

```yaml
collection_tokens:
  colors:
    # SIGNATURE: Luxurious, Timeless, Premium
    primary: "#0D0D0D"           # Black
    accent: "#D4AF37"            # Gold
    accent_secondary: "#B76E79"  # Rose Gold
    accent_soft: "#C9A962"       # Soft Gold
    white: "#FAFAFA"             # Off-white
    cream: "#F5F3EF"             # Warm Grey
    text_primary: "#0D0D0D"
    text_secondary: "#6B6B6B"
    text_gold: "#D4AF37"

  gradients:
    gold: "linear-gradient(135deg, #D4AF37 0%, #F5D77A 50%, #D4AF37 100%)"
    rose_gold: "linear-gradient(135deg, #B76E79 0%, #E8B4BC 50%, #B76E79 100%)"
    subtle: "linear-gradient(180deg, #FAFAFA 0%, #F5F3EF 100%)"

  typography:
    headings:
      color: "#0D0D0D"
      accent_color: "#D4AF37"    # Gold for special headings
      family: "Cormorant Garamond"
    body:
      color: "#4A4A4A"
      family: "Inter"

  ui_elements:
    badge_new:
      background: "#D4AF37"      # Gold
      color: "#0D0D0D"
    badge_bundle:
      background: "#059669"
      color: "#FAFAFA"
    cta_primary:
      background: "#0D0D0D"
      color: "#FAFAFA"
      hover_background: "#D4AF37"
      hover_color: "#0D0D0D"

  imagery:
    style: "Clean, minimal, premium"
    background: "White or cream seamless"
    accents: "Gold/rose gold props or details"
    subjects: "Products and clean model shots"
    color_grade: "Warm, true-to-color, high detail"
```

---

## SECTION 1: CLEAN HERO

### Specification

```yaml
section:
  id: "sig_hero"
  name: "Clean Hero"
  type: "minimal_hero"
  height:
    desktop: "80vh"
    mobile: "70vh"
  background:
    type: "image"
    url: "/assets/images/signature-hero.jpg"
    alt: "Clean studio shot of SIGNATURE essentials"
    position: "center center"
    size: "cover"
    overlay: "linear-gradient(180deg, rgba(250,250,250,0.1) 0%, rgba(250,250,250,0.3) 100%)"

  image_specs:
    style: "Clean white/grey studio"
    subject: "Single model or neatly arranged product flat lay"
    focus: "Fabric quality, fit, craftsmanship"
```

### Content

```yaml
content:
  collection_name:
    text: "SIGNATURE"
    font: "Cormorant Garamond"
    size: "clamp(2.5rem, 8vw, 4.5rem)"
    weight: 400
    letter_spacing: "0.2em"
    color: "#0D0D0D"

  tagline:
    text: "The Foundation. Built to Last."
    font: "Inter"
    size: "clamp(0.875rem, 2vw, 1rem)"
    weight: 400
    letter_spacing: "0.15em"
    color: "#6B6B6B"
    margin_top: "16px"

  cta_primary:
    text: "BUILD YOUR WARDROBE"
    url: "#categories"
    style:
      background: "#0D0D0D"
      color: "#FAFAFA"
      padding: "18px 48px"
      font_size: "0.75rem"
      letter_spacing: "0.15em"
      hover:
        background: "#6B6B6B"
    margin_top: "40px"
```

### Elementor Configuration

```json
{
  "elementor_widget": "container",
  "settings": {
    "content_width": "full",
    "min_height": {"unit": "vh", "size": 80},
    "min_height_mobile": {"unit": "vh", "size": 70},
    "flex_direction": "column",
    "flex_justify_content": "center",
    "flex_align_items": "center",
    "background_background": "classic",
    "background_image": {"url": "/assets/images/signature-hero.jpg"},
    "background_size": "cover",
    "background_position": "center center",
    "background_overlay_background": "gradient",
    "background_overlay_color": "rgba(250,250,250,0.1)",
    "background_overlay_color_b": "rgba(250,250,250,0.3)"
  },
  "children": [
    {
      "elementor_widget": "heading",
      "settings": {
        "title": "SIGNATURE",
        "header_size": "h1",
        "align": "center",
        "typography_font_family": "Cormorant Garamond",
        "typography_font_size": {"unit": "rem", "size": 4.5},
        "typography_letter_spacing": {"unit": "em", "size": 0.2},
        "title_color": "#0D0D0D"
      }
    },
    {
      "elementor_widget": "text-editor",
      "settings": {
        "editor": "The Foundation. Built to Last.",
        "align": "center",
        "typography_font_family": "Inter",
        "typography_font_size": {"unit": "rem", "size": 1},
        "typography_letter_spacing": {"unit": "em", "size": 0.15},
        "text_color": "#6B6B6B"
      }
    },
    {
      "elementor_widget": "button",
      "settings": {
        "text": "BUILD YOUR WARDROBE",
        "link": {"url": "#categories"},
        "button_text_color": "#FAFAFA",
        "background_color": "#0D0D0D",
        "button_text_color_hover": "#FAFAFA",
        "button_background_hover_color": "#6B6B6B",
        "button_padding": {"unit": "px", "top": 18, "right": 48, "bottom": 18, "left": 48}
      }
    }
  ]
}
```

---

## SECTION 2: ESSENTIALS PHILOSOPHY

### Specification

```yaml
section:
  id: "sig_philosophy"
  name: "Essentials Philosophy"
  type: "split_content"
  background: "#FFFFFF"
  padding:
    desktop: "100px 0"
    mobile: "60px 0"
  layout:
    desktop: "40% image / 60% content"
    mobile: "stacked"
```

### Content

```yaml
content:
  image:
    url: "/assets/images/signature-fabric-detail.jpg"
    alt: "Close-up of premium Pima cotton fabric"
    type: "macro_detail"

  headline:
    text: "ESSENTIALS, ELEVATED"
    font: "Cormorant Garamond"
    size: "clamp(1.5rem, 4vw, 2.25rem)"
    color: "#0D0D0D"

  body_copy:
    paragraphs:
      - text: "The SIGNATURE collection isn't about what's new. It's about what lasts."
        style: "primary"
        color: "#4A4A4A"

      - text: "Premium cotton. Reinforced stitching. Cuts that flatter every body. These are the pieces you'll reach for first, always."
        style: "secondary"
        color: "#6B6B6B"
```

---

## SECTION 3: CATEGORY NAVIGATION

### Specification

```yaml
section:
  id: "sig_categories"
  name: "Category Navigation"
  type: "category_cards"
  anchor: "categories"
  background: "#F5F3EF"
  padding:
    desktop: "80px 24px"
    mobile: "48px 16px"
```

### Content

```yaml
content:
  header:
    headline: "BUILD YOUR BASE"
    font: "Cormorant Garamond"
    size: "clamp(1.25rem, 3vw, 1.75rem)"
    color: "#0D0D0D"

  categories:
    - name: "TOPS"
      count: 12
      icon: "👕"
      image: "/assets/images/categories/tops.jpg"
      url: "/collection/signature/?category=tops"

    - name: "BOTTOMS"
      count: 8
      icon: "👖"
      image: "/assets/images/categories/bottoms.jpg"
      url: "/collection/signature/?category=bottoms"

    - name: "OUTERWEAR"
      count: 6
      icon: "🧥"
      image: "/assets/images/categories/outerwear.jpg"
      url: "/collection/signature/?category=outerwear"

    - name: "ACCESSORIES"
      count: 4
      icon: "🧢"
      image: "/assets/images/categories/accessories.jpg"
      url: "/collection/signature/?category=accessories"

    - name: "SETS"
      count: 3
      icon: "📦"
      image: "/assets/images/categories/sets.jpg"
      url: "/collection/signature/?category=sets"
      badge: "SAVE 20%"

  card_style:
    background: "#FFFFFF"
    border: "1px solid rgba(0,0,0,0.05)"
    padding: "24px"
    hover:
      border_color: "#0D0D0D"
      shadow: "0 8px 24px rgba(0,0,0,0.08)"
```

---

## SECTION 4: PRODUCT GRID

### Specification

```yaml
section:
  id: "sig_products"
  name: "Product Grid"
  type: "filterable_grid"
  anchor: "products"
  background: "#FFFFFF"
  padding:
    desktop: "80px 24px"
    mobile: "48px 16px"
```

### Content

```yaml
content:
  filters:
    layout: "horizontal"
    items:
      - type: "dropdown"
        label: "Size"
        options: ["XS", "S", "M", "L", "XL", "XXL", "3XL"]
      - type: "dropdown"
        label: "Color"
        options: ["Black", "White", "Grey", "Cream", "Navy"]
      - type: "dropdown"
        label: "Category"
        options: ["All", "Tops", "Bottoms", "Outerwear", "Accessories"]
    sort:
      label: "Sort"
      default: "Featured"
      options: ["Featured", "Price: Low to High", "Price: High to Low", "Newest"]

  product_grid:
    source: "woocommerce"
    category: "signature"
    columns:
      desktop: 4
      tablet: 3
      mobile: 2
    gap: "16px"
    pagination: true
    products_per_page: 16

  product_card:
    style: "clean"
    background: "#FFFFFF"
    border: "1px solid rgba(0,0,0,0.05)"
    hover:
      border_color: "#0D0D0D"
    image:
      aspect_ratio: "3:4"
      hover_effect: "secondary_image"
    color_swatches:
      show: true
      max_display: 4
      format: "circles"
```

---

## SECTION 5: QUALITY PROOF POINTS

### Specification

```yaml
section:
  id: "sig_quality"
  name: "Quality Proof Points"
  type: "icon_grid"
  background: "#F5F3EF"
  padding:
    desktop: "60px 24px"
    mobile: "40px 16px"
```

### Content

```yaml
content:
  header:
    headline: "WHY SIGNATURE?"
    font: "Cormorant Garamond"
    size: "1.25rem"
    color: "#0D0D0D"

  proof_points:
    columns:
      desktop: 6
      tablet: 3
      mobile: 2
    items:
      - icon: "🌿"
        label: "Premium Pima Cotton"

      - icon: "🧵"
        label: "Reinforced Seams"

      - icon: "✓"
        label: "Pre-shrunk & Tested"

      - icon: "📐"
        label: "Inclusive Sizing (XS-3XL)"

      - icon: "↩️"
        label: "100-Day Returns"

      - icon: "🌍"
        label: "Sustainably Made"

  style:
    icon_size: "2rem"
    label_font: "Inter"
    label_size: "0.75rem"
    label_color: "#6B6B6B"
```

---

## SECTION 6: BUNDLE UPSELL

### Specification

```yaml
section:
  id: "sig_bundle"
  name: "Bundle Upsell"
  type: "promotional_split"
  background:
    type: "gradient"
    value: "linear-gradient(135deg, #F5F3EF 0%, #FFFFFF 100%)"
  padding:
    desktop: "80px 24px"
    mobile: "48px 16px"
```

### Content

```yaml
content:
  image:
    url: "/assets/images/signature-bundle.jpg"
    alt: "The Starter Bundle: Tee, Hoodie, and Jogger neatly folded"
    style: "Neatly stacked/folded products on clean background"

  badge:
    text: "SAVE 20%"
    style:
      background: "#059669"
      color: "#FFFFFF"

  headline:
    text: "THE STARTER BUNDLE"
    font: "Cormorant Garamond"
    size: "clamp(1.5rem, 4vw, 2rem)"
    color: "#0D0D0D"

  subline:
    text: "3 essentials. 1 perfect foundation."
    font: "Inter"
    size: "1rem"
    color: "#6B6B6B"

  pricing:
    original: "$375"
    sale: "$299"
    original_style:
      text_decoration: "line-through"
      color: "#6B6B6B"
    sale_style:
      font_size: "2rem"
      font_weight: 600
      color: "#0D0D0D"

  bundle_contents:
    - "Essential Crew Tee"
    - "Signature Heavyweight Hoodie"
    - "Classic Fit Jogger"

  cta:
    text: "BUILD YOUR BUNDLE"
    url: "/product/starter-bundle/"
    style:
      background: "#0D0D0D"
      color: "#FAFAFA"
      padding: "16px 40px"
      width: "100%"
      max_width: "300px"
```

---

## FULL PAGE ASSEMBLY

```yaml
page_sections:
  - section_id: "sig_hero"
    order: 1
    visible: true

  - section_id: "sig_philosophy"
    order: 2
    visible: true

  - section_id: "sig_categories"
    order: 3
    visible: true
    anchor: "categories"

  - section_id: "sig_products"
    order: 4
    visible: true
    anchor: "products"

  - section_id: "sig_quality"
    order: 5
    visible: true

  - section_id: "sig_bundle"
    order: 6
    visible: true
```

### Agent Execution Checklist

```yaml
execution_checklist:
  phase_1_setup:
    - task: "Create 'signature' WooCommerce category"
      status: "pending"

    - task: "Create subcategory tags: tops, bottoms, outerwear, accessories, sets"
      status: "pending"

  phase_2_content:
    - task: "Create hero image (clean studio shot)"
      specs:
        style: "Minimal white/grey studio"
        subject: "Model in signature basics or product flat lay"
      status: "pending"

    - task: "Create fabric detail macro image"
      status: "pending"

    - task: "Create 5 category card images"
      status: "pending"

    - task: "Create bundle product image"
      status: "pending"

  phase_3_build:
    - task: "Build all 6 sections"
      status: "pending"

  phase_4_products:
    - task: "Create bundle product with 20% discount"
      status: "pending"
```

---

*End of SIGNATURE Collection Specification*
