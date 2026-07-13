---
name: style-tile
description: "Creates style tiles for web design projects with typography, colors, UI elements, textures, and mood references. Use when aligning on visual direction before full design."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Style Tile

## When to Use This Skill

Use this skill when you need to:
- Establish visual direction for a web design project before full mockups
- Align stakeholders on design aesthetic without building complete pages
- Bridge the gap between brand guidelines and actual web implementation
- Give a designer or developer clear direction for UI styling

**DO NOT** use this skill for wireframing, full page mockups, or brand identity creation. Style tiles sit between brand guidelines and page design — they define the visual feel without committing to layout.

---

## Core Principle

A STYLE TILE SHOWS HOW THE BRAND FEELS ON SCREEN — IT ANSWERS "WHAT WILL THIS LOOK LIKE?" WITHOUT DESIGNING EVERY PAGE.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Project** | "What web project is this for? (new site, redesign, landing page)" | New website |
| **Brand adjectives** | "Describe the desired feel in 3-5 adjectives." | Must be provided |
| **Target audience** | "Who will use this site?" | Must be provided |
| **Reference sites** | "Share 3-5 websites you admire visually and why." | Must be provided |
| **Anti-references** | "Share 1-2 sites that feel wrong for your brand." | None |
| **Existing brand assets** | "Logo, colors, fonts — what do you have?" | Logo and basic colors |

**GATE: Confirm brief before creating style tile specifications.**

---

## Phase 2: Design

### Style Tile Components

A complete style tile includes specifications for:

1. **Color palette** — primary, secondary, accent, neutrals with hex codes
2. **Typography** — heading font, body font, size scale, weight variations
3. **Button styles** — primary CTA, secondary, ghost/outline, hover states
4. **Form elements** — input fields, dropdowns, checkboxes, error states
5. **Card/container styles** — border radius, shadow depth, background treatment
6. **Image treatment** — photo style, overlay treatment, border or mask shapes
7. **Iconography style** — line weight, style reference, size
8. **Texture/pattern** — background patterns, subtle textures, gradients
9. **Mood adjectives** — 3-5 words that capture the target feeling

### Typography Scale

Define a type scale with exact values:
- Display: 48-64px
- H1: 36-48px
- H2: 28-36px
- H3: 22-28px
- Body: 16-18px
- Small/Caption: 12-14px
- Line height: 1.4-1.6 for body, 1.1-1.2 for headings

**GATE: Present the style tile specification and wait for feedback. Iterate until the direction is approved.**

---

## Phase 3: Build

### Deliverables

**1. Style Tile Document**
- Complete specification for every visual element listed above
- Organized in a single-page reference format
- Includes hex codes, font names, pixel values, and border radius values

**2. CSS Design Tokens**
- Variables list ready for implementation:
  - `--color-primary: #XXXX`
  - `--font-heading: 'Inter', sans-serif`
  - `--radius-default: 8px`
  - `--shadow-card: 0 2px 8px rgba(0,0,0,0.1)`

**3. Component Style Specs**
- Button: padding, font size, border radius, background color, hover state
- Card: padding, border, shadow, border radius
- Input: height, border, focus state, error state
- Link: color, underline treatment, hover state

**4. Mood Board Reference**
- 5-8 reference images capturing the target aesthetic
- Notes on what to take from each reference (typography from this one, spacing from that one)

---

## Phase 4: Polish

### Design Handoff

Package the style tile for the person implementing it:
- For designers: Figma-ready specifications with component descriptions
- For developers: CSS variables and utility class suggestions
- For page builders: color codes and font names formatted for Webflow, WordPress, or Squarespace

### Iteration Protocol

Style tiles are meant to be iterated. Present up to 3 directions if the first does not land. Each iteration adjusts based on specific feedback ("warmer colors," "more whitespace," "bolder typography").

---

## Example 1: Bold SaaS Startup

**Adjectives:** Bold, modern, confident, energetic.
**Colors:** Deep navy (#0F1729), electric blue (#3B82F6), white, warm gray.
**Typography:** Inter Bold for headings, Inter Regular for body.
**Buttons:** Rounded (8px radius), solid blue, white text, subtle shadow on hover.
**Cards:** White with 1px border, 12px radius, light shadow.

## Example 2: Warm Lifestyle Brand

**Adjectives:** Warm, organic, inviting, refined.
**Colors:** Terracotta (#C2725A), cream (#FFF8F0), sage (#6B8F71), charcoal (#2D3436).
**Typography:** Playfair Display for headings, Source Sans Pro for body.
**Buttons:** Pill-shaped (full radius), terracotta fill, cream text.
**Cards:** Cream background, no border, subtle warm shadow, 16px radius.

---

## Anti-Patterns

- **Style tile as final design** — it shows direction, not layout. Do not expect it to replace mockups.
- **Too many options at once** — presenting 5 style directions creates decision paralysis. Maximum 2-3 options.
- **No interactive states** — buttons without hover states and inputs without focus states leave gaps for implementation.
- **Vague specifications** — "modern font" is not actionable. Include the exact font name, weight, and size.
- **Skipping anti-references** — knowing what the client does NOT want is as valuable as knowing what they do want.

---

## Recovery

- **Client cannot articulate the desired feel:** Use a preference test — show 5 diverse website screenshots and ask for gut reactions (love/hate/neutral).
- **Style tile rejected:** Ask which specific elements feel wrong. Often it is one thing (color too cold, font too formal) not the whole direction.
- **Cannot agree on direction:** Create two contrasting style tiles (e.g., bold vs. minimal) and let the contrast clarify the preference.
- **Style tile looks good but does not translate to pages:** Bridge the gap with a single sample section (hero area) using the style tile elements before committing to full page design.
