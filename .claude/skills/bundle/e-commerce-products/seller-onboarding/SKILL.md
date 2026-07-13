---
name: seller-onboarding
description: "Creates seller onboarding programs for marketplaces with verification, listing guides, and success milestones. Use when building seller activation flows for platform businesses."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Seller Onboarding

## When to Use This Skill

Use this skill when you need to:
- Design an onboarding program for sellers joining a marketplace
- Create verification and approval workflows for new sellers
- Build listing guides and templates that ensure quality
- Define seller success milestones and activation metrics

**DO NOT** use this skill for buyer onboarding, SaaS user onboarding, or seller marketing programs. This is for marketplace seller activation and onboarding.

---

## Core Principle

SELLER ONBOARDING HAS ONE GOAL — GET THE SELLER TO THEIR FIRST TRANSACTION AS FAST AS POSSIBLE. EVERY STEP THAT DOES NOT SERVE THAT GOAL IS FRICTION TO REMOVE.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Marketplace type** | "What do sellers offer on your platform? Products, services, rentals?" | No default — must be provided |
| **Seller profile** | "Who is your typical seller? Individual, small business, professional?" | Small business owner |
| **Verification needs** | "What must you verify? Identity, credentials, insurance, inventory?" | Identity and business verification |
| **Current drop-off** | "Where do sellers abandon the onboarding process?" | Unknown — designing from scratch |
| **Time to first sale** | "How long does it take a new seller to get their first transaction?" | Unknown — establishing baseline |
| **Listing complexity** | "How complex is creating a listing? Photos, pricing, descriptions?" | Moderate (title, description, photos, price) |

**GATE: Confirm the brief before designing the onboarding flow.**

---

## Phase 2: Design the Flow

### Onboarding Stages

```
1. Application / Signup
   ↓
2. Verification
   ↓
3. Profile Setup
   ↓
4. First Listing
   ↓
5. Listing Optimization
   ↓
6. First Transaction
   ↓
7. Graduated (active seller)
```

### Verification Workflow

| Verification Type | Method | Timeline |
|-------------------|--------|----------|
| Identity | Government ID upload | 24-48 hours |
| Business | Business license or registration | 24-48 hours |
| Credentials | Professional license or certification | 48-72 hours |
| Background | Third-party background check | 3-5 business days |
| Sample work | Portfolio review by team | 24-48 hours |

Choose only the verifications essential for your marketplace. Each added step increases drop-off.

### Success Milestones

| Milestone | Target Timeframe | Metric |
|-----------|-----------------|--------|
| Profile complete | Day 1 | 100% of required fields filled |
| First listing live | Day 1-3 | At least 1 approved listing |
| Listing optimized | Day 3-7 | Photos, full description, competitive price |
| First inquiry/view | Day 7-14 | At least 1 buyer interaction |
| First transaction | Day 14-30 | Completed sale or booking |

**GATE: Confirm flow and milestones before writing onboarding content.**

---

## Phase 3: Write

### Welcome Email

```
Subject: Welcome to [Platform] — here is your path to your first sale

Hey [Name],

You are in. Here is exactly what to do next:

1. Complete your profile (2 minutes)
2. Create your first listing (5 minutes)
3. Get your first sale

We have helped [X] sellers get started, and most get their first inquiry within [timeframe]. Let me show you how.

[Complete My Profile →]
```

### Listing Guide

Create a step-by-step listing creation guide:

**Title:** Be specific. "[Service/Product] for [audience] — [key differentiator]"
- Good: "Brand Identity Design for Startups — Logo, Colors, Typography"
- Bad: "Design Services"

**Description:** Follow this structure:
1. What the buyer gets (deliverables)
2. How it works (process)
3. Who it is for (ideal buyer)
4. Why choose you (differentiator)

**Photos:** Minimum 3, maximum 8. First photo is the listing thumbnail — make it count.

**Pricing:** Research 5 competitors on the platform. Price within 20% of the average to start.

### Seller Success Email Sequence

| Email | Timing | Subject | Purpose |
|-------|--------|---------|---------|
| Welcome | Day 0 | "Your path to your first sale" | Activate profile and first listing |
| Listing tips | Day 2 | "Top sellers do this with their listings" | Optimize listing quality |
| First week check | Day 7 | "How is your first week going?" | Re-engage and offer help |
| Boost offer | Day 14 | "Get more visibility for your listing" | Promote listing if no transactions |
| Success story | Day 21 | "How [Seller] got 10 sales in their first month" | Social proof and motivation |

---

## Phase 4: Polish

### 1. Listing Quality Scorecard

```
## Listing Quality Score

| Element | Points | Criteria |
|---------|--------|----------|
| Title | /20 | Specific, includes key terms, under 80 chars |
| Description | /25 | Covers deliverables, process, audience, differentiator |
| Photos | /20 | Minimum 3, high quality, first photo is compelling |
| Pricing | /15 | Competitive, clear, no hidden fees |
| Response time | /10 | Under 4 hours average |
| Profile completeness | /10 | Photo, bio, credentials, reviews |

**Score 80+:** Featured placement eligible
**Score 60-79:** Standard listing
**Score below 60:** Improvement suggestions sent automatically
```

### 2. Seller Dashboard Recommendations

Show new sellers:
- Profile completion percentage
- Listing quality score
- Views and inquiries count
- Comparison to average seller in their category
- Next step recommendation (always one clear action)

### 3. Quality Checklist

```
## Seller Onboarding Checklist

- [ ] Onboarding stages defined (application → first transaction)
- [ ] Verification requirements are minimal and clearly communicated
- [ ] Verification timeline is stated upfront (no surprises)
- [ ] Welcome email sends immediately on approval
- [ ] Listing guide with examples is provided
- [ ] Listing quality scorecard is defined
- [ ] 5-email onboarding sequence covers Days 0-21
- [ ] Success milestones are defined with target timeframes
- [ ] Seller dashboard shows next-step recommendations
- [ ] Drop-off points are tracked and optimized
```

---

## Example

**Marketplace:** Freelance photography platform
**Seller:** Professional and semi-professional photographers

**Listing guide excerpt:**
"Your first photo IS your listing. Buyers scroll fast — you have 2 seconds. Use your strongest portfolio piece as the thumbnail. Not a selfie, not a logo, not a sunset. Your best client work, period."

**Milestone tracker:**
"Day 1: Profile live with headshot and bio. Day 3: First portfolio listing with 5+ photos. Day 7: Pricing set within 15% of category average. Day 14: First inquiry received."

---

## Anti-Patterns

- **Too much verification upfront** — verify the minimum needed for trust. Add deeper verification as sellers level up.
- **No listing examples** — telling sellers to "create a great listing" without showing what great looks like guarantees mediocre listings.
- **Ignoring time-to-first-sale** — if sellers wait 30+ days for a first transaction, they will leave. Actively drive demand to new sellers.
- **One-size-fits-all onboarding** — a professional with 100 sales elsewhere needs a different path than a complete beginner.
- **No quality control** — low-quality listings damage the entire marketplace. Set standards and enforce them.

---

## Recovery

- **High drop-off at verification:** Reduce required documents. Allow sellers to start listing while verification processes in the background.
- **Listings are low quality:** Send automated improvement suggestions based on the quality scorecard. Offer a listing review service.
- **Sellers are not getting sales:** Manually feature new sellers, send buyer emails highlighting new providers, or offer first-transaction promotions.
- **Sellers ask too many questions:** The onboarding materials are unclear. Rewrite based on the top 5 support questions.
