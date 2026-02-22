# WCAG 2.2 AA Checklist

## Perceivable

### 1.1 Text Alternatives
- [ ] All images have `alt` text (decorative images use `alt=""`)
- [ ] Complex images have long descriptions
- [ ] Form inputs have associated labels

### 1.3 Adaptable
- [ ] Content uses semantic HTML (`<nav>`, `<main>`, `<article>`, `<aside>`)
- [ ] Reading order matches visual order
- [ ] Instructions don't rely solely on sensory characteristics

### 1.4 Distinguishable
- [ ] **Normal text contrast ratio >= 4.5:1** (WCAG 1.4.3)
- [ ] **Large text contrast ratio >= 3:1** (18pt+ or 14pt+ bold)
- [ ] Text can be resized to 200% without loss
- [ ] No images of text (except logos)
- [ ] Content reflows at 320px width without horizontal scroll (1.4.10)
- [ ] Non-text contrast >= 3:1 for UI components and graphics (1.4.11)
- [ ] Text spacing adjustable (1.4.12)

## Operable

### 2.1 Keyboard Accessible
- [ ] All functionality available via keyboard
- [ ] No keyboard traps
- [ ] Skip navigation link present
- [ ] Focus visible on all interactive elements (2.4.7)

### 2.4 Navigable
- [ ] Page has descriptive `<title>`
- [ ] Focus order is logical
- [ ] Link purpose clear from text (no "click here")
- [ ] Multiple ways to find pages (nav + sitemap + search)
- [ ] Headings are descriptive and hierarchical

### 2.5 Input Modalities
- [ ] Touch targets are at least 24x24 CSS pixels (2.5.8 — new in 2.2)
- [ ] Dragging has non-dragging alternative (2.5.7 — new in 2.2)

## Understandable

### 3.1 Readable
- [ ] Page language declared (`<html lang="en">`)
- [ ] Abbreviations expanded on first use

### 3.2 Predictable
- [ ] No unexpected context changes on focus/input
- [ ] Consistent navigation across pages
- [ ] Consistent identification of components

### 3.3 Input Assistance
- [ ] Error messages identify the field and describe the error
- [ ] Labels or instructions provided for user input
- [ ] Error suggestions provided when known (3.3.3)
- [ ] Redundant entry avoided where possible (3.3.7 — new in 2.2)
- [ ] Accessible authentication — no cognitive tests (3.3.8 — new in 2.2)

## Robust

### 4.1 Compatible
- [ ] Valid HTML (no duplicate IDs)
- [ ] ARIA roles, states, and properties correct
- [ ] Status messages use `role="status"` or `aria-live`

## Color-Specific Rules

| Context | Minimum Ratio | WCAG Level |
|---------|--------------|------------|
| Normal text (<18pt) | 4.5:1 | AA |
| Large text (>=18pt or >=14pt bold) | 3:1 | AA |
| UI components & graphics | 3:1 | AA |
| Normal text (enhanced) | 7:1 | AAA |
| Large text (enhanced) | 4.5:1 | AAA |

## Common Violations (SkyyRose)

- Gold (#D4AF37) on white: 3.25:1 — **FAILS AA** for normal text
- Rose gold (#B76E79) on white: 3.8:1 — **FAILS AA normal**, passes AA-Large only
- Black on gold: 14.7:1 — **PASSES AAA**
- Crimson (#DC143C) on white: 4.63:1 — **PASSES AA**
- Rose gold on dark backgrounds recommended for body text
