---
name: email-sequence
description: "Builds complete automated email sequences with timing delays, conditional triggers, A/B subject lines, and platform-specific implementation notes. Use when a user needs a welcome series, nurture sequence, launch sequence, re-engagement campaign, or any multi-email automation flow."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Email Sequence

## When to Use This Skill

Use this skill when you need to:
- Build a welcome series that onboards new subscribers and sets expectations
- Create a nurture sequence that warms leads toward a purchase or action
- Write a launch sequence that drives sales for a product, course, or service drop
- Design a re-engagement campaign that wins back inactive subscribers
- Map out any multi-email automation with timing delays and conditional triggers

**DO NOT** use this skill for one-off email drafts, cold outreach to strangers (use cold-outreach instead), or transactional emails (order confirmations, password resets).

---

## Core Principle

EVERY EMAIL IN THE SEQUENCE MUST EARN THE NEXT OPEN — IF A SUBSCRIBER DOES NOT HAVE A REASON TO OPEN EMAIL 3, EMAILS 4 THROUGH 7 ARE DEAD.

---

## Sequence Type Reference

Use this table to set defaults when the user describes what they need. These are starting points — adjust based on user input.

| Sequence Type | Emails | Duration | Primary Goal | Default Trigger |
|---------------|--------|----------|-------------|----------------|
| **Welcome** | 5 | 14 days | Orient, build trust, deliver lead magnet value | New subscriber opt-in |
| **Nurture** | 7 | 30 days | Educate, build authority, warm toward offer | Completed welcome series |
| **Launch** | 6 | 7 days | Drive purchase during a specific window | Launch date / cart open |
| **Re-engagement** | 3 | 10 days | Reactivate or clean inactive subscribers | No opens in 60+ days |

---

## Phase 1: Strategy

Gather the information needed to build the right sequence. Ask the user for these inputs. If they do not provide them, use the defaults in parentheses.

1. **Sequence type** — welcome, nurture, launch, or re-engagement (ask, no default)
2. **Goal** — what action should the subscriber take by the end? (varies by type)
3. **Audience** — who is receiving this sequence? Be specific about awareness level (problem-aware by default)
4. **Number of emails** — use the reference table defaults unless the user overrides
5. **Platform** — ConvertKit, Mailchimp, ActiveCampaign, or other (ConvertKit by default)
6. **Brand voice** — casual, professional, bold, warm (casual-professional by default)
7. **Product or offer** — what are they ultimately selling or promoting? (ask, no default)
8. **Lead magnet or entry point** — what did the subscriber opt in for? (ask for welcome/nurture)

### Strategy Brief Template

Present this to the user before writing a single email:

```
## Sequence Strategy Brief

**Type:** Welcome series
**Goal:** Convert free subscribers into course buyers within 14 days
**Audience:** Aspiring freelance designers who downloaded the "5 Portfolio Templates" lead magnet
**Emails:** 5 over 14 days
**Platform:** ConvertKit
**Voice:** Casual-professional, encouraging, first-person
**Product:** "Design Freelance Accelerator" online course ($297)
**Entry point:** Free portfolio template PDF download
```

**GATE: Do not proceed to Phase 2 until the user confirms or adjusts the strategy brief.**

---

## Phase 2: Map the Flow

Build the sequence map before writing any email copy. This gives the user a visual overview of the entire automation.

### Sequence Map Format

For each email, define:

1. **Email number and name** — descriptive label (not just "Email 1")
2. **Send timing** — delay from trigger or previous email
3. **Purpose** — one sentence on what this email accomplishes
4. **Conditional trigger** — any branching logic (opened/clicked/purchased)
5. **CTA** — the single action you want the reader to take

### Example Sequence Map: Welcome Series (5 Emails / 14 Days)

```
TRIGGER: New subscriber downloads "5 Portfolio Templates"
  |
  v
EMAIL 1: "The Welcome" (Immediately)
  Purpose: Deliver the lead magnet, set expectations for what's coming
  CTA: Download the templates
  |
  v  [Wait 2 days]
  |
EMAIL 2: "The Quick Win" (Day 2)
  Purpose: Help them get one fast result from the lead magnet
  CTA: Try the 15-minute portfolio exercise
  |
  v  [Wait 2 days]
  |
EMAIL 3: "The Story" (Day 4)
  Purpose: Share your origin story or a client success story to build trust
  CTA: Reply with their biggest freelance challenge
  |
  v  [Wait 3 days]
  |
  +--- IF clicked link in Email 3 ---> Tag "engaged"
  |
EMAIL 4: "The Deeper Problem" (Day 7)
  Purpose: Name the real obstacle they face and position your solution
  CTA: Read the case study / watch the training
  |
  v  [Wait 7 days]
  |
EMAIL 5: "The Invitation" (Day 14)
  Purpose: Present your paid offer as the logical next step
  CTA: Check out the course / book a call
  |
  +--- IF purchased ---> Move to Customer sequence
  +--- IF not purchased ---> Move to Nurture sequence
```

### Conditional Branch Patterns

Use these standard triggers in the sequence map:

| Trigger | Action | Platform Notes |
|---------|--------|---------------|
| Opened Email X | Send follow-up variant | All platforms support this |
| Clicked link in Email X | Tag subscriber, branch to offer path | ConvertKit: "Link Trigger"; Mailchimp: "Click" goal |
| Did NOT open Email X | Resend with new subject line after 48h | ConvertKit: Visual Automations; ActiveCampaign: "Wait + Condition" |
| Purchased product | Remove from sales sequence, add to customer sequence | Requires integration (Stripe, Gumroad, etc.) |
| Replied to email | Tag as "engaged," prioritize for personal follow-up | Manual or via helpdesk integration |

**GATE: Present the full sequence map to the user. Do not write email copy until the map is approved.**

---

## Phase 3: Write the Emails

Write each email in the sequence with this structure. Present all emails together as a complete set.

### Email Format

For every email, deliver:

1. **Subject Line A** — primary subject line
2. **Subject Line B** — A/B test variant (different angle, not just a word swap)
3. **Preview text** — the snippet that shows after the subject line in the inbox (40-90 characters)
4. **Body** — the full email copy
5. **CTA** — clearly marked in the body
6. **Send timing** — exact delay from previous email or trigger

### Subject Line Rules

- **A/B variants must test different angles**, not just synonyms. "5 Portfolio Mistakes" vs "Why Your Portfolio Isn't Landing Clients" — good. "5 Portfolio Mistakes" vs "Five Portfolio Mistakes" — useless.
- **Keep under 50 characters** — mobile inboxes truncate beyond this
- **Preview text must complement, not repeat** the subject line
- **NEVER use ALL CAPS, excessive punctuation, or spam trigger words** (free, guarantee, act now, limited time)

### Email Body Rules

- **One CTA per email.** Not two. Not "also check out." One action.
- **Length varies by purpose:** delivery emails can be short (100 words), story emails can be longer (300 words), sales emails should be 200-400 words
- **Use line breaks generously** — no paragraph longer than 3 sentences
- **Write in second person** ("you") with first person ("I") for personal voice
- **End every email with a P.S. line** — it is the second most-read part of any email after the subject line

### Example Email: Welcome Series, Email 1 — "The Welcome"

```
Subject Line A: your portfolio templates are inside
Subject Line B: grab your 5 templates (and what's coming next)

Preview text: Plus the one thing most freelancers miss

---

Hey [FIRST_NAME],

Welcome — and thanks for grabbing the 5 Portfolio Templates.

Here's your download link: [LINK]

Quick tip before you dive in: Template #3 (the case study layout)
is the one my students say lands the most client calls. Start there
if you're short on time.

Over the next two weeks, I'm going to send you a few emails that
will help you turn these templates into an actual client-getting
portfolio — not just a pretty PDF collecting dust.

Here's what's coming:

- Day 2: A 15-minute exercise to customize your first template
- Day 4: The story that made me quit my agency job and freelance full-time
- Day 7: The real reason most portfolios don't convert (and the fix)
- Day 14: An invitation to go deeper, if you want to

For now, download your templates and pick the one that fits your work best.

Talk soon,
[YOUR NAME]

P.S. If you hit reply and tell me what kind of freelance work you do,
I'll point you to the template that fits best. I read every reply.
```

### Example Email: Launch Sequence, Email 1 — "The Announcement" (Day 1 of 7)

```
Subject Line A: doors are open (finally)
Subject Line B: the thing I've been building for 6 months

Preview text: Design Freelance Accelerator is live

---

Hey [FIRST_NAME],

For the past 6 months I've been building something I wish existed
when I was struggling to land freelance clients.

It's called the Design Freelance Accelerator, and today it's officially
open for enrollment.

Here's the short version: it's a 6-week program that takes you from
"I have skills but no clients" to "I have a full pipeline and I'm
raising my rates."

Inside you'll get:

- The portfolio framework that helped me go from $35/hr to $5,000/project
- My exact outreach scripts (the ones that book calls, not the ones that get ignored)
- Weekly live sessions where I review your portfolio and positioning
- A private community of freelancers at your stage (no gurus, no fluff)

The investment is $297. Enrollment closes on [DATE].

If you've been reading these emails and thinking "I need to actually
do this" — this is the moment.

Check out the full details here: [LINK]

Talk soon,
[YOUR NAME]

P.S. The first 20 people who enroll get a free 1-on-1 portfolio
review with me. As of right now, there are [X] spots left.
```

### Example Email: Launch Sequence, Email 4 — "The Objection Handler" (Day 4 of 7)

```
Subject Line A: "but I'm not ready yet"
Subject Line B: the most common thing people tell me

Preview text: Here's my honest answer

---

Hey [FIRST_NAME],

The number one thing people tell me when they see the Accelerator:

"This looks great, but I don't think I'm ready yet."

I get it. Here's my honest take:

If you have the skills to do the work but you're struggling to
find people who will pay you well for it — you're not "not ready."
You have a positioning and visibility problem, not a skill problem.

The Accelerator doesn't teach you how to design. It teaches you how
to get hired.

Quick proof: Maria joined the last cohort as a junior designer doing
$500 logo projects. Six weeks later she had repositioned as a brand
identity specialist and landed a $4,200 project. She didn't learn
new design skills — she learned how to present the ones she had.

If that sounds like your situation, this is the program.

Enrollment closes [DATE]: [LINK]

Talk soon,
[YOUR NAME]

P.S. If you have a specific question about whether this is right
for you, just reply to this email. I'll give you an honest answer —
even if that answer is "wait."
```

**GATE: Present all emails to the user as a complete sequence. Do not finalize until the user approves the copy, subject lines, and timing.**

---

## Phase 4: Deliver

Once the user approves, organize the final output and add platform-specific implementation notes.

### Delivery Format

Write the complete sequence to `sequences/[sequence-type]-sequence.md` with these sections: Strategy Brief, Sequence Map, Email Copy (all emails with Subject A/B, preview text, body, CTA), A/B Test Plan, Platform Implementation Notes, Pre-Delivery Checklist.

### Platform Implementation Notes

Include setup instructions specific to the user's email platform:

#### ConvertKit

- Create a Visual Automation with the opt-in form as the trigger
- Add each email as an "Email" step with "Delay" steps between them
- Use "Conditions" for branching (clicked link, tag applied, purchased)
- A/B subject lines: use the built-in "A/B" toggle on each email step (50/50 split by default, winner sent after 4 hours)
- Tag subscribers with "Link Triggers" on key CTAs for segmentation
- Remove from sequence on purchase using a "Goal" step or event trigger

#### Mailchimp

- Build the sequence as a "Customer Journey" (not a classic automation)
- Add "Send Email" actions with "Time Delay" between them
- Use "If/Else" branches for conditional logic (opened, clicked, tagged)
- A/B subject lines: create the email, toggle "A/B Test," select "Subject Line," set sample size to 50% and wait time to 4 hours
- Use "Tags" to segment subscribers who click key links
- Add a "Goal" exit point for purchases (requires e-commerce integration)

#### ActiveCampaign

- Create an Automation with the trigger as "Subscribes to list" or "Tag is added"
- Use "Send Email" actions with "Wait" conditions between them
- Branching: "If/Else" blocks based on "Has opened email," "Has clicked link," or "Has tag"
- A/B subject lines: use the "Split Action" to send variant A to 50% and variant B to 50%, then add a "Wait + Condition" to continue with the winner
- Use "Add Tag" actions after key link clicks for segmentation
- Exit the automation on purchase using "Goal" conditions tied to your payment processor

### A/B Testing Defaults

When the user does not specify testing preferences, apply these defaults:

| Parameter | Default |
|-----------|---------|
| Split ratio | 50/50 |
| Wait time before picking winner | 4 hours |
| Winning metric | Open rate (subject lines), Click rate (body variants) |
| Minimum sample size | 100 subscribers (below this, skip A/B and send best guess) |

### Pre-Delivery Checklist

Include this at the end of every delivered sequence:

```
## Pre-Delivery Checklist

- [ ] Every email has a single, clear CTA (not two, not zero)
- [ ] Subject lines are under 50 characters
- [ ] Preview text does not repeat the subject line
- [ ] A/B subject lines test different angles, not word swaps
- [ ] No email sends less than 24 hours after the previous one
- [ ] Conditional branches are clearly labeled (trigger + action)
- [ ] P.S. line included on every email
- [ ] Personalization tokens ([FIRST_NAME]) are correct for the platform
- [ ] Unsubscribe link is included (platform handles this automatically)
- [ ] Purchase / goal exit points are defined
- [ ] Tone is consistent across all emails in the sequence
- [ ] No spam trigger words in subject lines (free, guarantee, act now)
```

---

## Anti-Patterns

**NEVER do these in email sequences:**

- **Sending daily emails in a nurture sequence** — subscribers feel bombarded and unsubscribe. Minimum 2-day gaps for welcome/nurture, 1-day gaps only during a launch window.
- **Clickbait subject lines** — "You won't BELIEVE what happened" or "This changes everything" erodes trust and trains subscribers to ignore you. Subject lines must honestly reflect the email content.
- **Burying the CTA** — if readers have to scroll past 500 words to find the action, they will not take it. The CTA should be visible without excessive scrolling, and repeated at the bottom for longer emails.
- **Multiple CTAs per email** — "Buy the course, also join the webinar, also follow me on Instagram" splits attention and reduces action on all three. One email, one ask.
- **No clear reason to open the next email** — each email should tease or set up the next one. If Email 3 does not give the reader a reason to watch for Email 4, the sequence dies.
- **Skipping the welcome email** — sending a nurture or pitch email first without delivering the lead magnet and setting expectations breaks trust immediately.
- **Identical A/B subject lines** — "5 Tips" vs "Five Tips" is not a test. Variants must represent different hooks, angles, or emotional appeals.
- **Walls of text** — no paragraph longer than 3 sentences. Use white space. Email is a scanning medium.
- **Assuming the subscriber remembers you** — early emails in a sequence should briefly remind the reader who you are and why they signed up.

---

## Recovery

- **User is unsure which sequence type they need:** Ask what triggered the request. If they just launched a lead magnet, it is a welcome series. If they have an engaged list and a product to sell, it is a launch sequence. If their open rates are dropping, it is re-engagement. Guide them to the right type.
- **User wants more emails than recommended:** Allow it, but flag the risk. More than 7 emails in a welcome series or 8 in a launch sequence typically sees steep drop-off in opens after the midpoint. Recommend front-loading the most important content.
- **User has no lead magnet or entry point:** Help them define one before building the welcome sequence. A sequence without a clear entry trigger has no anchor. Suggest a simple option: checklist PDF, short video training, or template pack.
- **User's list is under 100 subscribers:** Flag that A/B testing will not produce statistically meaningful results at this size. Recommend they write one strong subject line per email instead of splitting, and start A/B testing when they cross 500 subscribers.
- **User wants to include affiliate or sponsor content in the sequence:** Advise against it in the first 3 emails of any sequence — trust is not established yet. If they insist, limit it to a brief mention in the P.S. line, never the main CTA.
- **User does not know their email platform yet:** Default to ConvertKit for creators and solopreneurs, Mailchimp for e-commerce, ActiveCampaign for advanced automation needs. Provide implementation notes for all three and let them choose later.
- **If 3 revision rounds on the same email produce no approval:** Stop and reassess. Ask the user to share an email they admire from another creator so you can match the voice and structure they are looking for.

---

## Quick Reference: Timing Defaults by Sequence Type

### Welcome Series (5 Emails / 14 Days)

| Email | Name | Delay | Purpose |
|-------|------|-------|---------|
| 1 | The Welcome | Immediate | Deliver lead magnet, set expectations |
| 2 | The Quick Win | +2 days | Help them get a fast result |
| 3 | The Story | +2 days | Build trust through narrative |
| 4 | The Deeper Problem | +3 days | Name the obstacle, position solution |
| 5 | The Invitation | +7 days | Present the paid offer |

### Nurture Series (7 Emails / 30 Days)

| Email | Name | Delay | Purpose |
|-------|------|-------|---------|
| 1 | The Reintroduction | +3 days after welcome ends | Re-engage with a fresh angle |
| 2 | The Framework | +4 days | Teach a core concept or method |
| 3 | The Case Study | +4 days | Prove the method works with evidence |
| 4 | The Common Mistake | +4 days | Call out a pitfall they are likely making |
| 5 | The Behind-the-Scenes | +5 days | Show your process or daily reality |
| 6 | The Resource Drop | +5 days | Share a tool, template, or curated list |
| 7 | The Soft Pitch | +5 days | Introduce your offer as a natural next step |

### Launch Series (6 Emails / 7 Days)

| Email | Name | Delay | Purpose |
|-------|------|-------|---------|
| 1 | The Announcement | Day 1 | Reveal the offer, generate excitement |
| 2 | The Deep Dive | Day 2 | Explain what is included and who it is for |
| 3 | The Social Proof | Day 3 | Share testimonials, results, case studies |
| 4 | The Objection Handler | Day 5 | Address the top 1-2 reasons people hesitate |
| 5 | The Deadline Warning | Day 6 | Remind them the window is closing |
| 6 | The Final Call | Day 7 | Last chance, cart closes tonight |

### Re-engagement Series (3 Emails / 10 Days)

| Email | Name | Delay | Purpose |
|-------|------|-------|---------|
| 1 | The Check-In | Day 1 | Acknowledge the silence, offer value |
| 2 | The Best-Of | +5 days | Share your top-performing content they missed |
| 3 | The Farewell | +4 days | Let them self-select: stay or unsubscribe |
