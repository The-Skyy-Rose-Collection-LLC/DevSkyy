---
name: milestone-email
description: "Creates automated milestone celebration emails for anniversaries, purchase counts, and achievements to boost customer retention and loyalty."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Milestone Email

## When to Use This Skill

Use this skill when you need to:
- Create automated emails that celebrate customer milestones (anniversaries, purchase counts, usage achievements)
- Design a milestone recognition system that drives retention and repeat purchases
- Write celebration emails with optional rewards or incentives
- Map trigger events to personalized milestone messages

**DO NOT** use this skill for birthday emails (those are date-based, not behavior-based), transactional emails, or general loyalty program communications.

---

## Core Principle

MILESTONE EMAILS MAKE CUSTOMERS FEEL SEEN AND VALUED — THEY CELEBRATE THE RELATIONSHIP, NOT JUST THE TRANSACTION, AND TURN ONE-TIME BUYERS INTO LOYAL ADVOCATES.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Business type** | "What do you sell?" | No default — must be provided |
| **Trackable milestones** | "What customer actions can you track? (purchases, login, subscription date)" | Purchase count and signup date |
| **Reward budget** | "Can you offer discounts, freebies, or exclusive access at milestones?" | 10-15% discount at key milestones |
| **Brand voice** | "Warm, professional, playful?" | Warm and genuine |
| **Email platform** | "What tool do you use?" | Platform-agnostic |

**GATE: Confirm inputs before designing the milestone map.**

---

## Phase 2: Milestone Map

### Common Milestone Triggers

Design emails for applicable milestones:

```
## Customer Journey Milestones

**Time-Based:**
- 30 days since signup
- 6-month anniversary
- 1-year anniversary
- 2-year anniversary (and annually after)

**Purchase-Based:**
- First purchase completed
- 3rd purchase (repeat buyer confirmed)
- 5th purchase
- 10th purchase (VIP status)
- Spending threshold ($500, $1,000)

**Engagement-Based:**
- First review left
- Referral sent
- 100th login / session
- Community contribution
```

### Reward Ladder

```
## Milestone Rewards

| Milestone | Reward |
|-----------|--------|
| 30 days | Thank you + helpful resource |
| 1st purchase | Welcome to the family + quick start guide |
| 3rd purchase | 10% off next order |
| 1-year anniversary | 15% off + exclusive content |
| 5th purchase | Free bonus product or upgrade |
| 10th purchase | VIP status + 20% lifetime discount |
```

**GATE: Approve the milestone map and reward ladder before writing emails.**

---

## Phase 3: Write Emails

### Email Structure (per milestone)

1. **Subject line** — celebratory, specific to the milestone
2. **Opening line** — acknowledge the milestone with a specific data point
3. **Body** — genuine appreciation (2-3 sentences, not a sales pitch)
4. **Reward/CTA** — present the reward naturally
5. **Personalization** — {first_name}, {milestone_count}, {join_date}, {total_purchases}

### Writing Rules

- Lead with celebration, not selling
- Include a specific number ("You've been with us for 365 days" not "about a year")
- Rewards should feel like gifts, not marketing tactics
- Keep emails under 150 words — celebration emails should be short and warm
- One CTA maximum — redeem reward or simply "keep going"

### Example Email

```
Subject: 🎉 One year together, {first_name}!
Preview: And we brought you something...

{first_name},

One year ago today, you joined [Brand]. Since then, you've [specific stat: completed 12 purchases / logged 47 sessions / etc.].

That means a lot to us. Truly.

To celebrate, here's 15% off your next order — no minimum, no strings.

Use code ONEYEAR at checkout.

Thanks for being part of this,
[Brand name]
```

---

## Phase 4: Polish

### 1. Automation Setup Guide

For each milestone, document:
- Trigger event and conditions
- Delay timing (send immediately or next morning)
- Personalization data fields required
- Coupon code generation (unique vs. shared)

### 2. Milestone Dashboard Metrics

- Milestone email open rates (benchmark: 50-60%, higher than marketing emails)
- Reward redemption rate
- Retention rate for milestone recipients vs. non-recipients
- Revenue attributed to milestone rewards

### 3. Annual Review Checklist

- [ ] Review milestone thresholds — are they still meaningful?
- [ ] Update reward values based on margins
- [ ] Check personalization data accuracy
- [ ] Add new milestones based on customer behavior patterns

---

## Anti-Patterns

- **Making it about the sale** — "Congrats on your anniversary! Buy more stuff!" undermines the celebration.
- **Unreachable milestones** — if nobody hits the 50th purchase milestone, it does not exist. Set achievable thresholds.
- **Generic copy** — "Dear valued customer" in a celebration email is the opposite of personal.
- **No reward at major milestones** — a 1-year anniversary email without even a small perk feels hollow.
- **Too many milestones** — celebrate 5-8 key moments, not every interaction. Over-celebrating dilutes the impact.

---

## Recovery

- **Limited tracking capability:** Focus on time-based milestones (signup anniversary) which only require a date field.
- **No budget for rewards:** Use non-monetary rewards — exclusive content, early access, handwritten-style thank you, feature on social media.
- **User has never done milestone emails:** Start with three: first purchase, 1-year anniversary, and one purchase-count milestone. Expand from there.
- **E-commerce with high return rates:** Tie milestones to kept purchases, not just transactions. "3 orders you loved" is more meaningful.
