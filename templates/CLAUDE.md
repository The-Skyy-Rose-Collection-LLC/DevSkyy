# DevSkyy Templates

> Brand-consistent, responsive, accessible | 14 files

## Templates
```
templates/elementor/
├── homepage.json           # Landing page
├── product_single.json     # Product detail
├── cart.json               # Shopping cart
├── header.json / footer.json  # Global
└── three_js_viewer.html    # 3D viewer
```

## Pattern
```json
{
  "title": "SkyyRose Homepage",
  "content": [{
    "elType": "section",
    "settings": {"layout": "full_width"},
    "elements": [{
      "elType": "widget",
      "widgetType": "heading",
      "settings": {"title": "Where Love Meets Luxury"}
    }]
  }]
}
```

## Standards
| Standard | Requirement |
|----------|-------------|
| Responsive | Mobile-first |
| Brand | SkyyRose colors (#B76E79) |
| A11y | WCAG 2.1 AA |

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS
| Task | Tool |
|------|------|
| Brand assets | **MCP**: `brand_context` |
| WordPress sync | **MCP**: `wordpress_sync` |
| Template review | **Agent**: `code-reviewer` |

**"Templates are brand promises in code."**
