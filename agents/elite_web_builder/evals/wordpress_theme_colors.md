# Eval: WordPress Theme Colors

## Capability
Generate a `theme.json` color palette from brand guidelines.

## Task
Given brand colors (primary, secondary, accent), produce a valid `theme.json`
color palette section with correct slugs, hex values, and names.

## Input
```json
{
  "brand_colors": {
    "rose_gold": "#B76E79",
    "crimson": "#DC143C",
    "mauve": "#D8A7B1",
    "onyx": "#353839",
    "gold": "#D4AF37"
  }
}
```

## Expected Output
- Valid JSON with `settings.color.palette` array
- Each entry has `slug`, `color`, `name`
- Hex values match input EXACTLY (zero tolerance)
- Slugs are kebab-case
- Names are Title Case

## Success Criteria
- pass@1 = 100% (zero tolerance for color hallucination)
- All hex values verified against input
- JSON parses without error
- No extra colors added beyond input

## Grader
Code — diff extracted hex values from output vs input brand colors.

## Severity
CRITICAL — color hallucination breaks brand identity.
