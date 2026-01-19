# Visual Design

This skill provides comprehensive knowledge of visual design principles for e-commerce. It activates when users mention "design system", "color palette", "typography", "visual hierarchy", "branding", "UI design", or need visual design guidance.

---

## Design Philosophy

**EVERY PIXEL HAS PURPOSE.**

Great visual design isn't decoration—it's communication. Every color, font, spacing choice, and visual element should serve the brand story and guide users toward their goals.

## Color Theory for E-Commerce

### Psychology of Colors

| Color | Emotion | Best For |
|-------|---------|----------|
| Black | Luxury, sophistication | High-end fashion, jewelry |
| White | Purity, simplicity | Minimalist brands, tech |
| Blue | Trust, reliability | Finance, healthcare |
| Green | Natural, growth | Organic, sustainability |
| Red | Energy, urgency | Sales, food, entertainment |
| Orange | Friendly, confidence | Creative, youth |
| Purple | Premium, creative | Beauty, wellness |
| Gold | Luxury, success | Premium products |

### Building a Color System

```css
:root {
  /* Primary - Brand identity */
  --color-primary-50: #f0f4ff;
  --color-primary-100: #e0e7ff;
  --color-primary-200: #c7d2fe;
  --color-primary-300: #a5b4fc;
  --color-primary-400: #818cf8;
  --color-primary-500: #6366f1;  /* Main */
  --color-primary-600: #4f46e5;
  --color-primary-700: #4338ca;
  --color-primary-800: #3730a3;
  --color-primary-900: #312e81;

  /* Neutral - Text and backgrounds */
  --color-neutral-50: #fafafa;
  --color-neutral-100: #f5f5f5;
  --color-neutral-200: #e5e5e5;
  --color-neutral-300: #d4d4d4;
  --color-neutral-400: #a3a3a3;
  --color-neutral-500: #737373;
  --color-neutral-600: #525252;
  --color-neutral-700: #404040;
  --color-neutral-800: #262626;
  --color-neutral-900: #171717;

  /* Semantic */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #3b82f6;
}
```

### Contrast & Accessibility

```css
/* WCAG AA requires 4.5:1 for normal text, 3:1 for large text */
/* WCAG AAA requires 7:1 for normal text, 4.5:1 for large text */

/* Good contrast combinations */
.text-on-light {
  color: var(--color-neutral-900); /* On white: 21:1 */
}

.text-on-dark {
  color: var(--color-neutral-50); /* On black: 21:1 */
}

.text-secondary {
  color: var(--color-neutral-600); /* On white: 7.4:1 */
}
```

## Typography

### Font Pairing Strategies

**Contrast Principle**: Pair fonts with contrasting characteristics.

1. **Serif + Sans-serif** (Classic)
   - Display: Playfair Display
   - Body: Inter

2. **Geometric + Humanist** (Modern)
   - Display: Futura
   - Body: Source Sans Pro

3. **High contrast + Low contrast** (Elegant)
   - Display: Didot
   - Body: Helvetica Neue

### Type Scale

```css
/* Modular scale: 1.25 (Major Third) */
:root {
  --font-size-xs: 0.64rem;    /* 10.24px */
  --font-size-sm: 0.8rem;     /* 12.8px */
  --font-size-base: 1rem;     /* 16px */
  --font-size-lg: 1.25rem;    /* 20px */
  --font-size-xl: 1.563rem;   /* 25px */
  --font-size-2xl: 1.953rem;  /* 31.25px */
  --font-size-3xl: 2.441rem;  /* 39px */
  --font-size-4xl: 3.052rem;  /* 48.8px */
  --font-size-5xl: 3.815rem;  /* 61px */
}

/* Responsive typography */
html {
  font-size: 16px;
}

@media (max-width: 768px) {
  html {
    font-size: 14px;
  }
}

/* Fluid typography */
h1 {
  font-size: clamp(2rem, 5vw, 4rem);
}
```

### Font Weights & Usage

```css
:root {
  --font-weight-light: 300;
  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
}

/* Usage guidelines */
.heading { font-weight: var(--font-weight-bold); }
.subheading { font-weight: var(--font-weight-semibold); }
.body { font-weight: var(--font-weight-regular); }
.caption { font-weight: var(--font-weight-light); }
```

### Line Height & Spacing

```css
/* Line heights */
--line-height-tight: 1.2;    /* Headlines */
--line-height-snug: 1.375;   /* Subheadings */
--line-height-normal: 1.5;   /* Body text */
--line-height-relaxed: 1.75; /* Long-form */

/* Letter spacing */
--tracking-tight: -0.025em;  /* Large headlines */
--tracking-normal: 0;        /* Body */
--tracking-wide: 0.025em;    /* Caps, buttons */
--tracking-wider: 0.05em;    /* Small caps */
```

## Spacing System

### 8-Point Grid

```css
:root {
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-5: 1.25rem;   /* 20px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-10: 2.5rem;   /* 40px */
  --space-12: 3rem;     /* 48px */
  --space-16: 4rem;     /* 64px */
  --space-20: 5rem;     /* 80px */
  --space-24: 6rem;     /* 96px */
  --space-32: 8rem;     /* 128px */
}
```

### Component Spacing Guidelines

| Component | Internal Padding | External Margin |
|-----------|-----------------|-----------------|
| Button | 12px 24px | 8px |
| Card | 24px | 16px |
| Section | 80-120px vertical | 0 |
| Form input | 12px 16px | 16px bottom |
| Modal | 32px | - |

## Visual Hierarchy

### Size Hierarchy
```
1. Hero headline: 48-72px
2. Section title: 32-40px
3. Card title: 20-24px
4. Body text: 16-18px
5. Captions: 12-14px
```

### Weight Hierarchy
```
1. Headlines: Bold (700)
2. Subheadings: Semibold (600)
3. Body: Regular (400)
4. Supporting: Light (300)
```

### Contrast Hierarchy
```
1. Primary actions: Full color
2. Secondary content: 80% opacity
3. Tertiary info: 60% opacity
4. Disabled: 40% opacity
```

## Layout Principles

### Grid Systems

```css
/* 12-column grid */
.grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: var(--space-6);
}

/* Content widths */
:root {
  --container-sm: 640px;
  --container-md: 768px;
  --container-lg: 1024px;
  --container-xl: 1280px;
  --container-2xl: 1536px;
}

.container {
  width: 100%;
  max-width: var(--container-xl);
  margin: 0 auto;
  padding: 0 var(--space-4);
}
```

### White Space

**Rules for breathing room:**
1. More important = more space around it
2. Related items = less space between
3. Sections need generous vertical spacing
4. Mobile needs tighter, desktop needs looser

```css
/* Section spacing */
.section {
  padding: var(--space-16) 0;
}

@media (min-width: 768px) {
  .section {
    padding: var(--space-24) 0;
  }
}
```

## Component Design

### Buttons

```css
/* Button hierarchy */
.btn-primary {
  background: var(--color-primary-500);
  color: white;
  padding: var(--space-3) var(--space-6);
  border-radius: 8px;
  font-weight: var(--font-weight-medium);
  transition: all 0.2s ease;
}

.btn-primary:hover {
  background: var(--color-primary-600);
  transform: translateY(-1px);
}

.btn-secondary {
  background: transparent;
  color: var(--color-primary-500);
  border: 1px solid var(--color-primary-500);
}

.btn-ghost {
  background: transparent;
  color: var(--color-neutral-700);
}
```

### Cards

```css
.card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.card__image {
  aspect-ratio: 4/3;
  object-fit: cover;
}

.card__content {
  padding: var(--space-6);
}
```

### Product Cards

```css
.product-card {
  position: relative;
}

.product-card__badge {
  position: absolute;
  top: var(--space-3);
  left: var(--space-3);
  background: var(--color-error);
  color: white;
  padding: var(--space-1) var(--space-2);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.product-card__quick-actions {
  position: absolute;
  top: var(--space-3);
  right: var(--space-3);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.product-card:hover .product-card__quick-actions {
  opacity: 1;
}
```

## Shadows & Depth

```css
:root {
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.1);
  --shadow-2xl: 0 25px 50px rgba(0, 0, 0, 0.15);

  /* Elevation levels */
  --elevation-1: var(--shadow-sm);  /* Cards at rest */
  --elevation-2: var(--shadow-md);  /* Cards on hover */
  --elevation-3: var(--shadow-lg);  /* Dropdowns, popovers */
  --elevation-4: var(--shadow-xl);  /* Modals, dialogs */
}
```

## Design System Documentation

### Token Structure
```
Foundation
├── Colors (primary, neutral, semantic)
├── Typography (families, sizes, weights)
├── Spacing (scale, grid)
└── Shadows (elevations)

Components
├── Buttons (variants, sizes, states)
├── Cards (product, content, feature)
├── Forms (inputs, selects, checkboxes)
├── Navigation (header, footer, mobile)
└── Product (gallery, info, cart)

Patterns
├── Hero sections
├── Product grids
├── Category layouts
├── Checkout flow
└── Account pages
```

### Design Tokens (JSON)
```json
{
  "colors": {
    "primary": {
      "500": { "value": "#6366f1" }
    }
  },
  "typography": {
    "fontSize": {
      "base": { "value": "1rem" }
    }
  },
  "spacing": {
    "4": { "value": "1rem" }
  }
}
```

## E-Commerce Specific Patterns

### Trust Indicators
- Security badges
- Payment icons
- Review stars
- Shipping info
- Return policy

### Call-to-Action Hierarchy
1. Add to Cart (primary, prominent)
2. Add to Wishlist (secondary)
3. Share (tertiary)

### Price Display
```css
.price {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
}

.price--sale {
  color: var(--color-error);
}

.price--original {
  text-decoration: line-through;
  color: var(--color-neutral-400);
  font-size: var(--font-size-base);
}

.price--savings {
  background: var(--color-error);
  color: white;
  padding: var(--space-1) var(--space-2);
  font-size: var(--font-size-sm);
}
```

## Dark Mode

```css
@media (prefers-color-scheme: dark) {
  :root {
    --color-background: var(--color-neutral-900);
    --color-surface: var(--color-neutral-800);
    --color-text-primary: var(--color-neutral-50);
    --color-text-secondary: var(--color-neutral-300);
    --color-border: var(--color-neutral-700);
  }
}

/* Manual toggle */
[data-theme="dark"] {
  --color-background: var(--color-neutral-900);
  /* ... */
}
```

## Responsive Design Tokens

```css
/* Breakpoints */
--breakpoint-sm: 640px;
--breakpoint-md: 768px;
--breakpoint-lg: 1024px;
--breakpoint-xl: 1280px;
--breakpoint-2xl: 1536px;

/* Container padding */
--container-padding-mobile: var(--space-4);
--container-padding-tablet: var(--space-6);
--container-padding-desktop: var(--space-8);
```
