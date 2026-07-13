---
name: color-palette-generator
description: "Generates brand color palettes with hex codes, accessibility ratings, application guidelines, and print/digital specifications. Use when establishing or refreshing brand colors."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Color Palette Generator

## When to Use This Skill

Use this skill when you need to:
- Create a brand color palette from scratch
- Expand an existing palette with complementary colors
- Ensure color accessibility compliance (WCAG standards)
- Document color usage guidelines for consistent application

**DO NOT** use this skill for full brand identity guides, logo design, or UI component design. This is specifically for color palette creation and documentation.

---

## Core Principle

A COLOR PALETTE MUST WORK IN EVERY CONTEXT — SCREEN, PRINT, LARGE BACKGROUNDS, SMALL TEXT — AND PASS ACCESSIBILITY STANDARDS FOR ALL USERS.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Brand personality** | "Describe your brand in 3 adjectives." | Must be provided |
| **Industry** | "What industry are you in?" | Must be provided |
| **Existing colors** | "Do you have any colors already? (hex codes, brand materials)" | Starting fresh |
| **Preferences** | "Any colors you love or hate?" | None |
| **Primary use** | "Where will colors be used most? (website, print, social, packaging)" | Website and social |
| **Competitors** | "What colors do your competitors use? (to differentiate)" | Will research |

**GATE: Confirm brief before generating palettes.**

---

## Phase 2: Generate

### Palette Structure

Every brand palette needs these roles:

| Role | Purpose | Count |
|------|---------|-------|
| **Primary** | Main brand color, CTAs, key elements | 1 |
| **Secondary** | Supporting color, section backgrounds, accents | 1-2 |
| **Neutral dark** | Text, dark backgrounds, headers | 1 |
| **Neutral light** | Light backgrounds, cards, spacing | 1 |
| **Accent** | Highlights, alerts, special elements | 1 |
| **Success/Error** | Functional colors for UI feedback | 2 (green/red) |

### Generation Method

1. Start with the primary color based on brand personality and industry
2. Use color theory to build harmonious relationships (complementary, analogous, triadic)
3. Generate 2-3 complete palette options
4. Test each for accessibility before presenting

**GATE: Present 2-3 palette options and wait for selection.**

---

## Phase 3: Document

### Deliverables

**1. Complete Color Specification**

For each color in the palette:
- Color name (brand-specific, e.g., "Ocean Blue" not just "Blue")
- Hex code (#1A73E8)
- RGB values (26, 115, 232)
- HSL values
- CMYK values (for print)
- Pantone match (closest)

**2. Accessibility Report**
- Contrast ratio for each color pair used for text
- WCAG AA compliance (4.5:1 for normal text, 3:1 for large text)
- WCAG AAA compliance where achievable
- Recommended text colors on each background color

**3. Usage Guidelines**
- Which color for which use case (backgrounds, buttons, text, links, hover states)
- Maximum percentage of each color in a typical layout (e.g., primary: 10%, neutrals: 70%)
- Color combinations to use and combinations to avoid
- Dark mode variations if applicable

**4. Application Examples**
- Sample website section using the palette
- Social media post example
- Business card or print layout example
- Email template color usage

---

## Phase 4: Polish

### Digital Asset Package

- Swatch file descriptions for design tools (Figma, Canva, Adobe)
- CSS custom properties for web implementation
- Tailwind config values (if applicable)

### Print Preparation Notes

- CMYK values verified for accurate print reproduction
- Paper stock considerations that affect color appearance
- Recommend print proof before large runs

---

## Example 1: Bold Tech Startup

**Primary:** Electric Blue (#2563EB) — confidence, trust, innovation
**Secondary:** Slate Gray (#475569) — professionalism, balance
**Accent:** Amber (#F59E0B) — energy, CTAs
**Neutrals:** Near-black (#0F172A), Off-white (#F8FAFC)

## Example 2: Wellness Brand

**Primary:** Sage Green (#6B8F71) — calm, natural, growth
**Secondary:** Warm Sand (#D4B896) — approachable, earthy
**Accent:** Terracotta (#C2725A) — warmth, CTAs
**Neutrals:** Charcoal (#2D3436), Cream (#FFF9F0)

---

## Anti-Patterns

- **Too many colors** — more than 6-8 colors creates visual chaos. Constrain the palette.
- **Ignoring accessibility** — beautiful colors that fail contrast requirements exclude users and risk legal issues.
- **Matching competitor colors** — if every competitor is blue, differentiate. Standing out matters more than fitting in.
- **Screen-only thinking** — colors that look great on screen may print poorly. Always provide CMYK values.
- **No neutral colors** — a palette of all vibrant colors has nowhere for the eye to rest. Include dark and light neutrals.

---

## Recovery

- **User cannot describe brand personality:** Show them 5 color palettes and ask which feels closest. Reverse-engineer the personality from their preference.
- **Existing color fails accessibility:** Suggest slight adjustments (darken or lighten by 10-15%) that maintain the feel while passing WCAG.
- **Too attached to a specific color:** Build the rest of the palette around it. One non-negotiable color can anchor a great palette.
- **Palette looks different on different screens:** Provide the hex codes and note that screen calibration varies. Print proofs are the only reliable standard.
