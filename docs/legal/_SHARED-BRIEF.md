# SkyyRose Store Policies — Shared Source of Truth

> **This file is the single source of truth (SSOT) for every store policy.**
> Every cross-cutting value below MUST be identical across all six policy documents.
> If a value here changes, all docs that reference it change together.
> Drafted 2026-06-05. Grounded in the live skyyrose.co site + theme source — not invented.

---

## Legal entity & identity

| Field | Value |
|-------|-------|
| Legal entity | **SkyyRose LLC** |
| Brand / trade name | SkyyRose (styled "SKYYROSE") |
| Website | https://skyyrose.co |
| Governing law / jurisdiction | State of California, United States |
| Principal place of business | Oakland, California *(city/state confirmed; full street address = placeholder)* |
| Effective date / Last updated | **June 5, 2026** *(replaces the stale "February 25, 2026" on the current live pages)* |
| Currency | USD |

## Contact channels (use exactly these)

| Purpose | Email |
|---------|-------|
| Privacy / data requests | privacy@skyyrose.co |
| Legal / terms / IP | legal@skyyrose.co |
| Orders / returns / shipping / support | support@skyyrose.co |

## Placeholders — RESOLVED 2026-06-05 (founder-confirmed; filled into all six docs)

- Registered mailing address → **SkyyRose LLC, 3400 Cottage Way, Suite G2, Sacramento, CA 95825** (legal-notice / CCPA address; brand-origin "Oakland" header references intentionally kept)
- Phone → **line removed** (founder direction)
- EU/UK representative → **not required** (Art.27 GDPR / UK GDPR)
- Email marketing provider → **Klaviyo** (verified via Klaviyo MCP, account RP9Mvx)
- Arbitration provider (ToS) → **American Arbitration Association (AAA)**

Still open before publish: licensed-attorney review (esp. ToS arbitration / class-waiver), then publish as WP pages + footer links.

## Products & audience

- Luxury streetwear apparel & accessories.
- Collections: **Black Rose, Love Hurts, Signature, Kids Capsule**.
- **Kids Capsule** sells children's apparel, but the site is a **general-audience commercial site**; purchases are made by adults. COPPA stance: *we do not knowingly collect personal information from children under 13.*

## Shipping (CANONICAL — from theme `inc/woocommerce.php:29`, NOT the stale live page)

| Method | Time | Cost |
|--------|------|------|
| US Standard | 5–7 business days | **$7.95** |
| US Express | 2–3 business days | **$14.95** |
| US Free Standard | 5–7 business days | **Orders $150+** |
| International (40+ countries) | ~10–14 business days | Calculated at checkout by destination + weight |

- Order processing: 1–3 business days (up to 5 during collection drops / holidays).
- International duties & import taxes = **recipient's responsibility**, not included in shipping cost.

## Returns & exchanges (CANONICAL — from `template-shipping-returns.php`)

- **30-day** return window from delivery.
- Condition: unworn, original condition, **tags attached**, original packaging.
- US returns: **prepaid label**; refund issued **within 5–7 business days** of receipt to original payment method.
- **Non-returnable:** items marked "Final Sale", worn/washed/altered items, items without tags, gift cards, customized pieces.
- Exchanges: **free for US**; international customers pay return shipping, replacement reshipped free.

## Pre-orders

- Card **charged at time of pre-order**.
- Estimated ship dates shown on each product page; pre-order items ship separately from in-stock items.
- Cancellable for full refund **up to 48 hours before** the estimated ship date; after that, standard return policy applies once delivered.

## Payments & data recipients (GROUNDED — live-site grep 2026-06-05)

| Processor / recipient | Role | Privacy relevance |
|-----------------------|------|-------------------|
| Stripe | Card payments | PCI-handled; card data never stored on SkyyRose servers |
| PayPal | Alternative payments | Redirect/checkout |
| WordPress.com / Automattic (Jetpack) | Hosting, stats, security, Instant Search, social sharing | First-party host + analytics |
| Google Analytics | Site analytics | Cookies; advertising features |
| **TikTok pixel** | **Advertising** | **Cross-context behavioral advertising → CPRA "share"** |
| WooCommerce | E-commerce engine | Session/cart cookies |

## Compliance flags every relevant doc must honor

- **CCPA/CPRA (California):** entity is a CA LLC → full California consumer-rights section + **"Do Not Sell or Share My Personal Information"** (TikTok pixel + GA = "sharing").
- **GDPR/UK GDPR:** ships to 40+ countries incl. EU/UK → lawful bases, data-subject rights, transfers, `[EU/UK REPRESENTATIVE]` placeholder.
- **COPPA:** Kids Capsule → "we do not knowingly collect from under-13" clause.
- **ADA / WCAG 2.1 AA:** accessibility statement targets WCAG 2.1 Level AA.

## Mandatory on EVERY document

1. An attorney-review disclaimer banner at the top (these are templates, not legal advice).
2. `Last updated: June 5, 2026`.
3. Contact block using the exact emails above.
4. Consistent cross-references by these exact doc titles: **Privacy Policy, Terms of Service, Refund & Return Policy, Shipping Policy, Cookie Policy, Accessibility Statement**.

## The six documents

1. `privacy-policy.html`
2. `terms-of-service.html`
3. `refund-return-policy.html`
4. `shipping-policy.html`
5. `cookie-policy.html`
6. `accessibility-statement.html`
