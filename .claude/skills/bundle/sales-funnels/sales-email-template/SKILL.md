---
name: sales-email-template
description: "Writes individual sales email templates for follow-up, proposal, negotiation, and close scenarios. Use when you need ready-to-send sales emails for specific situations."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Sales Email Template

## When to Use This Skill

Use this skill when you need to:
- Write a sales email for a specific scenario (follow-up, proposal, negotiation, close)
- Create reusable email templates with personalization placeholders
- Build a library of sales emails for different stages of the sales process
- Improve response rates on outbound or follow-up sales communications

**DO NOT** use this skill for email marketing campaigns, drip sequences, or newsletters. This is for one-to-one sales emails sent to prospects and leads.

---

## Core Principle

EVERY SALES EMAIL MUST EARN A REPLY — NOT JUST AN OPEN. IF THE RECIPIENT CANNOT RESPOND IN UNDER 30 SECONDS, THE ASK IS TOO BIG.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Email scenario** | "What type of sales email? (cold outreach, follow-up, proposal, negotiation, close)" | No default — must be provided |
| **Prospect context** | "Who is the recipient? What do you know about them?" | Business owner, some familiarity |
| **Your offer** | "What are you selling?" | No default — must be provided |
| **Previous interaction** | "What has happened before this email? (met at event, had a call, sent proposal)" | Varies by scenario |
| **Desired next step** | "What action do you want them to take?" | Book a call or reply |
| **Tone** | "Professional, casual, direct?" | Professional but human |

**GATE: Confirm the scenario and context before writing.**

---

## Phase 2: Email Design

### Scenario-Specific Frameworks

**Cold Outreach:**
- Hook: Reference something specific about them (recent post, company news, mutual connection)
- Value: One sentence on how you can help
- Proof: One credibility point (client result, relevant experience)
- CTA: Simple question that's easy to respond to

**Follow-Up (after call/meeting):**
- Reference: Specific detail from the conversation
- Recap: Key takeaway or agreed-upon next step
- Value add: Share something useful (article, resource, idea)
- CTA: Confirm the next step with a specific date/time

**Proposal Send:**
- Context: Brief reminder of their problem and your solution
- Proposal: Attach or link to the proposal
- Highlight: Call out the 1-2 most relevant sections
- CTA: "Take a look and let me know if you have questions. Happy to hop on a quick call to walk through it."

**Negotiation:**
- Acknowledge: Their concern or counter-offer
- Reframe: Shift focus from price to value/ROI
- Flexibility: What you can adjust (timeline, scope, payment terms)
- CTA: Suggest a specific compromise

**Close:**
- Urgency: Why now matters (timing, availability, pricing)
- Recap: The key benefits they've already acknowledged
- Simplify: Remove any remaining friction
- CTA: Direct ask for the commitment

**GATE: Confirm the framework approach before writing the email.**

---

## Phase 3: Write the Email

### Email Structure (all scenarios)

1. **Subject line** — 5-8 words, relevant and personal
2. **Opening line** — personalized, no generic greetings
3. **Body** — 3-6 sentences max (under 150 words)
4. **CTA** — one clear, low-friction ask
5. **Sign-off** — professional, warm

### Writing Rules

- Under 150 words total — short emails get more replies
- One CTA per email — do not ask them to "check out our website AND book a call AND review the proposal"
- No attachments in cold emails — they trigger spam filters and create friction
- Personalization must feel genuine, not stalker-ish
- Write at a 6th grade reading level — simple language, short sentences
- Avoid sales jargon: "synergy," "touch base," "circle back," "leverage"

### Template Format

Use {placeholders} for personalization:

```
Subject: {specific_reference} — quick question

Hi {first_name},

{Personalized opening referencing something specific about them or their business.}

{1-2 sentences on how you can help, tied to their specific situation.}

{One proof point: "We helped [similar company] achieve [specific result]."}

{CTA question — easy to respond to with a yes/no or short answer.}

Best,
{your_name}
```

---

## Phase 4: Polish

### 1. Follow-Up Cadence

If no reply, recommend a follow-up schedule:
- Follow-up 1: 3 business days later (add value, don't just "check in")
- Follow-up 2: 5 business days later (new angle or resource)
- Follow-up 3: 7 business days later (breakup email — "Should I close your file?")

### 2. Subject Line Variations

Provide 3 subject line options per email, testing different approaches.

### 3. Response Handling Guide

For each likely response type, provide a suggested reply:
- Positive response → move to next step
- "Not now" → schedule follow-up, stay helpful
- Price objection → value reframe
- No response → follow-up sequence
- "Not interested" → graceful exit, leave door open

---

## Anti-Patterns

- **"Just checking in" follow-ups** — every follow-up must add new value or a new angle. Never just "bump this to the top of your inbox."
- **Wall-of-text emails** — anything over 200 words in a sales email gets skimmed or skipped.
- **Generic openers** — "I hope this email finds you well" signals mass email. Personalize the first line.
- **Multiple asks** — "Could you review the proposal, share it with your team, and let me know your budget?" is three asks. Pick one.
- **Overselling in email** — the email's job is to get a reply or book a call. The selling happens on the call.

---

## Recovery

- **No information about the prospect:** Write a template with clear {placeholder} instructions for what to research and customize before sending.
- **User wants a long, detailed email:** Explain that reply rates drop significantly past 150 words. Offer to create a longer proposal document linked from a short email instead.
- **Cold email compliance concerns:** Include a note about CAN-SPAM (US), GDPR (EU), and CASL (Canada) requirements — identification, opt-out, and legitimate interest.
- **No previous interaction:** Default to cold outreach framework. Focus on relevance and a single low-friction CTA.
