---
name: checkout-optimizer
description: Audits e-commerce checkout flows and recommends friction-reduction improvements to increase conversion rates. Use this skill when a user has cart abandonment issues, low checkout completion rates, or wants to optimize their online store's purchase flow.
allowed-tools: Read Write Bash(ls) WebFetch
---

# Checkout Optimizer

## When to Use This Skill

- User reports high cart abandonment rates (industry average is ~70%)
- User wants to improve checkout completion or conversion rate
- User is launching a new store and wants checkout best practices
- User is switching e-commerce platforms and needs to design the checkout flow
- User notices drop-off at a specific step in their checkout funnel

## Core Principle

EVERY EXTRA FIELD, CLICK, OR PAGE IN CHECKOUT IS A REASON TO LEAVE — REMOVE EVERYTHING THAT DOES NOT DIRECTLY COMPLETE THE PURCHASE.

## Workflow

### Phase 1: Gather Current State

1. Identify the e-commerce platform (Shopify, WooCommerce, Squarespace, custom)
2. Get current metrics if available:
   - Cart abandonment rate
   - Checkout completion rate
   - Average order value
   - Top exit pages in funnel
3. Map the current checkout steps (how many pages/steps from cart to confirmation)
4. List all form fields currently required

### Phase 2: Audit Against Friction Checklist

5. Score the checkout against these 15 friction points:

| # | Friction Point | Impact | Status |
|---|---------------|--------|--------|
| 1 | Guest checkout available (no forced account creation) | CRITICAL | |
| 2 | Single-page or accordion checkout (not multi-page) | HIGH | |
| 3 | Only essential form fields (name, email, address, payment) | HIGH | |
| 4 | Auto-fill enabled for address and payment fields | HIGH | |
| 5 | Express payment options (Apple Pay, Google Pay, PayPal) | HIGH | |
| 6 | Order summary visible throughout checkout | MEDIUM | |
| 7 | Shipping costs shown before checkout (no surprise fees) | CRITICAL | |
| 8 | Trust badges visible (SSL, payment logos, guarantee) | MEDIUM | |
| 9 | Progress indicator showing current step | MEDIUM | |
| 10 | Mobile-optimized (large tap targets, no horizontal scroll) | CRITICAL | |
| 11 | Error messages are inline and specific (not top-of-page) | MEDIUM | |
| 12 | Promo code field is collapsed (not prominently displayed) | LOW | |
| 13 | Cart persistence (items saved if user leaves and returns) | HIGH | |
| 14 | Return policy and contact info accessible from checkout | MEDIUM | |
| 15 | Confirmation page with order number and next steps | LOW | |

6. **GATE: Any CRITICAL items marked as failing must be the top priority recommendations**

### Phase 3: Generate Recommendations

7. Produce a prioritized fix list, ordered by impact:
   - Priority 1 (do immediately): CRITICAL friction points that are failing
   - Priority 2 (do this week): HIGH friction points that are failing
   - Priority 3 (do this month): MEDIUM and LOW items

8. For each recommendation, provide:
   - The specific change to make
   - How to implement it on their platform
   - Expected impact (with realistic conversion improvement range)

### Phase 4: Abandoned Cart Recovery

9. If cart abandonment is the primary concern, add a recovery sequence:
   - Email 1 (1 hour after abandonment): Cart reminder with product images
   - Email 2 (24 hours): Social proof or review highlight
   - Email 3 (72 hours): Final nudge with small incentive (free shipping or 10% off)

10. Provide email templates for each touch

### Phase 5: Deliver

11. Output the complete audit scorecard
12. Output prioritized recommendations with implementation steps
13. If applicable, output abandoned cart email sequence

## Example 1: Shopify Store Selling Handmade Jewelry

**Current state:**
- Platform: Shopify
- Cart abandonment: 78%
- Checkout: 3-page checkout (info, shipping, payment)
- Form fields: 14 fields including phone, company name, apt/suite
- No guest checkout (requires account)
- No express payment options
- Shipping costs only shown on page 2

**Audit Scorecard:**

| # | Friction Point | Status | Notes |
|---|---------------|--------|-------|
| 1 | Guest checkout | FAIL | Account required — top priority fix |
| 2 | Single-page checkout | FAIL | 3 pages currently |
| 3 | Essential fields only | FAIL | 14 fields, should be 8 |
| 4 | Auto-fill enabled | PASS | Shopify default |
| 5 | Express payments | FAIL | No Apple Pay, Google Pay, or PayPal |
| 6 | Order summary visible | PASS | Sidebar summary on desktop |
| 7 | Shipping costs pre-checkout | FAIL | Hidden until page 2 |
| 8 | Trust badges | FAIL | No badges visible |
| 9 | Progress indicator | PASS | Shopify default breadcrumbs |
| 10 | Mobile-optimized | PASS | Shopify default responsive |
| 11 | Inline error messages | PASS | Shopify default |
| 12 | Collapsed promo field | FAIL | Prominent field causing exit to search for codes |
| 13 | Cart persistence | PASS | Shopify default |
| 14 | Return policy accessible | FAIL | No link in checkout |
| 15 | Confirmation page | PASS | Standard Shopify |

**Score: 7/15 passing**

**Prioritized Recommendations:**

**Priority 1 — Do immediately:**

1. **Enable guest checkout**
   - Shopify Admin > Settings > Checkout > Customer accounts > "Accounts are optional"
   - Expected impact: 5-10% reduction in abandonment

2. **Show shipping costs on product pages or cart page**
   - Add shipping calculator widget to cart page
   - Or use flat-rate shipping and display it on product pages: "Flat rate $5.95 shipping"
   - Expected impact: 8-12% reduction in abandonment

3. **Enable express payment options**
   - Shopify Admin > Settings > Payments > Enable Shopify Payments (includes Apple Pay, Google Pay)
   - Add PayPal Express as secondary option
   - Expected impact: 3-7% increase in mobile conversions

**Priority 2 — Do this week:**

4. **Remove unnecessary form fields**
   - Remove: Company name, Apt/Suite (make optional), Phone (make optional)
   - Keep: Email, First name, Last name, Address, City, State, ZIP, Country
   - Shopify Admin > Settings > Checkout > Form options
   - Expected impact: 2-4% improvement in completion rate

5. **Collapse the promo code field**
   - Use Shopify's "Show discount code field" toggle or a custom CSS solution to collapse it behind a "Have a code?" link
   - Expected impact: Reduces exits from users leaving to search for discount codes

**Priority 3 — Do this month:**

6. **Add trust badges** — payment method logos and "Secure Checkout" badge near the payment button
7. **Add return policy link** — footer link in checkout to your returns page
8. **Switch to one-page checkout** — Shopify now offers one-page checkout for all plans

## Example 2: WooCommerce Store Selling Specialty Coffee

**Current state:**
- Platform: WooCommerce
- Cart abandonment: 72%
- Checkout: Single-page (WooCommerce default)
- 11 form fields
- Guest checkout enabled
- No express payments
- Free shipping threshold at $50 but not communicated until cart

**Audit Score: 9/15 passing**

**Top 3 Recommendations:**

1. **Add express payment (Stripe + PayPal Express)**
   - Install WooCommerce Stripe Gateway plugin
   - Enable Apple Pay and Google Pay in Stripe dashboard
   - Add PayPal Checkout plugin for PayPal Express buttons
   - Place express payment buttons above the standard form
   - Expected impact: 4-8% conversion improvement on mobile

2. **Show free shipping progress on product pages and cart**
   - Add a banner: "Free shipping on orders over $50 — you're $XX away!"
   - Use the "Free Shipping Progress Bar" plugin or add custom code to cart page
   - Expected impact: 10-15% increase in AOV for orders between $30-$49

3. **Reduce form fields from 11 to 7**
   - Remove: Company, Phone (or make optional), Order notes
   - Combine First/Last name into single "Full Name" field if possible
   - Expected impact: 2-3% completion rate improvement

**Abandoned Cart Recovery Email — Email 1 (1 hour):**

```
Subject: You left some great coffee behind

Hey [First Name],

Looks like you were checking out our [Product Name] but didn't finish your order.

No worries — your cart is saved and ready when you are.

[CART CONTENTS WITH PRODUCT IMAGE]
[Product Name] — [Size] — $XX.XX

Complete Your Order → [Button linking to saved cart]

Questions about our coffee? Just reply to this email — we're real
people who love talking about coffee.

Cheers,
The Summit Roasters Team

P.S. Orders over $50 ship free.
```

## Recovery and Fallback

- If the user cannot provide current metrics, use industry benchmarks: 70% cart abandonment is average, 3% checkout conversion is typical for small e-commerce
- If the user is on a platform that limits checkout customization (like basic Squarespace), focus on what can be changed: express payments, field reduction, and pre-checkout improvements
- If the audit reveals the checkout is already well-optimized (12+ passing), shift focus to pre-checkout friction: product page clarity, shipping communication, and cart page design
- If the user lacks technical ability to implement changes, prioritize platform-native settings changes over custom code solutions

## Constraints

- Do not recommend removing email from checkout — it is required for order confirmation and receipts
- Do not recommend removing address fields for physical product stores
- Conversion improvement estimates must be given as ranges, not exact numbers
- Do not recommend specific apps or plugins without confirming platform compatibility
- Never suggest dark patterns (hidden fees, forced upsells blocking checkout, confusing opt-outs)
- All recommendations must be implementable without a developer unless otherwise noted
- Focus on the 3-5 highest-impact changes, not an exhaustive list of 20 minor tweaks
