# WCAG 2.2 AA Checklist

## Contrast Ratios
- Normal text (< 18pt): 4.5:1 minimum
- Large text (>= 18pt or >= 14pt bold): 3:1 minimum
- UI components and graphical objects: 3:1 minimum
- Focus indicators: 3:1 against adjacent colors

## Images
- All `<img>` elements MUST have `alt` attribute
- Decorative images: `alt=""` (empty, not missing)
- Complex images: long description via `aria-describedby`

## Forms
- All inputs MUST have associated `<label>`
- Error messages MUST identify the field and describe the error
- Required fields MUST be indicated (not by color alone)

## Keyboard Navigation
- All interactive elements MUST be keyboard accessible
- Focus order MUST be logical (follows DOM order)
- No keyboard traps
- Skip navigation link for repetitive content
- Focus visible on all interactive elements

## ARIA
- Use semantic HTML first, ARIA only when needed
- `role`, `aria-label`, `aria-labelledby`, `aria-describedby`
- Live regions: `aria-live="polite"` for dynamic content
- `aria-expanded` for collapsible sections

## Color
- Information MUST NOT be conveyed by color alone
- Use icons, patterns, or text alongside color indicators
