---
name: wholesale-catalog
description: "Creates wholesale catalogs with product listings, tiered pricing, MOQs, and ordering information for retail buyers."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Wholesale Catalog

## When to Use This Skill

Use this skill when you need to:
- Create a wholesale catalog to pitch your products to retail buyers
- Structure tiered pricing with minimum order quantities
- Write product descriptions tailored for B2B retail purchasing decisions
- Build an ordering process that makes it easy for retailers to buy

**DO NOT** use this skill for consumer-facing product catalogs, dropshipping supplier pages, or internal inventory documents. This is for B2B wholesale sales materials.

---

## Core Principle

A WHOLESALE CATALOG SELLS PROFITABILITY TO THE RETAILER — EVERY PRODUCT DESCRIPTION, PRICE POINT, AND MARGIN NOTE MUST ANSWER: "WILL THIS SELL IN MY STORE AND MAKE ME MONEY?"

---

## Phase 1: Catalog Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Product line** | "Which products are available for wholesale?" | No default — must be provided |
| **Retail price (MSRP)** | "What is the suggested retail price for each product?" | No default — must be provided |
| **Wholesale pricing** | "What wholesale discount do you offer — 50% off MSRP, tiered, other?" | 50% off MSRP |
| **Minimum order quantities** | "What are your MOQs — per SKU and per order?" | 12 units per SKU, $200 order minimum |
| **Target retailers** | "What type of stores are you targeting — boutiques, specialty, chains?" | Independent boutiques and specialty shops |

**GATE: Confirm product list, pricing, and MOQs before building the catalog.**

---

## Phase 2: Catalog Structure

### Catalog Layout

```
## [Brand Name] Wholesale Catalog — [Season/Year]

### Table of Contents
1. Brand Story & Values
2. Product Lines
3. Pricing & MOQs
4. Ordering Information
5. Shipping & Terms
6. Contact
```

### Brand Introduction (1 paragraph)

Write a concise brand story that answers:
- What do you make and why?
- Who is your end customer?
- What makes your products sell well at retail?
- Include any notable press, awards, or retail partnerships

### Product Listing Format

For each product:

```
### [Product Name]
**SKU:** [SKU number]
**MSRP:** $XX.XX
**Wholesale:** $XX.XX (XX% margin for retailer)
**MOQ:** XX units
**Available variants:** [Colors, sizes, flavors]
**Dimensions/Weight:** [For shipping calculations]
**Key selling points:** [2-3 bullet points for the retailer's sales staff]
**Bestseller status:** [Yes/No — call out top performers]
```

---

## Phase 3: Pricing & Terms

### Tiered Pricing Table

```
## Wholesale Pricing Tiers

| Order Size | Discount off MSRP | Retailer Margin |
|-----------|-------------------|----------------|
| 12-47 units | 50% | 50% |
| 48-99 units | 55% | 55% |
| 100+ units | 60% | 60% |

**Opening order minimum:** $200
**Reorder minimum:** $100
**Payment terms:** Net 30 (after credit approval) or prepay via credit card
```

### Terms & Policies

Include these sections:
- **Payment terms** — Net 30, COD, prepay options
- **Shipping** — who pays, estimated costs, carrier preferences
- **Damages & returns** — defective product policy, no returns on undamaged goods
- **MAP policy** — Minimum Advertised Price requirements, if applicable
- **Exclusivity** — territorial or online exclusivity terms, if offered

---

## Phase 4: Ordering & Delivery

### Order Form Template

```
## Wholesale Order Form

**Retailer name:** _______________
**Contact name:** _______________
**Email:** _______________
**Shipping address:** _______________
**Tax ID / Resale certificate #:** _______________

| SKU | Product | Variant | Qty | Unit Price | Line Total |
|-----|---------|---------|-----|-----------|------------|
| | | | | | |

**Subtotal:** ___
**Shipping:** ___
**Total:** ___

**Payment method:** [ ] Net 30  [ ] Credit Card  [ ] Prepay
```

### Delivery Information

- Standard lead time for wholesale orders
- Rush order availability and surcharges
- Shipping carrier and method options
- Drop-shipping availability (if offered)

### Sell Sheet (One-Pager)

Create a condensed one-page sell sheet for trade shows and sales calls:
- Hero product image
- Top 3-5 SKUs with wholesale pricing
- Key brand differentiators
- QR code linking to full catalog or ordering portal
- Contact information

---

## Anti-Patterns

- **Consumer-focused descriptions** — retailers do not care about the emotional unboxing experience. They care about margins, sell-through, and reorder rates.
- **No MSRP listed** — retailers need to see their margin at a glance. Always show both wholesale and suggested retail.
- **Hidden MOQs** — burying minimums in fine print wastes everyone's time. State them clearly upfront.
- **No product photos** — wholesale buyers still need to see what they are buying. Include clean product shots.
- **Overly complex ordering** — if placing an order requires a phone call and three forms, you will lose buyers. Make it simple.

---

## Recovery

- **Retailer pushback on pricing:** Show the margin math. If 50% margin is not enough, explore volume tiers or exclusive product bundles.
- **No wholesale experience:** Start with a simple PDF catalog and direct ordering via email. Upgrade to an online portal as volume grows.
- **Products not suited for wholesale:** Not every product works at wholesale margins. If your COGS is too high for 50% off MSRP, consider a wholesale-specific product line.
- **Low initial orders:** Offer a risk-free trial — smaller opening order with easy reorder process. Lower the barrier to the first purchase.
- **Retailer wants exclusivity:** Consider territorial exclusivity in exchange for minimum annual purchase commitments.
