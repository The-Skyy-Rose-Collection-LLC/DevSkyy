---
name: design-system
description: Create a comprehensive design system for an immersive theme
user-invocable: true
---

# Design System Creation

You are creating a comprehensive design system for an immersive e-commerce theme.

## Design System Philosophy

**CONSISTENCY THROUGH SYSTEM.**

A design system isn't just colors and fonts—it's the DNA of the experience. Every decision compounds into the final result.

## Process

### 1. Gather Context

Before creating, understand:
- Brand personality
- Target audience
- Industry context
- Existing brand assets (if any)
- Technical platform (Elementor/Divi)

### 2. Use the Visual Designer Agent

Trigger the **visual-designer** agent to create the system.

### 3. Design System Components

**Foundation Layer**

1. **Color System**
   - Primary brand color + scale (50-900)
   - Secondary color + scale
   - Neutral grays + scale
   - Semantic colors (success, warning, error, info)
   - Usage guidelines

2. **Typography System**
   - Display font (headlines)
   - Body font (paragraphs)
   - Type scale (sizes with ratios)
   - Line heights
   - Letter spacing
   - Font weights and usage

3. **Spacing System**
   - Base unit (4px or 8px)
   - Spacing scale
   - Section spacing
   - Component spacing

4. **Grid System**
   - Container widths
   - Column structure
   - Gutter widths
   - Breakpoints

**Component Layer**

5. **Buttons**
   - Primary, secondary, ghost variants
   - Sizes (small, medium, large)
   - States (default, hover, active, disabled)
   - Icon buttons

6. **Cards**
   - Product cards
   - Content cards
   - Feature cards
   - Shadow/elevation system

7. **Forms**
   - Input fields
   - Select dropdowns
   - Checkboxes/radios
   - Error states
   - Labels and helpers

8. **Navigation**
   - Header structure
   - Mobile menu
   - Footer structure
   - Breadcrumbs

**E-Commerce Layer**

9. **Product Elements**
   - Product gallery
   - Price display
   - Variant selectors
   - Add to cart
   - Stock indicators

10. **Trust Elements**
    - Rating stars
    - Review displays
    - Security badges
    - Payment icons

### 4. Output Format

```
# Design System: [Theme Name]

## Brand Essence
- Personality: [3-5 adjectives]
- Voice: [tone description]
- Visual metaphor: [what it looks/feels like]

---

## Color System

### Primary
--color-primary-50: #[hex]
--color-primary-100: #[hex]
--color-primary-200: #[hex]
--color-primary-300: #[hex]
--color-primary-400: #[hex]
--color-primary-500: #[hex] (main)
--color-primary-600: #[hex]
--color-primary-700: #[hex]
--color-primary-800: #[hex]
--color-primary-900: #[hex]

Usage: [when to use each]

### Secondary
[Same structure]

### Neutral
[Same structure]

### Semantic
--color-success: #[hex]
--color-warning: #[hex]
--color-error: #[hex]
--color-info: #[hex]

---

## Typography

### Font Stack
Display: [Font Name], [fallbacks]
Body: [Font Name], [fallbacks]

### Type Scale
--font-size-xs: [value]
--font-size-sm: [value]
--font-size-base: [value]
--font-size-lg: [value]
--font-size-xl: [value]
--font-size-2xl: [value]
--font-size-3xl: [value]
--font-size-4xl: [value]
--font-size-5xl: [value]

### Weights
--font-weight-light: 300
--font-weight-regular: 400
--font-weight-medium: 500
--font-weight-semibold: 600
--font-weight-bold: 700

### Usage
H1: [size, weight, line-height]
H2: [size, weight, line-height]
H3: [size, weight, line-height]
Body: [size, weight, line-height]
Small: [size, weight, line-height]

---

## Spacing

### Scale
--space-1: 0.25rem (4px)
--space-2: 0.5rem (8px)
--space-3: 0.75rem (12px)
--space-4: 1rem (16px)
--space-6: 1.5rem (24px)
--space-8: 2rem (32px)
--space-10: 2.5rem (40px)
--space-12: 3rem (48px)
--space-16: 4rem (64px)
--space-20: 5rem (80px)
--space-24: 6rem (96px)

### Section Spacing
Mobile: [value]
Desktop: [value]

---

## Shadows

--shadow-sm: [value]
--shadow-md: [value]
--shadow-lg: [value]
--shadow-xl: [value]

---

## Border Radius

--radius-sm: [value]
--radius-md: [value]
--radius-lg: [value]
--radius-full: 9999px

---

## Components

### Buttons
[CSS/specifications for each variant]

### Cards
[CSS/specifications for each variant]

### Forms
[CSS/specifications for inputs, selects, etc.]

---

## Implementation Notes

### Elementor Global Settings
[How to configure in Elementor]

### Divi Theme Customizer
[How to configure in Divi]

### CSS Custom Properties
[Complete :root block]
```

## Important

- Every choice should trace back to brand personality
- Test color combinations for accessibility
- Provide rationale for decisions
- Include implementation specifics for the page builder
- Ralph Loop until the system is comprehensive and cohesive
