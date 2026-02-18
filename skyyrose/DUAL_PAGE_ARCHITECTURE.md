# SkyyRose Dual-Page Architecture
## 3D Immersive Experience + Traditional Landing Pages

---

## Architecture Overview

Each collection has **TWO complementary pages** that work together:

### 1. **3D Immersive Page** (Interactive Product Discovery)
- Full-screen scene with interactive hotspots
- Click hotspots to discover products organically
- Modal pop-ups with product details
- Original concept from `SKYYROSE_EXPERIENCE_ANALYSIS.md`
- **URLs:** `/explore/black-rose.html`, `/explore/love-hurts.html`, `/explore/signature.html`

### 2. **Landing Page** (Traditional E-Commerce)
- Hero section with collection branding
- Product grid with all items
- Quick view and add to cart
- SEO-optimized content
- **URLs:** `/collections/black-rose.html`, `/collections/love-hurts.html`, `/collections/signature.html`

---

## Page Structure

```
skyyrose.co/
├── index.html                          # Homepage (collection selector)
│
├── explore/                            # 3D IMMERSIVE PAGES
│   ├── black-rose.html                # BLACK ROSE 3D scene
│   ├── love-hurts.html                # LOVE HURTS 3D scene
│   └── signature.html                 # SIGNATURE 3D scene
│
├── collections/                        # LANDING PAGES
│   ├── black-rose.html                # BLACK ROSE traditional grid
│   ├── love-hurts.html                # LOVE HURTS traditional grid
│   └── signature.html                 # SIGNATURE traditional grid
│
└── shop.html                           # All products across collections
```

---

## User Journey Flow

### Entry Point: Homepage

```
[Homepage]
   ↓
[Collection Card Clicked]
   ↓
[CHOICE: 3D Experience OR Traditional Grid]
```

### Option 1: Explore First (Discovery-Driven)

```
Homepage → 3D Immersive Page → Click Hotspot → Product Modal → Add to Cart
                                    ↓
                            [View Full Collection Button]
                                    ↓
                            Landing Page (Grid View)
```

### Option 2: Browse First (Product-Driven)

```
Homepage → Landing Page (Grid) → Browse Products → Quick View → Add to Cart
               ↓
        [Experience Collection in 3D Button]
               ↓
        3D Immersive Page (Discovery)
```

---

## Navigation Flow

### Homepage to Collection

**Collection Card** should offer BOTH entry points:

```html
<article class="collection-card collection-black-rose">
  <div class="card-content">
    <h3>BLACK ROSE</h3>
    <p>Gothic romance meets dark florals</p>

    <!-- TWO CTAs -->
    <div class="card-actions">
      <a href="/explore/black-rose.html" class="btn-explore">
        🌹 Explore in 3D
      </a>
      <a href="/collections/black-rose.html" class="btn-browse">
        📋 Browse Collection
      </a>
    </div>
  </div>
</article>
```

### Cross-Linking Between Pages

**3D Immersive Page** → **Landing Page**

```html
<!-- Fixed CTA in 3D page -->
<a href="/collections/black-rose.html" class="view-full-collection-btn">
  View Full Collection Grid
</a>
```

**Landing Page** → **3D Immersive Page**

```html
<!-- Hero section CTA -->
<div class="hero-actions">
  <a href="/explore/black-rose.html" class="btn-explore-3d">
    Experience in 3D
  </a>
  <a href="#products" class="btn-browse">
    Browse Products
  </a>
</div>
```

---

## File Implementation

### 3D Immersive Pages

**Structure:**
```html
<!DOCTYPE html>
<html lang="en" data-experience="3d-immersive" data-collection="black-rose">
<head>
  <title>Explore BLACK ROSE in 3D | SkyyRose</title>
  <link rel="stylesheet" href="../assets/css/base-v2.css">
  <link rel="stylesheet" href="../assets/css/3d-experience.css">
  <link rel="stylesheet" href="../assets/css/collections/black-rose.css">
</head>
<body class="immersive-experience">

  <!-- Skip to products for accessibility -->
  <a href="/collections/black-rose.html" class="skip-link">
    Skip to Traditional View
  </a>

  <!-- Full-screen scene with hotspots -->
  <div id="scene-container" class="scene-black-rose">
    <img src="../assets/images/scenes/black-rose.jpg" alt="Gothic garden showroom">

    <!-- Product hotspots -->
    <button class="hotspot" data-product="br-001" style="left: 25%; top: 40%;">
      <span class="hotspot-pulse"></span>
      <span class="hotspot-label">Black Rose Tee</span>
    </button>
    <!-- More hotspots... -->
  </div>

  <!-- Navigation controls -->
  <nav class="scene-nav">
    <a href="black-rose.html" class="active">The Garden</a>
    <a href="love-hurts.html">The Ballroom</a>
    <a href="signature.html">The Runway</a>
  </nav>

  <!-- CTA to landing page -->
  <a href="/collections/black-rose.html" class="view-grid-btn">
    View Full Collection
  </a>

  <!-- Product modal (shared component) -->
  <div id="product-modal" class="modal">
    <!-- Product details, add to cart, etc. -->
  </div>

  <script src="../assets/js/3d-experience.js"></script>
</body>
</html>
```

### Landing Pages

**Already Created:** `/collections/black-rose.html`

Contains:
- Hero section with collection logo
- Collection story
- Product grid (6 products)
- Cross-sell to other collections
- CTA to 3D experience page

---

## CSS Architecture

### Shared Styles

```css
/* Base luxury styles (all pages) */
base-v2.css

/* Collection-specific variables */
collections/black-rose.css
collections/love-hurts.css
collections/signature.css
```

### Page-Specific Styles

```css
/* 3D immersive pages */
3d-experience.css
  - Full-screen scene container
  - Hotspot animations
  - Scene navigation
  - Product modal overlay

/* Landing pages */
homepage.css (for main index)
collection-landing.css (if needed)
  - Product grid
  - Quick view buttons
  - Filter/sort UI
```

---

## JavaScript Architecture

### 3D Immersive Page

```javascript
// assets/js/3d-experience.js

class ImmersiveExperience {
  constructor() {
    this.currentScene = 'black-rose';
    this.hotspots = [];
    this.products = [];
  }

  // Load scene and hotspots
  init() {
    this.loadScene(this.currentScene);
    this.renderHotspots();
    this.attachEventListeners();
  }

  // Hotspot interaction
  onHotspotClick(productId) {
    this.openProductModal(productId);
  }

  // Product modal
  openProductModal(productId) {
    const product = this.getProduct(productId);
    this.renderModal(product);

    // Track analytics
    gtag('event', 'product_view_3d', {
      product_id: productId,
      collection: this.currentScene
    });
  }

  // Navigate to landing page
  viewFullCollection() {
    window.location.href = `/collections/${this.currentScene}.html`;
  }
}

// Initialize
const experience = new ImmersiveExperience();
experience.init();
```

### Landing Page

```javascript
// assets/js/collection.js

class CollectionPage {
  constructor() {
    this.products = [];
    this.wishlist = [];
    this.filters = {
      size: null,
      priceRange: null,
      sortBy: 'featured'
    };
  }

  init() {
    this.loadProducts();
    this.renderGrid();
    this.attachEventListeners();
  }

  // Quick view modal
  quickView(productId) {
    const product = this.getProduct(productId);
    this.renderQuickViewModal(product);
  }

  // Add to cart
  addToCart(productId, variant) {
    // WooCommerce integration
    this.wpClient.addToCart(productId, variant);
  }

  // Wishlist toggle
  toggleWishlist(productId) {
    const isInWishlist = this.wishlist.includes(productId);
    if (isInWishlist) {
      this.removeFromWishlist(productId);
    } else {
      this.addToWishlist(productId);
    }
  }

  // Navigate to 3D experience
  explore3D() {
    const collection = document.documentElement.dataset.collection;
    window.location.href = `/explore/${collection}.html`;
  }
}

// Initialize
const collectionPage = new CollectionPage();
collectionPage.init();
```

---

## Serena & Context7 Integration

### Serena AI Assistant

**Placement:** Both 3D and Landing pages

```html
<!-- Serena floating avatar (bottom-right) -->
<div id="serena-assistant" class="ai-assistant">
  <button class="assistant-avatar" aria-label="Chat with Serena">
    <img src="/assets/images/serena/avatar.png" alt="Serena AI Assistant">
    <span class="assistant-status online"></span>
  </button>

  <div class="assistant-chat-bubble" hidden>
    <div class="chat-messages"></div>
    <input type="text" placeholder="Ask about products...">
  </div>
</div>

<script src="/assets/js/serena-ai.js"></script>
```

**Functionality:**

```javascript
// assets/js/serena-ai.js

class SerenaAssistant {
  constructor() {
    this.geminiClient = new GeminiClient();
    this.context = {
      page: document.documentElement.dataset.experience || 'landing',
      collection: document.documentElement.dataset.collection,
      viewedProducts: [],
      cartItems: []
    };
  }

  async chat(userMessage) {
    // Context-aware responses
    const systemPrompt = `
      You are Serena, the AI fashion assistant for SkyyRose luxury brand.

      Current context:
      - Page: ${this.context.page}
      - Collection: ${this.context.collection}
      - User is viewing: ${this.context.viewedProducts.join(', ')}

      Provide helpful, personalized product recommendations.
      Be sophisticated, knowledgeable, and enthusiastic about luxury fashion.
    `;

    const response = await this.geminiClient.generateContent({
      model: 'gemini-3-flash-preview',
      prompt: systemPrompt + '\n\nUser: ' + userMessage
    });

    return response.text;
  }

  // Proactive suggestions
  suggest() {
    if (this.context.viewedProducts.length >= 3) {
      this.showBubble('I notice you love gothic elegance! Would you like to see the Thorn Leather Jacket?');
    }
  }
}
```

### Context7 Documentation

**Knowledge Base Integration:**

```javascript
// assets/js/context7-integration.js

class Context7 {
  constructor() {
    this.knowledgeBase = {
      collections: {},
      products: {},
      sizing: {},
      careInstructions: {}
    };
  }

  // Load documentation from Context7
  async loadKnowledge() {
    const response = await fetch('/api/context7/knowledge-base.json');
    this.knowledgeBase = await response.json();
  }

  // Search for answers
  search(query) {
    // Semantic search through documentation
    // Return relevant snippets for Serena to use
  }

  // Product-specific help
  getProductInfo(productId) {
    return this.knowledgeBase.products[productId];
  }
}
```

**Documentation Structure:**

```
/docs/
├── context7/
│   ├── collections/
│   │   ├── black-rose.md         # Collection philosophy, story
│   │   ├── love-hurts.md
│   │   └── signature.md
│   ├── products/
│   │   ├── br-001.md             # Product details, materials, care
│   │   ├── br-002.md
│   │   └── ...
│   ├── sizing-guide.md
│   ├── care-instructions.md
│   └── faq.md
```

---

## Mobile Responsiveness

### 3D Immersive (Mobile)

```css
@media (max-width: 768px) {
  /* Scale scene for mobile */
  .scene-container {
    height: 100vh;
    overflow-x: hidden;
  }

  /* Larger hotspot touch targets */
  .hotspot {
    width: 60px;
    height: 60px;
  }

  /* Swipe gestures between scenes */
  .scene-container {
    touch-action: pan-x;
  }
}
```

### Landing Page (Mobile)

```css
@media (max-width: 768px) {
  /* Single column product grid */
  .products-grid {
    grid-template-columns: 1fr;
  }

  /* Sticky "Explore in 3D" button */
  .btn-explore-3d {
    position: fixed;
    bottom: 80px;
    right: 20px;
    z-index: 100;
  }
}
```

---

## SEO Strategy

### 3D Immersive Pages

```html
<head>
  <title>Explore BLACK ROSE Collection in Immersive 3D | SkyyRose</title>
  <meta name="description" content="Discover the BLACK ROSE Collection through an immersive 3D virtual showroom experience. Click product hotspots to explore gothic luxury fashion.">
  <meta name="robots" content="index, follow">

  <!-- Canonical points to landing page (main version) -->
  <link rel="canonical" href="https://skyyrose.co/collections/black-rose.html">

  <!-- Alternate for traditional experience -->
  <link rel="alternate" href="https://skyyrose.co/collections/black-rose.html" title="Traditional View">
</head>
```

### Landing Pages

```html
<head>
  <title>BLACK ROSE Collection | Gothic Luxury Fashion | SkyyRose</title>
  <meta name="description" content="Shop the BLACK ROSE Collection: 6 pieces of gothic luxury fashion. Black Rose Tee, Rose Garden Dress, Thorn Leather Jacket. Free shipping over $200.">
  <meta name="robots" content="index, follow">

  <!-- This is the canonical version -->
  <link rel="canonical" href="https://skyyrose.co/collections/black-rose.html">

  <!-- Alternate for immersive experience -->
  <link rel="alternate" href="https://skyyrose.co/explore/black-rose.html" title="3D Experience">

  <!-- Structured data for products -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": "BLACK ROSE Collection",
    "description": "Gothic romance meets dark florals",
    "url": "https://skyyrose.co/collections/black-rose.html",
    "itemListElement": [...]
  }
  </script>
</head>
```

---

## Analytics Tracking

### Events to Track

```javascript
// 3D Immersive Page
gtag('event', 'experience_enter', {
  experience_type: '3d_immersive',
  collection: 'black-rose'
});

gtag('event', 'hotspot_click', {
  product_id: 'br-001',
  collection: 'black-rose',
  position: { x: 0.25, y: 0.40 }
});

// Landing Page
gtag('event', 'collection_view', {
  collection: 'black-rose',
  view_type: 'grid'
});

gtag('event', 'product_quick_view', {
  product_id: 'br-001'
});

// Cross-navigation
gtag('event', 'navigate_3d_to_grid', {
  collection: 'black-rose',
  products_viewed: ['br-001', 'br-003']
});

gtag('event', 'navigate_grid_to_3d', {
  collection: 'black-rose'
});
```

---

## Next Steps

### Immediate Tasks

1. ✅ **Homepage** (`index-v2.html`) - COMPLETE
2. ✅ **Landing Page Template** (`collections/black-rose.html`) - COMPLETE
3. ⏳ **3D Immersive Page** (`explore/black-rose.html`) - TO CREATE
4. ⏳ **3D Experience CSS** (`assets/css/3d-experience.css`) - TO CREATE
5. ⏳ **3D Experience JS** (`assets/js/3d-experience.js`) - TO CREATE
6. ⏳ **Collection JS** (`assets/js/collection.js`) - TO CREATE
7. ⏳ **Serena AI Integration** (`assets/js/serena-ai.js`) - TO CREATE
8. ⏳ **Context7 Knowledge Base** (`docs/context7/`) - TO CREATE

### Build Sequence

```bash
# 1. Optimize logos
npm run build:logos

# 2. Generate product images with Gemini
npm run generate:models

# 3. Optimize all images
npm run build:images

# 4. Test dual-page navigation
# - Homepage → 3D → Landing → Back to 3D
# - Homepage → Landing → 3D → Back to Landing

# 5. Deploy and verify
```

---

## User Testing Checklist

### 3D Immersive Page
- [ ] Scene loads within 2 seconds
- [ ] Hotspots are visible and clickable
- [ ] Modal opens with product details
- [ ] "View Full Collection" button works
- [ ] Keyboard navigation functional
- [ ] Touch gestures work on mobile

### Landing Page
- [ ] Hero section loads instantly
- [ ] Product grid renders correctly
- [ ] Quick view modals work
- [ ] Add to cart functional
- [ ] "Explore in 3D" button works
- [ ] Wishlist toggle persists

### Cross-Navigation
- [ ] Smooth transitions between pages
- [ ] Context preserved (viewed products)
- [ ] Analytics track page flows
- [ ] Back button works correctly

### Serena AI
- [ ] Avatar loads and animates
- [ ] Chat responds in <2 seconds
- [ ] Recommendations are relevant
- [ ] Works on both page types

---

**Architecture Status:** Ready for implementation
**Next Action:** Create 3D immersive pages for each collection
