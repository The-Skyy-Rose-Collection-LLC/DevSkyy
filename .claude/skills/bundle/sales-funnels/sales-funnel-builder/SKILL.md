---
name: sales-funnel-builder
description: "Maps complete sales funnels with stages, conversion points, content, and optimization opportunities. Use when you need to design or audit your customer acquisition path."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Sales Funnel Builder

## When to Use This Skill

Use this skill when you need to:
- Map a complete sales funnel from traffic source to purchase and beyond
- Identify conversion points, drop-off risks, and optimization opportunities
- Define the content and messaging needed at each funnel stage
- Design upsell, downsell, and retention paths after the initial purchase

**DO NOT** use this skill for individual landing pages, email sequences alone, or ad campaign planning. This is for mapping the entire funnel architecture.

---

## Core Principle

A FUNNEL IS ONLY AS STRONG AS ITS WEAKEST STAGE — MAP EVERY STEP, MEASURE EVERY TRANSITION, AND FIX THE BIGGEST DROP-OFF FIRST.

---

## Phase 1: Funnel Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Core offer** | "What is the main product or service you're selling?" | No default — must be provided |
| **Price point** | "What does it cost?" | No default — must be provided |
| **Traffic sources** | "Where does your traffic come from? (organic, ads, social, referrals)" | Mixed organic and paid |
| **Current funnel** | "Do you have an existing funnel? What does it look like?" | No existing funnel |
| **Lead magnet** | "Do you have a free offer to capture emails?" | None — will recommend one |
| **Upsells/downsells** | "Do you have additional offers at different price points?" | None yet |

**GATE: Confirm the funnel brief before designing the architecture.**

---

## Phase 2: Funnel Architecture

### Funnel Stages

Map each stage with its purpose, content, and conversion goal:

```
## Funnel Map

**Stage 1: Awareness (Top of Funnel)**
- Traffic source → Content/Ad
- Goal: Capture attention and drive clicks
- Content: Blog posts, social content, ads
- Metric: Click-through rate

**Stage 2: Capture (Lead Generation)**
- Content/Ad → Lead Magnet Landing Page
- Goal: Convert visitors to leads
- Content: Landing page + lead magnet
- Metric: Opt-in rate (target: 25-40%)

**Stage 3: Nurture (Trust Building)**
- Lead Magnet → Email Sequence
- Goal: Build trust and demonstrate expertise
- Content: 5-7 nurture emails
- Metric: Email engagement rate

**Stage 4: Convert (Sale)**
- Email Sequence → Sales Page
- Goal: Purchase the core offer
- Content: Sales page, checkout page
- Metric: Sales conversion rate (target: 1-5%)

**Stage 5: Maximize (Post-Purchase)**
- Purchase → Order Bump + Upsell
- Goal: Increase average order value
- Content: Order bump, upsell page, downsell page
- Metric: AOV increase (target: 30-50% lift)

**Stage 6: Retain (Loyalty)**
- Purchase → Onboarding + Retention Emails
- Goal: Deliver value and create repeat buyers
- Content: Onboarding sequence, milestone emails
- Metric: Repeat purchase rate, refund rate
```

### Conversion Flow Diagram

```
[Traffic] → [Landing Page] → [Thank You / Lead Magnet Delivery]
                                        ↓
                               [Nurture Email 1-5]
                                        ↓
                                [Sales Page]
                                   ↓         ↓
                            [Checkout]    [Exit → Downsell]
                                ↓
                        [Order Bump Offer]
                                ↓
                          [Upsell Page]
                            ↓         ↓
                       [Accept]    [Downsell Page]
                                        ↓
                              [Thank You + Onboarding]
```

**GATE: Present the funnel architecture for approval before detailing each stage.**

---

## Phase 3: Stage Details

For each stage, provide:

1. **Page/asset needed** — what to build
2. **Copy direction** — headline approach, key messaging
3. **Tech requirements** — tools, integrations, tracking
4. **Benchmark metrics** — what good looks like at this stage
5. **Optimization levers** — what to test first if this stage underperforms

### Funnel Math

```
## Projected Funnel Performance

1,000 visitors/month
× 30% opt-in rate = 300 leads
× 5% sales conversion = 15 sales
× $297 price = $4,455 revenue
× 40% take order bump ($47) = 6 bumps = $282
× 20% take upsell ($197) = 3 upsells = $591

Monthly revenue: $5,328
Revenue per lead: $17.76
Cost per lead breakeven: $17.76
```

---

## Phase 4: Polish

### 1. Implementation Priority List

Rank funnel assets by build priority (what to create first, second, third).

### 2. Tech Stack Recommendations

Suggest tools for each funnel component based on the user's budget and technical ability.

### 3. Optimization Roadmap

After launch, prioritize optimization in this order:
1. Fix the lowest-converting stage first
2. Test headlines on landing pages (biggest impact)
3. Optimize email sequence engagement
4. Test upsell/downsell offers and pricing

---

## Anti-Patterns

- **Building the funnel bottom-up** — start with the core offer and sales page, then work backward to traffic. Do not build a lead magnet for a product that does not exist yet.
- **Too many steps before the sale** — every additional step loses people. Keep the path as short as possible.
- **No post-purchase path** — the funnel does not end at checkout. Onboarding and retention are where lifetime value is built.
- **Ignoring funnel math** — if the numbers do not work on paper, they will not work in practice. Run the projections first.
- **Optimizing traffic before fixing conversion** — sending more traffic to a broken funnel wastes money.

---

## Recovery

- **No existing offer:** Start with the offer first. Define what you sell before building the funnel around it.
- **No lead magnet idea:** Suggest 3 lead magnet concepts based on the core offer topic (checklist, template, mini-course).
- **User overwhelmed by complexity:** Recommend a minimum viable funnel: landing page → email sequence → sales page. Add upsells later.
- **No traffic yet:** Build the funnel first, then plan traffic acquisition. Organic content is the lowest-cost starting point.
- **Multiple products, no clear funnel:** Identify the lowest-priced entry product and build the funnel around that. Other products become upsells.
