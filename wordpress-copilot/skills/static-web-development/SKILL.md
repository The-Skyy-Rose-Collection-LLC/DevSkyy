---
name: Static Web Development
description: Expert knowledge in HTML, CSS, responsive design, CSS Grid, Flexbox, modern layout techniques, and semantic markup. Triggers on keywords like "html", "css", "layout", "responsive", "grid", "flexbox", "semantic", "accessibility markup", "forms".
version: 1.0.0
---

# Static Web Development

Master modern HTML, CSS, and layout techniques for building accessible, responsive, and performant static web pages.

## When to Use This Skill

Activate when working on:
- HTML structure and semantic markup
- CSS layouts (Grid, Flexbox, positioning)
- Responsive design and media queries
- Form design and validation
- CSS animations and transitions
- Typography and spacing systems
- Print stylesheets
- Static site generation

## Modern HTML

### Semantic Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="SkyyRose - Where Love Meets Luxury">
  <title>SkyyRose | Luxury Fashion Jewelry</title>

  <!-- Open Graph -->
  <meta property="og:title" content="SkyyRose Luxury Jewelry">
  <meta property="og:description" content="Handcrafted luxury fashion jewelry">
  <meta property="og:image" content="https://skyyrose.co/og-image.jpg">
  <meta property="og:type" content="website">

  <!-- Preconnect to CDNs -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="dns-prefetch" href="https://cdn.babylonjs.com">

  <link rel="stylesheet" href="/style.css">
</head>
<body>
  <header role="banner">
    <nav role="navigation" aria-label="Main navigation">
      <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/collections">Collections</a></li>
        <li><a href="/about">About</a></li>
      </ul>
    </nav>
  </header>

  <main role="main">
    <article>
      <header>
        <h1>Signature Collection</h1>
        <time datetime="2026-02-06">February 6, 2026</time>
      </header>

      <section>
        <h2>Product Details</h2>
        <p>Handcrafted with precision...</p>
      </section>
    </article>
  </main>

  <aside role="complementary">
    <h2>Related Products</h2>
    <!-- Related content -->
  </aside>

  <footer role="contentinfo">
    <p>&copy; 2026 SkyyRose LLC. All rights reserved.</p>
  </footer>
</body>
</html>
```

### Accessible Forms

```html
<form action="/checkout" method="post" novalidate>
  <fieldset>
    <legend>Shipping Information</legend>

    <div class="form-group">
      <label for="full-name">
        Full Name <span aria-label="required">*</span>
      </label>
      <input
        type="text"
        id="full-name"
        name="full_name"
        required
        aria-required="true"
        aria-describedby="name-error"
        autocomplete="name"
      >
      <span id="name-error" class="error" aria-live="polite"></span>
    </div>

    <div class="form-group">
      <label for="email">Email Address <span aria-label="required">*</span></label>
      <input
        type="email"
        id="email"
        name="email"
        required
        aria-required="true"
        aria-describedby="email-error email-hint"
        autocomplete="email"
        inputmode="email"
      >
      <span id="email-hint" class="hint">We'll never share your email</span>
      <span id="email-error" class="error" aria-live="polite"></span>
    </div>

    <div class="form-group">
      <label for="phone">Phone Number</label>
      <input
        type="tel"
        id="phone"
        name="phone"
        autocomplete="tel"
        inputmode="tel"
        pattern="[0-9]{3}-[0-9]{3}-[0-9]{4}"
        placeholder="555-555-5555"
      >
    </div>
  </fieldset>

  <button type="submit">Place Order</button>
</form>
```

## Modern CSS

### CSS Custom Properties (Variables)

```css
:root {
  /* SkyyRose Brand Colors */
  --color-primary: #B76E79;
  --color-primary-hover: #A65E69;
  --color-secondary: #2C2C2C;
  --color-accent: #E8C5A5;

  /* Typography */
  --font-heading: 'Playfair Display', serif;
  --font-body: 'Inter', sans-serif;
  --font-size-base: 1rem;
  --font-size-lg: 1.25rem;
  --font-size-xl: 1.5rem;
  --font-size-2xl: 2rem;

  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  --spacing-2xl: 3rem;

  /* Transitions */
  --transition-fast: 150ms ease-out;
  --transition-base: 300ms ease-in-out;
  --transition-slow: 600ms cubic-bezier(0.43, 0.13, 0.23, 0.96);

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);

  /* Borders */
  --border-radius-sm: 0.25rem;
  --border-radius-md: 0.5rem;
  --border-radius-lg: 1rem;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  :root {
    --color-primary: #C98090;
    --color-secondary: #F5F5F5;
  }
}
```

### CSS Grid Layouts

```css
/* Product Grid */
.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--spacing-xl);
  padding: var(--spacing-xl);
}

/* Responsive: 1 column on mobile, 2 on tablet, 3+ on desktop */
@media (min-width: 768px) {
  .product-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  }
}

/* Collection Page Layout */
.collection-layout {
  display: grid;
  grid-template-areas:
    "header header"
    "sidebar content"
    "footer footer";
  grid-template-columns: 250px 1fr;
  grid-template-rows: auto 1fr auto;
  min-height: 100vh;
  gap: var(--spacing-xl);
}

.collection-header { grid-area: header; }
.collection-sidebar { grid-area: sidebar; }
.collection-content { grid-area: content; }
.collection-footer { grid-area: footer; }

/* Responsive: Stack on mobile */
@media (max-width: 768px) {
  .collection-layout {
    grid-template-areas:
      "header"
      "content"
      "sidebar"
      "footer";
    grid-template-columns: 1fr;
  }
}
```

### Flexbox Patterns

```css
/* Centered Container */
.container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}

/* Space Between (Header Layout) */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
}

/* Auto-Wrapping Row */
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

/* Column with Equal Spacing */
.vertical-stack {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

/* Stretch Last Item */
.sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.sidebar > :last-child {
  flex-grow: 1;
}
```

### Responsive Design

```css
/* Mobile-First Approach */
.hero {
  padding: var(--spacing-lg);
  font-size: var(--font-size-base);
}

/* Tablet */
@media (min-width: 768px) {
  .hero {
    padding: var(--spacing-xl);
    font-size: var(--font-size-lg);
  }
}

/* Desktop */
@media (min-width: 1024px) {
  .hero {
    padding: var(--spacing-2xl);
    font-size: var(--font-size-xl);
  }
}

/* Large Desktop */
@media (min-width: 1440px) {
  .hero {
    max-width: 1400px;
    margin: 0 auto;
    font-size: var(--font-size-2xl);
  }
}

/* Container Queries (Modern) */
.card-container {
  container-type: inline-size;
  container-name: card;
}

@container card (min-width: 400px) {
  .card {
    display: flex;
    flex-direction: row;
  }
}
```

### CSS Animations

```css
/* Smooth Hover Effects */
.product-card {
  transition: transform var(--transition-base);
}

.product-card:hover {
  transform: translateY(-8px);
}

/* Fade In Animation */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in {
  animation: fadeIn var(--transition-slow) ease-out;
}

/* Shimmer Loading Effect */
@keyframes shimmer {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
}

.skeleton {
  background: linear-gradient(
    90deg,
    #f0f0f0 25%,
    #e0e0e0 50%,
    #f0f0f0 75%
  );
  background-size: 2000px 100%;
  animation: shimmer 2s linear infinite;
}

/* Rose Gold Gradient */
.rose-gold-shimmer {
  background: linear-gradient(
    90deg,
    #B76E79 0%,
    #E8C5A5 50%,
    #B76E79 100%
  );
  background-size: 200% 100%;
  animation: shimmer 3s linear infinite;
}
```

### Typography

```css
/* Responsive Typography */
html {
  font-size: 16px;
}

@media (min-width: 768px) {
  html {
    font-size: 18px;
  }
}

@media (min-width: 1024px) {
  html {
    font-size: 20px;
  }
}

/* Fluid Typography */
h1 {
  font-size: clamp(2rem, 5vw + 1rem, 4rem);
  font-family: var(--font-heading);
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

/* Body Copy */
p {
  font-family: var(--font-body);
  font-size: var(--font-size-base);
  line-height: 1.6;
  color: var(--color-secondary);
  max-width: 65ch; /* Optimal reading length */
}

/* Luxury Serif Headings */
.luxury-heading {
  font-family: var(--font-heading);
  font-weight: 400;
  font-style: italic;
  color: var(--color-primary);
  letter-spacing: 0.05em;
}
```

## Performance

### Critical CSS

```html
<head>
  <!-- Inline critical CSS -->
  <style>
    /* Above-the-fold styles only */
    body { margin: 0; font-family: system-ui; }
    .hero { min-height: 100vh; display: flex; }
  </style>

  <!-- Preload fonts -->
  <link rel="preload" href="/fonts/playfair.woff2" as="font" type="font/woff2" crossorigin>

  <!-- Async load non-critical CSS -->
  <link rel="stylesheet" href="/style.css" media="print" onload="this.media='all'">
</head>
```

### Modern Image Formats

```html
<picture>
  <source srcset="product.avif" type="image/avif">
  <source srcset="product.webp" type="image/webp">
  <img
    src="product.jpg"
    alt="SkyyRose Signature Necklace"
    width="800"
    height="600"
    loading="lazy"
    decoding="async"
  >
</picture>
```

## Print Stylesheets

```css
@media print {
  /* Hide non-essential elements */
  header, footer, nav, .sidebar, .ads {
    display: none;
  }

  /* Optimize for print */
  body {
    font-size: 12pt;
    line-height: 1.5;
    color: #000;
    background: #fff;
  }

  /* Prevent page breaks inside elements */
  .product-card, figure, blockquote {
    page-break-inside: avoid;
  }

  /* Add URLs to links */
  a[href]::after {
    content: " (" attr(href) ")";
  }

  /* Show all images */
  img {
    max-width: 100% !important;
  }
}
```

## SkyyRose-Specific Patterns

### Luxury Card Design

```css
.luxury-product-card {
  background: #fff;
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-md);
  overflow: hidden;
  transition: all var(--transition-base);
}

.luxury-product-card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-4px);
}

.luxury-product-card__image {
  aspect-ratio: 4 / 3;
  object-fit: cover;
  width: 100%;
}

.luxury-product-card__content {
  padding: var(--spacing-lg);
}

.luxury-product-card__title {
  font-family: var(--font-heading);
  font-size: var(--font-size-xl);
  color: var(--color-primary);
  margin-bottom: var(--spacing-sm);
}

.luxury-product-card__price {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-secondary);
}
```

### Rose Gold Accents

```css
.rose-gold-accent {
  border-left: 4px solid var(--color-primary);
  padding-left: var(--spacing-md);
}

.rose-gold-underline {
  position: relative;
  display: inline-block;
}

.rose-gold-underline::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, var(--color-primary), var(--color-accent));
}
```

## Accessibility

```css
/* Focus visible for keyboard navigation */
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Skip to main content */
.skip-to-main {
  position: absolute;
  top: -40px;
  left: 0;
  background: var(--color-primary);
  color: white;
  padding: 8px;
  z-index: 100;
}

.skip-to-main:focus {
  top: 0;
}

/* Visually hidden but accessible */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

/* High contrast mode */
@media (prefers-contrast: high) {
  .product-card {
    border: 2px solid currentColor;
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

## References

See `references/` for detailed guides:
- `css-grid-guide.md` - Complete CSS Grid reference
- `flexbox-patterns.md` - Common Flexbox layouts
- `responsive-design.md` - Mobile-first techniques
- `typography-system.md` - Typographic scales and rhythm
- `accessibility-checklist.md` - HTML/CSS accessibility

## Examples

See `examples/` for working implementations:
- `product-grid.html` - CSS Grid product layout
- `luxury-card.html` - SkyyRose card design
- `responsive-nav.html` - Mobile-friendly navigation
- `accessible-form.html` - Complete accessible form
- `print-styles.html` - Print-optimized page
