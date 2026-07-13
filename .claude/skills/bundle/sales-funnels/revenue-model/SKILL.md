---
name: revenue-model
description: "Designs revenue models with pricing tiers, unit economics, LTV calculations, and growth projections. Use when planning or validating your business revenue strategy."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Revenue Model

## When to Use This Skill

Use this skill when you need to:
- Design a revenue model with pricing tiers and unit economics
- Calculate customer lifetime value (LTV) and acquisition cost (CAC) targets
- Build financial projections for the next 12-24 months
- Validate whether a business idea or pricing strategy is financially viable

**DO NOT** use this skill for full financial statements, investor pitch decks, or tax planning. This is for revenue modeling and unit economics analysis.

---

## Core Principle

A REVENUE MODEL IS NOT A WISH LIST — EVERY NUMBER MUST BE GROUNDED IN REAL DATA OR DEFENSIBLE ASSUMPTIONS, AND THE MODEL MUST SHOW THE PATH FROM WHERE YOU ARE TO WHERE YOU WANT TO BE.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Business type** | "What do you sell?" | No default — must be provided |
| **Current revenue** | "What are you making now? (monthly or annually)" | Pre-revenue or early stage |
| **Revenue goal** | "What's your 12-month revenue target?" | No default — must be provided |
| **Pricing** | "What do you charge? (one-time, subscription, per-project)" | No default — must be provided |
| **Customer count** | "How many customers/clients do you have?" | Under 50 |
| **Acquisition channels** | "How do you get customers?" | Organic + referrals |
| **Margins** | "What's your approximate profit margin per sale?" | 70%+ for digital, varies for services |

**GATE: Confirm inputs before building the model.**

---

## Phase 2: Revenue Architecture

### Revenue Stream Mapping

```
## Revenue Streams

**Stream 1: [Core Product/Service]**
- Type: [One-time / Subscription / Per-project]
- Price: $[X]
- Frequency: [Monthly / Annual / Per engagement]
- Margin: [X]%

**Stream 2: [Secondary Product/Service]**
- Type: [One-time / Subscription / Per-project]
- Price: $[X]
- Frequency: [Monthly / Annual / Per engagement]
- Margin: [X]%

**Stream 3: [Additional Revenue]** (if applicable)
- Type: [Affiliate / Ads / Licensing / etc.]
```

### Unit Economics

```
## Unit Economics

**Average Revenue Per Customer (ARPC):** $[X]
**Cost of Goods Sold (COGS):** $[X] per customer
**Gross Margin Per Customer:** $[X] ([X]%)
**Customer Acquisition Cost (CAC):** $[X]
**CAC Payback Period:** [X] months
**Customer Lifetime Value (LTV):** $[X]
**LTV:CAC Ratio:** [X]:1 (target: 3:1 or higher)

**Churn Rate (if subscription):** [X]% monthly
**Average Customer Lifespan:** [X] months
```

**GATE: Approve the revenue architecture before running projections.**

---

## Phase 3: Financial Projections

### 12-Month Revenue Projection

Build a month-by-month projection:

```
## Monthly Revenue Projection

| Month | New Customers | Total Customers | Revenue | Cumulative |
|-------|--------------|-----------------|---------|------------|
| 1 | [X] | [X] | $[X] | $[X] |
| 2 | [X] | [X] | $[X] | $[X] |
| ... | | | | |
| 12 | [X] | [X] | $[X] | $[X] |

**Annual Revenue:** $[X]
**Average Monthly Revenue:** $[X]
**Growth Rate:** [X]% month-over-month
```

### Scenario Analysis

```
## Three Scenarios

**Conservative (80% confidence):**
- [X] new customers/month, [X]% churn
- Annual revenue: $[X]

**Base Case (50% confidence):**
- [X] new customers/month, [X]% churn
- Annual revenue: $[X]

**Aggressive (20% confidence):**
- [X] new customers/month, [X]% churn
- Annual revenue: $[X]
```

### Revenue Levers

Identify the 3-5 biggest levers for growing revenue:
1. Increase customer acquisition volume
2. Raise prices or add premium tier
3. Reduce churn (for subscription models)
4. Increase average order value (upsells, cross-sells)
5. Introduce new revenue streams

---

## Phase 4: Polish

### 1. Key Assumptions Document

List every assumption the model is built on:
- Customer acquisition rate and growth
- Churn rate assumptions
- Pricing stability
- Market size constraints
- Seasonal fluctuations

### 2. Break-Even Analysis

Calculate the number of customers or revenue needed to cover:
- Fixed costs (tools, software, overhead)
- Variable costs (fulfillment, support)
- Desired owner salary

### 3. Model Review Schedule

- Monthly: compare actual vs. projected, adjust assumptions
- Quarterly: revise the full 12-month projection
- Annually: rebuild the model from scratch with updated data

---

## Anti-Patterns

- **Hockey stick projections with no basis** — showing 10x growth without a plan to acquire customers is fantasy, not modeling.
- **Ignoring churn** — subscription models without churn estimates are wildly inaccurate. Even 5% monthly churn loses half your customers in a year.
- **Single scenario planning** — only modeling the best case leaves you unprepared for reality.
- **Forgetting CAC** — revenue means nothing if customer acquisition costs more than the customer is worth.
- **Static pricing** — the model should show how pricing changes affect the entire projection. Build in flexibility.

---

## Recovery

- **No data to base projections on:** Start with industry benchmarks and the user's current acquisition rate. Model from reality, not wishes.
- **Pre-revenue business:** Build the model around break-even first. How many customers at what price covers costs?
- **Multiple products, complex model:** Focus on the core revenue stream first. Add secondary streams after the primary model is solid.
- **User wants guaranteed numbers:** Explain that models are estimates based on assumptions. The value is in understanding the levers, not predicting exact numbers.
