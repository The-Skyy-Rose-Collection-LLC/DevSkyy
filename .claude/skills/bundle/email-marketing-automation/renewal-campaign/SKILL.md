---
name: renewal-campaign
description: "Builds subscription renewal campaigns with reminder sequences, incentives, and save offers. Use when reducing churn and increasing subscription retention rates."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Renewal Campaign

## When to Use This Skill

Use this skill when you need to:
- Build an email sequence that encourages subscription renewals
- Create save offers for subscribers considering cancellation
- Design a renewal reminder timeline with escalating incentives
- Reduce churn by proactively engaging subscribers before their renewal date

**DO NOT** use this skill for initial onboarding, win-back campaigns for already-churned customers, or free trial conversion emails. This is for retaining active subscribers approaching renewal.

---

## Core Principle

RENEWAL IS NOT A TRANSACTION — IT IS A MOMENT TO REMIND CUSTOMERS OF THE VALUE THEY HAVE RECEIVED AND THE VALUE THEY WOULD LOSE BY LEAVING.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Product** | "What subscription product is renewing?" | No default — must be provided |
| **Subscription price** | "What's the renewal price?" | No default — must be provided |
| **Billing cycle** | "Monthly or annual?" | Annual |
| **Current churn rate** | "What percentage of subscribers don't renew?" | Unknown |
| **Renewal type** | "Auto-renew or manual renewal required?" | Auto-renew |
| **Save offer budget** | "Can you offer a discount to prevent cancellation?" | Up to 20% off |

**GATE: Confirm the brief before building the campaign.**

---

## Phase 2: Campaign Architecture

### Renewal Timeline

```
## Renewal Email Sequence

**60 days before renewal:**
Email 1: Value recap — "Here's what you've accomplished this year"

**30 days before renewal:**
Email 2: What's coming — preview new features or content

**14 days before renewal:**
Email 3: Renewal reminder + any loyalty incentive

**7 days before renewal:**
Email 4: Direct renewal reminder + FAQ

**1 day before renewal:**
Email 5: Final reminder — "Your subscription renews tomorrow"

**Post-renewal (auto-renew):**
Email 6: Thank you + what's new for the next period

**Post-cancellation (if they cancel):**
Email 7: Save offer — "Before you go, we'd like to offer..."
Email 8 (7 days later): Final save attempt with different angle
```

### Cancellation Save Flow

```
## Cancellation Interception

Step 1: Cancellation reason survey (required before processing)
Step 2: Tailored save offer based on reason:
  - "Too expensive" → Discounted rate or downgrade option
  - "Not using it enough" → Usage tips + pause option
  - "Missing features" → Roadmap preview + feedback collection
  - "Found alternative" → Competitive comparison + loyalty discount
Step 3: If declined → process cancellation gracefully
Step 4: Post-cancellation email with open door to return
```

**GATE: Approve the campaign architecture before writing.**

---

## Phase 3: Write Campaign Content

### Value Recap Email (60 days out)

Personalize with actual usage data:
```
Subject: Your year with [Product] — by the numbers

{first_name}, you've been a member for [X] months. Here's what you've achieved:

- [Usage stat 1: e.g., "Created 47 projects"]
- [Usage stat 2: e.g., "Saved an estimated 120 hours"]
- [Usage stat 3: e.g., "Downloaded 23 templates"]

And we're just getting started. Here's what's coming in the next [period]...
```

### Renewal Reminder Emails

Keep these short and clear:
- State the renewal date and amount
- Link to account/billing page
- For manual renewals: direct renewal button
- For auto-renewals: reassurance + how to update payment method

### Save Offer Scripts

Tailored by cancellation reason:
```
"Too expensive" response:
"We'd hate to see you go over price. How about [X]% off your next
[period]? That brings your cost to $[discounted price]/[period]."

"Not using it" response:
"Totally fair. Instead of cancelling, would you like to pause your
subscription for [30/60/90] days? Your account and data stay intact."
```

---

## Phase 4: Polish

### 1. Churn Prediction Indicators

Flag at-risk subscribers before renewal based on:
- Login frequency declining over 60 days
- Support tickets or complaints
- Feature usage dropping
- Payment failures in the past

### 2. Metrics to Track

- Renewal rate (target: 80%+ for annual, 90%+ for monthly)
- Save offer acceptance rate
- Cancellation reason distribution
- Revenue saved from save offers
- Time to churn after save offer (do saved customers stay long-term?)

### 3. Ongoing Optimization

- A/B test save offer amounts (10% vs. 20% vs. free month)
- Test renewal email timing and frequency
- Survey renewed customers: "What almost made you cancel?"

---

## Anti-Patterns

- **Surprising customers with charges** — always remind before auto-renewal. Surprise charges create chargebacks and negative reviews.
- **Begging in cancellation flow** — "Please don't go!" is undignified. Present value and options, then respect the decision.
- **No cancellation reason capture** — every cancellation without a reason is a missed learning opportunity.
- **Save offers that are too generous** — 50% off to save one subscriber trains them to threaten cancellation for discounts.
- **Ignoring low-usage subscribers** — if they are not using the product, they will not renew. Engage them months before renewal, not days.

---

## Recovery

- **No usage data available:** Focus on feature highlights and customer testimonials instead of personalized recaps.
- **Very high churn (over 30%):** The problem may not be the renewal campaign — it may be the product or onboarding. Investigate root causes.
- **User has no save offer budget:** Use non-monetary saves: pause option, downgrade tier, extended free month, or personalized support call.
- **Monthly subscription with constant churn:** Consider switching to annual billing with a discount incentive. Annual subscribers churn at significantly lower rates.
