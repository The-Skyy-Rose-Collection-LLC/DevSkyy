# SKYYROSE LOVE HURTS COLLECTION PAGE SPECIFICATION

# Version: 1.0.0

# Last Updated: 2024-12-11

# Platform: WordPress + WooCommerce + Elementor Pro

---

## PAGE METADATA

```yaml
page:
  name: "LOVE HURTS Collection"
  slug: "/collection/love-hurts/"
  template: "elementor_header_footer"
  collection_id: "love_hurts"
  woocommerce_category: "love-hurts"

  seo:
    title: "LOVE HURTS | Wear Your Heart, Own Your Story | SkyyRose"
    description: "LOVE HURTS - where emotion meets luxury streetwear. A collection honoring family legacy and authentic expression. Born in Oakland, made with heart."
    keywords: ["emotional streetwear", "oakland fashion", "family legacy clothing", "heartfelt fashion"]

  og:
    image: "/assets/images/og-love-hurts.jpg"
    type: "product.group"

  brand_essence:
    mood: "Warm, emotional, authentic, bold"
    tagline: "Wear Your Heart. Own Your Story."
    voice: "Personal, inviting, heartfelt, never performative"
    origin_story: "'Hurts' is the founder's family name - this collection honors that legacy"
```

---

## COLLECTION DESIGN TOKENS

```yaml
collection_tokens:
  colors:
    primary: "#8B3A3A"          # Deep rose/burgundy
    secondary: "#5C2828"        # Darker burgundy
    accent: "#D4A5A5"           # Soft rose
    background_warm: "#1A1212"  # Warm dark
    background_light: "#FDF8F8" # Cream with rose tint
    text_primary: "#FAFAFA"
    text_dark: "#2D1F1F"
    text_muted: "rgba(250, 250, 250, 0.7)"

  gradients:
    hero: "linear-gradient(180deg, #5C2828 0%, #8B3A3A 50%, #1A1212 100%)"
    warm_overlay: "linear-gradient(180deg, rgba(139,58,58,0.4) 0%, rgba(26,18,18,0.8) 100%)"

  typography:
    headings:
      color: "#FAFAFA"
      family: "Cormorant Garamond"
    body:
      color: "rgba(250, 250, 250, 0.85)"
      family: "Inter"

  imagery:
    style: "Warm, emotional, authentic"
    subjects: "Models expressing genuine emotion - joy, contemplation, strength"
    locations: "Oakland landmarks, Lake Merritt, urban streets with warmth"
    color_grade: "Warm tones, slightly lifted shadows"
```

---

## SECTION 1: EMOTIONAL HERO

### Specification

```yaml
section:
  id: "lh_hero"
  name: "Emotional Hero"
  type: "split_video_hero"
  height:
    desktop: "100vh"
    mobile: "90vh"
  background:
    type: "video"
    video_url: "/assets/videos/love-hurts-hero.mp4"
    fallback_image: "/assets/images/love-hurts-hero-fallback.jpg"
    overlay: "linear-gradient(180deg, rgba(139,58,58,0.3) 0%, rgba(26,18,18,0.7) 100%)"

  video_specs:
    content: "Models expressing genuine emotion - not blank faces. Joy, contemplation, strength. Oakland backdrop visible."
    duration: "15-20s loop"
    style: "Warmer color grade than BLACK ROSE, more movement and life"
    subjects: "2-3 models, diverse, authentic expressions"
```

### Content

```yaml
content:
  collection_name:
    text: "LOVE HURTS"
    font: "Cormorant Garamond"
    size: "clamp(2.5rem, 8vw, 5rem)"
    weight: 400
    letter_spacing: "0.2em"
    color: "#FAFAFA"

  tagline:
    text: "Wear Your Heart. Own Your Story."
    font: "Inter"
    size: "clamp(0.875rem, 2vw, 1.125rem)"
    weight: 400
    letter_spacing: "0.15em"
    color: "rgba(250, 250, 250, 0.8)"
    margin_top: "16px"

  cta_primary:
    text: "SHOP THE COLLECTION"
    url: "#products"
    style:
      background: "#FDF8F8"
      color: "#5C2828"
      padding: "18px 48px"
      font_size: "0.75rem"
      letter_spacing: "0.15em"
      hover:
        background: "#FAFAFA"
        color: "#8B3A3A"
    margin_top: "40px"
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
    "background_video_link": "/assets/videos/love-hurts-hero.mp4",
    "background_video_fallback": {"url": "/assets/images/love-hurts-hero-fallback.jpg"},
    "background_overlay_background": "gradient",
    "background_overlay_color": "rgba(139,58,58,0.3)",
    "background_overlay_color_b": "rgba(26,18,18,0.7)",
    "background_overlay_gradient_angle": {"unit": "deg", "size": 180}
  },
  "children": [
    {
      "elementor_widget": "heading",
      "settings": {
        "title": "LOVE HURTS",
        "header_size": "h1",
        "align": "center",
        "typography_font_family": "Cormorant Garamond",
        "typography_font_size": {"unit": "rem", "size": 5},
        "typography_font_size_mobile": {"unit": "rem", "size": 2.5},
        "typography_letter_spacing": {"unit": "em", "size": 0.2},
        "title_color": "#FAFAFA",
        "_animation": "fadeIn"
      }
    },
    {
      "elementor_widget": "text-editor",
      "settings": {
        "editor": "Wear Your Heart. Own Your Story.",
        "align": "center",
        "typography_font_family": "Inter",
        "typography_font_size": {"unit": "rem", "size": 1.125},
        "typography_letter_spacing": {"unit": "em", "size": 0.15},
        "text_color": "rgba(250, 250, 250, 0.8)"
      }
    },
    {
      "elementor_widget": "button",
      "settings": {
        "text": "SHOP THE COLLECTION",
        "link": {"url": "#products"},
        "align": "center",
        "button_text_color": "#5C2828",
        "background_color": "#FDF8F8",
        "button_text_color_hover": "#8B3A3A",
        "button_background_hover_color": "#FAFAFA",
        "button_padding": {"unit": "px", "top": 18, "right": 48, "bottom": 18, "left": 48}
      }
    }
  ]
}
```

---

## SECTION 2: ORIGIN STORY

### Specification

```yaml
section:
  id: "lh_origin"
  name: "Origin Story"
  type: "split_content_story"
  background:
    type: "gradient"
    value: "linear-gradient(135deg, #FDF8F8 0%, #F5EEEE 100%)"
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
    url: "/assets/images/love-hurts-heritage.jpg"
    alt: "Heritage image representing the Hurts family legacy"
    type: "warm_portrait_or_vintage"
    content: "Could be vintage family photo style, Oakland heritage, or warm portrait"

  pretitle:
    text: "THE NAME TELLS THE STORY"
    font: "Inter"
    size: "0.75rem"
    letter_spacing: "0.15em"
    color: "#8B3A3A"

  headline:
    text: "LOVE HURTS isn't just a statement—it's a family legacy."
    font: "Cormorant Garamond"
    size: "clamp(1.5rem, 4vw, 2.25rem)"
    color: "#2D1F1F"
    style: "normal"

  body_copy:
    paragraphs:
      - text: "The \"Hurts\" name has been part of our story for generations. This collection honors that history while inviting you to write your own."
        style: "primary"
        color: "#4A3535"

      - text: "Because love—real love—leaves its mark."
        style: "italic"
        color: "#8B3A3A"
        font: "Cormorant Garamond"
        size: "1.125rem"

  design_note: "This section should feel personal and inviting, not corporate"
```

### Elementor Configuration

```json
{
  "elementor_widget": "container",
  "settings": {
    "content_width": "full",
    "background_background": "gradient",
    "background_color": "#FDF8F8",
    "background_color_b": "#F5EEEE",
    "background_gradient_angle": {"unit": "deg", "size": 135},
    "padding": {"unit": "px", "top": 100, "right": 0, "bottom": 100, "left": 0}
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
            "_element_width": "40%",
            "_element_width_mobile": "100%",
            "min_height": {"unit": "px", "size": 400}
          },
          "children": [
            {
              "elementor_widget": "image",
              "settings": {
                "image": {"url": "/assets/images/love-hurts-heritage.jpg"},
                "image_size": "full",
                "width": {"unit": "%", "size": 100},
                "object-fit": "cover",
                "border_radius": {"unit": "px", "size": 0}
              }
            }
          ]
        },
        {
          "elementor_widget": "container",
          "settings": {
            "_element_width": "60%",
            "_element_width_mobile": "100%",
            "flex_direction": "column",
            "flex_justify_content": "center",
            "padding": {"unit": "px", "top": 0, "right": 40, "bottom": 0, "left": 40}
          },
          "children": [
            {
              "elementor_widget": "text-editor",
              "settings": {
                "editor": "THE NAME TELLS THE STORY",
                "typography_font_family": "Inter",
                "typography_font_size": {"unit": "rem", "size": 0.75},
                "typography_letter_spacing": {"unit": "em", "size": 0.15},
                "text_color": "#8B3A3A"
              }
            },
            {
              "elementor_widget": "heading",
              "settings": {
                "title": "LOVE HURTS isn't just a statement—it's a family legacy.",
                "header_size": "h2",
                "typography_font_family": "Cormorant Garamond",
                "typography_font_size": {"unit": "rem", "size": 2.25},
                "title_color": "#2D1F1F"
              }
            },
            {
              "elementor_widget": "text-editor",
              "settings": {
                "editor": "The \"Hurts\" name has been part of our story for generations. This collection honors that history while inviting you to write your own.",
                "typography_font_family": "Inter",
                "typography_font_size": {"unit": "rem", "size": 1},
                "typography_line_height": {"unit": "em", "size": 1.7},
                "text_color": "#4A3535"
              }
            },
            {
              "elementor_widget": "text-editor",
              "settings": {
                "editor": "<em>Because love—real love—leaves its mark.</em>",
                "typography_font_family": "Cormorant Garamond",
                "typography_font_size": {"unit": "rem", "size": 1.125},
                "typography_font_style": "italic",
                "text_color": "#8B3A3A"
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

## SECTION 3: EMOTIONAL LOOKBOOK

### Specification

```yaml
section:
  id: "lh_lookbook"
  name: "Emotional Lookbook"
  type: "fullwidth_carousel"
  background: "#FAFAFA"
  padding:
    desktop: "80px 0"
    mobile: "48px 0"
```

### Content

```yaml
content:
  carousel:
    type: "editorial_slider"
    autoplay: true
    autoplay_speed: 5000
    pause_on_hover: true
    slides:
      - image: "/assets/images/lookbook/love-hurts-1.jpg"
        alt: "Model at Lake Merritt sunset in LOVE HURTS hoodie"
        caption: "Lake Merritt, Oakland"

      - image: "/assets/images/lookbook/love-hurts-2.jpg"
        alt: "Urban Oakland street scene with LOVE HURTS joggers"
        caption: "Streets of Oakland"

      - image: "/assets/images/lookbook/love-hurts-3.jpg"
        alt: "Intimate studio portrait expressing vulnerability"
        caption: "Studio Session"

      - image: "/assets/images/lookbook/love-hurts-4.jpg"
        alt: "Friends laughing in LOVE HURTS collection"
        caption: "Community"

      - image: "/assets/images/lookbook/love-hurts-5.jpg"
        alt: "Solo contemplative moment in LOVE HURTS tee"
        caption: "Reflection"

  image_specs:
    aspect_ratio: "16:9"
    height:
      desktop: "70vh"
      mobile: "50vh"
    object_fit: "cover"

  footer_text:
    text: "Every piece carries intention. What will yours say?"
    font: "Cormorant Garamond"
    size: "1.125rem"
    style: "italic"
    color: "#4A3535"

  navigation:
    type: "dots"
    position: "bottom-center"
    active_color: "#8B3A3A"
    inactive_color: "rgba(139, 58, 58, 0.3)"
```

### Elementor Configuration

```json
{
  "elementor_widget": "container",
  "settings": {
    "content_width": "full",
    "background_color": "#FAFAFA",
    "padding": {"unit": "px", "top": 80, "right": 0, "bottom": 80, "left": 0}
  },
  "children": [
    {
      "elementor_widget": "slides",
      "settings": {
        "slides": [
          {
            "background_image": {"url": "/assets/images/lookbook/love-hurts-1.jpg"},
            "heading": "",
            "description": "Lake Merritt, Oakland"
          },
          {
            "background_image": {"url": "/assets/images/lookbook/love-hurts-2.jpg"},
            "heading": "",
            "description": "Streets of Oakland"
          },
          {
            "background_image": {"url": "/assets/images/lookbook/love-hurts-3.jpg"},
            "heading": "",
            "description": "Studio Session"
          },
          {
            "background_image": {"url": "/assets/images/lookbook/love-hurts-4.jpg"},
            "heading": "",
            "description": "Community"
          },
          {
            "background_image": {"url": "/assets/images/lookbook/love-hurts-5.jpg"},
            "heading": "",
            "description": "Reflection"
          }
        ],
        "slides_height": {"unit": "vh", "size": 70},
        "slides_height_mobile": {"unit": "vh", "size": 50},
        "autoplay": "yes",
        "autoplay_speed": 5000,
        "pause_on_hover": "yes",
        "navigation": "dots",
        "pagination_color": "rgba(139, 58, 58, 0.3)",
        "pagination_color_active": "#8B3A3A"
      }
    },
    {
      "elementor_widget": "text-editor",
      "settings": {
        "editor": "<em>Every piece carries intention. What will yours say?</em>",
        "align": "center",
        "typography_font_family": "Cormorant Garamond",
        "typography_font_size": {"unit": "rem", "size": 1.125},
        "text_color": "#4A3535"
      }
    }
  ]
}
```

---

## SECTION 4: PRODUCT GRID WITH EDITORIAL

### Specification

```yaml
section:
  id: "lh_products"
  name: "Product Grid with Editorial"
  type: "mixed_content_grid"
  anchor: "products"
  background: "#FDF8F8"
  padding:
    desktop: "80px 24px"
    mobile: "48px 16px"
```

### Content

```yaml
content:
  filters:
    show: true
    position: "top"
    style: "pill_buttons"
    options:
      - label: "All"
        value: "*"
        active_default: true
      - label: "Tops"
        value: "tops"
      - label: "Bottoms"
        value: "bottoms"
      - label: "Outerwear"
        value: "outerwear"
      - label: "Accessories"
        value: "accessories"
    style_config:
      active:
        background: "#8B3A3A"
        color: "#FAFAFA"
      inactive:
        background: "transparent"
        color: "#4A3535"
        border: "1px solid rgba(139, 58, 58, 0.3)"

  product_grid:
    source: "woocommerce"
    category: "love-hurts"
    columns:
      desktop: 4
      tablet: 3
      mobile: 2
    gap: "16px"

  editorial_cards:
    insert_after_every: 4
    cards:
      - type: "story_card"
        background: "linear-gradient(135deg, #8B3A3A 0%, #5C2828 100%)"
        headline: "The Story"
        subline: "Behind the Collection →"
        url: "/about/love-hurts-story/"

      - type: "quote_card"
        background: "#FDF8F8"
        quote: "\"Fashion should feel like an embrace.\""
        attribution: "— SkyyRose"

  product_card:
    style: "warm"
    background: "#FFFFFF"
    border: "1px solid rgba(139, 58, 58, 0.1)"
    hover:
      border_color: "#8B3A3A"
      shadow: "0 8px 24px rgba(139, 58, 58, 0.1)"
    title_color: "#2D1F1F"
    price_color: "#4A3535"
```

### WooCommerce Product Card Styles

```css
/* LOVE HURTS Product Grid */
.love-hurts-grid {
  background: #FDF8F8;
}

.love-hurts-grid .product {
  background: #FFFFFF;
  border: 1px solid rgba(139, 58, 58, 0.1);
  transition: all 0.3s ease;
}

.love-hurts-grid .product:hover {
  border-color: #8B3A3A;
  box-shadow: 0 8px 24px rgba(139, 58, 58, 0.1);
}

.love-hurts-grid .product .woocommerce-loop-product__title {
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  font-weight: 500;
  color: #2D1F1F;
}

.love-hurts-grid .product .price {
  color: #4A3535;
}

/* Editorial Card */
.editorial-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  text-align: center;
  min-height: 100%;
}

.editorial-card.story-card {
  background: linear-gradient(135deg, #8B3A3A 0%, #5C2828 100%);
  color: #FAFAFA;
}

.editorial-card.quote-card {
  background: #FDF8F8;
  border: 1px solid rgba(139, 58, 58, 0.2);
}

/* Filter Pills */
.filter-pills {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 32px;
}

.filter-pill {
  padding: 8px 20px;
  font-size: 0.75rem;
  letter-spacing: 0.05em;
  border-radius: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.filter-pill.active {
  background: #8B3A3A;
  color: #FAFAFA;
  border: 1px solid #8B3A3A;
}

.filter-pill:not(.active) {
  background: transparent;
  color: #4A3535;
  border: 1px solid rgba(139, 58, 58, 0.3);
}

.filter-pill:not(.active):hover {
  border-color: #8B3A3A;
}
```

---

## SECTION 5: CUSTOMER STORIES

### Specification

```yaml
section:
  id: "lh_stories"
  name: "Customer Stories"
  type: "testimonial_grid"
  background: "#F5EEEE"
  padding:
    desktop: "100px 24px"
    mobile: "60px 16px"
```

### Content

```yaml
content:
  header:
    headline: "THEIR STORIES. YOUR TURN."
    font: "Cormorant Garamond"
    size: "clamp(1.5rem, 4vw, 2rem)"
    color: "#2D1F1F"

  stories:
    source: "ugc_reviews"
    max_display: 6
    columns:
      desktop: 3
      tablet: 2
      mobile: 1

    fallback_stories:
      - image: "/assets/images/ugc/customer-1.jpg"
        quote: "This hoodie got me through my hardest days. It's like wearing a hug."
        name: "@maya_creates"
        product: "Heart Heavyweight Hoodie"

      - image: "/assets/images/ugc/customer-2.jpg"
        quote: "Finally, a brand that gets it. Emotion isn't weakness—it's power."
        name: "@oakland_native"
        product: "Sentiment Crew Tee"

      - image: "/assets/images/ugc/customer-3.jpg"
        quote: "Wore this to my graduation. My grandma would have loved it."
        name: "@jess.marie"
        product: "Legacy Joggers"

  story_card:
    style: "centered_image_quote"
    image:
      size: "80px"
      border_radius: "50%"
      border: "2px solid rgba(139, 58, 58, 0.2)"
    quote:
      font: "Inter"
      size: "0.9375rem"
      style: "italic"
      color: "#4A3535"
    attribution:
      font: "Inter"
      size: "0.75rem"
      color: "#8B3A3A"

  footer:
    cta_text: "Share Your Story"
    hashtag: "#LOVEHURTS"
    url: "https://instagram.com/explore/tags/lovehurts"
    color: "#8B3A3A"
```

### Elementor Configuration

```json
{
  "elementor_widget": "container",
  "settings": {
    "content_width": "full",
    "background_color": "#F5EEEE",
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
            "title": "\"THEIR STORIES. YOUR TURN.\"",
            "header_size": "h2",
            "align": "center",
            "typography_font_family": "Cormorant Garamond",
            "typography_font_size": {"unit": "rem", "size": 2},
            "title_color": "#2D1F1F"
          }
        },
        {
          "elementor_widget": "container",
          "settings": {
            "flex_direction": "row",
            "flex_direction_mobile": "column",
            "flex_gap": {"unit": "px", "size": 24},
            "flex_wrap": "wrap"
          },
          "children": [
            {
              "elementor_widget": "container",
              "settings": {
                "_element_width": "calc(33.333% - 16px)",
                "_element_width_mobile": "100%",
                "background_color": "#FFFFFF",
                "padding": {"unit": "px", "top": 32, "right": 24, "bottom": 32, "left": 24},
                "border_radius": {"unit": "px", "size": 0},
                "flex_direction": "column",
                "flex_align_items": "center"
              },
              "children": [
                {
                  "elementor_widget": "image",
                  "settings": {
                    "image": {"url": "/assets/images/ugc/customer-1.jpg"},
                    "image_size": "custom",
                    "image_custom_dimension": {"width": 80, "height": 80},
                    "border_radius": {"unit": "%", "size": 50},
                    "border_border": "solid",
                    "border_width": {"unit": "px", "size": 2},
                    "border_color": "rgba(139, 58, 58, 0.2)"
                  }
                },
                {
                  "elementor_widget": "text-editor",
                  "settings": {
                    "editor": "<em>\"This hoodie got me through my hardest days. It's like wearing a hug.\"</em>",
                    "align": "center",
                    "typography_font_family": "Inter",
                    "typography_font_size": {"unit": "rem", "size": 0.9375},
                    "text_color": "#4A3535"
                  }
                },
                {
                  "elementor_widget": "text-editor",
                  "settings": {
                    "editor": "— @maya_creates",
                    "align": "center",
                    "typography_font_size": {"unit": "rem", "size": 0.75},
                    "text_color": "#8B3A3A"
                  }
                }
              ]
            }
          ]
        },
        {
          "elementor_widget": "text-editor",
          "settings": {
            "editor": "Share Your Story: <a href='https://instagram.com/explore/tags/lovehurts' target='_blank'>#LOVEHURTS</a>",
            "align": "center",
            "typography_font_size": {"unit": "rem", "size": 0.875},
            "text_color": "#8B3A3A"
          }
        }
      ]
    }
  ]
}
```

---

## SECTION 6: NEWSLETTER

### Specification

```yaml
section:
  id: "lh_newsletter"
  name: "Collection Newsletter"
  type: "email_capture"
  background: "#1A1212"
  padding:
    desktop: "80px 24px"
    mobile: "60px 24px"
```

### Content

```yaml
content:
  headline:
    text: "JOIN THE STORY"
    font: "Cormorant Garamond"
    size: "clamp(1.25rem, 3vw, 1.5rem)"
    color: "#FAFAFA"

  subheadline:
    text: "New pieces, customer stories, and moments that matter. Straight to your inbox."
    font: "Inter"
    size: "0.875rem"
    color: "rgba(250, 250, 250, 0.7)"

  form:
    provider: "klaviyo"
    list_id: "{{KLAVIYO_LOVE_HURTS_LIST}}"
    fields:
      - type: "email"
        placeholder: "Your email"
        required: true
    button:
      text: "JOIN"
      style:
        background: "#8B3A3A"
        color: "#FAFAFA"
        hover:
          background: "#D4A5A5"
          color: "#2D1F1F"
```

---

## FULL PAGE ASSEMBLY

### Section Order

```yaml
page_sections:
  - section_id: "lh_hero"
    order: 1
    visible: true

  - section_id: "lh_origin"
    order: 2
    visible: true

  - section_id: "lh_lookbook"
    order: 3
    visible: true

  - section_id: "lh_products"
    order: 4
    visible: true
    anchor: "products"

  - section_id: "lh_stories"
    order: 5
    visible: true

  - section_id: "lh_newsletter"
    order: 6
    visible: true
```

### Agent Execution Checklist

```yaml
execution_checklist:
  phase_1_setup:
    - task: "Create 'love-hurts' WooCommerce category"
      status: "pending"

    - task: "Create product tags: tops, bottoms, outerwear, accessories"
      status: "pending"

  phase_2_content:
    - task: "Create hero video (emotional, warm, Oakland backdrop)"
      specs:
        duration: "15-20s"
        style: "Warmer than BLACK ROSE, more movement"
        subjects: "Models with genuine expressions"
        locations: "Oakland streets, Lake Merritt"
      status: "pending"

    - task: "Create origin story heritage image"
      specs:
        style: "Warm, personal, heritage feel"
        size: "1000x1200px"
      status: "pending"

    - task: "Create 5 lookbook images"
      specs:
        locations: ["Lake Merritt", "Oakland streets", "Studio", "Community", "Solo"]
        aspect: "16:9"
        color_grade: "Warm, lifted shadows"
      status: "pending"

    - task: "Collect or create 3+ customer story UGC images"
      status: "pending"

  phase_3_build:
    - task: "Build Section 1: Emotional Hero"
      status: "pending"

    - task: "Build Section 2: Origin Story"
      status: "pending"

    - task: "Build Section 3: Lookbook Carousel"
      status: "pending"

    - task: "Build Section 4: Product Grid"
      status: "pending"

    - task: "Build Section 5: Customer Stories"
      status: "pending"

    - task: "Build Section 6: Newsletter"
      status: "pending"
```

---

*End of LOVE HURTS Collection Specification*
