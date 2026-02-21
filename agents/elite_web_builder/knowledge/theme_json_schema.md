# WordPress FSE theme.json Validation Reference

## Version 2 Schema (Current)

### Required Structure
```json
{
  "$schema": "https://schemas.wp.org/trunk/theme.json",
  "version": 2,
  "settings": {},
  "styles": {},
  "templateParts": [],
  "customTemplates": [],
  "patterns": []
}
```

### Required Fields
- `version`: Must be `2` (integer, not string)
- `$schema`: Recommended for validation tooling

## Color Palette Rules

### Entry Format
```json
{
  "slug": "rose-gold",
  "name": "Rose Gold",
  "color": "#B76E79"
}
```

### Validation Rules
- `slug`: kebab-case only (`[a-z0-9-]+`), no duplicates
- `name`: Human-readable, required
- `color`: Valid hex (`#RGB`, `#RRGGBB`, `#RRGGBBAA`)
- No duplicate slugs within the palette array

## Typography

### fontFamilies Structure
```json
{
  "fontFamily": "'Playfair Display', serif",
  "slug": "playfair-display",
  "name": "Playfair Display",
  "fontFace": [
    {
      "fontFamily": "Playfair Display",
      "fontWeight": "400 900",
      "fontStyle": "normal",
      "fontDisplay": "swap",
      "src": ["file:./assets/fonts/PlayfairDisplay-Variable.woff2"]
    }
  ]
}
```

### Validation Rules
- `slug`: kebab-case, no duplicates
- `fontFamily`: Valid CSS font-family value
- `fontFace.fontDisplay`: MUST be `swap` (performance requirement)
- `fontFace.src`: Array of valid file paths or URLs
- Each fontFace MUST have `fontFamily`, `fontWeight`, `src`

## Spacing

### spacingScale
```json
{
  "spacingScale": {
    "operator": "*",
    "increment": 1.5,
    "steps": 7,
    "mediumStep": 1.5,
    "unit": "rem"
  }
}
```

### Custom Spacing
```json
{
  "spacingSizes": [
    { "slug": "10", "size": "0.25rem", "name": "Extra Small" },
    { "slug": "20", "size": "0.5rem", "name": "Small" },
    { "slug": "30", "size": "1rem", "name": "Medium" },
    { "slug": "40", "size": "1.5rem", "name": "Large" },
    { "slug": "50", "size": "2.5rem", "name": "Extra Large" }
  ]
}
```

### blockGap, padding, margin
- `blockGap`: Space between blocks in a container
- `padding`: Container inner spacing
- `margin`: Container outer spacing

## Layout

### Settings
```json
{
  "layout": {
    "contentSize": "800px",
    "wideSize": "1200px",
    "allowEditing": true
  }
}
```

- `contentSize`: Default content width
- `wideSize`: Wide alignment width
- `allowEditing`: Whether users can modify layout in editor

## Styles Section

### Global Styles
```json
{
  "styles": {
    "color": {
      "background": "var(--wp--preset--color--base)",
      "text": "var(--wp--preset--color--contrast)"
    },
    "typography": {
      "fontFamily": "var(--wp--preset--font-family--montserrat)",
      "fontSize": "var(--wp--preset--font-size--medium)"
    },
    "elements": {
      "link": { "color": { "text": "var(--wp--preset--color--rose-gold)" } },
      "h1": { "typography": { "fontFamily": "var(--wp--preset--font-family--playfair-display)" } }
    }
  }
}
```

## Validation Tool
```bash
# WP-CLI validation
wp theme validate theme.json

# JSON Schema validation
npx ajv validate -s https://schemas.wp.org/trunk/theme.json -d theme.json
```

## Common Mistakes
- Missing `version: 2` (must be integer `2`, not string `"2"`)
- Duplicate slugs in color palette or font families
- Invalid hex values (missing `#`, wrong length)
- fontFace without `src` array
- fontFace without `fontDisplay: swap` (performance penalty)
- Using `px` for font sizes instead of `rem`/`clamp()`
- Referencing non-existent preset vars in styles
