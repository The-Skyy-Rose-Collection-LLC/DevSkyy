---
name: customer-journey-map
description: Maps the full customer journey from awareness through advocacy, identifying touchpoints, emotions, pain points, and conversion gaps. Use when a user wants to understand their customer experience end-to-end, find drop-off points, improve conversion at specific stages, or design a better onboarding/purchase flow.
allowed-tools: Read Write Bash(mkdir:*)
---

# Customer Journey Map

## When to Use This Skill

- User wants to understand how customers move from discovery to purchase to loyalty
- User is experiencing drop-off at a specific stage and wants to diagnose why
- User is launching a new product/service and needs to design the full experience
- User wants to compare their current journey against an ideal journey
- User says things like "where am I losing customers" or "map my funnel" or "customer experience"

## Core Principle

EVERY JOURNEY STAGE MUST INCLUDE: what the customer DOES, what they THINK, what they FEEL, and what GAPS exist between their expectation and reality.

## Workflow

### Step 1: Gather Context

Ask the user for:
1. What product or service is this journey for?
2. Who is the primary customer persona? (role, goals, frustrations)
3. What channels do customers use to find you? (organic, paid, referral, social)
4. Where do you think customers are dropping off today?

If the user cannot answer all four, proceed with what they provide and flag assumptions.

### Step 2: Define Journey Stages

Map the journey across these 6 standard stages:

| Stage | Customer Goal | Key Question |
|-------|--------------|--------------|
| **Awareness** | Realize they have a problem | "How do they first hear about you?" |
| **Consideration** | Evaluate options | "What are they comparing you against?" |
| **Decision** | Choose and purchase | "What triggers the final yes?" |
| **Onboarding** | Get first value | "How fast do they see results?" |
| **Retention** | Continue using/buying | "Why do they stay or leave?" |
| **Advocacy** | Recommend to others | "What makes them tell a friend?" |

### Step 3: Map Each Stage

For every stage, document:

1. **Touchpoints** — Every interaction (website visit, email, call, ad, etc.)
2. **Actions** — What the customer literally does at this stage
3. **Thoughts** — What questions or concerns they have
4. **Emotions** — Their emotional state (excited, confused, anxious, delighted)
5. **Pain Points** — Friction, confusion, or frustration they experience
6. **Opportunities** — Gaps where you could improve the experience

### Step 4: Identify Critical Gaps

Analyze the map for:
- **Drop-off points** — Where customers leave and never come back
- **Emotion dips** — Where positive sentiment turns negative
- **Missing touchpoints** — Stages with no proactive communication
- **Handoff failures** — Where the customer is passed between systems/people and context is lost
- **Time gaps** — Where too much time passes between interactions

### Step 5: Deliver the Journey Map

Output a complete text-based journey map using this format, plus a prioritized list of 3-5 improvements ranked by impact and effort.

## Example 1: Online Course Creator

**Context:** Sarah sells a $497 online course on email marketing for small businesses.

```
CUSTOMER JOURNEY MAP: Email Marketing Mastery Course
Customer Persona: Small business owner, 1-5 employees, $50K-$200K revenue
Primary channels: Instagram, podcast guesting, Google search

================================================================
STAGE 1: AWARENESS
================================================================
Touchpoints:  Instagram Reels, podcast guest appearances, blog posts (SEO)
Actions:      Sees a reel about email open rates > clicks profile > reads bio
Thoughts:     "My emails get terrible open rates. Maybe I'm doing it wrong."
Emotions:     Frustrated (with current results), Curious (about better way)
Pain Points:  Hard to tell if Sarah is credible from a 30-second reel
Opportunities: Add social proof to bio; pin a testimonial reel

================================================================
STAGE 2: CONSIDERATION
================================================================
Touchpoints:  Free lead magnet (Email Subject Line Swipe File), email nurture sequence, sales page
Actions:      Downloads swipe file > reads 3-4 nurture emails > visits sales page > checks reviews
Thoughts:     "This free stuff is good, but is the course worth $497?"
Emotions:     Interested but skeptical, price-sensitive
Pain Points:  Nurture sequence is 14 days — too long, loses momentum
Opportunities: Shorten nurture to 7 days; add case study email on day 3

================================================================
STAGE 3: DECISION
================================================================
Touchpoints:  Sales page, checkout page, cart abandonment email
Actions:      Reads sales page > adds to cart > hesitates > leaves > gets abandonment email > purchases
Thoughts:     "Can I get a refund if it doesn't work? Will I actually finish it?"
Emotions:     Anxious about spending, fear of wasting money
Pain Points:  Guarantee policy buried at bottom of sales page; no payment plan visible
Opportunities: Move guarantee above the fold; add 3-payment option prominently

================================================================
STAGE 4: ONBOARDING
================================================================
Touchpoints:  Welcome email, course platform login, Module 1
Actions:      Gets login > enters platform > watches Module 1 intro > completes first exercise
Thoughts:     "OK, where do I start? This is a lot of content."
Emotions:     Excited but overwhelmed
Pain Points:  No clear "start here" path; platform navigation is confusing
Opportunities: Add a "Quick Win in 24 Hours" guided path; simplify dashboard

================================================================
STAGE 5: RETENTION
================================================================
Touchpoints:  Weekly check-in emails, community forum, office hours
Actions:      Completes 3 of 8 modules > stops logging in > gets re-engagement email > returns
Thoughts:     "I got busy. I'll finish it later. Did I even make progress?"
Emotions:     Guilty, disengaged
Pain Points:  No progress tracking; community feels dead (low engagement)
Opportunities: Add progress bar + milestone celebrations; seed community with daily prompts

================================================================
STAGE 6: ADVOCACY
================================================================
Touchpoints:  Completion certificate, referral program, testimonial request
Actions:      Finishes course > gets certificate > shares on LinkedIn > refers a friend
Thoughts:     "That was worth it. My open rates went from 18% to 34%."
Emotions:     Proud, accomplished, generous
Pain Points:  No referral incentive; testimonial request comes too late (30 days after)
Opportunities: Ask for testimonial at moment of completion; offer 20% referral commission

================================================================
TOP 3 IMPROVEMENTS (Impact vs Effort)
================================================================
1. Shorten nurture sequence from 14 to 7 days [HIGH impact, LOW effort]
2. Add "Quick Win in 24 Hours" onboarding path [HIGH impact, MEDIUM effort]
3. Move guarantee + payment plan above the fold on sales page [HIGH impact, LOW effort]
```

## Example 2: Local Service Business

**Context:** Mike runs a residential cleaning company in Austin, TX.

```
CUSTOMER JOURNEY MAP: CleanPro Austin — Residential Cleaning
Customer Persona: Dual-income household, kids, $100K+ HHI, values time over money
Primary channels: Google search, Nextdoor, referrals from friends

================================================================
STAGE 1: AWARENESS
================================================================
Touchpoints:  Google "house cleaning Austin", Nextdoor recommendations, friend referral
Actions:      Searches Google > sees CleanPro in map pack > clicks website
Thoughts:     "I need someone reliable. Last cleaner was inconsistent."
Emotions:     Hopeful but guarded (burned before)
Pain Points:  Website loads slowly on mobile; no reviews visible on homepage
Opportunities: Speed up mobile site; embed Google reviews on homepage

================================================================
STAGE 2: CONSIDERATION
================================================================
Touchpoints:  Website, Google reviews, quote request form, phone call
Actions:      Reads services page > checks Google reviews (4.6 stars) > submits quote form
Thoughts:     "Are they insured? Do they bring their own supplies? Can I trust them in my home?"
Emotions:     Cautious, comparing 2-3 options
Pain Points:  Quote form asks too many fields (12); no instant pricing estimate
Opportunities: Reduce form to 4 fields; add instant price calculator

================================================================
STAGE 3: DECISION
================================================================
Touchpoints:  Quote email, follow-up call, booking confirmation
Actions:      Receives quote email > calls with questions > books first cleaning
Thoughts:     "Price is fair. Let me try one cleaning before committing to recurring."
Emotions:     Cautiously optimistic
Pain Points:  Quote email is plain text, looks unprofessional; no photos of team
Opportunities: Design branded quote template; include team photo + bio

================================================================
STAGE 4: ONBOARDING (First Clean)
================================================================
Touchpoints:  Pre-clean checklist email, day-of text from cleaner, post-clean follow-up
Actions:      Receives prep checklist > lets team in > inspects after > responds to follow-up
Thoughts:     "Did they get the corners? Will they be consistent next time?"
Emotions:     Evaluating critically — this clean determines everything
Pain Points:  No way to leave specific instructions for the team; post-clean follow-up is generic
Opportunities: Add a "special instructions" field; send personalized follow-up asking about specific rooms

================================================================
STAGE 5: RETENTION
================================================================
Touchpoints:  Recurring booking reminders, quality check calls, seasonal upsell emails
Actions:      Continues biweekly service > occasionally skips > gets loyalty discount at 6 months
Thoughts:     "They're consistent. I don't even think about cleaning anymore."
Emotions:     Relieved, loyal
Pain Points:  Different cleaners each visit — no consistency in who shows up
Opportunities: Assign a dedicated team; notify client if team changes

================================================================
STAGE 6: ADVOCACY
================================================================
Touchpoints:  Referral card, Google review request, Nextdoor mention
Actions:      Tells neighbor > posts on Nextdoor > leaves Google review
Thoughts:     "Mike's team is great. Happy to recommend."
Emotions:     Satisfied, generous
Pain Points:  No referral reward; never asked directly for a review
Opportunities: Offer $25 credit per referral; send review request after 3rd clean (not 1st)

================================================================
TOP 3 IMPROVEMENTS (Impact vs Effort)
================================================================
1. Add instant price calculator to website [HIGH impact, MEDIUM effort]
2. Assign dedicated cleaning teams to recurring clients [HIGH impact, LOW effort]
3. Send Google review request after 3rd clean with direct link [HIGH impact, LOW effort]
```

## Recovery and Fallback

- If the user only knows 1-2 stages well, map those in detail and mark other stages as "NEEDS DISCOVERY — schedule customer interviews to fill this gap"
- If the user has no customer data, build a hypothesis journey and label it "ASSUMED — validate with 5 customer conversations"
- If the user's business model does not fit 6 stages (e.g., one-time purchase with no retention), collapse stages and note why
- If 3 attempts to clarify the persona or channels fail, proceed with the most common persona for their industry and flag all assumptions

## Constraints

- **NEVER fabricate customer data** — if the user does not provide data, label assumptions clearly
- **ALWAYS include emotions** — this is what separates a journey map from a basic funnel
- **ALWAYS output a prioritized improvement list** — the map without actions is just a diagram
- Keep each stage section to 6-8 lines maximum
- Use text-based formatting only (no images, no Mermaid, no external tools)
- One persona per map — if multiple personas exist, create separate maps
