# SkyyRose Spinning Logo - Quick Start Guide

## 🎯 Quick Usage

### Option 1: PHP Function (Recommended)
```php
<?php skyyrose_spinning_logo(); ?>
```

### Option 2: Shortcode (Elementor/Page Builders)
```
[skyyrose_spinning_logo]
[skyyrose_spinning_logo variant="silver"]
```

### Option 3: Complete Header
```php
<?php skyyrose_header_with_spinning_logo(); ?>
```

---

## 📦 Installation

### Already Integrated!
The spinning logo is already set up in the SkyyRose Immersive theme. Just add this line to `functions.php`:

```php
require_once SKYYROSE_IMMERSIVE_DIR . '/inc/spinning-logo-functions.php';
```

---

## 🎨 Color Variants (Auto-Detected)

| Page | Color | Preview |
|------|-------|---------|
| Homepage | Gold (#D4AF37) | Default luxury |
| Black Rose | Silver (#C0C0C0) | Icy metallic |
| Love Hurts | Deep Rose (#D4A5A5) | Warm emotional |
| Signature | Rose Gold (#B76E79) | Premium elegant |

**Manual Override:**
```php
[skyyrose_spinning_logo variant="rose-gold"]
```

---

## ⚙️ Animation Settings

- **Spin Duration**: 8 seconds
- **Rotation**: Continuous, linear
- **Hover**: Pauses elegantly
- **Glow**: Intensifies on hover
- **Size**: 60px (desktop), 48px (mobile)

---

## 📁 Files Created

```
wordpress/skyyrose-immersive/
├── assets/
│   ├── css/spinning-logo.css          # Standalone CSS
│   ├── js/header.js                   # Scroll behavior
│   └── images/skyyrose-logo-spinner.svg # Logo SVG
└── inc/spinning-logo-functions.php    # PHP functions
```

---

## 🚀 Quick Customization

### Change Spin Speed
```css
.skyyrose-logo__spinner {
  animation-duration: 5s; /* Faster */
}
```

### Disable Hover Pause
```css
.skyyrose-logo:hover .skyyrose-logo__spinner {
  animation-play-state: running;
}
```

### Add Custom Color
```css
.skyyrose-logo--custom .skyyrose-logo__spinner path {
  fill: #FF6B9D;
}
```

---

## 🔧 Troubleshooting

### Logo Not Spinning?
1. Check CSS is loaded: View Source → Search "spinning-logo.css"
2. Verify SVG path is correct
3. Check browser console for errors

### Wrong Color?
1. Check page type: `echo skyyrose_get_logo_variant();`
2. Verify body classes match collection slugs
3. Use manual override if needed

---

## 📖 Full Documentation

See: `.serena/memories/spinning_logo_implementation.md`

---

## ✨ Features

✅ Theme-agnostic (easy to migrate)  
✅ No external dependencies  
✅ Responsive (desktop/mobile)  
✅ Accessibility compliant  
✅ Elementor compatible  
✅ Auto color detection  
✅ Smooth animations  
✅ Performance optimized  

---

**Version**: 1.0.0  
**Author**: SkyyRose LLC  
**Support**: support@skyyrose.com