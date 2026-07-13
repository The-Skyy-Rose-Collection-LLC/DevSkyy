---
name: trial-to-paid-email
description: "Writes trial-to-paid conversion email sequences with feature education, social proof, and urgency progression. Use when optimizing free trial conversion rates."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Trial-to-Paid Email Sequence

## When to Use This Skill

Use this skill when you need to:
- Write an email sequence that converts free trial users to paying customers
- Design a trial nurture flow with feature education and social proof
- Optimize trial-to-paid conversion by guiding users to the activation moment
- Create urgency progression as the trial expiration approaches

**DO NOT** use this skill for post-purchase onboarding, win-back campaigns, or general email marketing. This is for trial conversion sequences only.

---

## Core Principle

THE TRIAL EMAIL SEQUENCE HAS ONE JOB — GET THE USER TO EXPERIENCE THE PRODUCT'S CORE VALUE BEFORE THE TRIAL EXPIRES. EVERY EMAIL REMOVES A BARRIER OR ACCELERATES THAT MOMENT.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Product name** | "What is the product?" | No default — must be provided |
| **Trial length** | "How long is the free trial?" | 14 days |
| **Core value moment** | "What action means a user has experienced real value?" | No default — must be provided |
| **Current conversion rate** | "What percentage of trials convert to paid?" | Unknown |
| **Pricing** | "What are the plan options and prices?" | No default — must be provided |
| **Top objections** | "Why do trial users NOT convert? Top 3 reasons." | Price, did not use it enough, unclear value |

**GATE: Confirm the brief before writing the sequence.**

---

## Phase 2: Map the Sequence

### 14-Day Trial Email Sequence Map

| Email | Day | Goal | Tone |
|-------|-----|------|------|
| 1: Welcome | 0 | Set expectations, drive first action | Warm, clear |
| 2: Quick Win | 1 | Guide to first value moment | Helpful, urgent |
| 3: Feature Spotlight | 3 | Educate on a key feature | Educational |
| 4: Social Proof | 5 | Show what others achieved | Inspirational |
| 5: Advanced Feature | 7 | Deepen engagement (mid-trial) | Expert |
| 6: Check-In | 9 | Ask if they need help, handle objections | Personal |
| 7: Urgency | 11 | Trial ending soon, recap value | Direct |
| 8: Last Chance | 13 | Final push, limited-time offer (optional) | Urgent |
| 9: Trial Expired | 14 | Grace period or downgrade notice | Matter-of-fact |

Adjust timing for 7-day or 30-day trials proportionally.

**GATE: Confirm the sequence map before writing individual emails.**

---

## Phase 3: Write

### Email Templates

**Email 1: Welcome (Day 0)**
- Subject: What to do first in [Product]
- Body: Welcome, set expectations for the trial period, one CTA to complete the first action
- Length: 100-150 words

**Email 2: Quick Win (Day 1)**
- Subject: Try this in 2 minutes
- Body: Step-by-step to achieve the first value moment, screenshot or GIF
- Length: 100-125 words

**Email 3: Feature Spotlight (Day 3)**
- Subject: [Feature] saves [audience] [time/money]
- Body: One feature explained with a use case and benefit
- Length: 125-150 words

**Email 4: Social Proof (Day 5)**
- Subject: How [Customer] uses [Product] to [result]
- Body: Brief case study or testimonial with specific results
- Length: 125-150 words

**Email 5: Advanced Feature (Day 7)**
- Subject: Most people miss this feature
- Body: Deeper feature that increases stickiness
- Length: 125-150 words

**Email 6: Check-In (Day 9)**
- Subject: Quick question about your trial
- Body: Personal check-in, ask what is blocking them, offer help
- Length: 75-100 words

**Email 7: Urgency (Day 11)**
- Subject: Your trial ends in 3 days
- Body: Recap value received, preview what happens after trial, CTA to upgrade
- Length: 125-150 words

**Email 8: Last Chance (Day 13)**
- Subject: Last day to keep your [Product] account
- Body: Final push, optional discount or extended trial offer
- Length: 100-125 words

**Email 9: Trial Expired (Day 14)**
- Subject: Your trial has ended — here is what happens next
- Body: What they lose access to, how to reactivate, grace period if offered
- Length: 100 words

### Copy Rules

- Every email has exactly ONE CTA (not multiple links competing)
- Subject lines are under 50 characters
- Body copy is under 150 words per email
- Use the user's name and product activity data if available (behavioral triggers)
- No attachments — everything links to in-app

---

## Phase 4: Polish

### 1. Behavioral Triggers

Enhance the sequence with activity-based branching:
- **Activated users:** Skip emails 2-3, send advanced content earlier
- **Inactive users (Day 3, no login):** Insert a re-engagement email with a how-to video
- **Power users:** Send an upgrade email earlier with a usage-based pitch

### 2. A/B Test Plan

- Test subject lines on Email 1 and Email 7 (highest-impact emails)
- Test CTA placement (top vs. bottom of email)
- Test with and without a discount in Email 8

### 3. Quality Checklist

```
## Trial Email Sequence Checklist

- [ ] 7-9 emails mapped across the trial period
- [ ] Email 1 sends immediately upon signup
- [ ] Every email has exactly one CTA
- [ ] Subject lines are under 50 characters
- [ ] Body copy is under 150 words per email
- [ ] Social proof email includes specific results (not vague praise)
- [ ] Urgency escalates naturally (not panic-inducing from Day 1)
- [ ] Check-in email sounds personal, not automated
- [ ] Expired email explains what happens next clearly
- [ ] Behavioral triggers are defined for active vs. inactive users
```

---

## Example

**Product:** InvoiceBot, 14-day trial, $29/month

**Email 2 (Quick Win):**
```
Subject: Create your first invoice in 60 seconds

Hey [Name],

Here is the fastest way to see InvoiceBot in action:

1. Click "New Invoice"
2. Type: "Invoice [client name] $500 for consulting, net 30"
3. Hit send

That is it. InvoiceBot fills in your business details, calculates tax, and delivers a PDF.

Try it now — your first invoice takes under 60 seconds.

[Create My First Invoice]
```

**Email 7 (Urgency):**
```
Subject: 3 days left on your trial

Hey [Name],

Your InvoiceBot trial ends on [date]. Here is what you have done so far:
- Created [X] invoices
- Saved approximately [Y] minutes

After your trial, you will lose access to automatic reminders, tax calculations, and your invoice templates.

Keep everything for $29/month — less than the cost of one late payment.

[Upgrade Now]
```

---

## Anti-Patterns

- **Starting with urgency** — Day 1 should be helpful, not pressuring. Save urgency for the final 3 days.
- **Too many CTAs** — each email gets one link. Multiple choices reduce clicks.
- **Ignoring inactive users** — users who never log in need a different message than active users. Branch the flow.
- **Generic social proof** — "Thousands of happy users" convinces nobody. Use one specific story with results.
- **No expired email** — silence after trial ends feels like abandonment. Always send a clear "what happens next" email.

---

## Recovery

- **Very short trial (7 days):** Compress to 5 emails. Cut Feature Spotlight and Advanced Feature. Focus on quick win, social proof, and urgency.
- **Very long trial (30 days):** Add more educational content in weeks 2-3. Keep urgency to final week only.
- **No conversion data:** Start the sequence and measure open rates, click rates, and conversion at each email. Optimize after 30 days of data.
- **Low open rates:** Test subject lines first. Then test send times. Then test sender name (personal name vs. company name).
