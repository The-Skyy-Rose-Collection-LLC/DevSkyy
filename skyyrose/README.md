# 🌹 SkyyRose - Immersive Luxury Fashion Experience

## Overview

SkyyRose is an immersive virtual showroom experience for luxury fashion brand SkyyRose. Users explore three themed rooms (The Garden, The Ballroom, The Runway), each showcasing different collections through interactive product hotspots.

**Current Status:** Phase 1 - Foundation & Performance (In Progress)

## Project Structure

```
skyyrose/
├── index.html                 # Main HTML structure
├── package.json              # Build dependencies
├── README.md                 # This file
├── assets/
│   ├── css/
│   │   └── styles.css       # Luxury dark theme styles
│   ├── js/
│   │   ├── config.js        # Product data (16 products)
│   │   └── app.js           # Main application logic
│   └── images/
│       ├── scenes/          # Scene images (optimized)
│       │   └── source/      # Source images (to be added)
│       └── products/        # Product images (to be added)
└── build/
    ├── optimize-images.js   # Image optimization pipeline
    └── generate-alt-text.js # Gemini AI alt text (Phase 4)
```

## Features

### ✅ Implemented (Phase 1)

- **Semantic HTML5 Structure**
  - Proper ARIA labels and roles
  - Screen reader support
  - Skip links for accessibility

- **Luxury Dark Theme**
  - Color palette: Deep blacks, rose accents, gold highlights
  - Typography: Bebas Neue (display), Cormorant Garamond (editorial), Inter (body)
  - Smooth animations with `cubic-bezier` easing

- **Navigation System**
  - Explore sidebar with collection list
  - Arrow navigation (left/right)
  - Pip navigation (bottom bar)
  - Keyboard shortcuts (← → keys, 1-3 for rooms, ESC)

- **Product Hotspots**
  - Animated pulse effect
  - Hover labels
  - Click to open modal

- **Product Modal**
  - Full product details
  - Price, description, specifications
  - Product variants (size, color)
  - Add to Cart / Pre-Order buttons

- **Accessibility**
  - Focus-visible rose outlines
  - Reduced motion support
  - Screen reader announcements
  - Focus trap in modal
  - Keyboard navigation

### 🚧 In Progress (Phase 1)

- **Image Optimization Pipeline**
  - Sharp-based optimization script created
  - Converts to WebP + JPEG fallback
  - Generates mobile versions (50% scale)
  - Target: 48% file size reduction

### 📋 Planned

- **Phase 2:** Service Worker & Offline Support
- **Phase 3:** WordPress/WooCommerce Integration
- **Phase 4:** Gemini AI Enhancement (alt text generation)
- **Phase 5:** Enhanced Features (swipe, wishlist, analytics, animated avatar)

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Source images for the three scenes

### Installation

```bash
# Install dependencies
npm install

# Add source images to:
# - assets/images/scenes/source/black-rose-source.jpg
# - assets/images/scenes/source/love-hurts-source.jpg
# - assets/images/scenes/source/signature-source.jpg

# Optimize images
npm run build:images

# Serve locally
npm run dev
```

### Required Source Images

To complete the build, add high-quality scene images (recommended 2560x1440 or higher):

1. **Black Rose (The Garden)**
   - Theme: Gothic romance, dark florals
   - Mood: Mystery, elegance
   - Color: Rose accent (#B76E79)

2. **Love Hurts (The Ballroom)**
   - Theme: Dramatic, passionate, edgy
   - Mood: Bold, provocative
   - Color: Blood red accent (#8B0000)

3. **Signature (The Runway)**
   - Theme: High fashion, editorial
   - Mood: Luxury, prestige
   - Color: Gold accent (#D4AF37)

Place source files in: `assets/images/scenes/source/`

## Collections & Products

### BLACK ROSE Collection (6 products)
- Black Rose Tee - $85
- Rose Garden Dress - $245
- Thorn Leather Jacket - $595
- Midnight Bloom Pants - $165
- Gothic Rose Boots - $425
- Rose Petal Scarf - $135

### LOVE HURTS Collection (5 products)
- Blood Rose Corset - $325
- Heartbreak Leather Pants - $475
- Thorn Crown Headpiece - $285
- Bleeding Heart Ring - $195
- Passion Killer Heels - $525

### SIGNATURE Collection (5 products)
- Golden Hour Gown - $1,295
- Executive Power Blazer - $645
- Dynasty Handbag - $1,450
- Prestige Watch - $3,995
- Empress Sunglasses - $425

## Performance Targets

| Metric | Before | After | Status |
|--------|--------|-------|--------|
| Initial Load | 1.1MB | 230KB | 🚧 In Progress |
| Time to Interactive (4G) | 3-4s | <1s | 📋 Planned |
| Repeat Visit Load | 3-4s | <100ms | 📋 Planned |
| Mobile Load (3G) | 8-10s | 2-3s | 📋 Planned |
| Lighthouse Performance | ~60 | >90 | 📋 Planned |

## Technology Stack

- **Frontend:** Vanilla JavaScript (no frameworks)
- **Styling:** CSS3 with CSS Variables
- **Fonts:** Google Fonts (Bebas Neue, Cormorant Garamond, Inter)
- **Build:** Node.js, Sharp for image optimization
- **Future:** WordPress REST API, WooCommerce, Gemini AI

## Browser Support

- Chrome (recommended)
- Safari 14+
- Firefox
- Edge

Fallbacks provided for:
- WebP → JPEG
- Service Worker (graceful degradation)
- Modern CSS features (progressive enhancement)

## Accessibility

**WCAG 2.1 AA Compliance:**
- ✅ Keyboard navigation
- ✅ Screen reader support
- ✅ Focus indicators
- ✅ ARIA labels
- ✅ Reduced motion support
- ✅ Semantic HTML

## Development Roadmap

### Phase 1: Foundation & Performance (Week 1) - Current
- [x] Extract HTML structure
- [x] Create CSS with luxury dark theme
- [x] Build JavaScript application
- [x] Create product configuration
- [x] Set up build pipeline
- [ ] Add source images
- [ ] Optimize images
- [ ] Implement progressive loading

### Phase 2: Service Worker (Week 1-2)
- [ ] Create service worker
- [ ] Implement caching strategy
- [ ] Add offline support
- [ ] Version management

### Phase 3: WordPress Integration (Week 2)
- [ ] Build WordPress REST API client
- [ ] Dynamic product loading
- [ ] WooCommerce cart integration
- [ ] Product variant handling

### Phase 4: AI Enhancement (Week 3)
- [ ] Accessibility features
- [ ] Gemini alt text generation
- [ ] Enhanced focus management
- [ ] Screen reader optimization

### Phase 5: Advanced Features (Week 3-4)
- [ ] Swipe gestures (mobile)
- [ ] Wishlist with localStorage
- [ ] Social sharing
- [ ] Analytics integration (GA4)
- [ ] Animated avatar assistant with Gemini AI

## License

UNLICENSED - Private project for SkyyRose brand

## Support

For issues or questions, contact the development team.
