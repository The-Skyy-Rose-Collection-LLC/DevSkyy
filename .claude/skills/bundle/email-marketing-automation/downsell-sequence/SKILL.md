---
name: downsell-sequence
description: "Builds downsell offers and sequences for prospects who decline the primary offer. Use when you need to capture revenue from people who say no to your main pitch."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Downsell Sequence

## When to Use This Skill

Use this skill when you need to:
- Create a downsell offer for prospects who decline your primary product
- Write downsell page copy and follow-up email sequences
- Design a product ladder that captures revenue at multiple price points
- Build a downsell into an existing sales funnel or checkout flow

**DO NOT** use this skill for upsells (higher-priced offers), order bumps, or discount promotions to existing customers. This is for structured downsell offers after a prospect says no.

---

## Core Principle

A DOWNSELL IS NOT A DISCOUNT ON THE SAME THING — IT IS A DIFFERENT OFFER AT A LOWER PRICE POINT THAT STILL SOLVES THE PROSPECT'S PROBLEM, JUST IN A SMALLER WAY.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Primary offer** | "What did the prospect decline?" | No default — must be provided |
| **Primary price** | "What was the price they said no to?" | No default — must be provided |
| **Reason for decline** | "Why do most people say no? (price, timing, trust, fit)" | Price is the main objection |
| **Existing lower-tier product** | "Do you have a smaller version of this offer?" | Will design one |
| **Downsell trigger** | "Where does the no happen? (sales page exit, checkout abandon, after pitch)" | Sales page exit or post-webinar |

**GATE: Confirm the brief before designing the downsell.**

---

## Phase 2: Downsell Design

### Downsell Types

Choose the right downsell structure:

**1. Lite Version** — same product, fewer features or modules
- Full course ($497) → Core modules only ($197)
- Best for: info products, courses, memberships

**2. Payment Plan** — same product, spread over time
- $497 one-time → 3 payments of $197
- Best for: price objection with high perceived value

**3. Different Format** — same knowledge, lower-cost delivery
- Group coaching ($997) → Self-paced course ($297)
- Best for: service-based businesses

**4. Starter/Essentials** — entry-level version
- Full toolkit ($197) → Starter pack ($47)
- Best for: digital products, templates, tools

### Downsell Pricing Rules

```
## Pricing Guidelines

- Downsell should be 30-60% of the primary offer price
- Must feel like a genuine deal, not a punishment for saying no
- Payment plans: total can be 10-20% more than one-time price (financing premium)
- Never downsell to less than $17 — below that, use a tripwire instead
```

**GATE: Approve the downsell concept before writing copy.**

---

## Phase 3: Write Downsell Copy

### Downsell Page Structure

1. **Headline** — acknowledge their decision, present the alternative
2. **Empathy paragraph** — "I get it, [primary offer] might not be right for you right now"
3. **Introduce the downsell** — here is what IS available at a lower investment
4. **What's included** — clear bullet list
5. **Price reveal** — with anchor to original offer value
6. **CTA** — "Get [Downsell Product] for $X"
7. **No thanks link** — always provide a way to decline gracefully

### Copy Rules

- Never guilt-trip or pressure — the prospect already said no once
- Frame as a genuine alternative, not a lesser version
- Lead with what they GET, not what's removed
- Keep the page to 200-400 words — if they declined a long sales page, a shorter one converts better
- Include a "No thanks, I'll pass" link that is visible and not hidden

### Example Downsell Page

```
## Wait — before you go...

I totally understand that [Primary Product] might not be the right fit right now.

But I don't want you to leave empty-handed, because I know you're serious about [desired outcome].

That's why I put together [Downsell Product Name] — it gives you the essential tools to get started at a fraction of the investment.

Here's what's included:
✓ [Core component 1]
✓ [Core component 2]
✓ [Core component 3]

Instead of $497, you can get started for just $197.

[Get Instant Access for $197]

No thanks, I'll pass for now → [exit link]
```

### Follow-Up Email Sequence

If they also decline the downsell, send a 2-email follow-up:

**Email 1 (24 hours later):** Share a free resource related to their problem. No pitch. Build goodwill.
**Email 2 (5 days later):** Soft mention of the downsell with a deadline. "The offer is available for 3 more days."

---

## Phase 4: Polish

### 1. Funnel Integration Map

Show where the downsell fits in the complete funnel flow:
```
Sales Page → [No] → Downsell Page → [No] → Exit + Email Follow-Up
                                    → [Yes] → Checkout → Thank You
```

### 2. Conversion Benchmarks

- Downsell page conversion: 10-20% of people who declined the primary offer
- Payment plan acceptance: 30-50% of price-objection declines
- Follow-up email recovery: additional 3-5%

### 3. Implementation Checklist

- [ ] Downsell product created and ready for delivery
- [ ] Downsell page built with exit intent or decline trigger
- [ ] Payment processing configured for the lower price
- [ ] Follow-up emails scheduled for non-buyers
- [ ] Buyer tags set to exclude from further downsell messaging
- [ ] "No thanks" link works and leads to a clean exit

---

## Anti-Patterns

- **Discounting the same product** — slashing the price of the same offer feels desperate and trains buyers to wait for deals.
- **Aggressive downsell copy** — "You'd be crazy to pass this up!" after they already said no is combative.
- **No exit option** — trapping people on a downsell page without a "no thanks" link damages trust.
- **Multiple downsells in a row** — one downsell is strategic. Three downsell pages in sequence feels like a trap.
- **Downselling to existing customers** — never show a downsell to someone who already bought the primary offer.

---

## Recovery

- **No lower-tier product exists:** Extract 30-40% of the primary offer into a standalone product. Focus on the "quick win" components.
- **Primary offer is already low-priced ($47):** A downsell at $17-27 may work, but consider if a payment plan (2x $27) is more effective.
- **User says "just discount the main offer":** Explain that discounting the same offer devalues it. A different product at a lower price preserves the primary offer's positioning.
- **Low downsell conversion (under 5%):** The offer may not solve a genuine need. Revisit what problem the downsell addresses and whether the audience actually wants it.
