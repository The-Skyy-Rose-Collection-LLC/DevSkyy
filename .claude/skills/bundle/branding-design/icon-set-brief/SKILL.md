---
name: icon-set-brief
description: "Briefs icon set design with style direction, size requirements, use cases, consistency guidelines, and delivery specifications. Use when commissioning custom icons for your brand."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Icon Set Brief

## When to Use This Skill

Use this skill when you need to:
- Commission a custom icon set for your website, app, or marketing
- Brief a designer on icon style, sizes, and usage requirements
- Define consistency rules for icons across your brand
- Create specifications for icon delivery and implementation

**DO NOT** use this skill for selecting stock icon libraries, designing icons yourself, or creating illustration briefs. This is for briefing custom icon set design.

---

## Core Principle

ICONS MUST BE INSTANTLY RECOGNIZABLE AT THEIR SMALLEST SIZE — IF THE ICON NEEDS A LABEL TO BE UNDERSTOOD, THE ICON HAS FAILED.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Icon count** | "How many icons do you need?" | 15-25 |
| **Use cases** | "Where will icons be used? (website, app, presentations, print)" | Website |
| **Icon list** | "List each icon needed with its concept (e.g., settings gear, user profile, shopping cart)." | Must be provided |
| **Style preference** | "Line, filled, duotone, or 3D? Share 2-3 icon sets you admire." | Line style |
| **Brand guidelines** | "Brand colors, visual style, personality." | Must be provided |
| **Sizes needed** | "What sizes? (16px, 24px, 32px, 48px)" | 24px primary, 16px and 32px variants |

**GATE: Confirm brief before proceeding.**

---

## Phase 2: Design

### Style Specification

Define the visual rules for the entire set:

- **Style:** Line, filled, duotone, or combination
- **Stroke weight:** Consistent across all icons (e.g., 1.5px at 24px size)
- **Corner radius:** Sharp, rounded, or mixed with specific radius
- **Grid:** Base grid size (24x24 with 2px padding = 20x20 safe area)
- **Color:** Monochrome, two-color, or full brand palette
- **Perspective:** Flat or isometric

### Consistency Rules

- All icons must share the same stroke weight, corner radius, and visual density
- Key lines (horizontal, vertical, circular) should align across the set
- Optical sizing: simpler icons may need slightly larger visual weight to feel balanced

**GATE: Present the style specification with example references before the icon list.**

---

## Phase 3: Build

### Deliverables

**1. Complete Icon Brief Document**
- Style specification with all visual rules
- Full icon list with concept description per icon
- Size and format requirements
- Usage context for each icon

**2. Technical Specification Sheet**
| Spec | Value |
|------|-------|
| Grid size | 24x24px |
| Safe area | 20x20px (2px padding) |
| Stroke weight | 1.5px |
| Corner radius | 2px |
| Export sizes | 16, 24, 32, 48px |
| File formats | SVG (primary), PNG (fallback) |
| Color modes | Single color (inherits CSS color) |

**3. Naming Convention**
- File naming format: `icon-[concept]-[size].[format]`
- Example: `icon-settings-24.svg`, `icon-user-16.png`
- Organized in folders by size or by concept

**4. Quality Checklist**
- [ ] All icons visually consistent in weight and style
- [ ] Readable at smallest size (16px)
- [ ] SVGs are clean (no unnecessary groups, proper viewBox)
- [ ] Pixel-aligned at primary size
- [ ] Accessible: sufficient contrast, not sole indicator of meaning

---

## Phase 4: Polish

### Implementation Guide

- How to integrate SVGs into the website or app
- CSS color inheritance setup for monochrome icons
- Accessibility notes: pair icons with labels for screen readers

### Future Expansion

- How to request additional icons while maintaining consistency
- Designer handoff notes for the icon grid and style rules
- Template file for designing new icons in the established style

---

## Example 1: SaaS Dashboard Icons (20 icons)

**Style:** 1.5px line, rounded corners, monochrome. Icons for: dashboard, analytics, settings, users, billing, notifications, search, filters, export, help, plus 10 feature-specific icons.

## Example 2: E-commerce Website Icons (15 icons)

**Style:** 2px line with filled accents, brand color duo. Icons for: cart, wishlist, search, menu, account, shipping, returns, payment, star rating, filter, sort, compare, gift, support, location.

---

## Anti-Patterns

- **Inconsistent stroke weight** — one icon with 1px strokes next to one with 3px strokes looks like two different icon sets.
- **Too detailed at small sizes** — intricate icons that look great at 48px become blobs at 16px. Design for the smallest size first.
- **No grid system** — icons designed freehand without a grid will never align consistently.
- **Mixing styles** — line icons and filled icons in the same set create visual discord unless intentionally designed as a system.
- **Raster-only delivery** — PNGs cannot scale. Always require SVG as the primary format.

---

## Recovery

- **Designer delivers inconsistent icons:** Provide the style spec and ask for a revision pass focused on stroke weight and visual density alignment.
- **Icons not clear at small size:** Request simplified versions for 16px use. Many icon sets have detailed and compact variants.
- **Budget too low for custom icons:** Recommend a quality open-source icon library (Lucide, Phosphor, Tabler) and customize colors to match the brand.
- **Icon list keeps growing:** Set a V1 scope and commit to it. Additional icons come in a V2 batch after V1 is approved and implemented.
