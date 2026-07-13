---
name: store-page-audit
description: "Audits e-commerce store pages for conversion optimization with layout, copy, trust signals, and technical recommendations."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Store Page Audit

## When to Use This Skill

Use this skill when you need to:
- Audit product pages, collection pages, or checkout flows for conversion issues
- Identify layout, copy, and trust signal gaps reducing sales
- Create a prioritized list of fixes to improve conversion rate
- Benchmark page elements against e-commerce best practices

**DO NOT** use this skill for full website redesigns, blog audits, or technical SEO site audits. This is for e-commerce store page conversion optimization only.

---

## Core Principle

EVERY ELEMENT ON A PRODUCT PAGE EITHER MOVES THE BUYER TOWARD CLICKING "ADD TO CART" OR CREATES FRICTION THAT PUSHES THEM AWAY — AUDIT FOR BOTH.

---

## Phase 1: Page Information

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Page URL or screenshot** | "Share the page URL or a screenshot of the page to audit." | No default — must be provided |
| **Page type** | "Is this a product page, collection page, homepage, or cart/checkout?" | Product page |
| **Current conversion rate** | "What is the current conversion rate for this page?" | Unknown — benchmark against 2-3% industry average |
| **Platform** | "What platform — Shopify, WooCommerce, Squarespace, other?" | Shopify |
| **Top concern** | "What do you think is the biggest issue?" | General audit — check everything |

**GATE: Confirm page details and priorities before conducting the audit.**

---

## Phase 2: Audit Framework

Evaluate the page across six categories. Score each 1-5 (1 = critical issues, 5 = optimized).

### 1. Above-the-Fold Impact

- [ ] Product image is high quality, zoomable, and shows the product in use
- [ ] Product title is clear and includes relevant search terms
- [ ] Price is visible immediately (no scrolling required)
- [ ] Primary CTA button ("Add to Cart") is visible without scrolling
- [ ] Unique value proposition or key benefit is stated near the title

### 2. Product Copy & Description

- [ ] Description leads with benefits, not features
- [ ] Bullet points break up key specs and selling points
- [ ] Copy addresses the top 3 objections the buyer would have
- [ ] Size, dimensions, materials, or specs are easy to find
- [ ] Tone matches the brand and target audience

### 3. Trust Signals

- [ ] Customer reviews are visible on the page (star rating + count)
- [ ] Shipping information is clear (cost, timeline, free shipping threshold)
- [ ] Return/refund policy is accessible without leaving the page
- [ ] Payment security badges or icons are visible near checkout
- [ ] Social proof elements — testimonials, user photos, "X sold" counters

### 4. Visual & Layout

- [ ] Multiple product images (5+ recommended) showing different angles
- [ ] Consistent image style and quality across the page
- [ ] Mobile layout is clean with easy tap targets
- [ ] White space is used effectively — page does not feel cluttered
- [ ] CTA button color contrasts with the page background

### 5. Technical Performance

- [ ] Page loads in under 3 seconds
- [ ] Images are compressed and optimized
- [ ] No broken links, missing images, or layout shifts
- [ ] Page is fully functional on mobile devices
- [ ] Structured data markup is present for rich search results

### 6. Conversion Path

- [ ] Add-to-cart button is sticky or repeated on long pages
- [ ] Upsell or cross-sell recommendations are present
- [ ] Urgency or scarcity elements are used authentically
- [ ] Cart is easy to access and modify
- [ ] Checkout process has minimal steps and friction

---

## Phase 3: Audit Report

### Report Format

```
## Store Page Audit Report

**Page:** [URL or page name]
**Date:** [Date]
**Overall Score:** [X/30]

### Scores by Category

| Category | Score (1-5) | Priority |
|----------|------------|----------|
| Above-the-Fold | 3 | High |
| Product Copy | 2 | Critical |
| Trust Signals | 4 | Low |
| Visual & Layout | 3 | Medium |
| Technical | 5 | None |
| Conversion Path | 2 | Critical |

### Critical Fixes (Do These First)

1. **[Issue]** — [What is wrong] → [Specific fix]
2. **[Issue]** — [What is wrong] → [Specific fix]

### High Priority Improvements

3. **[Issue]** — [What is wrong] → [Specific fix]

### Medium Priority Enhancements

4. **[Issue]** — [What is wrong] → [Specific fix]

### Low Priority Polish

5. **[Issue]** — [What is wrong] → [Specific fix]
```

---

## Phase 4: Action Plan

### Implementation Roadmap

Organize fixes into sprints:

| Sprint | Timeframe | Focus | Expected Impact |
|--------|-----------|-------|----------------|
| Sprint 1 | This week | Critical fixes — CTA visibility, copy rewrites | Highest conversion lift |
| Sprint 2 | Week 2 | Trust signals and social proof additions | Reduced cart abandonment |
| Sprint 3 | Week 3-4 | Visual improvements and technical optimization | Better user experience |
| Sprint 4 | Month 2 | A/B testing top changes to validate impact | Data-driven refinement |

### Before/After Copy Examples

Provide rewritten copy for the top 2-3 issues identified. Show the current version alongside the improved version so the user can implement immediately.

---

## Anti-Patterns

- **Auditing without knowing the audience** — recommendations must fit the buyer, not generic best practices.
- **Recommending a full redesign** — incremental improvements are faster and measurable. Do not suggest starting over.
- **Ignoring mobile** — 60%+ of e-commerce traffic is mobile. Every recommendation must work on small screens.
- **Adding urgency dishonestly** — fake countdown timers and inflated "X people viewing" counters erode trust.
- **Focusing only on visuals** — a beautiful page with weak copy still will not convert.

---

## Recovery

- **No page URL available:** Ask for screenshots or a screen recording. Audit from visuals if the live page cannot be accessed.
- **No conversion data:** Benchmark against industry averages (2-3% for most e-commerce). Focus on obvious friction points.
- **User overwhelmed by recommendations:** Prioritize the top 3 fixes that will have the largest impact. Save the rest for later.
- **Platform limitations:** Note which recommendations require developer help vs. what can be done in the platform's built-in editor.
- **Disagreement on design choices:** Back recommendations with data or examples from high-converting stores in their niche.
