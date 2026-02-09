# SkyyRose Brand Colors Reference

## Brand Flagship Colors
**Primary Brand Identity**

- **Rose Gold:** `#B76E79` - Main brand color
- **Gold:** `#D4AF37` - Luxury accent
- **Gradient:** `linear-gradient(135deg, #B76E79 0%, #D4AF37 100%)`

---

## Collection-Specific Color Palettes

### Signature Collection
**Gold + Rose Gold** (Luxury rose garden pavilion)

- **Primary:** Gold `#D4AF37`
- **Secondary:** Rose Gold `#B76E79`
- **Background:** Warm ivory to golden `linear-gradient(135deg, #fff5e6 0%, #ffd9a6 100%)`
- **Accent Text:** Saddle Brown `#8b4513`

**Use Case:** Homepage, luxury product showcases, premium collections

---

### Black Rose Collection
**Metallic Silver + Black + White** (Gothic cathedral garden)

- **Primary:** Metallic Silver `#C0C0C0`
- **Secondary:** Black `#000000`
- **Tertiary:** White `#FFFFFF`
- **Background:** Deep black `linear-gradient(135deg, #1a1a1a 0%, #000000 100%)`
- **Glow Effect:** Silver glow `rgba(192, 192, 192, 0.6)`

**Use Case:** Dark/edgy collections, gothic aesthetic, nighttime scenes

---

### Love Hurts Collection
**Red + Black + White** (Enchanted castle with Beauty & Beast theme)

- **Primary:** Crimson Red `#DC143C`
- **Secondary:** Black `#000000`
- **Tertiary:** White `#FFFFFF`
- **Background:** Deep red-black `linear-gradient(135deg, #1a0000 0%, #000000 100%)`
- **Glow Effect:** Red glow `rgba(220, 20, 60, 0.7)`
- **Rose Petals:** Crimson to dark red gradient

**Use Case:** Romantic collections, Valentine's Day, passionate themes

---

### Preorder Gateway
**Dusty Pink + Rose Gold** (Futuristic portal hub)

- **Primary:** Dusty Pink (Mauve) `#D8A7B1`
- **Secondary:** Rose Gold `#B76E79`
- **Background:** Deep purple-blue `linear-gradient(135deg, #1a0a2e 0%, #16213e 100%)`
- **Portal Energy:** Dusty pink glow `rgba(216, 167, 177, 0.6)`

**Use Case:** Exclusive previews, coming soon products, limited editions

---

## Implementation Files

### Core Brand Files
- `/assets/css/brand-variables.css` - CSS custom properties
- `/assets/css/luxury-theme.css` - Global luxury styling
- `/assets/css/collection-colors.css` - Collection-specific overrides

### Collection-Specific Files
- `/assets/css/signature-collection.css`
- `/assets/css/black-rose-collection.css`
- `/assets/css/love-hurts-collection.css`
- `/assets/css/preorder-collection.css`

### Enqueue Function
- `/inc/enqueue-brand-styles.php` - Loads all brand CSS files

---

## Typography

### Font Families
- **Headings:** Playfair Display, Didot, Bodoni (serif)
- **Body:** Montserrat, Futura, Avenir (sans-serif)
- **Accent:** Cormorant Garamond (serif)

### Font Weights
- Light: 300
- Regular: 400
- Medium: 500
- Semibold: 600
- Bold: 700

---

## Luxury Effects

### Shadows
```css
--shadow-gold: 0 4px 16px rgba(212, 175, 55, 0.3);
--shadow-rose: 0 4px 16px rgba(183, 110, 121, 0.3);
--shadow-silver: 0 4px 16px rgba(192, 192, 192, 0.3);
```

### Glows
```css
--glow-gold: 0 0 20px rgba(212, 175, 55, 0.5);
--glow-rose: 0 0 20px rgba(183, 110, 121, 0.5);
--glow-dusty-pink: 0 0 20px rgba(216, 167, 177, 0.5);
```

### Transitions
```css
--transition-luxury: 600ms cubic-bezier(0.4, 0, 0.2, 1);
```

---

## Usage Guidelines

### Product Hotspots
Use collection-specific primary color with radial gradients and matching glow effects.

### Buttons & CTAs
Use collection gradient backgrounds with primary color borders.

### Loading Screens
Match collection background gradient with appropriate text colors.

### Modals
Light collections (Signature): White background with colored borders
Dark collections (Black Rose, Love Hurts): Dark semi-transparent with glowing borders

---

**Last Updated:** 2026-02-09
**Version:** 1.0.0
