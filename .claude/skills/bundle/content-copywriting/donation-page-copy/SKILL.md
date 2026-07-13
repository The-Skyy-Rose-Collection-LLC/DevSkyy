---
name: donation-page-copy
description: "Writes donation page copy with urgency, impact framing, recurring giving encouragement, and trust signals."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Donation Page Copy

## When to Use This Skill

Use this skill when you need to:
- Write copy for an online donation page that converts visitors into donors
- Create impact-framed giving levels with urgency and trust elements
- Optimize an existing donation page for higher conversion and recurring giving
- Build donation page copy for campaigns, year-end drives, or evergreen giving

**DO NOT** use this skill for fundraising letters, grant applications, or crowdfunding campaigns. This is specifically for the donation page where the transaction happens.

---

## Core Principle

A DONATION PAGE HAS ONE JOB: REMOVE EVERY BARRIER BETWEEN THE VISITOR'S DESIRE TO HELP AND THE COMPLETED TRANSACTION — EVERY WORD MUST EITHER BUILD CONFIDENCE OR REDUCE FRICTION.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Organization** | "What is the organization and mission?" | No default — must be provided |
| **Page type** | "Evergreen donation page or campaign-specific?" | Evergreen |
| **Giving levels** | "What donation amounts do you want to suggest?" | $25, $50, $100, $250 |
| **Impact statements** | "What does each dollar amount accomplish?" | No default — must be provided |
| **Recurring giving** | "Do you want to encourage monthly giving?" | Yes |
| **Trust signals** | "Any ratings, certifications, or transparency badges? (GuideStar, Charity Navigator)" | None available |

**GATE: Confirm the brief before writing.**

---

## Phase 2: Page Structure

### Donation Page Architecture

```
1. Headline — emotional, benefit-driven, 8 words or fewer
2. Sub-headline — one sentence expanding on the headline
3. Impact statement — what donations accomplish (2-3 sentences)
4. Giving levels — pre-set amounts with impact descriptions
5. Recurring toggle — monthly giving option with framing
6. Custom amount — option for donors who want a different amount
7. Trust signals — ratings, transparency data, security badges
8. Donor info form — name, email, payment (keep minimal)
9. Dedication/tribute option — give in someone's honor
10. Social proof — donor count, recent gifts, testimonials
```

### Giving Level Design

```
| Amount | Impact Statement | Recommended Default |
|--------|-----------------|-------------------|
| $25 | [Tangible outcome] | |
| $50 | [Tangible outcome] | Yes (pre-selected) |
| $100 | [Tangible outcome] | |
| $250 | [Tangible outcome] | |
| Other | "Enter your amount" | |
```

Pre-select the middle option. It anchors expectations without intimidating.

**GATE: Present the page structure for approval.**

---

## Phase 3: Write

### Copy Elements

**Headline Options (pick one):**
- "Give [Outcome] to [Beneficiary]"
- "Your Gift Changes Everything for [Beneficiary]"
- "[Number] [People] Are Counting on You"

**Sub-headline:**
One sentence that connects the donor's action to the outcome. "When you give today, you [specific impact]."

**Impact Section:**
```
Every dollar you give goes directly to [mission]. Here is what your gift makes possible:

$25 — [Specific, tangible outcome]
$50 — [Specific, tangible outcome]
$100 — [Specific, tangible outcome]
$250 — [Specific, tangible outcome]
```

**Recurring Giving Frame:**
```
## Become a Monthly Giver
Monthly gifts provide stable funding that lets us plan ahead and serve more [beneficiaries].

$25/month = $300/year = [annual impact]
$50/month = $600/year = [annual impact]

Monthly donors receive: [quarterly impact updates, exclusive content, recognition]
```

**Trust Signals Section:**
```
## Your Gift Is Safe and Effective
- [X]% of funds go directly to programs
- [Rating/certification if available]
- Secure payment processing via [Stripe/PayPal]
- Tax-deductible — you will receive a receipt immediately
```

**Social Proof:**
```
Join [X] donors who have already given this [month/year].
"[Short testimonial from a donor about why they give]" — [Name, City]
```

---

## Phase 4: Polish

### 1. Conversion Optimization

```
## Page Optimization Checklist
- [ ] Page loads in under 3 seconds
- [ ] Form has 5 or fewer fields (name, email, amount, payment)
- [ ] Pre-selected amount is the middle tier
- [ ] Monthly giving is presented as the default or prominently featured
- [ ] Mobile experience is seamless (50%+ of donations are mobile)
- [ ] Confirmation page thanks and shows impact
- [ ] Auto-receipt email triggers immediately
```

### 2. Thank-You Page

After donation, display:
- Heartfelt thank-you message
- Specific impact of their gift amount
- Social sharing buttons ("Tell your friends")
- Option to make it recurring (if one-time)
- Link to the impact report

### 3. A/B Test Ideas

- Headline: emotional vs. data-driven
- Default amount: $25 vs. $50 vs. $100
- Monthly vs. one-time as default selection
- With donor testimonial vs. without
- Photo of beneficiary vs. no photo

---

## Example 1: Education Nonprofit Donation Page

```
Headline: "Give a Child the Gift of Reading"
$25 — Provides 5 books for a classroom library
$50 — Funds one month of after-school tutoring
$100 — Sponsors a student for one semester
$250 — Fully funds one child's reading program for a year
Monthly frame: "$25/month means one child always has a tutor waiting"
```

## Example 2: Animal Rescue Donation Page

```
Headline: "Save a Life Today"
$25 — Feeds a rescued animal for one month
$50 — Covers vaccinations for one animal
$100 — Funds emergency veterinary care
$250 — Sponsors a full rescue and rehabilitation
Trust signal: "98 cents of every dollar goes to animal care"
```

---

## Anti-Patterns

- **Too many form fields** — every extra field reduces conversions. Name, email, payment. That is it.
- **No impact framing** — "$50" means nothing. "$50 feeds a family for a week" means everything.
- **Burying recurring giving** — monthly donors are 5x more valuable over time. Feature this prominently.
- **No trust signals** — donors need to know their money is safe and well-used. Show security and transparency.
- **Slow page load** — every second of load time drops conversion by 7%. Optimize relentlessly.
- **Generic thank-you** — "Thank you for your donation" wastes the highest-engagement moment. Show specific impact and encourage sharing.

---

## Recovery

- **No impact data available:** Estimate based on budget. If you spend $100,000 on programs serving 500 people, each person costs $200 to serve. Frame donor levels accordingly.
- **No trust signals or ratings:** State the program expense ratio. "X cents of every dollar goes to programs" is a powerful trust signal you can calculate yourself.
- **Low recurring giving rate:** Test defaulting to monthly, framing the annual impact, and offering a small incentive (quarterly updates, donor badge).
- **Page exists but converts poorly:** Audit against the checklist. The most common issues are too many form fields, no pre-selected amount, and missing impact framing.
