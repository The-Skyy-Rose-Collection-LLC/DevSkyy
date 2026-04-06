# Elementor JSON Patterns

## Structure Overview

Elementor pages are stored as nested JSON with three element types:
- **Section** — Full-width container (rows)
- **Column** — Vertical divisions within sections
- **Widget** — Actual content elements

```json
{
  "id": "abc1234",
  "elType": "section|column|widget",
  "settings": {},
  "elements": []
}
```

## Section Templates

### Full-Width Hero

```json
{
  "id": "hero001",
  "elType": "section",
  "settings": {
    "layout": "full_width",
    "content_width": {"unit": "%", "size": 100},
    "min_height": {"unit": "vh", "size": 100},
    "background_background": "classic",
    "background_image": {"url": "https://skyyrose.co/wp-content/uploads/hero.jpg"},
    "background_position": "center center",
    "background_size": "cover",
    "background_overlay_background": "classic",
    "background_overlay_color": "#0A0A0A",
    "background_overlay_opacity": {"unit": "%", "size": 40}
  },
  "elements": [
    {
      "id": "col001",
      "elType": "column",
      "settings": {
        "_column_size": 100,
        "align": "center",
        "vertical_align": "middle"
      },
      "elements": []
    }
  ]
}
```

### Two Column Layout

```json
{
  "id": "twocol001",
  "elType": "section",
  "settings": {
    "gap": "extended",
    "structure": "20"
  },
  "elements": [
    {
      "id": "left001",
      "elType": "column",
      "settings": {"_column_size": 50},
      "elements": []
    },
    {
      "id": "right001",
      "elType": "column",
      "settings": {"_column_size": 50},
      "elements": []
    }
  ]
}
```

## Widget Templates

### Heading

```json
{
  "id": "head001",
  "elType": "widget",
  "widgetType": "heading",
  "settings": {
    "title": "BLACK ROSE COLLECTION",
    "header_size": "h1",
    "align": "center",
    "title_color": "#FFFFFF",
    "typography_typography": "custom",
    "typography_font_family": "Bebas Neue",
    "typography_font_size": {"unit": "px", "size": 72},
    "typography_font_weight": "700",
    "typography_text_transform": "uppercase",
    "typography_letter_spacing": {"unit": "px", "size": 3}
  }
}
```

### Text Editor

```json
{
  "id": "text001",
  "elType": "widget",
  "widgetType": "text-editor",
  "settings": {
    "editor": "<p>Built for those who move through darkness like it's home.</p>",
    "align": "center",
    "text_color": "#FFFFFF",
    "typography_typography": "custom",
    "typography_font_family": "Inter",
    "typography_font_size": {"unit": "px", "size": 18},
    "typography_font_weight": "400"
  }
}
```

### Button

```json
{
  "id": "btn001",
  "elType": "widget",
  "widgetType": "button",
  "settings": {
    "text": "SHOP NOW",
    "link": {"url": "/shop/black-rose/", "is_external": false},
    "align": "center",
    "size": "lg",
    "button_type": "default",
    "background_color": "#B76E79",
    "button_text_color": "#FFFFFF",
    "border_radius": {"unit": "px", "size": 0},
    "typography_typography": "custom",
    "typography_font_family": "Bebas Neue",
    "typography_font_size": {"unit": "px", "size": 18},
    "typography_letter_spacing": {"unit": "px", "size": 2}
  }
}
```

### Image

```json
{
  "id": "img001",
  "elType": "widget",
  "widgetType": "image",
  "settings": {
    "image": {
      "url": "https://skyyrose.co/wp-content/uploads/product.jpg",
      "id": 123
    },
    "image_size": "full",
    "align": "center",
    "width": {"unit": "%", "size": 100},
    "hover_animation": "grow"
  }
}
```

### WooCommerce Products Grid

```json
{
  "id": "prod001",
  "elType": "widget",
  "widgetType": "wc-products",
  "settings": {
    "columns": "4",
    "rows": "2",
    "paginate": "yes",
    "query_post_type": "product",
    "query_posts_per_page": 8,
    "query_product_cat_ids": [15],
    "orderby": "date",
    "order": "desc"
  }
}
```

## Product Hotspot Pattern

Interactive product hotspots for lookbook images:

```json
{
  "id": "hotspot001",
  "elType": "widget",
  "widgetType": "image-hotspot",
  "settings": {
    "image": {"url": "https://skyyrose.co/wp-content/uploads/lookbook.jpg"},
    "hotspots": [
      {
        "hotspot_x": {"unit": "%", "size": 35},
        "hotspot_y": {"unit": "%", "size": 45},
        "hotspot_label": "BLACK ROSE TEE",
        "hotspot_link": {"url": "/product/black-rose-tee/"},
        "hotspot_icon": {"value": "fas fa-plus"}
      },
      {
        "hotspot_x": {"unit": "%", "size": 60},
        "hotspot_y": {"unit": "%", "size": 70},
        "hotspot_label": "SIGNATURE JOGGER",
        "hotspot_link": {"url": "/product/signature-jogger/"},
        "hotspot_icon": {"value": "fas fa-plus"}
      }
    ]
  }
}
```

## SkyyRose Theme Presets

### Colors

```json
{
  "__globals__": {
    "background_color": "globals/colors?id=void-black",
    "text_color": "globals/colors?id=pure-white",
    "accent_color": "globals/colors?id=rose-gold"
  }
}
```

### Typography Presets

```json
{
  "typography_typography": "custom",
  "typography_font_family": "Bebas Neue",
  "typography_font_size": {"unit": "px", "size": 48},
  "typography_font_weight": "700",
  "typography_text_transform": "uppercase",
  "typography_letter_spacing": {"unit": "px", "size": 2}
}
```

## Python Generator

```python
import json
import random
import string

def element_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))

def create_section(columns: list, settings: dict = None) -> dict:
    base = {
        "id": element_id(),
        "elType": "section",
        "settings": settings or {},
        "elements": columns
    }
    return base

def create_column(widgets: list, size: int = 100) -> dict:
    return {
        "id": element_id(),
        "elType": "column",
        "settings": {"_column_size": size},
        "elements": widgets
    }

def create_heading(text: str, size: str = "h2", color: str = "#FFFFFF") -> dict:
    return {
        "id": element_id(),
        "elType": "widget",
        "widgetType": "heading",
        "settings": {
            "title": text,
            "header_size": size,
            "title_color": color
        }
    }

def create_button(text: str, url: str, color: str = "#B76E79") -> dict:
    return {
        "id": element_id(),
        "elType": "widget",
        "widgetType": "button",
        "settings": {
            "text": text,
            "link": {"url": url},
            "background_color": color
        }
    }

# Build complete page
def build_landing_page(hero_image: str, title: str, cta_url: str) -> str:
    page = [
        create_section(
            columns=[create_column([
                create_heading(title, "h1"),
                create_button("SHOP NOW", cta_url)
            ])],
            settings={
                "layout": "full_width",
                "min_height": {"unit": "vh", "size": 100},
                "background_image": {"url": hero_image}
            }
        )
    ]
    return json.dumps(page, indent=2)
```
