---
name: exchange-policy
description: "Writes exchange policies with eligibility criteria, process steps, customer communication templates, and exception handling. Use when establishing or improving your exchange process."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Exchange Policy

## When to Use This Skill

Use this skill when you need to:
- Write a clear exchange policy for your e-commerce store
- Design the exchange process workflow from request to resolution
- Create customer communication templates for exchange scenarios
- Establish exception handling guidelines for edge cases

**DO NOT** use this skill for refund policies, warranty claims, or customer service training. This is for product exchange policies and processes specifically.

---

## Core Principle

A GOOD EXCHANGE POLICY KEEPS THE REVENUE AND THE CUSTOMER — MAKE EXCHANGING EASIER THAN RETURNING AND CUSTOMERS WILL CHOOSE TO STAY.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Product types** | "What products are eligible for exchange? (all, apparel only, specific categories)" | All products |
| **Exchange window** | "How many days after purchase can customers exchange?" | 30 days |
| **Condition requirements** | "Must items be unused, unworn, with tags?" | Unused, original packaging |
| **Exchange types** | "Same product different size/color, or exchange for a different product?" | Same product, different variant |
| **Shipping cost** | "Who pays for exchange shipping? (customer, company, split)" | Company pays |
| **Current pain points** | "What exchange issues do you deal with most?" | Sizing exchanges, slow process |
| **Platform** | "E-commerce platform? (Shopify, WooCommerce, etc.)" | Shopify |

**GATE: Confirm brief before writing the policy.**

---

## Phase 2: Design

### Exchange Policy Framework

1. **Eligibility** — what can be exchanged, what cannot
2. **Timeframe** — days from purchase or delivery
3. **Condition** — required product condition for exchange
4. **Process** — how to initiate and complete an exchange
5. **Shipping** — who pays, how labels are provided
6. **Exceptions** — sale items, personalized items, final sale
7. **Processing time** — how long from receipt to new shipment

### Exchange Workflow

```
Customer requests exchange → Team reviews eligibility →
Approved: prepaid label sent → Customer ships item →
Item received and inspected → New item shipped →
Tracking sent to customer → Exchange complete
```

**GATE: Present the policy framework for approval before writing the full document.**

---

## Phase 3: Build

### Deliverables

**1. Customer-Facing Exchange Policy**
- Plain-language policy for the website
- Organized with clear headings (What, When, How, Exceptions)
- FAQ section addressing top 5 exchange questions
- Step-by-step exchange process (numbered, no ambiguity)

**2. Internal Exchange SOP**
- Step-by-step process for the team handling exchanges
- Decision tree for eligibility evaluation
- Inspection criteria for received items
- Inventory management (returning exchanged item to stock or writing off)

**3. Customer Communication Templates**
- Exchange request acknowledgment email
- Exchange approved email (with label and instructions)
- Exchange denied email (with reason and alternatives)
- New item shipped confirmation email
- Exchange complete follow-up email

**4. Exception Handling Guide**
| Scenario | Policy | Action |
|----------|--------|--------|
| Item outside exchange window | Deny if over 45 days, consider if 31-45 | Manager discretion |
| Item worn/damaged by customer | Deny exchange | Offer discount on new purchase |
| Item out of stock in requested size | Offer alternative or store credit | Customer chooses |
| International exchange | Customer pays return shipping | Provide customs guidance |
| Gift exchange (no receipt) | Exchange for store credit at current price | Verify product is carried |

---

## Phase 4: Polish

### Policy Placement

- Link prominently from product pages, cart, and footer navigation
- Include exchange policy summary in order confirmation email
- Add to FAQ page and customer service knowledge base

### Measurement

Track monthly:
- Exchange request volume (as % of orders)
- Top exchange reasons (size, color, defect, preference)
- Exchange completion rate (started vs. completed)
- Time to resolution (request to new item delivered)
- Post-exchange retention (do exchange customers buy again?)

### Policy Review

- Quarterly: review exchange data and adjust policy for recurring issues
- Seasonally: adjust for holiday gift exchanges (extended window in Dec-Jan)
- On trigger: update when adding new product categories or selling internationally

---

## Example 1: Apparel Brand (Sizing Exchanges)

**Policy:** Free exchanges within 30 days of delivery. Items must be unworn with tags attached. Prepaid return label provided. New size shipped within 2 business days of receiving the return. Exchange window extended to 60 days during holiday season (Nov 15 - Jan 15).

## Example 2: Home Goods Store (Product Exchanges)

**Policy:** Exchanges within 14 days of delivery for same-value or higher-value items (customer pays difference). Items must be unused and in original packaging. Customer pays return shipping. Exchanges processed within 5 business days.

---

## Anti-Patterns

- **Hidden or hard to find** — a policy buried in fine print creates frustrated customers who call support. Make it visible and easy to find.
- **Too restrictive** — "No exchanges under any circumstances" loses customers and generates chargebacks. Some flexibility builds loyalty.
- **Too generous without tracking** — unlimited exchanges with no tracking enables abuse. Monitor for patterns.
- **Slow processing** — a 3-week exchange process makes customers wish they had just returned and rebought. Speed builds trust.
- **Making exchanges harder than returns** — if returning for a refund is easier than exchanging, customers will choose the refund. Make exchanges the path of least resistance.

---

## Recovery

- **High exchange rate on one product:** Investigate the root cause. If sizing is the issue, improve the size guide. If quality is the issue, address the product.
- **Customer wants to exchange but outside the window:** Use judgment. A customer at day 35 of a 30-day window who is polite and loyal deserves an exception. Document the exception.
- **Exchange item is out of stock:** Offer store credit, an alternative product, or a refund. Never leave the customer in limbo waiting for a restock.
- **Fraud concerns:** Track exchange patterns per customer. Flag accounts with unusually high exchange frequency for review. Implement verification for high-value exchanges.
