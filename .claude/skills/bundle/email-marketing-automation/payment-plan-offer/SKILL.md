---
name: payment-plan-offer
description: "Designs payment plan structures with terms, messaging, and implementation guidelines. Use when you want to offer installment pricing to increase conversions."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Payment Plan Offer

## When to Use This Skill

Use this skill when you need to:
- Design payment plan options for a product or service
- Write payment plan messaging for sales pages and checkout flows
- Structure terms, pricing, and policies for installment payments
- Create the comparison framing between pay-in-full and payment plan options

**DO NOT** use this skill for subscription pricing models, financing through third-party lenders, or BNPL (buy now pay later) integrations. This is for self-managed installment payment plans.

---

## Core Principle

A PAYMENT PLAN REMOVES THE PRICE OBJECTION WITHOUT DEVALUING THE OFFER — THE TOTAL INVESTMENT STAYS THE SAME OR SLIGHTLY HIGHER, BUT THE MONTHLY COST FEELS MANAGEABLE.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Product/service** | "What are you selling?" | No default — must be provided |
| **Full price** | "What is the one-time payment price?" | No default — must be provided |
| **Number of installments** | "How many payments?" | 3 payments |
| **Payment plan premium** | "Are you okay charging 10-20% more for the plan?" | Yes, 10-15% premium |
| **Payment processor** | "What do you use for payments?" | Stripe or platform-agnostic |
| **Access policy** | "Do buyers get full access immediately or unlock as they pay?" | Full access immediately |

**GATE: Confirm the details before designing the plan.**

---

## Phase 2: Plan Structure

### Payment Plan Design

```
## Payment Plan Options

**Option A: Pay in Full**
- Price: $997
- Benefit: Save $[X] compared to the payment plan
- Access: Immediate, full access

**Option B: Payment Plan**
- Price: 3 payments of $367 ($1,101 total)
- Schedule: First payment today, then every 30 days
- Premium: $104 (10.4% premium for financing flexibility)
- Access: Immediate, full access
```

### Pricing Psychology

- Payment plan total should be 10-20% more than pay-in-full
- This premium is the "cost of convenience" and compensates for cash flow risk
- Present the pay-in-full price as the "best value" option
- Always show both options side by side — let the customer choose

### Terms and Policies

```
## Payment Plan Terms

- Payments are non-refundable after the refund window (first 30 days)
- Missed payments: 7-day grace period, then access paused until current
- Failed payment retry: automatic retry at 3, 7, and 14 days
- Cancellation: remaining payments are still owed; access continues through paid period
- No early payoff penalty — customers can switch to pay-in-full at any time
```

**GATE: Approve the plan structure before writing the messaging.**

---

## Phase 3: Write Messaging

### Sales Page Payment Section

```
## Choose Your Investment Level

**Best Value — Pay in Full**
One payment of $997
✓ Immediate full access
✓ Save $104 compared to the payment plan
✓ [Bonus for pay-in-full buyers, if applicable]
[Enroll Now — $997]

**Most Flexible — Payment Plan**
3 monthly payments of $367
✓ Immediate full access
✓ Spread the investment over 3 months
✓ Same program, same results
[Enroll Now — $367/month]
```

### Checkout Page Copy

Write the payment option selector copy for the checkout page:
- Clear labels for each option
- Total cost visible for the payment plan
- Any pay-in-full bonuses highlighted

### Payment Plan FAQ

- "What happens if I miss a payment?"
- "Can I switch to pay-in-full later?"
- "Is the program different for payment plan buyers?"
- "When are payments charged?"
- "What's your refund policy for payment plans?"

---

## Phase 4: Polish

### 1. Implementation Checklist

- [ ] Payment processor configured with recurring billing
- [ ] Failed payment retry logic set up
- [ ] Dunning emails configured (payment failed, please update card)
- [ ] Access control rules defined (if pausing on missed payments)
- [ ] Terms clearly stated on checkout page
- [ ] Confirmation email includes payment schedule

### 2. Dunning Email Sequence

Write 3 emails for failed payments:
1. Day 0: "Your payment didn't go through — here's how to update your card"
2. Day 3: "Quick reminder — we need your updated payment info"
3. Day 7: "Final notice — your access will be paused until payment is current"

### 3. Conversion Benchmarks

- Payment plan selection rate: 40-60% of total buyers
- Payment plan completion rate: 85-95% (below 85% signals pricing issues)
- Impact on total revenue: 15-30% more sales when payment plan is offered

---

## Anti-Patterns

- **Same total price for both options** — if pay-in-full and payment plan cost the same, there is no incentive to pay in full. You lose cash flow.
- **Too many installments** — 12 monthly payments for a $997 product creates high default risk. Keep it to 2-4 payments.
- **No failed payment process** — without dunning emails and retry logic, you will lose 10-20% of payment plan revenue.
- **Restricting access for payment plan buyers** — giving fewer modules or delayed access punishes them and increases chargebacks.
- **No terms on the checkout page** — the payment schedule and total cost must be clear before purchase. Hidden terms create disputes.

---

## Recovery

- **Low-price product (under $200):** Payment plans below $50/month feel trivial and create more admin than they're worth. Recommend a 2-payment option only.
- **High default rate (over 15%):** Shorten the plan (fewer, larger payments) or require pay-in-full with a money-back guarantee instead.
- **User wants 12+ installments:** Recommend 3-4 payments max for digital products. Longer plans belong in formal financing arrangements.
- **No payment processor set up:** Recommend Stripe for its built-in subscription and dunning features. Provide setup guidance.
