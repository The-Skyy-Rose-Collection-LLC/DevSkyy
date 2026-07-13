---
name: size-guide
description: "Creates product size guides with measurement instructions, comparison charts, fit recommendations, and international conversions. Use when reducing size-related returns."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Size Guide

## When to Use This Skill

Use this skill when you need to:
- Create a size guide for apparel, footwear, or sized products
- Reduce return rates caused by incorrect sizing
- Build size comparison charts across international standards
- Write measurement instructions customers can follow at home

**DO NOT** use this skill for product specifications, general product descriptions, or manufacturing size specs. This is for customer-facing size guidance.

---

## Core Principle

EVERY SIZE GUIDE MUST ANSWER: "WHAT SIZE SHOULD I ORDER?" IN UNDER 60 SECONDS — IF CUSTOMERS GUESS, THEY RETURN.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Product type** | "What product needs a size guide? (tops, pants, shoes, accessories, furniture)" | Must be provided |
| **Size range** | "What sizes do you offer? (XS-XXL, numeric, one-size)" | Must be provided |
| **Measurements** | "Do you have garment measurements or body measurements for each size?" | Must be provided |
| **Fit type** | "How does the product fit? (true to size, runs small, runs large, relaxed, slim)" | True to size |
| **Markets** | "Do you sell internationally? (US, UK, EU sizing needed?)" | US only |
| **Return data** | "What percentage of returns are size-related?" | Unknown |

**GATE: Confirm brief and measurement data before proceeding.**

---

## Phase 2: Design

### Size Guide Components

1. **Size chart** — measurements mapped to each size
2. **How to measure** — step-by-step instructions with body measurement points
3. **Fit recommendations** — general guidance on fit and between-sizes advice
4. **International conversions** — US/UK/EU size equivalents
5. **Model reference** — what size the model is wearing and their measurements

### Measurement Types

**Apparel (body measurements):**
- Chest/bust, waist, hips, inseam (pants), shoulder width

**Apparel (garment measurements):**
- Chest width, body length, sleeve length, hem width

**Footwear:**
- Foot length in cm/inches, width (if applicable)

**GATE: Present the guide structure and confirm measurements are complete before writing.**

---

## Phase 3: Build

### Deliverables

**1. Size Chart Table**

| Size | Chest (in) | Waist (in) | Hips (in) | Length (in) |
|------|-----------|-----------|----------|------------|
| S | 34-36 | 28-30 | 34-36 | 27 |
| M | 37-39 | 31-33 | 37-39 | 28 |
| L | 40-42 | 34-36 | 40-42 | 29 |
| XL | 43-45 | 37-39 | 43-45 | 30 |

**2. How to Measure Instructions**
- Step-by-step for each measurement point
- What to wear while measuring (fitted clothing or underwear)
- Use a flexible measuring tape — not a ruler
- Stand relaxed, do not pull the tape tight

**3. Fit Recommendations**
- "This product runs true to size. Order your usual size."
- "Between sizes? Size up for a relaxed fit, size down for a fitted look."
- "Our model is 5'10", 155 lbs, wearing size M."

**4. International Conversion Table (if applicable)**

| US | UK | EU | Chest (cm) |
|----|----|----|-----------|
| S | S | 46 | 86-91 |
| M | M | 48 | 94-99 |
| L | L | 50 | 102-107 |

**5. FAQ**
- "What if I'm between two sizes?"
- "Do your products shrink after washing?"
- "How should I measure myself?"

---

## Phase 4: Polish

### Implementation Recommendations

- Link the size guide from every product page (not buried in the footer)
- Add a "Find Your Size" button near the size selector
- Mobile-optimized format (horizontal scroll tables or accordion sections)
- Consider a size quiz tool for interactive guidance

### Return Rate Tracking

After implementing the size guide, track:
- Size-related return rate (target: 20%+ reduction)
- Size guide page views vs. return rate correlation
- Customer feedback mentioning sizing accuracy

---

## Example 1: T-Shirt Size Guide (Unisex, S-XXL)

Body measurements in inches and cm, garment measurements for each size, "runs slightly oversized — if you prefer a fitted look, size down," model reference photo with size noted.

## Example 2: Shoe Size Guide (US/UK/EU)

Foot length measurement instructions (trace foot on paper, measure longest point), conversion table for US Men's, US Women's, UK, and EU sizes, width guidance if applicable, note on break-in period.

---

## Anti-Patterns

- **Measurements without instructions** — "Chest: 38 inches" is useless if the customer does not know how to measure their chest. Always include how-to.
- **Body vs. garment confusion** — mixing body measurements and garment measurements in the same chart without labeling creates returns. Label clearly.
- **Missing between-sizes advice** — most customers are between sizes. Tell them what to do.
- **Hiding the size guide** — a size guide nobody finds does not reduce returns. Make it prominent on every product page.
- **One guide for different product types** — t-shirts and pants need different measurements. Create product-specific guides.

---

## Recovery

- **No measurement data available:** Order one of each size and measure them. Garment measurements are better than no measurements.
- **Products vary across styles:** Note sizing variation per style or provide a fit description per product (slim, regular, relaxed).
- **International conversions are imprecise:** Note that conversions are approximate and recommend measuring for best results.
- **High return rates persist:** Survey returners on their experience. The guide may be accurate but hard to find or hard to understand.
