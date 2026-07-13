---
name: seasonal-inventory-plan
description: "Plans seasonal inventory with demand forecasting, ordering timelines, and clearance strategy to maximize revenue and minimize dead stock."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Seasonal Inventory Plan

## When to Use This Skill

Use this skill when you need to:
- Plan inventory purchases for an upcoming selling season
- Forecast demand based on historical sales and market trends
- Create ordering timelines that account for supplier lead times
- Design clearance and markdown strategies for end-of-season stock

**DO NOT** use this skill for evergreen inventory management, raw materials procurement, or service-based businesses without physical products.

---

## Core Principle

ORDER BASED ON DATA, NOT OPTIMISM — OVERSTOCK KILLS CASH FLOW AND UNDERSTOCK KILLS REVENUE. THE BEST SEASONAL PLAN BALANCES BOTH RISKS.

---

## Phase 1: Season Definition

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Season / event** | "What season or event are you planning for?" | No default — must be provided |
| **Product categories** | "Which product lines are seasonal?" | No default — must be provided |
| **Historical data** | "Do you have last year's sales data for this season? Share numbers or estimates." | No prior data — use industry benchmarks |
| **Supplier lead times** | "How far in advance do you need to place orders?" | 6-8 weeks |
| **Budget** | "What is your total inventory budget for this season?" | No default — must be provided |

### Season Brief

```
## Seasonal Inventory Brief

**Season:** Holiday 2024 (November 1 - December 31)
**Key products:** Candle gift sets, holiday-scented wax melts, ceramic holders
**Last year's revenue:** $28,000 across 3 product lines
**Growth target:** 30% increase ($36,400)
**Supplier lead time:** 8 weeks (order by September 1)
**Budget:** $12,000 for inventory
```

**GATE: Confirm the season brief before building the forecast.**

---

## Phase 2: Demand Forecast

### Forecasting Method

1. **Base forecast** — use last year's unit sales as the starting point
2. **Growth adjustment** — apply growth rate based on audience size increase, marketing spend, or market trends
3. **Product mix** — allocate percentages across categories based on historical performance
4. **Safety stock** — add 15-20% buffer for top sellers, 0% buffer for unproven items

### Forecast Template

```
## Demand Forecast

| Product | Last Year Units | Growth Factor | Forecast Units | Safety Stock | Order Qty |
|---------|----------------|---------------|---------------|-------------|-----------|
| Candle gift set (large) | 120 | 1.3x | 156 | +20% (31) | 187 |
| Candle gift set (small) | 200 | 1.3x | 260 | +15% (39) | 299 |
| Holiday wax melts (6-pack) | 340 | 1.2x | 408 | +15% (61) | 469 |
| Ceramic holder (new) | 0 | N/A | 80 | 0% | 80 |
```

### No Historical Data Approach

If no prior data exists:
- Start with a conservative estimate (sell-through rate of 60-70%)
- Order smaller initial quantities with a reorder plan
- Use pre-orders or waitlists to gauge demand before committing

---

## Phase 3: Ordering Timeline

### Timeline Template

Map every milestone backward from the first selling day:

```
## Ordering Timeline

**Season start:** November 1
**Key dates working backward:**

| Date | Action |
|------|--------|
| July 15 | Finalize product line and quantities |
| August 1 | Place orders with suppliers |
| September 1 | Receive and quality-check inventory |
| September 15 | Product photography and listing updates |
| October 1 | Pre-season marketing begins (email, social) |
| October 15 | Early access sale for VIP customers |
| November 1 | Full season launch |
| December 15 | Monitor stock levels — reorder fast-movers if possible |
| December 26 | Begin clearance pricing |
| January 15 | Final clearance — move remaining stock |
```

### Reorder Decision Points

Build triggers for mid-season reorders:
- If a product sells 50% of forecast in the first 30% of the season, reorder immediately
- If supplier can deliver within 2 weeks, keep a reorder option open for top 3 SKUs
- Set a "reorder cutoff date" beyond which new orders will not arrive in time

---

## Phase 4: Clearance & Post-Season Strategy

### Markdown Schedule

```
## Clearance Plan

| Timing | Discount | Goal |
|--------|----------|------|
| Last 2 weeks of season | 20% off | Move slow sellers before season ends |
| 1 week post-season | 30-40% off | Clear remaining seasonal stock |
| 2-3 weeks post-season | 50%+ off or bundle deals | Liquidate dead stock |
| 4+ weeks post-season | Donate, repurpose, or hold for next year | Zero remaining carrying cost |
```

### Leftover Inventory Options

- **Bundle with evergreen products** to move units without deep discounts
- **Offer as free gifts** with purchase to boost AOV on other products
- **Hold for next year** only if shelf life allows and storage cost is minimal
- **Donate for tax write-off** if liquidation is not cost-effective

### Post-Season Review

Document these metrics for next year:
- Total units ordered vs. total units sold (sell-through rate)
- Revenue vs. forecast accuracy
- Top 3 sellers and bottom 3 sellers
- Clearance revenue as percentage of total season revenue
- Lessons learned for next season ordering

---

## Anti-Patterns

- **Ordering based on hope** — "I think this will be huge" without data leads to overstock. Use numbers.
- **Ignoring lead times** — placing orders late means stockouts during peak demand.
- **No clearance plan** — holding seasonal inventory past its window ties up cash and storage.
- **Over-diversifying SKUs** — too many products spread inventory budget thin. Focus on proven winners.
- **Skipping the post-season review** — if you do not document what happened, you will repeat the same mistakes.

---

## Recovery

- **No historical data:** Use competitor research, Google Trends, and small test orders to build a baseline. Plan conservatively.
- **Supplier cannot meet timeline:** Find backup suppliers, reduce order quantities, or shift to faster-shipping alternatives.
- **Budget too small for forecast:** Prioritize top sellers, cut unproven products, and plan a smaller launch with reorder triggers.
- **Mid-season stockout:** Source locally if possible, offer pre-orders for restocks, and redirect marketing to in-stock items.
- **Excess inventory post-season:** Implement clearance plan immediately — do not wait hoping it will sell at full price next season.
