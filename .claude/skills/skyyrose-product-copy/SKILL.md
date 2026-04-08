---
name: skyyrose-product-copy
description: "Write conversion-optimized product descriptions, collection page copy, and product FAQs for SkyyRose luxury streetwear on WooCommerce. Use when creating or improving product listings, writing collection page descriptions, or generating product FAQ content for skyyrose.co."
allowed-tools: Read Write Edit Glob Grep
---

# SkyyRose Product Copy System

## When to Use This Skill

- Writing new WooCommerce product descriptions for skyyrose.co
- Improving existing product copy that lacks brand voice
- Writing collection page descriptions (Black Rose, Love Hurts, Signature, Kids Capsule)
- Generating product FAQs to reduce pre-purchase hesitation
- Optimizing product SEO (titles, meta descriptions, alt text)
- Creating pre-order product copy with exclusivity and urgency

**DO NOT** use for ad copy (use `skyyrose-paid-media`), email copy (use `skyyrose-email-flows`), or social captions (use `skyyrose-content-engine`).

---

## Brand Voice Quick Reference

| Element | Rule |
|---------|------|
| Tone | Luxury but grounded, poetic but never pretentious |
| Tagline | "Luxury Grows from Concrete." |
| NEVER say | "high-quality", "affordable luxury", "premium", "exclusive" as standalone |
| ALWAYS show | Weight (gsm), construction (double-stitched), material specifics |
| Oakland voice | "The Town" not "the Bay Area" for Oakland-specific |
| Pre-order language | "Limited to X pieces" not "Pre-order now" |
| Reading level | 8th grade — short sentences, sensory language, active voice |

### Collection Voices

| Collection | Voice | Accent Color | Font | Mood |
|-----------|-------|-------------|------|------|
| **Black Rose** | Defiant, bold, midnight elegance | Silver #C0C0C0 | Cinzel | "Built for those who move through darkness like it's home" |
| **Love Hurts** | Passionate, dramatic, emotionally raw | Crimson #DC143C | Playfair Display | "Every stitch carries a story you don't have to explain" |
| **Signature** | Confident, golden, Bay Area swagger | Gold #D4AF37 | Playfair Display | "Where the fog meets the gold, legends wear their name" |
| **Kids Capsule** | Playful, empowering, proud | Rose Gold #B76E79 | Playfair Display | "Little royalty, big energy" |

---

## WooCommerce Product Fields

| Field | Max Length | Purpose |
|-------|-----------|---------|
| Product Title | 70 chars (SEO sweet spot) | Keyword + brand + differentiator |
| Short Description | 150-200 chars | Above-the-fold hook, benefit-first |
| Long Description | 300-600 words | Story + features + specs + CTA |
| SEO Title (Yoast/RankMath) | 60 chars | Primary keyword first |
| Meta Description | 155 chars | Benefit + keyword + CTA |
| Image Alt Text | 125 chars | Descriptive + primary keyword |
| URL Slug | Keyword-rich | `black-rose-hoodie` not `product-br-004` |

---

## Core Workflow

### Phase 1: Gather Product Intelligence

For every product, confirm:
1. **SKU and product name** (cross-reference memory for exact names)
2. **Collection** (determines voice, color, typography)
3. **Product type** (hoodie, jersey, shorts, jacket, etc.)
4. **Price** and **pre-order status**
5. **Key physical details** (weight/gsm, material, construction, sizing)
6. **Limited quantity** (if applicable — jersey series = 80 pieces each)
7. **What makes it special** (design story, cultural reference, construction detail)

If the user provides items 1-3, proceed with known brand defaults.

### Phase 2: Write the Product Listing

Generate every element in this order:

**1. Product Title**
```
[Collection] [Product Name] — [Key Differentiator]
```
Examples:
- "Black Rose Hoodie — Heavyweight 380gsm French Terry"
- "Love Hurts Varsity Jacket — Full-Grain Leather Sleeves"
- "Bay Bridge Shirt — Golden Gate Series"

**2. Short Description (WooCommerce excerpt)**
One to two sentences. Benefit first, then the sensory hook.

Black Rose example:
> Heavyweight French terry that drops like armor. Double-stitched seams, ribbed cuffs, embroidered Black Rose script across the chest.

Love Hurts example:
> Full-grain leather sleeves meet wool-blend body in a varsity silhouette that doesn't ask permission. Chenille "Love Hurts" patch. Hand-finished details throughout.

Signature example:
> Golden hour trapped in cotton. Mint and lavender colorblock hoodie with brushed fleece interior and rose gold hardware.

**3. Long Description**
Structure:

```
[Opening hook — 1-2 sentences that set the scene]

[The story — why this piece exists, what it represents]

[Construction details — material, weight, stitching, hardware]

[Fit and sizing — how it wears, what to expect]

[Pre-order / exclusivity callout if applicable]

[CTA — specific, not generic]
```

**4. SEO Elements**
- SEO Title: `[Primary Keyword] — [Brand] | [Collection]`
- Meta Description: 155 chars, benefit + keyword + subtle CTA
- Alt Text per image: `[Product name] [view] — [one detail]`
- URL: `/product/[slug]/`

**5. Product FAQ (3-5 questions)**
Standard questions to address:
- What's the fabric/material?
- How does it fit? (true to size, oversized, etc.)
- When will pre-orders ship?
- Is this a limited release?
- How do I care for this piece?

### Phase 3: Polish

Run this checklist before delivering:

| Check | Verify |
|-------|--------|
| Collection voice match | Copy sounds like Black Rose / Love Hurts / Signature / Kids |
| Benefits lead features | Every bullet starts with what you FEEL, not what it IS |
| No unproven superlatives | Zero "best", "#1", "world-class" without proof |
| Sensory language present | Weight, texture, drape, feel are mentioned |
| Pre-order handled | Limited quantity and exclusivity communicated |
| SEO complete | Title, meta, alt text, slug all present |
| Character limits met | All fields within WooCommerce limits |
| No banned phrases | No "high-quality", "affordable luxury", "premium" alone |
| CTA is specific | "Claim yours before they're gone" beats "Buy now" |
| Oakland/Bay reference | Natural cultural reference if applicable |

### Phase 4: Deliver

Save as `{sku}-product-copy.md` or update directly in theme files.
Include a copy-paste section at the end for WooCommerce admin entry.

---

## Example: Black Rose Hoodie (br-004, $40, PRE-ORDER)

### Product Title (54/70 chars)
```
Black Rose Hoodie — Heavyweight French Terry
```

### Short Description
```
Heavyweight French terry that drops like armor. Double-stitched seams, ribbed cuffs, embroidered Black Rose script across the chest. Built in The Town. Limited pre-order.
```

### Long Description
```
Some hoodies you wear. This one wears a reputation.

The Black Rose Hoodie is 380gsm French terry — dense enough to cut wind, soft enough to live in. The kind of weight that reminds you it's there every time you move. Every seam is double-stitched. The ribbed cuffs hold their shape season after season. The Black Rose script across the chest is embroidered, not printed — because print fades. Embroidery doesn't.

This is the Black Rose Collection: dark, deliberate, Oakland to the core. Named for the beauty that grows where it shouldn't. Where others see concrete, we see potential.

CONSTRUCTION
• 380gsm French terry (heavyweight — this is not a fast-fashion fleece)
• Double-stitched seams throughout
• Embroidered Black Rose script — front chest
• Ribbed cuffs and hem
• Brushed interior
• Kangaroo pocket with reinforced edges

FIT
Relaxed fit, true to size. If you want oversized, size up one.

PRE-ORDER
Limited release. Once they're gone, they're gone. Ships within 4-6 weeks of order close.

This isn't just a hoodie. It's what luxury looks like when it grows from concrete.
```

### SEO
```
SEO Title: "Black Rose Hoodie — SkyyRose Heavyweight Streetwear" (52/60 chars)
Meta Description: "380gsm French terry hoodie with embroidered Black Rose script. Double-stitched, built in Oakland. Limited pre-order from SkyyRose." (131/155 chars)
URL: /product/black-rose-hoodie/
Alt: "Black Rose Hoodie front view — embroidered script on heavyweight black French terry"
```

### Product FAQ
```
Q: What's the fabric weight?
A: 380gsm French terry — significantly heavier than standard hoodies (typically 250-280gsm). You'll feel the difference immediately.

Q: How does it fit?
A: Relaxed fit, true to size. For an oversized silhouette, go up one size.

Q: When does my pre-order ship?
A: Pre-orders ship within 4-6 weeks of the order window closing. You'll receive tracking via email.

Q: Is this a limited release?
A: Yes. Once pre-order quantities are reached, this run is closed. We don't do restocks on every drop.

Q: How do I care for this hoodie?
A: Machine wash cold, inside out. Tumble dry low or hang dry. The embroidery is built to last — no special treatment needed.
```

---

## Example: Bay Bridge Shorts (sg-001, $195, PRE-ORDER)

### Product Title (56/70 chars)
```
Bay Bridge Shorts — Limited Bridge Series Edition
```

### Short Description
```
The bridge between streetwear and statement piece. Premium construction, gold hardware, bridge-inspired colorway. 80 pieces. That's it.
```

### Long Description
```
The Bay Bridge isn't just infrastructure. It's identity. Two cities connected by steel and intention — and these shorts carry that same energy.

The Bay Bridge Shorts are the flagship piece of the Bridge Series. Every detail is deliberate: the colorway mirrors the bridge at golden hour, the hardware is gold-finished, and the cut sits clean whether you're walking Lakeshore or sitting courtside.

This is limited to 80 pieces. Not because we can't make more — because we chose not to. When you see someone else wearing these, you'll know they understood what this represents.

CONSTRUCTION
• Premium twill blend — structured but breathable
• Gold-finished hardware (zipper, drawstring tips)
• Bridge Series embroidered patch — right thigh
• Reinforced pockets with hidden interior pocket
• Elastic waistband with external drawstring

FIT
Athletic cut, true to size. Hits just above the knee.

Ships within 4-6 weeks of pre-order close.

80 pieces. Oakland to San Francisco. This is the bridge.
```

---

## Collection Page Copy

### Template Structure

```
## H1: [Collection Name] Collection — [Positioning Line]

### Above-Fold Intro (2-3 sentences)
[What the collection is + who it's for + emotional hook]

### Below-Grid SEO Description (200-300 words)
[Story of the collection → what's included → how to choose → internal links]

### Cross-Sell Links
[Related collections with natural transitions]

### Meta Title / Description
[SEO-optimized with collection keywords]
```

### Black Rose Collection Page Example

**H1:** "Black Rose Collection — Dark Elegance from The Town"

**Intro:** "The Black Rose Collection is midnight given form. Built for those who find beauty in darkness and wear their Oakland roots like armor. Limited edition streetwear that doesn't whisper — it announces."

**Below-Grid Description:**
"Every piece in the Black Rose Collection carries the same DNA: heavyweight construction, dark palettes, and details that reveal themselves over time. From the signature Heavyweight Hoodie to the limited-edition jersey series celebrating Bay Area sports culture, Black Rose is where luxury streetwear meets Oakland identity.

The jersey series — limited to 80 pieces each — draws from the Bay's sports legacy: SF-inspired, Oakland heritage, Bay Bridge connection, and The Rose (Sharks). Each features the exclusive "Black is Beautiful" design with alternating rose-filled numbers and collection-specific sleeve patches.

Whether you're starting with the Black Rose Crewneck or going all-in on the Sherpa Jacket, every piece is built to layer, built to last, and built to be seen.

Browse the full Black Rose lineup below. New drops added throughout the season."

**Meta:** "Black Rose Collection — Limited Edition Oakland Streetwear | SkyyRose" (65 chars)
**Meta Desc:** "Dark elegance from The Town. Heavyweight hoodies, limited jerseys, and statement streetwear. 80-piece runs. Pre-order from SkyyRose." (134 chars)

---

## Anti-Patterns

- **DO NOT** write generic product copy — "This comfortable hoodie is made with quality materials" could be any brand
- **DO NOT** lead with features — "100% cotton" means nothing without "Softer than anything in your closet"
- **DO NOT** use "affordable luxury" — SkyyRose IS luxury. Period.
- **DO NOT** skip the cultural reference — every collection is rooted in a place and a story
- **DO NOT** write walls of text — use line breaks, bullets, sections for scannable listings
- **DO NOT** use generic CTAs — "Claim yours" beats "Add to cart"
- **DO NOT** fabricate specs — if you don't know the gsm or material, flag it with [NEEDS: fabric weight]
- **DO NOT** ignore pre-order status — every pre-order product must communicate limited availability

## Recovery

- **User gives minimal product info:** Ask for SKU, collection, and product type. Use memory for known products.
- **Unknown fabric/material specs:** Write around the gap with sensory language and flag `[NEEDS: material specs]`
- **Product doesn't fit a collection voice:** Default to Signature voice (most versatile) and note for user review.
- **Existing copy needs improvement:** Read current copy, identify top 3 weaknesses, rewrite with before/after comparison.
