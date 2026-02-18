# SkyyRose - Revised Architecture (Multi-Page Luxury Experience)

## Critical Changes

### 1. Multi-Page Structure (SEO + UX)

```
skyyrose.co/
├── index.html                    # Homepage (collection selector)
├── collections/
│   ├── black-rose.html          # BLACK ROSE landing page
│   ├── love-hurts.html          # LOVE HURTS landing page
│   └── signature.html           # SIGNATURE landing page
├── product.html                 # Dynamic product page template
└── shop.html                    # All products grid
```

**Benefits:**
- Each collection gets unique URL (SEO)
- Share-able collection pages
- Distinct branding per collection
- Better WordPress integration
- Analytics per collection

### 2. Enhanced Typography System

**Current Issues:**
- Bebas Neue: Too sporty, not luxury
- Cormorant Garamond: Good but underutilized
- Inter: Too tech, not editorial

**Luxury Font Upgrade:**

```css
/* PRIMARY: Ultra-luxury serif for headlines */
--font-display: 'Playfair Display', 'Cormorant Garamond', serif;
--font-weight-display: 700; /* Bold for impact */

/* SECONDARY: Elegant serif for product names */
--font-editorial: 'Cormorant Garamond', Georgia, serif;
--font-weight-editorial: 600; /* Semi-bold */

/* TERTIARY: Premium sans for body */
--font-body: 'Montserrat', 'Inter', sans-serif;
--font-weight-body: 400;

/* ACCENT: Luxury script for special elements */
--font-script: 'Great Vibes', cursive; /* Signature elements */
```

**Font Sizing (Luxury Scale):**
```css
/* Massive hero headlines */
--text-hero: clamp(4rem, 10vw, 8rem);      /* 64-128px */

/* Collection titles */
--text-display: clamp(3rem, 8vw, 6rem);    /* 48-96px */

/* Product names */
--text-title: clamp(2rem, 5vw, 3.5rem);    /* 32-56px */

/* Body text (highly readable) */
--text-body: clamp(1.125rem, 2vw, 1.25rem); /* 18-20px */

/* Luxury needs generous spacing */
letter-spacing: 0.05em; /* Airy, breathable */
line-height: 1.6;       /* Comfortable reading */
```

### 3. Brand Color System (Dynamic Per Collection)

**Homepage:** Unified luxury palette
```css
--primary: #0A0A0A;      /* Deep void */
--accent: #B76E79;       /* Rose (default) */
--gold: #D4AF37;         /* Prestige */
--highlight: #FFFFFF;    /* Pure white */
```

**BLACK ROSE Page:** Rose-dominant
```css
--collection-primary: #B76E79;    /* Rose */
--collection-secondary: #8B4556;  /* Deep rose */
--collection-accent: #E8A5B2;     /* Light rose */
--gradient: linear-gradient(135deg, #B76E79, #8B4556);
```

**LOVE HURTS Page:** Blood-dominant
```css
--collection-primary: #8B0000;    /* Blood red */
--collection-secondary: #5C0000;  /* Dark blood */
--collection-accent: #C41E3A;     /* Crimson */
--gradient: linear-gradient(135deg, #8B0000, #5C0000);
```

**SIGNATURE Page:** Gold-dominant
```css
--collection-primary: #D4AF37;    /* Gold */
--collection-secondary: #B8941E;  /* Dark gold */
--collection-accent: #FFD700;     /* Bright gold */
--gradient: linear-gradient(135deg, #D4AF37, #B8941E);
```

### 4. Gemini AI Integration for Product Models

**Use Cases:**

**A. Generate Product Images**
```javascript
// Use Gemini 3 Pro Image to generate product mockups
async function generateProductImage(product) {
  const prompt = `
    Create a luxury fashion product photo for:
    Product: ${product.name}
    Style: ${product.collection} - ${product.description}
    Setting: ${product.collection === 'BLACK ROSE' ? 'Gothic garden with dark roses' :
              product.collection === 'LOVE HURTS' ? 'Dramatic ballroom with red lighting' :
              'Minimalist runway with golden accents'}
    Quality: High-end editorial photography, professional lighting, sharp details
    Resolution: 2048x2048, magazine quality
  `;

  const result = await geminiClient.generateImage({
    model: 'gemini-3-pro-image-preview',
    prompt: prompt,
    aspectRatio: '1:1'
  });

  return result.image;
}
```

**B. Generate Scene Backgrounds**
```javascript
// Generate immersive scene backgrounds
async function generateSceneImage(collection) {
  const scenePrompts = {
    'BLACK ROSE': `
      Luxury gothic garden showroom with black roses, elegant dark florals,
      moody atmospheric lighting, high-end boutique interior, editorial photography,
      mysterious and romantic ambiance, ultra-high resolution 4K
    `,
    'LOVE HURTS': `
      Dramatic luxury ballroom with deep red lighting, passionate atmosphere,
      crystal chandeliers, elegant drapery, high-fashion setting,
      bold and provocative mood, editorial quality 4K
    `,
    'SIGNATURE': `
      Minimalist high-fashion runway with golden accents, prestige luxury setting,
      clean lines, marble floors, museum-quality lighting,
      editorial excellence, ultra-premium 4K resolution
    `
  };

  const result = await geminiClient.generateImage({
    model: 'gemini-3-pro-image-preview',
    prompt: scenePrompts[collection],
    aspectRatio: '16:9'
  });

  return result.image;
}
```

**C. AI-Powered Product Descriptions**
```javascript
// Generate luxury product copy
async function generateProductCopy(product) {
  const prompt = `
    Write luxury fashion product copy for:

    Product: ${product.name}
    Collection: ${product.collection}
    Price: ${product.price}
    Features: ${product.spec}

    Style: Aspirational, exclusive, editorial tone
    Target: High-end luxury fashion consumers
    Length: 2-3 sentences
    Tone: Sophisticated, evocative, desire-driven
  `;

  const result = await geminiClient.generateContent({
    model: 'gemini-3-pro-preview',
    prompt: prompt
  });

  return result.text;
}
```

### 5. Page Structure (Each Collection)

**Example: black-rose.html**
```html
<!DOCTYPE html>
<html lang="en" data-collection="black-rose">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BLACK ROSE Collection | SkyyRose</title>

  <!-- Luxury Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;900&family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Montserrat:wght@300;400;500;600&family=Great+Vibes&display=swap" rel="stylesheet">

  <!-- Collection-specific CSS -->
  <link rel="stylesheet" href="../assets/css/base.css">
  <link rel="stylesheet" href="../assets/css/collections/black-rose.css">
</head>
<body class="collection-black-rose">

  <!-- Full-screen Hero -->
  <section class="hero" role="banner">
    <div class="hero-background">
      <!-- Gemini-generated scene image -->
      <picture>
        <source srcset="assets/images/scenes/black-rose.webp" type="image/webp">
        <img src="assets/images/scenes/black-rose.jpg" alt="BLACK ROSE Collection - Gothic luxury garden">
      </picture>
    </div>

    <div class="hero-content">
      <h1 class="hero-title">
        <span class="collection-name">BLACK ROSE</span>
        <span class="collection-tagline">Where darkness blooms</span>
      </h1>

      <p class="hero-description">
        Gothic romance meets dark florals in our most enigmatic collection.
        6 pieces of wearable art that celebrate mystery and elegance.
      </p>

      <div class="hero-actions">
        <a href="#products" class="btn btn-primary">Explore Collection</a>
        <a href="/shop.html" class="btn btn-secondary">Shop All</a>
      </div>
    </div>

    <!-- Scroll indicator -->
    <div class="scroll-indicator">
      <span>Scroll to explore</span>
      <div class="scroll-arrow"></div>
    </div>
  </section>

  <!-- Product Grid (with hotspots alternative) -->
  <section id="products" class="products">
    <div class="container">
      <h2 class="section-title">The Collection</h2>

      <div class="product-grid">
        <!-- 6 products, each with Gemini-generated images -->
        <article class="product-card">
          <div class="product-image">
            <img src="assets/images/products/black-rose-tee.jpg" alt="Black Rose Tee">
            <span class="product-badge">BESTSELLER</span>
          </div>
          <div class="product-info">
            <h3 class="product-name">Black Rose Tee</h3>
            <p class="product-tagline">Gothic elegance meets street style</p>
            <span class="product-price">$85</span>
            <button class="btn-quick-view">Quick View</button>
          </div>
        </article>
        <!-- Repeat for 6 products -->
      </div>
    </div>
  </section>

  <!-- Collection Story -->
  <section class="collection-story">
    <div class="container">
      <div class="story-content">
        <h2>The Garden</h2>
        <p>
          In the shadows of midnight, roses bloom darker than obsidian.
          This collection celebrates the beauty found in darkness,
          where gothic romance meets modern luxury.
        </p>
      </div>
    </div>
  </section>

  <!-- Cross-sell: Other Collections -->
  <section class="other-collections">
    <h2>Explore More</h2>
    <div class="collection-cards">
      <a href="love-hurts.html" class="collection-card collection-card-love-hurts">
        <span class="card-title">LOVE HURTS</span>
      </a>
      <a href="signature.html" class="collection-card collection-card-signature">
        <span class="card-title">SIGNATURE</span>
      </a>
    </div>
  </section>

</body>
</html>
```

### 6. Revised File Structure

```
skyyrose/
├── index.html                       # Homepage (collection selector)
├── collections/
│   ├── black-rose.html
│   ├── love-hurts.html
│   └── signature.html
├── shop.html                        # All products
├── product.html                     # Product template
├── assets/
│   ├── css/
│   │   ├── base.css                # Shared luxury styles
│   │   ├── typography.css          # Font system
│   │   ├── components.css          # Buttons, cards, modals
│   │   └── collections/
│   │       ├── black-rose.css      # Rose theme
│   │       ├── love-hurts.css      # Blood theme
│   │       └── signature.css       # Gold theme
│   ├── js/
│   │   ├── app.js                  # Main application
│   │   ├── wordpress-client.js     # WooCommerce API
│   │   ├── gemini-client.js        # Gemini AI integration
│   │   └── components/
│   │       ├── product-modal.js
│   │       ├── cart.js
│   │       └── wishlist.js
│   └── images/
│       ├── scenes/                 # Gemini-generated
│       └── products/               # Gemini-generated
└── build/
    ├── optimize-images.js
    └── generate-content.js         # Gemini content generation
```

### 7. Testing Checklist

**Visual Quality:**
- [ ] Fonts render beautifully at all sizes
- [ ] Color gradients smooth and luxury-grade
- [ ] Images high-resolution (2x retina)
- [ ] Spacing generous (luxury = space)
- [ ] Animations smooth 60fps

**Functionality:**
- [ ] Navigation flows between collections
- [ ] Product modals work perfectly
- [ ] Cart integration functional
- [ ] Mobile responsive (touch-optimized)
- [ ] Fast load times (<2s 4G)

**Brand Experience:**
- [ ] Each collection feels distinct
- [ ] Color themes immersive
- [ ] Typography hierarchy clear
- [ ] Luxury feel throughout
- [ ] Professional polish

### 8. Immediate Actions Required

1. **Upgrade Typography**
   - Replace Bebas Neue with Playfair Display
   - Increase font sizes (luxury = generous type)
   - Add Great Vibes for signature elements

2. **Implement Multi-Page Architecture**
   - Create separate collection landing pages
   - Build homepage as collection selector
   - Add proper WordPress integration per page

3. **Enhance Color System**
   - Dynamic CSS variables per collection
   - Gradient overlays on images
   - Accent colors throughout UI

4. **Integrate Gemini AI**
   - Generate scene backgrounds
   - Create product images
   - AI-powered descriptions

5. **Test Everything**
   - Cross-browser (Chrome, Safari, Firefox)
   - Mobile devices (iOS, Android)
   - Performance (Lighthouse >90)
   - Accessibility (WCAG AA)

---

## Next Steps

Should I proceed with:
1. Creating the upgraded homepage with collection selector?
2. Building BLACK ROSE landing page with luxury typography?
3. Setting up Gemini AI integration for image generation?
4. All of the above in parallel?
