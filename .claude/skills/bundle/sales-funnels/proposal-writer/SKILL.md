---
name: proposal-writer
description: "Generates complete client proposals from a conversational scope discussion, producing a professional document with executive summary, problem statement, proposed solution, deliverables, pricing, timeline, and terms. Use when a user needs to send a proposal to a prospect, formalize a project scope, or respond to an RFP."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Proposal Writer

## When to Use This Skill

Use this skill when:
- A user needs to send a proposal to a prospect or client before starting work
- Someone wants to formalize a project scope into a professional document
- A user is responding to an RFP (request for proposal) and needs a structured response
- A freelancer, consultant, or agency owner says they need to "write up a proposal"
- A user has finished a discovery call and needs to turn the conversation into a deliverable

**DO NOT** use this skill for:
- Internal project briefs or plans (those are not client-facing proposals)
- Invoices or payment requests (those happen after the proposal is accepted)
- Contracts or legal agreements (proposals precede contracts; use a contract skill for binding documents)
- Pitch decks or slide presentations (use a pitch-deck skill instead)

---

## Core Principle

A PROPOSAL IS A DECISION DOCUMENT, NOT A BROCHURE. EVERY SECTION MUST HELP THE CLIENT SAY YES BY ANSWERING: WHAT IS THE PROBLEM, HOW WILL YOU SOLVE IT, WHAT WILL IT COST, AND WHEN WILL IT BE DONE.

---

## Phase 1: Scope Interview

Conduct a structured conversation to extract everything needed to write the proposal. **Do not skip this phase.** A proposal built on assumptions will lose the deal.

### Group 1 -- Client and Project Context (ask all at once):

1. Who is the client? (Company name, contact name, their role)
2. What is the project? (One sentence describing what they want done)
3. How did this opportunity come about? (Referral, inbound lead, cold outreach, RFP)
4. What industry or niche is the client in?

### Group 2 -- Problem and Outcomes (ask after Group 1 is answered):

5. What problem is the client trying to solve? (In their words, not yours)
6. What has the client already tried? (Previous solutions, vendors, or internal attempts)
7. What does success look like for this project? (Specific outcomes, metrics, or end states)
8. Who are the stakeholders or decision-makers beyond your main contact?

### Group 3 -- Scope and Constraints (ask after Group 2 is answered):

9. What are the key deliverables? (List everything the client expects to receive)
10. What is the budget range? (Even a rough range helps: "They said $5K-$8K" or "No idea, mid-market client")
11. What is the desired timeline? (Start date, end date, or key milestones)
12. Are there any constraints or non-negotiables? (Tech stack, brand guidelines, regulatory, internal deadlines)
13. What pricing model makes sense? (Fixed-price, retainer, tiered -- see Pricing Frameworks below)

### Scope Interview Tips

- If the user says "I don't know" to budget: default to presenting a tiered pricing model (Good / Better / Best) so the client can self-select.
- If the user cannot articulate the client's problem: ask them to recall the discovery call. "What did the client complain about? What was the trigger that made them reach out?"
- If deliverables are vague: push for specifics. "When you say 'website redesign,' does that mean 5 pages, 15 pages, e-commerce, blog, all of the above?"

**GATE: Do not proceed to Phase 2 until you have answers to at least questions 1, 2, 5, 7, 9, and either 10 or 13.** A proposal without a clear problem, outcome, deliverables, and pricing direction is not ready to write.

---

## Phase 2: Structure the Proposal

Build the proposal using this exact structure. Every section is required unless marked optional.

### Proposal Document Structure

```
# [Project Name] -- Proposal for [Client Company]

Prepared by: [User's Name / Company]
Prepared for: [Client Contact Name], [Client Company]
Date: [Today's date]

---

## Executive Summary

[2-4 sentences. State the problem, the proposed solution, the primary
outcome, and the investment range. This is the only section some
decision-makers will read -- make it count.]

---

## Problem Statement

[3-5 sentences. Describe the client's current situation, the pain
it causes, and why it needs to be addressed now. Use the client's
own language from the discovery conversation. Do NOT use jargon.]

---

## Proposed Solution

[1-2 paragraphs. Describe your approach at a high level. Explain
WHY this approach works, not just WHAT you will do. Connect the
solution directly back to the stated problem.]

---

## Deliverables

| # | Deliverable | Description | Timeline |
|---|-------------|-------------|----------|
| 1 | [Item] | [What the client receives] | [When] |
| 2 | [Item] | [What the client receives] | [When] |
| 3 | [Item] | [What the client receives] | [When] |

---

## Pricing

[Use the appropriate pricing framework -- see below.
Always present pricing AFTER deliverables so the client
understands what they are paying for before seeing the number.]

---

## Project Timeline

| Phase | Milestone | Duration | Target Date |
|-------|-----------|----------|-------------|
| 1 | [Milestone] | [X days/weeks] | [Date] |
| 2 | [Milestone] | [X days/weeks] | [Date] |
| 3 | [Milestone] | [X days/weeks] | [Date] |

---

## Terms & Conditions

### Payment Terms
[Payment schedule: e.g., 50% upfront, 50% on completion]

### Revision Policy
[Number of revision rounds included: default to 2 rounds]

### Ownership & IP
[Who owns the deliverables after final payment]

### Cancellation
[What happens if either party needs to cancel mid-project]

### Validity
[How long this proposal is valid: default to 14 days]

---

## Next Steps

1. Review this proposal
2. Reply with any questions or requested changes
3. Sign and return to begin the project on [proposed start date]
```

### Section-by-Section Writing Rules

**Executive Summary:**
- Write this LAST, after all other sections are complete
- Must stand alone -- a decision-maker should be able to read only this section and understand the proposal
- Include the investment amount or range
- Keep to 2-4 sentences maximum

**Problem Statement:**
- Use the client's own words and framing from the scope interview
- Never blame the client for the problem
- Connect the problem to a business impact (lost revenue, wasted time, missed opportunity)

**Proposed Solution:**
- Lead with the outcome, not the process
- Avoid listing tools or technologies unless the client specifically asked about them
- One clear approach -- do not present multiple solution options here (save options for pricing tiers)

**Deliverables Table:**
- Every deliverable must be a tangible thing the client receives (a file, a system, a report, a design)
- "Strategy sessions" or "consulting hours" are NOT deliverables on their own -- tie them to a specific output
- Include timeline per deliverable, not just for the whole project

**Pricing:**
- Always present pricing AFTER deliverables
- Use the pricing framework that matches the project type (see below)
- Round to clean numbers ($5,000 not $4,850)

**Timeline:**
- Milestones must be concrete checkpoints, not vague phases
- "Design mockups delivered" is a milestone; "Design phase" is not
- Include a start date assumption

**Terms:**
- Default payment: 50% upfront, 50% on completion for projects under $10K
- Default payment: 50% upfront, 25% at midpoint, 25% on completion for projects over $10K
- Default revisions: 2 rounds included
- Default validity: 14 days
- Adjust any of these based on user input

---

## Pricing Frameworks

Use one of these three frameworks based on the project type. **Default to fixed-price unless the user specifies otherwise.**

### Fixed-Price (Default)

Best for: projects with a clear scope, defined deliverables, and a known end date.

```
## Pricing

**Project Investment: $X,XXX**

This is a fixed-price engagement covering all deliverables listed
above. The investment includes:

- [Deliverable 1]
- [Deliverable 2]
- [Deliverable 3]
- [X] rounds of revisions
- [X] weeks of post-launch support

**Payment Schedule:**
- 50% ($X,XXX) due upon proposal acceptance
- 50% ($X,XXX) due upon final delivery

Additional revisions beyond [X] rounds: $XXX per round.
```

### Retainer (Monthly)

Best for: ongoing services, marketing, support, or advisory work with no fixed end date.

```
## Pricing

**Monthly Retainer: $X,XXX/month**

This retainer covers:

- [Included service 1] (up to [quantity] per month)
- [Included service 2] (up to [quantity] per month)
- [Included service 3]
- [Response time commitment, e.g., "24-hour response on business days"]

**Minimum commitment:** [X] months
**Billing:** Monthly, invoiced on the 1st, due within 15 days

Additional work beyond the retainer scope is billed at $XXX/hour
with prior approval.

Either party may cancel with 30 days written notice after the
minimum commitment period.
```

### Tiered (Good / Better / Best)

Best for: when the client's budget is unknown, or when you want to offer flexibility. **Always recommend the middle tier.**

```
## Pricing

We have structured three options based on scope and investment:

### Option 1: [Tier Name] -- $X,XXX
- [Deliverable 1]
- [Deliverable 2]
- [X] revision rounds
- Best for: [who this tier suits]

### Option 2: [Tier Name] -- $X,XXX (Recommended)
- Everything in Option 1, plus:
- [Additional deliverable]
- [Additional deliverable]
- [X] revision rounds
- Best for: [who this tier suits]

### Option 3: [Tier Name] -- $X,XXX
- Everything in Option 2, plus:
- [Premium deliverable]
- [Premium deliverable]
- [X] revision rounds
- [Ongoing support period]
- Best for: [who this tier suits]

**Payment Schedule:**
- 50% due upon proposal acceptance
- 50% due upon final delivery
```

**Pricing rules:**
- **NEVER list hourly rates in a fixed-price proposal.** The client is buying an outcome, not your time.
- **Round to clean numbers.** $5,000 not $4,850. $3,000/mo not $2,975/mo.
- **Middle tier should be 1.5x to 2x the base tier.** Top tier should be 2x to 3x the base tier.
- **Name tiers with descriptive labels**, not "Bronze / Silver / Gold." Use names like "Foundation / Growth / Scale" or "Essential / Professional / Premium."

---

## Phase 3: Review with User

Present the complete proposal to the user in the chat. Then ask:

1. "Does the executive summary accurately capture what you want to communicate?"
2. "Are the deliverables correct and complete? Anything missing or anything that should be removed?"
3. "Does the pricing feel right for this client and this scope?"
4. "Any changes to the timeline, terms, or payment structure?"

**GATE: Do not write to file until the user explicitly approves.** Acceptable approvals: "looks good," "yes," "approved," "send it," "save it," or similar affirmative.

If the user requests changes, make them and re-present the updated proposal. **If the user requests more than 3 rounds of revisions, pause and ask:** "We have been through several rounds of changes. Would you like to finalize what we have and note any remaining items as follow-ups, or keep refining?"

---

## Phase 4: Deliver

After user approval, write the proposal to a file.

**Step 1:** Determine the output path.

Default filename: `[client-company]-[project-keyword]-proposal.md`

If the user specified a path, use that. Otherwise, write to the current working directory.

**Step 2:** Write the file using the Write tool.

**Step 3:** Confirm delivery. Report: "Your proposal for [Client Company] has been saved to [file path]. The document includes [X] sections, [X] deliverables, and a [pricing model] pricing structure."

**Step 4:** Offer next steps: "Would you like me to also create a follow-up email to send with this proposal?"

---

## Example 1: Web Design Proposal for a Bakery ($5K-$8K, Tiered)

**User says:** "I need to write a proposal for a bakery called Sweet Crumb. The owner, Lisa Martinez, wants a new website. Budget is $5K-$8K. She found me through a referral."

**Phase 1 produces:** Client is Lisa Martinez, Owner, Sweet Crumb Bakery. Problem: outdated single-page Wix site losing 5-10 catering leads/month because there is no catering menu or inquiry form online. Tried to update herself, gave up. Success: professional site with full menu, catering inquiry form, mobile-friendly, self-updatable. Deliverables: 5-page site, inquiry form, Google Maps, SEO. Timeline: 6 weeks. Pricing model: tiered (budget range suggests flexibility).

**Phase 2 produces a proposal with these key sections:**

Executive Summary: "Sweet Crumb Bakery needs a professional website that showcases your full menu, captures catering inquiries, and gives corporate clients confidence in your brand. We will design and build a 5-page website with a catering inquiry system, mobile-responsive design, and a content management system you can update yourself. Investment ranges from $5,000 to $7,500 depending on the package you choose."

Deliverables table: 6 items (wireframes, design mockups, development, inquiry form, content upload, launch and handoff) each with a weekly timeline.

Tiered pricing:
- Foundation ($5,000): 5-page site, mobile-responsive, inquiry form, Maps, 2 revision rounds
- Growth ($6,500, Recommended): adds SEO, Google Business Profile, menu management, 3 revision rounds
- Scale ($7,500): adds online ordering, email signup, 60 days post-launch support

Timeline: 5 phases across 6 weeks with milestones (wireframes approved, mockups approved, development complete, content loaded, site launched).

Terms: 50/50 payment split, 2-3 revision rounds by tier, $200/extra round, 14-day validity.

**Phase 3:** User reviews and says "Looks great, save it."

**Phase 4:** Saved to `sweet-crumb-bakery-website-proposal.md`.

---

## Example 2: Marketing Retainer for a SaaS Startup ($3K/mo, Retainer)

**User says:** "I need a proposal for a SaaS startup called Stackline. They want ongoing content marketing -- blog posts, social media, email newsletters. The founder, Dev Patel, wants to start at $3K/month."

**Phase 1 produces:** Client is Dev Patel, Founder, Stackline (B2B SaaS, project management for remote teams). Problem: 200 paying users but no content engine -- no blog, inconsistent social, flat organic traffic. Previous freelance writer failed due to voice mismatch. Success: go from 200 to 500 paying users in 6 months via content-driven acquisition. Monthly deliverables: 4 blog posts, 12 social posts, 2 newsletters, performance report. Budget: $3K/mo, 6-month minimum. Constraint: Dev approves all blog posts.

**Phase 2 produces a proposal with these key sections:**

Executive Summary: "Stackline needs a consistent content engine to drive organic signups and reduce Dev's involvement in content creation. We will produce 4 SEO-optimized blog posts, 12 social media posts, and 2 email newsletters per month -- all aligned with Stackline's voice and growth goals. The monthly investment is $3,000 with a 6-month commitment."

Deliverables table: 5 items (blog posts 4/mo, social posts 12/mo, newsletters 2/mo, performance report 1/mo, content strategy as one-time Month 1 setup).

Retainer pricing: $3,000/month covering all deliverables plus 1 revision round per blog post, 48-hour response time. Additional posts $500 each. 6-month minimum, 30-day cancellation notice after minimum.

Timeline: 4 phases (onboarding Week 1, strategy Week 2, first deliverables Week 4, full cadence Month 2+).

Terms: monthly invoicing on the 1st, content ownership transfers upon payment, $1,500 early termination fee, 14-day validity.

**Phase 3:** User reviews and approves.

**Phase 4:** Saved to `stackline-content-marketing-proposal.md`.

---

## Anti-Patterns

**NEVER do these when writing proposals:**

- **DO NOT pad the scope with unnecessary deliverables to inflate the price.** Every line item must solve a part of the client's stated problem. If the client needs a website, do not add "social media audit" unless they asked for it.
- **DO NOT list hourly rates in a fixed-price proposal.** Hourly rates invite the client to do math and question your efficiency. Fixed-price means you are selling an outcome. If you must mention hourly overage rates, keep them only in the terms section for out-of-scope work.
- **DO NOT use jargon the client will not understand.** "Responsive UI/UX with progressive enhancement" means nothing to a bakery owner. Say "a website that looks great on phones and desktops."
- **DO NOT present the price before the deliverables.** The client must understand what they are getting before they see the number. Price without context triggers sticker shock.
- **DO NOT write vague deliverables.** "Marketing support" is not a deliverable. "4 SEO blog posts per month, 1,200-1,500 words each" is a deliverable.
- **DO NOT include multiple solution options in the Proposed Solution section.** One clear approach. If you want to offer options, put them in the pricing tiers only.
- **DO NOT use tentative language.** "We might be able to..." or "We could possibly..." undermines confidence. State what you will do.
- **DO NOT copy-paste generic terms from the internet.** Terms should be specific to this project and this client. A $3K retainer and a $50K build have different payment structures.
- **DO NOT skip the executive summary.** Some decision-makers only read the summary and the price. If the summary is missing or weak, you lose them.

---

## Recovery

### User Cannot Define the Problem

If the user struggles to articulate the client's problem:
1. Ask: "What did the client complain about on the discovery call? What specific frustration or goal did they mention?"
2. If still vague, ask: "What will happen to the client's business if they do nothing and keep things as they are?"
3. If after 3 attempts the problem remains unclear: "The problem statement is the backbone of the proposal. Without a clear problem, the proposal will not be persuasive. Would you like to go back to the client with a few clarifying questions before we write this?"

### Budget Is Unknown

If the user has no idea what the client can spend:
1. Default to the tiered pricing framework (Good / Better / Best) so the client can self-select.
2. Ask the user: "What is the minimum you would do this project for, and what would the ideal engagement look like?" Use those as the base and top tiers.
3. If the user cannot even provide a minimum: "Without any pricing anchor, I will structure this as a tiered proposal with ranges typical for [project type] in [industry]. You can adjust the numbers before sending."

### Scope Is Too Large for One Proposal

If the scope interview reveals a project that would exceed 20 deliverables or span more than 6 months:
1. Suggest phasing: "This is a large scope. I recommend splitting it into Phase 1 (the immediate priorities) and Phase 2 (the next stage). We can write the proposal for Phase 1 now and reference Phase 2 as a future engagement."
2. If the user insists on one document, include a phased timeline and milestone-based payments to make the large scope manageable.

### User Wants to Change Pricing Model Mid-Draft

If the user switches from fixed-price to retainer (or vice versa) during Phase 3 review:
1. Do not push back. Rewrite the pricing section using the appropriate framework.
2. Adjust the payment terms to match the new model.
3. Re-present only the changed sections, not the entire proposal.

### File Write Fails

If the Write tool fails:
1. Report the error to the user.
2. Present the complete proposal as formatted text in the chat so the user can copy it manually.
3. Offer to retry with a different file path.

**If 3 write attempts fail, stop attempting and present the proposal in chat.** Tell the user: "I was unable to save the file. The complete proposal is above -- you can copy it directly into your document."

---

## Pre-Delivery Checklist

Before delivering the final proposal (whether to file or in chat), verify:

- [ ] Executive summary can stand alone and includes the investment amount
- [ ] Problem statement uses the client's own language, not jargon
- [ ] Proposed solution connects directly back to the stated problem
- [ ] Every deliverable in the table is a tangible output the client receives
- [ ] Pricing uses clean, round numbers
- [ ] Pricing appears AFTER deliverables in the document
- [ ] Timeline has concrete milestones with dates, not vague phase names
- [ ] Payment terms match the pricing model (fixed vs. retainer vs. tiered)
- [ ] Terms include revision policy, ownership, cancellation, and validity period
- [ ] No hourly rates appear in a fixed-price proposal
- [ ] No jargon the client would need to Google
- [ ] No placeholder text like [TBD] remains unless intentionally flagged
- [ ] Client name and company name are correct throughout
- [ ] Next steps section tells the client exactly what to do
