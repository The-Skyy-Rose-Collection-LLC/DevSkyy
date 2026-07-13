---
name: packaging-brief
description: "Writes product packaging design briefs with dimensions, material considerations, messaging hierarchy, compliance requirements, and vendor specs. Use when designing physical packaging."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Packaging Brief

## When to Use This Skill

Use this skill when you need to:
- Brief a designer on product packaging for a physical product
- Define packaging requirements including dimensions, materials, and messaging
- Plan packaging for an e-commerce product launch
- Create specifications for a packaging manufacturer

**DO NOT** use this skill for digital product packaging, shipping box logistics, or warehouse fulfillment processes. This is for consumer-facing product packaging design.

---

## Core Principle

PACKAGING IS YOUR LAST SALESPERSON — IT MUST COMMUNICATE YOUR VALUE PROPOSITION, DIFFERENTIATE FROM COMPETITORS, AND CREATE A POSITIVE FIRST IMPRESSION IN UNDER 3 SECONDS.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Product** | "What product needs packaging?" | Must be provided |
| **Dimensions** | "Product dimensions and weight?" | Must be provided |
| **Retail or DTC** | "Where will this be sold? (retail shelf, online DTC, both)" | Online DTC |
| **Brand guidelines** | "Do you have brand colors, fonts, and logo files?" | Must be provided or will reference brand-identity-guide |
| **Budget per unit** | "Target cost per packaging unit?" | $1-3 per unit |
| **Quantity** | "First production run size?" | 500-1,000 units |
| **Sustainability** | "Any sustainability requirements? (recyclable, compostable, minimal)" | Recyclable preferred |
| **Compliance** | "Any required legal text, certifications, or barcodes?" | Basic product info |

**GATE: Confirm brief before proceeding.**

---

## Phase 2: Design

### Messaging Hierarchy

Define what appears on each face of the packaging, ranked by importance:

1. **Front face (hero):** Brand name, product name, hero image or key visual, primary benefit claim
2. **Back face:** Product description, features/ingredients, usage instructions, certifications
3. **Side panels:** Secondary info, social handles, website, barcode/SKU
4. **Bottom/top:** Compliance text, manufacturing info, recycling symbols

### Material Considerations

| Material | Best For | Sustainability | Cost |
|----------|---------|---------------|------|
| Kraft cardboard | Eco-friendly brands, lightweight products | Recyclable, biodegradable | Low |
| Rigid box | Premium/luxury unboxing experience | Recyclable | High |
| Poly mailer | Soft goods, clothing, low-cost shipping | Varies (recycled options) | Very low |
| Custom molded | Fragile products, tech accessories | Varies | High (tooling cost) |

**GATE: Present the packaging concept and material recommendation before detailing specs.**

---

## Phase 3: Build

### Deliverables

**1. Complete Packaging Brief**
- Product and packaging dimensions (dieline specifications)
- Material and finish recommendations (matte, gloss, spot UV, foil)
- Color specifications (CMYK, Pantone for brand colors)
- Messaging hierarchy with exact copy for each panel
- Image and graphic placement guidelines

**2. Dieline Template Request**
- Dimensions for the packaging manufacturer to create the dieline
- Panel layout with zones for each content area
- Bleed, trim, and safe zone specifications

**3. Copy Document**
- All text that appears on packaging, organized by panel
- Legal and compliance text verified
- Barcode placement and size requirements

**4. Vendor Specification Sheet**
- Material, dimensions, finish, and quantity
- Print method (offset, digital, flexographic)
- Proofing requirements (digital proof, printed proof, production sample)
- Timeline: design → proof → production → delivery

---

## Phase 4: Polish

### Pre-Production Checklist

- [ ] Dieline approved by manufacturer
- [ ] All copy proofread by two people
- [ ] Compliance text verified for selling region
- [ ] Color proof reviewed in natural lighting
- [ ] Packaging tested with actual product inside
- [ ] Shipping durability tested (drop test, compression)
- [ ] Cost per unit confirmed with manufacturer

### Post-Launch Review

After the first 100 units ship, evaluate: damage rate, customer feedback on unboxing, return reasons related to packaging.

---

## Example 1: Skincare Product (DTC, premium positioning)

**Packaging:** Rigid box with magnetic closure, matte white exterior, foil-stamped logo, tissue paper insert. Cost target: $3.50/unit at 1,000 qty.

## Example 2: Food Product (Retail shelf, competitive pricing)

**Packaging:** Kraft stand-up pouch with window, 2-color flexo print, resealable zipper. Cost target: $0.75/unit at 5,000 qty. FDA-compliant nutrition panel.

---

## Anti-Patterns

- **Designing before sizing** — designing packaging without confirmed product dimensions leads to expensive redesigns. Dimensions first.
- **Too much text** — packaging is not a brochure. Prioritize ruthlessly. If they cannot read it in 3 seconds, cut it.
- **Ignoring shelf competition** — design in context. How does your packaging look next to competitors on a shelf or in a search result grid?
- **Forgetting compliance** — missing required text (ingredients, warnings, barcodes) means reprinting the entire run. Check early.
- **Low-MOQ surprise** — custom packaging often has minimum order quantities of 500-5,000. Confirm MOQs match your production plan.

---

## Recovery

- **No brand guidelines yet:** Use the brand-identity-guide skill first, or define minimum brand elements (logo, 2 colors, 1 font) before briefing packaging.
- **Budget too low for custom packaging:** Use stock packaging (plain kraft boxes, stock poly mailers) with custom stickers or stamps for V1. Upgrade with volume.
- **Product dimensions not finalized:** Use estimated dimensions with a note that the brief must be updated before production. Do not order packaging for unfinished products.
- **Selling internationally:** Flag compliance requirements per market (EU, UK, Asia have different labeling requirements). Recommend regulatory review.
