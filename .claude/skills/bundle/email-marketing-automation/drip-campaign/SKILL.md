---
name: drip-campaign
description: "Builds nurture drip campaigns with conditional logic, lead scoring triggers, and content mapping per stage. Use when you need automated email sequences that move leads through your funnel based on behavior."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Drip Campaign

## When to Use This Skill

Use this skill when you need to:
- Build an automated email nurture sequence that moves leads toward a purchase
- Design conditional logic paths based on subscriber behavior (opens, clicks, purchases)
- Map content to each stage of the buyer journey within an email sequence
- Set up lead scoring triggers that advance or redirect subscribers

**DO NOT** use this skill for one-off broadcast emails, transactional emails (order confirmations, receipts), or SMS sequences. This is for multi-step automated email campaigns with branching logic.

---

## Core Principle

EVERY DRIP CAMPAIGN MUST MOVE THE SUBSCRIBER CLOSER TO A SPECIFIC ACTION — EACH EMAIL EARNS PERMISSION TO SEND THE NEXT ONE BY DELIVERING VALUE FIRST.

---

## Phase 1: Campaign Brief

Before building any sequence, gather the inputs that define the campaign's structure and goals.

### Required Inputs

Ask the user for each of these. If they do not provide one, use the default.

| Input | What to Ask | Default |
|-------|------------|---------|
| **Campaign goal** | "What action should subscribers take by the end?" | No default — must be provided |
| **Entry trigger** | "How do people enter this sequence? (opt-in, purchase, tag, etc.)" | Email opt-in via lead magnet |
| **Audience stage** | "Are these cold leads, warm leads, or existing customers?" | Warm leads (opted in but haven't purchased) |
| **Number of emails** | "How many emails in the sequence?" | 5-7 emails |
| **Sending cadence** | "How often should emails send?" | Every 2-3 days |
| **Email platform** | "What email tool are you using?" | Platform-agnostic |

### Brief Template

Present this before moving to Phase 2:

```
## Drip Campaign Brief

**Campaign goal:** Purchase the $297 course
**Entry trigger:** Downloaded free PDF guide
**Audience stage:** Warm leads — interested but not committed
**Sequence length:** 7 emails over 18 days
**Cadence:** Days 0, 2, 5, 8, 11, 14, 18
**Platform:** ConvertKit
**Lead scoring:** +5 per open, +10 per click, +25 for pricing page visit
```

**GATE: Do not proceed to Phase 2 until the user confirms or adjusts the brief.**

---

## Phase 2: Sequence Map

Build the complete campaign architecture before writing any email copy.

### Sequence Map Rules

1. **Each email has a single job** — educate, build trust, create desire, or ask for the sale
2. **Conditional branches** must trigger on measurable actions (opened, clicked, visited page, scored above threshold)
3. **Lead scoring thresholds** determine when a subscriber moves to a sales-focused path
4. **Exit conditions** remove subscribers who convert or disengage

### Sequence Map Format

```
## Email Sequence Map

**Email 1 (Day 0):** Welcome + deliver lead magnet
  → If opened → continue sequence
  → If not opened after 48hrs → resend with new subject line

**Email 2 (Day 2):** Quick win / immediate value
  → Click on resource link → +10 points

**Email 3 (Day 5):** Story-driven lesson (pain point)
  → If score > 30 → move to fast-track (skip to Email 5)

**Email 4 (Day 8):** Case study / social proof

**Email 5 (Day 11):** Soft pitch — introduce offer
  → Click on sales page → +25 points, tag as "sales-interested"

**Email 6 (Day 14):** Objection handling
  → If purchased → exit sequence, enter customer onboarding

**Email 7 (Day 18):** Final CTA with urgency / deadline
  → If no purchase → move to long-term nurture sequence
```

**GATE: Present the sequence map and wait for user approval before writing email copy.**

---

## Phase 3: Write Email Copy

With an approved sequence map, write each email in the campaign.

### Email Structure (per email)

1. **Subject line** — 6-10 words, curiosity or benefit-driven
2. **Preview text** — complements the subject line (40-90 characters)
3. **Body copy** — 150-300 words per email (short, scannable)
4. **Single CTA** — one clear action per email
5. **Conditional logic notes** — what triggers based on subscriber behavior

### Writing Rules

- Write in second person ("you") with a conversational tone
- Each email must standalone — subscribers may skip emails
- Front-load value before any pitch
- Include personalization tokens where relevant: {first_name}, {lead_magnet_name}
- Sales emails (5-7) use direct response copywriting principles

---

## Phase 4: Polish

After all emails are written, deliver these finishing elements.

### 1. Lead Scoring Matrix

```
## Lead Scoring

| Action | Points |
|--------|--------|
| Email open | +5 |
| Link click | +10 |
| Sales page visit | +25 |
| Pricing page visit | +25 |
| Reply to email | +15 |
| No open (3 consecutive) | -20 |

**Thresholds:**
- Score > 50 → Tag as "engaged", move to fast-track
- Score > 80 → Tag as "hot lead", notify for personal outreach
- Score < 0 → Move to re-engagement sequence
```

### 2. Platform Setup Checklist

- [ ] All emails loaded into automation tool
- [ ] Entry trigger configured and tested
- [ ] Conditional branches set with correct logic
- [ ] Lead scoring rules active
- [ ] Exit conditions configured (purchase, unsubscribe)
- [ ] UTM parameters added to all links
- [ ] Test subscriber run through complete sequence

### 3. Performance Benchmarks

Provide target metrics: open rate (35-45% for nurture), click rate (3-5%), conversion rate by email, and unsubscribe threshold per email (under 0.5%).

---

## Anti-Patterns

- **Selling in Email 1** — the first email delivers what was promised. Selling before trust is built kills the sequence.
- **Multiple CTAs per email** — one email, one job, one link. Split focus kills click rates.
- **No conditional logic** — a linear sequence ignores subscriber behavior. Always branch on engagement.
- **Too many emails too fast** — more than one email per day feels like spam. Space them out.
- **Generic subject lines** — "Newsletter #4" gets deleted. Every subject line must earn the open.
- **No exit condition** — subscribers who purchase must leave the sequence immediately.

---

## Recovery

- **No clear campaign goal:** Ask what product or action they want subscribers to take. If no product exists yet, build a lead nurture sequence focused on trust-building.
- **Too many emails requested (15+):** Recommend splitting into two sequences with a trigger between them.
- **No email platform chosen:** Write platform-agnostic copy with conditional logic described in plain language.
- **User wants to sell immediately:** Explain the value-first approach but offer a compressed 3-email sequence with faster pitch timing.
- **Sequence map rejected:** Ask which emails feel wrong — too many, wrong order, or missing a topic. Isolate and fix.
