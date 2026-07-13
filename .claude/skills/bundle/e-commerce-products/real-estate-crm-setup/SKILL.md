---
name: real-estate-crm-setup
description: "Sets up real estate CRM systems with pipeline stages, lead scoring, and automated follow-up sequences."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Real Estate CRM Setup

## When to Use This Skill

Use this skill when you need to:
- Set up or restructure a CRM for real estate lead management
- Define pipeline stages that match the buyer and seller journey
- Create lead scoring criteria to prioritize follow-up efforts
- Design automated follow-up sequences for different lead types

**DO NOT** use this skill for CRM software selection, technical integrations, or general sales CRM setup. This is for real estate-specific CRM configuration.

---

## Core Principle

YOUR CRM IS ONLY AS GOOD AS YOUR PROCESS — THE BEST TOOL IN THE WORLD FAILS IF YOUR PIPELINE STAGES, FOLLOW-UP SEQUENCES, AND LEAD SCORING DO NOT MATCH HOW REAL ESTATE DEALS ACTUALLY HAPPEN.

---

## Phase 1: CRM Requirements

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **CRM platform** | "What CRM are you using — Follow Up Boss, KVCore, LionDesk, other?" | Follow Up Boss |
| **Business model** | "Are you a solo agent, team, or brokerage?" | Solo agent |
| **Lead sources** | "Where do your leads come from — Zillow, website, referrals, social, open houses?" | Mixed — referrals, Zillow, and website |
| **Monthly lead volume** | "How many new leads do you get per month?" | 20-50 |
| **Current pain point** | "What is not working in your current follow-up process?" | Leads falling through the cracks |

**GATE: Confirm platform and lead sources before designing the system.**

---

## Phase 2: Pipeline Design

### Buyer Pipeline Stages

```
## Buyer Pipeline

| Stage | Definition | Action Required |
|-------|-----------|----------------|
| New Lead | Just entered the system — no contact yet | Make first contact within 5 minutes |
| Contacted | Initial conversation completed | Qualify: timeline, budget, pre-approval |
| Qualifying | Gathering requirements, assessing readiness | Schedule buyer consultation |
| Active Buyer | Pre-approved, actively searching | Set up property alerts, schedule showings |
| Showing | Actively touring properties | Follow up after each showing |
| Offer Submitted | Offer written and presented | Monitor negotiations, update client |
| Under Contract | Offer accepted, in escrow | Manage inspection, appraisal, closing tasks |
| Closed | Transaction completed | Move to past client nurture pipeline |
| Lost / Inactive | Not responsive or chose another agent | Add to long-term nurture sequence |
```

### Seller Pipeline Stages

```
## Seller Pipeline

| Stage | Definition | Action Required |
|-------|-----------|----------------|
| New Lead | Seller inquiry received | Make first contact within 5 minutes |
| Contacted | Initial conversation completed | Schedule listing appointment |
| Listing Appointment | Meeting scheduled | Prepare CMA and listing presentation |
| Pre-Listing | Preparing to list — staging, photos, pricing | Coordinate listing prep tasks |
| Active Listing | Property on market | Weekly seller updates, showing feedback |
| Under Contract | Accepted offer, in escrow | Manage contingencies and closing process |
| Closed | Transaction completed | Move to past client nurture pipeline |
| Lost / Inactive | Did not list or chose another agent | Add to long-term nurture sequence |
```

---

## Phase 3: Lead Scoring

### Scoring Criteria

```
## Lead Scoring Model

### Timeline Score (0-30 points)
| Timeline | Points |
|----------|--------|
| Buying/selling within 30 days | 30 |
| Within 1-3 months | 20 |
| Within 3-6 months | 10 |
| 6+ months or "just looking" | 5 |

### Financial Readiness (0-30 points)
| Status | Points |
|--------|--------|
| Pre-approved / home equity available | 30 |
| Spoken with lender, not yet approved | 15 |
| Have not contacted a lender | 5 |

### Engagement Level (0-20 points)
| Behavior | Points |
|----------|--------|
| Responded to follow-up within 24 hours | 10 |
| Attended showing or meeting | 10 |
| Opened emails but no response | 3 |
| No engagement | 0 |

### Lead Source Quality (0-20 points)
| Source | Points |
|--------|--------|
| Personal referral | 20 |
| Past client | 20 |
| Direct website inquiry | 15 |
| Open house sign-in | 10 |
| Zillow/portal lead | 5 |
| Purchased lead list | 3 |

### Priority Tiers
| Score | Priority | Follow-Up Cadence |
|-------|----------|------------------|
| 70-100 | Hot | Daily contact |
| 40-69 | Warm | 2-3x per week |
| 20-39 | Nurture | Weekly |
| 0-19 | Long-term | Monthly drip |
```

---

## Phase 4: Automated Sequences

### New Lead Response Sequence

```
## New Lead — First 7 Days

**Minute 1:** Auto-text: "Hi [Name], this is [Your name] with [Company].
I saw your interest in [property/area]. When is a good time to chat?"

**Minute 5:** Phone call attempt #1

**Hour 1 (if no answer):** Email: Introduction + value proposition + CTA

**Day 1 (evening):** Phone call attempt #2

**Day 2:** Text: "Hi [Name], just following up. Are you looking to
buy or sell in [area]? I'd love to help."

**Day 3:** Phone call attempt #3

**Day 5:** Email: Market update for their area of interest + CTA

**Day 7:** Text: Final initial outreach — "I don't want to be a pest,
but I'm here whenever you're ready. Save my number."

**After Day 7:** Move to nurture sequence if no response.
```

### Past Client Nurture Sequence

```
## Past Client — Annual Touchpoints

| Month | Touchpoint | Method |
|-------|-----------|--------|
| January | Market year-in-review | Email |
| February | Home anniversary congratulations | Handwritten card |
| March | Spring home maintenance tips | Email |
| May | Home valuation update | Email + CTA |
| July | Summer check-in | Phone call |
| September | Fall market update | Email |
| November | Gratitude note | Handwritten card |
| December | Holiday greeting | Card or small gift |

**Ongoing:** Monthly newsletter subscription
**Goal:** 12+ touchpoints per year
```

### CRM Setup Checklist

- [ ] Pipeline stages configured for buyers and sellers
- [ ] Lead scoring criteria implemented
- [ ] Automated new lead response sequence active
- [ ] Past client nurture sequence scheduled
- [ ] Lead sources tagged for tracking ROI
- [ ] Property alerts configured for active buyers
- [ ] Task reminders set for manual follow-up steps
- [ ] Reporting dashboard showing pipeline and conversion metrics

---

## Anti-Patterns

- **Too many pipeline stages** — complexity kills adoption. Keep it under 10 stages per pipeline.
- **No speed-to-lead process** — responding to new leads hours later instead of minutes dramatically reduces conversion.
- **Set it and forget it** — automation handles the first touch, but conversion requires personal follow-up.
- **Not tracking lead sources** — without source tracking, you cannot calculate ROI on marketing spend.
- **Overcomplicating lead scoring** — start simple and refine. A basic hot/warm/cold system beats an unused 100-point model.

---

## Recovery

- **CRM has messy data:** Deduplicate contacts, update pipeline stages, and tag all leads by source. Schedule a quarterly cleanup.
- **Team not using the CRM:** Simplify the process, demonstrate ROI, and make CRM usage non-negotiable for lead assignments.
- **Low response rates on automated sequences:** Test different messaging, timing, and channels. Personalize the first touch.
- **Too many leads to follow up with:** Use lead scoring to prioritize. Focus daily effort on hot leads, automate nurture for the rest.
- **Switching CRM platforms:** Export all contacts with tags and notes. Map old pipeline stages to new ones. Rebuild automation sequences.
